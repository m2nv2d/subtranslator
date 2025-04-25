# Detailed Technical Design

## Introduction
This document describes the concrete code structure, modules, classes, functions, and data types for the Flask‑based subtitle‑translation web app. It is intended for backend and frontend engineers implementing or reviewing the project. It assumes familiarity with Python, Flask, asyncio, Tenacity, Google Generative AI (`google-genai` SDK), JavaScript (`fetch` API), and basic web concepts.

## Table of Contents
- Module Structure & File Organization
- Detailed Component Design
  - src/config_loader.py
  - src/exceptions.py
  - src/models.py
  - src/parser.py
  - src/gemini_helper.py
  - src/context_detector.py
  - src/chunk_translator.py
  - src/reassembler.py
  - src/app.py (Flask routes & orchestration)
- Interfaces & Interaction Patterns
- Workflow / Use Case Examples
- Implementation Notes, Edge Cases, and TODOs
- Testing Considerations

---

## Module Structure & File Organization
Proposed project layout using a `src` directory for application code and structured `tests` directory. Snake_case for files and PascalCase for classes.

```
project_root/
│  .env
│  pyproject.toml
│  README.md
│
├─ src/                     # Main application source code
│  │  __init__.py           # Makes 'src' a package
│  │  app.py                # Flask app instance, routes, entry point
│  │  config_loader.py      # Configuration loading
│  │  exceptions.py         # Custom exceptions
│  │  models.py             # Data models (DTOs, Config)
│  │  parser.py             # SRT parsing and chunking
│  │  gemini_helper.py      # Helper functions for Gemini API
│  │  context_detector.py   # Detect context
│  │  chunk_translator.py   # Translate chunks
│  │  reassembler.py        # Reassemble into SRT format
│
│templates/            # Standard Flask templates folder
│  │    └─ index.html
│  │
│  └─ static/               # Standard Flask static files folder
│     css/
│       │   └─ style.css
│       └─ js/
│           └─ app.js        # Frontend JavaScript for async submission & UI updates
│
└─ tests/                    # Testing directory
   automated/            # Automated tests (unit, integration, etc.)
     │  unit/             # Unit tests for individual components
     │    │ __init__.py
     │    │ test_parser.py
     │    │ test_context_detector.py # Will mock genai.Client methods
     │    │ test_chunk_translator.py # Will mock genai.Client methods
     │    │   └─ ... (other unit tests mirroring src structure)
     │    └─ integration/      # Integration tests for component interactions
     │      __init__.py
     │        └─ test_app_routes.py # Will mock genai.Client at service boundary
     │        └─ ...
     │
     └─ manual/               # Manual test cases, scripts, or related artifacts
```

**Naming conventions:**
*   Files & modules: `snake_case.py`
*   Classes: `PascalCase`
*   Functions / variables: `snake_case`
*   Constants: `UPPER_SNAKE_CASE`

---

## Detailed Component Design

### src/config_loader.py
Purpose: Load and validate environment variables at startup.

Functions and classes
- `load_config() -> Config`
  - Reads `.env` (located in the project root) via python‑dotenv
  - Validates presence of `GEMINI_API_KEY` (logs and exits if missing)
  - Loads optional vars with defaults:
    - `TARGET_LANGUAGES`: String containing comma-separated **full language names** (e.g., `"Vietnamese,French"`). Parses this string into a `List[str]`. (default: `"Vietnamese,French"` which parses to `["Vietnamese", "French"]`)
    - `CHUNK_MAX_BLOCKS`: int (default `100`)
    - `RETRY_MAX_ATTEMPTS`: int (default `6`)
    - `LOG_LEVEL`: str (default `"INFO"`)
  - Returns a `Config` data class instance (defined in `src.models`)

### src/exceptions.py
Custom exception hierarchy for clear error handling within the application.

Classes
- `ValidationError(Exception)`
- `ParsingError(Exception)`
- `ContextDetectionError(Exception)`
- `ChunkTranslationError(Exception)`
- `GenAIClientInitError(Exception)`
- `GenAIRequestError(Exception)`
- `GenAIParsingError(Exception)`

### src/models.py
Data Transfer Objects and configuration model used across the application.

