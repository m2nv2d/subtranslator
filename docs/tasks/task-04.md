**Task 4: Gemini API Client Helper**

**Project Context**

This project is a web application designed to translate subtitle files (`.srt`) using Google's Gemini large language model. To interact with the Gemini API, we need a standardized way to initialize the API client. This task involves creating a dedicated Python module (`src/gemini_helper.py`) that contains a function responsible solely for initializing this client using configuration details. This helper ensures the client initialization logic is centralized and reusable.

**Prerequisites**

*   Access to the project's codebase, specifically the `src` directory.
*   Python environment set up with necessary dependencies installed (including `google-genai`). You should have a way to install packages (e.g., using `uv` or `pip`).
*   Familiarity with Python functions, classes, imports, exception handling, and type hinting.
*   Need to reference other project files for specific definitions:
    *   `src/models.py`: Contains the `Config` data class definition, which holds the API key. Check this file for the exact structure and attribute name (e.g., `gemini_api_key`).
    *   `src/exceptions.py`: Contains custom exception classes. Check this file for the exact name of the exception to raise on initialization failure (e.g., `GenAIClientInitError`).

**Subtask 1: Create Module and Define Imports**

*   Create the file `src/gemini_helper.py`.
*   Import the necessary libraries and project modules:
    *   The `google.genai` library.
    *   The `Config` class from `src.models`. (Verify the exact path and class name by checking `src/models.py`).
    *   The specific custom exception for client initialization errors from `src.exceptions`. (Verify the exact path and class name by checking `src.exceptions.py`).

**Subtask 2: Implement the Initialization Function**

*   Define a function named `init_genai_client`.
*   This function should accept one argument: `config`, which is an instance of the `Config` class (add the appropriate type hint by importing from `src.models`).
*   The function should be type-hinted to return an instance of `genai.client.Client`.

**Subtask 3: Initialize the Gemini Client**

*   Inside the `init_genai_client` function, first retrieve the necessary API key from the `config` object passed into the function, then use it to initialize the client before passing it back to the caller.

*   Here is the correct way to initialize the client according to the official doc:

from google import genai
client = genai.Client(api_key="your_api_key")

**Subtask 4: Implement Error Handling**

*   Wrap the client initialization logic within a `try...except` block.
*   If an exception occurs, raise the specific custom exception defined for client initialization errors (e.g., `GenAIClientInitError` - confirm name in `src/exceptions.py`). Make sure to include context from the original exception when raising the custom one (e.g., `raise GenAIClientInitError("Failed to initialize Gemini Client") from e`).

**Subtask 5: Return the Client Instance**

*   If the client is initialized successfully without raising an exception, return the created `genai.client.Client` instance from the `init_genai_client` function.

**Subtask 6: Write a debug script**

*   Write a debug script to test the `init_genai_client` function.
*   The script should load the configuration, initialize the client, and print the client instance.
*   The script should be placed in the `tests/manual/` directory.
