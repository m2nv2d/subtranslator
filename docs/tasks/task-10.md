# Task 10: Update Technical Document

Your task is to compare the provided Technical Design Document at `docs/TECHNICAL_DESIGN.md` (specifically the "Detailed Component Design" and related sections) against the actual Python code found in the corresponding files within the project's `src/` directory. Identify any discrepancies between the design document's description and the actual implementation in the code. Based on these discrepancies, update the Technical Design Document at `docs/TECHNICAL_DESIGN.md` so it accurately reflects the current state of the codebase.

**DO NOT suggest any changes to the Python code itself.** Your output must only contain suggested modifications to the text of the Technical Design Document.

**Task Breakdown:**

**Task 1: Review `src/config_loader.py`**

1.  Locate and read the code in `project_root/src/config_loader.py`.
2.  Compare the implementation of the `load_config` function against its description in the "Detailed Component Design > src/config_loader.py" section of the design document.
3.  Verify:
    *   Does the function exist with the name `load_config`?
    *   Does it return an object compatible with the `Config` model described in `src/models.py` (check return type hints if available, or infer from usage)?
    *   Does it load `GEMINI_API_KEY`? How is its absence handled (e.g., log and exit, raise error)?
    *   Does it load `TARGET_LANGUAGES`? How is it parsed (comma-separated string to `List[str]`)? What is the actual default value in the code?
    *   Does it load `CHUNK_MAX_BLOCKS`? Is it an `int`? What is the actual default value?
    *   Does it load `RETRY_MAX_ATTEMPTS`? Is it an `int`? What is the actual default value?
    *   Does it load `LOG_LEVEL`? Is it a `str`? What is the actual default value?
    *   Are there any other configuration variables loaded that are not mentioned in the design?
4.  Based on any discrepancies found, update the description of `src/config_loader.py` in `docs/TECHNICAL_DESIGN.md`.

**Task 2: Review `src/exceptions.py`**

1.  Locate and read the code in `project_root/src/exceptions.py`.
2.  Compare the custom exception classes defined in the file against the list provided in the "Detailed Component Design > src/exceptions.py" section of the design document.
3.  Verify:
    *   Does each exception listed in the design document exist in the code with the exact same name?
    *   Are there any additional custom exceptions defined in the code that are *not* listed in the design document?
    *   Are the inheritance relationships (`Exception`) correctly described?
4.  Update the list of exceptions in `docs/TECHNICAL_DESIGN.md` to match the code.

**Task 3: Review `src/models.py`**

1.  Locate and read the code in `project_root/src/models.py`.
2.  Compare the data classes (`SubtitleBlock`, `Config`) defined in the code against their descriptions in the "Detailed Component Design > src/models.py" section.
3.  For `SubtitleBlock`:
    *   Verify the existence and names of the fields (`index`, `start`, `end`, `content`, `translated_content`).
    *   Verify the data types (or type hints) for each field (`int`, `datetime`, `str`, `Optional[str]`).
    *   Verify default values (e.g., `translated_content=None`).
    *   Are there any extra fields not mentioned in the design?
4.  For `Config`:
    *   Verify the existence and names of the fields (`gemini_api_key`, `target_languages`, `chunk_max_blocks`, `retry_max_attempts`, `log_level`).
    *   Verify the data types (`str`, `List[str]`, `int`, `int`, `str`).
    *   Are there any extra fields not mentioned in the design?
5.  Update the descriptions of these data classes in `docs/TECHNICAL_DESIGN.md`.

**Task 4: Review `src/parser.py`**

1.  Locate and read the code in `project_root/src/parser.py`.
2.  Compare the implementation of the `parse_srt` function against its description in the "Detailed Component Design > src/parser.py" section.
3.  Verify:
    *   Does the function exist with the name `parse_srt`?
    *   Do the parameters match the design (`file_path: str`, `chunk_max_blocks: int`)? Note: The design says `file_path: str` but the description implies it receives a file object from Flask (`request.files.get('file')`). Check the *actual* parameter type used in the code. If it takes a Flask `FileStorage` object or similar, the design doc needs updating.
    *   Does the return type match `List[List[SubtitleBlock]]` (check type hints or infer)?
    *   Does the code perform validation (e.g., `.srt` extension check, file size check)? What is the actual size limit used?
    *   Does it raise `ValidationError` on failure? Does it raise any other exceptions (e.g., `ParsingError`)?
    *   Does it use the `srt` library (`import srt`)?
    *   Does it map subtitle objects to `SubtitleBlock` instances?
    *   Does it split the blocks into chunks based on `chunk_max_blocks`?
