# Review Notes: Error Handling & Resilience

**Files Reviewed:**
*   `src/main.py`
*   `src/routers/translate.py`
*   `src/translator/exceptions.py`
*   `src/translator/chunk_translator.py`
*   `src/core/errors.py`

## Observations & Analysis

1.  **Exception Hierarchy & Handling:**
    *   **Good:** Specific exceptions defined in `translator.exceptions.py` allow for targeted handling.
    *   **Good:** `main.py` uses `@app.exception_handler` to provide global handlers for custom translator exceptions, `RetryError`, `HTTPException`, and generic `Exception`. This ensures that most errors result in a standardized JSON response.
    *   **Observation:** `routers/translate.py` explicitly catches and re-raises several translator exceptions (`ValidationError`, `ParsingError`, etc.). While this might be for specific logging within the route, it appears redundant given the global handlers in `main.py` that already catch these same exceptions.
    *   **Good:** `core/errors.py` provides a simple, standardized way to format error responses.

2.  **Retry Logic (`tenacity` in `chunk_translator.py`):**
    *   **Good:** `tenacity` is used for retrying individual chunk translations (`_translate_single_chunk`) via the `configurable_retry` decorator.
    *   **Good:** Retry attempts (`RETRY_MAX_ATTEMPTS`) and wait periods are configurable.
    *   **Potential Issue:** The retry logic triggers on `retry=retry_if_exception_type(Exception)`. This means *any* exception during the chunk translation (including potentially non-recoverable ones like programming errors or `ValidationError`) will trigger a retry. It might be better to retry only on specific, transient errors (e.g., network issues, API rate limits, specific `google.api_core.exceptions`). The current Gemini client might raise specific exceptions that could be targeted here.
    *   **Observation:** The `@configurable_retry` decorator attempts to extract `settings` and `chunk_index` from `kwargs` or `args`. This logic seems complex and potentially fragile if the signature of the wrapped function changes. Passing these explicitly might be clearer.
    *   **Good:** `translate_all_chunks` uses `asyncio.gather(..., return_exceptions=True)` correctly to handle multiple concurrent tasks and aggregates failures into a single `ChunkTranslationError` if any chunk fails permanently.

3.  **Error Reporting:**
    *   **Good:** Global handlers log errors before returning responses.
    *   **Potential Issue:** Generic `Exception` handlers in `main.py` and `routers/translate.py` return `500 Internal Server Error` with potentially generic messages ("An unexpected internal server error occurred.", or `str(e)`). While sensitive details shouldn't be leaked, logging the full traceback server-side is crucial (which seems to be happening), but providing a unique error ID to the user could help correlate user reports with server logs.
    *   **Good:** `ChunkTranslationError` raised by `translate_all_chunks` includes details about which chunks failed.

4.  **Background Task Failures (`routers/translate.py`):**
    *   **Potential Issue:** Temporary file cleanup (`os.unlink`, `os.rmdir`) is scheduled using `BackgroundTasks`. If the main request processing fails *before* the cleanup tasks are scheduled (e.g., during `file.read()` or `parse_srt`), the temporary files might be left behind. Using a `try...finally` block or an `async context manager` within the `translate_srt` function could ensure cleanup happens more reliably.
    *   **Observation:** Failures *within* the background cleanup tasks themselves are not explicitly handled or logged, although FastAPI might log them by default.

## Questions

*   Is the explicit catching and re-raising of exceptions in `routers/translate.py` intentional for specific route-level logging/actions, or is it leftover code that could be simplified by relying solely on the global handlers?
*   What specific exceptions does the `genai_client.aio.models.generate_content` call typically raise on failure (e.g., rate limits, network errors, invalid requests)? Should the retry logic target these specific exceptions instead of `Exception`?
*   Is leaving temporary files behind on early request failure (before background task scheduling) an acceptable risk, or should more robust cleanup (e.g., `try...finally`) be implemented?

## Suggestions

1.  **Simplify Router Exception Handling:** Consider removing the explicit `try...except` blocks for translator exceptions in `routers/translate.py` if they aren't adding value beyond what the global handlers in `main.py` provide. Rely on the global handlers for consistent error responses.
2.  **Refine Retry Logic:** Modify the `configurable_retry` decorator in `chunk_translator.py` to retry only on specific, potentially transient exceptions expected from the Gemini API calls (e.g., `google.api_core.exceptions.ServiceUnavailable`, `google.api_core.exceptions.DeadlineExceeded`, `google.api_core.exceptions.ResourceExhausted`) instead of generic `Exception`.
3.  **Improve Decorator Argument Handling:** Pass `settings` and `chunk_index` explicitly to the `_translate_single_chunk` function within the retry logic instead of relying on introspection within the decorator.
4.  **Enhance Resource Cleanup:** Implement more robust temporary file cleanup in `routers/translate.py` using a `try...finally` block to ensure `os.unlink` and `os.rmdir` are called even if errors occur before the background tasks are scheduled.
5.  **(Optional) Unique Error IDs:** Consider generating a unique ID for each request or significant error, logging it server-side, and including it in the 500 error responses. This helps correlate user-reported issues with specific server logs. 