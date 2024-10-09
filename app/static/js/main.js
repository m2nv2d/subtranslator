document.addEventListener('DOMContentLoaded', function () {
    let isTranslating = false;
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file');
    const fileName = document.getElementById('file-name');
    const submitButton = form.querySelector('button[type="submit"]');
    const downloadLink = document.getElementById('download-link');
    const debugInfo = document.getElementById('debug-info');

    fileInput.addEventListener('change', function (e) {
        if (this.files && this.files[0]) {
            if (this.files[0].name.toLowerCase().endsWith('.srt')) {
                fileName.textContent = this.files[0].name;
            } else {
                alert('Please select a .srt file.');
                this.value = ''; // Clear the file input
                fileName.textContent = '';
            }
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
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
        submitButton.disabled = true;
        downloadLink.classList.add('hidden');
        debugInfo.classList.add('hidden');

        try {
            const response = await axios.post('/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            isTranslating = false;
            submitButton.innerHTML = '<i class="fas fa-sync-alt mr-2"></i>Translate';
            submitButton.disabled = false;
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
            submitButton.innerHTML = '<i class="fas fa-sync-alt mr-2"></i>Translate';
            submitButton.disabled = false;
            alert('An error occurred: ' + (error.response?.data?.error || error.message));
        }
    });
});