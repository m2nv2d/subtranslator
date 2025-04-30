# Review Notes: Input Validation & Security

**Files Reviewed:**
*   `src/routers/translate.py`
*   `src/translator/parser.py`
*   `src/core/config.py`
*   `src/core/dependencies.py`

## Observations & Analysis

1.  **File Upload Validation:**
    *   **Good:** File extension is checked (`.srt`, case-insensitive) in both `routers/translate.py` and `translator/parser.py` (though the check in `parser.py` is more robust as it happens after the temporary file is saved).
    *   **Good:** `werkzeug.utils.secure_filename` is used in `routers/translate.py` to sanitize the filename before using it in `os.path.join`. This mitigates path traversal risks associated with the filename itself.
    *   **Good:** File size is validated against a maximum (`MAX_FILE_SIZE_BYTES = 2MB`) and checked for emptiness in `translator/parser.py`.
    *   **Observation:** File content is read fully into memory (`await file.read()`) in `routers/translate.py`. While FastAPI's `UploadFile` handles this, it reiterates the potential memory concern for large files (up to 2MB currently).
    *   **Potential Issue:** No validation is performed on the *content* of the SRT file beyond what the `srt.parse` library does. Maliciously crafted SRT files (e.g., "billion laughs" type attacks if the parser uses XML, though the standard `srt` library likely doesn't) are a theoretical risk, although unlikely for the standard SRT format.

2.  **Form Data Validation:**
    *   **Good:** `target_lang` is validated for presence and checked against the allowed list defined in `settings.TARGET_LANGUAGES` (`routers/translate.py`).
    *   **Minor Issue:** `speed_mode` form field has a default ("normal") but isn't explicitly validated against the expected values ("normal", "fast", "mock"). If an unexpected value is passed, the translation logic might behave unexpectedly (e.g., defaulting to the "normal" model in `_translate_single_chunk` logic) rather than failing fast with a validation error.

3.  **API Key Handling:**
    *   **Good:** `AI_API_KEY` is loaded from `.env` using `pydantic-settings` (`core/config.py`), keeping it separate from source code.
    *   **Good:** The API key is handled within the configuration (`Settings`) and dependency injection (`get_genai_client`) layers. It's passed directly to `genai.Client` and doesn't appear to be logged or stored insecurely.
    *   **Good:** `get_genai_client` handles initialization errors gracefully by returning `None` and logging the error, preventing crashes if the key is invalid or missing. The route handler correctly checks for this `None` value.

4.  **Error Messages & Security:**
    *   **Good:** Standardized error responses are used (`core/errors.py`).
    *   **Observation:** Error messages returned to the client seem generally safe and don't expose internal details like file paths or stack traces (based on reviewing `main.py` exception handlers and `core/errors.py`). Full details are logged server-side.

## Questions

*   Is the 2MB file size limit (`MAX_FILE_SIZE_BYTES`) appropriate for the expected use case?
*   Is the potential memory usage from reading the full file into memory acceptable, or should streaming upload/parsing be considered for robustness?
*   Should `speed_mode` be explicitly validated against allowed values?

## Suggestions

1.  **Validate `speed_mode`:** Add explicit validation in `routers/translate.py` to ensure the `speed_mode` form field is one of the allowed values ("normal", "fast", "mock"). Raise a `ValidationError` if it's not.
    *Example:*
    ```python
    # In translate_srt function
    ALLOWED_SPEED_MODES = {"normal", "fast", "mock"}
    if speed_mode not in ALLOWED_SPEED_MODES:
        logger.warning(f"Translation request failed: Invalid speed mode '{speed_mode}'.")
        raise ValidationError(f"Invalid speed mode: {speed_mode}. Allowed: {', '.join(ALLOWED_SPEED_MODES)}")
    ```
2.  **Consider Streaming Upload (Optional/If Needed):** If memory usage with the current 2MB limit (or a future larger limit) becomes a concern, investigate using FastAPI's streaming request body features (`request.stream()`) or `UploadFile.read(size)` iteratively combined with a streaming SRT parser, although this adds complexity.
3.  **Review SRT Parser Security (Low Priority):** Briefly check the documentation or source of the `srt` library if concerned about potential vulnerabilities related to parsing malformed content, although this is generally a low risk for this format. 