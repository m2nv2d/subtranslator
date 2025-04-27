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

**Expected .env file format (example):**
```dotenv
TARGET_LANGUAGES=Vietnamese, French
CHUNK_MAX_BLOCKS=100
RETRY_MAX_ATTEMPTS=6
LOG_LEVEL=INFO
AI_PROVIDER=google-gemini
AI_API_KEY=api-key-here
FAST_MODEL=gemini-1.5-flash-latest
NORMAL_MODEL=gemini-1.5-pro-latest
```

Functions and classes
- `load_config() -> models.Config`
  - Locates and reads `.env` from project root (one level up from src) via python‑dotenv.
  - Handles missing `.env` gracefully by falling back to environment variables.
  - Loads required string variables: `AI_PROVIDER`, `AI_API_KEY`, `FAST_MODEL`, and `NORMAL_MODEL`. Logs error and exits if missing.
  - Loads optional vars with defaults and extensive validation:
    - `TARGET_LANGUAGES`: Comma-separated full language names (e.g., `"Vietnamese,French"`).
      Strips whitespace, filters empty entries, falls back to default `["Vietnamese", "French"]` if invalid or missing.
    - `CHUNK_MAX_BLOCKS`: Positive integer (default `100`). Logs error and exits if non-integer or non-positive.
    - `RETRY_MAX_ATTEMPTS`: Non-negative integer (default `6`). Logs error and exits if non-integer or negative.
    - `LOG_LEVEL`: Valid uppercase log level string (default `"INFO"`, must be one of `["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]`). Logs error and uses default if invalid.
  - Logs warnings for any parsing/validation issues with optional variables that fall back to defaults.
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
  - `ai_api_key: str`
  - `target_languages: List[str]` # List of full language names (e.g., ["Vietnamese", "French"])
  - `chunk_max_blocks: int`
  - `retry_max_attempts: int`
  - `log_level: str`
  - `ai_provider: str` # e.g., "google-gemini"
  - `fast_model: str` google-gemini
  - `normal_model: str`
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
Facilitates the initialization of the `google-genai` client instance. **Note:** This helper assumes the caller has already verified that the `ai_provider` is `google-gemini` and that `ai_api_key` is provided in the config.

Imports
- `from google import genai`
- `translator.exceptions`
- `translator.models`

Functions
- `init_genai_client(config: models.Config) -> genai.client.Client`
  - Initializes a `genai.client.Client` instance with the API key from `config.ai_api_key`.
  - Asserts that `config.ai_api_key` is not None (as a safety check, though the caller should ensure this).
  - Raises `exceptions.GenAIClientInitError` if initialization fails (e.g., invalid key format).

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
    `config: models.Config` # Pass config for retry settings and model names (required)
  `) -> str`
  - Extracts text from *all lines* of the *first chunk* in `sub`.
  - Determine the method to use based on value of `speed_mode`.
  - If speed_mode = mock, return random context.
  - If speed_mode is 'fast' or 'normal':
    - **Check if `genai_client` is available:** If `genai_client` is `None`, raise `RuntimeError("Gemini client not available for context detection")` or handle appropriately (e.g., return default context, log error).
    - Uses the passed `genai_client` instance (with specific model names fetched from `config.fast_model` or `config.normal_model` based on `speed_mode`) to make remote API requests. Asserts that the required model name is present in config.
    - Uses a `tenacity` decorator directly on the function, configured with a **hardcoded 3 attempts** (ignoring `config.retry_max_attempts`), to wrap the API call.
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
    `genai_client: Optional[genai.client.Client],` # Pass the initialized Client instance; required if speed_mode isn't "mock"
    `config: models.Config` # Pass config for retry settings and model names (required)
  `) -> None`
  - Uses `asyncio.TaskGroup` to run `_translate_single_chunk` concurrently for each chunk in `sub`, passing `genai_client` and `config`.
  - Catches exceptions from tasks (including retried API errors from `_translate_single_chunk`) and raises `exceptions.ChunkTranslationError`.

