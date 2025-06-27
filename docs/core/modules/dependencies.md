# Dependencies Module (`dependencies.py`)

## Module Overview

### Purpose and Responsibilities
The `dependencies.py` module serves as the central dependency injection hub for the subtranslator application. It provides FastAPI dependency providers for all major application components including configuration, AI providers, concurrency control, statistics tracking, and rate limiting.

### Design Pattern Used
- **Dependency Injection Pattern**: Provides centralized dependency management for FastAPI
- **Singleton Pattern**: Uses `@functools.lru_cache()` to ensure single instances of expensive resources
- **Factory Pattern**: Each function acts as a factory for creating/retrieving dependencies
- **Circuit Breaker Pattern**: Graceful handling of AI client initialization failures

### Integration Points
- FastAPI's dependency injection system (`Depends`)
- Configuration management through `core.config`
- AI provider abstraction through `core.providers`
- Statistics tracking through `core.stats`
- Rate limiting through `core.rate_limiter`
- Concurrency control using asyncio semaphores
- HTTP client management for OpenRouter provider (aiohttp)

## 🔍 Abstraction-Level Reference

### `get_application_settings` Function

```python
@functools.lru_cache()
def get_application_settings() -> Settings
```

**Description**: Dependency provider that loads and caches application configuration settings.

**Returns**: 
- `Settings` - Validated configuration settings instance

**Behavior**: 
- Loads configuration on first call using `get_settings()`
- Caches result for subsequent calls (singleton behavior)
- Logs configuration loading process
- Converts configuration errors to HTTP exceptions

**Raises**: 
- `HTTPException(500)` - If configuration loading fails
  - For Pydantic validation errors
  - For general configuration loading errors

**Example Usage**:
```python
from fastapi import FastAPI, Depends
from core.dependencies import get_application_settings

app = FastAPI()

@app.get("/config")
async def get_config(settings: Settings = Depends(get_application_settings)):
    return {
        "ai_provider": settings.AI_PROVIDER,
        "target_languages": settings.TARGET_LANGUAGES,
        "max_concurrent": settings.MAX_CONCURRENT_TRANSLATIONS
    }
```

**Tips/Notes**:
- Uses LRU cache for performance optimization
- Critical errors are logged with full traceback
- HTTP 500 errors provide user-friendly messages while logging detailed errors
- Should be used as FastAPI dependency for automatic error handling

---

### `get_ai_provider` Function

```python
@functools.lru_cache()
def get_ai_provider(settings: Settings = Depends(get_application_settings)) -> AIProvider
```

**Description**: Dependency provider that initializes and caches the AI provider based on configuration.

**Parameters**:
- `settings: Settings` - Application configuration (injected dependency)

**Returns**: 
- `AIProvider` - Initialized AI provider instance (MockProvider, GeminiProvider, or OpenRouterProvider)

**Behavior**: 
- Creates provider based on settings.AI_PROVIDER configuration
- Supports "google-gemini", "openrouter", and "mock" providers
- Handles initialization failures by raising HTTP 500 exceptions
- Caches successful provider instances
- Logs all initialization attempts and outcomes

**Raises**: 
- `HTTPException(500)` - If provider initialization fails
  - For invalid provider configuration
  - For provider-specific initialization errors (e.g., invalid API keys)

**Example Usage**:
```python
@app.post("/translate")
async def translate_text(
    provider: AIProvider = Depends(get_ai_provider)
):
    # Provider is guaranteed to be available due to dependency validation
    context = await provider.detect_context(subtitle_chunks, "fast")
    
    # Use provider for translation
    failed_attempts, chunks_with_failures = await provider.translate_all_chunks(
        context=context,
        sub=subtitle_chunks,
        target_lang="Vietnamese",
        speed_mode="fast",
        semaphore=semaphore
    )
    return {"status": "completed", "failures": failed_attempts}
```

**Tips/Notes**:
- Provider is guaranteed to be initialized or HTTP 500 is raised
- Supports production (Google Gemini, OpenRouter) and development (Mock) workflows
- Provider abstraction enables easy testing and development
- All providers implement the same interface for consistent usage
- OpenRouter provider requires aiohttp dependency for HTTP-based API calls

