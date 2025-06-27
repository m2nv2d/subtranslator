# Configuration Module (`config.py`)

## Module Overview

### Purpose and Responsibilities
The `config.py` module serves as the central configuration management system for the subtranslator application. It handles loading, validating, and providing access to all application settings through environment variables and `.env` files.

### Design Pattern Used
- **Settings Pattern**: Uses Pydantic's `BaseSettings` for configuration management
- **Singleton Pattern**: Configuration is cached using `@functools.lru_cache()` for efficient access
- **Validation Pattern**: Built-in field validation ensures configuration integrity

### Integration Points
- Imported by `dependencies.py` for dependency injection
- Used throughout the application for accessing configuration values
- Integrates with FastAPI's dependency system
- Supports `.env` file loading from project root

## 🔍 Abstraction-Level Reference

### `Settings` Class

```python
class Settings(BaseSettings)
```

**Description**: Main configuration class that loads and validates all application settings using Pydantic BaseSettings.

**Behavior**: 
- Automatically loads configuration from environment variables and `.env` files
- Validates all settings according to defined constraints
- Provides immutable configuration object (frozen=True)
- Handles type conversion and validation automatically

**Configuration Fields**:

#### Required Fields
- `AI_API_KEY: str` - API key for the AI provider (required, no default)

#### Optional Fields with Defaults
- `AI_PROVIDER: str = "google-gemini"` - AI provider to use for translation (supports: google-gemini, openrouter, mock)
- `FAST_MODEL: str = "gemini-2.5-flash-preview-04-17"` - Model for fast translations
- `NORMAL_MODEL: str = "gemini-2.5-pro-preview-03-25"` - Model for normal translations
- `TARGET_LANGUAGES: tuple[str, ...] = ("Vietnamese", "French")` - Available target languages
- `CHUNK_MAX_BLOCKS: int = 100` - Maximum subtitle blocks per chunk (must be > 0)
- `RETRY_MAX_ATTEMPTS: int = 4` - Maximum retry attempts (must be >= 0)
- `LOG_LEVEL: str = "INFO"` - Logging level
- `MAX_CONCURRENT_TRANSLATIONS: int = 10` - Maximum concurrent translations (must be > 0)

**Example Usage**:
```python
# Load settings
settings = Settings()

# Access configuration values
api_key = settings.AI_API_KEY
target_langs = settings.TARGET_LANGUAGES
chunk_size = settings.CHUNK_MAX_BLOCKS
```

**Tips/Notes**:
- Configuration is immutable once loaded (frozen=True)
- Environment variables take precedence over .env file values
- Case-sensitive configuration keys
- Extra configuration keys are ignored

---

### `validate_target_languages` Method

```python
@model_validator(mode="before")
@classmethod
def validate_target_languages(cls, values: dict) -> dict
```

**Description**: Pre-validation method that processes TARGET_LANGUAGES from string format to tuple format.

**Parameters**:
- `values: dict` - Raw configuration values before validation

**Returns**: 
- `dict` - Modified configuration values with TARGET_LANGUAGES converted to tuple

**Behavior**: 
- Parses comma-separated language strings into tuples
- Handles both environment variables and .env file values
- Strips whitespace from language names
- Falls back to default languages if parsing fails

**Example Usage**:
```bash
# Environment variable
export TARGET_LANGUAGES="Spanish,Italian,German"

# .env file
TARGET_LANGUAGES=Spanish,Italian,German
```

**Tips/Notes**:
- Automatically called during Settings initialization
- Handles malformed input gracefully
- Empty language lists default to ("Vietnamese", "French")

---

### `validate_languages` Method

```python
@field_validator("TARGET_LANGUAGES")
@classmethod
def validate_languages(cls, value) -> tuple[str, ...]
```

**Description**: Post-validation method that ensures TARGET_LANGUAGES is not empty.

**Parameters**:
- `value` - The TARGET_LANGUAGES value after initial processing

**Returns**: 
- `tuple[str, ...]` - Validated tuple of language names

**Behavior**: 
- Ensures at least one target language is specified
- Provides default languages if value is empty

**Tips/Notes**:
- Final validation step for TARGET_LANGUAGES
- Cannot be bypassed due to Pydantic validation system

---

### `validate_log_level` Method

```python
@field_validator("LOG_LEVEL")
@classmethod
def validate_log_level(cls, v: str) -> str
```

**Description**: Validates that LOG_LEVEL is one of the standard Python logging levels.

**Parameters**:
- `v: str` - The log level string to validate

**Returns**: 
- `str` - Validated log level in uppercase

**Behavior**: 
- Converts input to uppercase for consistency
- Validates against standard logging levels
- Logs warning and defaults to "INFO" for invalid levels

**Valid Values**: 
- "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

**Example Usage**:
```bash
export LOG_LEVEL=debug  # Automatically converted to "DEBUG"
```

**Tips/Notes**:
- Case-insensitive input
- Invalid levels trigger warning but don't fail startup
- Defaults to "INFO" for production safety

---

### `load_provider_specific_config` Method

```python
@model_validator(mode="before")
@classmethod
def load_provider_specific_config(cls, values: dict) -> dict
```

**Description**: Pre-validation method that loads provider-specific configuration from .env values, allowing provider-specific API keys and model names.

**Parameters**:
- `values: dict` - Raw configuration values before validation

**Returns**: 
- `dict` - Modified configuration values with provider-specific settings mapped to generic fields

