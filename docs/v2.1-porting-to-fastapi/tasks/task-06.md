# Task 6: Introduce Routers (`APIRouter`)

## Project Context
This project is a web application, recently ported from Flask to FastAPI, designed to translate subtitle files (`.srt`). The core translation logic resides in the `src/translator/` package. The main FastAPI application instance and current route definitions (`GET /` and `POST /translate`) are located in `src/main.py`. The goal of this task is to organize the routes using FastAPI's `APIRouter`.

## Prerequisites
- The project structure includes `src/main.py` containing the `FastAPI` app instance and route handlers for `/` and `/translate`.
- Familiarity with FastAPI's `APIRouter` concept for organizing routes.
- The `src/translator/` package contains the necessary business logic modules.

## Subtask 1: Create the Router File and Move Routes
- Create a new directory `src/routers/`.
- Inside `src/routers/`, create a new Python file, for instance, `translate.py`.
- In `src/routers/translate.py`, import `APIRouter` from `fastapi` and instantiate it (e.g., `router = APIRouter()`).
- Locate the route handler functions for `GET /` and `POST /translate` within the current `src/main.py`. Examine their function signatures, including parameters (like `request: Request`, `file: UploadFile`, `target_lang: str`, `speed_mode: str`, and any injected dependencies via `Depends`) and return types (`HTMLResponse`, `StreamingResponse`, `HTTPException`).
- Move the *complete implementation* of these two route handler functions (including their decorators like `@app.get("/")` or `@app.post("/translate")`) from `src/main.py` into `src/routers/translate.py`.
- Adapt the decorators to use the new `router` instance (e.g., `@router.get("/")`).
- Ensure all necessary imports previously used by these route handlers in `src/main.py` (e.g., `HTMLResponse`, `StreamingResponse`, `UploadFile`, `Form`, `HTTPException`, functions/models from `src/translator`, `pathlib`, `io`, `shutil`, `tempfile`, `os`, `secure_filename`, any dependency functions like `get_config` or `get_genai_client` if implemented) are now correctly imported within `src/routers/translate.py`. Also ensure the `genai_client` and `config` objects, if accessed globally in `main.py` previously, are now accessed appropriately (e.g., via dependencies) within the router functions. Reference the existing `src/main.py` for the exact imports needed.

## Subtask 2: Include the Router in the Main Application
- In `src/main.py`, remove the original route handler function definitions and their associated decorators (`@app.get("/")`, `@app.post("/translate")`) that were moved in Subtask 1.
- Import the `router` instance created in `src/routers/translate.py` into `src/main.py`.
- Use `app.include_router()` in `src/main.py` to incorporate the routes defined in the imported router into the main FastAPI application instance. Ensure this inclusion happens after the main `app` instance is created.

## Subtask 3: Verification
- **Automated Tests:** If an automated test suite exists using FastAPI's `TestClient` against the main `app` instance (from `src/main.py`), ensure these tests still pass. The tests should confirm that requests to `GET /` and `POST /translate` are routed correctly and produce the expected responses, even though the implementation now resides in a separate router file. No changes to the tests themselves should be necessary if they target the main `app`.
- **Manual Tests:**
    - Start the FastAPI server using the `dev.sh` script.
    - Manually test the `POST /translate` endpoint running `tests/manual/test_translate_api.sh` Check server logs for any errors during the request processing.