# Review Notes: Resource Management

**Files Reviewed:**
*   `src/routers/translate.py`

## Observations & Analysis

1.  **Temporary File Handling:**
    *   **Good:** The application correctly uses the `tempfile` module (`tempfile.mkdtemp`) to create a dedicated temporary directory for processing each uploaded file. This avoids polluting a shared temporary space and simplifies cleanup.
    *   **Good:** `aiofiles` is used to write the uploaded content to the temporary file asynchronously.
    *   **Good:** Cleanup logic (`os.unlink` for the file, `os.rmdir` for the directory) is present.

2.  **Cleanup Mechanism:**
    *   **Observation:** Cleanup is performed using FastAPI's `BackgroundTasks`. This means the cleanup operations (`os.unlink`, `os.rmdir`) are scheduled to run *after* the response has been sent to the client.
    *   **Potential Issue:** The background tasks for cleanup are only added *after* the entire translation workflow (parsing, context detection, translation, reassembly) completes successfully within the main `try` block. If any exception occurs during this workflow (e.g., `ParsingError`, `ChunkTranslationError`, `file.read()` error, or even an unexpected `Exception`), the route handler will exit (either through an explicit `raise` or an exception handler in `main.py`) *before* `background_tasks.add_task` is called. In these failure scenarios, the temporary directory and file created at the beginning of the `try` block will be left behind on the server.
    *   **Minor Observation:** The cleanup functions (`os.unlink`, `os.rmdir`) are synchronous standard library functions. While running them in background tasks prevents them from blocking the response, they will still execute synchronously within the background worker/thread pool that FastAPI uses for background tasks. For purely async operations, `aiofiles.os.remove` and `aiofiles.os.rmdir` could be used, although the practical impact is likely negligible.

## Questions

*   Is the potential for leaving temporary files/directories on the server in case of processing errors acceptable?

## Suggestions

1.  **Implement Robust Cleanup:** Use a `try...finally` block to ensure cleanup code always runs, regardless of whether the translation workflow succeeds or fails. Move the temporary file/directory creation *outside* the main `try` block so the paths are available in the `finally` block.

    *Example Structure:*
    ```python
    # In translate_srt function
    temp_dir = None
    temp_file_path = None
    try:
        # Secure filename
        original_filename = secure_filename(file.filename)
        
        # Create temp resources *before* the main try block
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, original_filename)
        
        # --- Start main processing --- 
        try:
            # Save uploaded file asynchronously
            content = await file.read()
            async with aiofiles.open(temp_file_path, "wb") as temp_file:
                await temp_file.write(content)
            logger.debug(f"Saved uploaded file temporarily to: {temp_file_path}")

            # ... (rest of the parsing, translation, reassembly logic) ...

            # Return translated SRT file
            # ... (prepare StreamingResponse) ...
            return StreamingResponse(...)

        # --- Exception handling for the workflow --- 
        except ValidationError as e:
            logger.warning(f"Validation error during translation: {e}")
            raise
        except ParsingError as e:
            # ... other specific exceptions ...
            raise
        except Exception as e:
            logger.exception(f"Unhandled exception during translation: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        # --- Cleanup --- 
        # This block executes whether the try block succeeded or failed
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except OSError as e:
                logger.error(f"Error removing temporary file {temp_file_path}: {e}")
        if temp_dir and os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except OSError as e:
                logger.error(f"Error removing temporary directory {temp_dir}: {e}")
    ```
    *Note:* This example uses synchronous `os` functions in the `finally` block. If strict non-blocking is required even during cleanup, `aiofiles.os` could be used, potentially requiring the `finally` block to be `async` (which is supported) or running the async cleanup functions using `asyncio.run` or similar if the context isn't already async.

2.  **(Alternative) Async Context Manager:** Implement an asynchronous context manager to handle the creation and cleanup of the temporary directory and file. This can lead to cleaner code within the route handler. 