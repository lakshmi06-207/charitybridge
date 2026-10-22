/* ============================================================
   CHARITYBRIDGE CHAT
   Clean version
   Community -> Message -> Chat
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    /* --------------------------------------------------------
       CHAT DATA
       -------------------------------------------------------- */

    var chatData = {
        selectedUserId: null,
        currentUserId: null
    };

    var dataElement = document.getElementById("chat-data");

    if (dataElement) {
        try {
            chatData = JSON.parse(dataElement.textContent);
        } catch (error) {
            console.error("Chat data error:", error);
        }
    }

    var currentUserId = Number(chatData.currentUserId || 0);
    var selectedUserId = Number(chatData.selectedUserId || 0);


    /* --------------------------------------------------------
       ELEMENTS
       -------------------------------------------------------- */

    var peopleSearch = document.getElementById("peopleSearch");
    var messageInput = document.getElementById("messageInput");
    var sendButton = document.getElementById("sendButton");
    var messagesArea = document.getElementById("messagesArea");
    var conversationTitle = document.getElementById("conversationTitle");

    var notificationButton =
        document.getElementById("notificationButton");

    var notificationPanel =
        document.getElementById("notificationPanel");

    var notificationClose =
        document.getElementById("notificationClose");

    var attachmentButton =
        document.getElementById("attachmentButton");

    var voiceButton =
        document.getElementById("voiceButton");

    var aiRudder =
        document.getElementById("aiRudder");

    var aiPanel =
        document.getElementById("aiPanel");

    var aiClose =
        document.getElementById("aiClose");

    var aiInput =
        document.getElementById("aiInput");

    var aiSend =
        document.getElementById("aiSend");

    var aiConversation =
        document.getElementById("aiConversation");

    var pageToast =
        document.querySelector(".page-toast");


    /* --------------------------------------------------------
       TOAST
       -------------------------------------------------------- */

    function showToast(message) {

        if (!pageToast) {
            alert(message);
            return;
        }

        pageToast.textContent = message;
        pageToast.classList.add("show");

        window.setTimeout(function () {
            pageToast.classList.remove("show");
        }, 2500);
    }


    /* --------------------------------------------------------
       SEARCH PEOPLE
       -------------------------------------------------------- */

    if (peopleSearch) {

        peopleSearch.addEventListener("input", function () {

            var searchText =
                peopleSearch.value.toLowerCase().trim();

            var people =
                document.querySelectorAll(".person-card");

            people.forEach(function (person) {

                var name =
                    person.getAttribute("data-person-name") || "";

                name = name.toLowerCase();

                if (name.indexOf(searchText) !== -1) {
                    person.style.display = "";
                } else {
                    person.style.display = "none";
                }
            });
        });
    }


    /* --------------------------------------------------------
       SELECT PERSON
       -------------------------------------------------------- */

    
