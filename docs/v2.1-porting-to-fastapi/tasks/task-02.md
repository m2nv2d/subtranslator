## Task 2: Review `translator/` Modules

### Project Context
This project is a web application originally built with Flask that translates subtitle files (SRT format). It uses the Google Generative AI API for translation. The application is currently being ported to FastAPI. The core translation logic resides in the `src/translator/` package. This task focuses *only* on reviewing this `translator` package to ensure its stability and compatibility during the framework migration. The web framework layer (`src/app.py` being replaced by `src/main.py`) handles HTTP requests, responses, file uploads, and orchestrates calls into the `translator` package.

### Prerequisites
Familiarity with the project structure as outlined in the technical design document. The `translator` package contains the following key components (refer to `src/translator/` for the actual code):
*   `exceptions.py`: Custom exceptions.
*   `models.py`: Data classes (`SubtitleBlock`, `Config`).
*   `parser.py`: SRT file parsing and chunking.
*   `gemini_helper.py`: Google GenAI client initialization.
*   `context_detector.py`: Detects context from subtitle chunks.
*   `chunk_translator.py`: Translates subtitle chunks, potentially using `asyncio`.
*   `reassembler.py`: Reassembles translated chunks into SRT format.

The goal is to reuse the `translator` code with minimal changes. The web layer (now FastAPI) will be responsible for calling functions within this package.

### Subtask 1: Verify Framework Independence
Review all modules within the `src/translator/` directory. Ensure that none of these modules directly import or depend on Flask, Werkzeug, or any other Flask-specific components. The logic within this package should be pure Python, interacting only with standard libraries, specified third-party libraries (`srt`, `tenacity`, `google-genai`), and other modules within the `translator` package itself.

### Subtask 2: Confirm Interface Stability
Verify that the public functions intended to be called by the web framework layer retain the signatures specified in the technical design. Specifically check the following functions in their respective modules (referencing the actual code in `src/translator/`):
*   `parser.parse_srt`: Expects `file_path: str`, `chunk_max_blocks: int`; returns `List[List[models.SubtitleBlock]]`.
*   `context_detector.detect_context`: Expects `sub: List[List[models.SubtitleBlock]]`, `speed_mode: str`, `genai_client: Optional[genai.client.Client]`, `config: models.Config`; returns `str`.
*   `chunk_translator.translate_all_chunks`: Expects `context: str`, `sub: List[List[models.SubtitleBlock]]`, `target_lang: str`, `speed_mode: str`, `genai_client: Optional[genai.client.Client]`, `config: models.Config`; returns `None` (modifies `sub` in place).
*   `reassembler.reassemble_srt`: Expects `sub: List[List[models.SubtitleBlock]]`; returns `bytes`.
*   `gemini_helper.init_genai_client`: Expects `config: models.Config`; returns `genai.client.Client`.

Ensure data types defined in `src/translator/models.py` (`SubtitleBlock`, `Config`) are used consistently according to these signatures.

### Subtask 3: Check Internal Interactions and Async Usage
Confirm that internal interactions between the `translator` modules are correctly implemented using relative imports (e.g., `from . import models`). Verify that the use of `asyncio` within `chunk_translator.py` (like `asyncio.TaskGroup` and `async def` functions) is self-contained and does not depend on an external event loop provided by the web framework. The calling layer (FastAPI) will handle running the top-level async function (`translate_all_chunks`).

### Subtask 4: Validate AI Client Handling
Review `context_detector.py` and `chunk_translator.py`. Confirm they correctly handle the `genai_client` parameter potentially being `None`. According to the design, if `speed_mode` is not `'mock'` and the client is needed but is `None`, these functions should raise an appropriate error (e.g., `RuntimeError`), which the calling web framework layer is expected to handle. Ensure they do not attempt to use methods on a `None` client object.

### Debugging and Verification
After reviewing and making any necessary minor adjustments for framework independence, you can perform a basic sanity check by running a script like `tests/manual/test_translator_logic.py`. This script should ideally import functions directly from the `translator` package, create mock `Config` objects, potentially mock the `genai.Client`, prepare sample `SubtitleBlock` data, and call the core functions (`parse_srt`, `detect_context`, `translate_all_chunks`, `reassemble_srt`) to ensure they execute without errors related to framework dependencies or incorrect internal logic. This isolates the translator logic from the web framework changes.