**Behavior**: 
- Maps provider-specific keys to generic configuration fields
- For `google-gemini`: Maps `GEMINI_API_KEY` → `AI_API_KEY`, `GEMINI_FAST_MODEL` → `FAST_MODEL`, etc.
- For `openrouter`: Maps `OPENROUTER_API_KEY` → `AI_API_KEY`, `OPENROUTER_FAST_MODEL` → `FAST_MODEL`, etc.
- Provides sensible defaults for OpenRouter models if not specified
- Falls back to generic keys if provider-specific keys are not found

**Example Usage**:
```bash
# OpenRouter configuration
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_FAST_MODEL=google/gemini-2.5-flash
OPENROUTER_NORMAL_MODEL=google/gemini-2.5-pro

# Google Gemini configuration  
AI_PROVIDER=google-gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_FAST_MODEL=gemini-2.5-flash-preview-04-17
GEMINI_NORMAL_MODEL=gemini-2.5-pro-preview-03-25
```

**Tips/Notes**:
- Automatically called during Settings initialization
- Enables clean separation of provider-specific configurations
- Maintains backward compatibility with generic field names

---

### `validate_model_names` Method

```python
@model_validator(mode="after")
def validate_model_names(self) -> Settings
```

**Description**: Post-validation method that ensures model names are provided for specific AI providers.

**Parameters**: None (operates on self)

**Returns**: 
- `Settings` - The validated settings instance

**Behavior**: 
- Validates model configuration based on AI_PROVIDER
- Ensures required models and API keys are specified for google-gemini provider
- Ensures required API key is specified for openrouter provider
- Can be extended for other AI providers

**Raises**: 
- `ValueError` - If required model names or API keys are missing for google-gemini provider
- `ValueError` - If required API key is missing for openrouter provider

**Tips/Notes**:
- Provider-specific validation logic
- Extensible for additional AI providers
- Runs after all field validators complete

---

### `get_settings` Function

```python
def get_settings() -> Settings
```

**Description**: Factory function that loads and returns application settings with proper error handling. Supports command-line argument overrides and excludes environment variables to prevent conflicts.

**Returns**: 
- `Settings` - Configured settings instance

**Behavior**: 
- Locates project root directory automatically
- Attempts to load .env file from project root
- Parses command-line arguments for configuration overrides (--key=value format)
- Excludes environment variables to prevent conflicts with .env files
- Handles missing .env files gracefully
- Provides detailed error logging
- Falls back to mock provider if initial loading fails

**Raises**: 
- `Exception` - Re-raises any configuration loading errors after logging

**Example Usage**:
```python
from core.config import get_settings

# Load settings
settings = get_settings()

# Use settings
max_chunks = settings.CHUNK_MAX_BLOCKS
```

**Tips/Notes**:
- Automatically finds project root relative to module location
- Works with or without .env file present
- Should be used with dependency injection for optimal caching
- Logs all configuration loading steps for debugging

---

## Configuration File Examples

### Environment Variables
```bash
# Required
AI_API_KEY=your_api_key_here

# Optional
AI_PROVIDER=google-gemini
FAST_MODEL=gemini-2.5-flash-preview-04-17
NORMAL_MODEL=gemini-2.5-pro-preview-03-25
TARGET_LANGUAGES=Spanish,French,German
CHUNK_MAX_BLOCKS=150
RETRY_MAX_ATTEMPTS=3
LOG_LEVEL=DEBUG
MAX_CONCURRENT_TRANSLATIONS=5
```

### .env File Examples

#### OpenRouter Configuration
```env
# AI Provider Configuration
AI_PROVIDER=openrouter

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_FAST_MODEL=google/gemini-2.5-flash
OPENROUTER_NORMAL_MODEL=google/gemini-2.5-pro

# Translation Settings
TARGET_LANGUAGES=Vietnamese,French,Spanish
CHUNK_MAX_BLOCKS=100
RETRY_MAX_ATTEMPTS=4
MAX_CONCURRENT_TRANSLATIONS=10

# Logging
LOG_LEVEL=INFO
```

#### Google Gemini Configuration
```env
# AI Provider Configuration
AI_PROVIDER=google-gemini

# Google Gemini Configuration  
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_FAST_MODEL=gemini-2.5-flash-preview-04-17
GEMINI_NORMAL_MODEL=gemini-2.5-pro-preview-03-25

# Translation Settings
TARGET_LANGUAGES=Vietnamese,French,Spanish
CHUNK_MAX_BLOCKS=100
RETRY_MAX_ATTEMPTS=4
MAX_CONCURRENT_TRANSLATIONS=10

# Logging
LOG_LEVEL=INFO
```

#### Generic/Fallback Configuration
```env
# Generic fallback configuration (used if provider-specific keys are not set)
AI_PROVIDER=google-gemini
AI_API_KEY=fallback_api_key
FAST_MODEL=fallback_fast_model
NORMAL_MODEL=fallback_normal_model

# Translation Settings
TARGET_LANGUAGES=Vietnamese,French,Spanish
CHUNK_MAX_BLOCKS=100
RETRY_MAX_ATTEMPTS=4
MAX_CONCURRENT_TRANSLATIONS=10

# Logging
LOG_LEVEL=INFO
```

## Error Handling

### Common Configuration Errors
1. **Missing API Key**: Application will fail to start if AI_API_KEY is not provided
2. **Invalid Log Level**: Warning logged, defaults to "INFO"
3. **Invalid Numeric Values**: Pydantic validation errors with detailed messages
4. **Malformed Language List**: Gracefully defaults to Vietnamese and French

### Debugging Configuration Issues
- Check application logs for configuration loading messages
- Verify .env file location (must be in project root)
- Ensure environment variable names match exactly (case-sensitive)
- Use LOG_LEVEL=DEBUG for detailed configuration loading information