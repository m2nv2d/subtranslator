# Detailed Technical Design

## Introduction
This document describes the concrete code structure, modules, classes, functions, and data types for the FastAPI‑based subtitle‑translation web app. It is intended for backend and frontend engineers implementing or reviewing the project. It assumes familiarity with Python, FastAPI, asyncio, Tenacity, Google Generative AI (`google-genai` SDK), and basic web concepts.

## Table of Contents
- Module Structure & File Organization
- Detailed Component Design
  - src/core/config.py
  - src/core/dependencies.py 
  - src/core/errors.py
  - src/core/stats.py
  - src/translator/exceptions.py
  - src/translator/models.py
  - src/translator/parser.py
  - src/translator/gemini_helper.py
  - src/translator/context_detector.py
  - src/translator/chunk_translator.py
  - src/translator/reassembler.py
  - src/main.py (FastAPI app instance)
  - src/routers/translate.py (FastAPI routes)
  - src/templates/index.html
  - src/static/css/style.css
  - src/static/js/app.js
- Interfaces & Interaction Patterns
- Workflow / Use Case Examples
- Implementation Notes, Edge Cases, and TODOs
- Testing Considerations

---

## Module Structure & File Organization
Project layout using a `src` directory for application code and structured `tests` directory. Snake_case for files and PascalCase for classes.

```
project_root/
│  .env
│  pyproject.toml
│  README.md
│
├─ src/                     # Main application source code
│  │  __init__.py           # Makes 'src' a package
│  │  main.py               # FastAPI app instance, mounts routers
│  │
│  ├─ core/                 # Core application components
│  │  │  __init__.py        # Makes 'core' a package
│  │  │  config.py          # Configuration using Pydantic Settings
│  │  │  dependencies.py    # FastAPI dependency providers
│  │  │  errors.py          # Error response models and utilities
│  │  │  stats.py           # In-memory application statistics store
│  │
│  ├─ routers/              # FastAPI endpoint routers
│  │  │  __init__.py        # Makes 'routers' a package
│  │  │  translate.py       # Translation endpoints and orchestration
│  │
│  ├─ translator/           # Core translation logic package
│  │  │  __init__.py        # Makes 'translator' a package, exports key functions
│  │  │  exceptions.py      # Custom exceptions
│  │  │  models.py          # Data models (DTOs)
│  │  │  parser.py          # SRT parsing and chunking
│  │  │  gemini_helper.py   # Helper functions for Gemini API
│  │  │  context_detector.py # Detect context
│  │  │  chunk_translator.py # Translate chunks
│  │  │  reassembler.py     # Reassemble translated SRT
│  │
│  ├─ templates/            # Jinja2 templates folder
│  │  │  index.html         # Main upload form template
│  │
│  └─ static/               # Static files folder
│     │  css/
│     │    │  style.css
│     │  └─ js/
│     │      │  app.js
│
└─ tests/                   # Testing directory
   ├─ automated/            # Automated tests (unit, integration, etc.)
   │    │  unit/            # Unit tests for individual components
   │    │    │ __init__.py
   │    │    └─ core/       # Tests for core components (config, stats)
   │    │    └─ translator/ # Unit tests mirroring src/translator structure
   │    │
   │    └─ integration/     # Integration tests for component interactions
   │        │ __init__.py
   │        └─ ...
   │
   ├─ manual/               # Manual test cases and scripts
   │
   └─ samples/              # Sample SRT files for testing
```

**Naming conventions:**
*   Files & modules: `snake_case.py`
*   Classes: `PascalCase`
*   Functions / variables: `snake_case`
*   Constants: `UPPER_SNAKE_CASE`

---

## Detailed Component Design

### src/core/config.py
Purpose: Define and validate application settings using Pydantic.

