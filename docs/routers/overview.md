# Routers Components Overview

## Purpose

The `routers` package contains FastAPI route handlers that provide the HTTP API interface for the Subtranslator application. This package serves as the integration layer between the web interface and the core translation business logic, handling request orchestration, response formatting, and error management.

## Internal Structure

```
src/routers/
├── __init__.py          # Package initialization
└── translate.py         # Main translation and statistics endpoints
```

## Exposed Interface

### HTTP Endpoints

#### GET `/`
- **Purpose**: Serve the main application interface
- **Response**: HTML page with file upload form
- **Template**: Renders `templates/index.html` with available target languages
- **Dependencies**: Application settings for language list

#### POST `/translate`
- **Purpose**: Handle SRT file translation requests
- **Parameters**:
  - `file`: UploadFile (SRT file, required)
  - `target_lang`: str (target language, required)
  - `speed_mode`: str (processing mode: "normal", "fast", "mock", default: "normal")
- **Response**: StreamingResponse with translated SRT file
- **Dependencies**: Settings, AI client, semaphore, statistics store

#### GET `/stats`
- **Purpose**: Retrieve application statistics
- **Response**: JSON with total statistics and individual file statistics
- **Dependencies**: Statistics store

### Integration Components
- **Jinja2Templates**: Template rendering for HTML responses
- **Router Instance**: FastAPI APIRouter for endpoint organization
- **Dependency Injection**: Centralized access to application services

## Design Pattern

The routers package implements the **Controller Pattern** with **Dependency Injection**:

- **Request Orchestration**: Route handlers coordinate between multiple business logic components
- **Dependency Management**: Services are injected rather than directly instantiated
- **Error Boundary**: Comprehensive exception handling with appropriate HTTP status mapping
- **Response Formatting**: Consistent response formats across all endpoints

## Request Processing Flow

### Translation Request Pipeline
```
HTTP Request → Input Validation → Service Orchestration → Response Generation
     ↓              ↓                    ↓                     ↓
File Upload → Validate Format → Parse → Context → Translate → Download
     ↓              ↓                    ↓                     ↓
Statistics → Temp Storage → Chunks → AI Processing → Cleanup → Response
```

### Error Handling Pipeline
```
Exception → Classification → Status Code Mapping → Error Response → Cleanup
    ↓           ↓                 ↓                   ↓            ↓
Domain Error → HTTP Status → JSON Response → User Message → Resource Cleanup
```

## Key Features

### Request Orchestration
- **Service Coordination**: Manages interaction between parser, translator, and statistics components
- **Resource Management**: Handles temporary file creation and guaranteed cleanup
- **Progress Tracking**: Updates statistics throughout the translation lifecycle
- **Dependency Resolution**: Coordinates between injected services (AI client, settings, semaphore)

### Error Management
- **Exception Mapping**: Translates domain exceptions to appropriate HTTP status codes
- **User-Friendly Messages**: Provides clear error descriptions without exposing internals
- **Resource Cleanup**: Ensures temporary files are removed even on failures
- **Statistics Accuracy**: Properly records failed requests for monitoring

### File Processing
- **Secure Upload Handling**: Uses werkzeug utilities for safe filename processing
- **Size Validation**: Enforces file size limits to prevent abuse
- **Streaming Response**: Efficient file download without memory buffering
- **Content-Type Management**: Proper MIME types and download headers

### Performance Optimization
- **Async Processing**: Full async/await pattern for non-blocking operations
- **Concurrent Translation**: Delegates to business logic for parallel processing
- **Resource Pooling**: Shared AI client and semaphore across requests
- **Caching**: Settings cached for repeated access

## Integration Points

### With Core Components
```python
# Dependency injection pattern
async def translate_srt(
    settings: Annotated[Settings, Depends(get_application_settings)],
    genai_client: Annotated[genai.client.Client | None, Depends(get_genai_client)],
    semaphore: Annotated[asyncio.Semaphore, Depends(get_translation_semaphore)],
    stats_store: Annotated[AppStatsStore, Depends(get_stats_store)],
    # ... file parameters
):
```

