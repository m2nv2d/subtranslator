## Task 5: Async Operations

### Project Context
The project is a web application built with FastAPI that translates Subtitle files (SRT format). It receives an SRT file via a POST request, potentially uses the Google Generative AI (Gemini) API to perform the translation based on selected speed modes ('fast', 'normal', or 'mock'), and returns the translated SRT file. This task focuses on ensuring all potentially blocking I/O operations within the asynchronous FastAPI framework are handled asynchronously to maintain application responsiveness.

### Prerequisites
-   The project uses FastAPI and Uvicorn.
-   The Google Generative AI SDK (`google-genai`) is used for LLM interactions.
-   An asynchronous file I/O library (like `aiofiles`) should be available or added as a dependency.
-   The main application logic resides in `src/main.py` and the core translation logic is within the `src/translator/` package. Relevant files include `src/translator/chunk_translator.py` and potentially `src/translator/models.py` for data structures.

### Subtask 1: Implement Async File I/O in Route Handler
Locate the `POST /translate` endpoint function within `src/main.py`. This function receives an uploaded file (`UploadFile` type). Identify the section where this file is saved to a temporary location on the filesystem. Modify this file-saving logic to use asynchronous file operations, ensuring the application's event loop is not blocked during file writing. Ensure proper handling of the temporary file/directory lifecycle (creation and cleanup, potentially considering background tasks if implemented previously).

### Subtask 2: Verify Async LLM API Calls
Examine the `_translate_single_chunk` asynchronous function located in `src/translator/chunk_translator.py`. Its signature is approximately: `async def _translate_single_chunk(system_prompt: str, chunk_index: int, chunk: List[models.SubtitleBlock], target_lang: str, speed_mode: str, genai_client: Optional[genai.client.Client], config: models.Config) -> None`. Verify that within this function, when `speed_mode` requires an actual API call ('fast' or 'normal') and a `genai_client` instance is available, the interaction with the Google Generative AI service uses the client's asynchronous interface. Specifically, confirm that the call is made using `genai_client.aio.models.generate_content` or an equivalent async method provided by the SDK, rather than a synchronous/blocking call.

### Subtask 3: Identify and Address Other Blocking Operations
Review the codebase, particularly within the async route handlers in `src/main.py` and any asynchronous functions they call within the `src/translator/` package. Identify any other operations that might block the event loop, such as synchronous network requests, lengthy computations, or blocking database interactions (if any were added). Refactor these operations to be asynchronous or delegate them to a separate thread pool if asynchronous alternatives are not readily available, ensuring the main event loop remains responsive. Based on the provided design, primary focus should be on file I/O and the LLM call.