**Expected .env file format (example):**
```dotenv
TARGET_LANGUAGES=Vietnamese, French
CHUNK_MAX_BLOCKS=100
RETRY_MAX_ATTEMPTS=4
LOG_LEVEL=INFO
AI_PROVIDER=google-gemini
AI_API_KEY=api-key-here
FAST_MODEL=gemini-2.5-flash-preview-04-17
NORMAL_MODEL=gemini-2.5-pro-preview-03-25
MAX_CONCURRENT_TRANSLATIONS=10
```

Classes
- `Settings(BaseSettings)`
  - Uses `pydantic_settings.BaseSettings` for environment variable loading
  - Required string variables: `AI_PROVIDER`, `AI_API_KEY`, `FAST_MODEL`, and `NORMAL_MODEL`. 
  - Optional vars with defaults and extensive validation:
    - `TARGET_LANGUAGES`: Tuple of full language names parsed from comma-separated string (e.g., `"Vietnamese,French"`), defaults to `("Vietnamese", "French")` if invalid or missing. Type changed from `list` to `tuple` for hashability.
    - `CHUNK_MAX_BLOCKS`: Positive integer (default `100`). Validated with Pydantic Field constraints.
    - `RETRY_MAX_ATTEMPTS`: Non-negative integer (default `4`). Validated with Pydantic Field constraints.
    - `LOG_LEVEL`: Valid uppercase log level string (default `"INFO"`, must be one of `["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]`). Validated with custom validator.
    - `MAX_CONCURRENT_TRANSLATIONS`: Positive integer (default `10`). Controls maximum concurrent translation tasks.
  - Model validators for target languages and model names
  - Field validators for log level and target languages

- `get_settings() -> Settings`
  - Locates and reads `.env` from project root via pydantic
  - Initializes and returns a `Settings` instance

### src/core/dependencies.py
Purpose: Provide FastAPI dependencies for settings and AI client.

Functions
- `@functools.lru_cache() get_application_settings() -> Settings`
  - Dependency provider for application settings
  - Cached for reuse across requests
  - Configures logging based on settings
  - Raises HTTPException if settings loading fails
  
- `get_genai_client(settings: Settings = Depends(get_application_settings)) -> genai.client.Client | None`
  - Dependency provider for Generative AI client
  - Initializes client only if `settings.AI_PROVIDER` is "google-gemini"
  - Returns None if provider is different or initialization fails
  - Logs errors but does not raise exceptions, letting route handlers handle them

- `get_translation_semaphore(settings: Settings = Depends(get_application_settings)) -> asyncio.Semaphore`
  - Dependency provider for a global translation semaphore
  - Limits concurrent translation tasks based on `settings.MAX_CONCURRENT_TRANSLATIONS`
  - Uses LRU cache to ensure a single semaphore instance is shared across the application

- `@functools.lru_cache() get_stats_store() -> AppStatsStore`
  - Dependency provider for the application statistics store.
  - Cached to ensure a single `AppStatsStore` instance is shared globally.
  - Initializes the store on the first call.

### src/core/errors.py
Purpose: Standard error response formats and utilities.

Classes
- `ErrorDetail(BaseModel)`
  - Pydantic model for standard error response format
  - `error: str` field to contain error messages

Functions
- `create_error_response(message: str) -> dict`
  - Creates standardized error response dictionaries
  - Returns `{"error": message}`

### src/core/stats.py
Purpose: Define and manage in-memory application statistics.

Classes
- `FileStats(BaseModel)`
  - Pydantic model for tracking statistics of a single file translation request.
  - Fields: `request_id`, `filename`, `file_size`, `status`, `start_time`, `end_time`, `duration_ms`, `total_chunks`, `total_blocks`, `failed_chunks`.

- `TotalStats(BaseModel)`
  - Pydantic model for tracking aggregated application statistics.
  - Fields: `total_files_processed`, `total_translation_failures`, `total_successful_translations`, `last_updated`.

- `AppStatsStore`
  - Manages the in-memory storage of statistics using dictionaries.
  - Provides thread-safe methods (using locks) to:
    - `create_file_entry`: Initialize stats for a new file request.
    - `update_parsing_stats`: Update stats after parsing.
    - `update_translation_stats`: Update stats after translation attempts.
    - `complete_request`: Mark a request as completed or failed, updating total stats.
    - `get_stats`: Retrieve current `TotalStats` and a dictionary of `FileStats`.

