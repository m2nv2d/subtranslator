# Task 3: Context Detection Logic

## Project Context

This task involves creating a Python module responsible for analyzing the initial content of a subtitle file to determine its general context or topic. This module is part of a larger Flask web application designed to translate subtitle files (`.srt` format). The detected context might be used later in the translation process to improve accuracy. The application parses the SRT file into chunks of subtitle blocks before processing.

You will need to interact with data structures and configurations defined elsewhere in the project.

## Prerequisites

Before starting, familiarize yourself with the following components. Check the current files in the `src/` directory for the most up-to-date definitions, as they might have evolved:

1.  **Data Models (`src/models.py`):** Understand the structure of `SubtitleBlock` (containing `index`, `start`, `end`, `content`, `translated_content`) and `Config` (containing `gemini_api_key`, `target_languages`, `chunk_max_blocks`, `retry_max_attempts`, `log_level`).
2.  **Custom Exceptions (`src/exceptions.py`):** Be aware of the custom exception classes defined here, particularly `ContextDetectionError`.
3.  **External Libraries:** You will need `tenacity` for implementing retry logic and `google-genai` for interacting with the Gemini API (specifically the `genai.client.Client` type, although you won't implement the API call itself yet). Ensure these are listed as dependencies for the project.

### Subtask 1: Implement `detect_context` Function

*   **Location:** `src/context_detector.py`
*   **Goal:** Create the main function that orchestrates context detection.
*   **Requirements:**
    *   Define a function with the following signature:
        `detect_context(sub: List[List[SubtitleBlock]], speed_mode: str, genai_client: genai.client.Client, config: models.Config) -> str`
        *   `sub`: A list where each element is a list (chunk) of `SubtitleBlock` objects, representing the parsed SRT file.
        *   `speed_mode`: A string indicating the desired processing mode. Expected values are `"mock"`, `"fast"`, or `"normal"`.
        *   `genai_client`: An initialized instance of the Gemini client (from `google-genai` SDK. Remember, it's not the old `google-generativeai` package). This is required if `speed_mode` is not `"mock"`.
        *   `config`: An instance of the `Config` data class containing application settings.
        *   Returns: A string representing the detected context.
    *   Implement the logic based on `speed_mode`:
        *   **If `speed_mode` is `"mock"`:** Implement this fully. The function should immediately return a hardcoded context string (e.g., `"General conversation"`, `"Technical discussion"`, or similar). It should *not* attempt any external API calls or complex processing.
        *   **If `speed_mode` is `"fast"` or `"normal"`:** Implement the scaffolding for this logic.
            *   Indicate that this path requires the `genai_client`.
            *   Extract the text content from the `SubtitleBlock` objects within the *first chunk* (`sub[0]`), combining roughly the first 100 lines of dialogue.
            *   Set up retry logic using the `tenacity` library decorator around the section intended for the API call. Configure the retries using `config.retry_max_attempts`. The specific retry conditions (e.g., which exceptions to retry on) can be general for now, anticipating potential API errors.
            *   **Crucially, do *not* implement the actual Gemini API call.** Leave clear comments or placeholder code indicating where the prompt would be constructed, where the `genai_client` method (like `generate_content`) would be called, and where the response would be parsed.
            *   Ensure that if the process (including retries) were to fail, it would raise a `ContextDetectionError` (imported from `src/exceptions.py`). For now, you might add a placeholder `raise ContextDetectionError("API call not implemented")` within the non-mock path after the text extraction step.

### Subtask 2: Create Debug Script

*   **Location:** `tests/manual/test_context_detector.py`
*   **Goal:** Create a simple command-line script to manually test the `detect_context` function, primarily for the implemented `"mock"` mode.
*   **Requirements:**
    *   The script should accept two command-line arguments: the path to an SRT file and the `speed_mode` string (`"mock"`, `"fast"`, or `"normal"`)
    *   Load the application configuration by calling the `load_config` function (check its location, likely `src/config_loader.py`).
    *   Parse the input SRT file using the `parse_srt` function (check its location, likely `src/parser.py`). Pass the required arguments, including `config.chunk_max_blocks`.
    *   Call the `detect_context` function from `src.context_detector` with the parsed subtitle chunks, the speed mode, the client object (or `None`), and the loaded config.
    *   Print the string returned by `detect_context` to the console. If any exceptions occur during parsing or detection, catch them and print an informative error message.