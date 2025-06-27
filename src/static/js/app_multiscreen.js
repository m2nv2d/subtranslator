document.addEventListener('DOMContentLoaded', () => {
    // Screen elements
    const welcomeScreen = document.getElementById('welcome-screen');
    const progressScreen = document.getElementById('progress-screen');
    const resultScreen = document.getElementById('result-screen');
    
    // Form elements
    const translateForm = document.getElementById('translate-form');
    const fileInput = document.getElementById('file-input');
    const targetLangSelect = document.getElementById('target-lang');
    const speedModeSelect = document.getElementById('speed-mode');
    const submitButton = document.getElementById('submit-button');
    const fileNameDisplay = document.getElementById('file-name-display');
    
    // Progress elements
    const translationStatus = document.getElementById('translation-status');
    const progressBar = document.getElementById('progress-bar');
    const cancelButton = document.getElementById('cancel-button');
    
    // Result elements
    const resultIcon = document.getElementById('result-icon');
    const resultTitle = document.getElementById('result-title');
    const resultMessage = document.getElementById('result-message');
    const downloadButton = document.getElementById('download-button');
    const newTranslationButton = document.getElementById('new-translation-button');
    
    // State variables
    let currentTranslationId = null;
    let statusCheckInterval = null;
    let downloadUrl = null;
    let downloadFilename = null;

    // Verify all required elements exist
    const requiredElements = [
        welcomeScreen, progressScreen, resultScreen, translateForm, fileInput, 
        targetLangSelect, speedModeSelect, submitButton, translationStatus, 
        progressBar, cancelButton, resultIcon, resultTitle, resultMessage, 
        downloadButton, newTranslationButton
    ];
    
    if (requiredElements.some(el => !el)) {
        console.error('Error: One or more required elements not found.');
        alert('Error: Page setup failed. Please refresh.');
        return;
    }

    // Screen navigation functions
    function showScreen(screen) {
        [welcomeScreen, progressScreen, resultScreen].forEach(s => s.classList.remove('active'));
        screen.classList.add('active');
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
                dropZone.classList.add('border-slate-500', 'bg-slate-50');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-slate-500', 'bg-slate-50');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                fileInput.files = files;
                updateFileDisplay(files[0].name);
            }
        });
    }

    // Update file name display when selected
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            updateFileDisplay(fileInput.files[0].name);
        }
    });

    function updateFileDisplay(fileName) {
        if (fileNameDisplay) {
            fileNameDisplay.textContent = fileName;
        }
    }

    // Status checking function
    async function checkTranslationStatus() {
        if (!currentTranslationId) return;
        
        try {
            const response = await fetch(`/translate/status/${currentTranslationId}`);
            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }
            
            const status = await response.json();
            
            // Update status message (progress bar is indeterminate)
            translationStatus.textContent = status.message || 'Processing...';
            
            // Check if translation is complete
            if (status.status === 'completed') {
                clearInterval(statusCheckInterval);
                showResult(true, 'Translation Complete!', 'Your translated file is ready for download.', status.download_url, status.filename);
            } else if (status.status === 'failed') {
                clearInterval(statusCheckInterval);
                showResult(false, 'Translation Failed', status.error || 'An error occurred during translation.');
            } else if (status.status === 'cancelled') {
                clearInterval(statusCheckInterval);
                showResult(false, 'Translation Cancelled', 'The translation was cancelled.');
            }
        } catch (error) {
            console.error('Status check error:', error);
            // Don't immediately fail - network issues might be temporary
        }
    }

    // Show result screen
    function showResult(success, title, message, url = null, filename = null) {
        if (success) {
            resultIcon.textContent = 'check_circle';
            resultIcon.className = 'material-icons text-4xl text-green-600 mb-3 block';
            resultTitle.className = 'text-green-700 text-xl font-medium mb-2';
            downloadUrl = url;
            downloadFilename = filename;
            if (url) {
                downloadButton.classList.remove('hidden');
            }
        } else {
            resultIcon.textContent = 'error';
            resultIcon.className = 'material-icons text-4xl text-red-600 mb-3 block';
            resultTitle.className = 'text-red-700 text-xl font-medium mb-2';
            downloadButton.classList.add('hidden');
        }
        
        resultTitle.textContent = title;
        resultMessage.textContent = message;
        showScreen(resultScreen);
    }

    // Form submission handler
    translateForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        // Basic validation
        if (!fileInput.files || fileInput.files.length === 0) {
            alert('Please select an SRT file.');
            return;
        }
        
        const file = fileInput.files[0];
        if (!file.name.toLowerCase().endsWith('.srt')) {
            alert('Invalid file type. Please upload an SRT file.');
            return;
        }
        
        if (!targetLangSelect.value) {
            alert('Please select a target language.');
            return;
        }

        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_lang', targetLangSelect.value);
        formData.append('speed_mode', speedModeSelect.value);

        // Show progress screen
        showScreen(progressScreen);
        translationStatus.textContent = `Translating ${file.name}...`;

        try {
            // Start translation
            const response = await fetch('/translate/async', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Request failed: ${response.status}`);
            }

            const result = await response.json();
            currentTranslationId = result.translation_id;
            
            // Start status checking
            statusCheckInterval = setInterval(checkTranslationStatus, 1000);
            
        } catch (error) {
            console.error('Translation start error:', error);
            showResult(false, 'Translation Failed', error.message);
        }
    });

    // Cancel button handler
    cancelButton.addEventListener('click', async () => {
        if (!currentTranslationId) return;
        
        try {
            const response = await fetch(`/translate/cancel/${currentTranslationId}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                clearInterval(statusCheckInterval);
                showResult(false, 'Translation Cancelled', 'The translation was cancelled successfully.');
            }
        } catch (error) {
            console.error('Cancel error:', error);
        }
    });

    // Download button handler
    downloadButton.addEventListener('click', () => {
        if (downloadUrl) {
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = downloadFilename || 'translated.srt';
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    });

    // New translation button handler
    newTranslationButton.addEventListener('click', () => {
        // Reset state
        currentTranslationId = null;
        downloadUrl = null;
        downloadFilename = null;
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
        }
        
        // Reset form
        translateForm.reset();
        fileNameDisplay.textContent = 'Drag & Drop your .SRT file here';
        
        // Show welcome screen
        showScreen(welcomeScreen);
    });
});