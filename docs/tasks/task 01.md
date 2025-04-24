# Task 1: Foundational Models & Configuration

## Objective

Implement the basic data structures (models.py), custom exceptions (exceptions.py), and the configuration loading mechanism (config_loader.py) along with its unit tests.

## Instructions

### Phase 1: Define Models and Exceptions (No Tests Required for these basic structures)

File: src/models.py

Implement: Define two data classes based on the technical design document.

Class SubtitleBlock:

Fields: index: int, start: datetime, end: datetime, content: str, translated_content: Optional[str] = None. Ensure correct type hints, including from datetime import datetime and from typing import Optional.

Class Config:

Fields: gemini_api_key: str, target_languages: List[str], chunk_max_blocks: int, retry_max_attempts: int, log_level: str. Ensure correct type hints, including from typing import List.

File: src/exceptions.py

Implement: Define the custom exception classes as specified in the technical design.

Classes: ValidationError, ParsingError, ContextDetectionError, ChunkTranslationError, ApiHelperError.

Behavior: Each class should inherit directly from the base Exception. No additional logic is required within these classes for now.

### Phase 2: Implement Configuration Loader Tests

File: tests/automated/unit/test_config_loader.py

Implement: Unit tests for the load_config function (which you will implement after writing these tests).

Dependencies: You will need to mock environment variables (os.environ) or the behavior of python-dotenv. You may also need to mock logging and potentially sys.exit. Use unittest.mock.patch or pytest fixtures with monkeypatching.

Test Cases:

Test Success: Simulate an environment where GEMINI_API_KEY and all optional variables (TARGET_LANGUAGES, CHUNK_MAX_BLOCKS, RETRY_MAX_ATTEMPTS, LOG_LEVEL) are set. Verify that load_config returns a Config object with the correct values and types.

Test Defaults: Simulate an environment where only the required GEMINI_API_KEY is set. Verify that load_config returns a Config object where the optional variables have their specified default values (check technical design: TARGET_LANGUAGES=["vi","fr"], CHUNK_MAX_BLOCKS=100, RETRY_MAX_ATTEMPTS=6, LOG_LEVEL="INFO"). Ensure TARGET_LANGUAGES is correctly parsed from a comma-separated string in the mock env var into a List[str].

Test Missing Required: Simulate an environment where GEMINI_API_KEY is not set. Verify that calling load_config results in a log message indicating the error (mock logging.error or similar) and attempts to exit (mock sys.exit and assert it was called, or expect a specific custom exception if you prefer that for testability, though the design specifies log and exit).

Test Type Conversion: Ensure CHUNK_MAX_BLOCKS and RETRY_MAX_ATTEMPTS are correctly loaded as integers, even if provided as strings in the environment. Ensure TARGET_LANGUAGES is correctly parsed from a string like "en,es,de" into ["en", "es", "de"].

### Phase 3: Implement Configuration Loader Logic

File: src/config_loader.py

Implement: The load_config() function.

Dependencies: Import os, logging, sys, dotenv. Import Config from src.models.

Behavior:

Use dotenv.load_dotenv() to load variables from a .env file (which should be located in the project root, outside the src directory).

Retrieve environment variables using os.getenv().

Validation: Check if GEMINI_API_KEY is present. If not, log an error message detailing the missing variable and call sys.exit(1).

Defaults & Types:

Retrieve TARGET_LANGUAGES. If present, split the comma-separated string into a List[str]. If not present, use the default ["vi", "fr"].

Retrieve CHUNK_MAX_BLOCKS. If present, convert to int. If not present or conversion fails, use default 100. Handle potential ValueError during conversion gracefully (e.g., log a warning and use default).

Retrieve RETRY_MAX_ATTEMPTS. If present, convert to int. If not present or conversion fails, use default 6. Handle potential ValueError gracefully.

Retrieve LOG_LEVEL. If not present, use default "INFO". Ensure the value is treated as a string.

Return: Instantiate and return a Config object (from src.models) populated with the retrieved or default values.

Reference: You will need to refer to src.models.py to know the structure of the Config class you need to return.

Execute these phases in order. Ensure the tests in Phase 2 pass after completing the implementation in Phase 3.
