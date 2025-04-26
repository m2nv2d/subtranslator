# Detailed Technical Design

## Introduction
This document describes the concrete code structure, modules, classes, functions, and data types for the Flask‑based subtitle‑translation web app. It is intended for backend and frontend engineers implementing or reviewing the project. It assumes familiarity with Python, Flask, asyncio, Tenacity, Google Generative AI (`google-genai` SDK), and basic web concepts.

## Table of Contents
- Module Structure & File Organization
- Detailed Component Design
  - src/config_loader.py
  - src/translator/exceptions.py
  - src/translator/models.py
  - src/translator/parser.py
  - src/translator/gemini_helper.py
  - src/translator/context_detector.py
  - src/translator/chunk_translator.py
  - src/translator/reassembler.py
  - src/app.py (Flask routes & orchestration)
  - src/templates/index.html
  - src/static/css/style.css
  - src/static/js/app.js
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
│  │
│  ├─ translator/           # Core translation logic package
│  │  │  __init__.py         # Makes 'translator' a package
│  │  │  exceptions.py       # Custom exceptions
│  │  │  models.py           # Data models (DTOs, Config)
│  │  │  parser.py           # SRT parsing and chunking
│  │  │  gemini_helper.py    # Helper functions for Gemini API
│  │  │  context_detector.py # Detect context
│  │  │  chunk_translator.py # Translate chunks
│  │  │  reassembler.py
│  │
│  ├─ templates/            # Standard Flask templates folder
│  │  │    └─ index.html
│  │
│  └─ static/               # Standard Flask static files folder
│     │  css/
│     │    │   └─ style.css
│     │  └─ js/
│     │      └─ app.js
│
└─ tests/                    # Testing directory
   automated/            # Automated tests (unit, integration, etc.)
     │  unit/             # Unit tests for individual components
     │    │ __init__.py     │    │
     │    └─ translator/     # Unit tests mirroring src/translator structure
     │
     │  └─ integration/      # Integration tests for component interactions
     │      __init__.py
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
- `load_config() -> models.Config`
  - Locates and reads `.env` from project root (one level up from src) via python‑dotenv
  - Handles missing .env gracefully by falling back to environment variables
  - Validates presence of `GEMINI_API_KEY` (logs error and exits with message if missing)
  - Loads optional vars with defaults and extensive validation:
    - `TARGET_LANGUAGES`: Comma-separated full language names (e.g., `"Vietnamese,French"`).
      Strips whitespace, filters empty entries, falls back to default `["Vietnamese", "French"]` if invalid
    - `CHUNK_MAX_BLOCKS`: Positive integer (default `100`)
    - `RETRY_MAX_ATTEMPTS`: Non-negative integer (default `6`)
    - `LOG_LEVEL`: Valid uppercase log level string (default `"INFO"`, must be one of `["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]`)
  - Logs warnings for any parsing/validation issues
  - Returns a `Config` data class instance (defined in `src.translator.models`).

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
  - `retry_max_attempts: int` # Default handled in config_loader (currently 6)
  - `log_level: str`

### src/translator/parser.py
Validates SRT files specified by path before processing. Then use the srt library for parsing and chunking the uploaded srt into an in-memory object.

Imports
- `datetime`
- `typing.List, Optional`
- `srt`
- `translator.exceptions`
- `translator.models`

Functions
- `parse_srt(file_path: str, chunk_max_blocks: int) -> List[List[models.SubtitleBlock]]` (Note: Expects a path to a temporarily saved file, not a file stream/object).
  - Ensures file extension is `.srt`
  - Checks file size (must be `> 0` and `<= 2MB`).
  - Raises `exceptions.ValidationError` on validation failure (extension, size, empty file). Raises `exceptions.ParsingError` if the file cannot be read or SRT content is malformed.
  - Reads the file content using UTF-8 encoding (replacing errors) and uses `srt.parse()` to obtain subtitle objects.
  - Maps each subtitle block in original content to a `models.SubtitleBlock`
  - Splits blocks into disjoint lists of size `max_blocks`
  - Returns an empty list `[]` if the SRT file contains no valid subtitle blocks after parsing.

### src/translator/gemini_helper.py
Facilitates the initialization of the `google-genai` client instance.
- Defines constants for model names (`FAST_MODEL`, `NORMAL_MODEL`).

Imports
- `from google import genai`
- `translator.exceptions`
- `translator.models`

