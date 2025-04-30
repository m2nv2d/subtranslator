# Environment Configuration

This document describes the environment variables used for configuration in the Subtranslator application. You should create a `.env` file in the project root with the following variables:

```
# Required settings
# AI provider (required)
AI_PROVIDER=google-gemini

# API key for the AI provider (required)
AI_API_KEY=your-gemini-api-key-here

# Model names for translation (conditional required, based on provider)
FAST_MODEL=gemini-2.5-flash-preview-04-17
NORMAL_MODEL=gemini-2.5-pro-preview-03-25

# Optional settings with defaults
# Target languages (comma-separated list, default: "Vietnamese,French")
TARGET_LANGUAGES=Vietnamese,French,Spanish,German,Italian

# Maximum number of subtitle blocks per chunk (positive integer, default: 100)
CHUNK_MAX_BLOCKS=100

# Maximum number of retry attempts (non-negative integer, default: 6)
RETRY_MAX_ATTEMPTS=6

# Logging level (must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL, default: INFO)
LOG_LEVEL=INFO
```

## Configuration Details

### Required Settings

- `AI_PROVIDER`: The AI provider to use for translation (default: "google-gemini")
- `AI_API_KEY`: Your API key for the specified AI provider (required)
- `FAST_MODEL`: The model to use for fast translation mode (required when using "google-gemini")
- `NORMAL_MODEL`: The model to use for normal translation mode (required when using "google-gemini")

### Optional Settings

- `TARGET_LANGUAGES`: Comma-separated list of target languages available for translation (default: "Vietnamese,French")
- `CHUNK_MAX_BLOCKS`: Maximum number of subtitle blocks per chunk (default: 100, must be positive)
- `RETRY_MAX_ATTEMPTS`: Maximum number of retry attempts for failed operations (default: 6, must be non-negative)
- `LOG_LEVEL`: Logging level (default: "INFO", must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL) 