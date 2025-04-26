# Task 4: Error Handling

## Project Context
This project is a web application built with FastAPI that translates subtitle files (`.srt`). It receives an SRT file, a target language, and a speed mode via a form POST request. It then parses the file, detects context using an LLM (like Gemini), translates text chunks using the LLM, reassembles the file, and returns the translated SRT file. The core translation logic involves asynchronous operations and external API calls managed with retries.

## Prerequisites
- A working FastAPI application instance, typically named `app`, presumably located in `src/main.py`.
- Custom exception classes defined within the project. Check `src/translator/exceptions.py` for these classes. Expect to find exceptions like `ValidationError`, `ParsingError`, `ContextDetectionError`, and `ChunkTranslationError`.
- The `tenacity` library might be used for retries, potentially raising `tenacity.RetryError`.

## Subtask 1: Handle Custom Application Exceptions
Implement FastAPI exception handlers for the custom exceptions defined in `src/translator/exceptions.py`.
- For `ValidationError`, the handler should catch this exception and return a JSON response containing an `{"error": "error message from exception"}` body with an HTTP status code of 400 (Bad Request).
- For `ParsingError`, the handler should catch this exception and return a JSON response with an `{"error": "error message from exception"}` body and an HTTP status code of 422 (Unprocessable Entity).
- For `ContextDetectionError`, the handler should catch this exception and return a JSON response with an `{"error": "Failed to detect context: error message from exception"}` body and an HTTP status code of 500 (Internal Server Error).
- For `ChunkTranslationError`, the handler should catch this exception and return a JSON response with an `{"error": "Failed during translation: error message from exception"}` body and an HTTP status code of 500 (Internal Server Error).
- Each handler will typically accept the `Request` object and the specific exception instance as arguments.

## Subtask 2: Handle Retry Errors
Implement a FastAPI exception handler specifically for `tenacity.RetryError`. This error signifies that an operation (likely an external API call) failed after all configured retry attempts.
- The handler should catch `tenacity.RetryError` and return a JSON response.
- The response body should be `{"error": "LLM API failed after multiple retries: error message from exception"}`.
- The HTTP status code should be 504 (Gateway Timeout).

## Subtask 3: Handle Generic Exceptions
Implement a fallback FastAPI exception handler for the base `Exception` class. This handler will catch any unhandled exceptions that occur during request processing.
- The handler should log the exception details for debugging purposes (ensure standard logging is configured elsewhere).
- It should return a generic JSON response, such as `{"error": "An unexpected internal error occurred"}`.
- The HTTP status code should be 500 (Internal Server Error). This handler should be defined broadly enough to catch unforeseen errors but should not prevent more specific handlers (like those for HTTPExceptions or the custom ones above) from executing first. Ensure standard FastAPI `HTTPException` handling is not overridden unless intended.