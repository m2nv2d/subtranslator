# Architecture Overview

## 1. Introduction
This document outlines the architecture of a Flask-based web application designed for translating subtitle files (`.srt` format). Users upload an SRT file, select a target language and a processing speed mode ("normal" or "fast"), and receive a translated SRT file for download. The system leverages the Google Generative AI (Gemini) API via the `google-genai` SDK for translation, employing asynchronous processing for efficiency.

## 2. System Context

**Project Scope**
*   **IN-SCOPE:**
    *   A single-page web application built with Flask, Jinja2, and vanilla JavaScript/CSS.
    *   Handles upload, validation (format `.srt`, size ≤ 2MB), parsing, context detection, chunked asynchronous translation using Google Generative AI, reassembly, and download of SRT files.
    *   Configuration via environment variables (`.env` file) for API keys, target languages, chunk sizes, retry attempts, and log levels.
    *   Basic status feedback on the UI during processing.
    *   Structured error handling with custom exceptions and appropriate HTTP responses.
*   **OUT-OF-SCOPE:**
    *   Support for subtitle formats other than `.srt`.
    *   User accounts, authentication, persistent storage of jobs or files.
    *   Real-time translation progress updates beyond a simple status message.
    *   Horizontal scaling, advanced deployment strategies (CI/CD, containerization), extensive monitoring.

**External Systems / Integrations**
*   **Google Generative AI (Gemini):** Accessed via the `google-genai` Python SDK for context detection and translation tasks. Requires `GEMINI_API_KEY`.
*   **`srt` library (`srt3`):** Used for parsing uploaded SRT files into structured data and reassembling translated data back into SRT format.
*   **`python-dotenv`:** Loads configuration settings from a `.env` file into environment variables at application startup.
*   **`tenacity`:** Provides retry logic for potentially failing external API calls (Gemini).
*   **`asyncio`:** Used for concurrent execution of translation tasks for different subtitle chunks.

## 3. High-Level Architecture & Flow

