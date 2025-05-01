import os
import logging
import json
from pathlib import Path
from typing import List, Optional, Any, Annotated

from pydantic import model_validator, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode


class Settings(BaseSettings):
    """
    Application configuration settings using Pydantic BaseSettings.
    Loads and validates environment variables from a .env file.
    """
    # Required settings
    AI_PROVIDER: str = Field(default="google-gemini", description="AI provider to use for translation")
    AI_API_KEY: str = Field(..., description="API key for the AI provider")
    FAST_MODEL: str = Field(default="gemini-2.5-flash-preview-04-17", description="Model name for fast translations")
    NORMAL_MODEL: str = Field(default="gemini-2.5-pro-preview-03-25", description="Model name for normal translations")
    
    # Optional settings with defaults
    TARGET_LANGUAGES: Annotated[List[str], NoDecode] = Field(
        default=["Vietnamese", "French"],
        description="List of target languages available for translation"
    )
    CHUNK_MAX_BLOCKS: int = Field(
        default=100,
        description="Maximum number of subtitle blocks per chunk",
        gt=0
    )
    RETRY_MAX_ATTEMPTS: int = Field(
        default=4,
        description="Maximum number of retry attempts for failed operations",
        ge=0
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    MAX_CONCURRENT_TRANSLATIONS: int = Field(
        default=10,
        description="Maximum number of concurrent translation tasks allowed application-wide",
        gt=0
    )
    
    # Configure .env file support
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @model_validator(mode="before")
    @classmethod
    def validate_target_languages(cls, values: dict) -> dict:
        """
        Validate TARGET_LANGUAGES from environment variables or .env file.
        This catches the raw string value before it's converted to a list.
        """
        # Check for both the env var key and the direct key
        target_langs_key = 'TARGET_LANGUAGES'
        target_langs_env = os.environ.get(target_langs_key)
        
        if target_langs_env:
            # Set value based on the environment variable
            langs = [lang.strip() for lang in target_langs_env.split(',') if lang.strip()]
            values[target_langs_key] = langs if langs else ["Vietnamese", "French"]
        elif target_langs_key in values and isinstance(values[target_langs_key], str):
            # Set value based on the .env file string
            langs = [lang.strip() for lang in values[target_langs_key].split(',') if lang.strip()]
            values[target_langs_key] = langs if langs else ["Vietnamese", "French"]
        
        return values
    
    @field_validator("TARGET_LANGUAGES")
    @classmethod
    def validate_languages(cls, value):
        """Ensure TARGET_LANGUAGES is not empty"""
        if not value:
            return ["Vietnamese", "French"]
        return value
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate that LOG_LEVEL is one of the allowed values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level = v.upper()
        if level not in valid_levels:
            logging.warning(f"Invalid LOG_LEVEL='{v}'. Must be one of {valid_levels}. Using default: INFO")
            return "INFO"
        return level
    
    @model_validator(mode="after")
    def validate_model_names(self):
        """Validate model names based on the AI provider."""
        if self.AI_PROVIDER == "google-gemini":
            # For Google Gemini, ensure model names are provided
            if not self.FAST_MODEL or not self.NORMAL_MODEL:
                raise ValueError("FAST_MODEL and NORMAL_MODEL must be specified when using google-gemini provider")
        
        return self


def get_settings() -> Settings:
    """
    Load settings from environment variables and .env file.
    """
    try:
        # Find project root to locate .env file
        project_root = Path(__file__).resolve().parent.parent.parent
        dotenv_path = project_root / '.env'
        
        # Initialize settings
        settings = Settings(_env_file=dotenv_path if dotenv_path.is_file() else None)
        return settings
    except Exception as e:
        logging.error(f"Failed to load settings: {e}")
        raise 