#!/usr/bin/env python3
"""
Manual test script to verify that Pydantic Settings correctly loads
configuration from the actual .env file.

Usage:
    1. Make sure you have a .env file in the project root
    2. Run this script with: uv run tests/manual/test_pydantic_config.py
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to sys.path to enable absolute imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from core.config import Settings


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Testing Pydantic Settings configuration loading from .env file")
    
    # Find the actual .env file
    env_path = project_root / '.env'
    
    if not env_path.exists():
        logger.error(f"Error: .env file not found at {env_path}")
        logger.info("Please create a .env file in the project root with the necessary configuration.")
        sys.exit(1)
    
    logger.info(f"Using .env file at: {env_path}")
    
    try:
        # Load settings directly
        settings = Settings()
        
        # Log the loaded settings
        logger.info("Configuration loaded successfully!")
        logger.info(f"AI Provider: {settings.AI_PROVIDER}")
        logger.info(f"API Key: {'[REDACTED]' if settings.AI_API_KEY else 'Not provided'}")
        logger.info(f"Fast Model: {settings.FAST_MODEL}")
        logger.info(f"Normal Model: {settings.NORMAL_MODEL}")
        logger.info(f"Target Languages: {settings.TARGET_LANGUAGES}")
        logger.info(f"Chunk Max Blocks: {settings.CHUNK_MAX_BLOCKS}")
        logger.info(f"Retry Max Attempts: {settings.RETRY_MAX_ATTEMPTS}")
        logger.info(f"Log Level: {settings.LOG_LEVEL}")
        logger.info(f"Max Concurrent Translations: {settings.MAX_CONCURRENT_TRANSLATIONS}")
        
        logger.info("\nConfiguration test completed successfully!")
    
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        sys.exit(1) 