# Task number and name: 3 - FastAPI Endpoints & Integration

## Project Context
This project is a web application that translates subtitle files (in `.srt` format) from their original language to a user-selected target language. It uses the Google Gemini AI for the translation process. The core translation logic involves parsing the SRT file into chunks, detecting the overall context, translating each chunk using the AI (potentially in parallel), and then reassembling the translated chunks back into a downloadable SRT file. The application needs a web interface to allow users to upload a file, select the target language and translation speed, and receive the translated file.

## Prerequisites
- A FastAPI application instance exists in `src/main.py`.
- Required libraries are installed: `fastapi`, `uvicorn`, `pydantic`, `jinja2`, `python-multipart`, `google-generativeai`, `srt`, `tenacity`, `aiofiles`.
- Configuration is managed by a Pydantic `BaseSettings` model (let's call it `Settings`) in `src/config.py`, loaded automatically from environment variables or a `.env` file. This includes `target_languages: List[str]`.
- A dependency function `get_settings_dependency` exists in `src/dependencies.py` that provides an instance of `Settings`.
- A dependency function `get_gemini_client_dependency` exists in `src/dependencies.py` that provides a pre-initialized and configured `google.generativeai.Client` instance.
- Core translation logic functions are available in the `src/translator/` directory:
    - `src/translator/models.py`: Defines a Pydantic model `SubtitleBlock` with fields like `index`, `start`, `end`, `content`, `translated_content`.
    - `src/translator/parser.py`: Contains `parse_srt(file_path: str, chunk_max_blocks: int) -> List[List[models.SubtitleBlock]]`. It takes a file path string and returns a list of lists (chunks) of `SubtitleBlock` objects. It raises `translator.exceptions.ValidationError` or `translator.exceptions.ParsingError` on failure. Assume standard exceptions like `FileNotFoundError` might also occur if the path is invalid.
    - `src/translator/context_detector.py`: Contains `async def detect_context(sub: List[List[models.SubtitleBlock]], speed_mode: str, genai_client: genai.client.Client, config: Settings) -> str`. It takes the chunked subtitles, speed mode ("fast" or "normal"), the Gemini client instance, and the application settings, returning a context string. It might raise exceptions related to API calls (e.g., `google.api_core.exceptions` or custom ones like `translator.exceptions.ContextDetectionError`) or `tenacity.RetryError`.
    - `src/translator/chunk_translator.py`: Contains `async def translate_all_chunks(context: str, sub: List[List[models.SubtitleBlock]], target_lang: str, speed_mode: str, genai_client: genai.client.Client, config: Settings) -> None`. This function modifies the passed `SubtitleBlock` objects *in-place*, setting their `translated_content` field. It takes the context, chunks, target language string, speed mode, Gemini client, and settings. It uses `asyncio` internally and might raise exceptions related to API calls, JSON parsing (`translator.exceptions.GenAIParsingError`), or general processing (`translator.exceptions.ChunkTranslationError`), or `tenacity.RetryError`.
    - `src/translator/reassembler.py`: Contains `reassemble_srt(sub: List[List[models.SubtitleBlock]]) -> bytes`. Takes the (potentially modified) chunks and returns the complete translated SRT content as bytes.
- Static assets (`style.css`, `app.js`) are located in `src/static/`.
- The main HTML template (`index.html`) is located in `src/templates/`.

## Subtask 1: Configure Static Files and Templates
In `src/main.py`, configure the FastAPI application to:
- Serve static files from the `src/static/` directory under the path `/static`.
- Use Jinja2 for templating, loading templates from the `src/templates/` directory. Initialize a `Jinja2Templates` instance for this purpose.

## Subtask 2: Implement `GET /` Endpoint
Create an asynchronous route handler function for `GET /` requests in `src/main.py`.
- This route should depend on the `Settings` provided by `get_settings_dependency`.
- It needs to render the `src/templates/index.html` template.
- Pass the `request` object and the list of `target_languages` (obtained from the injected `Settings`) to the template context so that the language selection dropdown can be populated dynamically.

## Subtask 3: Implement `POST /translate` Endpoint Core Logic
Create an asynchronous route handler function for `POST /translate` requests in `src/main.py`.
- This route must accept `multipart/form-data` requests.
- Define parameters using FastAPI's type hints and utilities:
    - An uploaded file, named `file` (`UploadFile` from `fastapi`).
    - A form field named `target_lang` (string).
    - A form field named `speed_mode` (string).
- Inject dependencies for `Settings` (using `get_settings_dependency`) and the `genai.Client` (using `get_gemini_client_dependency`).
- Perform initial validation: Check if the received `target_lang` string exists within the `target_languages` list from the injected `Settings`. If not, raise an appropriate HTTP exception (e.g., 400 Bad Request) with a clear error message. Also validate the `speed_mode` if necessary (e.g., ensuring it's "fast" or "normal").
- Create a temporary directory using the `tempfile` module.
- Asynchronously read the content of the uploaded `file` and save it to a temporary file (with a secure filename, e.g., using `werkzeug.utils.secure_filename` or similar logic) within the created temporary directory. Use `aiofiles` for asynchronous file writing. Remember the full path to this temporary file.
- Call the `parse_srt` function (from `src/translator/parser.py`), passing the temporary file path and the `chunk_max_blocks` value from the `Settings`. Store the resulting list of chunks.
- Call the `detect_context` function (from `src/translator/context_detector.py`), passing the chunks, the received `speed_mode`, the injected `genai.Client`, and the injected `Settings`. Store the resulting context string.
- Call the `translate_all_chunks` function (from `src/translator/chunk_translator.py`), passing the context, the chunks, the received `target_lang`, the `speed_mode`, the injected `genai.Client`, and the injected `Settings`. This function modifies the chunks in place.
- Call the `reassemble_srt` function (from `src/translator/reassembler.py`), passing the modified chunks. Store the resulting bytes.

## Subtask 4: Implement `POST /translate` Endpoint Response
- Continuing within the `POST /translate` route handler:
- Generate a suitable download filename for the translated SRT file. It should incorporate the original filename stem and the target language (e.g., `original_stem_TargetLang.srt`). Use `pathlib` to help extract the stem from the original `file.filename`.
- Return the translated SRT bytes to the client. Use FastAPI's `StreamingResponse`. Wrap the bytes in an `io.BytesIO` object. Set the `media_type` to `"text/srt"`. Set the `Content-Disposition` header to `attachment; filename="your_generated_filename.srt"` to trigger a download in the browser.

## Subtask 5: Implement Cleanup
- Still within the `POST /translate` route handler, ensure that the temporary directory created earlier (and the temporary file within it) are reliably deleted after the request is processed, regardless of whether an error occurred during processing. Use a `try...finally` block around the core logic (parsing, context detection, translation, reassembly, response generation) to achieve this. Use appropriate functions (like `os.remove`, `shutil.rmtree`, or `os.rmdir`) within the `finally` block for cleanup.