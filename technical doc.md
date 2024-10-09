# Technical Documentation: Subtitle Translation Flask App

## 1. App Overview

### Purpose
The Subtitle Translation Flask App is designed to provide users with a simple and efficient way to translate subtitle files (`.srt`) from one language to another using a Language Learning Model (LLM). This tool is particularly useful for content creators, educators, and multilingual audiences who wish to make video content accessible in various languages.

### Main Features
- **File Upload:** Users can upload `.srt` subtitle files through a user-friendly interface.
- **LLM Integration:** The backend processes the uploaded file, extracts the textual content, and leverages an LLM to perform the translation.
- **Downloadable Output:** After translation, users can download the translated `.srt` file with preserved timing.
- **Progress Indicator:** A progress bar provides real-time feedback during the translation process.
- **Backend Throttling:** Implements rate limiting to prevent API overload by monitoring the number and size of LLM requests over specified time intervals.

## 2. General Interaction

### User Experience (UX) and Interaction Flow

1. **Landing Page:**
   - Users access the web application and are presented with a clean interface featuring an upload button.

2. **File Upload:**
   - Users click the "Upload `.srt` File" button to select and upload their subtitle file.

3. **Language Selection:**
   - (Optional) Users may select the target language for translation from a dropdown menu.

4. **Processing:**
   - Upon upload, the backend begins processing, and a progress bar displays the translation status.

5. **Download:**
   - Once translation is complete, a download link for the translated `.srt` file becomes available.

6. **Notifications:**
   - Users receive notifications in case of errors, such as unsupported file formats or exceeding rate limits.

### User Stories

1. **Uploading a Subtitle File:**
   - *As a user, I want to upload my `.srt` file so that I can translate it into another language.*

2. **Monitoring Translation Progress:**
   - *As a user, I want to see the progress of my subtitle translation to know when it's complete.*

3. **Downloading Translated Subtitles:**
   - *As a user, I want to download the translated `.srt` file once the translation is finished.*

4. **Handling Rate Limits:**
   - *As a user, I want to be informed if the service is currently busy or rate-limited to manage my usage accordingly.*

## 3. Basic Tech Stack Requirements

### Programming Languages
- **Python:** Backend development using Flask.
- **JavaScript:** Frontend interactivity and progress bar implementation.
- **HTML/CSS:** Structuring and styling the web interface.

### Frameworks and Libraries
- **Flask:** Lightweight web framework for building the backend.
- **Flask-Limiter:** For implementing rate limiting on backend requests.
- **Jinja2:** Templating engine for rendering HTML pages.
- **Requests:** To interact with the LLM API.
- **Bootstrap:** CSS framework for responsive and aesthetic UI design.
- **Axios or Fetch API:** Handling AJAX requests for file uploads and progress updates.

### Necessary Tools
- **Virtual Environment:** Using `venv` or `conda` to manage Python dependencies.
- **Git:** Version control for code management.
- **Postman:** For API testing and debugging.
- **Code Editor:** Such as VS Code or PyCharm for development.
- **LLM API Access:** Credentials and access to an appropriate LLM service (e.g., OpenAI GPT).

### Development Environments
- **Local Development Server:** Flask’s built-in development server for testing.
- **Docker (Optional):** Containerization for consistent deployment environments.

## 4. Major Components of the App

### Main Modules/Components

1. **Frontend Interface:**
   - Handles user interactions, file uploads, progress display, and download links.

2. **Backend Server:**
   - Manages file processing, communicates with the LLM API, and handles rate limiting.

3. **LLM Integration Module:**
   - Interfaces with the LLM API to perform translations.

4. **Rate Limiting Module:**
   - Monitors and restricts the number and size of API requests to prevent overload.

5. **File Processing Module:**
   - Parses `.srt` files, extracts text, and reassembles translated content with original timing.

### Component Interactions

1. **User Interaction:**
   - The user uploads an `.srt` file via the frontend interface.

2. **File Handling:**
   - The frontend sends the file to the backend for processing.

3. **Rate Limiting Check:**
   - The backend checks current API usage against rate limits before proceeding.

4. **Subtitle Processing:**
   - The file processing module parses the `.srt` file, extracts text, and sends it to the LLM integration module.

5. **Translation:**
   - The LLM integration module sends extracted text to the LLM API and retrieves the translated text.

6. **Reassembly:**
   - The file processing module re-attaches the original timing to the translated text.

7. **Response:**
   - The backend sends the translated `.srt` file back to the frontend for the user to download.

### High-Level Architecture Description

- **Client Side (Frontend):**
  - Built with HTML, CSS (Bootstrap), and JavaScript.
  - Communicates with the backend via HTTP requests for file upload and download.
  - Displays a progress bar based on backend processing status updates.

- **Server Side (Backend):**
  - Flask handles routing and request management.
  - Upon receiving a file upload, it invokes the file processing module.
  - Implements rate limiting using Flask-Limiter to control API usage.
  - Interacts with the LLM integration module to perform translations.
  - Returns the processed file to the client upon completion.

## 5. Specific Class and Method Definitions

### 5.1 Frontend Interface

