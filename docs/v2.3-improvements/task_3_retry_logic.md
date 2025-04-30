# Task 3: Simplify Retry Logic (`translator/chunk_translator.py`)

## Project Context
The current implementation uses a custom decorator `@configurable_retry` in `src/translator/chunk_translator.py` to apply `tenacity` retry logic to the `_translate_single_chunk` function. This decorator dynamically inspects function arguments to find `settings` and `chunk_index`, adding complexity.

## Goal
Simplify the retry mechanism by removing the `@configurable_retry` decorator and applying `tenacity`'s `@retry` decorator directly to `_translate_single_chunk`, ensuring all necessary parameters (like `settings` and `chunk_index` for logging) are explicitly passed or accessible.

## Prerequisites
Access to `src/translator/chunk_translator.py` and familiarity with the `tenacity` library.

## Subtask 1: Remove Custom Decorator
- Delete the `configurable_retry` function definition from `src/translator/chunk_translator.py`.
- Remove the `@configurable_retry` usage above the `_translate_single_chunk` function definition.

## Subtask 2: Apply `tenacity.retry` Decorator Directly
- Import `retry`, `stop_after_attempt`, `wait_fixed`, `retry_if_exception_type`, `before_sleep_log` directly from `tenacity` at the top of the file if not already done.
- Apply the `@retry` decorator directly to `_translate_single_chunk`.
- Configure the `@retry` decorator parameters. These should be based on the `settings` object, which is already a parameter of `_translate_single_chunk`.
    - `stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS)`
    - `wait=wait_fixed(1)` (Or use a value from settings if configurable waiting is desired)
    - `retry=retry_if_exception_type(Exception)` (Keep retrying on general exceptions for now, consistent with previous logic)
    - `before_sleep`: This requires access to the logger and potentially `chunk_index`. Since the logger is typically module-level or class-level, it might be tricky to configure directly in the decorator if it needs dynamic info like `chunk_index`. Consider alternatives:
        - **Option A (Simpler Logging):** Use `before_sleep_log(logger, logging.INFO, exc_info=True)` but without the dynamic `chunk_index` in the pre-retry log message.
        - **Option B (Custom `before_sleep`):** Define a simple local function `log_before_retry(retry_state)` that accesses the logger and potentially extracts `chunk_index` from `retry_state.args` if tenacity provides it. `retry_state.args` should contain the arguments passed to the decorated function.
    - `reraise=True`

*Target Structure:*
```python
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep_log # or custom before_sleep
import logging

logger = logging.getLogger(__name__)

# Option B: Custom before_sleep function
def log_before_retry(retry_state):
    # Access logger and potentially retry_state.args to get chunk_index
    logger.warning(f"Retrying chunk {retry_state.args[0]} after error: {retry_state.outcome.exception()}, attempt {retry_state.attempt_number}")

# ... other imports and code ...

@retry(
    stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS), # Need to ensure settings is accessible
    wait=wait_fixed(1), # Or settings.RETRY_WAIT_SECONDS
    retry=retry_if_exception_type(Exception),
    # Option A: before_sleep=before_sleep_log(logger, logging.WARNING, exc_info=True),
    # Option B: before_sleep=log_before_retry,
    reraise=True
)
async def _translate_single_chunk(
    chunk_index: int,
    chunk: List[SubtitleBlock],
    system_prompt: str,
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    settings: Settings,
    # These might no longer be needed if settings is used directly in decorator
    # retry_max_attempts: int = None,
    # normal_model: str = None,
    # fast_model: str = None
) -> None:
    # ... existing function body ...
    # Logging within the function can still report success/final failure with chunk_index
    try:
        # ... translation logic ...
        logger.info(f"Chunk {chunk_index} processed successfully.")
    except Exception as e:
        logger.error(f"Chunk {chunk_index} failed after final retry attempt.")
        raise # Tenacity will handle reraising based on decorator config
```
**Note:** Accessing `settings.RETRY_MAX_ATTEMPTS` directly within the decorator definition might require `settings` to be available at the module level when the function is defined, or might require a different approach if settings are only available at runtime via function arguments. If `settings` is only available inside the function, the decorator needs to be configured dynamically, which complicates things again. The simplest path is if `settings` can be accessed or passed when the decorator is applied.

**Alternative if `settings` isn't available at definition time:** The `translate_all_chunks` function could wrap the call to `_translate_single_chunk` inside a `tenacity.AsyncRetrying` block, configuring it dynamically using the `settings` available there.

## Subtask 3: Test Retry Logic
- Modify tests or manually trigger scenarios where the Gemini API call within `_translate_single_chunk` would fail (e.g., temporarily use invalid API key, mock the API to raise exceptions).
- Verify that:
    - The function retries the specified number of times (`settings.RETRY_MAX_ATTEMPTS`).
    - The configured wait period occurs between retries.
    - Logging (especially the `before_sleep` log) indicates retries are happening.
    - If all retries fail, the exception is propagated correctly (e.g., `ChunkTranslationError` from `translate_all_chunks` or `RetryError` caught by the global handler).
    - If a retry succeeds, the process continues normally.

## Testing
- Unit tests for `_translate_single_chunk` and `translate_all_chunks`, potentially mocking the `genai_client` to simulate failures and successes.
- Integration tests simulating API errors and observing the retry behavior and final outcome (success or appropriate error response). 