### src/translator/exceptions.py
Custom exception hierarchy for clear error handling within the application.

Classes
- `ValidationError(Exception)`
- `ParsingError(Exception)`
- `ContextDetectionError(Exception)`
- `ChunkTranslationError(Exception)`
- `GenAIClientInitError(Exception)`
- `GenAIRequestError(Exception)`
- `GenAIParsingError(Exception)`

### src/translator/models.py
Data Transfer Objects used across the application.

Classes
- `SubtitleBlock`
  - `index: int`
  - `start: datetime`
  - `end: datetime`
  - `content: str`
  - `translated_content: Optional[str] = None`

- `TranslatedBlock(BaseModel)`
  - `index: int` - The subtitle index
  - `translated_text: str` - The translated text content

- `TranslatedChunk(BaseModel)`
  - `translations: list[TranslatedBlock]` - List of translated blocks (Type hint updated to use `list`)

### src/translator/parser.py
Validates SRT files and parses them into subtitle blocks.

Imports
- `datetime`
- `typing.List, Optional`
- `srt`
- `translator.exceptions`
- `translator.models`

Functions
- `async parse_srt(file_path: str, chunk_max_blocks: int) -> list[list[models.SubtitleBlock]]`
  - Validates file extension and size
  - Reads and parses SRT content asynchronously 
  - Maps subtitle blocks to `models.SubtitleBlock` objects
  - Splits blocks into chunks of size `chunk_max_blocks`
  - Raises appropriate exceptions for validation and parsing failures

### src/translator/gemini_helper.py
Facilitates the initialization of the `google-genai` client instance.

Functions
- `init_genai_client(settings: Settings) -> genai.client.Client`
  - Initializes a `genai.client.Client` instance with the API key from `settings.AI_API_KEY`
  - Raises `GenAIClientInitError` if initialization fails

### src/translator/context_detector.py
Obtains a high-level context label from the first blocks.

Functions
- `async detect_context(`
    `sub: List[List[models.SubtitleBlock]],`
    `speed_mode: str,` # "mock", "fast", or "normal"
    `client: Optional[genai.client.Client],` 
    `settings: Settings`
  `) -> str`
  - Returns mock context if `speed_mode="mock"`
  - Uses appropriate model from settings based on `speed_mode`
  - Constructs request with `types.Content` and `types.Part` for proper prompt formatting
  - Makes async API requests to Gemini if necessary
  - Implements retry logic with tenacity
  - Returns context string describing the content

### src/translator/chunk_translator.py
Translates chunks in parallel using asyncio.

Functions
- `@configurable_retry`
  - Decorator that provides customizable retry behavior for translation functions
  - Uses tenacity for retry logic
  - Configures retry attempts based on settings
  - Returns a tuple `(retries, failed)` indicating the number of retries and if the final attempt failed.

- `async _translate_single_chunk(`
    `chunk_index: int,`
    `chunk: List[models.SubtitleBlock],`
    `system_prompt: str,`
    `speed_mode: str,` 
    `genai_client: Optional[genai.client.Client],`
    `settings: Settings,`
    `semaphore: asyncio.Semaphore,`
  `) -> None`
  - Acquires semaphore before translation to limit concurrent operations
  - Uses mock translation for `speed_mode="mock"`
  - Creates structured schema using `genai.types.Schema` to enforce JSON structure
  - Constructs request with `types.Content` and `types.Part` for proper prompt formatting
  - Makes async API calls for "fast"/"normal" modes with response_schema parameter
  - Uses Pydantic validation (TranslatedChunk model) to parse and validate JSON responses
  - Updates `translated_content` in chunk objects based on validated response
  - Applies retry logic via the `@configurable_retry` decorator (returns retry count and failure status).
  - Raises appropriate exceptions for API and parsing failures

