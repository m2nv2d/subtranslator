from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.exceptions import HTTPException
import asyncio
import io
import logging
import os
from pathlib import Path
from tenacity import RetryError
from google import genai

from config_loader import load_config
from exceptions import (
    ValidationError, 
    ParsingError, 
    ContextDetectionError, 
    ChunkTranslationError, 
    GenAIClientInitError
)
from gemini_helper import init_genai_client
from parser import parse_srt
from context_detector import detect_context
from chunk_translator import translate_all_chunks
from reassembler import reassemble_srt

# Load configuration
config = load_config()

# Configure logging
logging.basicConfig(
    level=config.log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create Flask app instance
app = Flask(__name__)

# Initialize shared Gemini client
genai_client = None
try:
    genai_client = init_genai_client(config)
    logging.info("Gemini Client initialized successfully.")
except Exception as e:
    logging.critical(f"Failed to initialize Gemini Client: {e}")
    raise RuntimeError("Critical component (Gemini Client) failed to initialize.") from e

# Error Handlers
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": str(e)}), 400

@app.errorhandler(ParsingError)
def handle_parsing_error(e):
    return jsonify({"error": str(e)}), 422

@app.errorhandler(ContextDetectionError)
def handle_context_detection_error(e):
    return jsonify({"error": f"Failed to detect context: {str(e)}"}), 500

@app.errorhandler(ChunkTranslationError)
def handle_chunk_translation_error(e):
    return jsonify({"error": f"Failed during translation: {str(e)}"}), 500

@app.errorhandler(RetryError)
def handle_retry_error(e):
    return jsonify({"error": f"Operation failed after multiple retries: {str(e)}"}), 504

@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify({"error": str(e)}), e.code

@app.errorhandler(Exception)
def handle_generic_error(e):
    logging.exception("An unexpected error occurred")
    return jsonify({"error": "An unexpected error occurred"}), 500

# Frontend route
@app.route('/')
def index():
    return render_template('index.html', languages=config.target_languages)

# Translation route
@app.route('/translate', methods=['POST'])
def translate():
    # Check if Gemini client is available
    if genai_client is None:
        return jsonify({
            "error": "Translation service is unavailable due to initialization failure."
        }), 503

    try:
        # Get uploaded file
        file = request.files.get('file')
        if not file:
            raise ValidationError("No file provided")

        # Get and validate target language
        target_lang = request.form.get('target_lang')
        if not target_lang:
            raise ValidationError("Target language not specified")
        if target_lang not in config.target_languages:
            raise ValidationError(f"Unsupported target language: {target_lang}")

        # Get speed mode with default
        speed_mode = request.form.get('speed_mode', 'normal')
        if speed_mode not in ['fast', 'normal']:
            speed_mode = 'normal'

        # Save file temporarily
        temp_file = Path(app.instance_path) / file.filename
        os.makedirs(app.instance_path, exist_ok=True)
        file.save(temp_file)

        try:
            # Parse SRT file
            subtitle_chunks = parse_srt(str(temp_file), config.chunk_max_blocks)

            # Detect context (using mock mode for now)
            context = detect_context(
                sub=subtitle_chunks,
                speed_mode='mock',  # Force mock mode for this task
                genai_client=genai_client,
                config=config
            )

            # Translate chunks
            asyncio.run(translate_all_chunks(
                context=context,
                sub=subtitle_chunks,
                target_lang=target_lang,
                speed_mode=speed_mode,
                genai_client=genai_client,
                config=config
            ))

            # Reassemble the translated SRT
            translated_content = reassemble_srt(subtitle_chunks)

            # Create in-memory file
            buffer = io.BytesIO(translated_content)

            # Generate output filename
            original_name = os.path.splitext(file.filename)[0]
            output_filename = f"{original_name}_{target_lang}.srt"

            return send_file(
                buffer,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/x-subrip'
            )

        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()

    except Exception as e:
        # Let the error handlers deal with specific exceptions
        raise

if __name__ == '__main__':
    app.run(debug=True)