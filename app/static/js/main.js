$(document).ready(function () {
    let isTranslating = false;

    $('#upload-form').on('submit', function (e) {
        e.preventDefault();
        var formData = new FormData();
        formData.append('file', $('#file')[0].files[0]);

        isTranslating = true;
        $('#translation-status').show();
        pollTranslationStatus();

        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                isTranslating = false;
                $('#download-link').show();
                $('#download-link a').attr('href', '/download/' + response.file_id);

                if (response.debug_info) {
                    $('#debug-info').show();
                    $('#num-chunks').text(response.debug_info.num_chunks);
                    $('#total-entries').text(response.debug_info.total_entries);
                    $('#num-success').text(response.debug_info.num_success);
                }
            },
            error: function (xhr, status, error) {
                isTranslating = false;
                alert('An error occurred: ' + xhr.responseJSON.error);
            }
        });
    });

    function pollTranslationStatus() {
        if (!isTranslating) {
            return;
        }

        $.ajax({
            url: '/translation_status',
            type: 'GET',
            success: function (response) {
                $('#responses-received').text(response.responses_received);
                $('#total-chunks').text(response.total_chunks);
                if (response.responses_received < response.total_chunks && isTranslating) {
                    setTimeout(pollTranslationStatus, 1000);  // Poll every second
                }
            },
            error: function () {
                console.log('Error fetching translation status');
                isTranslating = false;
            }
        });
    }
});