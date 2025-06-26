# Errors Module (`errors.py`)

## Module Overview

### Purpose and Responsibilities
The `errors.py` module provides standardized error response models and utilities for consistent API error reporting across the subtranslator application. It ensures all error responses follow a uniform structure and format.

### Design Pattern Used
- **Data Transfer Object (DTO) Pattern**: Uses Pydantic models for structured error data
- **Factory Pattern**: Helper function creates standardized error responses
- **Standardization Pattern**: Enforces consistent error response format across the API

### Integration Points
- Used by FastAPI endpoints for consistent error responses
- Integrates with Pydantic validation system
- Provides JSON-serializable error structures
- Used by exception handlers and middleware

## 🔍 Abstraction-Level Reference

### `ErrorDetail` Class

```python
class ErrorDetail(BaseModel)
```

**Description**: Standardized Pydantic model for API error responses that ensures consistent error reporting structure.

**Behavior**: 
- Validates error response data using Pydantic
- Provides JSON serialization for API responses
- Enforces required error message field
- Supports optional additional details

**Fields**:
- `error: str` - **Required**. Main error message describing what went wrong
- `detail: Optional[str]` - **Optional**. Additional error details or context

**Example Usage**:
```python
from core.errors import ErrorDetail

# Create error model directly
error_response = ErrorDetail(
    error="Translation failed",
    detail="API rate limit exceeded"
)

# Use in FastAPI response
from fastapi import HTTPException
raise HTTPException(
    status_code=429,
    detail=error_response.model_dump()
)
```

**JSON Output Example**:
```json
{
    "error": "Translation failed",
    "detail": "API rate limit exceeded"
}
```

**Tips/Notes**:
- Always serializes to consistent JSON structure
- Required `error` field prevents empty error responses
- Optional `detail` field allows for additional context without breaking consistency
- Compatible with FastAPI's automatic JSON serialization

---

### `create_error_response` Function

```python
def create_error_response(message: str, detail: Optional[str] = None) -> dict
```

**Description**: Factory function that creates standardized error response dictionaries using the ErrorDetail model.

**Parameters**:
- `message: str` - **Required**. The main error message describing what went wrong
- `detail: Optional[str] = None` - **Optional**. Additional error details or context information

**Returns**: 
- `dict` - Dictionary containing error information formatted according to ErrorDetail model

**Behavior**: 
- Creates ErrorDetail instance with provided parameters
- Converts model to dictionary using `model_dump()`
- Ensures consistent error response structure
- Handles optional detail parameter gracefully

**Example Usage**:
```python
from core.errors import create_error_response
from fastapi import HTTPException

# Simple error response
error_dict = create_error_response("File not found")
# Returns: {"error": "File not found", "detail": None}

# Error response with details
error_dict = create_error_response(
    message="Validation failed",
    detail="File size exceeds 10MB limit"
)
# Returns: {"error": "Validation failed", "detail": "File size exceeds 10MB limit"}

# Use in HTTP exception
raise HTTPException(
    status_code=400,
    detail=create_error_response(
        "Invalid file format",
        "Only .srt files are supported"
    )
)
```

**Tips/Notes**:
- Preferred method for creating error responses
- Automatically handles model validation and serialization
- Returns dictionary ready for JSON serialization
- Consistent with ErrorDetail model structure

## Usage Patterns

### FastAPI Exception Handling

```python
from fastapi import HTTPException
from core.errors import create_error_response

@app.post("/translate")
async def translate_file(file: UploadFile):
    try:
        # File processing logic
        if not file.filename.endswith('.srt'):
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    "Invalid file format",
                    "Only SRT subtitle files are supported"
                )
            )
        
        return await process_file(file)
    
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=create_error_response(
                "Processing error",
                str(e)
            )
        )
```

### Custom Exception Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.errors import create_error_response

app = FastAPI()

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            "Validation error",
            str(exc)
        )
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=404,
        content=create_error_response(
            "File not found",
            f"The requested file could not be located: {exc.filename}"
        )
    )
```

### Validation Error Responses

```python
from pydantic import ValidationError
from core.errors import create_error_response

async def validate_translation_request(data: dict):
    try:
        # Validation logic
        validated_data = TranslationRequest(**data)
        return validated_data
    except ValidationError as e:
        # Convert Pydantic errors to standard format
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append(f"{field}: {error['msg']}")
        
        raise HTTPException(
            status_code=422,
            detail=create_error_response(
                "Request validation failed",
                "; ".join(error_details)
            )
        )
```

### Conditional Error Details

```python
from core.errors import create_error_response
from core.config import get_settings

def create_debug_error_response(message: str, exception: Exception = None):
    settings = get_settings()
    
    # Include detailed error information in debug mode
    if settings.LOG_LEVEL == "DEBUG" and exception:
        detail = f"{type(exception).__name__}: {str(exception)}"
    else:
        detail = None
    
    return create_error_response(message, detail)

# Usage
try:
    result = risky_operation()
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=create_debug_error_response(
            "Internal server error",
            e if get_settings().LOG_LEVEL == "DEBUG" else None
        )
    )
```

## Error Response Standards

### HTTP Status Code Mapping

| Status Code | Error Type | Example Usage |
|-------------|------------|---------------|
| 400 | Bad Request | Invalid input format, missing required fields |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors, business logic violations |
| 429 | Too Many Requests | Rate limiting |
| 500 | Internal Server Error | Unexpected server errors |

### Error Message Guidelines

**Do:**
- Use clear, user-friendly language
- Be specific about what went wrong
- Provide actionable information when possible
- Keep error messages concise but informative

**Don't:**
- Expose internal system details in production
- Use technical jargon that users won't understand
- Include stack traces in user-facing responses
- Make error messages too generic to be useful

### Example Error Responses

```json
// File validation error
{
    "error": "Invalid file format",
    "detail": "Only .srt subtitle files are supported. Received: .txt"
}

// Size limit error  
{
    "error": "File too large",
    "detail": "File size (15.2MB) exceeds maximum limit of 10MB"
}

// Translation service error
{
    "error": "Translation service unavailable",
    "detail": "Google Gemini API is currently unreachable. Please try again later."
}

// Generic server error (production)
{
    "error": "Internal server error",
    "detail": null
}

// Generic server error (debug mode)
{
    "error": "Internal server error", 
    "detail": "ConnectionError: Failed to connect to API endpoint"
}
```

## Integration with FastAPI

### Automatic Error Model Documentation

```python
from fastapi import FastAPI
from core.errors import ErrorDetail

app = FastAPI()

@app.post("/translate", responses={
    400: {"model": ErrorDetail, "description": "Bad request"},
    422: {"model": ErrorDetail, "description": "Validation error"},
    500: {"model": ErrorDetail, "description": "Internal server error"}
})
async def translate_endpoint():
    # Endpoint implementation
    pass
```

This integration ensures that:
- API documentation shows consistent error response structure
- Client applications can rely on standardized error format
- Error handling is predictable across all endpoints
- OpenAPI/Swagger documentation is accurate and complete