- `async translate_all_chunks(`
    `context: str,`
    `sub: List[List[models.SubtitleBlock]],`
    `target_lang: str,` 
    `speed_mode: str,` 
    `client: Optional[genai.client.Client],`
    `settings: Settings,`
    `semaphore: asyncio.Semaphore,`
  `) -> tuple[int, int]`
  - Uses `asyncio.TaskGroup` for concurrent translation
  - Creates tasks for each chunk using `_translate_single_chunk`
  - Collects and reports on failed chunks
  - Returns a tuple containing the total number of chunks processed and the number of chunks that failed translation.

### src/translator/reassembler.py
Merges translated blocks back into a single SRT formatted string or bytes.

Function
- `reassemble_srt(sub: list[list[models.SubtitleBlock]]) -> str`
  - Uses the `srt` library to format blocks
  - Uses `translated_content` if available, otherwise original `content`
  - Returns SRT formatted string

### src/main.py
Entry point for the FastAPI app, configuring middleware, mounts, and exception handlers.

Imports
- `FastAPI`, related dependencies from `fastapi`
- `JSONResponse` for error responses
- `tenacity.RetryError` for retry failure handling
- `translator` module exceptions and functions
- `core.config`, `core.errors`, `core.dependencies`
- `routers.translate`

Setup
- Create FastAPI app instance `app = FastAPI(title="Subtranslator")`
- Mount static files `app.mount("/static", StaticFiles(directory=static_path), name="static")`
- Include the translate router `app.include_router(translate_router)`
- Register exception handlers for all custom exception types
  - `ValidationError` → 400 (Bad Request)
  - `ParsingError` → 422 (Unprocessable Entity)
  - `ContextDetectionError` → 500 (Internal Server Error)
  - `ChunkTranslationError` → 500 (Internal Server Error)
  - `RetryError` → 504 (Gateway Timeout)
  - `HTTPException` → Various status codes
  - `Exception` → 500 (Internal Server Error)

### src/routers/translate.py
Handles translation endpoints and orchestration.

Imports
- `FastAPI` router and related dependencies
- `Jinja2Templates` for HTML templates
- `google.genai` for Gemini client
- `translator` module functions and exceptions
- `core.config`, `core.errors`, `core.dependencies`
- `aiofiles` for asynchronous file operations

Setup
- Create router instance `router = APIRouter()`
- Initialize Jinja2 templates for HTML rendering

Routes
- `GET /`
  - Renders the main upload form using `templates/index.html`
  - Passes available target languages from settings
  - Returns HTML response

- `POST /translate`
  - Accepts SRT file upload, target language, and speed mode
  - Validates inputs (file type, language)
  - Checks if AI client is available when needed based on speed mode
  - Injects `AppStatsStore` dependency for statistics tracking.
  - Orchestrates the translation workflow:
    1. Create an entry in the `AppStatsStore`.
    2. Save uploaded file to temporary location using aiofiles.
    3. Parse SRT into chunks, update stats store with parsing results.
    4. Detect context.
    5. Translate chunks asynchronously with semaphore-based concurrency limits, update stats store with translation results (total chunks, failed chunks).
    6. Reassemble SRT.
    7. Mark request as completed in stats store.
    8. Return translated SRT as downloadable file.
  - Uses try/finally blocks for cleanup operations
  - Updates stats store to mark request as failed if exceptions occur during processing.
  - Handles exceptions with appropriate HTTP error responses
  - Ensures temporary files are cleaned up regardless of success or failure

- `GET /stats`
  - Accepts `AppStatsStore` dependency.
  - Calls `stats_store.get_stats()` to retrieve current statistics.
  - Returns a JSON response containing `TotalStats` and a dictionary of `FileStats`.

### src/templates/index.html
Renders the primary user interface using Jinja2 templates.

Key Components & Requirements:
-   Standard HTML5 structure.
-   Links to static CSS and JavaScript files
-   A main form (`id="translate-form"`, `enctype="multipart/form-data"`) containing:
    -   File input (`name="file"`, `accept=".srt"`, required).
    -   Target language select (`name="target_lang"`, required) populated from settings.
    -   Speed mode select (`name="speed_mode"`, values "normal", "fast", "mock", default "normal").
    -   Submit button (`id="submit-button"`).