function selectPerson(userId, userName) {

    const id = Number(userId);

    if (!Number.isInteger(id) || id <= 0) {
        showToast("Invalid user selected.");
        return;
    }

    if (id === Number(currentUserId)) {
        showToast("You cannot message yourself.");
        return;
    }

    window.location.href =
        "/chat?user_id=" + encodeURIComponent(id);
}

    /* --------------------------------------------------------
       FILTER CONVERSATION
       -------------------------------------------------------- */

    function filterConversation(userId) {

        if (!messagesArea) {
            return;
        }

        var rows =
            messagesArea.querySelectorAll(".message-row");

        var foundMessage = false;

        rows.forEach(function (row) {

            var senderId =
                Number(row.getAttribute("data-sender-id") || 0);

            var receiverId =
                Number(row.getAttribute("data-receiver-id") || 0);

            var belongsToConversation =
                (senderId === currentUserId &&
                 receiverId === Number(userId))
                ||
                (senderId === Number(userId) &&
                 receiverId === currentUserId);

            if (belongsToConversation) {

                row.style.display = "";

                foundMessage = true;

            } else {

                row.style.display = "none";
            }
        });

        var welcome =
            messagesArea.querySelector(".welcome-card");

        if (welcome) {
            if (foundMessage) {
                welcome.style.display = "none";
            } else {
                welcome.style.display = "";
            }
        }

        messagesArea.scrollTop =
            messagesArea.scrollHeight;
    }


    /* --------------------------------------------------------
       PERSON BUTTONS
       -------------------------------------------------------- */

    document.addEventListener("click", function (event) {

        var button =
            event.target.closest(".person-message-button");

        if (!button) {
            return;
        }

        var userId =
            button.getAttribute("data-user-id");

        if (!userId) {
            showToast("User not found.");
            return;
        }

        var card =
            button.closest(".person-card");

        var userName = "";

        if (card) {

            var nameElement =
                card.querySelector(".person-name");

            if (nameElement) {
                userName =
                    nameElement.textContent.trim();
            }

            if (!userName) {
                userName =
                    card.getAttribute("data-person-name") || "";
            }
        }

        selectPerson(userId, userName);
    });


    /* --------------------------------------------------------
       SEND MESSAGE
       -------------------------------------------------------- */

    async function sendMessage() {

        if (!messageInput) {
            return;
        }

        var message =
            messageInput.value.trim();

        if (!message) {
            return;
        }

        if (!selectedUserId) {
            showToast("Please select a person first.");
            return;
        }

        if (!currentUserId) {
            showToast("Please login first.");
            return;
        }

        if (sendButton) {
            sendButton.disabled = true;
        }

        try {

            var response =
                await fetch("/chat/send", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        receiver_id: selectedUserId,
                        message: message
                    })
                });

            var result =
                await response.json();

            if (!response.ok || !result.success) {

                showToast(
                    result.message ||
                    "Unable to send message."
                );

                return;
            }

            messageInput.value = "";

            addMessageToScreen(result.data);

        } catch (error) {

            console.error(
                "Send message error:",
                error
            );

            showToast(
                "Unable to send message."
            );

        } finally {

            if (sendButton) {
                sendButton.disabled = false;
            }
        }
    }


    /* --------------------------------------------------------
       SEND BUTTON
       -------------------------------------------------------- */

    if (sendButton) {

        sendButton.addEventListener(
            "click",
            function () {
                sendMessage();
            }
        );
    }


    /* --------------------------------------------------------
       ENTER TO SEND
       -------------------------------------------------------- */

    if (messageInput) {

        messageInput.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    sendMessage();
                }
            }
        );
    }


  

/* --------------------------------------------------------
   ADD MESSAGE: TEXT, VOICE, IMAGE, VIDEO, FILE AND TICKS
   -------------------------------------------------------- */