Functions
- `init_genai_client(config: models.Config) -> genai.client.Client`
  - Initializes a `genai.client.Client` instance with the API key from the config.
  - Raises `exceptions.GenAIClientInitError` if initialization fails.

### src/translator/context_detector.py
Obtains a high-level context label from the first blocks by using a mock response or calling the LLM API directly using the `google-genai` SDK via a passed client instance.

Imports
- `typing.List, Optional`
- `tenacity`
- `from google import genai`
- `translator.exceptions`
- `translator.models`

Function
- `detect_context(`
    `sub: List[List[models.SubtitleBlock]],`
    `speed_mode: str,` # Values: "mock", "fast", or "normal"
    `genai_client: Optional[genai.client.Client],` # Pass the initialized Client instance; *required* if speed_mode is "fast" or "normal", otherwise ignored.
    `config: models.Config` # Pass config for retry settings (required)
  `) -> str`
  - Extracts text from *all lines* of the *first chunk* in `sub`.
  - Determine the method to use based on value of `speed_mode`. We have a different generation method for mock, and one for fast or normal.
  - If speed_mode = mock, we just return some random context.
  - If speed_mode is 'fast' or 'normal', uses the passed `genai_client` instance (with specific model names `FAST_MODEL` or `NORMAL_MODEL` selected based on `speed_mode`) to make remote API requests. Uses a `tenacity` decorator directly on the function, configured with a **hardcoded 3 attempts** (ignoring `config.retry_max_attempts`), to wrap the API call.
  - Returns context string. Raises `ValueError` if `speed_mode` is invalid. On API failure after retries, `tenacity` reraises the original exception from the API client.

### src/translator/chunk_translator.py
Translates chunks in parallel using asyncio with a mock response or LLM API calls via the `google-genai` SDK using a passed client instance.

Imports
- `asyncio`
- `typing.List, Optional`
- `tenacity`
- `from google import genai`
- `translator.exceptions`
- `translator.models`

Functions

- `translate_all_chunks(`
    `context: str,`
    `sub: List[List[models.SubtitleBlock]],`
    `target_lang: str,` # Full language name (e.g., "Vietnamese")
    `speed_mode: str,` # Values: "mock", "fast", or "normal"
    `genai_client: genai.client.Client,` # (optional) pass the initialized Client instance, only required if speed_mode isn't "mock"
    `config: models.Config` # Pass config for retry settings (required)
  `) -> None`
  - Uses `asyncio.TaskGroup` to run `_translate_single_chunk` concurrently for each chunk in `sub`, passing `genai_client` (optional) and `config`.
  - Catches exceptions from tasks (including retried API errors from `_translate_single_chunk`) and raises `exceptions.ChunkTranslationError`.

- `async _translate_single_chunk(`
    `system_prompt: str,`
    `chunk_index: int,`
    `chunk: List[models.SubtitleBlock],`
    `target_lang: str,` # Full language name (e.g., "Vietnamese") - *Note: Used by caller (`translate_all_chunks`) to build `system_prompt`.*
    `speed_mode: str,` # Values: "mock", "fast", or "normal"
    `genai_client: Optional[genai.client.Client],` # (optional) pass the initialized Client instance, only required if speed_mode isn't "mock"
    `config: models.Config` # Pass config for retry settings (required)
  `) -> None`
  - Determine the method based on `speed_mode`. For 'fast'/'normal', uses the **async** client (`genai_client.aio.models.generate_content`) with appropriate model (`FAST_MODEL`/`NORMAL_MODEL`), requesting **JSON output**.
  - The 'mock' mode avoids API calls, copies original `content` to `translated_content` for each block, and includes a small `asyncio.sleep`.
  - Uses a `tenacity` decorator directly on the function, configured with a **hardcoded 3 attempts** (ignoring `config.retry_max_attempts`). After a successful API call, it **parses the JSON response** and modifies the `SubtitleBlock` objects in the passed `chunk` list by setting the `translated_content` field.
  - Raises `exceptions.ChunkTranslationError` if JSON parsing fails. On API failure after retries, `tenacity` reraises the original exception from the API client (which is then caught and wrapped by `translate_all_chunks`).

### src/translator/reassembler.py
Merges translated blocks back into a single .srt formatted byte stream suitable for direct download.

Imports
- `typing.List`
- `srt`
- `translator.models`