```
Browser (Client)
│ 1. User visits '/', gets HTML+JS+CSS
│ 2. User selects file (.srt), target language, speed mode
│ 3. User submits form (POST /translate with FormData)
▼
Flask App (`src/app.py` - Single Process)
│  [Startup]
│  • `src/config_loader.py`: Loads & validates .env -> `Config` object
│  • `src/translator/gemini_helper.py`: Initializes single shared `genai.Client` instance
│  • Configures logging, registers error handlers
│
├─ Route `/` (GET):
│   • Renders `templates/index.html`, passing `config.target_languages`
│
├─ Route `/translate` (POST):
│   • Check: Verify `genai_client` initialized successfully.
│   • Receive `file`, `target_lang`, `speed_mode`. Validate `target_lang`.
│   • Save uploaded file to temporary location.
│   • `src/translator/parser.py`: Validate temp file (ext, size), parse using `srt`, chunk into `List[List[SubtitleBlock]]`.
│   • `src/tranlator/context_detector.py`:
│     • Takes first chunk, constructs prompt.
│     • Calls **passed `genai_client`** (selects model based on `speed_mode`).
│     • Uses `tenacity` for retries (hardcoded attempts).
│     • Returns context string (e.g., "cooking tutorial").
│   • `src/translator/chunk_translator.py`:
│     • Uses `asyncio.run()` to call `translate_all_chunks`.
│     • `translate_all_chunks` uses `asyncio.TaskGroup` to run `_translate_single_chunk` concurrently for each chunk.
│     • `_translate_single_chunk`:
│       • Constructs prompt (with context, target_lang).
│       • Calls **passed `genai_client`** async method (selects model based on `speed_mode`, requests JSON).
│       • Uses `tenacity` for retries (hardcoded attempts).
│       • Parses JSON response, updates `SubtitleBlock.translated_content` in-place.
│       • Handles API/parsing errors.
│   • `src/translator/reassembler.py`:
│     • Uses `srt.compose` to merge translated/original blocks into SRT format string.
│     • Encodes string to bytes.
│   • `src/app.py`:
│     • Creates `io.BytesIO` buffer with translated bytes.
│     • Returns response via `send_file` (mimetype `text/srt`, `as_attachment=True`, dynamic filename).
│   • `finally` block: Cleans up temporary file.
│
└─ Static Files (`/static/*`): Serves CSS and JS.
```

## 4. Technology Stack
*   **Languages:** Python 3.x (leveraging `asyncio`), JavaScript (ES6+)
*   **Frameworks/Libraries:**
    *   Backend: Flask, Jinja2
    *   LLM Interaction: `google-genai` SDK
    *   Subtitle Handling: `srt` (from `srt3` package)
    *   Configuration: `python-dotenv`
    *   Concurrency/Retries: `asyncio`, `tenacity`
*   **Databases/Storage:** None (temporary file storage for uploads during request processing only).
*   **Frontend:** Vanilla JavaScript, HTML5, CSS3.
*   **Infrastructure:** Standard Python WSGI deployment (e.g., Gunicorn + Nginx) or Flask development server. Console-based logging.

## 5. Key Architectural Decisions
*   **Flask + Jinja2:** Minimalist framework suitable for a single-page application with straightforward routing and server-side rendering for the initial page load.
*   **`srt` library:** Provides reliable parsing and composition of SRT files, preserving timing and structure.
*   **Asynchronous Chunked Translation:** `asyncio` (`TaskGroup`) is used within `chunk_translator.py` to parallelize API calls to the Gemini service for different subtitle chunks, improving overall throughput. The main Flask route remains synchronous but orchestrates the async work using `asyncio.run`.
*   **Single Shared `genai.Client`:** A single `google-genai` client instance is initialized at application startup (`app.py` using `gemini_helper.py`) and passed as a dependency to modules requiring API access (`context_detector`, `chunk_translator`). This avoids repeated initializations and manages the client lifecycle centrally.
*   **Dependency Injection for Client:** Passing the `genai_client` instance explicitly makes dependencies clear and simplifies testing by allowing mock clients to be injected.
*   **In-Memory Processing (Primarily):** Subtitle data is loaded into memory as `SubtitleBlock` objects after parsing. Translation modifies these objects directly. A temporary file is used only briefly to handle the initial upload before parsing.
*   **Environment-Based Configuration:** `config_loader.py` reads settings (`GEMINI_API_KEY`, `TARGET_LANGUAGES`, etc.) from `.env` or environment variables, validated at startup. Avoids hardcoding sensitive information or deployment-specific settings.
*   **Custom Exceptions & Error Handling:** A dedicated `exceptions.py` defines specific error types. Flask's `@app.errorhandler` decorators in `app.py` catch these exceptions (and others like `tenacity.RetryError`) to return structured JSON error responses with appropriate HTTP status codes.
*   **Client-Side Download Trigger:** The translated SRT is sent as a byte stream; `app.js` uses `fetch` and `Blob`/Object URL APIs to initiate the file download in the user's browser.

## 6. Major System Components
*   **`src/config_loader.py`:** Loads and validates configuration from environment variables/.env into a `models.Config` object.
*   **`src/translator/exceptions.py`:** Defines custom application-specific exception classes (e.g., `ParsingError`, `ChunkTranslationError`).
*   **`src/translator/models.py`:** Contains data structures, notably `SubtitleBlock` (representing a single subtitle entry) and `Config` (holding application configuration).
*   **`src/translator/parser.py`:** Validates uploaded SRT file (path-based), parses its content using the `srt` library, and divides it into chunks of `SubtitleBlock` objects.
*   **`src/translator/gemini_helper.py`:** Responsible solely for initializing the shared `genai.Client` instance using the API key from the `Config`.
*   **`src/tranlator/context_detector.py`:** Determines a high-level context for the subtitles by sending the text from the first chunk to the Gemini API via the passed `genai_client`. Includes retry logic (`tenacity`).
*   **`src/translator/chunk_translator.py`:** Orchestrates the parallel translation of subtitle chunks using `asyncio.TaskGroup`. Each task calls the Gemini API (via the passed `genai_client`) requesting JSON output, handles retries (`tenacity`), parses the response, and updates the `SubtitleBlock` objects.
*   **`src/translator/reassembler.py`:** Takes the list of (potentially translated) `SubtitleBlock` chunks and uses the `srt` library to compose them back into a single SRT formatted byte stream.
*   **`src/app.py`:** The main Flask application file. Initializes the app, configuration, logging, and the shared `genai.Client`. Defines routes (`/`, `/translate`), orchestrates the workflow by calling other modules, manages the temporary upload file, handles errors via decorators, and sends responses.
*   **`templates/index.html`:** The Jinja2 template for the main user interface, including the upload form and status display area. Receives `target_languages` from `app.py`.
*   **`static/js/app.js`:** Client-side JavaScript handling form submission (via `fetch`), validation, UI updates (status messages, button states), and triggering the download of the translated file.
*   **`static/css/style.css`:** Provides styling for the web interface.

## 7. Data Flow & State Management
1.  **Startup:** `app.py` runs `config_loader.load_config()` and `gemini_helper.init_genai_client()` to prepare the `Config` object and the shared `genai_client`.
2.  **Page Load (`GET /`):** `app.py` renders `index.html`, injecting the list of `config.target_languages` into the template for the dropdown menu.
3.  **Translation Request (`POST /translate`):**
    *   Browser sends `FormData` (file, target language, speed mode) via `fetch` (triggered by `app.js`).
    *   `app.py` receives the request, validates `target_lang` against `config.target_languages`.
    *   The uploaded file is saved to a temporary path using `secure_filename`.
    *   `parser.parse_srt` reads the temp file, validates, parses, and chunks it into `List[List[SubtitleBlock]]` (in memory).
    *   `context_detector.detect_context` is called with the first chunk, `speed_mode`, the shared `genai_client`, and `config`. It returns a context string.
    *   `app.py` calls `asyncio.run(chunk_translator.translate_all_chunks(...))` passing context, chunks, language, speed mode, the shared `genai_client`, and `config`.
    *   `chunk_translator` executes multiple `_translate_single_chunk` tasks concurrently. Each task interacts with the Gemini API (using the passed client) and modifies the `translated_content` field of the `SubtitleBlock` objects within its assigned chunk (in memory).
    *   `reassembler.reassemble_srt` generates the final SRT content as bytes from the modified `SubtitleBlock` objects.
    *   `app.py` uses `send_file` to stream the byte data back to the client as a downloadable attachment.
    *   The temporary file is deleted in a `finally` block.
4.  **State:** Application state primarily consists of the immutable `Config` object and the shared `genai.Client` instance created at startup. Request-specific state (like the `SubtitleBlock` objects) exists only within the scope and memory of a single `/translate` request. No database or persistent file storage is used for user data.

## 8. Security & Privacy Considerations
*   **Upload Validation:** `parser.py` checks file extension (`.srt`) and size (≤ 2MB) to mitigate risks from malicious uploads. `werkzeug.utils.secure_filename` is used before saving the temporary file.
*   **In-Memory Processing:** Most data processing occurs on in-memory Python objects, minimizing disk footprint. Temporary upload files are deleted promptly after processing.
*   **API Key Security:** `GEMINI_API_KEY` is loaded from `.env`/environment variables and should not be hardcoded or logged.
*   **Logging:** Configured to avoid logging sensitive data like full subtitle content or API keys (depends on logging implementation details within functions).
*   **Trust Boundary:** User-uploaded content is untrusted. Validation is limited to format and size. The primary interaction is with the trusted Google Generative AI service.
*   **Error Handling:** Specific errors are caught and returned as JSON, avoiding leakage of internal stack traces to the client in production.

## 9. Scalability & Reliability
*   **Scalability:** Designed as a single-process application. Scalability is limited by the CPU and memory resources of the host machine and the rate limits/latency of the external Gemini API. It does not inherently support horizontal scaling.
*   **Reliability:**
    *   Relies heavily on the availability and reliability of the Google Generative AI API.
    *   `tenacity` is used in `context_detector` and `chunk_translator` to automatically retry failed API calls (currently with hardcoded 3 attempts), improving resilience against transient network issues or brief API hiccups.
    *   The application will fail to start or refuse translation requests if the `genai.Client` cannot be initialized (e.g., invalid API key).
    *   Structured error handling prevents crashes on expected failures (e.g., bad uploads, translation errors) and provides informative responses.

## 10. Other Cross-Cutting Concerns
*   **Logging:** Uses Python's standard `logging` module, configured in `app.py` based on the `LOG_LEVEL` setting from the `Config`. Provides basic operational visibility via console output.
*   **Error Handling:** Centralized in `app.py` using `@app.errorhandler` for custom exceptions, `tenacity.RetryError`, standard `HTTPException`s, and generic `Exception`s, ensuring consistent JSON error responses.
*   **Configuration:** Managed centrally via `config_loader.py` and the `Config` data class, sourced from `.env`/environment variables. Validation occurs at startup.
*   **Static Assets:** Vanilla CSS and JavaScript files are served directly by Flask's static file handling. No complex frontend build process is required.