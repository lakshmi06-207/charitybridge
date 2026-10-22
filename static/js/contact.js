/* ============================================================
   CHARITYBRIDGE CONTACT PAGE
============================================================ */


/* ============================================================
   DOM ELEMENTS
============================================================ */

const themeToggle =
    document.getElementById("themeToggle");

const themePanel =
    document.getElementById("themePanel");

const themeOptions =
    document.querySelectorAll(".theme-option");

const contactForm =
    document.getElementById("contactForm");

const nameInput =
    document.getElementById("name");

const emailInput =
    document.getElementById("email");

const subjectInput =
    document.getElementById("subject");

const messageInput =
    document.getElementById("message");

const characterCount =
    document.getElementById("characterCount");

const sendButton =
    document.getElementById("sendButton");

const sendButtonText =
    document.getElementById("sendButtonText");

const successMessage =
    document.getElementById("successMessage");

const errorMessage =
    document.getElementById("errorMessage");

const pageToast =
    document.getElementById("pageToast");

const toastIcon =
    document.getElementById("toastIcon");

const toastText =
    document.getElementById("toastText");


/* ============================================================
   THEME PANEL
============================================================ */

if (themeToggle && themePanel) {

    themeToggle.addEventListener("click", function (event) {

        event.stopPropagation();

        themePanel.classList.toggle("active");

    });


    document.addEventListener("click", function (event) {

        if (
            !themePanel.contains(event.target) &&
            !themeToggle.contains(event.target)
        ) {

            themePanel.classList.remove("active");

        }

    });

}


/* ============================================================
   THEME CHANGE
============================================================ */

function applyTheme(theme) {

    document.body.classList.remove(
        "theme-pink",
        "theme-violet",
        "theme-blue",
        "theme-gold"
    );


    if (theme !== "default") {

        document.body.classList.add(
            "theme-" + theme
        );

    }


    localStorage.setItem(
        "charitybridge-contact-theme",
        theme
    );

}


/* ============================================================
   THEME BUTTONS
============================================================ */

themeOptions.forEach(function (option) {

    option.addEventListener("click", function () {

        const theme =
            option.getAttribute("data-theme");

        applyTheme(theme);

        if (themePanel) {
            themePanel.classList.remove("active");
        }

    });

});


/* ============================================================
   LOAD SAVED THEME
============================================================ */

const savedTheme =
    localStorage.getItem(
        "charitybridge-contact-theme"
    );


if (savedTheme) {

    applyTheme(savedTheme);

}


/* ============================================================
   CHARACTER COUNTER
============================================================ */

function updateCharacterCount() {

    if (!messageInput || !characterCount) {
        return;
    }


    const currentLength =
        messageInput.value.length;

    const maxLength =
        messageInput.maxLength;


    characterCount.textContent =
        currentLength +
        " / " +
        maxLength;

}


if (messageInput) {

    messageInput.addEventListener(
        "input",
        updateCharacterCount
    );

    updateCharacterCount();

}


/* ============================================================
   ERROR HELPERS
============================================================ */

function clearErrors() {

    document.getElementById("nameError").textContent = "";
    document.getElementById("emailError").textContent = "";
    document.getElementById("subjectError").textContent = "";
    document.getElementById("messageError").textContent = "";

}


function showFieldError(
    elementId,
    message
) {

    const element =
        document.getElementById(elementId);

    if (element) {

        element.textContent =
            message;

    }

}


/* ============================================================
   EMAIL VALIDATION
============================================================ */

function isValidEmail(email) {

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        .test(email);

}


/* ============================================================
   FORM VALIDATION
============================================================ */

