## Task 3: FastAPI Endpoints & Integration

**Project Context**
This task involves creating the user-facing API endpoints for the subtitle translation application using the FastAPI framework. It builds directly upon the Pydantic models, configuration (`Settings`), and adapted core logic (async functions, Gemini client management) established in Tasks 1 and 2. The goal is to expose the application's functionality over HTTP, handling web requests, orchestrating the translation workflow, and returning responses.

**Prerequisites**
*   A working FastAPI project setup (`src/main.py` with a `FastAPI` instance).
*   Completed code from Task 1 (`src/config.py::Settings`, `src/translator/models.py::SubtitleBlock`) and Task 2 (`src/dependencies.py` with `get_settings` and `get_gemini_client` dependencies, adapted async functions in `src/translator/`, lifespan manager in `src/main.py` for client initialization).
*   Required libraries installed: `fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `aiofiles`.
*   An HTML template file located at `src/templates/index.html` (similar to the one described in the original Flask design).
*   Static assets (CSS, JS) located within a `src/static/` directory.

**Subtask 1: Configure Static Files and Templates**
In your main application file (`src/main.py`), configure FastAPI to serve static files and use Jinja2 for templating.
1.  Mount the static files directory: Use `app.mount("/static", StaticFiles(directory="src/static"), name="static")`. Ensure the `StaticFiles` class is imported from `starlette.staticfiles`.
2.  Configure Jinja2 templates: Instantiate `Jinja2Templates` pointing to the `src/templates` directory (e.g., `templates = Jinja2Templates(directory="src/templates")`). Ensure `Jinja2Templates` is imported from `fastapi.templating`.

**Subtask 2: Implement GET / Route**
Create the main landing page route that serves the HTML interface.
1.  Define an `async` function for the `GET` request to the root path (`/`). Use the `@app.get("/")` decorator.
2.  This function should accept `request: Request` (imported from `fastapi`) as a parameter.
3.  Inject the application settings using dependency injection: add a parameter `settings: Settings = Depends(get_settings)` (import `Depends` from `fastapi`, `Settings` from `src.config`, and `get_settings` from `src.dependencies`).
4.  Inside the function, retrieve the list of target languages from the injected `settings` object (`settings.target_languages`).
5.  Return a `TemplateResponse` using the configured `templates` object. Pass the template name (`"index.html"`), and a context dictionary containing at least `{"request": request, "languages": settings.target_languages}`.

**Subtask 3: Implement POST /translate Route**
Create the core API endpoint responsible for handling subtitle file uploads and translation requests.
1.  Define an `async` function for the `POST` request to the `/translate` path. Use the `@app.post("/translate")` decorator.
2.  Define the function parameters to accept the required inputs using FastAPI's parameter types:
    *   `file: UploadFile = File(...)`: For the uploaded `.srt` file (import `UploadFile` and `File` from `fastapi`).
    *   `target_lang: str = Form(...)`: For the target language selected by the user (import `Form` from `fastapi`).
    *   `speed_mode: str = Form(...)`: For the selected speed mode.
    *   Inject dependencies: `settings: Settings = Depends(get_settings)` and `genai_client = Depends(get_gemini_client)` (ensure the client type hint matches the actual client object type, e.g., `genai.Client` or `genai.GenerativeModel`).
3.  **Input Validation:**
    *   Immediately after receiving the parameters, check if the provided `target_lang` string is present within the `settings.target_languages` list. If not, raise an `HTTPException` (imported from `fastapi`) with a `status_code=400` (Bad Request) and an appropriate detail message (e.g., "Invalid target language specified").
    *   Optionally, add validation for `speed_mode` to ensure it's one of the expected values (e.g., "normal", "fast", "mock"). Raise a 400 `HTTPException` if invalid.
4.  **Temporary File Handling:**
    *   Use the `tempfile` module (e.g., `tempfile.mkdtemp()`) to create a secure temporary directory.
    *   Construct the full path for a temporary file within that directory (e.g., using `os.path.join`).
    *   Use the `aiofiles` library within an `async with aiofiles.open(temp_file_path, 'wb') as temp_f:` block to asynchronously write the contents of the uploaded file: `content = await file.read()`, followed by `await temp_f.write(content)`. Remember to handle potential file read errors.
5.  **Orchestration (Inside a `try` block):**
    *   Call the synchronous `parse_srt` function (from `src.translator.parser`) passing the `temp_file_path` and `settings.chunk_max_blocks`. Store the resulting list of subtitle chunks. Handle potential `ParsingError` or `ValidationError` exceptions raised by the parser (consider re-raising as appropriate HTTPExceptions or letting specific exception handlers catch them later).
    *   Call the asynchronous `detect_context` function (from `src.translator.context_detector`), passing the subtitle chunks, `speed_mode`, the injected `genai_client`, and the `settings`. Use `await` for the call.
    *   Call the asynchronous `translate_all_chunks` function (from `src.translator.chunk_translator`), passing the detected context, subtitle chunks, `target_lang`, `speed_mode`, the injected `genai_client`, and the `settings`. Use `await`. This function modifies the chunks in place.
    *   Call the synchronous `reassemble_srt` function (from `src.translator.reassembler`), passing the modified subtitle chunks. Store the returned bytes.
6.  **Response Generation:**
    *   Generate a suitable download filename for the translated file. Use the original filename stem (e.g., using `pathlib.Path(file.filename).stem`) combined with the target language (e.g., `f"{original_stem}_{target_lang}.srt"`).
    *   Create an in-memory byte stream from the reassembled bytes: `buffer = io.BytesIO(translated_srt_bytes)` (import `io`).
    *   Return a `StreamingResponse` (imported from `fastapi.responses`). Pass the `buffer` as the content. Set the `media_type` to `"text/srt"`. Add a `headers` dictionary with the `Content-Disposition` set for attachment and the generated filename (e.g., `{"Content-Disposition": f"attachment; filename={download_filename}"}`).
7.  **Cleanup (Inside a `finally` block):**
    *   Ensure the temporary directory created earlier and all its contents are reliably removed, regardless of whether the translation succeeded or failed. Use `os.remove` for the temporary file and `os.rmdir` for the directory, or preferably `shutil.rmtree(temp_dir_path)` (import `shutil`) to handle non-empty directories robustly. Place this cleanup logic within a `finally` clause associated with the `try` block that encompasses the temporary file creation and processing steps.

**Debugging**
1.  Run the FastAPI application using Uvicorn: `uvicorn src.main:app --reload`.
2.  Open your web browser and navigate to the root URL (e.g., `http://127.0.0.1:8000`). Verify the page loads and the language dropdown is populated correctly.
3.  Use the web form to upload a valid `.srt` file, select a language and speed mode, and submit. Check if the translation process completes and a file download is triggered. Use your browser's developer tools (Network tab) to inspect the request and response.
4.  For more direct API testing, use a tool like `curl` or HTTPie to send a `POST` request to the `/translate` endpoint. Ensure you construct a multipart/form-data request including the `file`, `target_lang`, and `speed_mode` fields. Example (conceptual using `curl`):
    ```bash
    curl -X POST http://127.0.0.1:8000/translate \
      -F "file=@/path/to/your/subtitle.srt" \
      -F "target_lang=Vietnamese" \
      -F "speed_mode=fast" \
      -o output.srt
    ```
    Check the `output.srt` file and any error messages returned by the server.