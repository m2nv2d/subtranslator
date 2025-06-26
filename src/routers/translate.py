import io
import logging
import os
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Annotated, Tuple

from fastapi import APIRouter, Request, File, Form, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from google import genai
from tenacity import RetryError
from werkzeug.utils import secure_filename
import aiofiles

from translator import (
    parse_srt,
    detect_context,
    reassemble_srt,
    translate_all_chunks,
    SubtitleBlock,
    ValidationError,
    ParsingError,
    ContextDetectionError,
    ChunkTranslationError,
)

from core.config import Settings
from core.dependencies import get_application_settings, get_genai_client, get_translation_semaphore, get_stats_store, get_application_rate_limiter
from core.stats import AppStatsStore, TotalStats, FileStats
from core.rate_limiter import check_session_file_limit

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

# Setup Jinja2 templates
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)

# Routes
@router.get("/", response_class=HTMLResponse)
async def index(request: Request, settings: Annotated[Settings, Depends(get_application_settings)]):
    """Renders the main upload form."""
    logger.debug("Serving index page.")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "languages": settings.TARGET_LANGUAGES}
    )


@router.get("/stats", response_model=Tuple[TotalStats, dict[str, FileStats]])
async def get_statistics(
    stats_store: Annotated[AppStatsStore, Depends(get_stats_store)]
):
    """Returns the current application statistics."""
    logger.info("Received request for /stats")
    total_stats, file_stats = await stats_store.get_stats()
    logger.debug(f"Returning stats: Total={total_stats}, Files={len(file_stats)} entries")
    # FastAPI automatically serializes Pydantic models and dicts
    return total_stats, file_stats


