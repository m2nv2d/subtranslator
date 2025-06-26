# Translate Router Module

## Module Overview
- **Purpose and responsibilities**: Handles HTTP routing for SRT translation requests, file uploads, template rendering, and statistics endpoints
- **Design pattern used**: FastAPI Router pattern with dependency injection, async/await concurrency, and comprehensive error handling
- **Integration points**: Core configuration, translation engine, statistics tracking, template rendering, and temporary file management

## 🔍 Abstraction-Level Reference

### Router Configuration
**Name**: `router`  
**Type**: `APIRouter`  
**Description**: FastAPI router instance that handles all translation-related endpoints.

**Template Configuration**:
- Templates directory: `src/templates`
- Template engine: Jinja2Templates

### Routes

#### index
**Signature**: `async def index(request: Request, settings: Annotated[Settings, Depends(get_application_settings)]) -> HTMLResponse`  
**Description**: Renders the main upload form page with available target languages.

**Parameters**:
- `request: Request` - FastAPI request object for template context
- `settings: Settings` - Application settings via dependency injection

**Returns**: HTMLResponse with rendered index.html template  
**Template Context**:
- `request` - Request object
- `languages` - List of available target languages from settings

**Side Effects**: Logs debug message for page serving  
**Example Template Variables**:
```python
{
    "request": request,
    "languages": ["Spanish", "French", "German", "Portuguese"]
}
```

#### get_statistics
**Signature**: `async def get_statistics(stats_store: Annotated[AppStatsStore, Depends(get_stats_store)]) -> Tuple[TotalStats, dict[str, FileStats]]`  
**Description**: Returns current application statistics including total metrics and per-file details.

**Parameters**:
- `stats_store: AppStatsStore` - Statistics storage service via dependency injection

**Returns**: Tuple containing total statistics and dictionary of file-specific statistics  
**Response Model**: `Tuple[TotalStats, dict[str, FileStats]]`  
**Side Effects**: Logs info and debug messages about statistics retrieval

**Example Response**:
```json
[
  {
    "total_requests": 42,
    "completed": 38,
    "failed": 4,
    "total_chunks": 1250,
    "total_blocks": 8500
  },
  {
    "file123": {
      "filename": "movie.srt",
      "size": 25600,
      "status": "completed",
      "chunks": 15,
      "blocks": 120
    }
  }
]
```

#### translate_srt
**Signature**: `async def translate_srt(...) -> StreamingResponse`  
**Description**: Main translation endpoint that handles file upload, validation, translation orchestration, and response delivery.

**Parameters**:
- `settings: Settings` - Application configuration via dependency injection
- `genai_client: genai.client.Client | None` - AI client via dependency injection
- `semaphore: asyncio.Semaphore` - Concurrency control via dependency injection  
- `stats_store: AppStatsStore` - Statistics tracking via dependency injection
- `file: UploadFile` - Uploaded SRT file from form data
- `target_lang: str` - Target language from form data
- `speed_mode: str` - Translation speed mode ("normal", "fast", "mock")

**Returns**: StreamingResponse with translated SRT file as downloadable attachment

**Workflow Steps**:
1. **Client Validation**: Verifies AI client availability for non-mock modes
2. **Input Validation**: Validates file type, target language, and speed mode
3. **File Processing**: Secures filename and reads file content
4. **Stats Initialization**: Creates statistics entry for request tracking
5. **Temporary Storage**: Saves uploaded file to temporary location
6. **SRT Parsing**: Parses SRT into subtitle chunks
7. **Context Detection**: Detects translation context using AI
8. **Chunk Translation**: Translates all subtitle chunks with retry logic
9. **SRT Reassembly**: Reassembles translated chunks into final SRT
10. **Response Delivery**: Returns translated file as streaming download

