# Detailed Technical Design

## Introduction
This document describes the concrete code structure, modules, classes, functions, and data types for the Flask‑based subtitle‑translation web app. It is intended for backend and frontend engineers implementing or reviewing the project. It assumes familiarity with Python, Flask, asyncio, and basic web concepts.

## Table of Contents
- Module Structure & File Organization
- Detailed Component Design
  - src/config_loader.py
  - src/exceptions.py
  - src/models.py
  - src/services/validator.py
  - src/services/parser.py
  - src/services/context_detector.py
  - src/services/chunk_translator.py
  - src/services/llm_helper.py
  - src/services/reassembler.py
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
│  requirements.txt
│  README.md
│
├─ src/                     # Main application source code
│  │  __init__.py           # Makes 'src' a package
│  │  app.py                # Flask app instance, routes, entry point
│  │  config_loader.py      # Configuration loading
│  │  exceptions.py         # Custom exceptions
│  │  models.py             # Data models (DTOs, Config)
│  │
│  ├─ services/             # Core business logic modules
│  │    ├─ __init__.py
│  │    ├─ validator.py
│  │    ├─ parser.py
│  │    ├─ context_detector.py
│  │    ├─ chunk_translator.py
│  │    ├─ llm_helper.py
│  │    └─ reassembler.py
│  │
│  ├─ templates/            # Standard Flask templates folder
│  │    └─ index.html
│  │
│  └─ static/               # Standard Flask static files folder
│       ├─ css/
│       │   └─ style.css
│       └─ js/
│           └─ app.js
│
└─ tests/                    # Testing directory
     ├─ automated/            # Automated tests (unit, integration, etc.)
     │    ├─ unit/             # Unit tests for individual components
     │    │   ├─ __init__.py
     │    │   ├─ test_validator.py
     │    │   ├─ test_parser.py
     │    │   └─ ... (other unit tests mirroring src structure)
     │    └─ integration/      # Integration tests for component interactions
     │        ├─ __init__.py
     │        └─ test_app_routes.py
     │        └─ ...
     │
     └─ manual/               # Manual test cases, scripts, or related artifacts
          ├─ test_cases.md     # Example: Manual test scenarios
          └─ upload_script.py  # Example: Helper script for manual testing
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
    - `TARGET_LANGUAGES`: List[str] (default `["vi","fr"]`)
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
- `ApiHelperError(Exception)`

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
  - `target_languages: List[str]`
  - `chunk_max_blocks: int`
  - `retry_max_attempts: int`
  - `log_level: str`

### src/services/validator.py
Validates uploaded files before processing.

Function
- `validate_upload(file: FileStorage) -> None`
  - Ensures file extension is `.srt`
  - Checks `file.content_length <= 2_000_000`
  - Raises `ValidationError` (from `src.exceptions`) on failure

### src/services/parser.py
Wraps the srt library for parsing and chunking.

Functions
- `parse_srt(content: str, max_blocks: int) -> sub: List[List[SubtitleBlock]]`
  - Uses `srt.parse(content)` to obtain subtitle objects
  - Maps each subtitle block in original content to a `SubtitleBlock` (from `src.models`)
  - Splits blocks into disjoint lists of size `max_blocks`

### src/services/context_detector.py
Obtains a high-level context label from the first blocks.

Function
- `detect_context(sub: List[List[SubtitleBlock]], llm_helper: LlmHelper) -> str`
  - Extracts text from first ~100 lines of the *first chunk* in `sub`.
  - Calls `llm_helper.detect_context(text_chunk)`. **Note: `llm_helper` instance is passed in.**
  - Returns a context string or raises `ContextDetectionError` (wrapping any `ApiHelperError`).

### src/services/chunk_translator.py
Translates chunks in parallel using asyncio.

Functions
- `translate_all_chunks(`
    `context: str,`
    `sub: List[List[SubtitleBlock]],`
    `target_lang: str,`
    `speed_mode: str,`
    `llm_helper: LlmHelper`  # Pass the LlmHelper instance
  `) -> None`
  - Uses `asyncio.gather` to run `_translate_single_chunk` concurrently for each chunk in `sub`, passing the `llm_helper` instance.
  - Consider using `return_exceptions=True` in `gather` for more robust error handling if partial success is desired.
  - Aborts and raises `ChunkTranslationError` on any failure (unless using `return_exceptions=True`, then aggregate/handle errors).
- `async _translate_single_chunk(`
    `context: str,`
    `chunk_index: int,` # Add index for better context/logging
    `chunk: List[SubtitleBlock],`
    `target_lang: str,`
    `speed_mode: str,`
    `llm_helper: LlmHelper` # Pass the LlmHelper instance
  `) -> None`
  - Prepares list of `content` strings from the `chunk`.
  - Calls `llm_helper.translate_chunk(context, target_lang, speed_mode, chunk_index, lines)`.
  - **Important:** Validates that the number of translated lines returned matches the number of blocks in the input `chunk`. Raises `ChunkTranslationError` if mismatched.
  - Assigns the returned `translated_content` back to the corresponding `SubtitleBlock` objects in the `chunk` list (modifies them in place).

