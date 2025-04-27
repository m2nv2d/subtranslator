# Product Requirements Document: Simple SRT Translator

## 1. Product Purpose & Vision
We are building a minimal Flask-based web application that allows a user to upload an SRT subtitle file, choose a target language from a predefined list, select a translation speed mode ("normal" or "fast"), and download a correctly formatted, translated SRT file. The application utilizes the Google Generative AI (Gemini) API for translation, configured via environment variables. This tool is intended for personal, educational, or hobbyist use, focusing on simplicity and core functionality rather than scalability or multi-user features.

## 2. Goals & Success Criteria
1.  **Functional:**
    *   A user can successfully upload a `.srt` file that is greater than 0 bytes and less than or equal to 2MB.
    *   The user can select a target language from a dropdown menu populated by the `TARGET_LANGUAGES` configuration setting.
    *   The user can select a speed mode: "normal" (default) or "fast".
    *   Upon clicking "Translate", the application processes the file using the `google-genai` SDK.
    *   The application returns a valid `.srt` file containing the translated text, preserving original timestamps and indices. The filename follows the pattern `original_stem_TargetLanguage.srt` (e.g., `my_video_Vietnamese.srt`).
    *   Validation errors (file type, size) or processing failures (API errors after retries, parsing issues) result in a clear error message displayed to the user on the status line.
2.  **User Experience (UX):**
    *   The application presents a single-page interface with a clean, functional design (using vanilla CSS).
    *   The "Translate" button is disabled, and a status message (e.g., "Translating...") is displayed in the `#status-message` area (styled with `.status-processing`) while the backend processes the request.
    *   On success, the status message updates (e.g., "Translation complete.", styled with `.status-success`), and a file download is initiated.
    *   On failure, the status message displays an appropriate error (e.g., "Translation failed: API error after retries", styled with `.status-error`), and the button is re-enabled.
3.  **Quality & Reliability:**
    *   API calls to Google Generative AI for context detection and chunk translation use `tenacity` for automatic retries (currently hardcoded to 3 attempts) on transient errors.
    *   If API calls fail after all retry attempts, the process is aborted, and an error is reported to the user.
    *   Subtitle parsing (using the `srt` library) and reassembly (`srt.compose`) must accurately preserve the original block indices and timestamps in the output file.
    *   Input SRT files are expected to be UTF-8 encoded; errors during parsing are handled gracefully (e.g., raising `ParsingError`).
4.  **Technical:**
    *   Implements context detection using the first subtitle chunk via the shared `genai.Client`.
    *   Implements chunked translation using `asyncio` (`TaskGroup`) for concurrent API calls via the shared `genai.Client`.
    *   Utilizes the `srt` library for robust SRT parsing and generation.
    *   Configuration (`AI_API_KEY`, `TARGET_LANGUAGES`, `CHUNK_MAX_BLOCKS`, `RETRY_MAX_ATTEMPTS`, `LOG_LEVEL`) is managed via `.env` file and loaded/validated at startup by `src/config_loader.py`.
    *   A single, shared `google.generativeai.Client` instance is created at startup (`app.py` via `gemini_helper.py`) and passed to necessary service modules.
    *   Employs custom exceptions (`src/exceptions.py`) and Flask error handlers (`app.py`) for structured error reporting.

## 3. Target Users & Stakeholders
*   **Primary Users:** Language learners, content creators, educators, hobbyist translators who need a quick, simple tool for translating SRT subtitle files without complex software or sign-ups.
*   **Secondary Stakeholders:** The developer(s) using this project to practice/demonstrate skills in Flask, asynchronous programming (`asyncio`), integrating with LLM APIs (`google-genai`), handling file uploads, and structuring a small web application.

