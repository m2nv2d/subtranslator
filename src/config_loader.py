# src/config_loader.py
import os
import sys
import logging
from typing import List
from dotenv import load_dotenv
from pathlib import Path

# Use relative import as models.py is in the same package (src)
from .models import Config

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config() -> Config:
    """
    Loads configuration from a .env file located in the project root,
    validates required fields, provides defaults for optional fields,
    and returns a populated Config object.
    """
    # Determine the project root directory (one level up from src)
    project_root = Path(__file__).resolve().parent.parent
    dotenv_path = project_root / '.env'

    # Load environment variables from .env file if it exists
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path, override=True)
        logging.info(f"Loaded environment variables from: {dotenv_path}")
    else:
        logging.warning(f".env file not found at: {dotenv_path}. Using environment variables or defaults.")

    # --- Subtask 3: Handle Mandatory Variable (GEMINI_API_KEY) ---
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logging.error("Mandatory environment variable 'GEMINI_API_KEY' not found or empty.")
        sys.exit("Error: Missing mandatory 'GEMINI_API_KEY' in environment or .env file. Exiting.")

    # --- Subtask 4: Handle Optional Variables with Defaults ---

    # Target Languages (List[str], comma-separated)
    default_target_languages = ["Vietnamese", "French"]
    target_languages_str = os.getenv("TARGET_LANGUAGES", ",".join(default_target_languages))
    try:
        # Strip whitespace from each language name and filter out empty strings
        target_languages = [lang.strip() for lang in target_languages_str.split(',') if lang.strip()]
        if not target_languages: # Handle case where string is empty or only commas/whitespace
             target_languages = default_target_languages
             logging.warning(f"TARGET_LANGUAGES was empty or invalid after parsing, using default: {default_target_languages}")
    except Exception as e:
        logging.warning(f"Error parsing TARGET_LANGUAGES='{target_languages_str}'. Using default: {default_target_languages}. Error: {e}")
        target_languages = default_target_languages

    # Chunk Max Blocks (int)
    default_chunk_max_blocks = 100
    chunk_max_blocks = default_chunk_max_blocks
    try:
        chunk_max_blocks_str = os.getenv("CHUNK_MAX_BLOCKS")
        if chunk_max_blocks_str is not None:
            parsed_value = int(chunk_max_blocks_str)
            if parsed_value > 0:
                chunk_max_blocks = parsed_value
            else:
                logging.warning(f"CHUNK_MAX_BLOCKS must be positive, got '{chunk_max_blocks_str}'. Using default: {default_chunk_max_blocks}")
    except (ValueError, TypeError):
        logging.warning(f"Invalid format for CHUNK_MAX_BLOCKS='{os.getenv('CHUNK_MAX_BLOCKS')}'. Using default: {default_chunk_max_blocks}")

    # Retry Max Attempts (int)
    default_retry_max_attempts = 6
    retry_max_attempts = default_retry_max_attempts
    try:
        retry_max_attempts_str = os.getenv("RETRY_MAX_ATTEMPTS")
        if retry_max_attempts_str is not None:
            parsed_value = int(retry_max_attempts_str)
            if parsed_value >= 0:
                 retry_max_attempts = parsed_value
            else:
                 logging.warning(f"RETRY_MAX_ATTEMPTS cannot be negative, got '{retry_max_attempts_str}'. Using default: {default_retry_max_attempts}")

    except (ValueError, TypeError):
        logging.warning(f"Invalid format for RETRY_MAX_ATTEMPTS='{os.getenv('RETRY_MAX_ATTEMPTS')}'. Using default: {default_retry_max_attempts}")

    # Log Level (str)
    default_log_level = "INFO"
    log_level = os.getenv("LOG_LEVEL", default_log_level).upper()
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_log_levels:
        logging.warning(f"Invalid LOG_LEVEL='{os.getenv('LOG_LEVEL')}'. Must be one of {valid_log_levels}. Using default: {default_log_level}")
        log_level = default_log_level

    # --- Subtask 5: Populate and Return Config Object ---
    config = Config(
        gemini_api_key=gemini_api_key,
        target_languages=target_languages,
        chunk_max_blocks=chunk_max_blocks,
        retry_max_attempts=retry_max_attempts,
        log_level=log_level,
    )

    logging.info("Configuration loaded successfully.")
    return config
