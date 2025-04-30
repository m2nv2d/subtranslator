# Review Notes: Translation Logic

**Files Reviewed:**
*   `src/translator/parser.py`
*   `src/translator/reassembler.py`
*   `src/translator/context_detector.py`
*   `src/translator/chunk_translator.py`
*   `src/translator/models.py`
*   `src/translator/gemini_helper.py`
*   `src/core/config.py`

## Observations & Analysis

1.  **Parsing & Reassembly (`parser.py`, `reassembler.py`, `models.py`):**
    *   **Good:** Uses the standard `srt` library for parsing and composition, which should handle typical SRT formats well.
    *   **Good:** The `SubtitleBlock` dataclass in `models.py` is a clear representation of the data.
    *   **Good:** `reassembler.py` correctly reconstructs the SRT file from chunks, falling back to original content if translation is missing, and encodes to UTF-8.
    *   **Observation:** Parsing reads the whole file into memory (as noted previously).

2.  **Context Detection (`context_detector.py`):**
    *   **Observation:** Context is determined by sending only the content of the *first* chunk (`sub[0]`, default 100 blocks) to the LLM.
    *   **Potential Issue:** For longer videos or videos with evolving topics, the context derived from only the beginning might be inaccurate or incomplete for later parts of the subtitle, potentially affecting translation quality for those sections.
    *   **Observation:** Uses the same potentially problematic `configurable_retry` decorator (retries on any `Exception`, complex arg extraction) as `chunk_translator.py`.
    *   **Good:** Provides a mock context for testing/offline use.

3.  **Prompt Engineering (`context_detector.py`, `chunk_translator.py`):**
    *   **Good:** Prompts clearly instruct the LLM on its role (context detector or translator).
    *   **Good:** The translation prompt specifies the desired JSON output format, including the keys (`index`, `translated_line_1`, etc.).
    *   **Good:** The translation prompt includes the detected `context` to guide the LLM.
    *   **Observation:** The user prompt for translation simply concatenates the index and content (`f"\n{i}\n{block.content}\n"`). This is simple but might be improvable (e.g., clearer separators, XML-like tags) depending on LLM performance.

4.  **API Interaction & Response Handling (`chunk_translator.py`):**
    *   **Good:** Explicitly requests JSON output from the Gemini API (`response_mime_type='application/json'`).
    *   **Potential Issue:** The JSON parsing logic strictly expects keys named `translated_line_1`, `translated_line_2`, ... and assumes a correct list-of-objects structure. LLM responses can sometimes deviate from the requested format (e.g., adding conversational text, minor key name changes, incorrect JSON syntax). The current code handles `json.JSONDecodeError` but might crash on `KeyError` or `TypeError` if the structure is valid JSON but not what's expected. This fragility could lead to chunk translation failures (and retries).
    *   **Observation:** Failures in parsing the LLM response currently raise `ChunkTranslationError` (specifically `GenAIParsingError` could be used here, though it's not currently imported/used) or potentially trigger retries if they manifest as other exceptions covered by the broad retry policy.

## Questions

*   How effective is the context detection based solely on the first chunk? Has testing revealed issues with context drift in longer videos?
*   How reliable has the LLM been in adhering to the requested JSON format (`translated_line_1`, etc.)? Are `JSONDecodeError` or other parsing-related errors frequent in logs?

## Suggestions

1.  **Improve Context Detection Robustness (Optional/If Needed):** If context detection proves insufficient based on the first chunk:
    *   Consider sampling blocks from multiple points in the subtitle file (e.g., beginning, middle, end) to generate the context prompt.
    *   Alternatively, pass the context detection prompt *along with each chunk* to the translation call, allowing the context to be potentially more localized, although this increases token usage.
2.  **Enhance LLM Response Parsing Robustness:** Make the JSON parsing logic in `_translate_single_chunk` more resilient to minor deviations:
    *   Wrap the JSON parsing and dictionary access in a `try...except` block that catches `json.JSONDecodeError`, `KeyError`, `TypeError`, and potentially others.
    *   Instead of iterating `translated_line_i`, consider iterating through `block.items()` and checking if keys *start with* `translated_line_` to handle potential variations or extra keys gracefully.
    *   Log the problematic response text when parsing fails to aid debugging.
    *   Consider raising the more specific `GenAIParsingError` (defined in `translator.exceptions`) when JSON parsing fails.
3.  **Refine Retry Logic (Covered Previously):** As mentioned in the Error Handling review, make the retry logic target specific transient API errors rather than all `Exception`s, which would prevent retries on non-recoverable issues like persistent JSON parsing failures.
4.  **Refine Retry Decorator Args (Covered Previously):** Pass `settings` and `chunk_index` explicitly to avoid introspection issues. 