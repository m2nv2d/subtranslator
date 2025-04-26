**Task 1: Define Data Models & Exceptions**

**Project Context**

This task is part of developing a Flask-based web application designed to translate subtitle files (like SRT format) using an external AI service (like Google Gemini). These initial modules establish the core data structures and error types used across the application.

**Prerequisites**

*   A working Python environment (version specified in project requirements, likely found in a `pyproject.toml` file if available).
*   Standard Python libraries: `dataclasses`, `datetime`, `typing`. No external packages need to be installed specifically for *this* task, though the project overall will have dependencies.
*   The project structure should be set up with a `src/` directory at the root, where the new files will be placed.

**Subtask 1: Implement Data Models (`src/models.py`)**

*   **Goal:** Create the Python classes that represent the data structures used within the application.
*   **Location:** Create or modify the file `src/models.py`.
*   **Requirements:**
    *   Ensure necessary imports are present: `dataclasses`, `datetime.datetime`, `typing.List`, `typing.Optional`.
    *   Define a data class named `SubtitleBlock`. It must have the following attributes with the specified types:
        *   `index: int`
        *   `start: datetime.datetime`
        *   `end: datetime.datetime`
        *   `content: str`
        *   `translated_content: Optional[str]` (with a default value of `None`).
    *   Define another data class named `Config`. It must have the following attributes with the specified types:
        *   `gemini_api_key: str`
        *   `target_languages: List[str]` (This will hold full language names like "Vietnamese").
        *   `chunk_max_blocks: int`
        *   `retry_max_attempts: int`
        *   `log_level: str`

**Subtask 2: Implement Custom Exceptions (`src/exceptions.py`)**

*   **Goal:** Define a hierarchy of custom exception classes for standardized error handling throughout the application.
*   **Location:** Create or modify the file `src/exceptions.py`.
*   **Requirements:**
    *   Define several custom exception classes. All these classes must inherit directly from Python's built-in `Exception` class.
    *   The specific exception classes to define are:
        *   `ValidationError`
        *   `ParsingError`
        *   `ContextDetectionError`
        *   `ChunkTranslationError`
        *   `GenAIClientInitError`
        *   `GenAIRequestError`
        *   `GenAIParsingError`
    *   These classes just need to be defined; no special internal logic is required within them at this stage.