**Class:** `AppFrontend`
- **Description:** Manages the user interface, including file uploads, progress display, and download links.

**Methods:**
- `initialize_upload_button()`
  - *Arguments:* None
  - *Description:* Sets up the event listener for the upload button.

- `handle_file_upload(file)`
  - *Arguments:* `file` (File object)
  - *Description:* Sends the uploaded file to the backend for processing.

- `update_progress_bar(progress)`
  - *Arguments:* `progress` (Integer 0-100)
  - *Description:* Updates the progress bar based on processing status.

- `enable_download_link(file_url)`
  - *Arguments:* `file_url` (String URL)
  - *Description:* Enables and displays the download link for the translated file.

### 5.2 Backend Server

**Class:** `FlaskApp`
- **Description:** Sets up Flask routes and integrates all backend components.

**Methods:**
- `__init__()`
  - *Arguments:* None
  - *Description:* Initializes the Flask application and configures extensions.

- `route_upload()`
  - *Arguments:* None
  - *Description:* Handles the `/upload` route to receive and process uploaded files.

- `route_download(file_id)`
  - *Arguments:* `file_id` (String)
  - *Description:* Handles the `/download/<file_id>` route to serve the translated file.

- `configure_rate_limiting()`
  - *Arguments:* None
  - *Description:* Sets up rate limiting policies using Flask-Limiter.

### 5.3 File Processing Module

**Class:** `SubtitleProcessor`
- **Description:** Parses and reconstructs `.srt` files.

**Methods:**
- `parse_srt(file_path)`
  - *Arguments:* `file_path` (String)
  - *Returns:* List of subtitle entries (each with timing and text)
  - *Description:* Parses the `.srt` file and extracts timing and text.

- `extract_text(subtitles)`
  - *Arguments:* `subtitles` (List)
  - *Returns:* List of text strings
  - *Description:* Extracts only the textual content from subtitle entries.

- `reassemble_srt(timing, translated_text)`
  - *Arguments:* `timing` (List), `translated_text` (List)
  - *Returns:* String representing the translated `.srt` file
  - *Description:* Combines original timings with translated text to create a new `.srt` file.

### 5.4 LLM Integration Module

**Class:** `LLMTranslator`
- **Description:** Interfaces with the LLM API to perform text translations.

**Methods:**
- `__init__(api_key)`
  - *Arguments:* `api_key` (String)
  - *Description:* Initializes the translator with the necessary API credentials.

- `translate_text(text_list, target_language)`
  - *Arguments:* `text_list` (List of Strings), `target_language` (String)
  - *Returns:* List of translated strings
  - *Description:* Sends the list of text strings to the LLM API and retrieves translations.

### 5.5 Rate Limiting Module

**Class:** `RateLimiter`
- **Description:** Manages and enforces API usage limits.

**Methods:**
- `check_limits(user_id)`
  - *Arguments:* `user_id` (String)
  - *Returns:* Boolean
  - *Description:* Checks if the user has exceeded the allowed number of requests.

- `update_usage(user_id, request_size)`
  - *Arguments:* `user_id` (String), `request_size` (Integer)
  - *Description:* Updates the usage statistics after a new request.

- `get_current_usage(user_id)`
  - *Arguments:* `user_id` (String)
  - *Returns:* Usage stats (e.g., requests per minute)
  - *Description:* Retrieves current API usage for the user.

## 6. Specific Workflow in Typical Interactions

### Use Case: Translating an Uploaded `.srt` File

1. **File Upload Initiation:**
   - The user accesses the web application and clicks the "Upload `.srt` File" button.
   - The `AppFrontend.initialize_upload_button()` method sets up the event listener for the upload action.

2. **Sending File to Backend:**
   - Upon selecting the file, the `AppFrontend.handle_file_upload(file)` method sends the file to the backend via an AJAX request to the `/upload` route.

3. **Backend Receives File:**
   - The `FlaskApp.route_upload()` method receives the file and invokes the `RateLimiter.check_limits(user_id)` to ensure the user hasn't exceeded rate limits.
   - If the limit is exceeded, an error response is sent to the frontend, notifying the user.

4. **Processing the Subtitle File:**
   - The `SubtitleProcessor.parse_srt(file_path)` method parses the `.srt` file, extracting timing and text.
   - The `SubtitleProcessor.extract_text(subtitles)` method retrieves only the textual content for translation.

5. **Translation via LLM:**
   - The `LLMTranslator.translate_text(text_list, target_language)` method sends the extracted text to the LLM API and receives the translated text.
   - The `RateLimiter.update_usage(user_id, request_size)` method updates the user's API usage statistics based on the size of the request.

6. **Reassembling Translated Subtitles:**
   - The `SubtitleProcessor.reassemble_srt(timing, translated_text)` method combines the original timing with the translated text to create a new `.srt` file.

7. **Storing and Serving the Translated File:**
   - The backend stores the translated `.srt` file, assigns it a unique `file_id`, and sends a success response to the frontend with the download link (e.g., `/download/<file_id>`).

