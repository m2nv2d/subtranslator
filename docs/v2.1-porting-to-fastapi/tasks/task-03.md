## Task 4: Review Templates & Static Files

### Project Context
This task is part of migrating a web application from Flask to FastAPI. The application translates subtitle files (.srt). This specific task focuses on ensuring the frontend components (HTML template, JavaScript, CSS) remain compatible after the backend framework change. The core backend logic for translation is handled elsewhere.

### Prerequisites
You should assume the backend has been partially migrated:
*   A FastAPI application instance exists (likely in `src/main.py`).
*   A route exists for `GET /` that serves the main HTML page. It uses Jinja2 for templating and passes a context variable named `languages` (a list of target language name strings, e.g., `["Vietnamese", "French"]`) to the template.
*   A route exists for `POST /translate` that accepts multipart form data containing `file` (an uploaded file), `target_lang` (string), and `speed_mode` (string). On success, it returns the translated file as a downloadable attachment (`media_type='text/srt'`). On failure, it returns a JSON response like `{"error": "some message..."}` with an appropriate HTTP error status code (e.g., 400, 422, 500, 503, 504).

### Subtask 1: Verify HTML Template (`src/templates/index.html`)
Review the `index.html` file located at `src/templates/index.html`.
*   Ensure it correctly uses the `languages` variable passed from the backend to populate the target language selection dropdown (`<select name="target_lang">`).
*   Verify that all asset links (CSS, JS, favicon) use relative paths (e.g., `/static/css/style.css`) that are compatible with how FastAPI serves static files (typically mounted at `/static`).
*   Check for any Flask-specific Jinja2 functions or filters (e.g., `url_for`) that might not be available or behave differently in the standard Jinja2 environment used by FastAPI. Replace or remove them if found, ensuring functionality remains (simple variable access like `{{ language }}` and standard loops/conditionals are fine).
*   Confirm the form structure (`id="translate-form"`, inputs `name="file"`, `name="target_lang"`, `name="speed_mode"`, button `id="submit-button"`) and the status display element (`id="status-message"`) match the expectations outlined in the Project Context and required by the JavaScript file.

### Subtask 2: Verify Client-Side JavaScript (`src/static/js/app.js`)
Review the `app.js` file located at `src/static/js/app.js`.
*   Confirm the script correctly identifies the form (`#translate-form`) and its elements.
*   Verify the `fetch` request targets the correct endpoint (`/translate`) using the `POST` method.
*   Ensure the script correctly constructs the `FormData` object based on the form inputs (`file`, `target_lang`, `speed_mode`).
*   Check the response handling logic:
    *   Success: Assumes the response is a blob (`response.ok` is true), triggers a download, and updates the status message (`#status-message`) using the appropriate CSS class (e.g., `status-success`).
    *   Error: Assumes the response is JSON (`response.ok` is false), parses the JSON to extract an error message (expecting format `{"error": "..."}`), and displays it in the status message using the appropriate CSS class (e.g., `status-error`).
*   Verify the UI state updates (disabling/enabling submit button, updating status message text and class) function as intended during the request lifecycle.
*   Ensure there are no hardcoded assumptions about the backend framework (Flask) that would break under FastAPI. The interaction relies on standard Fetch API, FormData, and HTTP responses, which should be compatible.

### Subtask 3: Verify CSS (`src/static/css/style.css`)
Quickly review the `style.css` file located at `src/static/css/style.css`.
*   Confirm the presence of the necessary CSS classes for styling the status message based on its state (`.status-processing`, `.status-success`, `.status-error`), as used by `app.js`.
*   Ensure CSS selectors still correctly target the elements in `index.html`. No changes are generally expected here unless HTML structure was significantly altered (which is not the goal of this migration phase).

### Debugging and Verification
To manually verify these changes, run the FastAPI application using an ASGI server (like Uvicorn). Consult the `tests/manual/` directory for any existing test cases or create one:
1.  Open the application's root URL (`/`) in a web browser.
2.  Check that the page loads correctly, styles are applied, and the target language dropdown is populated from the configuration.
3.  Select a valid `.srt` file, choose a target language, and select a speed mode.
4.  Submit the form.
5.  Observe the status message (`#status-message`): It should indicate processing, then either success or error.
6.  On success, verify that a file download is triggered with the correct filename format (`original_stem_TargetLanguage.srt`).
7.  If an error occurs (e.g., submitting without a file, or if the backend simulates an error), verify that the correct error message is displayed in the status area.
8.  Check the browser's developer console for any JavaScript errors during this process.