4.  Update the description of `src/parser.py` in `docs/TECHNICAL_DESIGN.md`, paying close attention to the actual parameter type for the file input.

**Task 5: Review `src/gemini_helper.py`**

1.  Locate and read the code in `project_root/src/gemini_helper.py`.
2.  Compare the implementation of the `init_genai_client` function against its description in the "Detailed Component Design > src/gemini_helper.py" section.
3.  Verify:
    *   Does the function exist with the name `init_genai_client`?
    *   Does it accept a `config: models.Config` parameter?
    *   Does it return a `genai.client.Client` instance (or whatever the `google-genai` SDK actually calls its client)? Check type hints or inferred type.
    *   Does it raise `GenAIClientInitError` on failure? Does it raise any other specific exceptions during initialization?
4.  Update the description of `src/gemini_helper.py` in `docs/TECHNICAL_DESIGN.md`

**Task 6: Review `src/context_detector.py`**

1.  Locate and read the code in `project_root/src/context_detector.py`.
2.  Compare the implementation of the `detect_context` function against its description in the "Detailed Component Design > src/context_detector.py" section.
3.  Verify:
    *   Does the function exist with the name `detect_context`?
    *   Do the parameters match the design (`sub: List[List[SubtitleBlock]]`, `speed_mode: str`, `genai_client: genai.client.Client`, `config: models.Config`)? Are the types correct? Is `genai_client` truly optional or always required based on the code logic?
    *   Does it return a `str`?
    *   Does the logic correctly branch based on `speed_mode` ("mock", "fast", "normal")?
    *   Does the "mock" mode simply return a string without API calls?
    *   Does the "fast"/"normal" mode use the passed `genai_client`?
    *   Is `tenacity` used for retries? Is it configured using `config.retry_max_attempts`? Is the retry applied to the correct part of the code (e.g., an internal helper or the main function)?
    *   Does it extract text from the first chunk? Approximately how many lines/blocks does it actually use?
    *   Does it raise `ContextDetectionError` on failure after retries? Does it raise any other exceptions?
4.  Update the description of `src/context_detector.py` in `docs/TECHNICAL_DESIGN.md`

**Task 7: Review `src/chunk_translator.py`**

1.  Locate and read the code in `project_root/src/chunk_translator.py`.
2.  Compare the implementation of `translate_all_chunks` and `_translate_single_chunk` against their descriptions in the "Detailed Component Design > src/chunk_translator.py" section.
3.  For `translate_all_chunks`:
    *   Does the function exist? Is it `async`?
    *   Do the parameters match (`context: str`, `sub: List[List[SubtitleBlock]]`, `target_lang: str`, `speed_mode: str`, `genai_client: genai.client.Client`, `config: models.Config`)? Are the types correct? Is `genai_client` truly optional?
    *   Does it return `None`?
    *   Does it use `asyncio.gather` to run `_translate_single_chunk` concurrently?
    *   Does it raise `ChunkTranslationError` if any task fails?