Function
- `reassemble_srt(sub: List[List[models.SubtitleBlock]]) -> bytes`
  - Uses the `srt` library (`srt.compose`) to format the blocks. Uses `translated_content` if available, otherwise falls back to the original `content`.
  - Encodes the final string to bytes, ready to be sent in the response.

### src/templates/index.html
Renders the primary user interface.

Key Components & Requirements:
-   Standard HTML5 structure.
-   Links to `static/css/style.css` and `static/js/app.js`. Includes `favicon.ico`.
-   A main form (`id="translate-form"`, `enctype="multipart/form-data"`) containing:
    -   File input (`name="file"`, `accept=".srt"`, required).
    -   Target language select (`name="target_lang"`, required).
        -   Options populated dynamically via Jinja loop over the `languages` variable passed from the backend (list of full language names).
    -   Speed mode select (`name="speed_mode"`, values "normal", "fast", default "normal").
    -   Submit button (`id="submit-button"`).
-   A status display area (`id="status-message"`) for feedback from `app.js`.

### src/static/js/app.js
Handles client-side interactivity and communication with the backend.

Key Logic & Requirements:
-   **Initialization:** Attaches listeners after `DOMContentLoaded`. Gets references to form elements (`#translate-form`, `#file-input`, `#target-lang`, `#speed-mode`, `#submit-button`, `#status-message`).
-   **Form Submission:**
    -   Intercepts form `submit` event, prevents default.
    -   Performs basic client-side validation (file presence, `.srt` extension, language selection).
    -   Constructs `FormData` including `file`, `target_lang`, and `speed_mode`.
    -   Disables submit button and updates `#status-message` (class `status-processing`) during processing.
-   **API Interaction:**
    -   Sends an asynchronous `fetch` `POST` request to the `/translate` endpoint with the `FormData`.
-   **Response Handling:**
    -   **Success (response.ok):** Expects the response body to be the translated SRT file (`Blob`). Triggers a client-side download using an object URL and dynamically generated filename (`original_stem_TargetLanguage.srt`). Updates `#status-message` (class `status-success`).
    -   **Error (!response.ok):** Attempts to parse response body as JSON, expecting `{ "error": "..." }`. Displays the error message (or a fallback HTTP status error) in `#status-message` (class `status-error`).
-   **UI State:** Re-enables the submit button in a `finally` block. Updates `#status-message` content and class (`status-processing`, `status-success`, `status-error`) based on request state/outcome.

### src/static/css/style.css
Provides visual styling for `index.html`.

Key Styling Aspects:
-   Basic page layout, typography, and color scheme.
-   Styles for the main form container (`#translate-form`) for centered layout and appearance.
-   Consistent styling for form controls (`input`, `select`, `button`).
-   Distinct visual states for the submit button (`button`, `button:hover`, `button:disabled`).
-   Specific background, text, and border colors for the status message states using classes:
    -   `.status-processing`
    -   `.status-success`
    -   `.status-error`
-   Ensures `#status-message` has appropriate dimensions and alignment.

### src/app.py (Flask routes & orchestration)
Entry point for the web app, wiring all components together. Initializes and manages the single `genai.Client` instance. Located within the `src` package.

Imports
- `Flask, request, render_template, send_file, jsonify` from `flask`
- `werkzeug.utils import secure_filename`
- `werkzeug.exceptions` # For standard HTTP errors
- `asyncio`
- `from google import generativeai as genai`
- `src.config_loader`
- `from translator import init_genai_client, parse_srt, detect_context, reassemble_srt, translate_all_chunks, Config, SubtitleBlock`
- `logging`
- `io`
- `tempfile`
- `os`
- `pathlib`
- `tenacity` # Potentially needed if defining retry config here

Setup
- Load app config via `config_loader.load_config() -> config: translator_models.Config`. Halts startup (`SystemExit`) if loading fails.
- Configure Python logging to console at `config.log_level`.
- Create Flask app instance `app = Flask(__name__, static_folder='static', template_folder='templates')`.
- Adds a route for `/favicon.ico`.
- **Instantiate shared Gemini client (Single instance for the app):**
  - `genai_client = None` # Initialize to None
  - `try:`
    - `genai_client = translator_gemini_helper.init_genai_client(config)` # Configure the library globally
    - `logging.info("Gemini Client initialized successfully.")`
  - `except Exception as e:` # Catch potential exceptions during client init (e.g., invalid key format - specifics depend on SDK)
    - `logging.exception("Failed to initialize Gemini Client. App startup failed.")`
    - raise `RuntimeError`("Critical component (Gemini Client) failed to initialize.") from e # Halts startup

