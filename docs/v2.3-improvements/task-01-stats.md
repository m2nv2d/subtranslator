# Task 1: Implement In-Memory Application Statistics

## Project Context
This is a simple, personal web application built with FastAPI for translating subtitle files (SRT) using a Generative AI model (specifically Google Gemini). Users upload an SRT file, select a target language and speed mode, and the application returns the translated file. The project structure includes modules for core utilities, routers, and translation logic, organized within a `src` directory. The main application instance is in `src/main.py`, core settings and dependencies are in `src/core/`, translation logic is in `src/translator/`, and routes are in `src/routers/`.

## Prerequisites
Review the technical design document provided previously to understand the existing file structure, modules, and core components, especially:
- `src/core/dependencies.py`
- `src/routers/translate.py`
- `src/translator/chunk_translator.py`
- `src/translator/parser.py`

## Subtask 1: Define Statistics Structures and Store

Create a new Python file `src/core/stats.py`.

Inside this file, define the data structures needed to hold statistics:
- A structure (like a class or Pydantic model) named `FileStats` to store statistics for a single file translation request. It must contain fields for: `request_id` (string), `filename` (string), `file_size_bytes` (integer), `speed_mode` (string), `total_blocks` (integer), `total_chunks` (integer), `translation_failed_attempts` (integer), `chunks_with_failures` (integer), `start_time` (datetime), `end_time` (optional datetime), and `status` (string, e.g., "processing", "completed", "failed").
- A structure (like a class or Pydantic model) named `TotalStats` to accumulate overall application statistics. It must contain fields for: `total_files_processed` (integer), `total_blocks_processed` (integer), `total_chunks_processed` (integer), `total_translation_failed_attempts` (integer), `total_chunks_with_failures` (integer), and `app_start_time` (datetime).

Define a class named `AppStatsStore`. This class will be the central in-memory store. It should have instance attributes to hold:
- An integer counter to generate unique request IDs.
- A dictionary to store `FileStats` instances, using the request ID as the key.
- A single instance of the `TotalStats` structure.
- An `asyncio.Lock` instance to protect concurrent access to the statistics data.

Implement the following asynchronous methods within the `AppStatsStore` class, ensuring they correctly use the `asyncio.Lock` to prevent race conditions:
- `async create_file_entry(filename: str, size: int, speed_mode: str) -> str`: Generates a unique request ID, initializes a `FileStats` entry with initial values (counters at 0, status "processing", `start_time` as current time), adds it to the internal dictionary, increments the `total_files_processed` counter in `TotalStats`, and returns the generated `request_id`.
- `async update_parsing_stats(request_id: str, num_chunks: int, total_blocks: int)`: Locates the `FileStats` entry for the given `request_id`, updates its `total_chunks` and `total_blocks` fields, and adds these counts to the corresponding fields in `TotalStats`.
- `async update_translation_stats(request_id: str, total_failed_attempts: int, chunks_with_failures: int)`: Locates the `FileStats` entry for the given `request_id`, updates its `translation_failed_attempts` and `chunks_with_failures` fields, and adds these counts to the corresponding fields in `TotalStats`.
- `async complete_request(request_id: str, status: str)`: Locates the `FileStats` entry for the given `request_id`, sets its `end_time` to the current time and its `status` to the provided value ("completed" or "failed").
- `async get_stats()`: Returns a snapshot of the current `TotalStats` and the dictionary of `FileStats`. Acquire the lock briefly to copy the data before returning to ensure consistency.

## Subtask 2: Add Stats Store Dependency

Locate the file `src/core/dependencies.py`.

Add a new asynchronous dependency provider function named `get_stats_store`.
Decorate this function with `@functools.lru_cache()` to ensure only a single instance of the `AppStatsStore` is created and reused across the application lifetime.
Inside the function, initialize and return an instance of the `AppStatsStore` class defined in `src/core/stats.py`.

## Subtask 3: Integrate Stats Updates in Router

Locate the file `src/routers/translate.py`.

Review the existing `POST /translate` function handler.
Inject the `AppStatsStore` dependency into the function signature using `Depends(get_stats_store)`.

Modify the `POST /translate` handler's logic to perform the following statistics updates by calling methods on the injected `stats_store`:
- At the very beginning of the request processing, after receiving the file object and other parameters, call `stats_store.create_file_entry` using the filename, size, and speed mode. Store the returned unique `request_id`.
- After the successful execution of `parser.parse_srt`, retrieve the total number of blocks and chunks from its result (Note: the return value of `parse_srt` needs to be modified in a later subtask). Call `stats_store.update_parsing_stats` with the `request_id`, number of chunks, and total blocks.
- After the successful execution of `chunk_translator.translate_all_chunks`, retrieve the aggregated translation statistics (total failed attempts and chunks with failures) from its result (Note: the return value of `translate_all_chunks` needs to be modified in a later subtask). Call `stats_store.update_translation_stats` with the `request_id`, total failed attempts, and chunks with failures.
- Implement a `try...except...finally` block around the core translation processing logic (parsing, context detection, translation, reassembly).
- In the `finally` block, call `stats_store.complete_request` with the `request_id`. Pass `"completed"` as the status if the `try` block finished without unhandled exceptions, and `"failed"` if an exception was caught.

## Subtask 4: Modify Chunk Translator Return Value

Locate the file `src/translator/chunk_translator.py`.

Review the `async translate_all_chunks` function. It orchestrates the translation of individual chunks.
Modify the return value of the inner `async _translate_single_chunk` function. This function should return statistics about its execution, specifically the number of times it retried translation for that specific chunk and a boolean indicating if the chunk ultimately failed after exhausting retries.
Modify the `async translate_all_chunks` function. It currently uses `asyncio.TaskGroup` or similar to run `_translate_single_chunk` concurrently. Update it to collect the return values from each spawned task.
Aggregate the collected statistics from all chunk tasks: sum the retry counts from all chunks to get the total failed attempts for the entire file translation, and count how many chunks returned `True` for the "failed" indicator to get the number of chunks with failures.
Modify the `async translate_all_chunks` function's return value to return these two aggregated numbers (total failed attempts for the file, number of chunks with failures) back to its caller (the router). The function will now return `Tuple[int, int]`.

## Subtask 5: Add Stats Endpoint

Locate the file `src/routers/translate.py`. Alternatively, you could create a new router file like `src/routers/stats.py` and include it in `src/main.py`, but for a simple personal app, adding it to `translate.py` might be acceptable. Add the new route to `translate.py` for simplicity.

Add a new FastAPI `GET` endpoint at the path `/stats`.
Inject the `AppStatsStore` dependency into this function's signature.
Inside the handler function for the `/stats` endpoint, call the `stats_store.get_stats()` method.
Return the result obtained from `stats_store.get_stats()`. FastAPI will automatically serialize the dictionary/Pydantic model returned into a JSON response.

## Subtask 6: Testing and Verification

**Automated Tests:**
- Add unit tests in `tests/automated/unit/core/test_stats.py` for the `AppStatsStore` class to verify its methods correctly update and retrieve statistics while using the lock.
- Add integration tests in `tests/automated/integration/` to test the `/stats` endpoint, confirming it returns data in the expected format.
- Enhance integration tests for the `/translate` endpoint to verify that submitting a file correctly updates the statistics visible via the `/stats` endpoint, checking counts for blocks, chunks, retries (by potentially mocking the AI response to force retries or failures), and overall status.