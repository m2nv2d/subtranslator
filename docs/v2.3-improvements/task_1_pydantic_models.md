# Task 1: Improve Request Validation with Pydantic Models

## Project Context
This task focuses on improving the request handling and validation for the `/translate` API endpoint within the FastAPI application. Currently, parameters like `target_lang` and `speed_mode` are accepted using basic `Form` fields, and validation logic is mixed within the endpoint function. The goal is to leverage Pydantic's validation capabilities directly within the endpoint definition where possible, making the code cleaner, more robust, and improving OpenAPI documentation.

## Goal
Refactor the `POST /translate` endpoint in `src/routers/translate.py` to use Pydantic validation features for its form parameters, specifically for `speed_mode`. Maintain the existing mechanism for file uploads (`UploadFile`) and runtime validation for `target_lang`.

## Prerequisites
Ensure the following libraries are available: `fastapi`, `pydantic`. You will need access to the existing code, particularly `src/routers/translate.py` and `src/core/config.py` (for accessing `settings.TARGET_LANGUAGES`).

## Subtask 1: Define Allowed Values for `speed_mode`
In `src/routers/translate.py` (or a potential future shared models file like `src/routers/models.py`), define a way to represent the allowed values for the `speed_mode` parameter. Using `typing.Literal` is a straightforward approach for this fixed set of values.
```python
# Example (to be added near imports in src/routers/translate.py or a models file)
from typing import Literal

AllowedSpeedModes = Literal["normal", "fast", "mock"]
```

## Subtask 2: Update `/translate` Endpoint Signature
Modify the signature of the `translate_srt` function in `src/routers/translate.py`:
- Change the type annotation for the `speed_mode` parameter from `str` to the `AllowedSpeedModes` Literal defined in Subtask 1.
- Update the default value for `speed_mode` if necessary (e.g., if using an Enum later, otherwise the string default is fine with Literal).

*Current:*
```python
async def translate_srt(
    # ... other parameters
    speed_mode: str = Form("normal")
):
    # ...
```

*Target:*
```python
async def translate_srt(
    # ... other parameters
    speed_mode: AllowedSpeedModes = Form("normal") # Use the Literal type
):
    # ...
```
FastAPI will now automatically validate that the provided `speed_mode` form field is one of `"normal"`, `"fast"`, or `"mock"`. If not, it will return a 422 Unprocessable Entity response.

## Subtask 3: Adapt Endpoint Logic
Inside the `translate_srt` function:
- **Remove** the manual validation block that checks if `speed_mode` is valid. This is now handled automatically by FastAPI based on the type hint.
- **Keep** the manual validation block that checks `target_lang` against the dynamically loaded `settings.TARGET_LANGUAGES`. This check is still necessary because the allowed languages are not known statically.

*Code to remove (example):*
```python
# Example - Remove similar logic for speed_mode validation if it exists
# if speed_mode not in ["normal", "fast", "mock"]:

#     logger.warning(f"Translation request failed: Invalid speed mode '{speed_mode}'.")

#     raise ValidationError(f"Invalid speed mode: {speed_mode}. Available: normal, fast, mock")

```

## Subtask 4: Verify No Changes Needed for Response or Settings
- **Response:** Confirm that the endpoint should still return `StreamingResponse` on success for direct file download. No Pydantic response model is needed for the success path of this specific endpoint. Error responses are already handled by the existing exception handlers using the `ErrorDetail` model (`src/core/errors.py`).
- **Settings Validation:** Reconfirm that the existing Pydantic validators within the `Settings` model in `src/core/config.py` (especially for `TARGET_LANGUAGES`) remain appropriate and do not require changes as part of this task.

## Testing
- Manually test the `/translate` endpoint (e.g., using `curl` or the web UI) or update automated tests:
    - Send requests with invalid `speed_mode` values (e.g., `"medium"`) and verify that a 422 status code and informative error message are returned automatically by FastAPI.
    - Send requests with valid `speed_mode` but invalid `target_lang` values and verify that the existing manual validation triggers, resulting in a 400 status code (due to the `ValidationError` handler).
    - Send valid requests and ensure they are processed correctly, returning the translated file.
- Check the auto-generated OpenAPI documentation (e.g., at `/docs`) to see how the `speed_mode` parameter is now documented with its allowed values. 