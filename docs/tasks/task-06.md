**Task 6: Subtitle Chunk Translation**

**Project Context**

This module, `chunk_translator`, is responsible for translating the text content within chunks of subtitles. It receives multiple chunks (each being a list of subtitle blocks) and needs to process them concurrently for efficiency. It uses provided context, a target language specification, and configuration settings. Your primary task is to implement the asynchronous orchestration structure using `asyncio` and a "mock" translation mode. The mock mode will simply copy the original text to the translated field without calling any external services, simulating the translation process.

**Prerequisites**

*   Ensure `asyncio` (part of standard Python) and `tenacity` are available in your environment. Check the project's dependency setup.
*   Familiarize yourself with the necessary definitions from other project modules:
    *   `src/models.py`: Check this file for the definitions of `SubtitleBlock` (which has `content` and `translated_content` attributes) and `Config` (which includes `retry_max_attempts`).
    *   `src/exceptions.py`: Check this file for the definition of `ChunkTranslationError`.

**Subtask 1: Create File Structure and Imports**

Create the file `src/chunk_translator.py`. Add the required imports at the beginning: `asyncio`, `tenacity`, `List`, `Any` from `typing`, `SubtitleBlock`, `Config` from `src.models`, and `ChunkTranslationError` from `src.exceptions`.

**Subtask 2: Implement Orchestration Function `translate_all_chunks`**

Define an `async` function responsible for managing the concurrent translation of all chunks. It must have the following exact signature:

```python
async def translate_all_chunks(
    context: str,
    sub: List[List[SubtitleBlock]],
    target_lang: str,
    speed_mode: str,
    genai_client: genai.client.Client, # Optional
    config: models.Config
) -> None:
```

*   Inside this function, create a list of tasks to be run concurrently. Iterate through the input `sub` (list of chunks), and for each `chunk` (and its index), create an `asyncio` task that calls the internal helper function `_translate_single_chunk`.
*   Ensure you pass all the necessary arguments (`context`, the `chunk_index`, the `chunk` itself, `target_lang`, `speed_mode`, `genai_client`, and `config`) to `_translate_single_chunk` when creating each task.
*   Use `asyncio.gather(*tasks)` to execute all the created tasks concurrently and wait for them all to complete.
*   Include basic error handling: wrap the `asyncio.gather` call in a `try...except` block. If any exception occurs during the execution of the tasks (which `gather` will propagate), catch it and raise a `ChunkTranslationError`, possibly including the original exception as the cause.

**Subtask 3: Implement Helper Function `_translate_single_chunk` (Mock & Placeholder)**

Define an internal `async` helper function to handle the logic for a single chunk. Apply the `tenacity.retry` decorator to this function *before* its definition. Configure the decorator to use the `retry_max_attempts` value from the `config` object (e.g., `stop=tenacity.stop_after_attempt(config.retry_max_attempts)`). For now, you can configure it to retry on `Exception`, but note that this should later be refined to retry only on specific, expected API-related exceptions.

The function must have the following exact signature:

```python
@tenacity.retry(...) # Add retry configuration here
async def _translate_single_chunk(
    context: str,
    chunk_index: int,
    chunk: List[SubtitleBlock],
    target_lang: str,
    speed_mode: str,
    genai_client: genai.client.Client, # Optional
    config: models.Config # Used for retry config
) -> None:
```

*   **Mock Logic:** Check if `speed_mode == "mock"`. If true, implement the mock translation:
    *   Iterate through each `SubtitleBlock` object within the `chunk` list.
    *   For each block, assign its `content` attribute to its `translated_content` attribute.
    *   Include a brief `await asyncio.sleep(0.1)` within the loop or just once in the mock path to simulate processing time.

*   **Real Logic Placeholder:** If `speed_mode` is *not* `"mock"`, insert a placeholder.

**Subtask 4: Create Manual Test Script**

Create a simple Python script inside the `tests/manual/` directory (e.g., `test_chunk_translator.py`). This script should serve as a basic way to run your `translate_all_chunks` function manually.

It has 2 arguments: a srt file and `speed_mode`. It call the appropriate branch of the `translate_all_chunks` function and print the result (first few blocks). If needed, it invoked gemini_helper.py to initialize the client and pass it to the `translate_all_chunks` function.