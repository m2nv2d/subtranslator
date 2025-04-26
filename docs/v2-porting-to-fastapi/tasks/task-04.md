## Task 4: Error Handling

**Project Context**
This task focuses on implementing robust and consistent error handling for the FastAPI application. Instead of letting exceptions propagate uncaught or relying solely on default FastAPI error responses, we will define specific handlers for custom application exceptions and common issues like API call failures after retries. This ensures that the API provides informative and appropriate error responses to the client (the frontend JavaScript).

**Prerequisites**
*   A working FastAPI application (`src/main.py`) with endpoints defined from Task 3.
*   Completed code from previous tasks, especially the custom exceptions defined in `src/translator/exceptions.py` (`ValidationError`, `ParsingError`, `ContextDetectionError`, `ChunkTranslationError`, etc.) and the core translation logic that might raise these exceptions.
*   Familiarity with FastAPI's exception handling mechanism (`@app.exception_handler`) and HTTP status codes.
*   Access to the `tenacity` library (as `RetryError` needs to be handled).
*   Python's standard `logging` module.
*   Optional: Pydantic for defining a standardized error response model.

**Subtask 1: Implement Handlers for Custom Application Exceptions**
In your main application file (`src/main.py`), define exception handler functions for the custom exceptions defined in `src/translator/exceptions.py`. Use the `@app.exception_handler(YourCustomException)` decorator for each.
1.  **ValidationError:** Create a handler for `translator.exceptions.ValidationError`. This handler should return a JSON response (using `fastapi.responses.JSONResponse`) with an HTTP status code of `400` (Bad Request). The response body should be a JSON object, e.g., `{"error": str(exception)}`.
2.  **ParsingError:** Create a handler for `translator.exceptions.ParsingError`. Return a `JSONResponse` with status code `422` (Unprocessable Entity) and a body like `{"error": str(exception)}`.
3.  **ContextDetectionError:** Create a handler for `translator.exceptions.ContextDetectionError`. Return a `JSONResponse` with status code `500` (Internal Server Error) and a body like `{"error": f"Failed to detect context: {exception}"}`.
4.  **ChunkTranslationError:** Create a handler for `translator.exceptions.ChunkTranslationError`. Return a `JSONResponse` with status code `500` (Internal Server Error) and a body like `{"error": f"Failed during translation: {exception}"}`.
Ensure you import the necessary exception types from `src.translator.exceptions` and `JSONResponse` from `fastapi.responses`. The handler functions should accept `request: Request` and `exception: YourCustomException` as arguments.

**Subtask 2: Implement Handler for API Retry Errors**
External API calls (to Gemini) are wrapped with `tenacity`. If all retries fail, `tenacity` raises a `RetryError`. Create a specific handler for this.
1.  Import `RetryError` from `tenacity`.
2.  Define an exception handler using `@app.exception_handler(RetryError)`.
3.  This handler should return a `JSONResponse` with status code `504` (Gateway Timeout), indicating that an upstream service (the LLM API) failed. The response body should be informative, e.g., `{"error": f"LLM API failed after multiple retries: {exception}"}`.

**Subtask 3: Implement Generic Fallback Exception Handler**
Add a catch-all handler for any unexpected errors that weren't caught by the more specific handlers.
1.  Define an exception handler using `@app.exception_handler(Exception)`.
2.  Inside this handler, **log the exception** using the standard `logging` module (e.g., `logging.exception("Unhandled error occurred")`) to capture the full traceback on the server side for debugging.
3.  Return a generic `JSONResponse` with status code `500` (Internal Server Error). The response body should *not* include the raw exception details to avoid leaking potentially sensitive information. Use a generic message, e.g., `{"error": "An unexpected internal error occurred"}`.

**Subtask 4: (Optional) Standardize Error Response Format**
To ensure consistency, you can define a simple Pydantic model for error responses.
1.  Define a Pydantic `BaseModel` (perhaps in `src/models.py` or a dedicated `src/schemas.py`), e.g., `class ErrorDetail(BaseModel): error: str`.
2.  Modify all the exception handlers created above (Subtasks 1, 2, 3) to return instances of this `ErrorDetail` model within the `JSONResponse` content (e.g., `content=ErrorDetail(error=message).model_dump()`). This enforces a consistent `{"error": "..."}` structure.

**Debugging**
1.  Run the FastAPI application using Uvicorn.
2.  **Test ValidationError:** Attempt to use the `/translate` endpoint via the web UI or `curl` but provide invalid input (e.g., select a language not in the configured list if you implemented that check in Task 3, or manually trigger a `ValidationError` if needed for testing). Verify you receive a 400 status code and the expected JSON error body.
3.  **Test ParsingError:** Upload a file that is *not* a valid SRT file, or an empty file, or a severely malformed SRT file to the `/translate` endpoint. Verify you receive a 422 status code and the corresponding JSON error.
4.  **Test RetryError/API Failure:** This is harder to test reliably without mocking. If you have a "mock" `speed_mode` that simulates errors, use that. Alternatively, temporarily configure an invalid API key in your `.env` file and restart the app. Make a translation request. This should cause the API calls within `context_detector` or `chunk_translator` to fail repeatedly, eventually triggering the `RetryError` handler. Verify the 504 status code and JSON response. (Remember to restore the valid API key afterwards).
5.  **Test Generic Handler:** Introduce a deliberate bug (e.g., a `NameError` or `TypeError`) within the `/translate` route logic (outside specific `try...except` blocks for custom errors) and make a request. Verify you receive a 500 status code and the generic JSON error message. Check the server logs to confirm the full traceback was logged.