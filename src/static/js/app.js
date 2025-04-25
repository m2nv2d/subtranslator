const form = document.getElementById('uploadForm');
const submitBtn = document.getElementById('submitBtn');
const status = document.getElementById('status');

function showStatus(message, type) {
    status.textContent = message;
    status.className = type;
    status.style.display = 'block';
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(form);
    
    // Basic validation
    const file = formData.get('file');
    if (!file) {
        showStatus('Please select a file', 'error');
        return;
    }
    if (!file.name.toLowerCase().endsWith('.srt')) {
        showStatus('Only .srt files are allowed', 'error');
        return;
    }
    if (file.size > 2 * 1024 * 1024) {
        showStatus('File size must be less than 2MB', 'error');
        return;
    }

    // Disable form and show processing status
    submitBtn.disabled = true;
    showStatus('Translating...', 'info');

    try {
        const response = await fetch('/translate', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name.replace('.srt', `_${formData.get('target_lang')}.srt`);
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showStatus('Translation complete! Check your downloads.', 'info');
        } else {
            const error = await response.json();
            showStatus(error.error || 'Translation failed', 'error');
        }
    } catch (error) {
        showStatus('Network error occurred', 'error');
    } finally {
        submitBtn.disabled = false;
    }
});