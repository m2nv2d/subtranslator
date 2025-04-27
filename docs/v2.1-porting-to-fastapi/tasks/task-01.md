## Task 1: Configuration & Models

**Project Context**
This project is a web application that translates subtitle files (specifically `.srt` format) using an external Generative AI service (Google Gemini). This task focuses on setting up the data models and configuration management needed for the application using Pydantic, preparing for integration with the FastAPI framework.

**Prerequisites**
Ensure you have access to and familiarity with the following Python libraries:
*   Pydantic (for data validation and modeling)
*   Pydantic-Settings (for loading configuration from environment variables and `.env` files)
*   python-dotenv (implicitly used by Pydantic-Settings to load `.env` files)

**Subtask 1: Define Core Data Model**
Locate the existing data structures defined in `src/translator/models.py`. Your goal is to redefine the `SubtitleBlock` structure as a Pydantic `BaseModel`. This model should represent a single subtitle entry and must include the following fields with their specified types:
*   `index`: `int`
*   `start`: `datetime` (from the `datetime` standard library module)
*   `end`: `datetime`
*   `content`: `str`
*   `translated_content`: `Optional[str]` (using `typing.Optional`), defaulting to `None`.

You can remove or ignore the original `Config` class definition found in this file, as it will be replaced in the next step. Ensure the new Pydantic `SubtitleBlock` model resides in `src/translator/models.py`.

**Subtask 2: Implement Configuration Settings**
Create a new file named `src/config.py`. In this file, implement the application's configuration loading using Pydantic-Settings.
Define a class named `Settings` that inherits from `pydantic_settings.BaseSettings`. This class will automatically load configuration values from environment variables and a `.env` file located in the project's root directory (one level above the `src` directory).

The `Settings` class must define the following configuration fields, incorporating validation and default values as described:
*   `ai_api_key`: A `str` representing the API key for the Gemini service. This field is mandatory and should not have a default value; loading should fail if it's missing.
*   `target_languages`: A `List[str]` containing the full names of languages the application can translate subtitles into (e.g., `["Vietnamese", "French"]`). This should be loaded from an environment variable (e.g., `TARGET_LANGUAGES="Vietnamese,French"`). Implement logic (e.g., using Pydantic validators or pre-processors) to parse a comma-separated string, strip whitespace from each language name, filter out any empty entries resulting from parsing, and default to `["Vietnamese", "French"]` if the environment variable is missing, empty, or contains invalid formatting.
*   `chunk_max_blocks`: An `int` specifying the maximum number of subtitle blocks to include in a single chunk for processing. Apply validation to ensure this value is a positive integer. Set the default value to `100`.
*   `retry_max_attempts`: An `int` defining the maximum number of retry attempts for API calls. Apply validation to ensure this value is a non-negative integer (zero or greater). Set the default value to `6`.
*   `log_level`: A `str` indicating the logging level for the application. Apply validation to ensure the value is one of the following uppercase strings: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`. Set the default value to `"INFO"`.

Configure the `Settings` class (via its `model_config` or `Config` inner class, depending on your Pydantic version) to read from a `.env` file. This new `Settings` class effectively replaces the functionality previously handled by `src/config_loader.py` and the old `Config` data class.

**Subtask 3: Create Configuration Dependency Function**
Create a new file named `src/dependencies.py`. Inside this file, define a simple synchronous function, for example named `get_settings`, that takes no arguments. This function's sole purpose is to instantiate the `Settings` class (defined in `src/config.py`) and return the instance. This function will later be used by FastAPI to inject the application settings into route handlers.

**Debugging**
Create a simple Python script named `test_config.py` inside the `tests/manual/` directory. This script should:
1.  Import the `Settings` class from `src.config`.
2.  Attempt to instantiate the `Settings` class.
3.  Print the values of all attributes of the created settings instance (e.g., `settings.ai_api_key`, `settings.target_languages`, etc.).
Run this script directly to verify that configuration is loaded correctly from your `.env` file and that defaults and validation logic are working as expected. You will need a `.env` file in the project root with at least `AI_API_KEY` defined for the script to succeed without errors.