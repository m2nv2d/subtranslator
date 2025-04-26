## Task 5: Testing & Deployment Preparation

**Project Context**
With the FastAPI application endpoints implemented, error handling configured, and core logic adapted (Tasks 1-4), this final phase focuses on ensuring the application's correctness through automated testing and preparing it for execution using an ASGI server (Uvicorn).

**Prerequisites**
*   A fully functional FastAPI application located in `src/main.py` resulting from completing Tasks 1-4.
*   Python testing libraries installed: `pytest`, `pytest-asyncio`, `httpx` (used by FastAPI's `TestClient`).
*   Familiarity with writing tests using `pytest`, especially for async code.
*   Understanding of FastAPI's `TestClient` and dependency overriding mechanism.
*   Access to the application's source code, including `src/main.py`, `src/dependencies.py`, `src/config.py`, and the core logic modules in `src/translator/`.

**Subtask 1: Implement Automated Tests**
Create automated tests to verify the functionality of the FastAPI application, focusing on API endpoints and their integration with the core logic. Place these tests within the `tests/automated/` directory (e.g., in `tests/automated/integration/test_api.py`).
1.  **Setup TestClient:** Import `TestClient` from `fastapi.testclient` and instantiate it by passing your FastAPI application instance (`from src.main import app`).
2.  **Write Async Tests:** Use `pytest` and `pytest-asyncio`. Define test functions using `async def` and mark them appropriately if needed by your `pytest-asyncio` configuration (often automatic).
3.  **Test `GET /` Endpoint:** Write a test that sends a `GET` request to `/` using the `TestClient`. Assert that the response status code is `200` (OK) and that the response content type is `text/html`. Optionally, check for the presence of expected elements in the HTML, like the language selector being populated based on a known test configuration.
4.  **Test `POST /translate` (Success Case):**
    *   **Mock Dependencies:** This is crucial. Before making the request, use FastAPI's dependency overriding mechanism (`app.dependency_overrides`) within the test function or fixture to replace the actual `get_settings` and `get_gemini_client` dependencies with mock versions.
        *   The mock settings should provide predictable configuration (e.g., specific `target_languages`).
        *   The mock Gemini client should mimic the behavior of the real client's methods (e.g., `generate_content`) without making actual API calls. It should return predictable successful translation results based on the input it receives in the test.
    *   **Prepare Request Data:** Create sample valid `.srt` file content (as bytes or a temporary file) and the corresponding form data (`target_lang`, `speed_mode`).
    *   **Send Request:** Use `TestClient.post("/translate", files={"file": ...}, data={"target_lang": ..., "speed_mode": ...})`.
    *   **Assert Response:** Check for a `200` status code. Verify the `Content-Type` header is `text/srt`. Assert that the `Content-Disposition` header indicates an attachment with the expected filename format. Optionally, parse the response content and verify the translation matches what the mock client was configured to return.
    *   **Cleanup Overrides:** Remember to clear the dependency overrides after the test (e.g., using a `pytest` fixture's teardown or resetting `app.dependency_overrides = {}`).
5.  **Test `POST /translate` (Error Cases):**
    *   **Validation Errors:** Test scenarios that should trigger validation errors (e.g., missing file, missing form fields, invalid `target_lang` based on mock settings). Assert that the appropriate status code (e.g., 400, 422) and JSON error response body (matching the format defined by your handlers in Task 4) are returned.
    *   **Parsing Errors:** Test with invalid/malformed SRT file content. Assert the 422 status code and expected error response.
    *   **API Failures (Mocked):** Configure your mock Gemini client dependency to simulate failures (e.g., raise specific exceptions or return error indicators that your core logic translates into custom exceptions like `ContextDetectionError` or `ChunkTranslationError`, or simulate repeated failures to trigger `RetryError`). Assert that the corresponding error handlers are invoked and return the correct status codes (e.g., 500, 504) and JSON error bodies.

**Subtask 2: Prepare for Uvicorn Execution**
Ensure the application is ready to be run by the Uvicorn ASGI server.
1.  **Verify Entry Point:** Confirm that your main application file (`src/main.py`) contains the instantiated FastAPI application object, typically named `app`. This is the object Uvicorn needs to target.
2.  **Basic Run Command:** Formulate the basic Uvicorn command to run the application from the project's root directory: `uvicorn src.main:app`.
3.  **Development Run:** For development, use the `--reload` flag to automatically restart the server on code changes: `uvicorn src.main:app --reload`.
4.  **Production Considerations (Mention):** Note that for actual production deployment, you would typically run Uvicorn without `--reload` and potentially configure multiple worker processes (e.g., `uvicorn src.main:app --workers 4`) or run Uvicorn workers managed by a process manager like Gunicorn (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app`). You would also configure the host (`--host 0.0.0.0`) and port (`--port 80` or `443` behind a reverse proxy) appropriately and handle HTTPS termination (usually via a reverse proxy like Nginx or Caddy). These production details are beyond the scope of this task but are important next steps.

**Debugging/Verification**
1.  Execute your test suite using `pytest` in your terminal from the project root. Ensure all tests pass, including those covering success and error scenarios with mocked dependencies. Fix any failing tests.
2.  Run the application locally using the development Uvicorn command: `uvicorn src.main:app --reload`.
3.  Perform final manual tests via the browser and/or `curl` to ensure the deployed application behaves as expected, exercising both successful translations and error conditions (e.g., uploading invalid files).