## Task 8: Flask Web Application & Orchestration

### Project Context

You are building the main web application file for a service that translates SRT subtitle files. This file will act as the entry point and orchestrator, connecting various backend modules. For this specific task, focus on integrating components but use mock logic for context detection and placeholder logic for the actual translation step. The application uses Flask and interacts with modules for configuration, parsing, context detection (mock for now), translation (placeholder for now), and reassembly. A shared client instance for a Generative AI service (like Gemini) will be initialized but not used for real API calls in this task's scope.

### Prerequisites

*   Access to the project's `src` directory structure as defined in the technical design.
*   Ensure necessary libraries are installed (Flask, python-dotenv, Werkzeug, google-genai, tenacity, srt). You might be using `uv` or `pip` for environment management.
*   Completed implementations (or stable interfaces) for the following modules should be available within the `src` directory. You will need to check these files for the exact, potentially updated, function signatures and data models:
    *   `src/config_loader.py`: Contains `load_config() -> models.Config`.
    *   `src/exceptions.py`: Defines custom exception classes like `ValidationError`, `ParsingError`, `ContextDetectionError`, `ChunkTranslationError`, `GenAIClientInitError`, etc.
    *   `src/models.py`: Defines data classes `Config` and `SubtitleBlock`. Check this file for the exact fields (e.g., `Config.target_languages`, `Config.chunk_max_blocks`, `Config.log_level`, `Config.ai_api_key`, `SubtitleBlock` fields).
    *   `src/parser.py`: Contains `parse_srt(file_path: str, chunk_max_blocks: int) -> List[List[models.SubtitleBlock]]`.
    *   `src/gemini_helper.py`: Contains `init_genai_client(config: models.Config) -> genai.client.Client`. Note: `genai.client.Client` is the type hint from the `google-genai` library.
    *   `src.context_detector.py`: Contains `detect_context(sub: List[List[models.SubtitleBlock]], speed_mode: str, genai_client: genai.client.Client, config: models.Config) -> str`. Assume this function correctly implements a "mock" mode behavior based on the `speed_mode` parameter.
    *   `src.chunk_translator.py`: Contains an async function `translate_all_chunks(context: str, sub: List[List[models.SubtitleBlock]], target_lang: str, speed_mode: str, genai_client: genai.client.Client, config: models.Config) -> None`. For this task, treat calls to this as a placeholder; ensure the call signature is correct, but don't rely on it performing actual translation yet. Assume it handles mock logic based on `speed_mode` if necessary for testing flow.
    *   `src.reassembler.py`: Contains `reassemble_srt(sub: List[List[models.SubtitleBlock]]) -> bytes`.
*   A `templates` directory with an `index.html` file suitable for rendering a basic form.
*   Standard Python libraries (`logging`, `io`, `asyncio`).

### Subtask 1: Initial Setup and Configuration

Implement the initial setup within `src/app.py`.
*   Import all necessary modules and libraries (Flask, request, render\_template, send\_file, jsonify, werkzeug exceptions, asyncio, io, tenacity, logging, google.genai, and all custom `src.*` modules listed above).
*   Load the application configuration by calling `src.config_loader.load_config()` and store the returned `models.Config` object.
*   Configure standard Python logging based on the `log_level` specified in the loaded config object.
*   Create the Flask application instance (`app = Flask(__name__)`).

### Subtask 2: Shared Generative AI Client Initialization

Implement the initialization of the shared Generative AI client instance within `src/app.py`.
*   Declare a variable (e.g., `genai_client`) initialized to `None`.
*   Use a try-except block to call `src.gemini_helper.init_genai_client`, passing the loaded `config` object. Store the returned client instance in your variable.
*   Log success or failure messages.
*   If initialization fails (catches `src.exceptions.GenAIClientInitError` or potentially other exceptions from the helper), log the error critically and raise a `RuntimeError` to halt application startup, indicating the critical component failed.

### Subtask 3: Application-Wide Error Handling

Define global error handlers using `@app.errorhandler` within `src/app.py`.
*   Create handlers for custom exceptions defined in `src.exceptions` (e.g., `ValidationError`, `ParsingError`, `ContextDetectionError`, `ChunkTranslationError`). These handlers should return a JSON response containing an "error" key with the exception message and an appropriate HTTP status code (e.g., 400, 422, 500).
*   Add a handler for `tenacity.RetryError`, returning a JSON error response and status code 504.
*   Consider adding handlers for standard `werkzeug.exceptions.HTTPException` if needed.
*   Implement a generic fallback handler for `Exception` to catch any unhandled errors, log them, and return a generic 500 JSON error response.

### Subtask 4: Implement Frontend Route (`GET /`)

Define the route for the main page within `src/app.py`.
*   Create a Flask route for `GET /`.
*   This route should render the `templates/index.html` template.
*   Pass the list of available target languages (`config.target_languages`, obtained from the loaded config object) to the template context under the key `languages`.

### Subtask 5: Implement Translation Route (`POST /translate`) - Orchestration Logic

Define the main translation workflow route within `src/app.py`.
*   Create a Flask route for `POST /translate`.
*   **Client Check:** At the beginning of the route handler, check if the shared `genai_client` instance (initialized in Subtask 2) is not `None`. If it is `None` (meaning initialization failed), return a JSON error response with status code 503 (Service Unavailable).
*   **Error Boundary:** Wrap the main processing logic within a `try...except` block to catch the custom exceptions defined in `src.exceptions` and allow the handlers defined in Subtask 3 to manage the responses.
*   **Input Processing:**
    *   Retrieve the uploaded file from `request.files` (handle potential missing file).
    *   Retrieve `target_lang` and `speed_mode` (defaulting to 'normal' if absent) from `request.form`.
    *   **Validate `target_lang`:** Check if the received `target_lang` string exists within the `config.target_languages` list. If not, raise `ValidationError`.
*   **Workflow Orchestration:**
    *   Call `src.parser.parse_srt`, passing the file object (you might need to save it temporarily or pass the stream) and `config.chunk_max_blocks`. Store the returned chunks (`List[List[models.SubtitleBlock]]`).
    *   Call `src.context_detector.detect_context`, passing the subtitle chunks, `speed_mode`, the shared `genai_client` instance, and the `config` object. Store the returned `context` string. **Ensure this call uses the *mock* detection logic (e.g., by passing `speed_mode='mock'` or relying on the detector's implementation).**
    *   Call `src.chunk_translator.translate_all_chunks` using `asyncio.run`. Pass the `context`, subtitle chunks, `target_lang`, `speed_mode`, the shared `genai_client` instance, and the `config` object. **Treat this as a placeholder call for now; it needs to match the function signature but doesn't need to perform real translation.** Assume it might update the `SubtitleBlock` objects in-place with mock data based on the `speed_mode`.
    *   Call `src.reassembler.reassemble_srt`, passing the (potentially mock-modified) subtitle chunks. Store the returned `bytes` object.
*   **Response Generation:**
    *   Create an in-memory file-like object (e.g., `io.BytesIO`) from the reassembled bytes.
    *   Use Flask's `send_file` function to send the buffer back to the client as a downloadable file attachment. Construct a suitable filename (e.g., based on the original filename and target language).

### Subtask 6: Basic Application Runner

Include a standard `if __name__ == "__main__":` block at the end of `src/app.py` to run the Flask development server when the script is executed directly. Use `app.run(debug=True)` or an equivalent for development purposes.
