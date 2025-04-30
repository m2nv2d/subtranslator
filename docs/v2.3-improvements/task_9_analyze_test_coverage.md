# Task 9: Analyze Test Coverage

## Project Context
The project includes a `tests/` directory with `automated` and `manual` subdirectories, but the effectiveness and coverage of the automated tests haven't been formally assessed. Understanding the current state of testing is vital before significant refactoring or feature additions.

## Goal
Analyze the existing automated test suite using a coverage tool (`pytest-cov`) to determine which parts of the `src` codebase are exercised by tests and identify key areas lacking coverage.

## Prerequisites
- Access to the `tests/automated/` directory and the `src/` directory.
- `pytest` and `pytest-cov` installed in the development environment.
- Understanding of code coverage concepts (lines, statements, branches).

## Subtask 1: Install Coverage Tool
- Ensure `pytest-cov` is added as a development dependency.
  ```bash
  # Run this if pytest-cov is not already in pyproject.toml [tool.uv.dev-dependencies]
  uv add pytest-cov --dev
  # Ensure dependencies are synced
  uv pip sync 
  ```

## Subtask 2: Run Coverage Analysis
- Execute `pytest` from the project root directory, enabling coverage reporting for the `src` directory and specifying the location of the automated tests.
  ```bash
  uv run pytest --cov=src tests/automated/
  # Optional: Generate an HTML report for easier visualization
  # uv run pytest --cov=src --cov-report=html tests/automated/
  ```

## Subtask 3: Review Coverage Report
- Examine the coverage report generated in the terminal (or the HTML report if created, usually in an `htmlcov/` directory).
- Note the following:
    - **Overall Coverage Percentage:** The total percentage of statements/lines covered across `src`.
    - **Per-File Coverage:** The coverage percentage for each individual file within `src` (e.g., `src/main.py`, `src/routers/translate.py`, `src/translator/parser.py`, etc.).
    - **Missing Lines/Branches:** Identify specific lines or conditional branches marked as uncovered by the report.

## Subtask 4: Identify Key Coverage Gaps
- Based on the report and application knowledge, identify critical areas with low or no coverage. Pay attention to:
    - **Core Logic (`src/translator/`):** Are parsing, context detection, chunking, translation orchestration (`translate_all_chunks`), and reassembly functions well-tested with various inputs and edge cases?
    - **API Endpoints (`src/routers/`):** Are the `/` and `/translate` endpoints tested using FastAPI's `TestClient`? Do tests cover:
        - Successful requests with different parameters (`target_lang`, `speed_mode`).
        - Input validation errors (invalid file type, missing language, invalid language, invalid speed mode).
        - Correct handling of different `speed_mode` values (mock, fast, normal), potentially mocking the Gemini client.
        - Correct file streaming response on success.
    - **Error Handling (`src/main.py`, `src/core/errors.py`):** Are the custom exception handlers triggered and tested? Do they produce the expected status codes and response formats?
    - **Configuration & Dependencies (`src/core/`):** Is configuration loading (`config.py`) and dependency logic (`dependencies.py`) tested?
    - **Edge Cases & Failures:** Are scenarios like Gemini API failures (requiring mocking), file I/O errors, or empty SRT files tested?

## Subtask 5: Document Findings and Recommendations
- Create a brief summary document (this file can be updated, or create a separate `test_coverage_analysis.md`).
- **Document:**
    - The overall coverage percentage.
    - List key modules/files with significantly low coverage.
    - List specific critical functionalities or error paths that appear untested.
- **Recommend:**
    - Prioritize writing tests for uncovered core logic (`translator` functions).
    - Recommend adding comprehensive API tests using `TestClient` for `routers/translate.py`.
    - Suggest tests for specific error handling paths.

## Testing
- This task itself is an analysis task. The "testing" involved is running the coverage tool and interpreting its results accurately. 