Classes
- `SubtitleBlock`
  - `index: int`
  - `start: datetime`
  - `end: datetime`
  - `content: str`
  - `translated_content: Optional[str] = None`
- `Config`
  - `gemini_api_key: str`
  - `target_languages: List[str]` # List of full language names (e.g., ["Vietnamese", "French"])
  - `chunk_max_blocks: int` # Default to 100
  - `retry_max_attempts: int` # Default to 5
  - `log_level: str`

### src/parser.py
Validates uploaded files before processing. Then use the srt library for parsing and chunking the uploaded srt into an in-memory object. The package is srt3 but still import srt.

Functions
- `parse_srt(file_path: str, chunk_max_blocks: int) -> sub: List[List[SubtitleBlock]]`
  - Ensures file extension is `.srt`
  - Checks `file.content_length <= 2_000_000`
  - Raises `ValidationError` (from `src.exceptions`) on failure
  - Read the file content and use `srt.parse()` to obtain subtitle objects
  - Maps each subtitle block in original content to a `SubtitleBlock` (from `src.models`)
  - Splits blocks into disjoint lists of size `max_blocks`

### src/gemini_helper.py
Facilitates the initialization of the `google-genai` client instance.

Functions
- `init_genai_client(config: Config) -> client: genai.client.Client`
  - Initializes a `genai.client.Client` instance with the API key from the config.
  - Raises `GenAIClientInitError` if initialization fails.

### src/context_detector.py
Obtains a high-level context label from the first blocks by using a mock response or calling the LLM API directly using the `google-genai` SDK via a passed client instance.

Imports
- `tenacity`
- `from google import genai`
- `src.exceptions`
- `src.models`

Function
- `detect_context(`
    `sub: List[List[SubtitleBlock]],`
    `speed_mode: str,` # Values: "mock", "fast", or "normal"
    `genai_client: genai.client.Client,` # (optional) pass the initialized Client instance, only required if speed_mode isn't "mock"
    `config: models.Config` # Pass config for retry settings (required)
  `) -> str`
  - Extracts text from first ~100 lines of the *first chunk* in `sub`.
  - Determine the method to use based on value of `speed_mode`. We have a different generation method for mock, and one for fast or normal.
  - If speed_mode = mock, we just return some random context.
  - If speed_mode is fast or normal, we need to use the passed genai_client instance to make remote API requests for context analysis. Use `tenacity` decorator (configured with `config.retry_max_attempts`) on an internal helper function or directly here to wrap the API call.
  - Returns context string or raises `ContextDetectionError` on failure after retries.

### src/chunk_translator.py
Translates chunks in parallel using asyncio with a mock response or LLM API calls via the `google-genai` SDK using a passed client instance.

Imports
- `asyncio`
- `tenacity`
- `from google import genai`
- `src.exceptions`
- `src.models`

Functions

- `translate_all_chunks(`
    `context: str,`
    `sub: List[List[SubtitleBlock]],`
    `target_lang: str,` # Full language name (e.g., "Vietnamese")
    `speed_mode: str,` # Values: "mock", "fast", or "normal"
    `genai_client: genai.client.Client,` # (optional) pass the initialized Client instance, only required if speed_mode isn't "mock"
    `config: models.Config` # Pass config for retry settings (required)
  `) -> None`
  - Uses `asyncio.gather` to run `_translate_single_chunk` concurrently for each chunk in `sub`, passing `genai_client` (optional) and `config`.
  - Aborts and raises `ChunkTranslationError` on any failure.

- `async _translate_single_chunk(`
    `context: str,`
    `chunk_index: int,`
    `chunk: List[SubtitleBlock],`
    `target_lang: str,` # Full language name (e.g., "Vietnamese")
    `speed_mode: str,` # Values: "mock", "fast", or "normal"
    `genai_client: genai.client.Client,` # (optional) pass the initialized Client instance, only required if speed_mode isn't "mock"
    `config: models.Config` # Pass config for retry settings (required)
  `) -> None`
  - Determine the method to use based on value of `speed_mode`. We have a different generation method for mock, and one for fast or normal.
  - The mock response doesn't do any transaltion, waits for a small period, and for each block in the chunk, copy the original content into the translated field.
  - The method that use real LLMs operates differently. Just add the retry logic with the `tenacity` decorator (configured with `config.retry_max_attempts`) on this function without implementing any logic code that calls the LLM and modify the chunk object (someone else would do that).
  - Raises `ChunkTranslationError` on API failures after all attempt.