Error Handling Setup
- Define custom error handlers using `@app.errorhandler`:
  - `@app.errorhandler(translator_exceptions.ValidationError)` -> `return jsonify({"error": str(e)}), 400`
  - `@app.errorhandler(translator_exceptions.ParsingError)` -> `return jsonify({"error": str(e)}), 422` # 422 Unprocessable Entity seems more appropriate for malformed content
  - `@app.errorhandler(translator_exceptions.ContextDetectionError)` -> `return jsonify({"error": "Failed to detect context: " + str(e)}), 500`
  - `@app.errorhandler(translator_exceptions.ChunkTranslationError)` -> `return jsonify({"error": "Failed during translation: " + str(e)}), 500`
  - Note: Specific handlers for `GenAIClientInitError`, `GenAIRequestError`, `GenAIParsingError` are not defined; these would likely be caught by `RetryError` or the generic `Exception` handler.
  - `@app.errorhandler(tenacity.RetryError)` -> `return jsonify({"error": "LLM API failed after multiple retries: " + str(e)}), 504` (Gateway Timeout)
  - `@app.errorhandler(werkzeug.exceptions.HTTPException)` -> Handle standard Flask/Werkzeug HTTP errors if needed.
  - `@app.errorhandler(Exception)` -> Generic fallback: `logging.exception("Unhandled error")`, `return jsonify({"error": "An unexpected error occurred"}), 500`

Routes
- `GET /`
  - Renders `templates/index.html`, passing the list of configured languages to the template:
    `return render_template('index.html', languages=config.target_languages)`
- `POST /translate`
  - **Check Client:** Add a check at the beginning: `if genai_client is None: return jsonify({"error": "Translation service is unavailable due to initialization failure."}), 503` (Service Unavailable) - *Note: Current setup raises error on init failure, so this might be redundant but good defense.*
  - **Temporary File Handling:** Use `tempfile.mkdtemp()` and `os.path.join` for safe temporary file creation.
  - **Try/Finally Block:** Wrap the core logic in a `try...finally` block. The `try` allows exceptions to be caught by the error handlers, and the `finally` ensures temporary file cleanup.
  - Inside `try`:
    - Get file: `file = request.files.get('file')` (handle potential missing file with `ValidationError`).
    - Save uploaded file to temporary dir using `secure_filename`.
    - Call `sub_chunks = translator_parser.parse_srt(temp_file_path, config.chunk_max_blocks)`, passing the path.
    - Get other parameters: `target_lang = request.form.get('target_lang')`, `speed_mode = request.form.get('speed_mode', 'normal')`.
    - **Validate Target Language:** Check if `target_lang` is present and in `config.target_languages`. Raise `translator_exceptions.ValidationError` if not.
    - Call `context = translator_context_detector.detect_context(sub_chunks, speed_mode, genai_client, config)` **(Pass the shared client instance & config)**
    - Execute `asyncio.run(translator_chunk_translator.translate_all_chunks(context, sub_chunks, target_lang, speed_mode, genai_client, config))` **(Pass the shared client instance & config)**
    - Call `translated_srt_bytes = translator_reassembler.reassemble_srt(sub_chunks)`
    - Create in-memory file: `buffer = io.BytesIO(translated_srt_bytes)`
    - Generate download filename (e.g., `original_stem_language.srt`). Use `pathlib.Path(file.filename).stem`.
    - Stream it back using Flask's `send_file`, providing the `io.BytesIO` buffer, mimetype (`text/srt`), `as_attachment=True`, and the generated `download_name`.
  - The `finally` block ensures the temporary file and directory are removed using `os.remove` and `os.rmdir` (or `shutil.rmtree`).

## Interfaces & Interaction Patterns
- Request flow (conceptual, actual calls use imported functions):
  - `src.app` receives request → `src.translator.parser` → `src.translator.context_detector` (uses passed `genai.Client`) → `src.translator.chunk_translator` (uses passed `genai.Client`) → `src.translator.reassembler` → `src.app` sends file response
