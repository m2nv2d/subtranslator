# Task 3: Mock LLM Interaction Wrapper

## Project Context

This project is a Flask web application for translating subtitle files (`.srt`). A core component interacts with a Large Language Model (LLM) like Google Gemini to perform context detection and the actual translation of text chunks.

This specific task is to create a **mock** version of this LLM interaction component. This mock will simulate the *interface* and *basic behavior* (like delays) of the real component but will **not** make any actual external API calls. It will return predefined or pass-through data. This allows other parts of the application (context detection orchestration, chunk translation orchestration) to be developed and tested independently without requiring LLM API keys or incurring costs during early development stages.

## Prerequisites

*   You need to create/edit the file `src/services/mock_llm_helper.py`.
*   You need to know the structure of the `Config` data class. Its definition is located in the file `src/models.py`. You can assume this file exists and contains a data class named `Config`.
*   You will need the `asyncio` library for simulating delays and `typing.List` for type hinting.
*   Required imports for `src/services/mock_llm_helper.py`:
    ```python
    import asyncio
    from typing import List
    from src.models import Config # Assuming Config is in src.models
    ```

### Subtask 1: Define the Mock `LlmHelper` Class and Initializer

*   In `src/services/mock_llm_helper.py`, define a class named `LlmHelper`.
*   Implement the `__init__` method for this class.
    *   It should accept `self` and `config: Config` as arguments.
    *   The initializer can simply store the `config` object (e.g., `self.config = config`) or do nothing with it, as the mock functionality won't depend on the configuration values.

```python
# Example structure:
class LlmHelper:
    def __init__(self, config: Config):
        # Store config if needed, or just pass
        self.config = config # Or simply: pass
```

### Subtask 2: Implement Mock `detect_context` Method

*   Add an `async` method named `detect_context` to the `LlmHelper` class.
*   It should accept `self` and `text: str` as arguments.
*   This method should **not** perform any complex logic or API calls.
*   It should simply return a fixed, hardcoded string: `"mock context"`.

```python
# Example structure:
class LlmHelper:
    # ... __init__ ...

    async def detect_context(self, text: str) -> str:
        # No actual processing of 'text' needed for mock
        return "mock context"
```

### Subtask 3: Implement Mock `translate_chunk` Method

*   Add an `async` method named `translate_chunk` to the `LlmHelper` class.
*   It should accept the following arguments:
    *   `self`
    *   `context: str`
    *   `target_lang: str`
    *   `speed_mode: str`
    *   `chunk_index: int`
    *   `lines: List[str]`
*   This method should simulate the time it takes for a real API call. Use `await asyncio.sleep(2)` to pause execution for 2 seconds.
*   After the delay, the method should return the **exact same list of strings** it received in the `lines` argument. It should not modify the content of the strings.

```python
# Example structure:
class LlmHelper:
    # ... __init__ ...
    # ... detect_context ...

    async def translate_chunk(self, context: str, target_lang: str, speed_mode: str, chunk_index: int, lines: List[str]) -> List[str]:
        # Simulate API call delay
        await asyncio.sleep(2)
        # Return the original lines unmodified
        return lines
```
