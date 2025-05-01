import functools
import logging
import sys
import asyncio

from core.config import get_settings, Settings
from fastapi import Depends, HTTPException
from google import genai
from pydantic import ValidationError as PydanticValidationError

from translator.exceptions import GenAIClientInitError
from translator.gemini_helper import init_genai_client

logger = logging.getLogger(__name__)

# Global semaphore instance, initialized later in get_translation_semaphore
_translation_semaphore: asyncio.Semaphore | None = None

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
        logger.error(f"Failed to initialize Generative AI client: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during Generative AI client initialization: {e}", exc_info=True)
        return None 

def get_translation_semaphore(settings: Settings = Depends(get_application_settings)) -> asyncio.Semaphore:
    """Dependency provider for the global translation semaphore.

    Initializes the semaphore on first call using the configured limit
    and returns the same instance on subsequent calls.
    """
    global _translation_semaphore
    if _translation_semaphore is None:
        limit = settings.MAX_CONCURRENT_TRANSLATIONS
        logger.info(f"Initializing global translation semaphore with limit: {limit}")
        _translation_semaphore = asyncio.Semaphore(limit)
    return _translation_semaphore 