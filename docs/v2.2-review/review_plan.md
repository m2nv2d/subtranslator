# Subtranslator v2.2 Code Review Plan

This document outlines the plan for reviewing the Subtranslator v2.2 codebase, focusing on identifying areas for improvement regarding correctness, robustness, performance, and security.

## Review Tasks

1.  **Error Handling & Resilience:**
    *   **Files:** `src/main.py`, `src/routers/translate.py`, `src/translator/exceptions.py`, `src/translator/chunk_translator.py`, `src/core/errors.py`
    *   **Checks:**
        *   Verify comprehensive exception handling for translator module errors in routers and main app.
        *   Assess `tenacity` retry logic (`RetryError`, `RETRY_MAX_ATTEMPTS`) for robustness, especially for API calls.
        *   Review error response generation (`create_error_response`) for clarity and security (no sensitive data leaks).
        *   Ensure failure handling/logging for background tasks (e.g., file cleanup).

2.  **Concurrency & Performance:**
    *   **Files:** `src/routers/translate.py`, `src/translator/chunk_translator.py`, `src/translator/gemini_helper.py`
    *   **Checks:**
        *   Analyze `translate_all_chunks` for efficient handling of `speed_mode` settings, including potential use of concurrency (`asyncio.gather`?).
        *   Examine Gemini API interactions (`gemini_helper.py`, `chunk_translator.py`) for correct usage of asynchronous calls (`client.aio.models.generate_content`).
        *   Review file I/O (`aiofiles` in `translate_srt`) for non-blocking operations.
        *   Evaluate chunking logic (`parse_srt`, `CHUNK_MAX_BLOCKS`) for efficiency and potential memory issues with large files.

3.  **Input Validation & Security:**
    *   **Files:** `src/routers/translate.py`, `src/core/config.py`
    *   **Checks:**
        *   Review file upload validation (`secure_filename`, file type check). Check for missing file size limits and potential path traversal (though `secure_filename` helps).
        *   Validate form inputs (`target_lang`, `speed_mode`) thoroughly.
        *   Ensure secure loading and usage of `AI_API_KEY` (no exposure in logs/errors).

4.  **Resource Management:**
    *   **Files:** `src/routers/translate.py`
    *   **Checks:**
        *   Confirm reliability of temporary file creation and cleanup (`tempfile`, `os.unlink`, `os.rmdir`, `BackgroundTasks`). Consider `try...finally` or context managers for robustness against premature errors.

5.  **Translation Logic:**
    *   **Files:** `src/translator/*`
    *   **Checks:**
        *   Review SRT parsing (`parser.py`) and reassembly (`reassembler.py`) for handling format variations and edge cases.
        *   Analyze context detection (`context_detector.py`) effectiveness and impact on translation quality.
        *   Check prompt construction and API response handling in `chunk_translator.py` for quality, cost-efficiency, and robustness.

6.  **Configuration:**
    *   **Files:** `src/core/config.py`, `src/core/dependencies.py`
    *   **Checks:**
        *   Review `Settings` model validation in `config.py`.
        *   Examine `genai_client` lifecycle management in `dependencies.py` for efficiency (singleton/caching).

7.  **Code Structure & Readability:**
    *   **Files:** Entire `src/` directory.
    *   **Checks:**
        *   Assess overall code organization and clarity of separation of concerns (`core`, `routers`, `translator`).
        *   Check for code clarity, necessary comments, and consistent naming conventions. 