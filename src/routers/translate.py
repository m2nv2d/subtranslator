import io
import logging
import os
import tempfile
import shutil
import asyncio
import uuid
from pathlib import Path
from typing import Annotated, Tuple, Dict, Optional
from enum import Enum

from fastapi import APIRouter, Request, File, Form, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from tenacity import RetryError
from werkzeug.utils import secure_filename
import aiofiles
from pydantic import BaseModel

from translator import (
    parse_srt,
    reassemble_srt,
    SubtitleBlock,
    ValidationError,
    ParsingError,
    ContextDetectionError,
    ChunkTranslationError,
)

from core.config import Settings
from core.dependencies import get_application_settings, get_ai_provider, get_translation_semaphore, get_stats_store, get_application_rate_limiter
from core.providers import AIProvider
from core.stats import AppStatsStore, TotalStats, FileStats
from core.rate_limiter import check_session_file_limit

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

# Setup Jinja2 templates
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)

# Async translation management
class TranslationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TranslationJob(BaseModel):
    id: str
    filename: str
    target_lang: str
    speed_mode: str
    status: TranslationStatus
    progress: float
    message: str
    error: Optional[str] = None
    download_url: Optional[str] = None
    created_at: float
    request_id: Optional[str] = None

class TranslationResponse(BaseModel):
    translation_id: str
    message: str

class TranslationStatusResponse(BaseModel):
    status: TranslationStatus
    progress: float
    message: str
    error: Optional[str] = None
    download_url: Optional[str] = None
    filename: Optional[str] = None

# In-memory storage for translation jobs (in production, use Redis or database)
translation_jobs: Dict[str, TranslationJob] = {}
translation_tasks: Dict[str, asyncio.Task] = {}

# Routes
@router.get("/", response_class=HTMLResponse)
async def index(request: Request, settings: Annotated[Settings, Depends(get_application_settings)]):
    """Renders the main upload form."""
    logger.debug("Serving index page.")
    return templates.TemplateResponse(
        "index_multiscreen.html",
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
    provider: Annotated[AIProvider, Depends(get_ai_provider)],
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
        # Provider is guaranteed to be available due to dependency injection
        logger.debug(f"Using AI provider: {settings.AI_PROVIDER}")

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
            context: str = await provider.detect_context(
                subtitle_chunks, speed_mode
            )
            logger.info(f"Detected context for {request_id}: '{context[:100]}...'" if context else f"No context detected for {request_id}.")

            # 3. Translate Chunks (Assumes modification in-place, returns stats)
            logger.debug(f"Translating chunks for {request_id}...")
            # NOTE: Assumes translate_all_chunks returns Tuple[int, int] as per Subtask 4 spec
            failed_attempts, chunks_with_failures = await provider.translate_all_chunks(
                context=context,
                sub=subtitle_chunks, # Pass list to be modified in-place
                target_lang=target_lang,
                speed_mode=speed_mode,
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


# Async translation worker function
async def process_translation_async(
    job_id: str,
    file_content: bytes,
    filename: str,
    target_lang: str,
    speed_mode: str,
    settings: Settings,
    provider: AIProvider,
    semaphore: asyncio.Semaphore,
    stats_store: AppStatsStore
):
    """Background task to process translation asynchronously."""
    job = translation_jobs.get(job_id)
    if not job:
        logger.error(f"Translation job {job_id} not found")
        return
    
    temp_dir = None
    request_id = None
    
    try:
        # Update job status
        job.status = TranslationStatus.PROCESSING
        job.message = "Preparing translation..."
        job.progress = 0.1
        
        # Create temp file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, filename)
        async with aiofiles.open(temp_file_path, "wb") as temp_file:
            await temp_file.write(file_content)
        
        # Create stats entry
        request_id = await stats_store.create_file_entry(
            filename=filename, size=len(file_content), speed_mode=speed_mode
        )
        job.request_id = request_id
        
        # Check if job was cancelled
        if job.status == TranslationStatus.CANCELLED:
            return
        
        # Parse SRT
        job.message = "Parsing subtitle file..."
        job.progress = 0.2
        subtitle_chunks: list[list[SubtitleBlock]] = await parse_srt(
            temp_file_path, settings.CHUNK_MAX_BLOCKS
        )
        num_chunks = len(subtitle_chunks)
        total_blocks = sum(len(chunk) for chunk in subtitle_chunks)
        await stats_store.update_parsing_stats(request_id, num_chunks, total_blocks)
        
        if job.status == TranslationStatus.CANCELLED:
            return
        
        # Detect Context
        job.message = "Detecting context..."
        job.progress = 0.3
        context: str = await provider.detect_context(subtitle_chunks, speed_mode)
        
        if job.status == TranslationStatus.CANCELLED:
            return
        
        # Translate Chunks
        job.message = "Translating content..."
        job.progress = 0.4
        failed_attempts, chunks_with_failures = await provider.translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=speed_mode,
            semaphore=semaphore,
        )
        await stats_store.update_translation_stats(request_id, failed_attempts, chunks_with_failures)
        
        if job.status == TranslationStatus.CANCELLED:
            return
        
        # Reassemble SRT
        job.message = "Finalizing translation..."
        job.progress = 0.9
        output_srt_content = reassemble_srt(subtitle_chunks)
        
        # Debug logging
        logger.info(f"output_srt_content type: {type(output_srt_content)}")
        logger.info(f"output_srt_content length: {len(output_srt_content) if output_srt_content else 'None'}")
        
        # Save translated file
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)
        new_filename = f"{os.path.splitext(filename)[0]}_{target_lang.lower()}.srt"
        output_file_path = output_dir / new_filename
        
        # Convert to string and write in text mode to match expected behavior
        if isinstance(output_srt_content, bytes):
            content_str = output_srt_content.decode('utf-8')
        else:
            content_str = str(output_srt_content)
            
        with open(output_file_path, "w", encoding='utf-8') as f:
            f.write(content_str)
        
        # Update job as completed
        job.status = TranslationStatus.COMPLETED
        job.progress = 1.0
        job.message = "Translation completed successfully!"
        job.download_url = f"/translate/download/{job_id}"
        
        # Update stats
        if request_id:
            await stats_store.complete_request(request_id, "completed")
        
        logger.info(f"Translation job {job_id} completed successfully")
        
    except asyncio.CancelledError:
        job.status = TranslationStatus.CANCELLED
        job.message = "Translation was cancelled"
        if request_id:
            await stats_store.complete_request(request_id, "cancelled")
        logger.info(f"Translation job {job_id} was cancelled")
        
    except Exception as e:
        job.status = TranslationStatus.FAILED
        job.error = str(e)
        job.message = f"Translation failed: {str(e)}"
        if request_id:
            await stats_store.complete_request(request_id, "failed")
        logger.error(f"Translation job {job_id} failed: {e}", exc_info=True)
        
    finally:
        # Cleanup temp directory (but keep output for download)
        if temp_dir and os.path.exists(temp_dir):
            try:
                # Only clean up input files, keep output directory
                input_file = os.path.join(temp_dir, filename)
                if os.path.exists(input_file):
                    os.remove(input_file)
            except OSError as e:
                logger.error(f"Error removing temporary input file for job {job_id}: {e}")


