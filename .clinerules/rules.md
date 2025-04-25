# Development Tooling Rules

- For Python tooling, use uv instead of pip. In particular:
Use `uv add` instead of `pip install`
Use `uv run some_script.py` instead of `python some_script.py`

- Prefer to use pyproject.toml to define configuration for a Python project
Use `uv pip install -r pyproject.toml` to install from it
Use `uv pip sync pyproject.toml` to sync from it (make sure that all project dependencies are installed and up-to-date with the lockfile)

- How to work with requirements.txt
Use `uv pip install -r requirements.txt` to install from it
Use `uv pip sync requirements.txt` to sync from it

- Put automated tests in tests/automated/ and manual test scripts in tests/manual/.

- When you generate any test code (automated or manual) inside the tests/ directory (including subfolders), remember to add the project's root to sys.path to allow 'from src import ...'