### src/reassembler.py
Merges translated blocks back into a single .srt formatted byte stream suitable for direct download.

Function
- `reassemble_srt(sub: List[List[SubtitleBlock]]) -> bytes`
  - Formats each block using srt or manual templating:
    ```
    1
    00:00:01,000 --> 00:00:04,000
    translated line 1
    translated line 2
    ```
  - Encodes the final string to bytes, ready to be sent in the response.

### src/app.py (Flask routes & orchestration)
Entry point for the web app, wiring all components together. Initializes and manages the single `genai.Client` instance. Located within the `src` package. Handles asynchronous requests from the frontend JavaScript.

Imports
- `Flask, request, render_template, send_file, jsonify` from `flask`
- `werkzeug.exceptions` # For standard HTTP errors
- `asyncio`
- `from google import genai`
- `src.config_loader`
- `src.exceptions`
- `src.models`
- `src.parser`
- `src.context_detector`
- `src.chunk_translator`
- `src.reassembler`
- `logging`
- `io`
- `tenacity` # Potentially needed if defining retry config here

Setup
- Load app config via `config_loader.load_config() -> config: models.Config`
- Configure Python logging to console at `config.log_level`.
- Create Flask app instance `app = Flask(__name__)`
- **Instantiate shared Gemini client (Single instance for the app):**
  - `genai_client = None` # Initialize to None
  - `try:`
    - `genai_client = gemini_helper.init_genai_client(config)` # Configure the library globally
    - `logging.info("Gemini Client initialized successfully.")`
  - `except Exception as e:` # Catch potential exceptions during client init (e.g., invalid key format - specifics depend on SDK)
    - `logging.exception("Failed to initialize Gemini Client. App startup failed.")`
    - raise RuntimeError("Critical component (Gemini Client) failed to initialize.") from e # Example: Halt startup

**Error Handling Setup**
- Define custom error handlers using `@app.errorhandler`. These handlers return JSON responses suitable for consumption by the frontend JavaScript.
  - `@app.errorhandler(exceptions.ValidationError)` -> `return jsonify({"error": str(e)}), 400`
  - `@app.errorhandler(exceptions.ParsingError)` -> `return jsonify({"error": str(e)}), 400` or `422`
  - `@app.errorhandler(exceptions.ContextDetectionError)` -> `return jsonify({"error": "Failed to detect context: " + str(e)}), 500`
  - `@app.errorhandler(exceptions.ChunkTranslationError)` -> `return jsonify({"error": "Failed during translation: " + str(e)}), 500`
  - `@app.errorhandler(exceptions.ApiHelperError)` -> `return jsonify({"error": "LLM API Error: " + str(e)}), 502` # Catch errors raised by services
  - `@app.errorhandler(tenacity.RetryError)` -> `return jsonify({"error": "LLM API failed after multiple retries: " + str(e)}), 504` (Gateway Timeout)
  - `@app.errorhandler(werkzeug.exceptions.HTTPException)` -> Handle standard Flask/Werkzeug HTTP errors if needed, returning JSON.
  - `@app.errorhandler(Exception)` -> Generic fallback: `logging.exception("Unhandled error")`, `return jsonify({"error": "An unexpected error occurred"}), 500`

Routes
- `GET /`
  - Renders `templates/index.html`, passing the list of configured languages to the template:
    `return render_template('index.html', languages=config.target_languages)`
