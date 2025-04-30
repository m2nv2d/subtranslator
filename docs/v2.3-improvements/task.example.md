# Task 1: Adapt `src/main.py` from Flask to FastAPI

## Project Context
You are refactoring a specific Python web application file, `src/main.py` (which was previously named `src/app.py`), from using the Flask framework to using the FastAPI framework. The goal is to make the application runnable via an ASGI server like Uvicorn, while reusing as much of the existing underlying business logic as possible. This logic resides primarily in a package named `translator` within the `src` directory. The application translates subtitle files (.srt).

## Prerequisites
Ensure the following libraries are available in the Python environment: `fastapi`, an ASGI server (like `uvicorn`), `jinja2`, `python-multipart` (for form data handling in FastAPI), and `aiofiles` (for asynchronous file operations). You will need access to the existing code, particularly the file `src/main.py` (which contains the Flask implementation) and the contents of the `src/translator/` directory, especially `src/translator/exceptions.py` for custom exception types. The overall project structure follows the layout described in the technical design document.

## Subtask 1: Update Imports and Basic Setup
Review the existing imports in `src/main.py`. Remove all Flask-specific imports (`Flask`, `request`, `render_template`, `send_file`, `jsonify`, `werkzeug.utils`, `werkzeug.exceptions`). Introduce corresponding imports from FastAPI for application creation (`FastAPI`), request/response objects (`Request`, `HTMLResponse`, `JSONResponse`, `StreamingResponse`), file handling (`UploadFile`, `File`), form data (`Form`), dependency injection (`Depends`, though maybe not used initially), static files (`StaticFiles`), templating (`Jinja2Templates`), and exceptions (`HTTPException`). Ensure necessary standard library imports (`io`, `os`, `pathlib`, `tempfile`, `shutil`, `logging`, `asyncio`) and imports from the `translator` package are retained or added if needed.

## Subtask 2: Initialize FastAPI Application, Templates, and Static Files
Replace the Flask application instance creation (`app = Flask(...)`) with a FastAPI instance (`app = FastAPI()`). Configure the application to serve static files from the `src/static` directory under the `/static` URL path using FastAPI's `StaticFiles` and `app.mount`. Initialize Jinja2 templating using `Jinja2Templates`, pointing it to the `src/templates` directory. Store the templates object in a variable (e.g., `templates`).

## Subtask 3: Preserve Configuration and AI Client Initialization Logic
Locate the existing code block responsible for loading application configuration (likely calling a function from `src.config_loader`) and conditionally initializing an AI client (e.g., `genai_client`) based on the configuration (`config.ai_provider`). This block, including logging, should remain largely unchanged and execute at the module level so that the `config` object and the `genai_client` (which might be `None`) are available globally within the `main.py` module for routes and handlers to use.

## Subtask 4: Convert Error Handlers
Find all Flask error handlers (`@app.errorhandler(...)`). Convert them to FastAPI exception handlers using the `@app.exception_handler(ExceptionType)` decorator. Each handler function must be defined as `async def handler_name(request: Request, exc: ExceptionType)` and should return a `fastapi.responses.JSONResponse` object with the appropriate JSON payload (e.g., `{"error": str(exc)}`) and HTTP status code. You need to create handlers for the custom exceptions defined in `src/translator/exceptions.py`:
- `ValidationError` (400)
- `ParsingError` (422)
- `ContextDetectionError` (500)
- `ChunkTranslationError` (500)
Also, handle `tenacity.RetryError` (504) and `RuntimeError` (503 if it's a client initialization/configuration issue, 500 otherwise). Note that `GenAIClientInitError`, `GenAIRequestError`, and `GenAIParsingError` might be caught by other handlers (like `RuntimeError` or `RetryError`) depending on where they are raised. Ensure appropriate logging is maintained within the handlers.

## Subtask 5: Refactor the Root Route (`GET /`)
Locate the Flask route for `GET /`. Convert its decorator to FastAPI's `@app.get("/", response_class=HTMLResponse)`. Change the function definition to be asynchronous (`async def`) and accept `request: Request` as the first argument. Replace the call to Flask's `render_template` with a call to the `templates.TemplateResponse` method of the Jinja2Templates instance created in Subtask 2. Ensure you pass the template name (`"index.html"`) and the context dictionary. The context dictionary must include the `request` object (`{"request": request, ...}`) and the `languages` variable derived from the global `config` object (`config.target_languages`).

## Subtask 6: Refactor the Translation Route (`POST /translate`)
Locate the Flask route for `POST /translate`. Convert its decorator to FastAPI's `@app.post("/translate")`. Change the function definition to be asynchronous (`async def`). Remove direct access to `request.form` and `request.files`. Instead, define parameters in the function signature using FastAPI's type hints and default values: `file: UploadFile = File(...)`, `target_lang: str = Form(...)`, `speed_mode: str = Form("normal")`.
Re-implement the file handling logic:
- Get the original filename using `file.filename`. Use `secure_filename` (imported from `werkzeug.utils` or reimplemented if Werkzeug is removed) on this name.
- Create a temporary directory using `tempfile.mkdtemp()`.
- Save the uploaded file content to a path within the temporary directory. You can use `await file.read()` and then write asynchronously using `aiofiles`, or use synchronous file operations which FastAPI will run in a thread pool.
- Keep the `try...finally` block that ensures the temporary directory is removed using `shutil.rmtree`.
Preserve the logic at the beginning of the function that checks `config.ai_provider`, `speed_mode`, and the availability of the global `genai_client`. When errors are detected here (e.g., client not available for required mode), raise FastAPI's `HTTPException` with the appropriate status code (501, 503) and detail message.
The calls to the underlying `translator` functions (`parse_srt`, `detect_context`, `reassemble_srt`) should remain syntactically similar. However, the call to `translate_all_chunks` was previously wrapped in `asyncio.run()`. Since the FastAPI route handler is now `async`, you should directly `await` the call: `await translator_chunk_translator.translate_all_chunks(...)`.
Replace the Flask `send_file` response. Create an `io.BytesIO` buffer from the `translated_srt_bytes` returned by the reassembler. Construct the `download_filename` using the original stem and target language, same as before. Return a `fastapi.responses.StreamingResponse`, passing the buffer, the `media_type='text/srt'`, and a `headers` dictionary containing the `Content-Disposition` header to trigger the download with the correct filename.

## Debug Script Reference
After implementing these changes in `src/main.py`, you can perform a basic manual test. Execute the script located at `tests/manual/run_fastapi_test.sh`. This script should start the Uvicorn server and potentially use `curl` or a similar tool to send a POST request with an SRT file to the `/translate` endpoint, verifying that it returns a translated SRT file without server errors. Consult the script for specific parameters or required test files.