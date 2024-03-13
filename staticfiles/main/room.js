const CSRF = $('input[name=csrfmiddlewaretoken]').val()
const roomName = JSON.parse($('#roomName')[0].textContent);
const YOUTUBE_URL = "https://www.youtube.com/watch?v=";
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

let player = null;
let socket = null;
var watchedTimestamp = 0;

/* If we are the first socket to connect, other sockets will sync to our video time. */
var isControlSocket = false;

const errorBox = $('#playback-error');
const errorSpan = $('#error-message');

function socket_connect() {
    socket = new WebSocket(`${protocol}//${window.location.host}/ws/room/${roomName}`);

    /*
    Handles messages dispatched from Consumer.
     */
    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        var {type} = data

        console.log("message received", data);

        switch (type) {
            case 'sync':
                var delta = Math.abs(player.currentTime() - data.time);
                if (delta > 5) {
                    player.currentTime(data.time)
                }
                break;
            case 'add_to_playlist':
                addToPlaylist(data)
                break;
            case 'delete_from_playlist':
                deleteFromPlaylist(data.video_pk)
                break;
            case 'chat':
                updateChatMessages()
                break;
            case "user_list":
                if (data.users.length <= 1) {
                    isControlSocket = true;
                }

                $('#user-list').children(':not(:first-child)').remove();
                data.users.forEach(onlineUsersSelectorAdd);
                $('#guest-list-counter').text(data.guests);
                break;
            case "video_play":
                player.play()
                break;
            case "video_pause":
                player.pause()
                break;
            case "video_switch":
                loadVideoSource(data['video'])
                break;
            case 'timestamp_requested':
                // client sends the requested timestamp back to consumer
                socket_message({'type': "video_timestamp", 'timestamp': player.currentTime()})
                break;
            case 'video_timestamp':
                const timestamp = data.timestamp;
                console.log("A socket requested to sync. Timestamp received", timestamp)
                watchedTimestamp = timestamp;
                break;
            default:
                console.error("Unknown message type! " + data.type);
                break;
        }
    }

    socket.onopen = function (e) {
        console.log("Successfully connected to the WebSocket.");
    }

    socket.onclose = function (e) {
        console.log("WebSocket connection closed unexpectedly.");
        setTimeout(function () {
            console.log("Reconnecting...");
            socket_connect();
        }, 3000);
    };

    socket.onerror = function (err) {
        console.log("WebSocket encountered an error: " + err.message);
        console.log("Closing the socket.");
        socket.close();
    }
}

/*
Dynamically changes the video.js player source to either an HTML5 or Youtube video.
 */
function loadVideoSource(vid) {
    var provider = "webm"
    // Youtube ID will never contain dots
    if (vid.includes('.')) {
        source = '/room/media/' + vid
    } else {
        source = YOUTUBE_URL + vid
        provider = "youtube"
    }

    if (!player.paused) {
        player.pause();
    }
    player.src({
        src: source,
        type: 'video/' + provider,
    });
    player.load();

    console.log('player.load()')
}

/*
Switches the current video to the one the user clicked on.
 */
function switchVideoHandler(pk) {
    $('#player').show();

    $.ajax({
        method: 'POST',
        url: `/room/${roomName}/set_playing/${pk}/`,
        headers: {'X-CSRFToken': CSRF},
        mode: 'same-origin',
        dataType: "json",
        success: function (data) {
            socket_message({'type': 'video_switch', 'video': data.video_id})
        },
        error: function (error) {
            let message = error.statusText;
            if (error.responseJSON !== undefined) {
                message += ": " + error.responseJSON.error
            }
            errorSpan.text(message);
            errorBox.show();
        }
    })
}

/*
Dynamically update the user list with authenticated users.
 */
function onlineUsersSelectorAdd(user) {
    const $userList = $('#user-list');
    const $userElem = $('<li>', {
        class: 'list-group-item custom-list-item',
        text: user
    });
    $userList.append($userElem);
}


