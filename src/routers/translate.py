import io
import logging
import os
import tempfile
import shutil
from pathlib import Path
from typing import Annotated

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
from core.dependencies import get_application_settings, get_genai_client

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

@router.post("/translate")
async def translate_srt(
    settings: Annotated[Settings, Depends(get_application_settings)],
    genai_client: Annotated[genai.client.Client | None, Depends(get_genai_client)],
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    speed_mode: str = Form("normal")
):
    """Handles the SRT file upload, translation orchestration, and response."""
    logger.info(f"Received request for /translate for target language '{target_lang}' with speed mode '{speed_mode}'")

    # Client Check (moved up slightly for clarity)
    # Check if the client is needed based on speed_mode and settings
    client_required = speed_mode != "mock" and settings.AI_PROVIDER == "google-gemini"

    if client_required and genai_client is None:
        # This covers two cases: provider is gemini but init failed, OR provider is not gemini
        # but speed_mode requires it (which shouldn't happen with proper config, but good to check)
        if settings.AI_PROVIDER != "google-gemini":
             logger.error("Translation request failed: AI provider '%s' does not support non-mock translation.", settings.AI_PROVIDER)
             raise HTTPException(
                 status_code=501, # Not Implemented or 503 Service Unavailable?
                 detail=f"Service Unavailable: AI provider '{settings.AI_PROVIDER}' does not support non-mock translation."
             )
        else:
             # Provider is gemini, but client failed to initialize
             logger.error("Translation request failed: Generative AI client is configured but not available.")
             raise HTTPException(
                 status_code=503,
                 detail="Service Unavailable: Translation backend not ready or failed to initialize."
             )

    # Input Validation
    if not file.filename or not file.filename.lower().endswith('.srt'):
        logger.warning(f"Translation request failed: Invalid file type '{file.filename}'.")
        raise ValidationError("Invalid file type. Please upload an SRT file.")

    if not target_lang:
        logger.warning("Translation request failed: Target language not specified.")
        raise ValidationError("Target language must be specified.")

    if target_lang not in settings.TARGET_LANGUAGES:
        logger.warning(f"Translation request failed: Invalid target language '{target_lang}'.")
        raise ValidationError(f"Invalid target language: {target_lang}. Available: {', '.join(settings.TARGET_LANGUAGES)}")

    # Secure filename and prepare temporary file path
    original_filename = secure_filename(file.filename)
    temp_dir = None  # Initialize temp_dir to None
    try:
        temp_dir = tempfile.mkdtemp() # Create temp dir inside try
        temp_file_path = os.path.join(temp_dir, original_filename)

        # Save uploaded file asynchronously
        content = await file.read()
        async with aiofiles.open(temp_file_path, "wb") as temp_file:
            await temp_file.write(content)
        logger.debug(f"Saved uploaded file temporarily to: {temp_file_path}")

        # Workflow Orchestration
        logger.info(f"Starting translation workflow for {original_filename} to {target_lang} ({speed_mode} mode)")

        # 1. Parse SRT
        logger.debug("Parsing SRT file...")
        subtitle_chunks: list[list[SubtitleBlock]] = await parse_srt(
            temp_file_path, settings.CHUNK_MAX_BLOCKS
        )
        logger.info(f"Parsed SRT into {len(subtitle_chunks)} chunk(s).")

        # 2. Detect Context
        logger.debug("Detecting context...")
        # Pass the potentially None client - detect_context should handle mock mode without it
        context: str = await detect_context(
            subtitle_chunks, speed_mode, genai_client, settings
        )
        logger.info(f"Detected context: '{context[:100]}...'")

        # 3. Translate Chunks
        logger.debug("Translating chunks...")
        # Pass the potentially None client - translate_all_chunks should handle mock mode without it
        await translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=speed_mode,
            client=genai_client,
            settings=settings,
        )
        logger.info("Chunks translated successfully.")

        # 4. Reassemble SRT
        logger.debug("Reassembling SRT...")
        output_srt_content = reassemble_srt(subtitle_chunks)
        logger.info("SRT reassembled successfully.")

        # 5. Return translated SRT file
        logger.info(f"Returning translated SRT for {original_filename} to {target_lang}")
        new_filename = f"{os.path.splitext(original_filename)[0]}_{target_lang.lower()}.srt"
        
        return StreamingResponse(
            io.BytesIO(output_srt_content.encode('utf-8') if isinstance(output_srt_content, str) else output_srt_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={new_filename}"}
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error during translation: {e}")
        raise
    except ParsingError as e:
        logger.error(f"Error parsing SRT: {e}")
        raise
    except ContextDetectionError as e:
        logger.error(f"Error detecting context: {e}")
        raise
    except ChunkTranslationError as e:
        logger.error(f"Error translating chunks: {e}")
        raise
    except RetryError as e:
        logger.error(f"Retry error after multiple attempts: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unhandled exception during translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Ensure cleanup happens regardless of success or failure
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Successfully removed temporary directory: {temp_dir}")
            except OSError as e:
                logger.error(f"Error removing temporary directory {temp_dir}: {e}")