**Error Conditions**:
- `HTTPException(501)` - Unsupported AI provider for non-mock translation
- `HTTPException(503)` - AI client not available
- `ValidationError` - Invalid file type, language, or speed mode
- `ParsingError` - SRT file parsing failure
- `ContextDetectionError` - AI context detection failure
- `ChunkTranslationError` - Translation process failure
- `RetryError` - Retry exhaustion

**Side Effects**:
- Creates and updates statistics entries
- Creates and cleans up temporary files
- Logs comprehensive workflow progress
- Updates semaphore for concurrency control

**File Naming Convention**:
```python
new_filename = f"{os.path.splitext(original_filename)[0]}_{target_lang.lower()}.srt"
# Example: "movie.srt" + "Spanish" -> "movie_spanish.srt"
```

**Concurrency Control**:
- Uses semaphore to limit concurrent translation requests
- Each translation acquires semaphore during chunk processing

**Temporary File Management**:
- Creates unique temporary directory per request
- Guarantees cleanup in finally block regardless of success/failure
- Uses secure filename generation

**Statistics Integration**:
- Tracks request lifecycle from creation to completion
- Records parsing metrics (chunks, blocks)
- Records translation metrics (failed attempts, chunks with failures)
- Updates final status ("completed" or "failed")

### Exception Handling Strategy

#### Workflow-Specific Exceptions
The translate_srt function implements a multi-layer exception handling approach:

1. **Pre-workflow Validation**: Client availability and input validation
2. **Workflow Execution**: Core translation pipeline with specific error types
3. **Generic Fallbacks**: Unexpected errors during any phase

**Exception Mapping**:
- `ParsingError` → HTTP 400 (Bad Request)
- `ContextDetectionError` → HTTP 500 (Internal Server Error)
- `ChunkTranslationError` → HTTP 500 (Internal Server Error)  
- `RetryError` → HTTP 504 (Gateway Timeout)

#### Resource Cleanup
**Invariants**:
- Temporary directories are always cleaned up via finally block
- Statistics entries are always marked with final status
- File handles are properly closed using async context managers

### Dependencies Integration

#### Settings Dependency
**Purpose**: Provides application configuration including target languages and AI settings  
**Usage**: Validates target language selection and configures translation parameters

#### GenAI Client Dependency  
**Purpose**: Provides configured AI client for translation services  
**Usage**: Required for non-mock translation modes, handles client initialization errors

#### Semaphore Dependency
**Purpose**: Controls concurrent translation requests to prevent resource exhaustion  
**Usage**: Acquired during translation workflow to limit parallel processing

#### Stats Store Dependency
**Purpose**: Provides statistics tracking and reporting capabilities  
**Usage**: Records request lifecycle, parsing metrics, and translation outcomes

### Security Considerations

#### File Upload Security
- Uses `secure_filename()` to sanitize uploaded filenames
- Validates file extensions before processing
- Limits file processing to temporary directories

#### Input Validation
- Whitelist validation for target languages
- Whitelist validation for speed modes
- File type validation using extension checking

#### Error Information Disclosure
- Generic error messages for internal failures
- Specific error messages only for validation issues
- No stack traces exposed to clients

### Performance Considerations

#### Async Processing
- All I/O operations use async/await patterns
- File operations use aiofiles for non-blocking I/O
- AI client calls are asynchronous

#### Memory Management
- Files are streamed rather than loaded entirely into memory
- Temporary files are used for large content processing
- Immediate cleanup of resources after use

#### Concurrency Control
- Semaphore prevents overwhelming AI services
- Statistics tracking is non-blocking
- Parallel chunk processing where possible

### Tips/Notes
- **File Handling**: Always use temporary files for uploaded content to prevent security issues
- **Error Logging**: Different log levels used appropriately (debug for workflow steps, info for milestones, error for failures)
- **Statistics**: Request tracking enables monitoring and debugging of translation performance
- **Extensibility**: Router pattern allows easy addition of new endpoints
- **Testing**: Mock mode enables testing without AI service dependencies
- **Monitoring**: Comprehensive logging and statistics enable production monitoring