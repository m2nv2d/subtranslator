## Task 5: Introduce Pydantic Models

### Project Context
This project is a web application, recently ported from Flask to FastAPI, that translates subtitle files (`.srt`). It uses the Google Generative AI SDK for translation, orchestrated by a core `translator` package. Key components include configuration loading (`src/config_loader.py`), SRT parsing (`src/translator/parser.py`), context detection (`src/translator/context_detector.py`), chunk translation (`src/translator/chunk_translator.py`), and reassembly (`src/translator/reassembler.py`). The main FastAPI application logic resides in `src/main.py`, serving an HTML frontend (`src/templates/index.html` with `src/static/js/app.js`).

### Prerequisites
-   Familiarity with Pydantic, especially `BaseModel` and `pydantic-settings` for environment variable management.
-   Access to the project codebase, particularly `src/translator/models.py`, `src/config_loader.py`, `src/main.py`, and the original technical design document detailing the `.env` structure and existing `Config` model.
-   A working Python environment with project dependencies installed (including `pydantic` and `pydantic-settings`).

### Subtask 1: Configuration Model with Pydantic Settings
-   **Goal:** Replace the current configuration loading mechanism with Pydantic's `BaseSettings`.
-   **Action:** Examine the existing `Config` data class defined in `src/translator/models.py` and the expected `.env` file format (by inspecting a sample `.env.example` file).
-   Implement a new Pydantic `BaseSettings` model (consider placing it in a dedicated `src/core/config.py` or similar, or adapt `src/translator/models.py`). This model should replicate the fields, types, default values, and validation logic previously handled by `src/config_loader.py:load_config()`. Pay attention to:
    -   Required fields (`AI_PROVIDER`, `AI_API_KEY`, `FAST_MODEL`, `NORMAL_MODEL` - conditionally required based on `AI_PROVIDER`).
    -   Optional fields with defaults and specific validation rules (`TARGET_LANGUAGES`, `CHUNK_MAX_BLOCKS`, `RETRY_MAX_ATTEMPTS`, `LOG_LEVEL`). Use Pydantic validators for type checking, range constraints, and custom parsing (e.g., comma-separated strings).
-   Refactor the application startup in `src/main.py` (and potentially any future dependency injection functions) to instantiate and use this new Pydantic settings model instead of calling `config_loader.load_config()`. The original `src/config_loader.py` might become redundant.
-   Ensure appropriate error handling during settings instantiation (Pydantic raises `ValidationError`).

### Subtask 2: Standardized Error Response Model
-   **Goal:** Define and utilize a Pydantic model for consistent JSON error responses.
-   **Action:** Review the error handling logic in `src/main.py` (specifically the `@app.exception_handler` functions) and the frontend JavaScript code (`src/static/js/app.js`) which expects an error structure like `{"error": "..."}`.
-   Define a simple Pydantic `BaseModel` (e.g., `ErrorDetail`) to represent this error structure.
-   Modify the exception handlers in `main.py` to return FastAPI's `JSONResponse` with content generated from an instance of this `ErrorDetail` model, or alternatively, use FastAPI's `HTTPException` where the `detail` parameter is structured according to (or is an instance of) this model.

### Subtask 3: Update Testing
-   **Goal:** Ensure the changes are adequately tested.
-   **Action (Automated):**
    -   Update or create unit tests for the new Pydantic settings model, covering various scenarios: valid `.env`, missing required variables, invalid values for optional variables, correct default value application.
-   **Action (Manual):**
    -   Create or update manual testing scripts/procedures in `tests/manual`. Verify that the application correctly loads configuration from a standard `.env` file after the changes.
    -   Manually trigger different error conditions (e.g., upload invalid file, use incorrect API key if possible, cause internal server error) and inspect the HTTP response body in the browser's developer tools or using tools like `curl` to confirm the error JSON matches the defined `ErrorDetail` structure.