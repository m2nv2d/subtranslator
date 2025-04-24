# Task 2: SRT File Parsing & Chunking

## Project Context

This task involves creating a Python module responsible for handling uploaded subtitle files in the SRT format. The primary goal is to validate the uploaded file, parse its content into a structured format, and then divide this structured content into manageable chunks for later processing. This module acts as the entry point for subtitle data into the system.

## Prerequisites

*   You will need to ensure the `srt` library is installed in the project's environment (it's typically imported as `import srt`).
*   You will interact with file uploads, likely represented by a `FileStorage` object from the Werkzeug library (commonly used by Flask). You should import this type if needed.
*   You will need custom data structures and exceptions defined elsewhere in the project. Specifically:
    *   The `SubtitleBlock` data class definition can be found in `src/models.py`. Check that file for the exact fields (`index`, `start`, `end`, `content`, `translated_content`).
    *   Custom exception classes `ValidationError` and `ParsingError` can be found in `src/exceptions.py`. Check that file for their definitions. You should import and raise these exceptions as required.

## Implementation within `src/parser.py`

### Define Core Data Structure (in `src/models.py`)

Before implementing the parser itself, ensure the necessary data structure exists. Navigate to the `src/models.py` file. Define a data class (or a standard class) named `SubtitleBlock`. This class will represent a single entry in an SRT file. It must contain the following fields with their specified types:

*   `index`: `int`
*   `start`: `datetime` (from the `datetime` module)
*   `end`: `datetime` (from the `datetime` module)
*   `content`: `str`
*   `translated_content`: `Optional[str]` (from the `typing` module), which should default to `None`.

Make sure to include necessary imports (`from datetime import datetime`, `from typing import Optional, List`).

### Define the Parsing Function

Create a function named `parse_srt` within the `src/parser.py` file. This function should accept two arguments:

1.  `file`: A `FileStorage` object representing the uploaded file.
2.  `max_blocks`: An integer specifying the maximum number of subtitle blocks allowed per chunk.

The function should return a list of lists, where each inner list contains `SubtitleBlock` objects (`List[List[SubtitleBlock]]`).

### Input File Validation

Before attempting to parse, the `parse_srt` function must validate the input `file`.

*   Check if the file extension is `.srt`. If not, raise a `ValidationError`.
*   Check if the file's content length (accessible via an attribute like `content_length` on the `FileStorage` object) is greater than 2,000,000 bytes (2MB). If it exceeds this limit, raise a `ValidationError`.

### SRT Content Parsing

If validation passes, read the content of the `file`. Use the `srt` library's parsing capabilities (e.g., a function like `srt.parse()`) to convert the raw SRT text content into a sequence of subtitle objects provided by the library. Handle potential errors during this parsing process (e.g., malformed SRT content) by raising a `ParsingError`.

### Data Structure Mapping

Iterate through the parsed subtitle objects obtained from the `srt` library. For each original subtitle object, create an instance of the `SubtitleBlock` data class (defined in `src/models.py`). Map the relevant information (index, start time, end time, content text) from the library's object to the corresponding fields in your `SubtitleBlock` instance. Ensure the `translated_content` field is initially set to `None`. Store these `SubtitleBlock` instances in a single list.

### Chunking Logic

Take the complete list of `SubtitleBlock` objects created in the previous step. Divide this list into smaller, disjoint lists (chunks). Each chunk should contain at most `max_blocks` `SubtitleBlock` objects. The function should return these chunks as a list of lists. For example, if `max_blocks` is 100 and you have 250 blocks, the result should be `[[100 blocks], [100 blocks], [50 blocks]]`.

## Manual Debugging Script

Create a simple Python script located at `tests/manual/test_parser.py`. This script should use the above parser to process a srt file (the sole argument of the script) and print out the number of chunks as well as content of first few blocks in the first chunk.

You should be able to run this script from the project root, like `uv run tests/manual/test_parser.py path/to/your/test.srt`.