- `async _translate_single_chunk(`
    `system_prompt: str,`
    `chunk_index: int,`
    `chunk: List[models.SubtitleBlock],`
    `target_lang: str,` # Full language name (e.g., "Vietnamese") - *Note: Used by caller (`translate_all_chunks`) to build `system_prompt`.*
    `speed_mode: str,` # Values: "mock", "fast", or "normal"
    `genai_client: Optional[genai.client.Client],` # Pass the initialized Client instance; required if speed_mode isn't "mock"
    `config: models.Config` # Pass config for retry settings and model names (required)
  `) -> None`
  - Determine the method based on `speed_mode`.
  - For 'mock' mode: copies original `content` to `translated_content`, includes `asyncio.sleep`.
  - For 'fast'/'normal':
    - **Check if `genai_client` is available:** If `genai_client` is `None`, raise `RuntimeError("Gemini client not available for chunk translation")` or handle appropriately.
    - Uses the **async** client (`genai_client.aio.models.generate_content`) with appropriate model (fetched from `config.fast_model` or `config.normal_model` based on `speed_mode`), requesting **JSON output**. Asserts that the required model name is present in config.
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
Entry point for the web app, wiring all components together. Conditionally initializes and manages the `genai.Client` instance based on configuration. Located within the `src` package.

Imports
- `Flask, request, render_template, send_file, jsonify` from `flask`
- `werkzeug.utils import secure_filename`
- `werkzeug.exceptions` # For standard HTTP errors
- `asyncio`
- `typing import Optional`
- `from google import generativeai as genai`
- `src.config_loader`
- `from translator import init_genai_client, parse_srt, detect_context, reassemble_srt, translate_all_chunks, Config, SubtitleBlock, exceptions as translator_exceptions, gemini_helper as translator_gemini_helper, parser as translator_parser, context_detector as translator_context_detector, chunk_translator as translator_chunk_translator, reassembler as translator_reassembler, models as translator_models` # Added models import
- `logging`
- `io`
- `tempfile`
- `os`
- `pathlib`
- `tenacity` # Potentially needed if defining retry config here
- `shutil` # For robust temp directory removal

Setup
- Load app config via `config_loader.load_config() -> config: translator_models.Config`. Halts startup (`SystemExit`) if loading fails (handled within `load_config`).
- Configure Python logging to console at `config.log_level`.
- Create Flask app instance `app = Flask(__name__, static_folder='static', template_folder='templates')`.
- Adds a route for `/favicon.ico`.
- **Conditionally instantiate shared AI client:**
  - `genai_client: Optional[genai.client.Client] = None` # Initialize to None
  - `if config.ai_provider == "google-gemini":`
    - `try:`
      - `genai_client = translator_gemini_helper.init_genai_client(config)` # Call helper only if provider matches
      - `logging.info(f"AI Provider '{config.ai_provider}' selected. Gemini Client initialized successfully.")`
    - `except translator_exceptions.GenAIClientInitError as e:`
      - `logging.exception(f"Failed to initialize Gemini Client for provider '{config.ai_provider}'. Translation features will be unavailable.")`
      - # Allow app to start, but client remains None. Errors will be caught later.
    - `except Exception as e:` # Catch other potential exceptions during client init
      - `logging.exception(f"An unexpected error occurred during Gemini Client initialization for provider '{config.ai_provider}'.")`
      - # Consider if this should halt startup or allow proceeding with client as None
      - raise RuntimeError(f"Critical component (Gemini Client for {config.ai_provider}) failed to initialize.") from e # Optionally halt startup
  - `elif config.ai_provider == "mock":` # Example: Handle a mock provider
    - `logging.info(f"AI Provider '{config.ai_provider}' selected. Using mock responses. No external client initialized.")`
    - # genai_client remains None, logic in translator components handles 'mock' speed_mode
  - `else:`
    - `logging.warning(f"Unsupported AI Provider '{config.ai_provider}' configured. Translation features requiring AI will be unavailable.")`
    - # genai_client remains None

Error Handling Setup
- Define custom error handlers using `@app.errorhandler`:
  - `@app.errorhandler(translator_exceptions.ValidationError)` -> `return jsonify({"error": str(e)}), 400`
  - `@app.errorhandler(translator_exceptions.ParsingError)` -> `return jsonify({"error": str(e)}), 422`
  - `@app.errorhandler(translator_exceptions.ContextDetectionError)` -> `return jsonify({"error": "Failed to detect context: " + str(e)}), 500`
  - `@app.errorhandler(translator_exceptions.ChunkTranslationError)` -> `return jsonify({"error": "Failed during translation: " + str(e)}), 500`
  - `@app.errorhandler(tenacity.RetryError)` -> `return jsonify({"error": "LLM API failed after multiple retries: " + str(e)}), 504` (Gateway Timeout)
  - `@app.errorhandler(werkzeug.exceptions.HTTPException)` -> Standard Flask/Werkzeug HTTP error handling.
  - `@app.errorhandler(RuntimeError)` -> Handle runtime errors like client unavailability: `logging.error(f"Runtime error: {e}")`, `return jsonify({"error": "Service configuration error prevents translation."}), 503`
  - `@app.errorhandler(Exception)` -> Generic fallback: `logging.exception("Unhandled error")`, `return jsonify({"error": "An unexpected error occurred"}), 500`

