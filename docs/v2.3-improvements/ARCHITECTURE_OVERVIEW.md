# Architecture Overview

## 1. Introduction
This document outlines the architecture of a FastAPI-based web application designed for translating subtitle files (`.srt` format). Users upload an SRT file, select a target language and a processing speed mode ("normal", "fast", or "mock"), and receive a translated SRT file for download. The system leverages the Google Generative AI (Gemini) API via the `google-genai` SDK for translation, employing asynchronous processing for efficiency.

## 2. System Context

**Project Scope**
*   **IN-SCOPE:**
    *   A single-page web application built with FastAPI, Jinja2, and vanilla JavaScript/CSS.
    *   Handles upload, validation (format `.srt`, size ≤ 2MB), parsing, context detection, chunked asynchronous translation using Google Generative AI, reassembly, and download of SRT files.
    *   Configuration via environment variables (`.env` file) using Pydantic Settings for API keys, target languages, chunk sizes, retry attempts, log levels, and concurrency limits.
    *   Basic status feedback on the UI during processing.
    *   Structured error handling with custom exceptions and appropriate HTTP responses.
*   **OUT-OF-SCOPE:**
    *   Support for subtitle formats other than `.srt`.
    *   User accounts, authentication, persistent storage of jobs or files.
    *   Real-time translation progress updates beyond a simple status message.
    *   Horizontal scaling, advanced deployment strategies (CI/CD, containerization), extensive monitoring.

**External Systems / Integrations**
*   **Google Generative AI (Gemini):** Accessed via the `google-genai` Python SDK for context detection and translation tasks. Requires `AI_API_KEY`.
*   **`srt` library:** Used for parsing uploaded SRT files into structured data and reassembling translated data back into SRT format.
*   **`pydantic` and `pydantic-settings`:** Used for configuration validation and loading from `.env` file.
*   **`tenacity`:** Provides retry logic for potentially failing external API calls (Gemini).
*   **`asyncio`:** Used for concurrent execution of translation tasks for different subtitle chunks using TaskGroup.
*   **`aiofiles`:** Used for asynchronous file operations.

## 3. High-Level Architecture & Flow

