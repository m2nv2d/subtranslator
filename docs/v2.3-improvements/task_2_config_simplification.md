# Task 2: Simplify Configuration Loading (`core/config.py`)

## Project Context
The current configuration loading in `src/core/config.py` uses `pydantic-settings` but includes custom validation logic (`validate_target_languages`) and a helper function (`get_settings`) that might be overly complex. This task aims to simplify this by leveraging more of `pydantic-settings`' built-in capabilities.

## Goal
Refactor the `Settings` model and its loading mechanism in `src/core/config.py` to:
1.  Potentially simplify the parsing of the `TARGET_LANGUAGES` environment variable.
2.  Simplify or remove the `get_settings` helper function by relying on `pydantic-settings`' standard `.env` discovery.

## Prerequisites
Access to `src/core/config.py` and understanding of how `pydantic-settings` loads variables from `.env` files and environment variables.

## Subtask 1: Analyze `TARGET_LANGUAGES` Parsing
- Review the `@model_validator(mode="before")` for `validate_target_languages`.
- Determine if the comma-separated string format for `TARGET_LANGUAGES` in the environment or `.env` file is fixed.
- Investigate if Pydantic or `pydantic-settings` offers a built-in way to handle comma-separated strings into a `List[str]`. Possibilities include:
    - Using `pydantic.Json` if the env var is a JSON list string (unlikely based on current code).
    - Using a custom `field_validator` specifically for `TARGET_LANGUAGES` (might be simpler than the current `model_validator`).
    - Potentially relying on `pydantic-settings`'s built-in parsing if the `NoDecode` annotation is removed (need to verify its purpose and impact).

## Subtask 2: Refactor `TARGET_LANGUAGES` Validation
- Based on the analysis, refactor the validation:
    - **Option A (If built-in parsing works):** Remove the `NoDecode` annotation and the `validate_target_languages` validator. Rely on standard parsing and potentially add a `field_validator` just to ensure the list is not empty (as the current `@field_validator("TARGET_LANGUAGES")` does).
    - **Option B (Simpler custom validator):** Replace the `model_validator` with a simpler `field_validator` that takes the raw string input (if `NoDecode` is kept) or the initially parsed value (if `NoDecode` is removed) and performs the split and validation.
- Ensure the default value (`["Vietnamese", "French"]`) is applied correctly if the environment variable is missing or empty.

## Subtask 3: Simplify `get_settings` Function
- Review the `get_settings` function.
- The current logic manually finds the project root and constructs the `.env` path.
- `pydantic-settings` typically finds `.env` files automatically by searching upwards from the execution directory or based on the `env_file` setting in `SettingsConfigDict`.
- **Action:** Remove the manual path finding logic in `get_settings`. Simplify it to directly instantiate `Settings()`: `settings = Settings()`. `pydantic-settings` should handle finding the `.env` file specified in `model_config`.
- **Dependency Injection Context:** Note that FastAPI dependency injection (`Depends(get_settings)`) usually manages the lifetime and caching of the settings instance, so the primary role of `get_settings` becomes just instantiation.

## Subtask 4: Test Configuration Loading
- Ensure the `.env` file is placed in the project root directory (where `uvicorn` or tests are run from) so `pydantic-settings` can find it automatically.
- Run the application or tests and verify:
    - `TARGET_LANGUAGES` are loaded correctly from the `.env` file (if present) or environment variables.
    - The default languages are used if the variable is not set or is empty.
    - Other settings (API keys, model names) are loaded correctly.
- Intentionally provide invalid or empty values for `TARGET_LANGUAGES` in `.env` to ensure defaults are applied.

## Testing
- Primarily involves verifying application startup and behavior:
    - Check logs for any errors during settings initialization.
    - Access the UI (`/`) and verify the language dropdown is populated correctly based on `.env` or defaults.
    - Make API calls (`/translate`) and ensure the `target_lang` validation uses the correct list of languages loaded into `settings.TARGET_LANGUAGES`.
    - Check that the `get_application_settings` dependency in `src/core/dependencies.py` still works correctly with the simplified `get_settings` function. 