/*
Dynamically loads the entire chat history at once for simplicity. Oldest messages are automatically deleted
from the database if there are too many in a given room, so the chat history can't be too large.
 */
function updateChatMessages() {
    $.get(`/room/${roomName}/chat_messages`, function (data) {
        let chatLog = $("#chat-messages");
        chatLog.html(data);
        chatLog.scrollTop(chatLog.prop('scrollHeight'));
    });
}

/*
Dynamically deletes the video object from the playlist element by video ID.
 */
function deleteFromPlaylist(pk) {
    $target = $(`.playlist-item[data-pk="${pk}"]`)

    $target.hide('slow', function () {
        $target.remove()

        if ($('.playlist-item').length === 0)
            $('#no-videos').show()
    });
}

/*
Dynamically appends the video object to the playlist element.
 */
function addToPlaylist(data) {
    if ($(".playlist-item").length === 0)
        $('#no-videos').hide()

    $("#playlist").append("<li class='playlist-item list-group-item' data-pk=" + data["pk"] + " style='display:none'>\
                <a href='javascript:switchVideoHandler(" + data["pk"] + ")' class='text-white'>\
                    [" + data.provider.toUpperCase() + "] " + data["title"] + "\
                </a>\
                <a href='javascript:deleteVideoHandler(" + data["pk"] + ")' class='text-white-50 float-right'>delete</a>\
            </li>")

    $('#playlist').find(".playlist-item:last").slideDown("fast")
}

// since autoplay behaves different across many browsers, just wait for the user to play the video themselves first
function onFirstPlay() {
    // We can assume the video has been loaded and played after the socket has connected successfully
    // and the timestamp has been received. This saves one call to the server.
    player.currentTime(watchedTimestamp);

    player.off("play", onFirstPlay);
    player.on("play", onVideoPlay);
}

function initVideojs(startVideo) {
    // initialize videojs player, add handlers, load current video if one is playing
    videojs('player').ready(function () {
        player = this;

        player.on("play", onFirstPlay);
        player.on("pause", onVideoPause);
        player.on('error', function (error) {
            if (error) {
                const errorText = player.error().message;
                errorSpan.text('Error loading video:' + errorText)
                errorBox.show();
            }
        });
        // meager attempt at autoplay because browsers don't like autoplaying videos with sound.
        player.on('loadedmetadata', () => {
            console.log('loadedmetadata')
            player.play()
        });

        // Load the video that has been playing previously
        if (startVideo !== 'None') {
            loadVideoSource(startVideo)

            $('#player').show();
        }

        /**
         * Periodically sends a synchronization request to the server. This should be called only by one socket
         * in the group.
         *
         * This function calculates the time elapsed since the last synchronization. If at least
         * X seconds have passed on a video timeupdate, a synchronization request is sent to the Consumer.
         * The last synchronization time is updated with the current video playback time.
         *
         * Since this would cause lots of requests to be sent, it's been turned off for the demo.
         */
        if (isControlSocket === true) {
            var lastSyncTime = 0;
            var interval = 20;
            player.on('timeupdate', function () {
                var currentTime = player.currentTime();

                // calculate time elapsed since the last sync
                var elapsedTime = currentTime - lastSyncTime;

                // if at least 15 seconds have passed since the last sync
                if (elapsedTime >= interval) {
                    socket_message({'type': 'sync', 'time': currentTime})

                    lastSyncTime = currentTime;
                }
            });
        }
    });
}

/*
Helper function to send a JSON-encoded message to the server which handles it with the Consumer.
 */
function socket_message(data) {
    socket.send(JSON.stringify(data));
}

function onVideoPlay() {
    socket_message({'type': "video_play"})
}

function onVideoPause() {
    if (player.seeking()) return;

    socket_message({'type': "video_pause"})
}

socket_connect();



