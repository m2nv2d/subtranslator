import functools
import logging
import sys

from core.config import get_settings, Settings
from fastapi import Depends, HTTPException
from google import genai
from pydantic import ValidationError as PydanticValidationError

from translator.exceptions import GenAIClientInitError
from translator.gemini_helper import init_genai_client

logger = logging.getLogger(__name__)


@functools.lru_cache()
def get_application_settings() -> Settings:
    """Dependency provider for the application settings.

    Loads the configuration using the Pydantic Settings model and caches the result.
    Raises HTTPException 500 if configuration loading fails.
    """
    try:
        logger.info("Loading application configuration...")
        # Get the settings from the Pydantic model
        settings = get_settings()
        
        # Configure logging
        log_level_str = settings.LOG_LEVEL.upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True
        )
        logger.info(f"Logging reconfigured to level {log_level_str}.")
        
        logger.info("Configuration loaded successfully.")
        return settings
    except PydanticValidationError as e:
        logger.critical(f"Pydantic Validation Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server Configuration Error: {e}"
        )
    except Exception as e:
        logger.critical(f"Failed to load application configuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Server Configuration Error: Failed to load configuration."
        )

def get_genai_client(settings: Settings = Depends(get_application_settings)) -> genai.client.Client | None:
    """Dependency provider for the Generative AI client.

    Initializes the client based on the configuration.
    Returns None if the provider is not 'google-gemini' or if initialization fails.
    """
    if settings.AI_PROVIDER != "google-gemini":
        logger.warning(f"AI provider is '{settings.AI_PROVIDER}', not 'google-gemini'. AI client will not be initialized.")
        return None

    logger.info("Initializing Generative AI client...")
    try:
        client = init_genai_client(settings)
        logger.info("Generative AI client initialized successfully.")
        return client
    except GenAIClientInitError as e:
        # Log the error, but return None as the client is unavailable.
        # The route handler will be responsible for checking None and raising HTTP 503.
        logger.error(f"Failed to initialize Generative AI client: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during Generative AI client initialization: {e}", exc_info=True)
        return None 