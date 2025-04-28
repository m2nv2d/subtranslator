# Task 4: Implement Background Tasks for Temporary File Cleanup

## Project Context
This project is a web application built with FastAPI that translates subtitle files (.srt). The core translation workflow involves:
1.  Receiving an uploaded .srt file via a POST request to the `/translate` endpoint.
2.  Creating a temporary directory using Python's `tempfile.mkdtemp()` to store the uploaded file securely during processing. The path to this directory is stored in a variable (e.g., `temp_dir`).
3.  Processing the file (parsing, translation, reassembling).
4.  Returning the translated file to the user as a download.
5.  Currently, the temporary directory and its contents are cleaned up using a `try...finally` block within the `/translate` endpoint function, calling `os.rmdir(temp_dir)` in the `finally` clause.

The goal of this task is to replace the synchronous `try...finally` cleanup mechanism with FastAPI's asynchronous `BackgroundTasks` feature to perform the cleanup after the response has been sent.

## Prerequisites
- The project uses FastAPI. The necessary FastAPI libraries are assumed to be installed.
- The standard Python libraries `tempfile` and `os` are used for temporary directory management.
- Familiarity with FastAPI route function definitions and dependency injection concepts.

## Subtask 1: Modify Endpoint Signature
Locate the main application file, likely `src/main.py`, and find the function handling the `POST /translate` route. Modify the signature of this function to accept an instance of `fastapi.BackgroundTasks`. This is typically done by adding a parameter like `background_tasks: BackgroundTasks` to the function definition. FastAPI will automatically inject this dependency.

## Subtask 2: Replace Cleanup Logic with Background Task
Within the same `/translate` function in `src/main.py`:
1.  Identify the `try...finally` block that currently ensures the cleanup of the temporary directory (the one calling `os.rmdir` on the temporary directory path variable within the `finally` part).
2.  Remove the `finally` block entirely, or at least remove the `os.rmdir` call from it. The `try` block might still be useful for handling exceptions during file processing *before* the response is prepared.
3.  Locate the point just *before* the function returns the successful `StreamingResponse` (or other response type).
4.  At this point, use the injected `background_tasks` instance to schedule the cleanup operation. Call its `add_task` method, passing the `os.rmdir` function as the first argument and the variable holding the path to the temporary directory (e.g., `temp_dir`) as the subsequent argument. Ensure this `add_task` call happens only if the temporary directory was successfully created earlier in the function execution flow.