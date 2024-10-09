document.addEventListener('DOMContentLoaded', function () {
    let isTranslating = false;
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file');
    const fileName = document.getElementById('file-name');
    const statusElement = document.getElementById('translation-status');
    const downloadLink = document.getElementById('download-link');
    const debugInfo = document.getElementById('debug-info');
    const progressBar = document.getElementById('progress-bar');

    fileInput.addEventListener('change', function (e) {
        if (this.files && this.files[0]) {
            fileName.textContent = this.files[0].name;
        }
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        if (!fileInput.files || fileInput.files[0].size === 0) {
            alert('Please select a non-empty file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        isTranslating = true;
        statusElement.classList.remove('hidden');
        downloadLink.classList.add('hidden');
        debugInfo.classList.add('hidden');

        try {
            const response = await axios.post('/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            isTranslating = false;
            downloadLink.classList.remove('hidden');
            downloadLink.querySelector('a').href = '/download/' + response.data.file_id;

            if (response.data.debug_info) {
                debugInfo.classList.remove('hidden');
                document.getElementById('num-chunks').textContent = response.data.debug_info.num_chunks;
                document.getElementById('total-entries').textContent = response.data.debug_info.total_entries;
                document.getElementById('num-success').textContent = response.data.debug_info.num_success;
            }
        } catch (error) {
            isTranslating = false;
            alert('An error occurred: ' + (error.response?.data?.error || error.message));
        }
    });

    async function pollTranslationStatus() {
        if (!isTranslating) {
            return;
        }

        try {
            const response = await axios.get('/translation_status');
            const { responses_received, total_chunks } = response.data;
            document.getElementById('responses-received').textContent = responses_received;
            document.getElementById('total-chunks').textContent = total_chunks;

            const progress = (responses_received / total_chunks) * 100;
            progressBar.style.width = `${progress}%`;

            if (responses_received < total_chunks && isTranslating) {
                setTimeout(pollTranslationStatus, 1000);  // Poll every second
            } else if (responses_received === total_chunks) {
                statusElement.classList.add('animate__fadeOut');
                setTimeout(() => {
                    statusElement.classList.add('hidden');
                    statusElement.classList.remove('animate__fadeOut');
                }, 1000);
            }
        } catch (error) {
            console.log('Error fetching translation status:', error);
            isTranslating = false;
        }
    }

    // Start polling when translation begins
    form.addEventListener('submit', pollTranslationStatus);
});