document.addEventListener('DOMContentLoaded', () => {
    const translateForm = document.getElementById('translate-form');
    const fileInput = document.getElementById('file-input');
    const targetLangSelect = document.getElementById('target-lang');
    const speedModeSelect = document.getElementById('speed-mode');
    const submitButton = document.getElementById('submit-button');
    const statusMessage = document.getElementById('status-message');

    if (!translateForm || !fileInput || !targetLangSelect || !speedModeSelect || !submitButton || !statusMessage) {
        console.error('Error: One or more required form elements not found.');
        if (statusMessage) {
            statusMessage.textContent = 'Error: Page setup failed. Please refresh.';
            statusMessage.className = 'status-error';
        }
        return;
    }

    translateForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default synchronous submission

        // --- Basic Client-Side Validation ---
        if (!fileInput.files || fileInput.files.length === 0) {
            statusMessage.textContent = 'Error: Please select an SRT file.';
            statusMessage.className = 'status-error';
            return;
        }
        const file = fileInput.files[0];
        if (!file.name.toLowerCase().endsWith('.srt')) {
             statusMessage.textContent = 'Error: Invalid file type. Please upload an SRT file.';
             statusMessage.className = 'status-error';
             return;
        }
        if (!targetLangSelect.value) {
            statusMessage.textContent = 'Error: Please select a target language.';
            statusMessage.className = 'status-error';
            return;
        }

        // --- Prepare for Submission ---
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_lang', targetLangSelect.value);
        formData.append('speed_mode', speedModeSelect.value);

        submitButton.disabled = true;
        statusMessage.textContent = 'Uploading and translating... Please wait.';
        statusMessage.className = 'status-processing'; // Add class for styling

        try {
            // --- Asynchronous Fetch Request ---
            const response = await fetch('/translate', {
                method: 'POST',
                body: formData,
            });

            // --- Handle Response ---
            if (response.ok) { // Status 200-299
                // Success: Assume response is the file blob
                const blob = await response.blob();
                const originalFilename = file.name;
                const filenameBase = originalFilename.substring(0, originalFilename.lastIndexOf('.')) || originalFilename;
                const targetLang = targetLangSelect.value;
                const downloadFilename = `${filenameBase}_${targetLang}.srt`;

                // Create a temporary link to trigger the download
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = downloadFilename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url); // Clean up the object URL
                a.remove();

                statusMessage.textContent = 'Translation complete!';
                statusMessage.className = 'status-success'; // Add class for styling
            } else {
                // Error: Try to parse JSON error message from backend
                let errorMessage = `Request failed with status: ${response.status} ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                        errorMessage = `Error: ${errorData.error}`;
                    }
                } catch (jsonError) {
                    console.error('Could not parse error response as JSON:', jsonError);
                    // Keep the generic status text error message
                }
                statusMessage.textContent = errorMessage;
                statusMessage.className = 'status-error'; // Add class for styling
            }
        } catch (error) {
            // Network error or other fetch issue
            console.error('Fetch error:', error);
            statusMessage.textContent = 'Error: Could not connect to the server or process the request.';
            statusMessage.className = 'status-error'; // Add class for styling
        } finally {
            // --- Re-enable Button ---
            submitButton.disabled = false;
        }
    });
});