8. **Displaying Progress and Completion:**
   - As the backend processes the translation, the `AppFrontend.update_progress_bar(progress)` method updates the progress bar based on status updates from the server.
   - Once processing is complete, the `AppFrontend.enable_download_link(file_url)` method makes the download link available to the user.

9. **File Download:**
   - The user clicks the download link, triggering the `FlaskApp.route_download(file_id)` method to serve the translated `.srt` file for download.

10. **Post-Processing:**
    - The backend logs the completed request and resets any temporary data associated with the translation task.

### Error Handling

- **Unsupported File Format:**
  - If a user uploads a non-`.srt` file, the backend responds with an error message, and the frontend displays a notification.

- **Rate Limit Exceeded:**
  - If the user exceeds the allowed number of requests, the backend sends a rate limit notification, and the frontend informs the user to retry after some time.

- **LLM API Failure:**
  - In case of LLM API errors, the backend captures the exception, logs the issue, and notifies the user of the failure.

### Progress Tracking

- The backend can periodically send progress updates to the frontend via WebSockets or polling endpoints.
- The frontend listens for these updates and adjusts the progress bar accordingly.
- Alternatively, the frontend can estimate progress based on the number of subtitle segments processed.

## Data Flow for Subtitle Translation

When a user uploads a subtitle file for translation, the following process occurs:

1. **File Upload Initiation**
   - The user selects a .srt file and submits the form on the main page (index.html).
   - The JavaScript function in `app/static/js/main.js` intercepts the form submission and sends an AJAX POST request to the `/upload` endpoint.

2. **Server-Side File Reception**
   - The `upload_file()` function in `app/routes.py` handles the POST request to `/upload`.
   - It checks if a file is present in the request and if it has a .srt extension.

3. **File Processing**
   - If the file is valid, it's saved to the `UPLOAD_FOLDER` defined in `config.py`.
   - The `SubtitleProcessor.parse_srt()` method in `app/models/subtitle_processor.py` reads the file and divides it into chunks of about 40 subtitle entries each.
   - `SubtitleProcessor.extract_text()` is called for each chunk to extract only the text content.

4. **Rate Limiting Check**
   - Before proceeding with translation, the `RateLimiter.check_limits()` method in `app/utils/rate_limiter.py` is called to ensure the user hasn't exceeded the rate limit.

5. **Translation Process**
   - An instance of `LLMTranslator` from `app/models/llm_translator.py` is created.
   - The `translate_text()` method is called asynchronously with the text chunks and a system prompt.
   - For each chunk, `send_translation_request()` is called, which:
     - Initializes the Google Generative AI model if not already done.
     - Sends the text to the API for translation.
     - Retries up to 3 times with increasing delays if an error occurs.
     - Updates the progress after each chunk is processed.

6. **Reassembly of Translated Subtitles**
   - Once all chunks are translated, `SubtitleProcessor.reassemble_srt()` is called for each chunk to combine the original timing information with the translated text.
   - The reassembled chunks are joined into a single string containing the complete translated subtitle file.

7. **Saving the Translated File**
   - The translated subtitle content is saved as a new file in the `UPLOAD_FOLDER` with a "translated_" prefix.

8. **Response to Client**
   - A JSON response is sent back to the client, including:
     - A success flag
     - The file ID (filename) of the translated subtitle file
     - Debug information (if in debug mode) including the number of chunks, total entries, number of requests sent, and number of successful requests

9. **Client-Side Handling of Response**
   - The JavaScript function in `main.js` receives the response and:
     - Updates the progress bar to 100%
     - Displays the download link for the translated file
     - Shows debug information if available

10. **Progress Tracking**
    - Throughout the translation process, the client-side JavaScript polls the `/progress` endpoint every second.
    - The server responds with the current progress, which is used to update the progress bar in real-time.

11. **File Download**
    - When the user clicks the download link, a GET request is sent to the `/download/<file_id>` endpoint.
    - The `download_file()` function in `routes.py` handles this request and sends the translated subtitle file to the user.

This flow ensures that the user can upload a subtitle file, see real-time progress of the translation, and download the translated file once the process is complete, all while respecting rate limits and providing debug information when necessary.

# Appendix

## Glossary

- **LLM (Language Learning Model):** An advanced AI model capable of understanding and generating human-like text, used here for translating subtitle content.
- **`.srt` File:** A common subtitle file format containing timestamped text for video content.
- **Flask:** A micro web framework written in Python for building web applications.
- **Rate Limiting:** A technique to control the amount of incoming or outgoing traffic to or from a network, ensuring stability and preventing abuse.

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-Limiter Documentation](https://flask-limiter.readthedocs.io/)
- [OpenAI API Documentation](https://beta.openai.com/docs/)
- [Bootstrap Documentation](https://getbootstrap.com/)
- [SRT File Format Specification](https://en.wikipedia.org/wiki/SubRip)

# Conclusion

This technical document outlines the structure and architecture required to build a Flask-based Subtitle Translation App leveraging an LLM for translations. By following the outlined components, classes, and workflows, a developer can implement a robust, user-friendly application with necessary features like file uploads, progress tracking, and rate limiting to ensure reliable performance.