- LLM interactions (including API calls, prompt engineering, response parsing, and retries) are handled directly within `src/translator/context_detector.py` and `src/translator/chunk_translator.py`, using the mock response or the `google-genai` SDK via the passed client instance.
- The **single, shared `genai.Client` instance** (or equivalent GenerativeModel instance) is created in `src/app.py` at startup using the API key from config and **passed as a required argument** down to the services that need it (`translator.context_detector`, `translator.chunk_translator`).
- The frontend (`index.html`, likely using `static/js/app.js`) receives the list of available target languages (full names) from the `GET /` route in `src.app.py` and populates the language selector.
- When the user submits the form, the selected full language name is sent in the `POST /translate` request data.
- Flask route (`src.app.py`) remains synchronous but uses `asyncio.run` to execute the core asynchronous translation logic (`translator_chunk_translator.translate_all_chunks`). `translator_context_detector.detect_context` is assumed synchronous for simplicity unless it needs to be async as well.
- The final translated `.srt` file is generated as bytes in memory and streamed directly to the client using Flask's `send_file`. No temporary files are saved to disk on the server *except* for the initial upload processing.

---

## Workflow / Use Case Examples
Example: user uploads `subs.srt`, selects "Vietnamese" and “fast” mode
- `src.config_loader.load_config()` reads `TARGET_LANGUAGES="Vietnamese,French"` from `.env` and stores `["Vietnamese", "French"]` in `config.target_languages`.
- `src.app` initializes the single `genai.Client` (or equivalent) instance at startup using `translator_gemini_helper.init_genai_client(config)`. If this fails, the app halts or enters a state where translation is unavailable.
- User visits `GET /`. `src.app.py` renders `index.html`, passing `languages=["Vietnamese", "French"]` to the template. The frontend JS populates the language selector with "Vietnamese" and "French".
- User selects "Vietnamese", "fast" mode, uploads `subs.srt`, and clicks submit, triggering a `POST /translate`.
- `src.app` receives the POST request, retrieves `target_lang='Vietnamese'` and `speed_mode='fast'`. Validates that "Vietnamese" is in `config.target_languages`.
- `src.app` saves the upload to a temporary file. `src.translator.parser` checks the temporary file's extension and size, then parses and chunks it into lists of `SubtitleBlock` objects.
- `src.app` calls `src.translator.context_detector.detect_context`, passing the chunks, `speed_mode`, the **shared `genai_client`**, and `config`.
- `src.translator.context_detector` extracts text, constructs a prompt, potentially selects a 'fast' model name (e.g., "gemini-1.5-flash-latest"), calls the appropriate method on the **passed `genai_client`** (with retries), parses the response → returns “cooking tutorial”.
- `src.app` calls `src.translator.chunk_translator.translate_all_chunks` using `asyncio.run`, passing context, chunks, `target_lang='Vietnamese'`, `speed_mode`, the **shared `genai_client`**, and `config`.
- `src.translator.chunk_translator` uses `asyncio.TaskGroup` to run `_translate_single_chunk` for each chunk. Each `_translate_single_chunk` call constructs a prompt (including `target_lang='Vietnamese'`), calls the appropriate method on the **passed `genai_client`** (potentially using a 'fast' model name, with retries), validates line counts, and updates `SubtitleBlock` objects in place.
- `src.translator.reassembler` combines the translated `SubtitleBlock` objects back into a single SRT formatted byte string.
- `src.app` creates an `io.BytesIO` buffer with the bytes and uses `send_file` to stream the content back to the user's browser as a downloadable file named like `subs_Vietnamese.srt`.

---

