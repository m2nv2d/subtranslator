# Dependencies Module (`dependencies.py`)

## Module Overview

### Purpose and Responsibilities
The `dependencies.py` module serves as the central dependency injection hub for the subtranslator application. It provides FastAPI dependency providers for all major application components including configuration, AI clients, concurrency control, and statistics tracking.

### Design Pattern Used
- **Dependency Injection Pattern**: Provides centralized dependency management for FastAPI
- **Singleton Pattern**: Uses `@functools.lru_cache()` to ensure single instances of expensive resources
- **Factory Pattern**: Each function acts as a factory for creating/retrieving dependencies
- **Circuit Breaker Pattern**: Graceful handling of AI client initialization failures

### Integration Points
- FastAPI's dependency injection system (`Depends`)
- Configuration management through `core.config`
- AI client initialization through `translator.gemini_helper`
- Statistics tracking through `core.stats`
- Concurrency control using asyncio semaphores

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

### `get_genai_client` Function

```python
@functools.lru_cache()
def get_genai_client(settings: Settings = Depends(get_application_settings)) -> genai.client.Client | None
```

**Description**: Dependency provider that initializes and caches the Google Generative AI client.

**Parameters**:
- `settings: Settings` - Application configuration (injected dependency)

**Returns**: 
- `genai.client.Client | None` - Initialized AI client or None if unavailable

**Behavior**: 
- Only initializes client if AI_PROVIDER is "google-gemini"
- Handles initialization failures gracefully by returning None
- Caches successful client instances
- Logs all initialization attempts and outcomes

**Example Usage**:
```python
@app.post("/translate")
async def translate_text(
    client: genai.client.Client | None = Depends(get_genai_client)
):
    if client is None:
        raise HTTPException(400, "AI client not available")
    
    # Use client for translation
    return await perform_translation(client, text)
```

**Tips/Notes**:
- Returns None instead of raising exceptions for unavailable clients
- Allows application to start even if AI client fails to initialize
- Client availability should be checked before use
- Logs warnings for non-google-gemini providers

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
2. **`get_genai_client()`** - Depends on settings
3. **`get_translation_semaphore()`** - Depends on settings  
4. **`get_stats_store()`** - Independent (no dependencies)

## Error Handling Strategy

### Configuration Errors
- Converted to HTTP 500 exceptions with user-friendly messages
- Detailed errors logged for debugging
- Application fails fast if configuration is invalid

### AI Client Errors
- Gracefully handled by returning None
- Allows application to start without AI capabilities
- Client availability must be checked before use

### Resource Initialization Errors
- Logged with full context
- Application-level fallbacks should be implemented
- Critical dependencies (config) cause startup failure

## Usage Patterns

### Basic Dependency Injection
```python
from fastapi import Depends
from core.dependencies import get_application_settings, get_genai_client

@app.get("/status")
async def get_status(
    settings: Settings = Depends(get_application_settings),
    client: genai.client.Client | None = Depends(get_genai_client)
):
    return {
        "ai_provider": settings.AI_PROVIDER,
        "ai_available": client is not None,
        "max_concurrent": settings.MAX_CONCURRENT_TRANSLATIONS
    }
```

### Rate-Limited Operations
```python
@app.post("/translate")
async def translate_endpoint(
    data: TranslationRequest,
    semaphore: asyncio.Semaphore = Depends(get_translation_semaphore),
    client: genai.client.Client | None = Depends(get_genai_client)
):
    if client is None:
        raise HTTPException(400, "Translation service unavailable")
    
    async with semaphore:
        return await perform_translation(client, data)
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