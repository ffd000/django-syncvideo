class FileUpload {
    constructor(input) {
        this.input = input
        this.max_length = 1024 * 1024 * 10;
    }

    create_progress_bar() {
        var progress = `<div class="file-icon">
                            <i class="fa fa-file-o" aria-hidden="true"></i>
                        </div>
                        <div class="file-details">
                            <p class="filename"></p>
                            <small class="textbox"></small>
                            <div class="progress" style="margin-top: 5px;">
                                <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%">
                                </div>
                            </div>
                        </div>`
        document.getElementById('uploaded_files').innerHTML = progress
    }

    upload() {
        this.initFileUpload();
    }

    initFileUpload() {
        this.create_progress_bar();
        this.file = this.input.files[0];
        this.upload_file(0, null);
    }

    upload_file(start, video_path) {
        const alertBox = document.getElementById('alert_box');
        const title = document.getElementById('video_file_title');
        var end;
        var self = this;
        var existing_path = video_path;
        var formData = new FormData();
        var nextChunk = start + this.max_length + 1;
        var currentChunk = this.file.slice(start, nextChunk);
        var uploadedChunk = start + currentChunk.size
        if (uploadedChunk >= this.file.size) {
            end = 1;
        } else {
            end = 0;
        }
        formData.append('file', currentChunk)
        formData.append('filename', this.file.name)
        $('.filename').text(this.file.name)
        $('.textbox').text("Uploading file")
        formData.append('eof', end)
        formData.append('existingPath', existing_path);
        formData.append('nextSlice', nextChunk);
        formData.append('title', title.value == null ? 'Untitled Video' : title.value);
        formData.append('status', '-1');
        $.ajaxSetup({
            headers: {"X-CSRFToken": $('input[name=csrfmiddlewaretoken]').val()}
        });

        $.ajax({
            xhr: function () {
                var xhr = new XMLHttpRequest();
                xhr.upload.addEventListener('progress', function (e) {
                    if (e.lengthComputable) {
                        if (self.file.size < self.max_length) {
                            var percent = Math.round((e.loaded / e.total) * 100);
                        } else {
                            var percent = Math.round((uploadedChunk / self.file.size) * 100);
                        }
                        $('.progress-bar').css('width', percent + '%')
                        $('.progress-bar').text(percent + '%')
                    }
                });
                return xhr;
            },

            url: `/room/${roomName}/upload/`,
            type: 'POST',
            cache: false,
            processData: false,
            contentType: false,
            data: formData,
            error: function (error) {
                let message = error.statusText;
                if (error.responseJSON !== undefined) {
                    message += ": " + error.responseJSON.error
                }
                alertBox.innerHTML = "<p class='text-danger'>Something went wrong: " + message + "</p>";
            },
            success: function (res) {
                if (nextChunk < self.file.size) {
                    // upload file in chunks
                    existing_path = res.existingPath
                    self.upload_file(nextChunk, existing_path);
                } else {
                    alertBox.innerHTML = "<p class='text-white'>Upload completed.</a></p>";

                    title.value = null;
                    self.file.value = null;
                    $("#fileupload").replaceWith($("#fileupload").val('').clone(true));
                    $('.progress').hide()
                    $('.textbox').hide()

                    res.type = 'add_to_playlist'
                    socket_message(res)
                }
            }
        });
    };
}