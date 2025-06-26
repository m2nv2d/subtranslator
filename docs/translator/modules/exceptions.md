# exceptions.py - Translation Error Handling Module

## Module Overview

**Purpose and responsibilities**: Defines a comprehensive hierarchy of custom exceptions for the subtitle translation system, providing granular error handling across different stages of the translation pipeline.

**Design pattern used**: Exception hierarchy pattern with domain-specific error types, following Python's exception handling best practices.

**Integration points**: 
- Used throughout all translator modules for consistent error reporting
- Integrates with retry mechanisms in `chunk_translator.py` and `context_detector.py`
- Provides error context for API responses in the router layer

## 🔍 Abstraction-Level Reference

### ConfigError

**Name and signature**: `class ConfigError(Exception)`

**Description and purpose**: Exception raised when application configuration loading or validation fails.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**: 
- Signals configuration-related failures
- Used during application startup when settings cannot be loaded or validated
- Provides a clear distinction between configuration issues and runtime errors

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import ConfigError

try:
    settings = load_config()
except InvalidConfigurationError:
    raise ConfigError("Failed to load application settings")
```

**Tips/Notes**: 
- Typically raised during application initialization
- Should be caught at the application level for graceful startup failure handling

---

### ValidationError

**Name and signature**: `class ValidationError(Exception)`

**Description and purpose**: Exception raised when input validation fails, particularly for file validation and user input checks.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**:
- Signals invalid input data (file size, format, content)
- Used in the parser module for SRT file validation
- Provides clear feedback about what validation rule was violated

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import ValidationError

if not file_path.endswith('.srt'):
    raise ValidationError("Invalid file type. Only .srt files are accepted.")

if file_size > MAX_FILE_SIZE_BYTES:
    raise ValidationError(f"File size exceeds the limit of {MAX_FILE_SIZE_MB}MB.")
```

**Tips/Notes**:
- Should include specific details about validation failure in the error message
- Used for both file validation and content validation
- Caught by API endpoints to return appropriate HTTP error codes

---

### ParsingError

**Name and signature**: `class ParsingError(Exception)`

**Description and purpose**: Exception raised when parsing of SRT files fails due to malformed content or file access issues.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**:
- Signals failures in SRT file parsing and content extraction
- Wraps underlying parsing library exceptions with domain context
- Distinguishes parsing failures from validation failures

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import ParsingError

try:
    parsed_subs = list(srt.parse(content))
except Exception as e:
    raise ParsingError(f"Failed to parse SRT file '{file_path}': {e}") from e
```

**Tips/Notes**:
- Should preserve the original exception as the cause using `from e`
- Include file path or context information in the error message
- Used when SRT content is syntactically invalid

---

### ContextDetectionError

**Name and signature**: `class ContextDetectionError(Exception)`

**Description and purpose**: Exception raised when AI-powered context detection fails or receives invalid parameters.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**:
- Signals failures in the context detection phase of translation
- Used for invalid speed mode parameters or AI service failures
- Provides feedback about context analysis problems

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import ContextDetectionError

if speed_mode not in ["mock", "fast", "normal"]:
    raise ContextDetectionError(f"Invalid speed_mode: {speed_mode}. Must be 'mock', 'fast', or 'normal'.")
```

**Tips/Notes**:
- Used in the context_detector module with retry mechanisms
- Should specify whether the error is due to invalid parameters or AI service issues
- Helps distinguish context detection failures from translation failures

---

### ChunkTranslationError

**Name and signature**: `class ChunkTranslationError(Exception)`

**Description and purpose**: Exception raised when translation of subtitle chunks fails, including AI response parsing errors.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**:
- Signals failures during the chunk translation process
- Used for AI response validation, JSON parsing, and schema validation errors
- Provides specific context about which chunk failed and why

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import ChunkTranslationError

try:
    validated_chunk = TranslatedChunk.model_validate_json(response.text)
except Exception as e:
    raise ChunkTranslationError(f"Response does not match expected schema: {str(e)}")

if not (0 <= block_index < len(chunk)):
    raise ChunkTranslationError(f"Invalid block index {block_index} received in translation response for chunk {chunk_index}.")
```

**Tips/Notes**:
- Used extensively in the chunk_translator module with retry logic
- Should include chunk index and specific failure reason
- Critical for debugging translation pipeline issues

---

### GenAIClientInitError

**Name and signature**: `class GenAIClientInitError(Exception)`

**Description and purpose**: Exception raised when Google Generative AI client initialization fails.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**:
- Signals failures in AI client setup and authentication
- Used during application startup or client refresh operations
- Indicates problems with API keys, network connectivity, or service availability

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import GenAIClientInitError

try:
    client = genai.Client(api_key=settings.AI_API_KEY)
    return client
except Exception as e:
    raise GenAIClientInitError("Failed to initialize Gemini Client") from e
```

**Tips/Notes**:
- Typically occurs during application startup
- Should preserve the original exception for debugging
- Indicates need to check API key configuration and network connectivity

---

### GenAIRequestError

**Name and signature**: `class GenAIRequestError(Exception)`

**Description and purpose**: Exception raised when requests to the Google Generative AI service fail.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**:
- Signals failures in AI API calls (rate limits, service errors, network issues)
- Used for runtime AI service communication problems
- Distinguishes request failures from response parsing failures

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import GenAIRequestError

try:
    response = await genai_client.aio.models.generate_content(...)
except Exception as e:
    raise GenAIRequestError(f"AI service request failed: {e}") from e
```

**Tips/Notes**:
- Often transient and suitable for retry mechanisms
- Should include context about which operation failed
- May indicate rate limiting or service outages

---

### GenAIParsingError

**Name and signature**: `class GenAIParsingError(Exception)`

**Description and purpose**: Exception raised when parsing of AI service responses fails due to unexpected format or content.

**Parameters**: Inherits from base `Exception` class
- `*args`: Variable arguments passed to base Exception

**Returns**: Exception instance

**Behavior**:
- Signals failures in processing AI service responses
- Used when response format doesn't match expected schema
- Indicates problems with response structure or content validation

**Raises**: N/A (this is an exception class)

**Example usage**:
```python
from translator.exceptions import GenAIParsingError

try:
    result = json.loads(response.text)
except json.JSONDecodeError as e:
    raise GenAIParsingError(f"Failed to parse AI response as JSON: {e}") from e
```

**Tips/Notes**:
- Often indicates changes in AI service response format
- Should include the problematic response content for debugging
- May require prompt engineering adjustments to fix

---

## Integration Patterns

The exception hierarchy supports several key integration patterns:

1. **Retry Logic Integration**: Exceptions like `ChunkTranslationError` and `ContextDetectionError` are designed to work with the retry decorators in other modules.

2. **Error Propagation**: Each exception type provides specific context that can be used by higher-level error handlers to determine appropriate responses.

3. **Debugging Support**: All exceptions are designed to preserve original error context using the `from e` pattern when wrapping lower-level exceptions.

4. **API Response Mapping**: The exception hierarchy allows the router layer to map different error types to appropriate HTTP status codes and user-friendly error messages.