## 4. Core Features
1.  **File Upload & Validation:**
    *   Provides an HTML file input accepting only `.srt` files.
    *   Client-side (`app.js`) check for file presence and `.srt` extension.
    *   Server-side (`parser.py`) validation enforces `.srt` extension, file size (> 0 bytes, <= 2MB), and basic readability.
    *   Rejects invalid uploads with an appropriate error message via the status line (`#status-message`).
2.  **Settings Controls:**
    *   **Target Language:** A `<select>` dropdown populated dynamically with full language names (e.g., "Vietnamese", "French") read from the `TARGET_LANGUAGES` setting in the configuration (`Config` object). Selection is required.
    *   **Speed Mode:** A `<select>` dropdown allowing the user to choose "normal" (default) or "fast". This choice influences the Gemini model used internally (`context_detector`/`chunk_translator`).
3.  **Context Analysis (`src/context_detector.py`):**
    *   Extracts text content from the *first chunk* of parsed subtitle blocks.
    *   Sends this text to the Gemini API (via the shared `genai.Client`) using a prompt designed to elicit a high-level topic or context for the video.
    *   Uses the selected `speed_mode` to potentially choose a specific Gemini model.
    *   Includes retry logic (`tenacity`).
4.  **Chunked Translation Pipeline (`src/chunk_translator.py`):**
    *   Takes the list of subtitle block chunks (from `parser.py`), the detected context, target language, speed mode, shared `genai.Client`, and `Config`.
    *   Uses `asyncio.TaskGroup` to launch concurrent translation tasks (`_translate_single_chunk`) for each chunk.
    *   Each task constructs a prompt including the chunk's text, context, and target language.
    *   Calls the Gemini API's async method (via the passed `genai.Client`), requesting JSON output, using the appropriate model based on `speed_mode`.
    *   Includes retry logic (`tenacity`).
    *   Parses the JSON response and updates the `translated_content` attribute of the `SubtitleBlock` objects *in-place*. Handles potential JSON parsing errors.
5.  **Output Generation (`src/reassembler.py`, `src.app.py`):**
    *   `reassembler.py` uses `srt.compose` to construct a valid SRT formatted string from the list of `SubtitleBlock` chunks, using `translated_content` where available, otherwise falling back to original `content`.
    *   Encodes the string to bytes.
    *   `app.py` creates an in-memory byte stream (`io.BytesIO`) and uses Flask's `send_file` to deliver the result to the user.
    *   The download is triggered `as_attachment=True` with a filename like `original_stem_TargetLanguage.srt`.
6.  **Error Handling & Status Updates:**
    *   Client-side (`app.js`): Disables the submit button and updates `#status-message` (e.g., "Translating...") upon form submission. Re-enables the button and updates status (`success` or `error` message) upon completion or failure.
    *   Server-side (`app.py`): Uses custom exception classes and Flask error handlers to catch errors from parsing, context detection, translation (including `tenacity.RetryError` for API failures), etc. Returns JSON error responses with appropriate HTTP status codes (e.g., 400, 422, 500, 503, 504).

## 5. User Experience (Flow & UI)
*   **Persona:** Alex, a student watching online course videos, wants subtitles translated into their native language, Spanish.
*   **Key Flow:**
    1.  Alex navigates to the web application URL (`/`).
    2.  The page displays a simple form: file input, language dropdown, speed mode dropdown ("normal", "fast"), and a "Translate" button.
    3.  Alex clicks "Choose File", selects `lecture_01.srt` (1.5MB).
    4.  Alex selects "Spanish" from the language dropdown.
    5.  Alex leaves the speed mode as "normal".
    6.  Alex clicks "Translate".
    7.  The "Translate" button becomes disabled. The status line below the form updates to "Translating...".
    8.  After processing (potentially seconds to minutes depending on file size and API latency), the browser prompts Alex to download `lecture_01_Spanish.srt`. The status line might briefly show "Translation complete."
    9.  *(Alternate Flow - Error)* If the Gemini API fails after retries during translation, the button re-enables, and the status line shows an error like: "Translation failed: LLM API failed after multiple retries."