### src/services/llm_helper.py
Purpose: Centralized LLM API calls with retry logic using Tenacity. Manages interaction with the configured LLM provider (Gemini).

Imports
- `tenacity`
- `src.exceptions`
- `src.models`
- `google-genai` (Gemini client library)

**Class**
- `LlmHelper`
  - `__init__(self, config: models.Config)`
    - Stores the `config` object (containing API key, retry attempts, etc.).
    - Initializes the Gemini API client using `config.gemini_api_key`.
    - Configures the base Tenacity retry decorator using `config.retry_max_attempts`. Can store the configured retryer instance as `self.retryer`.
  - `async detect_context(self, text: str) -> str`
    - Decorated with the configured Tenacity retry logic (e.g., `@self.retryer`).
    - Constructs the prompt/request for context detection.
    - Calls the Gemini API.
    - Parses the response to extract the context label.
    - Returns `response["context"]` or raises `ApiHelperError` on failure (after retries). **Needs to distinguish between retryable API errors (network, rate limits) and non-retryable errors (auth, bad request) within the retry configuration.**
  - `async translate_chunk(self, context: str, target_lang: str, speed_mode: str, chunk_index: int, lines: List[str]) -> List[str]`
    - Decorated with the configured Tenacity retry logic (e.g., `@self.retryer`).
    - Constructs the prompt/request for chunk translation, including context, target language, speed mode hint, and lines.
    - Calls the Gemini API.
    - Parses the response to extract the list of translated lines. **Must ensure the number of returned lines matches the input.**
    - Returns the list of translated lines or raises `ApiHelperError` on failure (after retries). **Needs to distinguish between retryable API errors and non-retryable errors.**

### src/services/reassembler.py
Merges translated blocks back into a single .srt stream.

Function
- `reassemble_srt(sub: List[List[SubtitleBlock]]) -> bytes`
  - Formats each block using srt or manual templating:
    ```
    1
    00:00:01,000 --> 00:00:04,000
    translated line 1
    translated line 2
    ```
  - Encodes the final string to bytes.

### src/app.py (Flask routes & orchestration)
Entry point for the web app, wiring all components together. Located within the `src` package.

Imports
- `Flask, request, render_template, send_file, jsonify` from `flask` # Added jsonify
- `werkzeug.exceptions` # For standard HTTP errors
- `asyncio`
- `src.config_loader`
- `src.exceptions`
- `src.models`
- `src.services.validator`
- `src.services.parser`
- `src.services.context_detector`
- `src.services.chunk_translator`
- `src.services.reassembler`
- `src.services.llm_helper` # Import the class LlmHelper
- `logging`
- `io`

Setup
- Load config via `config_loader.load_config() -> config: models.Config`
- Configure Python logging to console at `config.log_level`.
- Create Flask app instance `app = Flask(__name__)`
- **Instantiate shared services:**
  - `llm_helper_instance = llm_helper.LlmHelper(config)`

**Error Handling Setup**
- Define custom error handlers using `@app.errorhandler`:
  - `@app.errorhandler(exceptions.ValidationError)` -> `return jsonify({"error": str(e)}), 400` (Bad Request)
  - `@app.errorhandler(exceptions.ParsingError)` -> `return jsonify({"error": str(e)}), 400` (Bad Request - Malformed input) or `422` (Unprocessable Entity - Valid format, invalid content)
  - `@app.errorhandler(exceptions.ContextDetectionError)` -> `return jsonify({"error": "Failed to detect context: " + str(e)}), 500` (Internal Server Error - treat as internal failure)
  - `@app.errorhandler(exceptions.ChunkTranslationError)` -> `return jsonify({"error": "Failed during translation: " + str(e)}), 500` (Internal Server Error)
  - `@app.errorhandler(exceptions.ApiHelperError)` -> `return jsonify({"error": "LLM API Error: " + str(e)}), 502` (Bad Gateway - upstream service failed)
  - `@app.errorhandler(werkzeug.exceptions.HTTPException)` -> Handle standard Flask/Werkzeug HTTP errors if needed.
  - `@app.errorhandler(Exception)` -> Generic fallback: `logging.exception("Unhandled error")`, `return jsonify({"error": "An unexpected error occurred"}), 500`

Routes
- `GET /`
  - Renders `templates/index.html`