function addMessageToScreen(message) {

    if (!messagesArea || !message) {
        return;
    }

    var welcome = messagesArea.querySelector(".welcome-card");

    if (welcome) {
        welcome.remove();
    }

    var row = document.createElement("div");

    row.className = "message-row own-message";

    row.setAttribute("data-message-id", String(message.id || ""));
    row.setAttribute("data-sender-id", String(message.sender_id));
    row.setAttribute("data-receiver-id", String(message.receiver_id));

    var bubble = document.createElement("div");
    bubble.className = "message-bubble";

    var mediaPath = message.media_path || "";
    var mediaType = (message.media_type || "").toLowerCase();

    // Build the media URL from the path returned by Flask.
    var mediaUrl = "";

    if (mediaPath) {
        mediaUrl = "/static/" + mediaPath.replace(/^\/+/, "");
    }

    // Show the text or filename.
    if (message.message) {
        var text = document.createElement("div");
        text.className = "message-text";
        text.textContent = message.message;
        bubble.appendChild(text);
    }

    // Image attachment.
    if (mediaPath && mediaType === "image") {

        var image = document.createElement("img");

        image.src = mediaUrl;
        image.alt = message.message || "Shared image";
        image.loading = "lazy";
        image.style.display = "block";
        image.style.maxWidth = "100%";
        image.style.maxHeight = "300px";
        image.style.borderRadius = "10px";
        image.style.marginTop = "8px";

        bubble.appendChild(image);
    }

    // Video attachment.
    else if (mediaPath && mediaType === "video") {

        var video = document.createElement("video");

        video.src = mediaUrl;
        video.controls = true;
        video.preload = "metadata";
        video.style.display = "block";
        video.style.maxWidth = "100%";
        video.style.maxHeight = "300px";
        video.style.marginTop = "8px";

        bubble.appendChild(video);
    }

    // Voice or audio attachment.
    else if (mediaPath && mediaType === "audio") {

        var audio = document.createElement("audio");

        audio.src = mediaUrl;
        audio.controls = true;
        audio.preload = "metadata";
        audio.style.display = "block";
        audio.style.maxWidth = "100%";
        audio.style.marginTop = "8px";

        bubble.appendChild(audio);
    }

    // PDF, document, spreadsheet, zip or other file.
    else if (mediaPath) {

        var fileLink = document.createElement("a");

        fileLink.href = mediaUrl;
        fileLink.textContent = "📎 Open or download file";
        fileLink.target = "_blank";
        fileLink.rel = "noopener noreferrer";
        fileLink.download = "";

        fileLink.style.display = "block";
        fileLink.style.marginTop = "8px";
        fileLink.style.overflowWrap = "anywhere";

        bubble.appendChild(fileLink);
    }

    // Timestamp and delivery/read ticks.
    var footer = document.createElement("div");
    footer.className = "message-time";

    var time = document.createElement("span");
    time.textContent = formatMessageTime(message.created_at);

    var status = document.createElement("span");
    status.className = "message-status";
    status.style.marginLeft = "6px";

    var isRead = Number(message.is_read) === 1;
    var isDelivered = Number(message.is_delivered) === 1;

    if (isRead) {
        status.textContent = "✓✓";
        status.style.color = "#34B7F1";
        status.title = "Read";
    } else if (isDelivered) {
        status.textContent = "✓✓";
        status.style.color = "#8696A0";
        status.title = "Delivered";
    } else {
        status.textContent = "✓";
        status.style.color = "#8696A0";
        status.title = "Sent";
    }

    
footer.appendChild(time);
footer.appendChild(status);

// Delete message button
var deleteButton = document.createElement("button");
deleteButton.type = "button";
deleteButton.textContent = "🗑️";
deleteButton.title = "Delete message";
deleteButton.style.marginLeft = "8px";
deleteButton.style.border = "none";
deleteButton.style.background = "transparent";
deleteButton.style.cursor = "pointer";

deleteButton.addEventListener("click", async function () {
    var choice = prompt(
        "Type ME to delete for yourself, or EVERYONE to delete for everyone:"
    );

    if (!choice) return;

    choice = choice.trim().toLowerCase();

    if (choice !== "me" && choice !== "everyone") {
        showToast("Type ME or EVERYONE.");
        return;
    }

    if (
        choice === "everyone" &&
        Number(message.sender_id) !== currentUserId
    ) {
        showToast("You can delete only your own messages for everyone.");
        return;
    }

    if (!confirm("Are you sure you want to delete this message?")) {
        return;
    }

    try {
        var response = await fetch(
            "/chat/delete/" + encodeURIComponent(message.id),
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ delete_for: choice })
            }
        );

        var result = await response.json();

        if (!response.ok || !result.success) {
            showToast(result.message || "Unable to delete message.");
            return;
        }

        if (choice === "everyone") {
            var textElement = bubble.querySelector(".message-text");

            if (textElement) {
                textElement.textContent = "This message was deleted.";
            }

            bubble.querySelectorAll("img, video, audio, a").forEach(
                function (element) {
                    element.remove();
                }
            );

            showToast("Message deleted for everyone.");
        } else {
            row.remove();
            showToast("Message deleted.");
        }
    } catch (error) {
        console.error("Delete message error:", error);
        showToast("Unable to delete message.");
    }
});

footer.appendChild(deleteButton);

