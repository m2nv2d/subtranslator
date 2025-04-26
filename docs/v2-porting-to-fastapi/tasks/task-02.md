**Task 2: Core Logic Adaptation**

**Project Context**
This project is a web application designed to translate SRT (SubRip Text) subtitle files from one language to another using Google's Generative AI (Gemini). The core workflow involves:
1.  Receiving an SRT file upload.
2.  Parsing the SRT file into timed text blocks, grouped into chunks.
3.  Detecting the overall context of the subtitles using the initial chunk(s).
4.  Translating each chunk of subtitle blocks concurrently, using the detected context and target language.
5.  Reassembling the translated blocks back into a valid SRT format.
This task focuses on adapting the existing synchronous or partially asynchronous core logic functions to fully embrace asynchronous operations where I/O is involved, and ensuring they integrate correctly with a dependency injection pattern typical in frameworks like FastAPI.

**Prerequisites**
-   The necessary project dependencies, including `google-generativeai`, `tenacity`, `srt`, and `aiofiles`, should be installed in the environment.
-   Pydantic models for data representation (specifically `SubtitleBlock`, likely found in `src/translator/models.py`) and application configuration (`Settings`, likely found in `src/config.py` and inheriting from Pydantic's `BaseSettings`) are assumed to be defined or available from a previous task.
-   An understanding that the application configuration (`Settings` instance) and the initialized Gemini AI client (`genai.Client` instance) will be provided to functions via parameters, managed by an external dependency injection mechanism (to be set up in the web framework layer).

**Subtask 1: Review Gemini Client Helper**
-   Locate the module `src/translator/gemini_helper.py`.
-   Review the function responsible for initializing the Gemini client (e.g., `init_genai_client`).
-   Ensure this function accepts the application configuration (the `Settings` object from `src/config.py`) and uses the API key from it to return an initialized `genai.Client` instance.
-   This initialization function itself typically remains synchronous. The client instance it creates will be managed and injected elsewhere.

**Subtask 2: Adapt Context Detector**
-   Locate the module `src/translator/context_detector.py`.
-   Identify the primary function for context detection (signature likely similar to `detect_context(sub: List[List[SubtitleBlock]], speed_mode: str, genai_client: Optional[genai.client.Client], config: Settings) -> str`).
-   Modify this function definition to use `async def`.
-   Update the function signature to require the `genai.Client` instance and the application `Settings` instance as explicit, non-optional arguments.
-   Ensure that any calls made using the `genai_client` object to the Gemini API within this function are performed using `await`.
-   Verify that the existing retry logic (e.g., using a `tenacity` decorator) correctly wraps the `await`-ed API call.

**Subtask 3: Adapt Chunk Translator**
-   Locate the module `src/translator/chunk_translator.py`.
-   Identify the main orchestration function (signature likely similar to `translate_all_chunks(context: str, sub: List[List[SubtitleBlock]], target_lang: str, speed_mode: str, genai_client: Optional[genai.client.Client], config: Settings) -> None`) and the helper function for translating single chunks (signature likely similar to `_translate_single_chunk(..., genai_client: Optional[genai.client.Client], config: Settings) -> None`).
-   Ensure both functions are defined using `async def`.
-   Update their signatures to require the `genai.Client` instance and the application `Settings` instance as explicit, non-optional arguments.
-   Verify that API calls within `_translate_single_chunk` use the `genai_client.aio` interface (or equivalent async method) and are performed using `await`.
-   Confirm that the retry logic correctly wraps these `await`-ed calls.
-   Ensure the concurrency mechanism in `translate_all_chunks` (e.g., `asyncio.TaskGroup`) remains appropriate for managing the async `_translate_single_chunk` tasks.

**Subtask 4: Adapt Parser for Async File Handling**
-   Locate the module `src/translator/parser.py`.
-   Identify the SRT parsing function (signature likely similar to `parse_srt(file_path: str, chunk_max_blocks: int) -> List[List[SubtitleBlock]]`).
-   This function's primary role is parsing content from a file path using the `srt` library. If the `srt` library itself does not offer asynchronous file reading, this function (`parse_srt`) may remain internally synchronous.
-   Confirm that its signature accepts a file path string. The responsibility for asynchronously writing the uploaded file content (received as `UploadFile` in the web layer) to this temporary file path using `aiofiles` lies with the *calling code* (the route handler, to be implemented later), not within `parse_srt` itself.
-   Ensure the function retrieves necessary parameters like `chunk_max_blocks` via its arguments (the caller will extract this from the `Settings` object).

**Subtask 5: Review Reassembler**
-   Locate the module `src/translator/reassembler.py`.
-   Identify the function responsible for reassembling the translated chunks into SRT format (signature likely similar to `reassemble_srt(sub: List[List[SubtitleBlock]]) -> bytes`).
-   Review its implementation. This function typically involves synchronous, CPU-bound operations (string formatting, joining data). It should not require conversion to `async def`. No changes related to async adaptation are expected here.