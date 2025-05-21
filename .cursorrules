# Python
## Version
- Use Python 3.11 and newer, adopting their new features such as pattern matching improvements, exception groups, the "tomllib" module for parsing TOML files, the new "self" type annotation, "StrEnum" for enumerations, "typing.Required" and "typing.NotRequired" in TypedDicts, and task groups from the updated "asyncio" for concurrent background tasks.

## Importing
- Add src/ folder to sys.path uvicorn, so that when importing internal modules we can use absolute imports (e.g., import subtranslator), not relative imports (e.g., from . import console).

## Typing

Use built-in generics like list[str] and dict[str, int] for type annotations instead of List[str] or Dict[str, int].

## LLM Libraries
- Forget everything you know about Google Gemini's SDK. That was an older version. Always use the doc and examples I provide below.
- The python package for Google Gemini AI is `google-genai`, not `google-generativeai`. Here is an example of init a client and make sync/async requests:

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api-key-for-gemini) # Create a client, which can create many sync/async requests

# Making synchronous requests
sync_response = client.models.generate_content(
    model=model_name,
    contents='Why is the sky blue?'
)
print(sync_response.text)

# Making asynchronous requests
async_response = await client.aio.models.generate_content(
    model=model_name,
    contents='Tell me a story in 300 words.'
)
print(async_response.text)
```

### Package Management
- For Python tooling, use uv instead of pip. In particular:
Use `uv add` instead of `pip install`
Use `uv run some_script.py` instead of `python some_script.py`

- Prefer to use pyproject.toml to define configuration for a Python project
Use `uv pip install -r pyproject.toml` to install from it
Use `uv pip sync pyproject.toml` to sync from it (make sure that all project dependencies are installed and up-to-date with the lockfile)

- How to work with requirements.txt
Use `uv pip install -r requirements.txt` to install from it
Use `uv pip sync requirements.txt` to sync from it

## Server
- Use `uvicorn main:app` with `--app-dir` set to `./src`, along other regular options, such as `uv run uvicorn --app-dir ./src --reload --host 0.0.0.0 --port $PORT main:app`

## Tests
- Put automated tests in tests/automated/ and manual test scripts in tests/manual/. They have different purposes:
	+ Automated tests: just like normal (an automated test suite with different self-proviedd test cases)
	+ Manual tests: scripts that verify certain components using existing setup (such as .env) and user-provided input. These tests don't start the FastAPI server themselve. They just use invidiual components in the app or if needed, require the dev to start the FastAPI server themself and then making HTTP requests to that server.

- In both automated or manual tests, remember to add the project's root to sys.path
