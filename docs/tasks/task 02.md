# Task 2: Input Validation & Parsing

## Project Context

You are building the backend for a web application that translates subtitle files (specifically `.srt` format). This step focuses on validating the uploaded file and parsing its content into a structured format suitable for further processing.

## Prerequisites
*   The following files are assumed to exist from a previous step and contain the necessary definitions:
    *   `src/models.py`: Contains a data class named `SubtitleBlock` with attributes like `index`, `start`, `end`, `content`.
    *   `src/exceptions.py`: Contains custom exception classes `ValidationError` and `ParsingError`.
*   The required libraries `werkzeug` (typically installed with Flask) and `srt` are installed.
*   The project follows the structure outlined previously, placing service modules under `src/services/`.

### Task 2.1: Implement File Validator

**Goal:** Create a function that checks if an uploaded file meets the basic requirements (file type, size).

1.  **Create the file:** `src/services/validator.py`
2.  **Implement the function `validate_upload`:**
    *   **Signature:**
        ```python
        from werkzeug.datastructures import FileStorage
        from src.exceptions import ValidationError # Assumed to exist

        def validate_upload(file: FileStorage) -> None:
            # Implementation goes here
            pass
        ```
    *   **Functionality:**
        *   Check if the `file.filename` attribute ends with `.srt` (case-insensitive comparison is recommended).
        *   Check if the `file.content_length` attribute is greater than `0` and less than or equal to `2_000_000` (2MB).
        *   If either check fails, raise a `ValidationError` exception (imported from `src.exceptions`) with an appropriate error message.
        *   If both checks pass, the function should return `None` (indicating success).
    *   **Imports:** Make sure to import `FileStorage` from `werkzeug.datastructures` and `ValidationError` from `src.exceptions`.

---

### Task 2.2: Implement SRT Parser and Chunker

**Goal:** Create a function that takes the string content of an SRT file, parses it into structured blocks, and divides these blocks into smaller chunks.

1.  **Create the file:** `src/services/parser.py`
2.  **Implement the function `parse_srt`:**
    *   **Signature:**
        ```python
        from typing import List
        import srt # Assumed installed
        from src.models import SubtitleBlock # Assumed to exist
        from src.exceptions import ParsingError # Assumed to exist
        import datetime # srt uses datetime objects

        def parse_srt(content: str, max_blocks: int) -> List[List[SubtitleBlock]]:
            # Implementation goes here
            pass
        ```
    *   **Functionality:**
        *   Use the `srt.parse(content)` function to parse the input `content` string.
        *   **Error Handling:** Wrap the `srt.parse` call in a `try...except` block. If `srt` raises an exception during parsing (e.g., due to malformed content), catch it and raise a `ParsingError` (imported from `src.exceptions`), potentially wrapping the original exception.
        *   **Mapping:** Iterate through the subtitle objects returned by `srt.parse`. For each `srt.Subtitle` object, create an instance of the `SubtitleBlock` data class (imported from `src.models`). Map the corresponding attributes:
            *   `SubtitleBlock.index` from `srt.Subtitle.index`
            *   `SubtitleBlock.start` from `srt.Subtitle.start` (should be `datetime.timedelta`)
            *   `SubtitleBlock.end` from `srt.Subtitle.end` (should be `datetime.timedelta`)
            *   `SubtitleBlock.content` from `srt.Subtitle.content` (ensure it's a string)
        *   Store these `SubtitleBlock` instances in a list.
        *   **Chunking:** Divide the list of `SubtitleBlock` objects into disjoint sub-lists (chunks). Each chunk should contain at most `max_blocks` `SubtitleBlock` objects. For example, if `max_blocks` is 100 and you have 250 blocks, the output should be `[[block_1..block_100], [block_101..block_200], [block_201..block_250]]`.
        *   Return the list of chunks (`List[List[SubtitleBlock]]`).
    *   **Imports:** Make sure to import `List` from `typing`, `srt`, `datetime`, `SubtitleBlock` from `src.models`, and `ParsingError` from `src.exceptions`.

---

**Testing Reminder (for the human overseeing the AI):** After implementing these functions, write unit tests for `validate_upload` (testing valid/invalid inputs) and `parse_srt` (testing correct parsing, chunking, and error handling for malformed SRT content).
