import asyncio
import io
import logging
import os
import tempfile
from pathlib import Path

from google import genai
from flask import (Flask, jsonify, render_template, request,
                   send_file, send_from_directory)
from tenacity import RetryError
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.utils import secure_filename

import chunk_translator, config_loader, context_detector, exceptions, gemini_helper, models, parser, reassembler

# Load configuration
try:
    config = config_loader.load_config()
except exceptions.ConfigError as e:
    logging.basicConfig(level=logging.ERROR)
    logging.critical(f"Failed to load configuration: {e}")
    # Exit if config fails to load, as the app cannot run
    raise SystemExit(f"CRITICAL: Configuration loading failed - {e}") from e

# Configure logging
log_level_str = config.log_level.upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app instance
app = Flask(__name__)
app.static_folder = 'static' # Explicitly set static folder

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# AI Client Initialization
genai_client: genai.client.Client | None = None
try:
    genai_client = gemini_helper.init_genai_client(config)
    logger.info("Generative AI client initialized successfully.")
except exceptions.GenAIClientInitError as e:
    logger.critical(f"Failed to initialize Generative AI client: {e}")
    # Raising RuntimeError to halt startup if the client is essential
    raise RuntimeError(f"Critical component failure: {e}") from e
except Exception as e:
    logger.critical(f"An unexpected error occurred during Generative AI client initialization: {e}", exc_info=True)
    raise RuntimeError(f"Unexpected critical component failure: {e}") from e

# Application-Wide Error Handling
@app.errorhandler(exceptions.ValidationError)
def handle_validation_error(error: exceptions.ValidationError):
    logger.warning(f"Validation Error: {error}")
    response = jsonify(error=str(error))
    response.status_code = 400  # Bad Request
    return response

@app.errorhandler(exceptions.ParsingError)
def handle_parsing_error(error: exceptions.ParsingError):
    logger.error(f"Parsing Error: {error}", exc_info=True)
    response = jsonify(error=str(error))
    response.status_code = 422  # Unprocessable Entity
    return response

@app.errorhandler(exceptions.ContextDetectionError)
def handle_context_detection_error(error: exceptions.ContextDetectionError):
    logger.error(f"Context Detection Error: {error}", exc_info=True)
    response = jsonify(error=str(error))
    response.status_code = 500 # Internal Server Error (as it's part of backend processing)
    return response

@app.errorhandler(exceptions.ChunkTranslationError)
def handle_chunk_translation_error(error: exceptions.ChunkTranslationError):
    logger.error(f"Chunk Translation Error: {error}", exc_info=True)
    response = jsonify(error=str(error))
    response.status_code = 500 # Internal Server Error
    return response

@app.errorhandler(RetryError)
def handle_retry_error(error: RetryError):
    logger.error(f"Retry Error after multiple attempts: {error}", exc_info=True)
    response = jsonify(error="Service temporarily unavailable after multiple retries.")
    response.status_code = 504  # Gateway Timeout
    return response

@app.errorhandler(HTTPException)
def handle_http_exception(error: HTTPException):
    """Handles exceptions raised by Flask/Werkzeug (e.g., 404, 405, 413)."""
    logger.warning(f"HTTP Exception: {error.code} {error.name} - {error.description}")
    response = jsonify(error=f"{error.name}: {error.description}")
    response.status_code = error.code or 500
    return response

@app.errorhandler(Exception)
def handle_generic_exception(error: Exception):
    """Generic fallback handler."""
    logger.exception(f"Unhandled Exception: {error}")
    # For other generic exceptions, provide a standard message.
    error_message = "An unexpected internal server error occurred."
    status_code = 500
    if isinstance(error, InternalServerError) and hasattr(error, 'description'):
        # Use Werkzeug's description if available for 500 errors
        error_message = error.description
    elif not isinstance(error, HTTPException): # Avoid overriding specific HTTP error messages
        pass # Keep the generic message

    response = jsonify(error=error_message)
    response.status_code = status_code
    return response


# Frontend Route (GET /)
@app.route('/', methods=['GET'])
def index():
    """Renders the main upload form."""
    logger.debug("Serving index page.")
    return render_template('index.html', languages=config.target_languages)


