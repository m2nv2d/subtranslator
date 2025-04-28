import asyncio
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request, File, Form, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google import genai
from tenacity import RetryError
from werkzeug.utils import secure_filename

from translator import (
    parse_srt,
    detect_context,
    reassemble_srt,
    translate_all_chunks,
    Config,
    SubtitleBlock,
    ConfigError,
    ValidationError,
    ParsingError,
    ContextDetectionError,
    ChunkTranslationError,
    GenAIClientInitError,
)

from dependencies import get_config, get_genai_client

# Configure logging (this will be reconfigured once config is loaded via dependency)
# We set a basic default level here
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(title="Subtranslator")

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Setup Jinja2 templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=templates_path)

# Exception Handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation Error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )

@app.exception_handler(ParsingError)
async def parsing_error_handler(request: Request, exc: ParsingError):
    logger.error(f"Parsing Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=422,
        content={"error": str(exc)}
    )

@app.exception_handler(ContextDetectionError)
async def context_detection_error_handler(request: Request, exc: ContextDetectionError):
    logger.error(f"Context Detection Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

@app.exception_handler(ChunkTranslationError)
async def chunk_translation_error_handler(request: Request, exc: ChunkTranslationError):
    logger.error(f"Chunk Translation Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

@app.exception_handler(RetryError)
async def retry_error_handler(request: Request, exc: RetryError):
    logger.error(f"Retry Error after multiple attempts: {exc}", exc_info=True)
    return JSONResponse(
        status_code=504,
        content={"error": "Service temporarily unavailable after multiple retries."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected internal server error occurred."}
    )

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, config: Annotated[Config, Depends(get_config)]):
    """Renders the main upload form."""
    logger.debug("Serving index page.")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "languages": config.target_languages}
    )

@app.post("/translate")
async def translate_srt(
    config: Annotated[Config, Depends(get_config)],
    genai_client: Annotated[genai.client.Client | None, Depends(get_genai_client)],
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    speed_mode: str = Form("normal")
):
    """Handles the SRT file upload, translation orchestration, and response."""
    logger.info(f"Received request for /translate for target language '{target_lang}' with speed mode '{speed_mode}'")

    # Client Check (moved up slightly for clarity)
    # Check if the client is needed based on speed_mode and config
    client_required = speed_mode != "mock" and config.ai_provider == "google-gemini"

    if client_required and genai_client is None:
        # This covers two cases: provider is gemini but init failed, OR provider is not gemini
        # but speed_mode requires it (which shouldn't happen with proper config, but good to check)
        if config.ai_provider != "google-gemini":
             logger.error("Translation request failed: AI provider '%s' does not support non-mock translation.", config.ai_provider)
             raise HTTPException(
                 status_code=501, # Not Implemented or 503 Service Unavailable?
                 detail=f"Service Unavailable: AI provider '{config.ai_provider}' does not support non-mock translation."
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

    if target_lang not in config.target_languages:
        logger.warning(f"Translation request failed: Invalid target language '{target_lang}'.")
        raise ValidationError(f"Invalid target language: {target_lang}. Available: {', '.join(config.target_languages)}")

    # Secure filename and prepare temporary file path
    original_filename = secure_filename(file.filename)
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, original_filename)

    try:
        # Save uploaded file
        content = await file.read()
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(content)
        logger.debug(f"Saved uploaded file temporarily to: {temp_file_path}")

        # Workflow Orchestration
        logger.info(f"Starting translation workflow for {original_filename} to {target_lang} ({speed_mode} mode)")

        # 1. Parse SRT
        logger.debug("Parsing SRT file...")
        subtitle_chunks: list[list[SubtitleBlock]] = parse_srt(
            temp_file_path, config.chunk_max_blocks
        )
        logger.info(f"Parsed SRT into {len(subtitle_chunks)} chunk(s).")

        # 2. Detect Context
        logger.debug("Detecting context...")
        # Pass the potentially None client - detect_context should handle mock mode without it
        context: str = detect_context(
            subtitle_chunks, speed_mode, genai_client, config # Pass client here
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
            genai_client=genai_client, # Pass client here
            config=config
        )
        logger.info("Finished translating chunks.")

        # 4. Reassemble SRT
        reassembled_bytes: bytes = reassemble_srt(subtitle_chunks)
        logger.info("Reassembled translated SRT.")

        # Response Generation
        logger.debug("Preparing file response...")
        output_buffer = io.BytesIO(reassembled_bytes)
        output_filename = f"{Path(original_filename).stem}_{target_lang}.srt"

        logger.info(f"Sending translated file: {output_filename}")
        return StreamingResponse(
            output_buffer,
            media_type='text/srt',
            headers={
                'Content-Disposition': f'attachment; filename="{output_filename}"'
            }
        )

    finally:
        # Clean up the temporary file and directory
        try:
            os.remove(temp_file_path)
            os.rmdir(temp_dir)
            logger.debug(f"Cleaned up temporary file and directory: {temp_dir}")
        except OSError as e:
            logger.error(f"Error cleaning up temporary file {temp_file_path}: {e}")