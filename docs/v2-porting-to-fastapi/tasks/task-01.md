## Task 1: Configuration & Models Refactor for FastAPI

### Project Context
This task is part of migrating a Flask-based web application to FastAPI. The application translates subtitle files (specifically, `.srt` format) using an external AI service (Google Gemini). The goal of *this specific task* is to refactor the data models and configuration loading mechanism to use Pydantic, aligning with common FastAPI practices, replacing the previous custom approach.

### Prerequisites
*   Access to the project's source code repository.
*   Familiarity with Python, Pydantic (`BaseModel`, `BaseSettings`), and Python type hinting.
*   Access to the *Detailed Technical Design* document provided previously. You will need to refer to the sections describing `src/translator/models.py` and `src/config_loader.py` for the specifications of the original models and configuration variables.

### Subtask 1: Define Pydantic Data Model (`SubtitleBlock`)
*   **Objective:** Convert the existing data transfer object used for representing a single subtitle entry into a Pydantic model.
*   **Location:** Modify the file `src/translator/models.py`.
*   **Details:**
    *   Consult the original *Detailed Technical Design* document's definition for the `SubtitleBlock` class under the `src/translator/models.py` section. Also, review the current implementation in the `src/translator/models.py` file within the codebase itself to capture any potential discrepancies from the document.
    *   Define a Pydantic `BaseModel` named `SubtitleBlock` within `src/translator/models.py`.
    *   Ensure this model includes fields matching the original specification: `index` (integer), `start` (datetime object), `end` (datetime object), `content` (string), and `translated_content` (optional string, defaulting to `None`). Use appropriate Python type hints for each field.
    *   The previous implementation (likely a dataclass) should be replaced by this Pydantic model.

### Subtask 2: Implement Pydantic Settings Configuration
*   **Objective:** Replace the custom configuration loading script (`src/config_loader.py`) with Pydantic's `BaseSettings` for automated loading and validation from environment variables or a `.env` file.
*   **Location:** Create a new file named `src/config.py`. The old `src/config_loader.py` and the `Config` model previously in `src/translator/models.py` will become obsolete.
*   **Details:**
    *   Refer to the *Detailed Technical Design* document's description of `src/config_loader.py` and the `Config` model definition (previously in `src/translator/models.py`). Examine the current `src/config_loader.py` in the codebase and any existing `.env` file in the project root to understand the variable names and loading logic.
    *   In `src/config.py`, create a class named `Settings` that inherits from `pydantic_settings.BaseSettings`.
    *   Define fields within the `Settings` class to hold all configuration parameters previously managed by `config_loader.py`. These must include:
        *   `gemini_api_key`: `str` (This is mandatory).
        *   `target_languages`: `List[str]`
        *   `chunk_max_blocks`: `int`
        *   `retry_max_attempts`: `int`
        *   `log_level`: `str`
    *   Configure `BaseSettings` (if necessary, often automatic) to load values from environment variables, using a `.env` file located in the project root (one level above the `src` directory) as a source.
    *   Implement validation logic *within the `Settings` model using Pydantic validators*, mirroring the requirements outlined in the original design document for `config_loader.py`:
        *   `TARGET_LANGUAGES`: Should handle a comma-separated input string, strip whitespace, filter empty entries, and default to `["Vietnamese", "French"]` if parsing fails or the variable is absent.
        *   `CHUNK_MAX_BLOCKS`: Must be a positive integer, defaulting to `100`.
        *   `RETRY_MAX_ATTEMPTS`: Must be a non-negative integer, defaulting to `6`.
        *   `LOG_LEVEL`: Must be a valid uppercase log level string from the set `["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]`, defaulting to `"INFO"`.
    *   Ensure required fields like `gemini_api_key` are implicitly or explicitly marked as mandatory (Pydantic usually handles this based on lack of defaults or `Optional` type hint).