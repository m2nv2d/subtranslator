# Task 1: Configuration Loading

## Project Context

This task involves creating a module responsible for loading application configuration settings from an environment file. The goal is to centralize configuration management, provide default values for optional settings, and ensure essential settings like API keys are present at startup. This module will be used by the main application to access these settings.

## Prerequisites

*   You will need the `python-dotenv` library installed in your environment to handle reading `.env` files.
*   The project structure includes a `src` directory for source code. This module should be created as `src/config_loader.py`.
*   A `.env` file is expected to exist in the project's root directory (one level above `src`).
*   You will need to interact with a data class named `Config` which defines the structure of the configuration settings. This class definition can be found in `src/models.py`. You should inspect `src/models.py` to understand the exact fields and types required by the `Config` class (specifically `gemini_api_key: str`, `target_languages: List[str]`, `chunk_max_blocks: int`, `retry_max_attempts: int`, `log_level: str`).

### Subtask 1: Implement `load_config` Function

Create a function named `load_config` within `src/config_loader.py`. This function takes no arguments and is expected to return an instance of the `Config` data class, populated with values loaded from the environment or defaults. Make sure your function signature correctly indicates the return type by importing `Config` from `src.models`.

### Subtask 2: Read Environment Variables

Use the `python-dotenv` library to load variables from the `.env` file located in the project root directory into the environment.

### Subtask 3: Handle Mandatory Variable (`GEMINI_API_KEY`)

Retrieve the `GEMINI_API_KEY` environment variable. This variable is mandatory. If it is not found or is empty, log an informative error message indicating the missing key and cause the application to exit (e.g., raise a `SystemExit` or `RuntimeError`).

### Subtask 4: Handle Optional Variables with Defaults

Retrieve the following optional environment variables. If any are missing, use the specified default value:
*   `TARGET_LANGUAGES`: Expects a string of comma-separated full language names (e.g., `"Vietnamese,French"`). Parse this string into a `List[str]`. Default value if missing: `"Vietnamese,French"` (which should be parsed to `["Vietnamese", "French"]`).
*   `CHUNK_MAX_BLOCKS`: Expects an integer. Default value if missing: `100`.
*   `RETRY_MAX_ATTEMPTS`: Expects an integer. Default value if missing: `6`.
*   `LOG_LEVEL`: Expects a string. Default value if missing: `"INFO"`.
Ensure you handle potential type conversion errors if the environment variables are present but have incorrect formats (though basic handling is sufficient).

### Subtask 5: Populate and Return `Config` Object

Instantiate the `Config` data class (imported from `src.models`) using the values obtained in the previous steps (mandatory API key, optional variables or their defaults). Return this populated `Config` instance from the `load_config` function.

### Subtask 6: Create Debug Script

Create a simple Python script located at `tests/manual/test_config.py`. This script should:
1.  Import the `load_config` function from `src.config_loader`.
2.  Import the `Config` class from `src.models`.
3.  Call `load_config()` to get the configuration object.
4.  Print the resulting `Config` object to the console.
This script will help manually verify that the configuration is loaded correctly from a sample `.env` file.