### With Business Logic
```python
# Service orchestration
subtitle_chunks = await parse_srt(temp_file_path, settings.CHUNK_MAX_BLOCKS)
context = await detect_context(subtitle_chunks, speed_mode, genai_client, settings)
failed_attempts, chunks_with_failures = await translate_all_chunks(
    context, subtitle_chunks, target_lang, speed_mode, genai_client, settings, semaphore
)
output_content = reassemble_srt(subtitle_chunks)
```

### With Frontend
- **Template Integration**: Passes dynamic data (languages) to Jinja2 templates
- **Form Processing**: Handles multipart form data from JavaScript client
- **Response Format**: Provides appropriate responses for AJAX requests
- **Error Communication**: Returns structured error messages for client handling

## Best Practices

### Request Validation
```python
# Multi-layer validation approach
if not file.filename or not file.filename.lower().endswith('.srt'):
    raise ValidationError("Invalid file type. Please upload an SRT file.")

if target_lang not in settings.TARGET_LANGUAGES:
    raise ValidationError(f"Invalid target language: {target_lang}")
```

### Resource Management
```python
# Guaranteed cleanup pattern
temp_dir = None
try:
    temp_dir = tempfile.mkdtemp()
    # ... processing logic
finally:
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
```

### Statistics Integration
```python
# Complete lifecycle tracking
request_id = await stats_store.create_file_entry(filename, size, speed_mode)
try:
    # ... processing steps with updates
    await stats_store.update_parsing_stats(request_id, chunks, blocks)
    await stats_store.update_translation_stats(request_id, failed_attempts, failed_chunks)
    status = "completed"
except Exception:
    status = "failed"
    raise
finally:
    await stats_store.complete_request(request_id, status)
```

## Error Handling Strategy

### Exception Classification
- **ValidationError** → 400 Bad Request (client input errors)
- **ParsingError** → 422 Unprocessable Entity (file format issues)
- **ContextDetectionError** → 500 Internal Server Error (AI service issues)
- **ChunkTranslationError** → 500 Internal Server Error (translation failures)
- **RetryError** → 504 Gateway Timeout (service unavailable)
- **HTTPException** → Original status code (explicit HTTP errors)
- **Exception** → 500 Internal Server Error (unexpected failures)

### Error Response Format
```python
# Consistent error response structure
return JSONResponse(
    status_code=status_code,
    content=create_error_response(error_message)
)
```

## Performance Considerations

### Async Operation Patterns
- All file I/O operations use `aiofiles` for non-blocking behavior
- Business logic calls are properly awaited
- Statistics updates are async to prevent blocking
- Resource cleanup is async-safe

### Memory Management
- File content read once and reused
- Streaming responses prevent memory buffering
- Temporary files cleaned up promptly
- In-memory processing for subtitle data

### Concurrency Control
- Semaphore injection manages global concurrency limits
- AI client shared across requests to prevent resource exhaustion
- Statistics store handles concurrent access safely

## Security Considerations

### Input Validation
- File extension validation prevents arbitrary file upload
- File size limits prevent denial-of-service attacks
- Secure filename handling prevents path traversal
- Language validation against allowed list

### Error Information Disclosure
- Generic error messages for internal failures
- No stack traces exposed to clients
- API keys and sensitive config not logged
- Temporary file paths not exposed in responses

### Resource Protection
- Temporary file cleanup prevents disk exhaustion
- Processing timeouts prevent resource hogging
- Concurrency limits prevent service overload

## Monitoring and Observability

### Statistics Endpoint
```python
# Provides operational visibility
@router.get("/stats")
async def get_statistics(stats_store: Annotated[AppStatsStore, Depends(get_stats_store)]):
    total_stats, file_stats = await stats_store.get_stats()
    return total_stats, file_stats
```

### Logging Integration
- Request start/end logging with request IDs
- Error logging with full context
- Performance metrics (processing times)
- Resource usage tracking (file sizes, chunk counts)

### Health Monitoring
- AI client availability checking
- Service dependency validation
- Error rate tracking through statistics
- Resource cleanup monitoring