bubble.appendChild(footer);
row.appendChild(bubble);

    messagesArea.appendChild(row);

    messagesArea.scrollTop = messagesArea.scrollHeight;
}


    /* --------------------------------------------------------
       MESSAGE TIME
       -------------------------------------------------------- */

    function formatMessageTime(value) {

        if (!value) {
            return "";
        }

        var date =
            new Date(value);

        if (isNaN(date.getTime())) {
            return String(value);
        }

        return date.toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );
    }


/* --------------------------------------------------------
   ATTACHMENT BUTTON
   -------------------------------------------------------- */

if (attachmentButton) {

    var chatFileInput = document.createElement("input");

    chatFileInput.type = "file";
    chatFileInput.accept =
        "image/*,video/*,audio/*,.pdf,.txt,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip";

    chatFileInput.style.display = "none";
    document.body.appendChild(chatFileInput);

    attachmentButton.addEventListener("click", function () {

        if (!selectedUserId) {
            showToast("Please select a person first.");
            return;
        }

        chatFileInput.click();
    });

    chatFileInput.addEventListener("change", async function () {

        var file = chatFileInput.files[0];

        if (!file) {
            return;
        }

        if (file.size > 20 * 1024 * 1024) {
            showToast("File must be 20 MB or smaller.");
            chatFileInput.value = "";
            return;
        }

        var formData = new FormData();
        formData.append("receiver_id", selectedUserId);
        formData.append("file", file);

        try {

            attachmentButton.disabled = true;
            showToast("Uploading file...");

            var response = await fetch("/chat/upload", {
                method: "POST",
                body: formData
            });

            var result = await response.json();

            if (!response.ok || !result.success) {
                showToast(result.message || "File upload failed.");
                return;
            }

            addMessageToScreen(result.data);
            showToast("File sent successfully.");

        } catch (error) {

            console.error("Attachment error:", error);
            showToast("Unable to send the file.");

        } finally {

            attachmentButton.disabled = false;
            chatFileInput.value = "";

        }
    });
}


   
/* --------------------------------------------------------
   VOICE MESSAGE BUTTON
   Click once to record; click again to stop and send.
   -------------------------------------------------------- */

