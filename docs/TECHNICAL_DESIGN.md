# Detailed Technical Design

## Introduction
This document describes the concrete code structure, modules, classes, functions, and data types for the Flask‑based subtitle‑translation web app. It is intended for backend and frontend engineers implementing or reviewing the project. It assumes familiarity with Python, Flask, asyncio, Tenacity, Google Generative AI (`google-genai` SDK), and basic web concepts.

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
│  │  reassembler.py
│
│templates/            # Standard Flask templates folder
│  │    └─ index.html
│  │
│  └─ static/               # Standard Flask static files folder
│     css/
│       │   └─ style.css
│       └─ js/
│           └─ app.js
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
Entry point for the web app, wiring all components together. Initializes and manages the single `genai.Client` instance. Located within the `src` package.

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
- Define custom error handlers using `@app.errorhandler`:
  - `@app.errorhandler(exceptions.ValidationError)` -> `return jsonify({"error": str(e)}), 400`
  - `@app.errorhandler(exceptions.ParsingError)` -> `return jsonify({"error": str(e)}), 400` or `422`
  - `@app.errorhandler(exceptions.ContextDetectionError)` -> `return jsonify({"error": "Failed to detect context: " + str(e)}), 500`
  - `@app.errorhandler(exceptions.ChunkTranslationError)` -> `return jsonify({"error": "Failed during translation: " + str(e)}), 500`
  - `@app.errorhandler(exceptions.ApiHelperError)` -> `return jsonify({"error": "LLM API Error: " + str(e)}), 502` # Catch errors raised by services
  - `@app.errorhandler(tenacity.RetryError)` -> `return jsonify({"error": "LLM API failed after multiple retries: " + str(e)}), 504` (Gateway Timeout)
  - `@app.errorhandler(werkzeug.exceptions.HTTPException)` -> Handle standard Flask/Werkzeug HTTP errors if needed.
  - `@app.errorhandler(Exception)` -> Generic fallback: `logging.exception("Unhandled error")`, `return jsonify({"error": "An unexpected error occurred"}), 500`

Routes
- `GET /`
  - Renders `templates/index.html`, passing the list of configured languages to the template:
    `return render_template('index.html', languages=config.target_languages)`
- `POST /translate`
  - **Check Client:** Add a check at the beginning: `if genai_client is None: return jsonify({"error": "Translation service is unavailable due to initialization failure."}), 503` (Service Unavailable) - *Note: Current setup raises error on init failure, so this might be redundant but good defense.*
  - **Try/Catch Block:** Wrap the core logic in a `try...except` block to catch the custom exceptions and let the error handlers manage the response.
  - Get file: `file = request.files.get('file')` (handle potential missing file)
  - Call `parser.parse_srt(file, config.chunk_max_blocks) -> sub_chunks`
  - Get other parameters: `target_lang = request.form.get('target_lang')` (gets the selected full language name, e.g., "Vietnamese"), `speed_mode = request.form.get('speed_mode', 'normal')`. Add validation to ensure `target_lang` is in `config.target_languages`.
  - Call `context_detector.detect_context(sub_chunks, speed_mode, genai_client, config) -> context` **(Pass the shared client instance & config)**
  - Execute `asyncio.run(chunk_translator.translate_all_chunks(context, sub_chunks, target_lang, speed_mode, genai_client, config))` **(Pass the shared client instance & config)**
  - Call `reassembler.reassemble_srt(sub_chunks) -> translated_srt_bytes`
  - Create in-memory file: `buffer = io.BytesIO(translated_srt_bytes)`
  - Stream it back to user with Flask's `send_file`

---

## Interfaces & Interaction Patterns
- Request flow (conceptual, actual calls use imported functions):
  - `src.app` receives request → `src.parser` → `src.context_detector` (uses passed `genai.Client`) → `src.chunk_translator` (uses passed `genai.Client`) → `src.reassembler` → `src.app` sends file response
