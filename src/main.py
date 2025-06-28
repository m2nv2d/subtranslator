import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from tenacity import RetryError

from translator import (
    ValidationError,
    ParsingError,
    ContextDetectionError,
    ChunkTranslationError,
)

from core.errors import create_error_response
from core.config import get_settings

# Import the router
from routers.translate import router as translate_router

# Load settings - fail fast if configuration is invalid
try:
    settings = get_settings()
    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
except Exception as e:
    print(f"FATAL: Failed to load application configuration: {e}")
    print("Please check your environment variables and .env file configuration.")
    print("Application cannot start without valid configuration.")
    exit(1)

# Configure logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Use force=True to ensure handlers are updated if basicConfig was called implicitly before
)
logger = logging.getLogger(__name__)
logger.info(f"Logging configured to level {log_level_str}.")

# Create FastAPI app instance
app = FastAPI(title="Subtranslator")

# Middleware to ensure sessions have a session_id
@app.middleware("http")
async def ensure_session_id(request: Request, call_next):
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
        logger.debug(f"Assigned new session ID: {request.session['session_id']}")
    
    response = await call_next(request)
    return response

# Add session middleware (added after custom middleware so it executes first)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie="session_id"
)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

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