Routes
- `GET /`
  - Renders `templates/index.html`, passing the list of configured languages to the template:
    `return render_template('index.html', languages=config.target_languages)`
- `POST /translate`
  - **Check AI Provider and Client Availability:**
    - `speed_mode = request.form.get('speed_mode', 'normal')`
    - `if speed_mode != 'mock':`
      - `return jsonify({"error": f"Translation service not configured for provider '{config.ai_provider}' with speed mode '{speed_mode}'."}), 501` # Not Implemented
    - `if speed_mode != 'mock' and genai_client is None:`
      - `return jsonify({"error": f"Translation service unavailable for provider '{config.ai_provider}'. Client not initialized."}), 503` # Service Unavailable
  - **Temporary File Handling:** Use `tempfile.mkdtemp()` for safe temporary directory creation. Initialize `temp_dir = None` before try block.
  - **Try/Finally Block:** Wrap the core logic in a `try...finally` block.
  - Inside `try`:
    - Get file: `file = request.files.get('file')`. Validate presence.
    - Create temporary directory: `temp_dir = tempfile.mkdtemp()`
    - Secure filename and save: `filename = secure_filename(file.filename)`, `temp_file_path = os.path.join(temp_dir, filename)`, `file.save(temp_file_path)`
    - Parse SRT: `sub_chunks = translator_parser.parse_srt(temp_file_path, config.chunk_max_blocks)`
    - Get and validate target language: `target_lang = request.form.get('target_lang')`. Check presence and if in `config.target_languages`.
    - Detect context: `context = translator_context_detector.detect_context(sub_chunks, speed_mode, genai_client, config)` **(Passes potentially None client)**
    - Translate chunks: `asyncio.run(translator_chunk_translator.translate_all_chunks(context, sub_chunks, target_lang, speed_mode, genai_client, config))` **(Passes potentially None client)**
    - Reassemble SRT: `translated_srt_bytes = translator_reassembler.reassemble_srt(sub_chunks)`
    - Prepare response: `buffer = io.BytesIO(translated_srt_bytes)`, `download_filename = f"{pathlib.Path(filename).stem}_{target_lang}.srt"`
    - Send file: `return send_file(buffer, mimetype='text/srt', as_attachment=True, download_name=download_filename)`
  - The `finally` block ensures the temporary directory and its contents are removed: `if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)`

## Interfaces & Interaction Patterns
- Request flow (conceptual, actual calls use imported functions):
  - `src.app` receives request → Validates provider/client availability → `src.translator.parser` → `src.translator.context_detector` (uses passed `genai.Client` **only if available and needed**) → `src.translator.chunk_translator` (uses passed `genai.Client` **only if available and needed**) → `src.translator.reassembler` → `src.app` sends file response
- LLM interactions are handled within `src/translator/context_detector.py` and `src/translator/chunk_translator.py`, but only if `speed_mode` is not 'mock' **and** the `genai_client` instance passed from `app.py` is not `None`. These functions must check for the client's presence before attempting API calls.
- The **single, shared `genai.Client` instance** is created in `src.app.py` at startup and initialization succeeds. It is then **passed (potentially as `None`)** as an argument down to the services that might need it (`translator.context_detector`, `translator.chunk_translator`).
- The frontend (`index.html`, `static/js/app.js`) interaction remains the same, receiving languages and sending translation requests. The backend handles provider logic internally.
- Flask route (`src.app.py`) uses `asyncio.run` for asynchronous translation, preceded by checks for client availability based on `config.ai_provider` and `speed_mode`.

---

## Workflow / Use Case Examples
**Example 1: `AI_PROVIDER=google-gemini`, user selects "fast" mode**
- `src.config_loader.load_config()` reads `AI_PROVIDER="google-gemini"`, `AI_API_KEY`, model names, etc.
- `src.app` setup checks `config.ai_provider`. Since it's "google-gemini", it attempts to call `translator_gemini_helper.init_genai_client(config)`.
- If successful, `genai_client` is assigned the client instance. If it fails, `genai_client` remains `None`, and a log message is generated.
- User visits `GET /`, form populates as usual.
- User submits `POST /translate` with `speed_mode='fast'`.
- `src.app` checks: `speed_mode` is 'fast' (not 'mock'). It then checks `if genai_client is None:`.
    - If client initialization failed earlier, it returns a 503 error here.
    - If client is available, processing continues.