- LLM interactions (including API calls, prompt engineering, response parsing, and retries) are handled directly within `src.context_detector.py` and `src.chunk_translator.py`, using the mock response or the `google-genai` SDK via the passed client instance.
- The **single, shared `genai.Client` instance** (or equivalent GenerativeModel instance) is created in `src/app.py` at startup using the API key from config and **passed as a required argument** down to the services that need it (`context_detector`, `chunk_translator`).
- The frontend (`index.html`, likely using `static/js/app.js`) receives the list of available target languages (full names) from the `GET /` route in `src.app.py` and populates the language selector.
- When the user submits the form, the selected full language name is sent in the `POST /translate` request data.
- Flask route (`src.app.py`) remains synchronous but uses `asyncio.run` to execute the core asynchronous translation logic (`translate_all_chunks`). `detect_context` is assumed synchronous for simplicity unless it needs to be async as well.
- The final translated `.srt` file is generated as bytes in memory and streamed directly to the client using Flask's `send_file`. No temporary files are saved to disk on the server.

---

## Workflow / Use Case Examples
Example: user uploads `subs.srt`, selects "Vietnamese" and “fast” mode
- `src.config_loader.load_config()` reads `TARGET_LANGUAGES="Vietnamese,French"` from `.env` and stores `["Vietnamese", "French"]` in `config.target_languages`.
- `src.app` initializes the single `genai.Client` (or equivalent) instance at startup using `gemini_helper.init_genai_client(config)`. If this fails, the app halts or enters a state where translation is unavailable.
- User visits `GET /`. `src.app.py` renders `index.html`, passing `languages=["Vietnamese", "French"]` to the template. The frontend JS populates the language selector with "Vietnamese" and "French".
- User selects "Vietnamese", "fast" mode, uploads `subs.srt`, and clicks submit, triggering a `POST /translate`.
- `src.app` receives the POST request, retrieves `target_lang='Vietnamese'` and `speed_mode='fast'`. Validates that "Vietnamese" is in `config.target_languages`.
- `src.parser` checks file extension and size, chunks it into three lists of `SubtitleBlock` objects (100, 100, 50).
- `src.app` calls `src.context_detector.detect_context`, passing the chunks, `speed_mode`, the **shared `genai_client`**, and `config`.
- `src.context_detector` extracts text, constructs a prompt, potentially selects a 'fast' model name (e.g., "gemini-1.5-flash-latest"), calls the appropriate method on the **passed `genai_client`** (with retries using `config`), parses the response → returns “cooking tutorial”.
- `src.app` calls `src.chunk_translator.translate_all_chunks` using `asyncio.run`, passing context, chunks, `target_lang='Vietnamese'`, `speed_mode`, the **shared `genai_client`**, and `config`.
- `src.chunk_translator` uses `asyncio.gather` to run `_translate_single_chunk` for each chunk. Each `_translate_single_chunk` call constructs a prompt (including `target_lang='Vietnamese'`), calls the appropriate method on the **passed `genai_client`** (potentially using a 'fast' model name, with retries), validates line counts, and updates `SubtitleBlock` objects in place.
- `src.reassembler` combines the translated `SubtitleBlock` objects back into a single SRT formatted byte string.
- `src.app` creates an `io.BytesIO` buffer with the bytes and uses `send_file` to stream the content back to the user's browser as a downloadable file named like `subs_Vietnamese.srt`.

---