@router.post("/translate")
async def translate_srt(
    request: Request,
    settings: Annotated[Settings, Depends(get_application_settings)],
    genai_client: Annotated[genai.client.Client | None, Depends(get_genai_client)],
    semaphore: Annotated[asyncio.Semaphore, Depends(get_translation_semaphore)],
    stats_store: Annotated[AppStatsStore, Depends(get_stats_store)],
    _: None = Depends(check_session_file_limit),
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    speed_mode: str = Form("normal")
):
    """Handles the SRT file upload, translation orchestration, and response."""
    logger.info(f"Received request for /translate for target language '{target_lang}' with speed mode '{speed_mode}'")

    request_id = None
    status = "failed" # Default status
    temp_dir = None

    try:
        # Client Check
        client_required = speed_mode != "mock" and settings.AI_PROVIDER == "google-gemini"
        if client_required and genai_client is None:
            if settings.AI_PROVIDER != "google-gemini":
                logger.error("Translation request failed: AI provider '%s' does not support non-mock translation.", settings.AI_PROVIDER)
                raise HTTPException(
                    status_code=501,
                    detail=f"Service Unavailable: AI provider '{settings.AI_PROVIDER}' does not support non-mock translation."
                )
            else:
                logger.error("Translation request failed: Generative AI client is configured but not available.")
                raise HTTPException(
                    status_code=503,
                    detail="Service Unavailable: Translation backend not ready or failed to initialize."
                )

        # Input Validation
        if not file.filename or not file.filename.lower().endswith('.srt'):
            logger.warning(f"Validation error: Invalid file type '{file.filename}'.")
            raise ValidationError("Invalid file type. Please upload an SRT file.")
        if not target_lang:
            logger.warning("Validation error: Target language not specified.")
            raise ValidationError("Target language must be specified.")
        if target_lang not in settings.TARGET_LANGUAGES:
            logger.warning(f"Validation error: Invalid target language '{target_lang}'.")
            raise ValidationError(f"Invalid target language: {target_lang}. Available: {', '.join(settings.TARGET_LANGUAGES)}")
        allowed_speed_modes = {"fast", "normal", "mock"}
        if speed_mode not in allowed_speed_modes:
            logger.warning(f"Validation error: Invalid speed mode '{speed_mode}'.")
            raise ValidationError(f"Invalid speed mode: '{speed_mode}'. Allowed modes: {', '.join(allowed_speed_modes)}")

        # Secure filename and read content once to get size
        original_filename = secure_filename(file.filename)
        content = await file.read()
        file_size = len(content)
        logger.debug(f"Received file '{original_filename}' with size {file_size} bytes.")

        # Create stats entry *before* file I/O or workflow
        request_id = await stats_store.create_file_entry(
            filename=original_filename, size=file_size, speed_mode=speed_mode
        )
        logger.info(f"Created stats entry for request_id: {request_id}")

        # Prepare temporary file path and save content
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, original_filename)
        async with aiofiles.open(temp_file_path, "wb") as temp_file:
            await temp_file.write(content)
        logger.debug(f"Saved uploaded file temporarily to: {temp_file_path}")

        # --- Start of core workflow --- 
        try:
            logger.info(f"Starting translation workflow for {request_id} ({original_filename}) to {target_lang} ({speed_mode} mode)")

            # 1. Parse SRT
            logger.debug(f"Parsing SRT file for {request_id}...")
            subtitle_chunks: list[list[SubtitleBlock]] = await parse_srt(
                temp_file_path, settings.CHUNK_MAX_BLOCKS
            )
            num_chunks = len(subtitle_chunks)
            total_blocks = sum(len(chunk) for chunk in subtitle_chunks)
            logger.info(f"Parsed SRT for {request_id} into {num_chunks} chunk(s) with {total_blocks} total blocks.")
            await stats_store.update_parsing_stats(request_id, num_chunks, total_blocks)

            # 2. Detect Context
            logger.debug(f"Detecting context for {request_id}...")
            context: str = await detect_context(
                subtitle_chunks, speed_mode, genai_client, settings
            )
            logger.info(f"Detected context for {request_id}: '{context[:100]}...'" if context else f"No context detected for {request_id}.")

            # 3. Translate Chunks (Assumes modification in-place, returns stats)
            logger.debug(f"Translating chunks for {request_id}...")
            # NOTE: Assumes translate_all_chunks returns Tuple[int, int] as per Subtask 4 spec
            failed_attempts, chunks_with_failures = await translate_all_chunks(
                context=context,
                sub=subtitle_chunks, # Pass list to be modified in-place
                target_lang=target_lang,
                speed_mode=speed_mode,
                client=genai_client,
                settings=settings,
                semaphore=semaphore,
            )
            logger.info(f"Chunks translated for {request_id} with {failed_attempts} total attempts and {chunks_with_failures} chunks having failures.")
            await stats_store.update_translation_stats(request_id, failed_attempts, chunks_with_failures)

            # 4. Reassemble SRT
            logger.debug(f"Reassembling SRT for {request_id}...")
            output_srt_content = reassemble_srt(subtitle_chunks)
            logger.info(f"SRT reassembled successfully for {request_id}.")

            # Workflow successful
            status = "completed"

            # 5. Return translated SRT file
            new_filename = f"{os.path.splitext(original_filename)[0]}_{target_lang.lower()}.srt"
            logger.info(f"Returning translated SRT for {request_id} ({original_filename} to {target_lang}) as '{new_filename}'")
            return StreamingResponse(
                io.BytesIO(output_srt_content.encode('utf-8') if isinstance(output_srt_content, str) else output_srt_content),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={new_filename}"}
            )

        except (ParsingError, ContextDetectionError, ChunkTranslationError, RetryError) as workflow_error:
            logger.error(f"Workflow error for request {request_id}: {workflow_error}", exc_info=True)
            status = "failed"
            # Re-raise specific errors for FastAPI/caller to handle potentially
            # Or convert to HTTPException here if preferred
            if isinstance(workflow_error, ParsingError):
                 raise HTTPException(status_code=400, detail=f"Failed to parse SRT file: {workflow_error}")
            elif isinstance(workflow_error, ContextDetectionError):
                 raise HTTPException(status_code=500, detail=f"Failed to detect context: {workflow_error}")
            elif isinstance(workflow_error, ChunkTranslationError):
                 raise HTTPException(status_code=500, detail=f"Failed during chunk translation: {workflow_error}")
            elif isinstance(workflow_error, RetryError):
                 raise HTTPException(status_code=504, detail=f"Translation timed out or failed after multiple retries: {workflow_error}")
            else:
                 raise HTTPException(status_code=500, detail="An internal error occurred during translation workflow.") # Fallback

        except Exception as inner_e: # Catch unexpected errors during workflow
            logger.exception(f"Unexpected workflow exception for request {request_id}: {inner_e}")
            status = "failed"
            raise HTTPException(status_code=500, detail=f"Internal translation error occurred for request {request_id}.")
        # --- End of core workflow --- 

    except ValidationError as e:
        logger.warning(f"Validation error before workflow start: {e}")
        # request_id might be None here, status is implicitly failed
        raise HTTPException(status_code=400, detail=str(e)) # Use 400 for validation
    except HTTPException as e: 
         logger.error(f"HTTP Exception caught: {e.detail}")
         if request_id: # If entry was created before exception
             status = "failed" # Mark as failed if needed (though it defaults to failed)
         raise # Re-raise HTTPException
    except Exception as outer_e:
        logger.exception(f"Unhandled exception before or during setup for request {request_id or 'N/A'}: {outer_e}")
        if request_id:
            status = "failed"
        raise HTTPException(status_code=500, detail="An unexpected server error occurred during request setup.")
    finally:
        # Ensure cleanup happens regardless of success or failure
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Successfully removed temporary directory for request {request_id or 'N/A'}: {temp_dir}")
            except OSError as e:
                logger.error(f"Error removing temporary directory {temp_dir} for request {request_id or 'N/A'}: {e}")
        
        # Update final status in stats store if an entry was created
        if request_id:
            await stats_store.complete_request(request_id, status)
            logger.info(f"Request {request_id} marked as '{status}' in stats store.")