---

### `get_translation_semaphore` Function

```python
@functools.lru_cache()
def get_translation_semaphore(settings: Settings = Depends(get_application_settings)) -> asyncio.Semaphore
```

**Description**: Dependency provider that creates and caches a global semaphore for controlling concurrent translations.

**Parameters**:
- `settings: Settings` - Application configuration (injected dependency)

**Returns**: 
- `asyncio.Semaphore` - Semaphore with configured concurrency limit

**Behavior**: 
- Creates semaphore on first call with MAX_CONCURRENT_TRANSLATIONS limit
- Returns same semaphore instance on subsequent calls
- Logs semaphore initialization with configured limit
- Uses global variable to ensure true singleton behavior

**Example Usage**:
```python
@app.post("/translate")
async def translate_file(
    file: UploadFile,
    semaphore: asyncio.Semaphore = Depends(get_translation_semaphore)
):
    async with semaphore:
        # Translation work is now rate-limited
        result = await process_translation(file)
    return result
```

**Tips/Notes**:
- Provides application-wide concurrency control
- Prevents resource exhaustion from too many concurrent translations
- Semaphore limit configured via MAX_CONCURRENT_TRANSLATIONS setting
- Must be used with async context manager (`async with semaphore`)

---

### `get_stats_store` Function

```python
@functools.lru_cache()
def get_stats_store() -> AppStatsStore
```

**Description**: Dependency provider that initializes and caches the application statistics store.

**Returns**: 
- `AppStatsStore` - Thread-safe statistics store instance

**Behavior**: 
- Creates statistics store on first call
- Returns same store instance on subsequent calls
- Logs store initialization
- Store handles its own internal thread safety

**Example Usage**:
```python
@app.post("/translate")
async def translate_file(
    file: UploadFile,
    stats: AppStatsStore = Depends(get_stats_store)
):
    # Create tracking entry
    request_id = await stats.create_file_entry(
        filename=file.filename,
        size=len(await file.read()),
        speed_mode="fast"
    )
    
    try:
        # Perform translation
        result = await process_translation(file)
        await stats.complete_request(request_id, "completed")
        return result
    except Exception as e:
        await stats.complete_request(request_id, "failed")
        raise
```

**Tips/Notes**:
- Store is thread-safe and handles concurrent access internally
- Should be used for tracking all translation operations
- Provides both per-file and aggregate statistics
- Store methods are async and should be awaited

---

### `get_application_rate_limiter` Function

```python
def get_application_rate_limiter(settings: Settings = Depends(get_application_settings)) -> RateLimiter
```

**Description**: Dependency provider for the application rate limiter.

**Parameters**:
- `settings: Settings` - Application configuration (injected dependency)

**Returns**: 
- `RateLimiter` - Global rate limiter instance initialized with current settings

**Behavior**: 
- Returns the global rate limiter instance via `get_rate_limiter(settings)`
- Uses singleton pattern to ensure consistent rate limiting across requests
- Configured with SESSION_FILE_LIMIT from settings

**Example Usage**:
```python
@app.post("/translate")
async def translate_file(
    request: Request,
    rate_limiter: RateLimiter = Depends(get_application_rate_limiter)
):
    session_id = request.session.get("session_id")
    current_count = rate_limiter.get_session_count(session_id)
    
    # Rate limiting is typically handled by check_session_file_limit dependency
    # This is for informational purposes
    return {"current_uploads": current_count, "limit": rate_limiter.file_limit}
```

**Tips/Notes**:
- Usually used indirectly through `check_session_file_limit` dependency
- Provides access to rate limiting statistics and management
- Singleton instance shared across all requests

---

### `check_session_file_limit` Function

```python
def check_session_file_limit(
    request: Request,
    settings: Settings = Depends(get_application_settings)
) -> None
```

**Description**: FastAPI dependency to check session file upload limit before processing.

**Parameters**:
- `request: Request` - FastAPI request object containing session data
- `settings: Settings` - Application configuration (injected dependency)

**Returns**: 
- `None` - Dependency returns None on success