if (voiceButton) {

    var mediaRecorder = null;
    var recordedChunks = [];
    var voiceStream = null;
    var isRecordingVoice = false;

    voiceButton.addEventListener("click", async function () {

        if (!selectedUserId) {
            showToast("Please select a person first.");
            return;
        }

        // Second click: stop recording and send the audio.
        if (isRecordingVoice && mediaRecorder) {
            mediaRecorder.stop();
            return;
        }

        if (!navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia ||
            !window.MediaRecorder) {
            showToast("Voice recording is not supported in this browser.");
            return;
        }

        try {

            voiceStream =
                await navigator.mediaDevices.getUserMedia({
                    audio: true
                });

            recordedChunks = [];

            var options = {};

            if (MediaRecorder.isTypeSupported("audio/webm")) {
                options.mimeType = "audio/webm";
            }

            mediaRecorder =
                new MediaRecorder(voiceStream, options);

            mediaRecorder.addEventListener("dataavailable", function (event) {
                if (event.data && event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            });

            mediaRecorder.addEventListener("stop", async function () {

                isRecordingVoice = false;
                voiceButton.disabled = true;

                voiceStream.getTracks().forEach(function (track) {
                    track.stop();
                });

                var mimeType =
                    mediaRecorder.mimeType || "audio/webm";

                var extension =
                    mimeType.includes("ogg") ? "ogg" :
                    mimeType.includes("mp4") ? "m4a" : "webm";

                var audioBlob = new Blob(recordedChunks, {
                    type: mimeType
                });

                if (!audioBlob.size) {
                    showToast("No audio was recorded.");
                    voiceButton.disabled = false;
                    return;
                }

                var formData = new FormData();

                formData.append("receiver_id", selectedUserId);
                formData.append(
                    "file",
                    audioBlob,
                    "voice-message." + extension
                );

                try {

                    showToast("Sending voice message...");

                    var response = await fetch("/chat/upload", {
                        method: "POST",
                        body: formData
                    });

                    var result = await response.json();

                    if (!response.ok || !result.success) {
                        showToast(
                            result.message || "Unable to send voice message."
                        );
                        return;
                    }

                    addMessageToScreen(result.data);
                    showToast("Voice message sent.");

                } catch (error) {

                    console.error("Voice upload error:", error);
                    showToast("Unable to send voice message.");

                } finally {

                    voiceButton.disabled = false;
                    recordedChunks = [];

                }
            });

            mediaRecorder.start();
            isRecordingVoice = true;

            showToast("Recording... Click the voice button again to send.");

        } catch (error) {

            console.error("Microphone error:", error);
            showToast("Please allow microphone access to record voice.");

        }
    });
}


    /* --------------------------------------------------------
       NOTIFICATIONS
       -------------------------------------------------------- */

    if (notificationButton && notificationPanel) {

        notificationButton.addEventListener(
            "click",
            function () {

                notificationPanel.classList.toggle(
                    "active"
                );
            }
        );
    }

    if (notificationClose && notificationPanel) {

        notificationClose.addEventListener(
            "click",
            function () {

                notificationPanel.classList.remove(
                    "active"
                );
            }
        );
    }


    /* --------------------------------------------------------
       AI RUDDER
       -------------------------------------------------------- */

    if (aiRudder && aiPanel) {

        aiRudder.addEventListener(
            "click",
            function () {

                aiPanel.classList.toggle(
                    "active"
                );
            }
        );
    }

    if (aiClose && aiPanel) {

        aiClose.addEventListener(
            "click",
            function () {

                aiPanel.classList.remove(
                    "active"
                );
            }
        );
    }


    /* --------------------------------------------------------
       AI SEND
       -------------------------------------------------------- */

    function sendAIMessage() {

        if (!aiInput || !aiConversation) {
            return;
        }

        var question =
            aiInput.value.trim();

        if (!question) {
            return;
        }

        var userMessage =
            document.createElement("div");

        userMessage.className =
            "ai-user-message";

        userMessage.textContent =
            question;

        aiConversation.appendChild(
            userMessage
        );

        aiInput.value = "";

        var answer =
            document.createElement("div");

        answer.className =
            "ai-bot-message";

        answer.textContent =
            getAIResponse(question);

        aiConversation.appendChild(
            answer
        );

        aiConversation.scrollTop =
            aiConversation.scrollHeight;
    }


    function getAIResponse(question) {

        var text =
            question.toLowerCase();

        if (text.indexOf("donate") !== -1) {
            return "You can use the Donate section to make a contribution.";
        }

        if (text.indexOf("request") !== -1) {
            return "You can use the Request section to view or create help requests.";
        }

        if (text.indexOf("volunteer") !== -1) {
            return "You can use the Volunteer section to participate in community activities.";
        }

        if (text.indexOf("hello") !== -1 ||
            text.indexOf("hi") !== -1) {
            return "Hello! How can I help you today?";
        }

        return "I can help you navigate CharityBridge and its community features.";
    }


    if (aiSend) {

        aiSend.addEventListener(
            "click",
            function () {
                sendAIMessage();
            }
        );
    }


    if (aiInput) {

        aiInput.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    sendAIMessage();
                }
            }
        );
    }


    
/* --------------------------------------------------------
   INITIAL SELECTED USER
   -------------------------------------------------------- */

if (selectedUserId) {

    var selectedCard =
        document.querySelector(
            '.person-card[data-person-id="' +
            selectedUserId +
            '"]'
        );

    if (selectedCard) {

        var selectedName =
            selectedCard.querySelector(".person-name");

        if (conversationTitle) {
            conversationTitle.textContent =
                selectedName
                    ? selectedName.textContent.trim()
                    : "Community Messages";
        }

        filterConversation(selectedUserId);

    } else {

        filterConversation(selectedUserId);
    }
}



    /* --------------------------------------------------------
       INITIAL SCROLL
       -------------------------------------------------------- */

    if (messagesArea) {

        messagesArea.scrollTop =
            messagesArea.scrollHeight;
    }

});