-   A status display area (`id="status-message"`) for feedback from `app.js`.

### src/static/js/app.js
Handles client-side interactivity and communication with the backend.

Key Logic & Requirements:
-   Intercepts form submission and handles it asynchronously
-   Validates inputs client-side
-   Shows processing status to the user
-   Handles successful translation by triggering download
-   Displays errors in user-friendly format
-   Updates UI state based on processing status

### src/static/css/style.css
Provides visual styling for the web interface.

## Interfaces & Interaction Patterns
- Request flow (conceptual):
  - `src.main` receives request → Router handles it → Translation workflow in `translate.py` → Return response
- FastAPI dependency injection provides `settings`, `genai_client`, and `semaphore`
- LLM interactions in `context_detector.py` and `chunk_translator.py` use `client` passed from router
- The `genai_client` is created only if `settings.AI_PROVIDER` is "google-gemini" 
- Router endpoints check client availability based on request requirements
- Frontend interaction handled via HTML forms and JavaScript
- Concurrency management using global semaphore to limit parallel translation tasks

## Workflow / Use Case Examples
**Example: `AI_PROVIDER=google-gemini`, user selects "fast" mode**
- Application starts, `dependencies.py` initializes settings, client, and semaphore
- User visits `/`, form loads with languages from settings
- User submits with `speed_mode='fast'`
- Router validates inputs and checks if client exists (returns 503 if not)
- Router orchestrates translation workflow:
  - Parse SRT file into chunks
  - Detect context using client and fast model
  - Translate chunks concurrently using client and fast model, limited by semaphore 
  - Reassemble and return translated file
- Client browser downloads the translated file

## Implementation Notes, Edge Cases, and TODOs
- **Async Design:** The application is fully asynchronous using FastAPI, asyncio, aiofiles, and TaskGroup
- **Dependency Injection:** Settings, AI client, and semaphore provided through FastAPI dependency injection
- **Error Handling:** Comprehensive exception catching and mapping to HTTP responses
- **Concurrency Control:** Global semaphore limits concurrent translation requests
- **Retries:** Configurable retry behavior using tenacity and custom decorator
- **Configurable Models:** Both fast and normal model names can be configured
- **Client Management:** Single client instance managed through dependency injection
- **Validation:** Input validation at multiple levels (Pydantic, request handlers, parsers)
- **Exception Grouping:** Uses Python 3.11 exception groups for structured error handling
- **Resource Cleanup:** Robust temporary file cleanup in finally blocks
- **TODO:** Consider making context sample size configurable
- **TODO:** Implement more robust response validation for LLM responses
- **TODO:** Add more comprehensive logging for production troubleshooting
- **TODO:** Consider adding caching for frequent translations

## Testing Considerations
- **Test Structure:**
  - `tests/automated/unit/` for component unit tests (e.g., `core/test_stats.py`, `translator/test_parser.py`)
  - `tests/automated/integration/` for integration tests (e.g., testing the full `/translate` and `/stats` endpoints)
  - `tests/manual/` for manual testing scripts
  - `tests/samples/` for sample SRT files

- **Testing Strategies:**
  - Mock FastAPI dependencies for unit testing (`Settings`, `genai.Client`, `AppStatsStore`).
  - Test configuration loading with various environment values.
  - Mock Gemini client and responses for predictable test results.
  - Test client availability handling in route handlers.
  - Test all exception paths and error responses.
  - Test file upload and download workflows.
  - Test concurrency control with semaphore.
  - Test statistics tracking and the `/stats` endpoint for accuracy and correct updates.
  - Use `pytest-asyncio` for testing asynchronous code paths effectively.
  - Note: Some previous test files (e.g., `test_error_models.py`, `test_pydantic_settings.py`) might have been removed or refactored during development; ensure necessary coverage exists in current tests.