@router.post("/translate/async", response_model=TranslationResponse)
async def start_async_translation(
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_application_settings)],
    provider: Annotated[AIProvider, Depends(get_ai_provider)],
    semaphore: Annotated[asyncio.Semaphore, Depends(get_translation_semaphore)],
    stats_store: Annotated[AppStatsStore, Depends(get_stats_store)],
    _: None = Depends(check_session_file_limit),
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    speed_mode: str = Form("normal")
):
    """Start an asynchronous translation job."""
    # Input Validation
    if not file.filename or not file.filename.lower().endswith('.srt'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an SRT file.")
    if not target_lang or target_lang not in settings.TARGET_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Invalid target language: {target_lang}")
    allowed_speed_modes = {"fast", "normal", "mock"}
    if speed_mode not in allowed_speed_modes:
        raise HTTPException(status_code=400, detail=f"Invalid speed mode: {speed_mode}")
    
    # Read file content
    original_filename = secure_filename(file.filename)
    content = await file.read()
    
    # Create translation job
    job_id = str(uuid.uuid4())
    job = TranslationJob(
        id=job_id,
        filename=original_filename,
        target_lang=target_lang,
        speed_mode=speed_mode,
        status=TranslationStatus.PENDING,
        progress=0.0,
        message="Translation queued...",
        created_at=asyncio.get_event_loop().time()
    )
    
    translation_jobs[job_id] = job
    
    # Start background task
    task = asyncio.create_task(
        process_translation_async(
            job_id, content, original_filename, target_lang, speed_mode,
            settings, provider, semaphore, stats_store
        )
    )
    translation_tasks[job_id] = task
    
    logger.info(f"Started async translation job {job_id} for file {original_filename}")
    
    return TranslationResponse(
        translation_id=job_id,
        message="Translation started successfully"
    )


@router.get("/translate/status/{job_id}", response_model=TranslationStatusResponse)
async def get_translation_status(job_id: str):
    """Get the status of a translation job."""
    job = translation_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    
    return TranslationStatusResponse(
        status=job.status,
        progress=job.progress,
        message=job.message,
        error=job.error,
        download_url=job.download_url,
        filename=job.filename
    )


@router.post("/translate/cancel/{job_id}")
async def cancel_translation(job_id: str):
    """Cancel a translation job."""
    job = translation_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    
    if job.status in [TranslationStatus.COMPLETED, TranslationStatus.FAILED, TranslationStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Translation job cannot be cancelled")
    
    # Cancel the task
    task = translation_tasks.get(job_id)
    if task and not task.done():
        task.cancel()
    
    # Update job status
    job.status = TranslationStatus.CANCELLED
    job.message = "Translation cancelled by user"
    
    logger.info(f"Translation job {job_id} cancelled")
    
    return {"message": "Translation cancelled successfully"}


@router.get("/translate/download/{job_id}")
async def download_translation(job_id: str):
    """Download the translated file."""
    job = translation_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    
    if job.status != TranslationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Translation not completed")
    
    # Find the output file
    temp_dirs = [d for d in os.listdir(tempfile.gettempdir()) if d.startswith('tmp')]
    output_file = None
    
    for temp_dir_name in temp_dirs:
        temp_dir_path = os.path.join(tempfile.gettempdir(), temp_dir_name)
        output_dir = os.path.join(temp_dir_path, "output")
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.startswith(os.path.splitext(job.filename)[0]):
                    output_file = os.path.join(output_dir, file)
                    break
            if output_file:
                break
    
    if not output_file or not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Translated file not found")
    
    return FileResponse(
        path=output_file,
        media_type="application/octet-stream",
        filename=f"{os.path.splitext(job.filename)[0]}_{job.target_lang.lower()}.srt"
    )