## Implementation Notes, Edge Cases, and TODOs
- **SDK Methods & Client Initialization:** Verify the exact method names and parameters for text generation in the `google-genai` SDK (e.g., `generate_content`, `generate_text`, etc.) and update the calls in `context_detector` and `chunk_translator` accordingly. Ensure the client initialization in `app.py` matches the recommended pattern in the SDK documentation (e.g., using `genai.configure` and `genai.GenerativeModel` or `genai.Client`).
- **Target Language Validation:** Add explicit validation in the `POST /translate` route in `app.py` to ensure the `target_lang` received from the form is one of the languages listed in `config.target_languages`. Return a 400 error if not.
- **Filename Generation:** Consider if using the full language name in the output filename (e.g., `_Vietnamese.srt`) is desirable or if mapping it to a shorter code (e.g., `_vi.srt`) within `app.py` before calling `send_file` would be better.
- Error Handling: Ensure exceptions from `src.exceptions` are caught appropriately in `src.app.py`. Specific handlers for `ApiHelperError`, `tenacity.RetryError`, and potential `google.api_core.exceptions` (if the SDK raises them directly for API issues) are crucial. Add robust error handling around `genai.Client` initialization in `app.py`, potentially halting startup on failure.
- Retry Logic: Implement robust retry logic using `tenacity` within `context_detector.py` and `chunk_translator.py`, configured via `config.retry_max_attempts`. Ensure it correctly distinguishes between retryable and non-retryable API errors based on the exceptions raised by the `google-genai` SDK.
- Handle empty or malformed SRT files gracefully (e.g., raise `ParsingError` in `src.parser`).
- Cap `CHUNK_MAX_BLOCKS` to avoid excessive memory use or overly large LLM API calls.
- **Gemini Client Management:** The single `genai.Client` (or equivalent) instance is created once in `app.py`. Ensure this instance is thread-safe if using multi-threaded Flask workers (check SDK documentation). The current design assumes passing the appropriate `model` name (derived from `speed_mode`) within the generation call on the single client instance is sufficient.
- Response Validation: The check for matching numbers of input/output lines in `_translate_single_chunk` is critical to prevent data corruption.
- TODO: Expose context sample size (currently hardcoded ~100 lines in `src.context_detector`) as a configuration option in `src.config_loader`.
- Logging is configured in `src.app.py` based on the `LOG_LEVEL` environment variable. Ensure consistent logging across all modules, especially around API calls, retries, and client initialization.

---

## Testing Considerations
- **Test Structure:** Tests are organized within the top-level `tests/` directory, separated into `automated/` and `manual/`.
- **Automated Tests (`tests/automated/`):**
    - **Unit Tests (`tests/automated/unit/`):** Focus on testing individual functions and classes in isolation.
        - Mock dependencies like `srt` library calls, file system operations, and crucially, mock the **passed `genai.Client` instance** (or its relevant methods like `generate_content`) when testing `context_detector` and `chunk_translator`.
        - Mock the `config` object to test different configurations (e.g., target languages).
        - Examples:
            - `test_config_loader.py`: Test parsing of `TARGET_LANGUAGES` env var.
            - `test_parser.py`: Test rejection of invalid file types/sizes, correct parsing, chunking logic, and handling of malformed input.
            - `test_context_detector.py`: Mock the generation method on the passed `genai.Client` mock object. Test prompt construction, model name selection, response parsing, retry logic (using `tenacity.RetryError`), and error handling for API failures.
            - `test_chunk_translator.py`: Mock the generation method on the passed `genai.Client` mock object. Test concurrency with `asyncio`, prompt construction (verifying target language is passed correctly), model name selection, response parsing, **line count validation**, retry logic, and error handling.
            - `test_reassembler.py`: Test correct formatting of the output SRT string/bytes.
    - **Integration Tests (`tests/automated/integration/`):** Test the interaction between different components.
        - Example: `test_app_routes.py`: Use a Flask test client (`app.test_client()`).
            - Test the `GET /` route to ensure `languages` are passed to the template context correctly.
            - Test the `POST /translate` route: Mock the `genai.Client` instance itself *at the point it's passed to the services* or patch the specific generation methods called within `context_detector.detect_context` and `chunk_translator._translate_single_chunk`. Verify the overall flow, including validation of the submitted `target_lang` against the configured list. Mocking the client instance creation/configuration in `app.py` might also be necessary during test setup.
- **Manual Tests (`tests/manual/`):**
    - Contains resources for manual verification, such as checklists (`test_cases.md`), specific SRT files for edge-case testing, or helper scripts (`upload_script.py`) to facilitate testing specific scenarios against a running instance. These scripts could also initialize their own `genai.Client` and call service functions directly for debugging.
- **Test Coverage:** Aim for high unit test coverage for core logic within `src/` (especially the LLM interaction parts) and critical paths in `src.app.py`. Use integration tests to ensure components are wired correctly and `app.py` orchestrates the calls as expected, including passing the client instance correctly and handling language configuration/validation.
