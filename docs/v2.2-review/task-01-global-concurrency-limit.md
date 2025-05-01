**Task 01: Implement Global Concurrency Limit for Chunk Translation**

**Project Context**

This project is a FastAPI web application designed to translate SubRip Text (SRT) subtitle files. It parses the SRT file into blocks, potentially chunks these blocks, detects the overall context, translates the chunks concurrently using an external AI service (like Google Gemini), and finally reassembles the translated blocks into a new SRT file.

The core translation logic for individual chunks resides in the `_translate_single_chunk` async function within `src/translator/chunk_translator.py`. Currently, these translation tasks can run with unlimited concurrency within the `asyncio` event loop, potentially overwhelming the external AI service or consuming excessive resources.

The goal of this task is to introduce a global semaphore to limit the number of `_translate_single_chunk` tasks running concurrently across the entire application instance, regardless of how many user requests are being processed.

Refer to the technical design document provided previously for details on existing module structure, function signatures (like `parse_srt`, `detect_context`, `translate_all_chunks`, `_translate_single_chunk`, `reassemble_srt`), data models (`SubtitleBlock`), configuration (`Settings`), and dependency injection patterns. Assume the project follows the file structure outlined in that document.

**Prerequisites**

*   Familiarity with Python's `asyncio` library, specifically `asyncio.Semaphore`.
*   Understanding of FastAPI's dependency injection system (`Depends`).
*   Access to the project codebase, particularly the files mentioned in the subtasks below.
*   Ability to install project dependencies using the package manager specified in the project setup (e.g., `pyproject.toml`).

**Subtask 1: Add Concurrency Limit Configuration**

Modify the `Settings` class located in `src/core/config.py`. Introduce a new configuration setting, named appropriately (e.g., `MAX_CONCURRENT_TRANSLATIONS`), to define the maximum number of concurrent translation tasks allowed application-wide. This setting should:
*   Be loaded from environment variables (like other settings in this class).
*   Have a sensible default integer value (e.g., 10).
*   Be validated using Pydantic to ensure it's a positive integer.

**Subtask 2: Create and Provide Shared Semaphore Instance**

In `src/core/dependencies.py`, implement the creation of a single `asyncio.Semaphore` instance for the entire application.
*   Initialize this semaphore with the limit defined by the `MAX_CONCURRENT_TRANSLATIONS` setting retrieved from the application `Settings`.
*   Create a new FastAPI dependency provider function (e.g., `get_translation_semaphore`). This function should return the *same* semaphore instance every time it's called within the application's lifetime (hint: consider caching).

**Subtask 3: Inject Semaphore into Translation Route**

Locate the main translation endpoint handler function within `src/routers/translate.py` (responsible for handling `POST /translate` requests).
*   Modify this function's signature to accept the shared semaphore instance as a dependency, using FastAPI's `Depends` mechanism with the provider function created in Subtask 2.

**Subtask 4: Pass Semaphore to Chunk Translation Orchestrator**

Within the `POST /translate` route handler function (modified in Subtask 3), ensure the obtained semaphore instance is passed as an argument when calling the `translate_all_chunks` function.
*   Consequently, update the function signature of `translate_all_chunks` defined in `src/translator/chunk_translator.py` to accept this new `asyncio.Semaphore` parameter.

**Subtask 5: Pass Semaphore to Individual Chunk Translator Task**

Modify the `translate_all_chunks` function in `src/translator/chunk_translator.py`.
*   When this function creates and schedules the individual `_translate_single_chunk` tasks (e.g., using `asyncio.gather` or `asyncio.TaskGroup`), ensure that the semaphore instance (received as a parameter in Subtask 4) is passed as an argument to each `_translate_single_chunk` call.
*   Update the function signature of `_translate_single_chunk` in the same file (`src/translator/chunk_translator.py`) to accept this new `asyncio.Semaphore` parameter.

**Subtask 6: Apply Semaphore Lock within Chunk Translator**

Modify the `_translate_single_chunk` function in `src/translator/chunk_translator.py`.
*   Use the `asyncio.Semaphore` instance passed into this function (as per Subtask 5) to control access to the core translation logic.
*   Wrap the section of code that performs the actual translation (either the mock translation or the call to the external AI service) within an `async with semaphore:` block. This ensures that a semaphore slot is acquired before proceeding with the translation and released automatically afterward, effectively limiting concurrency.