- `POST /translate`
  - **Try/Catch Block:** Wrap the core logic in a `try...except` block to catch the custom exceptions and let the error handlers manage the response.
  - Get file: `file = request.files.get('file')` (handle potential missing file)
  - Call `validator.validate_upload(file)`
  - Read file content: `content = file.read().decode('utf-8')` (Consider adding error handling for decoding)
  - Call `parser.parse_srt(content, config.chunk_max_blocks) -> sub_chunks`
  - Call `context_detector.detect_context(sub_chunks, llm_helper_instance) -> context` **(Pass instance)**
  - Get other parameters: `target_lang = request.form.get('target_lang')`, `speed_mode = request.form.get('speed_mode')` (Add validation/defaults)
  - Execute `asyncio.run(chunk_translator.translate_all_chunks(context, sub_chunks, target_lang, speed_mode, llm_helper_instance))` **(Pass instance)**
  - Call `reassembler.reassemble_srt(sub_chunks) -> translated_srt_bytes`
  - Create in-memory file: `buffer = io.BytesIO(translated_srt_bytes)`
  - Generate filename: `filename = f"{file.filename.rsplit('.', 1)[0]}_{target_lang}.srt"`
  - Return result: `send_file(buffer, as_attachment=True, download_name=filename, mimetype='text/plain')` # Use text/plain or application/x-subrip

---

## Interfaces & Interaction Patterns
- Request flow (conceptual, actual calls use imported functions):
  - `src.app` receives request → `src.services.validator` → `src.services.parser` → `src.services.context_detector` → `src.services.chunk_translator` (using `src.services.llm_helper`) → `src.services.reassembler` → `src.app` sends response
- All LLM interactions are centralized in `src.services.llm_helper.py`.
- Flask route (`src.app.py`) remains synchronous but uses `asyncio.run` to execute the core asynchronous translation logic.

---

## Workflow / Use Case Examples
Example: user uploads `subs.srt`, selects Vietnamese and “fast” mode
- `src.app` receives the POST request.
- `src.services.validator` checks file extension and size.
- `src.services.parser` chunks the SRT into three lists of `SubtitleBlock` objects (100, 100, 50).
- `src.services.context_detector` analyzes the first chunk via `src.services.llm_helper` → returns “cooking tutorial”.
- `src.services.chunk_translator` uses `asyncio.run` and `asyncio.gather` to call `src.services.llm_helper.translate_chunk` concurrently for each chunk, passing the context.
- `src.services.reassembler` combines the translated `SubtitleBlock` objects back into a single SRT formatted byte string.
- `src.app` sends the byte string back as a downloadable file `subs_vi.srt`.

---

## Implementation Notes, Edge Cases, and TODOs
- Error Handling: Ensure exceptions from `src.exceptions` are caught appropriately in `src.app.py` and translated into user-friendly HTTP error responses.
- Handle empty or malformed SRT files gracefully (e.g., raise `ParsingError` in `src.services.parser`).
- Cap `CHUNK_MAX_BLOCKS` to avoid excessive memory use or overly large LLM API calls.
- Distinguish between retryable (e.g., temporary network issue, rate limit) vs. permanent LLM errors (e.g., invalid API key) in `src.services.llm_helper`.
- TODO: Expose context sample size (currently hardcoded ~100 lines in `src.services.context_detector`) as a configuration option in `src.config_loader`.
- Logging is configured in `src.app.py` based on the `LOG_LEVEL` environment variable. Ensure consistent logging across all modules.

---

## Testing Considerations
- **Test Structure:** Tests are organized within the top-level `tests/` directory, separated into `automated/` and `manual/`.
- **Automated Tests (`tests/automated/`):**
    - **Unit Tests (`tests/automated/unit/`):** Focus on testing individual functions and classes in isolation.
        - Mock dependencies like `srt` library calls, `llm_helper` functions (when testing callers like `chunk_translator`), and file system operations.
        - Examples:
            - `test_validator.py`: Test rejection of invalid file types/sizes.
            - `test_parser.py`: Test correct parsing, chunking logic, and handling of malformed input.
            - `test_llm_helper.py`: Test retry logic, error handling, and correct API payload formatting (using mocked API responses).
            - `test_reassembler.py`: Test correct formatting of the output SRT string/bytes.
    - **Integration Tests (`tests/automated/integration/`):** Test the interaction between different components.
        - Example: `test_app_routes.py`: Use a Flask test client (`app.test_client()`) to simulate HTTP requests to the `/translate` endpoint. Mock the LLM API calls at the `llm_helper` boundary to verify the overall flow from request to response generation without actual external API calls.
- **Manual Tests (`tests/manual/`):**
    - Contains resources for manual verification, such as checklists (`test_cases.md`), specific SRT files for edge-case testing, or helper scripts (`upload_script.py`) to facilitate testing specific scenarios against a running instance.
- **Test Coverage:** Aim for high unit test coverage for core logic within `src/services/` and critical paths in `src/app.py`. Use integration tests to ensure components are wired correctly.