- `POST /translate`
  - **Interaction:** This endpoint expects an asynchronous request (e.g., via `fetch` from `static/js/app.js`) containing multipart/form-data (file, target\_lang, speed\_mode).
  - **Check Client:** Add a check at the beginning: `if genai_client is None: return jsonify({"error": "Translation service is unavailable due to initialization failure."}), 503` (Service Unavailable)
  - **Try/Catch Block:** Wrap the core logic in a `try...except` block to catch the custom exceptions and let the JSON error handlers manage the response.
  - Get file: `file = request.files.get('file')` (handle potential missing file)
  - Call `parser.parse_srt(file, config.chunk_max_blocks) -> sub_chunks`
  - Get other parameters: `target_lang = request.form.get('target_lang')` (gets the selected full language name, e.g., "Vietnamese"), `speed_mode = request.form.get('speed_mode', 'normal')`. Add validation to ensure `target_lang` is in `config.target_languages`.
  - Call `context_detector.detect_context(sub_chunks, speed_mode, genai_client, config) -> context` **(Pass the shared client instance & config)**
  - Execute `asyncio.run(chunk_translator.translate_all_chunks(context, sub_chunks, target_lang, speed_mode, genai_client, config))` **(Pass the shared client instance & config)**
  - Call `reassembler.reassemble_srt(sub_chunks) -> translated_srt_bytes`
  - Create in-memory file: `buffer = io.BytesIO(translated_srt_bytes)`
  - **Success Response:** Stream the translated SRT file back using Flask's `send_file`. The frontend JavaScript will handle this response by initiating a download. Ensure appropriate headers (`Content-Disposition`, `Content-Type`) are set by `send_file`.
  - **Error Response:** If any exception occurs and is caught by the error handlers, a JSON response containing the error details will be returned automatically. The frontend JavaScript will parse this JSON and display the error.

---

## Interfaces & Interaction Patterns
- **Frontend Interaction:**
    - User loads `GET /`, which renders `index.html`. `src.app.py` passes the `config.target_languages` to the template.
    - `static/js/app.js` populates the language dropdown.
    - User fills the form (selects file, language, speed mode) and clicks submit.
    - `static/js/app.js` prevents the default form submission. It constructs a `FormData` object and sends an asynchronous `POST` request to `/translate` using the `fetch` API. It updates the UI to show a "processing" state.
- **Backend Processing:**
    - `src/app.py` (`POST /translate`) receives the fetch request.
    - It orchestrates the calls: `src.parser` → `src.context_detector` → `src.chunk_translator` → `src.reassembler`.
    - The single, shared `genai.Client` instance created at startup in `src/app.py` is passed down to `context_detector` and `chunk_translator`.
    - LLM interactions (API calls, prompt engineering, response parsing, retries) are handled within `src.context_detector` and `src.chunk_translator`.
- **Response Handling:**
    - **Success:** `src/app.py` uses `send_file` to stream the reassembled SRT bytes back with a 200 OK status. `static/js/app.js` receives this response, detects success (via `response.ok`), retrieves the data as a `Blob`, and triggers a file download in the user's browser. It updates the UI to show completion.
    - **Error:** If any exception occurs during backend processing, the corresponding `@app.errorhandler` in `src/app.py` catches it and returns a JSON response (e.g., `{"error": "..."}`) with an appropriate HTTP error code (4xx, 5xx). `static/js/app.js` receives this response, detects the error (via `response.ok` being false or checking status code), parses the JSON body, and displays the error message in the UI.
- Flask route (`src.app.py`) remains synchronous but uses `asyncio.run` to execute the core asynchronous translation logic (`translate_all_chunks`).
- No temporary files are saved to disk on the server; the translation happens in memory.

---

## Workflow / Use Case Examples
Example: user uploads `subs.srt`, selects "Vietnamese" and “fast” mode
- `src.config_loader.load_config()` reads `TARGET_LANGUAGES="Vietnamese,French"` and stores `["Vietnamese", "French"]`.
- `src.app` initializes the single `genai.Client` at startup.
- User visits `GET /`. `src.app.py` renders `index.html` with `languages=["Vietnamese", "French"]`. `static/js/app.js` populates the language selector.
- User selects "Vietnamese", "fast" mode, uploads `subs.srt`, and clicks submit.
- `static/js/app.js` prevents default submission, updates UI to "Processing...", creates `FormData`, and sends a `fetch` `POST` request to `/translate`.
- `src.app` (`POST /translate`) receives the request, retrieves `target_lang='Vietnamese'` and `speed_mode='fast'`. Validates "Vietnamese" is allowed.
- `src.parser` checks file, chunks it into lists of `SubtitleBlock` objects.
- `src.app` calls `src.context_detector.detect_context`, passing chunks, `speed_mode`, the shared `genai_client`, and `config`. Context ("cooking tutorial") is returned.
- `src.app` calls `src.chunk_translator.translate_all_chunks` via `asyncio.run`, passing context, chunks, `target_lang`, `speed_mode`, the shared `genai_client`, and `config`. `SubtitleBlock` objects are updated with translations.
- `src.reassembler` combines translated blocks into SRT bytes.
- `src.app` uses `send_file` to return the SRT bytes with a 200 OK status.
- `static/js/app.js` receives the successful `fetch` response, extracts the file data as a `Blob`, programmatically triggers a download named `subs_Vietnamese.srt` (or similar), and updates the UI status to "Translation complete!".

