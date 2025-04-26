**Phase 0: Project Setup & Dependencies**

1.  **Initialize Project:** Set up a new directory structure or branch.
2.  **Install Dependencies:** Add `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings` (for config), `python-dotenv`, `google-genai`, `tenacity`, `srt`, `jinja2`, `python-multipart` (for form data/file uploads), and `aiofiles` (for async file operations).
3.  **Basic FastAPI App:** Create `src/main.py` with a `FastAPI` instance. Add a simple `async def health_check():` route (`/health`) to verify setup with `uvicorn src.main:app --reload`.
4.  **Directory Structure:** Keep the `src/translator/` structure largely the same for the core logic modules. Move Flask-specific `templates/` and `static/` under `src/`.

**Phase 1: Configuration & Models**

5.  **Pydantic Models:**
    *   Convert `src/translator/models.py`: Change `SubtitleBlock` from a dataclass to a Pydantic `BaseModel`.
    *   Define `src/config.py`: Create a `Settings` class inheriting from Pydantic's `BaseSettings` to load configuration from `.env` automatically (replaces `config_loader.py`). Include fields like `gemini_api_key`, `target_languages` (perhaps validated as `List[str]`), `chunk_max_blocks`, `retry_max_attempts`, `log_level`.
6.  **Configuration Dependency:** Create a simple dependency function (e.g., in `src/dependencies.py`) that provides an instance of the `Settings` class.

**Phase 2: Core Logic Adaptation (Async Focus)**

7.  **Gemini Client Dependency:**
    *   Keep `src/translator/gemini_helper.py` for the `init_genai_client` function (or adapt it slightly).
    *   Create a dependency (e.g., in `src/dependencies.py`) that initializes the `genai.Client` *once* using the `Settings` dependency and yields/returns it. This manages the client lifecycle.
8.  **Async Function Signatures:**
    *   Ensure `src/translator/context_detector.py::detect_context` is `async def` as it performs network I/O. Update its signature to potentially accept the `genai.Client` and `Settings` instance directly (passed by the route handler).
    *   `src/translator/chunk_translator.py`: Functions `translate_all_chunks` and `_translate_single_chunk` are already async, which is great. Update signatures to accept `genai.Client` and `Settings` if needed. Keep Tenacity decorators.
9.  **Async File Handling (Parser):**
    *   Modify `src/translator/parser.py::parse_srt`: Instead of a file path, it *could* potentially accept `content: bytes` or `content: str`. However, the `srt` library likely works best with files.
    *   Therefore, the *route handler* (in `main.py`) will receive the `UploadFile`, *asynchronously* save its contents to a temporary file using `aiofiles`, and then pass the *temporary file path* to `parse_srt`. `parse_srt` itself might remain synchronous internally if the `srt` library doesn't support async I/O, but the surrounding file write will be non-blocking.
10. **Reassembler:** `src/translator/reassembler.py::reassemble_srt` likely remains synchronous CPU-bound code.

**Phase 3: FastAPI Endpoints & Integration**

11. **Static Files & Templates:**
    *   In `src/main.py`, mount the `StaticFiles` directory.
    *   Configure `Jinja2Templates`.
12. **`GET /` Route:**
    *   Create an `async def get_index(request: Request, settings: Settings = Depends(get_settings_dependency))` route.
    *   Use the injected `settings` to get `target_languages`.
    *   Return `templates.TemplateResponse("index.html", {"request": request, "languages": settings.target_languages})`.
13. **`POST /translate` Route:**
    *   Create an `async def translate_subtitle(...)` route.
    *   Define parameters using FastAPI type hints:
        *   `file: UploadFile = File(...)`
        *   `target_lang: str = Form(...)`
        *   `speed_mode: str = Form(...)`
        *   `settings: Settings = Depends(get_settings_dependency)`
        *   `genai_client: genai.Client = Depends(get_gemini_client_dependency)`
    *   **Input Validation:** Add validation for `target_lang` against `settings.target_languages` (can be done within the route or using a Pydantic model/enum if preferred). Maybe validate `speed_mode` values too.
    *   **Temporary File:** Use `tempfile.mkdtemp()` and `aiofiles` within an `async with` block to save `await file.read()` to a temporary path asynchronously.
    *   **Orchestration:**
        *   Call `sub_chunks = parse_srt(temp_file_path, settings.chunk_max_blocks)` (sync call after async save).
        *   `context = await detect_context(sub_chunks, speed_mode, genai_client, settings)`
        *   `await translate_all_chunks(context, sub_chunks, target_lang, speed_mode, genai_client, settings)`
        *   `translated_srt_bytes = reassemble_srt(sub_chunks)` (sync call)
    *   **Response:** Generate the filename. Return a `StreamingResponse(io.BytesIO(translated_srt_bytes), media_type="text/srt", headers={"Content-Disposition": f"attachment; filename={download_filename}"})`.
    *   **Cleanup:** Ensure the temporary directory is cleaned up using a `try...finally` block around the core logic.

**Phase 4: Error Handling**

14. **Exception Handlers:** Define custom exception handlers using `@app.exception_handler()` in `src/main.py` for your custom exceptions (`ValidationError`, `ParsingError`, etc.) and potentially for `tenacity.RetryError`. Map them to appropriate HTTP status codes and JSON responses (e.g., using a Pydantic error model).

**Phase 5: Testing & Deployment Prep**

15. **Write Tests:** Use `pytest` with `pytest-asyncio`. Employ FastAPI's `TestClient` to make requests to your async endpoints. Mock dependencies (especially the `genai.Client` and `Settings`) using FastAPI's dependency overrides feature.
16. **Run:** Use `uvicorn src.main:app --host 0.0.0.0 --port 8000` (or similar) to run the server.

This roadmap emphasizes using FastAPI's features like Dependency Injection for managing configuration and the Gemini client, leverages Pydantic for settings and potentially validation, ensures async is used for I/O (file saving, API calls), and structures the application in a way that is common for FastAPI projects.