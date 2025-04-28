# Task 4: Implement Dependency Injection

## Project Context
This project is a web application built with FastAPI for translating subtitle files (`.srt`) using an external AI service (specifically Google Gemini, though potentially others or a mock mode). The core translation logic resides in a `translator` package. Configuration is loaded from environment variables or a `.env` file, and an AI client instance (`genai.Client`) is conditionally initialized based on the configuration.

The goal of this task is to refactor the application to use FastAPI's dependency injection system (`Depends`) for managing access to the application configuration and the AI client instance within request handlers, instead of relying on global variables or manually passing them.

## Prerequisites
- A working FastAPI application structure exists in the `src/` directory, with the main application instance likely in `src/main.py`.
- The application successfully handles subtitle translation requests via a `POST /translate` endpoint and serves a frontend via `GET /`.
- Configuration loading logic exists, likely involving a `load_config` function in `src/config_loader.py` which returns a `Config` object (check `src/translator/models.py` for the `Config` class definition: `ai_api_key: str`, `target_languages: List[str]`, `chunk_max_blocks: int`, `retry_max_attempts: int`, `log_level: str`, `ai_provider: str`, `fast_model: str`, `normal_model: str`).
- AI client initialization logic exists, likely involving an `init_genai_client` function in `src/translator/gemini_helper.py` that takes the `Config` object and returns a `genai.client.Client` instance (check the file for exact signature and return type).
- Familiarity with FastAPI's `Depends` mechanism is assumed.

## Subtask 1: Create and Use Configuration Dependency
1.  Define a new synchronous dependency provider function (e.g., `get_config`). Place this function either directly in `src/main.py` or consider creating a dedicated `src/dependencies.py` module.
2.  This function should be responsible for loading the application configuration. It will likely call the existing `load_config` function found in `src/config_loader.py`. Ensure it returns the `Config` object as defined in `src/translator/models.py`.
3.  Implement caching for the configuration within this dependency function so that `load_config` is only called once during the application's lifecycle, not on every request.
4.  Identify all route handlers in `src/main.py` (and potentially other modules if routers are already in use) that currently access the application configuration directly (e.g., via a module-level variable loaded at startup).
5.  Modify these route handlers to receive the `Config` object by adding a parameter annotated with `Depends(get_config)`.
6.  Remove the previous mechanism of accessing the configuration within these routes (e.g., remove reliance on a global `config` variable loaded at startup within the route's scope).

## Subtask 2: Create and Use AI Client Dependency
1.  Define a second synchronous dependency provider function (e.g., `get_genai_client`). Place it alongside the `get_config` function.
2.  This function must depend on the configuration object. It should declare a parameter to receive the `Config` object using `Depends(get_config)`.
3.  Move the logic currently responsible for conditionally initializing the AI client (likely found at the module level in `src/main.py`) into this new function. This logic should:
    *   Check the `ai_provider` attribute of the injected `Config` object.
    *   If the provider matches the one requiring an external client (e.g., "google-gemini"), call the `init_genai_client` function found in `src/translator/gemini_helper.py`, passing the required configuration details (like the API key from the `Config` object). Check `gemini_helper.py` for the exact signature and expected arguments.
    *   Handle potential initialization errors gracefully (e.g., logging them).
    *   Return the initialized client instance (e.g., `genai.client.Client`) or `None` if initialization is not applicable for the configured provider or if it fails.
4.  Implement caching for the client instance (or `None`) within this dependency function, ensuring the initialization logic runs only once.
5.  Identify the route handler(s) that require the AI client (primarily the `/translate` endpoint in `src/main.py`).
6.  Modify these route handlers to receive the AI client instance (or `None`) by adding a parameter annotated with `Depends(get_genai_client)`.
7.  Remove the previous mechanism used by the route handler(s) to access the client instance (e.g., remove reliance on a global `genai_client` variable).
8.  Ensure the route handler logic still correctly checks if the received client instance is not `None` before attempting to use it, especially when the requested `speed_mode` is not "mock". The route should still raise appropriate HTTP errors (e.g., 503 Service Unavailable) if a required client is not available.

## Verification
Create a manual verification script, for example `tests/manual/verify_dependency_injection.py`. This script should:

1. Read the current environment settings from the `.env` file (no need to modify them).
2. Start the FastAPI application using `uvicorn` with the `--app-dir ./src` flag.
3. Use an HTTP client library (like `requests` or `httpx`) to send `POST` requests to the `/translate` endpoint with a sample `.srt` file.
4. Test both translation modes with your current environment configuration:
   * Send a request with `speed_mode="fast"` - This will verify if your AI client dependency is correctly injected and working
   * Send a request with `speed_mode="mock"` - This should work regardless of AI provider configuration
5. Log the responses and provide a summary of the results.

This verification approach lets you confirm that the dependency injection system is working correctly with your actual configuration. If the mock mode works but the fast mode fails with an appropriate error (when using an unsupported provider or invalid API key), that's expected behavior and confirms correct dependency injection.

Note: You don't need to test every possible combination of providers and modes. The key is to verify that your application correctly handles the dependency injection based on the configuration.