**Task 9: Frontend Integration with Asynchronous Submission**

**Project Context**

You are building the user interface for a web application that translates subtitle files (.srt). The backend is a Flask application. This task focuses on creating the HTML structure, basic styling, and the necessary JavaScript to allow users to upload an SRT file, select a target language, choose a speed mode, and submit the request *asynchronously*. This means the page will *not* reload; instead, JavaScript will handle the submission, provide feedback to the user during processing, and display the result (either triggering a file download on success or showing an error message on failure).

**Prerequisites**

*   The project follows a standard Flask structure with `templates/`, `static/css/`, and `static/js/` directories.
*   You need to understand how the Flask backend provides data to the main page template (`GET /`) and what data and format it expects for the translation request (`POST /translate`). Refer to the `src/app.py` file:
    *   Check the `GET /` route for the variable name passing the list of target languages (expected: `languages`).
    *   Check the `POST /translate` route for the expected `name` attributes for the form data: file (`file`), target language (`target_lang`), and speed mode (`speed_mode`).
    *   Crucially, understand the **expected backend responses** for the `POST /translate` endpoint:
        *   **Success:** An HTTP 200 OK status with the response body being the translated SRT file data (likely `Content-Type: application/octet-stream` or similar, suitable for `send_file`).
        *   **Error:** An HTTP error status (4xx or 5xx) with the response body being JSON containing an error message (e.g., `{"error": "..."}`). Verify the exact error JSON structure in the `app.py` error handlers.

**Subtask 1: Update HTML Structure (`templates/index.html`)**

*   Create/modify the HTML structure in `templates/index.html`. Include the form with file input (accepting `.srt`), target language dropdown (dynamically populated from the `languages` backend variable), speed mode dropdown ("fast", "normal"), and a submit button, similar to the basic version.
*   **Add an element** (e.g., a `<div>` or `<p>` with a specific ID) where status messages ("Uploading...", "Translating...", "Success!", "Error: ...") can be displayed to the user via JavaScript.
*   Ensure the HTML correctly links to the CSS (`static/css/style.css`) and JavaScript (`static/js/app.js`) files.

**Subtask 2: Implement Asynchronous Submission Logic (`static/js/app.js`)**

*   Write JavaScript code in `static/js/app.js`.
*   Add an event listener to the form's submit event. **Prevent the default form submission behavior**.
*   Inside the event handler:
    *   Perform basic client-side validation (e.g., check if a file is selected). If invalid, display an error message in the status area and stop.
    *   Gather the form data, including the selected file, target language, and speed mode, into a `FormData` object.
    *   Update the status area to indicate processing has started (e.g., "Uploading and translating...").
    *   Use the `fetch` API to send the `FormData` asynchronously to the `/translate` endpoint using the `POST` method.
    *   Handle the `fetch` response:
        *   Check `response.ok` or `response.status`.
        *   **If successful (e.g., status 200):**
            *   Assume the response body is the file content. Retrieve it as a `Blob`.
            *   Programmatically trigger a file download for the user (e.g., create an object URL and simulate a link click). Try to construct a meaningful filename (e.g., based on the original filename and target language).
            *   Update the status area to indicate success (e.g., "Translation complete! Check your downloads.").
        *   **If an error occurred (e.g., status 4xx, 5xx):**
            *   Attempt to parse the response body as JSON.
            *   Extract the error message from the JSON (referencing the structure defined in `src/app.py`'s error handlers).
            *   Display the extracted error message clearly in the status area.
        *   Include `catch` block for network errors or other issues during the `fetch` call and display a generic error message in the status area.
    *   Consider disabling the submit button while a request is in progress to prevent multiple submissions. Re-enable it once the request completes (either successfully or with an error).

**Subtask 3: Apply Basic Styling (`static/css/style.css`)**

*   Create or update the CSS file at `static/css/style.css`.
*   Apply basic styling to the form elements and the newly added status message area. Ensure the status messages (success, error, processing) are clearly visible.