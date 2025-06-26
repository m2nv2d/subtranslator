# Main Application Module

## Module Overview
- **Purpose and responsibilities**: FastAPI application initialization, configuration, static file serving, routing, and global exception handling
- **Design pattern used**: Application Factory pattern with centralized error handling and dependency injection
- **Integration points**: Core configuration system, translator module exceptions, router modules, and static file serving

## 🔍 Abstraction-Level Reference

### Application Instance
**Name**: `app`  
**Type**: `FastAPI`  
**Description**: Main FastAPI application instance that serves as the entry point for the SRT translation service.

**Configuration**:
- Title: "Subtranslator"
- Static files mounted at `/static` serving from `src/static`
- Includes translate router for all translation endpoints

**Example Usage**:
```python
# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Logging Configuration
**Function**: Module-level logging setup  
**Description**: Configures application-wide logging with level determined by settings configuration.

**Parameters**:
- Uses `LOG_LEVEL` from settings (defaults to INFO if settings fail to load)
- Format: `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`

**Side Effects**:
- Sets up global logging configuration
- Prints warning to stdout if settings loading fails
- Uses `force=True` to override any existing logging configuration

**Error Conditions**:
- Falls back to INFO level if settings cannot be loaded
- Prints warning message if configuration fails

### Exception Handlers

#### validation_error_handler
**Signature**: `async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse`  
**Description**: Handles validation errors from the translator module with appropriate HTTP status codes.

**Parameters**:
- `request: Request` - FastAPI request object
- `exc: ValidationError` - Custom validation exception from translator module

**Returns**: JSONResponse with status 400 and error message  
**Side Effects**: Logs warning message  
**Example Response**:
```json
{
  "error": "Invalid file type. Please upload an SRT file."
}
```

#### parsing_error_handler
**Signature**: `async def parsing_error_handler(request: Request, exc: ParsingError) -> JSONResponse`  
**Description**: Handles SRT file parsing errors with detailed error information.

**Parameters**:
- `request: Request` - FastAPI request object  
- `exc: ParsingError` - Custom parsing exception from translator module

**Returns**: JSONResponse with status 422 (Unprocessable Entity)  
**Side Effects**: Logs error with full traceback  
**Error Conditions**: Triggered when SRT file cannot be parsed

#### context_detection_error_handler
**Signature**: `async def context_detection_error_handler(request: Request, exc: ContextDetectionError) -> JSONResponse`  
**Description**: Handles errors during context detection phase of translation.

**Parameters**:
- `request: Request` - FastAPI request object
- `exc: ContextDetectionError` - Custom context detection exception

**Returns**: JSONResponse with status 500 (Internal Server Error)  
**Side Effects**: Logs error with full traceback  
**Error Conditions**: Triggered when AI context detection fails

#### chunk_translation_error_handler
**Signature**: `async def chunk_translation_error_handler(request: Request, exc: ChunkTranslationError) -> JSONResponse`  
**Description**: Handles errors during the chunk translation process.

**Parameters**:
- `request: Request` - FastAPI request object
- `exc: ChunkTranslationError` - Custom chunk translation exception

**Returns**: JSONResponse with status 500 (Internal Server Error)  
**Side Effects**: Logs error with full traceback  
**Error Conditions**: Triggered when subtitle chunk translation fails

#### retry_error_handler
**Signature**: `async def retry_error_handler(request: Request, exc: RetryError) -> JSONResponse`  
**Description**: Handles retry exhaustion errors from the tenacity library.

**Parameters**:
- `request: Request` - FastAPI request object
- `exc: RetryError` - Tenacity retry exhaustion exception

**Returns**: JSONResponse with status 504 (Gateway Timeout)  
**Side Effects**: Logs error with full traceback  
**Error Conditions**: Triggered when all retry attempts are exhausted

**Example Response**:
```json
{
  "error": "Service temporarily unavailable after multiple retries."
}
```

#### http_exception_handler
**Signature**: `async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse`  
**Description**: Handles standard FastAPI HTTP exceptions with consistent error format.

**Parameters**:
- `request: Request` - FastAPI request object
- `exc: HTTPException` - Standard FastAPI HTTP exception

**Returns**: JSONResponse with original status code and formatted error message  
**Side Effects**: Logs warning message  

#### generic_exception_handler
**Signature**: `async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse`  
**Description**: Catch-all handler for unhandled exceptions to prevent application crashes.

**Parameters**:
- `request: Request` - FastAPI request object
- `exc: Exception` - Any unhandled exception

**Returns**: JSONResponse with status 500 and generic error message  
**Side Effects**: Logs full exception details with traceback  
**Invariants**: Never exposes internal error details to clients

**Example Response**:
```json
{
  "error": "An unexpected internal server error occurred."
}
```

### Static File Configuration
**Mount Point**: `/static`  
**Directory**: `src/static`  
**Description**: Serves static assets (CSS, JavaScript, images) for the web interface.

**Integration**: Used by HTML templates to load client-side assets

### Router Integration
**Router**: `translate_router` from `routers.translate`  
**Description**: Includes all translation-related endpoints and the main index page.

**Endpoints Provided**:
- `GET /` - Main upload form
- `POST /translate` - SRT translation endpoint  
- `GET /stats` - Translation statistics

### Tips/Notes
- **Error Handling Strategy**: Uses a hierarchical approach with specific handlers for custom exceptions and generic fallbacks
- **Logging**: All exceptions are logged with appropriate levels (warning for client errors, error for server errors)
- **Security**: Uses `create_error_response` helper to ensure consistent error formatting and prevent information leakage
- **Development**: The application can be extended by adding new routers and exception handlers
- **Production**: Consider adding middleware for request logging, CORS, and security headers