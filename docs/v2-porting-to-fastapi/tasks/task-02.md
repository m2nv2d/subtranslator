## Task 2: Core Logic Adaptation (Async Focus)

**Project Context**
Following the setup of configuration and Pydantic models (Task 1), this task focuses on adapting the core subtitle processing logic found within the `src/translator/` directory. The primary goals are to ensure functions performing I/O (like API calls) are asynchronous (`async def`), to establish a clear pattern for managing and accessing the external Generative AI client instance using FastAPI's dependency injection principles, and to prepare for asynchronous file handling in the web layer.

**Prerequisites**
Ensure you have access to and familiarity with the following Python libraries and concepts:
*   Python's `asyncio` and `async`/`await` syntax.
*   The concept of Dependency Injection, particularly how FastAPI uses it.
*   The `google-generativeai` library (or the specific SDK being used for Gemini).
*   The `tenacity` library (for retry logic).
*   The `aiofiles` library (for asynchronous file operations).
*   The `srt` library (for subtitle parsing/composition).
*   Access to the application state mechanism in FastAPI (e.g., `app.state` or `request.app.state`).

You will need the code from Task 1 completed (`src/config.py`, `src/dependencies.py`, `src/translator/models.py`).

**Subtask 1: Manage Gemini Client Lifecycle and Dependency**
The application requires a single, shared instance of the Gemini client (e.g., `genai.Client` or `genai.GenerativeModel`) to interact with the AI service. This instance should be initialized once when the application starts and made available to API endpoints that need it.
1.  Locate the client initialization logic, likely within `src/translator/gemini_helper.py` (e.g., a function like `init_genai_client`).
2.  Modify `src/main.py`. Implement an `async` [lifespan context manager](https://fastapi.tiangolo.com/advanced/events/) for the FastAPI application instance (`app`).
3.  Within the `startup` part of the lifespan manager (before the `yield`):
    *   Instantiate the `Settings` class from `src/config.py` to get configuration values.
    *   Call the client initialization function (from `gemini_helper`) using the necessary configuration (like the API key from `Settings`).
    *   Store the successfully initialized client instance in the application state (e.g., `app.state.genai_client = client_instance`).
    *   Include error handling (e.g., `try...except`) around the initialization. If it fails, log a critical error and consider raising an exception to prevent the application from starting in a non-functional state.
4.  Within the `shutdown` part of the lifespan manager (after the `yield`), add any necessary cleanup code for the client, if applicable (often not required, but good practice to consider).
5.  Go to `src/dependencies.py`. Define a simple synchronous dependency function, named `get_gemini_client`, that accepts `request: Request` as an argument. This function should retrieve the pre-initialized client instance from the application state (`request.app.state.genai_client`) and return it.

**Subtask 2: Adapt Service Functions for Async and Dependencies**
Review and update the core service functions to align with async practices and dependency injection.
1.  Examine `src/translator/context_detector.py`. Ensure the main function responsible for detecting context (e.g., `detect_context`) is defined using `async def`, as it will involve network I/O when communicating with the Gemini API. Update its function signature to explicitly accept the Gemini client instance and the `Settings` instance as parameters. Remove any code that attempts to initialize the client internally; it should rely on the instance passed to it.
2.  Examine `src/translator/chunk_translator.py`. Verify that the functions responsible for orchestrating chunk translation (e.g., `translate_all_chunks`) and translating individual chunks (e.g., `_translate_single_chunk`) are already defined using `async def`. Update their function signatures to explicitly accept the Gemini client instance and the `Settings` instance as parameters. Ensure any existing `tenacity` retry decorators are compatible with async functions (they generally are) and remain in place. These functions should use the passed client instance for API calls.
3.  Ensure all functions modified above now import necessary types like the client type from the `google.generativeai` library and the `Settings` type from `src.config` for type hinting in their signatures.

**Subtask 3: Plan for Async File Handling in Parser**
Review `src/translator/parser.py`. This module is responsible for parsing the `.srt` file content.
1.  Identify the main parsing function (e.g., `parse_srt`). Note that it likely accepts a file path as input and uses the synchronous `srt` library internally.
2.  Recognize that while the *parsing logic itself* might remain synchronous (due to the underlying `srt` library), the process of *reading the uploaded file data* and *saving it to a temporary location* will be handled asynchronously in the API route handler (in `src/main.py`, to be implemented in Phase 3) using `aiofiles`.
3.  Therefore, **no changes are strictly required within `src/translator/parser.py` for this specific subtask**. The existing function signature (accepting a file path) is likely sufficient. The key takeaway is understanding that the asynchronous file read/write operations will happen *before* this synchronous parsing function is called by the route handler.

**Subtask 4: Verify Reassembler Synchronicity**
Review `src/translator/reassembler.py`. This module combines translated subtitle blocks back into the `.srt` format.
1.  Identify the main reassembly function (e.g., `reassemble_srt`). This function likely performs CPU-bound operations (string formatting, list iteration) using the `srt` library.
2.  Confirm that this function does not perform any I/O and therefore does not need to be `async def`. Its signature and implementation likely remain unchanged.

**Debugging**
Create a Python script named `tests/manual/test_core_logic_async.py`. This script should serve as a basic check for the adapted async functions and dependency passing (without requiring a running FastAPI server):
1.  Import `asyncio`.
2.  Import the `Settings` class from `src.config` and instantiate it (requires a valid `.env`).
3.  Import the client initialization function from `src.translator.gemini_helper` and manually initialize a client instance using the settings.
4.  Import the relevant async functions (e.g., `detect_context`, `translate_all_chunks`) from `src.translator.context_detector` and `src.translator.chunk_translator`.
5.  Import the `SubtitleBlock` model from `src.translator.models`.
6.  Create some sample `SubtitleBlock` data structured as required by the functions (list of lists of blocks).
7.  Use `asyncio.run()` to execute a top-level `async def main():` function.
8.  Inside `main()`, `await` calls to your adapted `detect_context` and `translate_all_chunks` functions, passing the manually created `Settings` instance, the manually initialized client instance, and the mock subtitle data.
9.  Add basic print statements or assertions to observe output or check for exceptions. (Note: Actual API calls will be made if not mocked. Consider adding simple mock logic or using "mock" `speed_mode` if available to avoid hitting the real API during this basic check).

Running this script helps verify that the async function signatures are correct, dependencies can be passed, and the basic async flow executes without immediate errors.