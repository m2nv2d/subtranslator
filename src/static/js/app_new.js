document.addEventListener('DOMContentLoaded', () => {
    const translateForm = document.getElementById('translate-form');
    const fileInput = document.getElementById('file-input');
    const targetLangSelect = document.getElementById('target-lang');
    const speedModeSelect = document.getElementById('speed-mode');
    const submitButton = document.getElementById('submit-button');
    const statusMessage = document.getElementById('status-message');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    // Verify all required elements exist
    if (!translateForm || !fileInput || !targetLangSelect || !speedModeSelect || !submitButton || !statusMessage) {
        console.error('Error: One or more required form elements not found.');
        showStatus('Error: Page setup failed. Please refresh.', 'error');
        return;
    }

    // Handle file drop zone functionality
    const dropZone = document.querySelector('.border-dashed');
    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-slate-500');
                dropZone.classList.add('bg-slate-50');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-slate-500');
                dropZone.classList.remove('bg-slate-50');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                fileInput.files = files;
                const fileName = files[0].name;
                if (fileName) {
                    updateFileDisplay(fileName);
                }
            }
        });
    }

    // Update file name display when selected
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            updateFileDisplay(fileInput.files[0].name);
        }
    });

    // Function to update the file display name
    function updateFileDisplay(fileName) {
        const fileNameDisplay = dropZone.querySelector('p.text-slate-600');
        if (fileNameDisplay) {
            fileNameDisplay.textContent = fileName;
        }
    }

    // Helper function to show status messages
    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = 'border rounded-lg p-4 text-center';
        
        switch (type) {
            case 'processing':
                statusMessage.classList.add('bg-blue-50', 'text-blue-700', 'border-blue-200');
                break;
            case 'success':
                statusMessage.classList.add('bg-green-50', 'text-green-700', 'border-green-200');
                break;
            case 'error':
                statusMessage.classList.add('bg-red-50', 'text-red-700', 'border-red-200');
                break;
        }
        
        statusMessage.classList.remove('hidden');
    }

    // Form submission handler
    translateForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default synchronous submission

        // --- Basic Client-Side Validation ---
        if (!fileInput.files || fileInput.files.length === 0) {
            showStatus('Error: Please select an SRT file.', 'error');
            return;
        }
        
        const file = fileInput.files[0];
        if (!file.name.toLowerCase().endsWith('.srt')) {
            showStatus('Error: Invalid file type. Please upload an SRT file.', 'error');
            return;
        }
        
        if (!targetLangSelect.value) {
            showStatus('Error: Please select a target language.', 'error');
            return;
        }

        // --- Prepare for Submission ---
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_lang', targetLangSelect.value);
        formData.append('speed_mode', speedModeSelect.value);

        submitButton.disabled = true;
        showStatus('Uploading and translating... Please wait.', 'processing');
        
        // Show progress bar
        if (progressContainer) {
            progressContainer.classList.remove('hidden');
            progressBar.style.width = '5%'; // Start with a small indicator
            progressText.textContent = 'Processing...'
        }

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

                // Update progress to 100%
                if (progressBar && progressText) {
                    progressBar.style.width = '100%';
                    progressText.textContent = '100% Complete';
                }

                showStatus('Translation complete!', 'success');
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
                showStatus(errorMessage, 'error');
            }
        } catch (error) {
            // Network error or other fetch issue
            console.error('Fetch error:', error);
            showStatus('Error: Could not connect to the server or process the request.', 'error');
        } finally {
            // --- Re-enable Button ---
            submitButton.disabled = false;
        }
    });
});