## Implementation Notes, Edge Cases, and TODOs
- **SDK Methods & Client Initialization:** Verify the exact method names and parameters for text generation in the `google-genai` SDK (e.g., `generate_content`, `generate_text`, etc.) and update the calls in `translator.context_detector` and `translator.chunk_translator` accordingly. Ensure the client initialization in `app.py` matches the recommended pattern in the SDK documentation (e.g., using `genai.configure` and `genai.GenerativeModel` or `genai.Client`).
- **DONE:** Explicit validation exists in the `POST /translate` route in `app.py` ensuring `target_lang` is provided and is one of the languages listed in `config.target_languages`. Returns a 400 `ValidationError` if not.
- **Filename Generation:** Consider if using the full language name in the output filename (e.g., `_Vietnamese.srt`) is desirable or if mapping it to a shorter code (e.g., `_vi.srt`) within `app.py` before calling `send_file` would be better.
- Error Handling: Handlers for custom exceptions (`translator.ValidationError`, `translator.ParsingError`, `translator.ContextDetectionError`, `translator.ChunkTranslationError`), `tenacity.RetryError`, `HTTPException`, and generic `Exception` are implemented in `app.py`. Robust error handling around `genai.Client` initialization (halting startup on failure) is also present. Note: `reraise=True` in retry decorators propagates underlying API exceptions (like `google.api_core.exceptions`).
- Retry Logic: Retry logic using `tenacity` is implemented in `translator.context_detector.py` and `translator.chunk_translator.py`, but it uses **hardcoded 3 attempts**, ignoring `config.retry_max_attempts`. It currently retries broadly on `Exception` and uses `reraise=True`.
- Handle empty or malformed SRT files gracefully (e.g., raise `ParsingError` in `src.translator.parser`).
- Cap `CHUNK_MAX_BLOCKS` to avoid excessive memory use or overly large LLM API calls.
- **Gemini Client Management:** The single `genai.Client` (or equivalent) instance is created once in `app.py`. Ensure this instance is thread-safe if using multi-threaded Flask workers (check SDK documentation). The current design assumes passing the appropriate `model` name (derived from `speed_mode`) within the generation call on the single client instance is sufficient.
- Response Validation: **MISSING:** The check for matching numbers of input/output lines (or general structural validation beyond basic JSON parsing) in `_translate_single_chunk`'s response handling (within `translator.chunk_translator`) is currently missing.
- TODO: Expose context sample size (currently hardcoded ~100 lines in `src.translator.context_detector`) as a configuration option in `src.config_loader`.
- Logging is configured in `src.app.py` based on the `LOG_LEVEL` environment variable. Ensure consistent logging across all modules, especially around API calls, retries, and client initialization.

---

## Testing Considerations
- **Test Structure:** Tests are organized within the top-level `tests/` directory, separated into `automated/` and `manual/`. Unit tests mirror the `src` structure (e.g., `tests/automated/unit/translator/`).
- **Automated Tests (`tests/automated/`):**
    - **Unit Tests (`tests/automated/unit/`):** Focus on testing individual functions and classes in isolation.
        - Mock dependencies like `srt` library calls, file system operations, and crucially, mock the **passed `genai.Client` instance** (or its relevant methods like `generate_content`) when testing `translator.context_detector` and `translator.chunk_translator`.
        - Mock the `config` object to test different configurations (e.g., target languages).
        - Examples:
            - `tests/automated/unit/test_config_loader.py`: Test parsing of `TARGET_LANGUAGES` env var.
            - `tests/automated/unit/translator/test_parser.py`: Test rejection of invalid file types/sizes, correct parsing, chunking logic, and handling of malformed input.
            - `tests/automated/unit/translator/test_context_detector.py`: Mock the generation method on the passed `genai.Client` mock object. Test prompt construction, model name selection, response parsing, retry logic (using `tenacity.RetryError`), and error handling for API failures.
            - `tests/automated/unit/translator/test_chunk_translator.py`: Mock the generation method on the passed `genai.Client` mock object. Test concurrency with `asyncio`, prompt construction (verifying target language is passed correctly), model name selection, response parsing, **line count validation**, retry logic, and error handling.
            - `tests/automated/unit/translator/test_reassembler.py`: Test correct formatting of the output SRT string/bytes.
    - **Integration Tests (`tests/automated/integration/`):** Test the interaction between different components.
        - Example: `test_app_routes.py`: Use a Flask test client (`app.test_client()`).
            - Test the `GET /` route to ensure `languages` are passed to the template context correctly.
            - Test the `POST /translate` route: Mock the `genai.Client` instance itself *at the point it's passed to the services* or patch the specific generation methods called within `translator.context_detector.detect_context` and `translator.chunk_translator._translate_single_chunk`. Verify the overall flow, including validation of the submitted `target_lang` against the configured list. Mocking the client instance creation/configuration in `app.py` might also be necessary during test setup.
- **Manual Tests (`tests/manual/`):**
    - Contains resources for manual verification, such as checklists (`test_cases.md`), specific SRT files for edge-case testing, or helper scripts (`upload_script.py`) to facilitate testing specific scenarios against a running instance. These scripts could also initialize their own `genai.Client` and call service functions directly for debugging.
- **Test Coverage:** Aim for high unit test coverage for core logic within `src/translator/` (especially the LLM interaction parts) and critical paths in `src.app.py`. Use integration tests to ensure components are wired correctly and `app.py` orchestrates the calls as expected, including passing the client instance correctly and handling language configuration/validation.