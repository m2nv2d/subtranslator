import functools
import logging
import sys
import asyncio

from core.config import get_settings, Settings
from core.stats import AppStatsStore
from core.rate_limiter import RateLimiter, get_rate_limiter, check_global_request_limit
from core.providers import AIProvider, create_provider
from fastapi import Depends, HTTPException
from pydantic import ValidationError as PydanticValidationError

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

@functools.lru_cache()
def get_ai_provider(settings: Settings = Depends(get_application_settings)) -> AIProvider:
    """Dependency provider for the AI provider.

    Initializes the provider based on the configuration.
    Raises HTTPException 500 if provider initialization fails.
    """
    logger.info(f"Initializing AI provider: {settings.AI_PROVIDER}")
    try:
        provider = create_provider(settings)
        logger.info(f"AI provider '{settings.AI_PROVIDER}' initialized successfully.")
        return provider
    except Exception as e:
        logger.error(f"Failed to initialize AI provider '{settings.AI_PROVIDER}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Server Configuration Error: Failed to initialize AI provider '{settings.AI_PROVIDER}': {str(e)}"
        ) 

@functools.lru_cache()
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

@functools.lru_cache()
def get_stats_store() -> AppStatsStore:
    """Dependency provider for the application statistics store.

    Initializes the store on first call and returns the same instance
    on subsequent calls.
    """
    logger.info("Initializing Application Statistics Store...")
    # The store itself handles async operations internally with its lock
    # The provider just needs to return the singleton instance.
    store = AppStatsStore()
    logger.info("Application Statistics Store initialized.")
    return store

def get_application_rate_limiter(settings: Settings = Depends(get_application_settings)) -> RateLimiter:
    """Dependency provider for the application rate limiter.

    Returns the global rate limiter instance initialized with current settings.
    """
    return get_rate_limiter(settings)