function validateForm() {

    clearErrors();

    let valid = true;


    const name =
        nameInput.value.trim();

    const email =
        emailInput.value.trim();

    const subject =
        subjectInput.value.trim();

    const message =
        messageInput.value.trim();


    /* NAME */

    if (!name) {

        showFieldError(
            "nameError",
            "Please enter your name."
        );

        valid = false;

    } else if (name.length < 2) {

        showFieldError(
            "nameError",
            "Name must contain at least 2 characters."
        );

        valid = false;

    }


    /* EMAIL */

    if (!email) {

        showFieldError(
            "emailError",
            "Please enter your email address."
        );

        valid = false;

    } else if (!isValidEmail(email)) {

        showFieldError(
            "emailError",
            "Please enter a valid email address."
        );

        valid = false;

    }


    /* SUBJECT */

    if (!subject) {

        showFieldError(
            "subjectError",
            "Please enter a subject."
        );

        valid = false;

    } else if (subject.length < 3) {

        showFieldError(
            "subjectError",
            "Subject is too short."
        );

        valid = false;

    }


    /* MESSAGE */

    if (!message) {

        showFieldError(
            "messageError",
            "Please enter your message."
        );

        valid = false;

    } else if (message.length < 5) {

        showFieldError(
            "messageError",
            "Message is too short."
        );

        valid = false;

    }


    return valid;

}


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;


function showToast(
    message,
    type = "success"
) {

    if (!pageToast || !toastText) {
        return;
    }


    toastText.textContent =
        message;


    if (type === "error") {

        toastIcon.textContent = "!";

    } else {

        toastIcon.textContent = "✓";

    }


    pageToast.classList.add("show");


    if (toastTimer) {

        clearTimeout(toastTimer);

    }


    toastTimer =
        setTimeout(function () {

            pageToast.classList.remove("show");

        }, 3500);

}


/* ============================================================
   FORM SUBMIT
============================================================ */

if (contactForm) {

    contactForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            if (!validateForm()) {

                showToast(
                    "Please check the highlighted fields.",
                    "error"
                );

                return;

            }


            if (sendButton) {

                sendButton.classList.add("loading");

            }


            if (sendButtonText) {

                sendButtonText.textContent =
                    "Sending...";

            }


            if (successMessage) {

                successMessage.classList.remove("show");

            }


            if (errorMessage) {

                errorMessage.classList.remove("show");

            }


            try {

                const formData =
                    new FormData(contactForm);


                const response =
                    await fetch(
                        contactForm.action,
                        {
                            method: "POST",
                            body: formData,
                            headers: {
                                "X-Requested-With":
                                    "XMLHttpRequest"
                            }
                        }
                    );


                const contentType =
                    response.headers.get(
                        "content-type"
                    ) || "";


                if (!response.ok) {

                    throw new Error(
                        "Request failed"
                    );

                }


                /*
                 * If the Flask route returns JSON,
                 * use the JSON response.
                 */

                if (
                    contentType.includes(
                        "application/json"
                    )
                ) {

                    const data =
                        await response.json();


                    if (
                        data.success === false
                    ) {

                        throw new Error(
                            data.message ||
                            "Unable to send message."
                        );

                    }

                }


                /*
                 * Success
                 */

                contactForm.reset();

                updateCharacterCount();


                if (successMessage) {

                    successMessage.classList.add(
                        "show"
                    );

                }


                showToast(
                    "Your message was sent successfully.",
                    "success"
                );


            } catch (error) {

                console.error(
                    "CONTACT FORM ERROR:",
                    error
                );


                if (errorMessage) {

                    errorMessage.classList.add(
                        "show"
                    );

                }


                showToast(
                    "Unable to send your message right now.",
                    "error"
                );


            } finally {

                if (sendButton) {

                    sendButton.classList.remove(
                        "loading"
                    );

                }


                if (sendButtonText) {

                    sendButtonText.textContent =
                        "Send Message";

                }

            }

        }
    );

}


/* ============================================================
   INPUT INTERACTION
============================================================ */

[
    nameInput,
    emailInput,
    subjectInput,
    messageInput
].forEach(function (input) {

    if (!input) {
        return;
    }


    input.addEventListener(
        "input",
        function () {

            const errorElement =
                document.getElementById(
                    input.id + "Error"
                );


            if (errorElement) {

                errorElement.textContent = "";

            }

        }
    );

});


/* ============================================================
   ESCAPE KEY
============================================================ */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Escape" &&
            themePanel
        ) {

            themePanel.classList.remove(
                "active"
            );

        }

    }
);


/* ============================================================
   PAGE READY
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateCharacterCount();

    }
);