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
    SubtitleBlock,
    ValidationError,
    ParsingError,
    ContextDetectionError,
    ChunkTranslationError,
    GenAIClientInitError,
)

from core.config import Settings
from core.errors import ErrorDetail, create_error_response
from core.dependencies import get_application_settings, get_genai_client

# Import the router
from routers.translate import router as translate_router

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

# Include the router
app.include_router(translate_router)

# Exception Handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation Error: {exc}")
    return JSONResponse(
        status_code=400,
        content=create_error_response(str(exc))
    )

@app.exception_handler(ParsingError)
async def parsing_error_handler(request: Request, exc: ParsingError):
    logger.error(f"Parsing Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=422,
        content=create_error_response(str(exc))
    )

@app.exception_handler(ContextDetectionError)
async def context_detection_error_handler(request: Request, exc: ContextDetectionError):
    logger.error(f"Context Detection Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=create_error_response(str(exc))
    )

@app.exception_handler(ChunkTranslationError)
async def chunk_translation_error_handler(request: Request, exc: ChunkTranslationError):
    logger.error(f"Chunk Translation Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=create_error_response(str(exc))
    )

@app.exception_handler(RetryError)
async def retry_error_handler(request: Request, exc: RetryError):
    logger.error(f"Retry Error after multiple attempts: {exc}", exc_info=True)
    return JSONResponse(
        status_code=504,
        content=create_error_response("Service temporarily unavailable after multiple retries.")
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.detail)
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=create_error_response("An unexpected internal server error occurred.")
    )

# The route handler functions for / and /translate have been moved to src/routers/translate.py
# and their implementation has been replaced with the router include above