*   **UI Considerations:**
    *   Clean, single-column layout that works reasonably on different screen sizes.
    *   Minimalist styling using vanilla CSS, prioritizing function over aesthetics.
    *   Clear visual distinction between status states (processing, success, error) using CSS classes on the `#status-message` element.

## 6. High-Level Functional Requirements
1.  The system **shall** serve a single HTML page rendered via Flask/Jinja2 at the root URL (`/`).
2.  The system **shall** validate uploaded files upon submission to ensure they have a `.srt` extension and a file size greater than 0 bytes and less than or equal to 2MB.
3.  The system **shall**, via `src/config_loader.py` at startup, load configuration from a `.env` file or environment variables, including `AI_API_KEY`, `TARGET_LANGUAGES`, `CHUNK_MAX_BLOCKS`, `RETRY_MAX_ATTEMPTS`, and `LOG_LEVEL`.
4.  The system **shall** use the `srt` library (via `src/parser.py`) to parse the content of the validated SRT file into chunks of `SubtitleBlock` data structures held in memory.
5.  The system **shall** determine a context hint by sending the text of the first chunk to the Gemini API via `src/context_detector.py` using the shared `genai.Client`.
6.  The system **shall** orchestrate asynchronous translation of subtitle chunks using `src/chunk_translator.py` (leveraging `asyncio` and `tenacity` for retries), passing the detected context, target language, speed mode, and using the shared `genai.Client` for API calls requesting JSON output.
7.  The system **shall** implement retry logic using `tenacity` (currently hardcoded to 3 attempts) for API calls within `context_detector` and `chunk_translator`.
8.  The system **shall** abort the translation process and display a user-facing error message (via the status line) if a persistent error occurs (e.g., validation failure, parsing error, API failure after retries).
9.  The system **shall** use the `srt` library (via `src/reassembler.py`) to reassemble the (potentially translated) `SubtitleBlock` data into a valid SRT format string, preserving original timestamps and indices.
10. The system **shall** deliver the resulting translated SRT data as a downloadable file attachment (using Flask's `send_file`), with a filename constructed as `original_stem_TargetLanguage.srt`.

## 7. Out-of-Scope Functionality
*   Support for any file formats other than `.srt` (e.g., VTT, ASS).
*   User accounts, login, authentication, or usage tracking.
*   Saving or persisting translation jobs or files on the server.
*   Real-time progress indication beyond a simple "Translating..." status message.
*   Advanced UI features or styling beyond basic functional CSS.
*   Guaranteed performance SLAs, high availability, or horizontal scaling capabilities.
*   Use of frontend frameworks like React, Vue, Angular, etc.
*   Containerization, automated deployment pipelines (CI/CD), or advanced monitoring/alerting.

## 8. Constraints & Assumptions
*   **Platform:** Primarily developed and run in a Linux-like environment.
*   **Technology:** Backend implemented in Python using Flask. Frontend uses vanilla JavaScript (ES6+), HTML5, and CSS3 rendered via Jinja2.
*   **Dependencies:** Requires Python 3.x with `asyncio` support. Key libraries include `Flask`, `google-genai`, `python-dotenv`, `srt`, `tenacity`. Package management via standard Python tools (e.g., `pip`, `uv`).
*   **LLM:** Relies exclusively on the Google Generative AI (Gemini) API, accessed via the `google-genai` SDK. Assumes a valid `AI_API_KEY` is provided via configuration.
*   **Input Files:** Assumes uploaded `.srt` files are generally well-formed and encoded in UTF-8. Maximum size is strictly enforced at 2MB.
*   **Translation Modes:** Only "normal" and "fast" modes are exposed. The mapping to specific Gemini models is an internal implementation detail within `context_detector` and `chunk_translator`.
*   **User Feedback:** Limited to the single status line (`#status-message`) on the main page for processing updates and error reporting.