4.  For `_translate_single_chunk`:
    *   Does the function exist? Is it `async`? Does the name start with an underscore (`_`)?
    *   Do the parameters match (`context: str`, `chunk_index: int`, `chunk: List[SubtitleBlock]`, `target_lang: str`, `speed_mode: str`, `genai_client: genai.client.Client`, `config: models.Config`)? Are the types correct? Is `genai_client` optional?
    *   Does it return `None`?
    *   Does the logic branch based on `speed_mode` ("mock", "fast", "normal")?
    *   Does the "mock" mode avoid API calls and copy original content to `translated_content`? Does it include a delay (`asyncio.sleep`)?
    *   Is `tenacity` used for retries on this function or an internal call? Is it configured using `config.retry_max_attempts`?
    *   Does the code *modify* the `SubtitleBlock` objects within the passed `chunk` list by setting the `translated_content` field (for non-mock modes, even if the LLM call itself isn't implemented, the structure to modify should be there)?
    *   Does it raise `ChunkTranslationError` on failure after retries? Does it raise any other exceptions?
5.  Update the descriptions of these functions in `docs/TECHNICAL_DESIGN.md`

**Task 8: Review `src/reassembler.py`**

1.  Locate and read the code in `project_root/src/reassembler.py`.
2.  Compare the implementation of the `reassemble_srt` function against its description in the "Detailed Component Design > src/reassembler.py" section.
3.  Verify:
    *   Does the function exist with the name `reassemble_srt`?
    *   Does it accept `sub: List[List[SubtitleBlock]]` as a parameter?
    *   Does it return `bytes`?
    *   Does the logic iterate through the chunks and blocks?
    *   Does it format the output according to the SRT standard (index, timestamps, content)? Does it use the `translated_content` field?
    *   Does it encode the final string to bytes?
4.  Update the description of `src/reassembler.py` in `docs/TECHNICAL_DESIGN.md`

**Task 9: Review `src/app.py` (Flask App and Routes)**

1.  Locate and read the code in `project_root/src/app.py`.
2.  Compare the setup, error handling, and route implementations against the descriptions in "Detailed Component Design > src/app.py".
3.  Verify Setup:
    *   Is config loaded using `config_loader.load_config()`?
    *   Is logging configured? How (e.g., basicConfig)? Does it use `config.log_level`?
    *   Is the Flask app instance created (`app = Flask(__name__)`)?
    *   Is the `genai_client` initialized using `gemini_helper.init_genai_client(config)`? Is it stored globally/module-level? Is there error handling around this initialization? Does the app halt/log/set client to `None` on failure as described?
4.  Verify Error Handling:
    *   Are there `@app.errorhandler` decorators for the custom exceptions listed in the design (`ValidationError`, `ParsingError`, `ContextDetectionError`, `ChunkTranslationError`, potentially `GenAI...Error`)?
    *   Is there an error handler for `tenacity.RetryError`?
    *   Is there a generic `Exception` handler?
    *   Do these handlers return `jsonify({"error": ...})` and the correct HTTP status codes as specified in the design?
5.  Verify `GET /` Route:
    *   Does the route exist?
    *   Does it call `render_template('index.html', languages=config.target_languages)`?
6.  Verify `POST /translate` Route:
    *   Does the route exist and accept `POST` requests?
    *   Does it check if `genai_client` is `None` and return a 503 JSON error if so?
    *   Does it retrieve the file (`request.files.get('file')`), `target_lang` (`request.form.get('target_lang')`), and `speed_mode` (`request.form.get('speed_mode', 'normal')`)?
    *   Does it validate `target_lang` against `config.target_languages`?
    *   Does it call `parser.parse_srt`? What argument is *actually* passed for the file (e.g., the `FileStorage` object, or a temporary path)?
    *   Does it call `context_detector.detect_context`, passing the shared `genai_client` and `config`?
    *   Does it call `chunk_translator.translate_all_chunks` using `asyncio.run`? Does it pass the shared `genai_client` and `config`?
    *   Does it call `reassembler.reassemble_srt`?
    *   Does it use `send_file` with an `io.BytesIO` buffer for the success response?
    *   Is the core logic wrapped in a `try...except` block that allows the `@app.errorhandler` decorators to catch exceptions?
7.  Update the description of `src/app.py` in `docs/TECHNICAL_DESIGN.md`, paying close attention to the actual flow, error handling implementation, and parameter passing.

**Task 10: Review High-Level Sections**

1.  Briefly review the "Module Structure & File Organization", "Interfaces & Interaction Patterns", "Workflow / Use Case Examples", and "Implementation Notes, Edge Cases, and TODOs" sections of the design document.
2.  Based on your findings from Tasks 1-9, identify any high-level descriptions in these sections that are now inaccurate. For example:
    *   Is the file structure still correct?
    *   Does the frontend/backend interaction pattern described still hold true based on `app.py`'s routes and expected data flow?
    *   Does the workflow example accurately reflect the function calls and data transformations you observed in the code?
    *   Are any of the "TODOs" or "Implementation Notes" actually completed or significantly different in the code?
3.  Update these high-level sections in `docs/TECHNICAL_DESIGN.md`