```
Browser (Client)
│ 1. User visits '/', gets HTML+JS+CSS
│ 2. User selects file (.srt), target language, speed mode
│ 3. User submits form (POST /translate with FormData)
▼
FastAPI App (`src/main.py` with `src/routers/translate.py`)
│  [Startup]
│  • `src/core/config.py`: Defines Settings model with Pydantic
│  • `src/core/dependencies.py`: Provides settings, genai client, translation semaphore, and stats store dependencies
│  • `src/core/stats.py`: Defines `AppStatsStore` and related models for in-memory statistics
│  • `src/translator/gemini_helper.py`: Initializes genai.Client instance as dependency
│  • Configures logging, mounts static files, registers error handlers
│
├─ Route `/` (GET) - in routers/translate.py:
│   • Renders `templates/index.html` using Jinja2Templates, passing `settings.TARGET_LANGUAGES`
│
├─ Route `/translate` (POST) - in routers/translate.py:
│   • Injects dependencies: `settings: Settings`, `genai_client: Client | None`, `semaphore: asyncio.Semaphore`, and `stats_store: AppStatsStore`
│   • Check: Verify `genai_client` initialized successfully if needed for speed_mode.
│   • Receive `file: UploadFile`, `target_lang`, `speed_mode`. Validate `target_lang`.
│   • Call `stats_store.create_file_entry` to initialize tracking.
│   • Create temporary directory and save uploaded file asynchronously using aiofiles.
│   • `src/translator/parser.py`: Validate temp file (ext, size), parse using `srt`, chunk into `list[list[SubtitleBlock]]`. Update stats store.
│   • `src/translator/context_detector.py`:
│     • Takes first chunk, constructs prompt.
│     • Uses **injected `client`** (selects model based on `speed_mode`).
│     • Uses structured requests with `types.Content` and `types.Part`.
│     • Uses `tenacity` for retries.
│     • Returns context string (e.g., "cooking tutorial").
│   • `src/translator/chunk_translator.py`:
│     • Uses `asyncio.TaskGroup()` to run `_translate_single_chunk` concurrently for each chunk.
│     • `_translate_single_chunk`:
│       • Uses `@configurable_retry` decorator for retry logic
│       • Acquires semaphore to limit concurrent operations
│       • Constructs prompt (with context, target_lang).
│       • Defines structured schema using `genai.types.Schema` for JSON output
│       • Uses **injected `client`** async method (selects model based on `speed_mode`, requests structured JSON).
│       • Validates JSON response using Pydantic models (`TranslatedChunk` and `TranslatedBlock`)
│       • Updates `SubtitleBlock.translated_content` in-place based on validated data.
│       • Handles API/parsing errors.
│       • Update stats store with translation results (failed chunks, total chunks).
│   • `src/translator/reassembler.py`:
│     • Uses `srt.compose` to merge translated/original blocks into SRT format string.
│   • `src/routers/translate.py`:
│     • Update stats store marking request completion (success/failure).
│     • Returns response via `StreamingResponse` with appropriate headers for download.
│   • Uses `try/finally` blocks to ensure temporary files are cleaned up.
│
├─ Route `/stats` (GET) - in routers/translate.py:
│   • Injects dependency: `stats_store: AppStatsStore`
│   • Calls `stats_store.get_stats()`.
│   • Returns JSON response with `TotalStats` and dictionary of `FileStats`.
│
└─ Static Files (`/static/*`): Serves CSS and JS via FastAPI.StaticFiles mounting.
```

## 4. Technology Stack
*   **Languages:** Python 3.11+ (leveraging `asyncio` TaskGroup and ExceptionGroups), JavaScript (ES6+)
*   **Frameworks/Libraries:**
    *   Backend: FastAPI, Jinja2, Uvicorn
    *   LLM Interaction: `google-genai` SDK
    *   Subtitle Handling: `srt`
    *   Configuration: Pydantic Settings
    *   Validation: Pydantic models for LLM response validation
    *   Concurrency/Retries: `asyncio`, `tenacity`, `aiofiles`
*   **Databases/Storage:** None (temporary file storage for uploads during request processing only).
*   **Frontend:** Vanilla JavaScript, HTML5, CSS3.
*   **Infrastructure:** Uvicorn ASGI server, optionally behind a reverse proxy like Nginx. Console-based logging.

## 5. Key Architectural Decisions
*   **FastAPI + Dependency Injection:** Modern, high-performance ASGI framework with built-in dependency injection for providing settings, clients, and semaphores to route handlers. Enables cleaner code organization and simplifies testing.
*   **Async-first Design:** FastAPI's native support for asynchronous request handling allows for efficient I/O operations without blocking the server. All translation-related functions are implemented as async.
*   **Concurrency Control with Semaphore:** Global semaphore limits the number of concurrent translation operations to prevent overloading the Gemini API or local resources.
*   **Structured Router Organization:** Routes are organized in dedicated router modules, making the codebase more maintainable as it grows.
*   **Pydantic Settings:** Configuration management is handled through Pydantic Settings models with strong validation and typing.
*   **Resource Cleanup:** Explicit try/finally blocks ensure temporary resources are properly cleaned up regardless of success or failure.
*   **`srt` library:** Provides reliable parsing and composition of SRT files, preserving timing and structure.
*   **Asynchronous Chunked Translation:** Concurrent API calls to the Gemini service for different subtitle chunks using `asyncio.TaskGroup`, improving overall throughput while managing concurrency.
*   **Dependency-Injected Gemini Client:** The `google-genai` client instance is provided as a FastAPI dependency, making it available to route handlers and services that need it. This simplifies testing and ensures a single instance is shared.
*   **In-Memory Processing (Primarily):** Subtitle data is loaded into memory as `SubtitleBlock` objects after parsing. Translation modifies these objects directly. A temporary file is used only briefly to handle the initial upload before parsing.
*   **In-Memory Statistics:** Application-level statistics (total files, failures, etc.) and per-request statistics are tracked in memory using a singleton `AppStatsStore` provided via dependency injection.
*   **Environment-Based Configuration:** Settings class reads configuration from `.env` or environment variables, with validation at startup.
*   **Custom Exceptions & Error Handling:** Custom exception types with FastAPI's exception handlers to return structured error responses with appropriate HTTP status codes. Uses Python 3.11's ExceptionGroups for structured concurrent error handling.
*   **Client-Side Download Trigger:** The translated SRT is sent as a stream with appropriate headers to trigger download in the browser.
*   **Structured Output with JSON Schema:** Uses Gemini's schema validation capabilities combined with Pydantic models to enforce structured JSON responses, ensuring consistent and valid output formats.

## 6. Major System Components
*   **`src/main.py`:** The FastAPI application entry point. Configures the app, mounts static files, registers exception handlers, and includes routers.
*   **`src/core/config.py`:** Defines the `Settings` class using Pydantic for configuration management, including concurrency settings.
*   **`src/core/dependencies.py`:** Provides FastAPI dependencies for settings, the Gemini client, the translation semaphore, and the application statistics store.
*   **`src/core/errors.py`:** Contains error response models and utilities.
*   **`src/core/stats.py`:** Defines the `AppStatsStore` class and `FileStats`, `TotalStats` models for managing in-memory application statistics.
*   **`src/routers/translate.py`:** Contains the translation and statistics route handlers, orchestrating the workflow by calling translator modules and the stats store.
*   **`src/translator/exceptions.py`:** Defines custom application-specific exception classes.
*   **`src/translator/models.py`:** Contains data structures, notably `SubtitleBlock` representing a single subtitle entry, and Pydantic models `TranslatedBlock` and `TranslatedChunk` for validating Gemini API responses.
*   **`src/translator/parser.py`:** Validates uploaded SRT file, parses its content using the `srt` library, and divides it into chunks of `SubtitleBlock` objects.
*   **`src/translator/gemini_helper.py`:** Responsible for initializing the Gemini client with the API key from Settings.
*   **`src/translator/context_detector.py`:** Determines a high-level context for the subtitles using the Gemini API. Includes retry logic and uses structured requests via `types.Content` and `types.Part`.
*   **`src/translator/chunk_translator.py`:** Orchestrates the parallel translation of subtitle chunks using TaskGroup. Each task calls the Gemini API with a structured JSON schema, handles retries using the configurable_retry decorator, validates the response with Pydantic models, and updates the `SubtitleBlock` objects.
*   **`src/translator/reassembler.py`:** Takes the list of translated `SubtitleBlock` chunks and composes them back into a single SRT formatted string.
*   **`src/templates/index.html`:** The Jinja2 template for the main user interface.
*   **`src/static/js/app.js`:** Client-side JavaScript handling form submission, validation, UI updates, and file download.
*   **`src/static/css/style.css`:** Provides styling for the web interface.

## 7. Data Flow & State Management
1.  **Startup:** FastAPI initializes dependencies on first request, creating Settings, the Gemini client, the translation semaphore, and the stats store as needed.
2.  **Page Load (`GET /`):** `routers/translate.py` renders `index.html` via Jinja2Templates, injecting the list of languages into the template.
3.  **Translation Request (`POST /translate`):**
    *   Browser sends `FormData` (file, target language, speed mode) via `fetch` from `app.js`.
    *   The route handler receives the request with injected dependencies (settings, genai_client, semaphore, stats_store).
    *   `stats_store.create_file_entry` is called.
    *   A temporary directory is created and the uploaded file is saved asynchronously using `aiofiles`.
    *   `parser.parse_srt` reads the temp file, validates, parses, and chunks it into `list[list[SubtitleBlock]]`. Stats are updated.
    *   `context_detector.detect_context` is called with the first chunk, `speed_mode`, the injected client, and settings.
    *   The route handler awaits `chunk_translator.translate_all_chunks(...)` passing context, chunks, language, speed mode, client, settings, and semaphore.
    *   `chunk_translator` creates tasks in a TaskGroup to execute multiple `_translate_single_chunk` operations concurrently, each acquiring the semaphore before processing.
    *   Each translation task modifies the `translated_content` field of each `SubtitleBlock` object.
    *   `reassembler.reassemble_srt` generates the final SRT content from the modified `SubtitleBlock` objects.
    *   The final status (success/failure) is recorded in the stats store.
    *   The route handler returns a `StreamingResponse` with the content to be downloaded.
    *   The temporary directory and its contents are cleaned up in a finally block.
4.  **Stats Request (`GET /stats`):**
    *   The route handler receives the request with the injected `stats_store` dependency.
    *   `stats_store.get_stats()` is called.
    *   A JSON response containing the current statistics is returned.
5.  **State:** Application state consists of the settings loaded from the environment, the shared Gemini client, the global translation semaphore, and the global `AppStatsStore` instance created as dependencies. Request-specific state exists only within the scope of a single request. No database or persistent storage is used.

## 8. Security & Privacy Considerations
*   **Upload Validation:** File extension and size checks to mitigate risks from malicious uploads. Secure filename handling before saving temporary files.
*   **In-Memory Processing:** Most data processing occurs on in-memory Python objects, minimizing disk footprint. Temporary upload files are deleted promptly after processing using try/finally blocks.
*   **API Key Security:** `AI_API_KEY` is loaded from `.env`/environment variables and protected through Pydantic Settings.
*   **Logging:** Configured to avoid logging sensitive data like full subtitle content or API keys.
*   **Trust Boundary:** User-uploaded content is untrusted. Validation is limited to format and size. The primary interaction is with the trusted Google Generative AI service.
*   **Error Handling:** Specific errors are caught and returned as structured responses, avoiding leakage of internal details to the client.
*   **Testing:** The component-based design with dependency injection facilitates unit testing (including mocking the stats store) and integration testing (testing the `/stats` endpoint).
*   **Concurrency Management:** Global semaphore controls the maximum number of concurrent translation operations, preventing resource exhaustion.

## 9. Scalability & Reliability
*   **Scalability:** FastAPI's ASGI design provides better performance than traditional WSGI frameworks. The application can handle more concurrent requests due to its asynchronous nature. Concurrency is controlled via a semaphore to prevent overloading external services or local resources. However, it is still designed as a single-process application, with scalability ultimately limited by the rate limits and latency of the external Gemini API.
*   **Reliability:**
    *   Relies on the availability and reliability of the Google Generative AI API.
    *   `tenacity` is used with a custom decorator to automatically retry failed API calls, improving resilience against transient issues.
    *   Structured JSON schemas coupled with Pydantic validation ensure consistent and well-formed responses from the Gemini API.
    *   The application will properly handle cases where the Gemini client cannot be initialized, returning appropriate error responses.
    *   Comprehensive exception handling with ExceptionGroups prevents crashes on expected failures and provides informative responses.
    *   Try/finally blocks ensure cleanup operations complete regardless of success or failure.

## 10. Other Cross-Cutting Concerns
*   **Logging:** Uses Python's standard `logging` module, configured based on settings. Provides operational visibility via console output.
*   **Error Handling:** Implemented through FastAPI's exception handlers and Python 3.11's ExceptionGroups, ensuring consistent structured responses for various error types.
*   **Configuration:** Managed through Pydantic Settings with strong validation and typing, sourced from `.env`/environment variables.
*   **Static Assets:** Static files are mounted and served by FastAPI's StaticFiles middleware. No complex frontend build process is required.
*   **Testing:** The component-based design with dependency injection facilitates unit testing (including mocking the stats store) and integration testing (testing the `/stats` endpoint).
*   **Concurrency Management:** Global semaphore controls the maximum number of concurrent translation operations, preventing resource exhaustion.