# Translation Route (POST /translate) - Orchestration Logic
@app.route('/translate', methods=['POST'])
def translate_srt():
    """Handles the SRT file upload, translation orchestration, and response."""
    logger.info("Received request for /translate")

    # Client Check
    if genai_client is None:
        logger.error("Translation request failed: Generative AI client not initialized.")
        # Using 503 Service Unavailable as the core dependency is missing
        response = jsonify(error="Service Unavailable: Translation backend not ready.")
        response.status_code = 503
        return response

    # Input Processing
    if 'file' not in request.files:
        logger.warning("Translation request failed: No file part.")
        raise exceptions.ValidationError("No file part in the request.")

    file = request.files['file']
    if file.filename == '':
        logger.warning("Translation request failed: No selected file.")
        raise exceptions.ValidationError("No file selected.")

    if not file or not file.filename.lower().endswith('.srt'):
         logger.warning(f"Translation request failed: Invalid file type '{file.filename}'.")
         raise exceptions.ValidationError("Invalid file type. Please upload an SRT file.")

    # Retrieve form data
    target_lang = request.form.get('target_lang')
    speed_mode = request.form.get('speed_mode', 'normal') # Default to 'normal'
    logger.debug(f"Received file: {file.filename}, target_lang: {target_lang}, speed_mode: {speed_mode}")

    # Validate target_lang
    if not target_lang:
        logger.warning("Translation request failed: Target language not specified.")
        raise exceptions.ValidationError("Target language must be specified.")
    if target_lang not in config.target_languages:
        logger.warning(f"Translation request failed: Invalid target language '{target_lang}'.")
        raise exceptions.ValidationError(f"Invalid target language: {target_lang}. Available: {', '.join(config.target_languages)}")

    # Secure filename and prepare temporary file path
    original_filename = secure_filename(file.filename)
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, original_filename)
    logger.debug(f"Saving uploaded file temporarily to: {temp_file_path}")
    file.save(temp_file_path)

    try:
        # Workflow Orchestration
        logger.info(f"Starting translation workflow for {original_filename} to {target_lang} ({speed_mode} mode)")

        # 1. Parse SRT
        logger.debug("Parsing SRT file...")
        subtitle_chunks: list[list[models.SubtitleBlock]] = parser.parse_srt(
            temp_file_path, config.chunk_max_blocks
        )
        logger.info(f"Parsed SRT into {len(subtitle_chunks)} chunk(s).")

        # 2. Detect Context
        logger.debug("Detecting context...")
        # Pass speed_mode to allow mock implementation if needed
        context: str = context_detector.detect_context(
            subtitle_chunks, speed_mode, genai_client, config
        )
        logger.info(f"Detected context: '{context[:100]}...'")

        # 3. Translate Chunks
        logger.debug("Translating chunks...")
        asyncio.run(chunk_translator.translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=speed_mode,
            genai_client=genai_client,
            config=config
        ))
        logger.info("Finished translating chunks.")

        # 4. Reassemble SRT
        reassembled_bytes: bytes = reassembler.reassemble_srt(subtitle_chunks)
        logger.info("Reassembled translated SRT.")

        # Response Generation
        logger.debug("Preparing file response...")
        output_buffer = io.BytesIO(reassembled_bytes)
        output_filename = f"{Path(original_filename).stem}_{target_lang}.srt"

        logger.info(f"Sending translated file: {output_filename}")
        return send_file(
            output_buffer,
            mimetype='text/srt',
            as_attachment=True,
            download_name=output_filename
        )

    finally:
        # Clean up the temporary file and directory
        try:
            os.remove(temp_file_path)
            os.rmdir(temp_dir)
            logger.debug(f"Cleaned up temporary file and directory: {temp_dir}")
        except OSError as e:
            logger.error(f"Error cleaning up temporary file {temp_file_path}: {e}")


# Application Runner
if __name__ == "__main__":
    is_debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask development server on port {port} (Debug: {is_debug})...")
    app.run(debug=is_debug, host='0.0.0.0', port=port)