- `src.app` saves upload, calls `parser`.
- `src.app` calls `context_detector`, passing the **initialized `genai_client`** and `config`. `context_detector` uses the client and `config.fast_model`.
- `src.app` calls `translate_all_chunks` via `asyncio.run`, passing the **initialized `genai_client`** and `config`. `chunk_translator` uses the client and `config.fast_model`.
- `src.app` calls `reassembler`, sends file response.

---

## Implementation Notes, Edge Cases, and TODOs
- **AI Provider Handling:** The application now explicitly handles the `AI_PROVIDER` setting. Only if it's `"google-gemini"` will it attempt to initialize the Gemini client. Other providers (like a potential `"mock"`) or unsupported values result in the `genai_client` remaining `None`. Downstream functions (`context_detector`, `chunk_translator`) must check if the client is `None` before attempting to use it, especially when `speed_mode` is not 'mock'.
- **Configuration Dependencies:** `AI_API_KEY`, `FAST_MODEL`, `NORMAL_MODEL` are now conditionally required by `config_loader`
- **SDK Methods:** Verification of `google-genai` SDK methods remains necessary.
- **DONE:** Target language validation in `POST /translate` is implemented.
- **Filename Generation:** Output filename `original_stem_TargetLanguage.srt` is used.
- Error Handling: Includes checks for client availability in `POST /translate` and relies on handlers for `RuntimeError` if components try to use a `None` client unexpectedly.
- Retry Logic: Still uses hardcoded 3 attempts, ignoring `config.retry_max_attempts`. **TODO:** Make retry attempts configurable.
- SRT Handling: Graceful handling of empty/malformed SRT files is implemented in the parser.
- **Gemini Client Management:** The single `genai.Client` instance is created once in `app.py` *if applicable*. Thread-safety considerations for the client still apply if using multi-threaded workers.
- Response Validation: **MISSING:** Structural validation of the LLM JSON response in `_translate_single_chunk` is still needed. **TODO:** Implement robust validation.
- TODO: Consider making context sample size configurable.
- Logging: Includes logs for provider selection and client initialization status.

---

## Testing Considerations
- **Test Structure:** Remains the same (`tests/automated/`, `tests/manual/`).
- **Automated Tests (`tests/automated/`):**
    - **Unit Tests (`tests/automated/unit/`):**
        - Mock dependencies (srt, file system).
        - Mock the `genai.Client` instance **when testing components that receive it**.
        - Mock the `config` object extensively:
            - Test `config_loader` with `AI_PROVIDER="google-gemini"` (requiring key/models) and other values (e.g., "mock", "unsupported"). Verify conditional requirement logic.
            - Test `context_detector` and `chunk_translator`:
                - Pass `config` with `ai_provider="google-gemini"`. Mock the passed `genai_client`'s methods. Verify model name selection (`config.fast_model` etc.).
                - Pass `config` with `ai_provider="mock"` or "unsupported". Pass `genai_client=None`. Verify that client methods are *not* called and appropriate behavior occurs (e.g., mock response if `speed_mode` is 'mock', or error/fallback if `speed_mode` is 'fast'/'normal').
    - **Integration Tests (`tests/automated/integration/`):**
        - Use Flask test client (`app.test_client()`).
        - Test `app.py` setup: Patch `config_loader.load_config` to return different mock `Config` objects.
            - Verify `genai_client` is initialized only when `config.ai_provider == "google-gemini"`. Patch `translator_gemini_helper.init_genai_client` to simulate success or failure.
            - Verify logging messages reflect the provider and initialization status.
        - Test `POST /translate` route:
            - With `config.ai_provider="google-gemini"` (mocked):
                - Simulate successful client init: Mock downstream translator calls. Verify success response.
                - Simulate failed client init: Verify 503 error response when `speed_mode` is not 'mock'.
                - Test with `speed_mode="mock"`: Verify mock translation occurs even if client init failed (or succeeded).
            - With `config.ai_provider="mock"` (mocked):
                - Test with `speed_mode="mock"`: Verify success with mock translation.
                - Test with `speed_mode="fast"`/`"normal"`: Verify 501/503 error response (depending on chosen logic for this combination).
            - With `config.ai_provider="unsupported"` (mocked):
                - Verify 501/503 error response for non-mock `speed_mode`.
- **Manual Tests (`tests/manual/`):** Use `.env` files with different `AI_PROVIDER` settings to manually verify application behavior.
- **Test Coverage:** Focus on testing the conditional logic in `app.py` setup and `POST /translate`, and the handling of the potentially `None` client in `context_detector` and `chunk_translator`.