**Error Scenario:** If `chunk_translator` fails after retries (e.g., API outage):
- `ChunkTranslationError` is raised.
- The `@app.errorhandler(exceptions.ChunkTranslationError)` in `src/app.py` catches it.
- The error handler returns `jsonify({"error": "Failed during translation: ..."}), 500`.
- `static/js/app.js` receives the `fetch` response with status 500. It parses the JSON body and displays "Error: Failed during translation: ..." in the UI status area.

---

## Implementation Notes, Edge Cases, and TODOs
- **SDK Methods & Client Initialization:** Verify `google-genai` SDK usage. Ensure client initialization in `app.py` is correct.
- **Target Language Validation:** Ensure `POST /translate` explicitly validates `target_lang` against `config.target_languages`.
- **Filename Generation:** Frontend JavaScript (`app.js`) should ideally generate a meaningful filename for the downloaded file. The backend (`app.py`) could potentially suggest a filename via the `Content-Disposition` header set by `send_file`.
- Error Handling: Robust JSON error responses from `src.app.py` handlers are crucial for the frontend JavaScript. Ensure consistent error format. Handle `genai.Client` initialization failure gracefully (current design halts startup or sets client to `None`, resulting in 503 errors on `/translate`).
- Retry Logic: Implement robust `tenacity` retries in `context_detector` and `chunk_translator`, configured via `config`.
- Handle empty/malformed SRT files gracefully (`ParsingError`).
- Cap `CHUNK_MAX_BLOCKS`.
- **Gemini Client Management:** Single `genai.Client` instance created in `app.py`. Ensure thread safety if needed (check SDK docs). Pass appropriate model names based on `speed_mode`.
- Response Validation: Check in `_translate_single_chunk` for matching line counts.
- **CORS:** If frontend and backend are ever served from different origins, CORS headers will need to be configured in the Flask app.
- TODO: Expose context sample size (currently ~100 lines) as config.
- Logging: Ensure consistent logging, especially around API calls, retries, errors, and client initialization.

---

## Testing Considerations
- **Test Structure:** `tests/` directory with `automated/` (unit, integration) and `manual/`.
- **Automated Tests (`tests/automated/`):**
    - **Unit Tests (`tests/automated/unit/`):** Isolate components. Mock `srt`, file operations, and the passed `genai.Client` methods (`generate_content`, etc.) in `context_detector` and `chunk_translator`. Mock `config`. Test parsing, chunking, context detection logic, translation logic (including concurrency, line count validation), retries, and reassembly. Also include unit tests for `static/js/app.js` (using tools like Jest) to test form handling, fetch calls, response processing (success/error), and UI updates (mocking DOM elements).
    - **Integration Tests (`tests/automated/integration/`):** Test component interactions via Flask test client (`app.test_client()`).
        - `test_app_routes.py`:
            - Test `GET /`: Verify template rendering and `languages` context.
            - Test `POST /translate`: Use the test client to simulate the `fetch` request. Mock the `genai.Client` instance passed to services or patch generation methods. Assert that the response has the correct status code (200 for success, error codes for failures) and the expected `Content-Type` (file stream for success, `application/json` for errors). Verify the content of the JSON error response matches the expected format.
- **Manual Tests (`tests/manual/`):** Checklists, specific SRT files, helper scripts. Test the full UI flow in a browser: upload, select language/mode, observe status updates, verify download on success, verify error message display on failure.
- **End-to-End Tests (Optional):** Tools like Selenium or Playwright could automate browser interactions to test the complete user flow, including JavaScript behavior, against a running application instance.
- **Test Coverage:** High unit test coverage for backend logic (`src/`) and frontend JavaScript (`static/js/`). Integration tests ensure `app.py` orchestrates correctly and returns appropriate responses for JavaScript consumption.