**Behavior**: 
- Extracts session ID from request session
- Validates session exists and is properly formatted
- Checks current file count against configured limit
- Increments file count if under limit
- Used as FastAPI dependency for automatic rate limiting

**Raises**: 
- `HTTPException(400)` - If session ID not found in request
- `HTTPException(429)` - If session file upload limit exceeded

**Example Usage**:
```python
@app.post("/translate")
async def translate_file(
    request: Request,
    file: UploadFile = File(...),
    _: None = Depends(check_session_file_limit),  # Rate limiting check
    # ... other dependencies
):
    # If we reach here, rate limiting passed
    return await process_file(file)
```

**Tips/Notes**:
- Should be included as dependency in file upload endpoints
- Uses underscore variable name since return value is not used
- Automatically enforces rate limiting without manual checks
- Works with session middleware to track user sessions

## Global Variables

### `_translation_semaphore`

```python
_translation_semaphore: asyncio.Semaphore | None = None
```

**Description**: Module-level variable storing the global semaphore instance.

**Behavior**: 
- Initialized to None on module load
- Set by `get_translation_semaphore()` on first call
- Ensures true singleton behavior across all dependency injections

**Tips/Notes**:
- Should not be accessed directly
- Use `get_translation_semaphore()` dependency provider instead
- Managed automatically by the dependency system

## Dependency Chain

The dependencies form a clear hierarchy:

1. **`get_application_settings()`** - Root dependency (no dependencies)
2. **`get_ai_provider()`** - Depends on settings
3. **`get_translation_semaphore()`** - Depends on settings  
4. **`get_stats_store()`** - Independent (no dependencies)
5. **`get_application_rate_limiter()`** - Depends on settings
6. **`check_session_file_limit()`** - Depends on settings, requires request context

## Error Handling Strategy

### Configuration Errors
- Converted to HTTP 500 exceptions with user-friendly messages
- Detailed errors logged for debugging
- Application fails fast if configuration is invalid

### AI Provider Errors
- Converted to HTTP 500 exceptions for initialization failures
- Provider is guaranteed to be available or request fails
- Supports fallback to mock provider for development/testing
- OpenRouter provider errors include HTTP API communication failures

### Resource Initialization Errors
- Logged with full context
- Application-level fallbacks should be implemented
- Critical dependencies (config, providers) cause startup failure

### Rate Limiting Errors
- HTTP 400 for missing session data
- HTTP 429 for exceeded upload limits
- Session management handled by middleware

## Usage Patterns

### Basic Dependency Injection
```python
from fastapi import Depends
from core.dependencies import get_application_settings, get_ai_provider

@app.get("/status")
async def get_status(
    settings: Settings = Depends(get_application_settings),
    provider: AIProvider = Depends(get_ai_provider)
):
    return {
        "ai_provider": settings.AI_PROVIDER,
        "ai_available": True,  # Provider is guaranteed to be available
        "max_concurrent": settings.MAX_CONCURRENT_TRANSLATIONS,
        "session_file_limit": settings.SESSION_FILE_LIMIT
    }
```

### Rate-Limited Operations
```python
@app.post("/translate")
async def translate_endpoint(
    request: Request,
    data: TranslationRequest,
    provider: AIProvider = Depends(get_ai_provider),
    semaphore: asyncio.Semaphore = Depends(get_translation_semaphore),
    _: None = Depends(check_session_file_limit)  # Session-based rate limiting
):
    # Both session and concurrency rate limiting applied
    async with semaphore:
        return await perform_translation(provider, data)
```

### Statistics Tracking
```python
@app.post("/translate-file")
async def translate_file_endpoint(
    file: UploadFile,
    stats: AppStatsStore = Depends(get_stats_store),
    settings: Settings = Depends(get_application_settings)
):
    # Track file processing
    request_id = await stats.create_file_entry(
        filename=file.filename,
        size=file.size or 0,
        speed_mode="normal"
    )
    
    try:
        result = await process_file(file, settings)
        await stats.complete_request(request_id, "completed")
        return result
    except Exception as e:
        await stats.complete_request(request_id, "failed")
        raise HTTPException(500, f"Translation failed: {str(e)}")
```