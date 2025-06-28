import os
import logging
import json
from pathlib import Path
from typing import Annotated

from pydantic import model_validator, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode


class Settings(BaseSettings):
    """
    Application configuration settings using Pydantic BaseSettings.
    Loads and validates environment variables from a .env file.
    """
    # Required settings
    AI_PROVIDER: str = Field(default="google-gemini", description="AI provider to use for translation")
    AI_API_KEY: str = Field(default="", description="API key for the AI provider")
    FAST_MODEL: str = Field(default="gemini-2.5-flash-preview-04-17", description="Model name for fast translations")
    NORMAL_MODEL: str = Field(default="gemini-2.5-pro-preview-03-25", description="Model name for normal translations")
    
    # Optional settings with defaults
    TARGET_LANGUAGES: Annotated[tuple[str, ...], NoDecode] = Field(
        default=("Vietnamese", "French"),
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
    SESSION_FILE_LIMIT: int = Field(
        default=50,
        description="Maximum number of files that can be uploaded per session",
        gt=0
    )
    SESSION_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for session middleware"
    )
    SHOW_SPEED_SELECTOR: bool = Field(
        default=True,
        description="Whether to show translation speed selector in the UI"
    )
    
    # Configure to read from environment variables only
    model_config = SettingsConfigDict(
        frozen=True,
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True
    )
    
    @model_validator(mode="before")
    @classmethod
    def validate_target_languages(cls, values: dict) -> dict:
        """
        Validate TARGET_LANGUAGES from .env file.
        This catches the raw string value before it's converted to a list.
        """
        target_langs_key = 'TARGET_LANGUAGES'
        
        if target_langs_key in values and isinstance(values[target_langs_key], str):
            # Set value based on the .env file string
            langs = tuple(lang.strip() for lang in values[target_langs_key].split(',') if lang.strip())
            values[target_langs_key] = langs if langs else ("Vietnamese", "French")
        
        return values
    
    @field_validator("TARGET_LANGUAGES")
    @classmethod
    def validate_languages(cls, value):
        """Ensure TARGET_LANGUAGES is not empty"""
        if not value:
            return ("Vietnamese", "French")
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
    
    @field_validator("AI_PROVIDER")
    @classmethod
    def validate_ai_provider(cls, v):
        """Validate that AI_PROVIDER is one of the supported values."""
        valid_providers = ["google-gemini", "openrouter", "mock"]
        if v.lower() not in valid_providers:
            raise ValueError(f"AI_PROVIDER must be one of {valid_providers}, got: {v}")
        return v.lower()
    
    @model_validator(mode="before")
    @classmethod
    def load_provider_specific_config(cls, values: dict) -> dict:
        """Load provider-specific configuration from environment variables."""
        import os
        
        provider = values.get("AI_PROVIDER", os.getenv("AI_PROVIDER", "google-gemini")).lower()
        
        if provider == "google-gemini":
            # Use provider-specific keys first, fall back to generic ones
            values["AI_API_KEY"] = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY", "")
            values["FAST_MODEL"] = os.getenv("GEMINI_FAST_MODEL") or os.getenv("FAST_MODEL", "gemini-2.5-flash-preview-04-17")
            values["NORMAL_MODEL"] = os.getenv("GEMINI_NORMAL_MODEL") or os.getenv("NORMAL_MODEL", "gemini-2.5-pro-preview-03-25")
                
        elif provider == "openrouter":
            # Use provider-specific keys first, fall back to generic ones
            values["AI_API_KEY"] = os.getenv("OPENROUTER_API_KEY") or os.getenv("AI_API_KEY", "")
            values["FAST_MODEL"] = os.getenv("OPENROUTER_FAST_MODEL") or os.getenv("FAST_MODEL", "google/gemini-2.5-flash")
            values["NORMAL_MODEL"] = os.getenv("OPENROUTER_NORMAL_MODEL") or os.getenv("NORMAL_MODEL", "google/gemini-2.5-pro")
        
        return values
    
    @model_validator(mode="after")
    def validate_model_names(self):
        """Validate model names and API key based on the AI provider."""
        if self.AI_PROVIDER == "google-gemini":
            if not self.FAST_MODEL or not self.NORMAL_MODEL:
                raise ValueError("GEMINI_FAST_MODEL and GEMINI_NORMAL_MODEL (or FAST_MODEL and NORMAL_MODEL) must be specified when using google-gemini provider")
            if not self.AI_API_KEY:
                raise ValueError("GEMINI_API_KEY (or AI_API_KEY) is required when using google-gemini provider")
                
        elif self.AI_PROVIDER == "openrouter":
            if not self.AI_API_KEY:
                raise ValueError("OPENROUTER_API_KEY (or AI_API_KEY) is required when using openrouter provider")
                
        elif self.AI_PROVIDER == "mock":
            # For mock provider, API key is optional, models are ignored
            pass
        
        return self


def get_settings() -> Settings:
    """
    Load settings from environment variables.
    Command-line arguments override environment variables.
    
    Raises:
        Exception: If configuration validation fails or required settings are missing.
    """
    # Parse command-line arguments for overrides
    import sys
    import os
    args = sys.argv[1:]  # Skip script name
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--') and '=' in arg:
            # Handle --key=value format
            key, value = arg[2:].split('=', 1)
            os.environ[key.upper()] = value
        elif arg.startswith('--') and i + 1 < len(args) and not args[i + 1].startswith('--'):
            # Handle --key value format
            key = arg[2:].upper()
            value = args[i + 1]
            os.environ[key] = value
            i += 1  # Skip the value argument
        i += 1
    
    # Initialize settings from environment variables - let exceptions propagate
    return Settings() 