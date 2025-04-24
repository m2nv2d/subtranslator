**Task 7: SRT File Reassembly**

**Project Context**

This project aims to translate SubRip Text (`.srt`) subtitle files. Your task is to implement the final step in the backend process: taking the subtitle data, which has already been parsed into chunks and theoretically translated (though translation might be mocked or incomplete at this stage), and formatting it back into a standard SRT file string, encoded as bytes. You will work within a predefined project structure.

**Prerequisites**

*   Familiarity with Python 3.x.
*   Understanding of the standard SRT file format structure (block index, timestamp range, text content, blank line separator).
*   The project uses a specific directory structure (`src/`, `tests/`). You will create/modify files within this structure.
*   You need to be aware of the data structure used to hold subtitle information. Locate and examine the `SubtitleBlock` data class defined in `src/models.py`. Pay attention to its attributes: `index` (int), `start` (datetime.time), `end` (datetime.time), `content` (str), and `translated_content` (Optional[str]). Your function will receive a list of lists containing these objects (`List[List[SubtitleBlock]]`).

**Subtask 1: Implement `reassemble_srt` Function**

*   **File:** Create or modify the file `src/reassembler.py`.
*   **Function Signature:** Implement a function with the following exact signature:
    ```python
    from typing import List
    # You will likely need to import SubtitleBlock from src.models
    # from src.models import SubtitleBlock # Adjust path if necessary based on execution context

    def reassemble_srt(sub: List[List[SubtitleBlock]]) -> bytes:
        # Implementation goes here
        pass
    ```
*   **Requirements:**
    *   The function must accept a nested list (`sub`) where each inner list contains `SubtitleBlock` objects representing a chunk of the original file.
    *   Iterate through the chunks and then through each `SubtitleBlock` within those chunks in their original order.
    *   For each `SubtitleBlock`, construct a string conforming to the standard SRT block format:
        ```
        [Index]
        [Start Timestamp] --> [End Timestamp]
        [Translated Content Line 1]
        [Translated Content Line 2]
        ...

        ```
    *   Use the `index` attribute from the `SubtitleBlock` for the block index.
    *   Format the `start` and `end` attributes (which should be `datetime.time` objects, check `src/models.py` to confirm) into the SRT timestamp format `HH:MM:SS,mmm` (hours:minutes:seconds,milliseconds). You might find utilities in the `srt` library helpful for this formatting, or you can do it manually.
    *   Use the `translated_content` attribute for the text part of the block. **Important:** Check if `translated_content` is not `None` or empty; if it is, you should fall back to using the original `content` attribute from the `SubtitleBlock` to ensure the structure remains valid even if translation failed for a block. Handle potential multi-line content correctly within the block.
    *   Concatenate all these formatted blocks into one large string. Ensure there is exactly one blank line separating consecutive SRT blocks.
    *   Finally, encode this complete SRT string into `bytes` using UTF-8 encoding and return the resulting `bytes` object.

**Subtask 2: Create Manual Test Script**

*   **File:** Create a new Python script file at `tests/manual/test_reassembly_flow.py`.
*   **Purpose:** This script will serve as a manual check for the reassembly logic by running it within a simulated end-to-end flow (using file parsing and *mocked* translation). It helps verify that `reassemble_srt` correctly formats the data structure it receives.
*   **Requirements:**
    *   The script should use `argparse` or a similar library to accept two command-line arguments: the path to an input `.srt` file and a `speed_mode` string (which won't affect this test's core logic but mirrors the app's intended usage).
    *   Import necessary functions/classes:
        *   `parse_srt` from `src.parser`
        *   `reassemble_srt` from `src.reassembler`
        *   `SubtitleBlock` and `Config` from `src.models`
        *   `load_config` from `src.config_loader` (to get default `chunk_max_blocks`)
        *   Standard libraries like `os`, `sys`, `argparse`, `io`.
    *   Load the application configuration using `load_config()` to get the `chunk_max_blocks` setting.
    *   Use `parse_srt` to parse the input SRT file into the `sub_chunks` structure (`List[List[SubtitleBlock]]`). Handle potential parsing errors gracefully (e.g., print an error and exit).
    *   Call the right `context_detector` or `chunk_translator` functions, depending on the `speed_mode`.
    *   Call your implemented `reassemble_srt(sub_chunks)` function, passing the modified `sub_chunks`.
    *   Take the returned `bytes` object, decode it back into a string (using UTF-8).
    *   Print the *first 40 lines* (or a similar reasonable amount) of the resulting reassembled SRT string to the console. This allows for quick visual verification of the output format (indices, timestamps, text, blank lines).