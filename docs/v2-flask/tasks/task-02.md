# Task 2: Configuration Loading

## Project Context

This task involves creating the core data structures (models) used throughout the application and implementing a module responsible for loading application configuration settings from an environment file. The goal is to define how data is represented, centralize configuration management, provide default values for optional settings, and ensure essential settings like API keys are present at startup. These components will be used by other parts of the application.

## Prerequisites

*   You will need the `python-dotenv` library installed in your environment to handle reading `.env` files.
*   The project structure includes a `src` directory for source code.
*   A `.env` file is expected to exist in the project's root directory (one level above `src`).

### Subtask 0: Create Data Models File (`src/models.py`)

Create the file `src/models.py`. Inside this file, define the data structures needed by the application using Python's `dataclasses` (or standard classes if preferred, but dataclasses are suitable). You will need standard library imports like `datetime` from `datetime`, `Optional` and `List` from `typing`. Define the following classes:

*   **`SubtitleBlock`**: Represents a single subtitle entry. It should have attributes for:
    *   `index` (integer)
    *   `start` (datetime object)
    *   `end` (datetime object)
    *   `content` (string)
    *   `translated_content` (optional string, initially None)
*   **`Config`**: Represents the application's configuration settings. It should have attributes for:
    *   `gemini_api_key` (string)
    *   `target_languages` (list of strings, e.g., `["Vietnamese", "French"]`)
    *   `chunk_max_blocks` (integer)
    *   `retry_max_attempts` (integer)
    *   `log_level` (string)

### Subtask 1: Implement `load_config` Function

Create a function named `load_config` within `src/config_loader.py`. This function takes no arguments and is expected to return an instance of the `Config` data class (defined in `src/models.py`), populated with values loaded from the environment or defaults. Make sure your function signature correctly indicates the return type by importing `Config` from `src.models`.

### Subtask 2: Read Environment Variables

Inside `load_config`, use the `python-dotenv` library to load variables from the `.env` file located in the project root directory into the environment.

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