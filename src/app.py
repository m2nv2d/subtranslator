import os
import os
import io
import logging
import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException, InternalServerError
from tenacity import RetryError
from google import genai

import config_loader, models, exceptions, parser, gemini_helper, context_detector, chunk_translator, reassembler

# Load configuration
try:
    config = config_loader.load_config()
except Exception as e:
    # Log critical error during startup if config fails
    logging.basicConfig(level=logging.ERROR) # Basic config for logging the error itself
    logging.critical(f"Failed to load configuration: {e}", exc_info=True)
    # Exit or raise a more specific startup error if desired
    raise RuntimeError(f"Application startup failed: Could not load configuration. Error: {e}")

# Configure logging based on loaded config
log_level_name = config.log_level.upper()
log_level = getattr(logging, log_level_name, logging.INFO) # Default to INFO if invalid
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.info(f"Logging configured with level: {log_level_name}")

# Create Flask app instance
app = Flask(__name__, template_folder='../templates')
logger.info("Flask application instance created.")

# AI Client Initialization

genai_client: genai.client.Client | None = None
try:
    genai_client = gemini_helper.init_genai_client(config)
    if genai_client:
        logger.info("Google Generative AI client initialized successfully.")
    else:
        raise RuntimeError("Application startup failed: GenAI client initialization returned None.")
except exceptions.GenAIClientInitError as e:
    logger.critical(f"Failed to initialize Google Generative AI client: {e}", exc_info=True)
    raise RuntimeError(f"Application startup failed: Critical component (GenAI Client) failed to initialize. Error: {e}")
except Exception as e:
    # Catch any other unexpected errors during client init
    logger.critical(f"An unexpected error occurred during GenAI client initialization: {e}", exc_info=True)
    raise RuntimeError(f"Application startup failed due to unexpected error during GenAI client init. Error: {e}")


# Application-Wide Error Handling

@app.errorhandler(exceptions.ValidationError)
def handle_validation_error(error):
    logger.warning(f"Validation Error: {error}")
    response = jsonify(error=str(error))
    response.status_code = 400 # Bad Request
    return response

@app.errorhandler(exceptions.ParsingError)
def handle_parsing_error(error):
    logger.error(f"Parsing Error: {error}", exc_info=True)
    response = jsonify(error=str(error))
    response.status_code = 422 # Unprocessable Entity
    return response

@app.errorhandler(exceptions.ContextDetectionError)
def handle_context_detection_error(error):
    logger.error(f"Context Detection Error: {error}", exc_info=True)
    response = jsonify(error=f"Failed to detect context: {error}")
    response.status_code = 500 # Internal Server Error
    return response

@app.errorhandler(exceptions.ChunkTranslationError)
def handle_chunk_translation_error(error):
    logger.error(f"Chunk Translation Error: {error}", exc_info=True)
    response = jsonify(error=f"Failed during translation process: {error}")
    response.status_code = 500 # Internal Server Error
    return response

@app.errorhandler(RetryError)
def handle_retry_error(error):
    logger.error(f"Retry Error: Operation failed after multiple attempts: {error}", exc_info=True)
    response = jsonify(error="Operation failed after multiple retries. Please try again later.")
    response.status_code = 504 # Gateway Timeout
    return response

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle Werkzeug HTTP exceptions."""
    logger.warning(f"HTTP Exception: {e.code} {e.name} - {e.description}")
    response = jsonify(error=f"{e.name}: {e.description}")
    response.status_code = e.code
    return response

@app.errorhandler(Exception)
def handle_generic_exception(error):
    """Generic fallback handler for unexpected errors."""
    logger.critical(f"Unhandled Exception: {error}", exc_info=True)
    # Ensure we don't expose sensitive details in the generic error
    response = jsonify(error="An unexpected internal server error occurred.")
    response.status_code = 500 # Internal Server Error
    return response


# Favicon Route
@app.route('/favicon.ico')
def favicon():
    """Serves the favicon."""
    static_dir = os.path.join(app.root_path, '..', 'templates', 'static')
    return send_from_directory(static_dir, 'favicon.ico', mimetype='image/png')

# Frontend Route (GET /)

@app.route('/', methods=['GET'])
def index():
    """Renders the main upload form."""
    logger.debug("Serving index page.")
    return render_template('index.html', languages=config.target_languages)

# Frontend Route (GET /)

@app.route('/translate', methods=['POST'])
def translate():
    """Handles the subtitle translation request."""
    logger.info("Received request for /translate")

    # Client Check
    if genai_client is None:
        logger.error("Translation request failed: GenAI client not available.")
        response = jsonify(error="Service temporarily unavailable due to configuration issue.")
        response.status_code = 503 # Service Unavailable
        return response

    # Error Boundary (covered by global handlers, but can add specific logic here if needed)
    try:
        # Input Processing
        if 'file' not in request.files:
            raise exceptions.ValidationError("No file part in the request.")

        file = request.files['file']
        if file.filename == '':
            raise exceptions.ValidationError("No selected file.")

        target_lang = request.form.get('target_lang')
        speed_mode = request.form.get('speed_mode', 'normal').lower() # Default to 'normal'

        if not target_lang:
            raise exceptions.ValidationError("Target language not specified.")

        # Validate target_lang
        if target_lang not in config.target_languages:
            logger.warning(f"Invalid target language selected: {target_lang}")
            raise exceptions.ValidationError(f"Invalid target language: '{target_lang}'. Available languages: {', '.join(config.target_languages)}")

        logger.info(f"Processing file: {file.filename}, Target Language: {target_lang}, Speed Mode: {speed_mode}")

        # Save uploaded file temporarily to pass its path to the parser
        # Using NamedTemporaryFile for automatic cleanup
        temp_file = None
        try:
            temp_file = NamedTemporaryFile(delete=False, suffix=".srt", prefix="upload_")
            file.save(temp_file.name)
            temp_file_path = temp_file.name
            logger.debug(f"Saved uploaded file temporarily to: {temp_file_path}")
        finally:
            if temp_file:
                temp_file.close() # Close the file handle

        # Workflow Orchestration
        # Parse SRT
        logger.debug("Parsing SRT file...")
        subtitle_chunks = parser.parse_srt(temp_file_path, config.chunk_max_blocks)
        logger.info(f"Parsed SRT into {len(subtitle_chunks)} chunks.")

        # Detect Context
        logger.debug("Detecting context...")
        context = context_detector.detect_context(subtitle_chunks, speed_mode, genai_client, config)
        logger.info(f"Detected context (mode: {speed_mode}): {context}")

        # Translate Chunks
        logger.debug("Translating chunks...")
        # Run the async translation function within the sync Flask route
        asyncio.run(chunk_translator.translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=speed_mode,
            genai_client=genai_client,
            config=config
        ))
        logger.info("Finished translation step")

        # Reassemble SRT
        reassembled_bytes = reassembler.reassemble_srt(subtitle_chunks)
        logger.info("Reassembled translated SRT.")

        # Response Generation
        original_filename = Path(file.filename).stem
        download_filename = f"{original_filename}_{target_lang}.srt"
        buffer = io.BytesIO(reassembled_bytes)
        buffer.seek(0)

        logger.info(f"Sending translated file: {download_filename}")
        return send_file(
            buffer,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/plain' # Use text/plain or application/x-subrip for SRT
        )

    finally:
        # Clean up the temporary file if it was created
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except OSError as e:
                logger.error(f"Error removing temporary file {temp_file_path}: {e}")


# Application Runner

if __name__ == "__main__":
    logger.info("Starting Flask development server.")
    app.run(debug=True, host='0.0.0.0', port=5000)
