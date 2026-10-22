/* =========================================================
   CHARITYBRIDGE
   VOLUNTEER MISSION HUB
   VOLUNTEER.JS
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       BASIC ELEMENTS
       ===================================================== */

    var modal = document.querySelector(".help-modal");
    var modalBackdrop = document.querySelector(".modal-backdrop");
    var modalClose = document.querySelector(".modal-close");

    var helpButtons = document.querySelectorAll(".help-button");
    var modalAction = document.querySelector(".modal-action");

    var selectedRequestId = null;


    /* =====================================================
       PAGE ENTRANCE
       ===================================================== */

    document.body.classList.add("volunteer-loaded");


    /* =====================================================
       HELP REQUEST MODAL
       ===================================================== */

    function openHelpModal(button) {

        if (!modal) {
            return;
        }

        selectedRequestId = button.getAttribute("data-request-id");

        var requestType = button.getAttribute("data-request-type") || "Help Request";
        var requestLocation = button.getAttribute("data-request-location") || "Location not available";        var requesterName = button.getAttribute("data-requester") || "Community Member";
        var requestDescription = button.getAttribute("data-description") || "Help requested by a community member.";

        var modalType = document.getElementById("modalRequestType");
       var modalLocation = document.getElementById("modalLocation");
        var modalRequester = document.getElementById("modalRequester");
        var modalDescription = document.querySelector("[data-modal-description]");

        if (modalType) {
            modalType.textContent = requestType;
        }

        if (modalLocation) {
            modalLocation.textContent = requestLocation;
        }

        if (modalRequester) {
            modalRequester.textContent = requesterName;
        }

        if (modalDescription) {
            modalDescription.textContent = requestDescription;
        }

        modal.classList.add("active");
        document.body.style.overflow = "hidden";

        setTimeout(function () {
            if (modalClose) {
                modalClose.focus();
            }
        }, 100);
    }


    function closeHelpModal() {

        if (!modal) {
            return;
        }

        modal.classList.remove("active");
        document.body.style.overflow = "";

        selectedRequestId = null;
    }


    /* =====================================================
       HELP BUTTON EVENTS
       ===================================================== */

/* =====================================================
   HELP BUTTON EVENTS - NO POPUP
   ===================================================== */

if (helpButtons.length > 0) {
    helpButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            var requestId = button.getAttribute("data-request-id");

            if (!requestId || button.disabled) {
                return;
            }

            button.disabled = true;
            button.innerHTML = "<span>⏳</span> SENDING...";

            var form = document.createElement("form");
            form.method = "POST";
            form.action = "/volunteer/interest/" + encodeURIComponent(requestId);

            document.body.appendChild(form);
            form.submit();
        });
    });
}



    /* =====================================================
       MODAL CLOSE
       ===================================================== */

    if (modalClose) {

        modalClose.addEventListener("click", function () {
            closeHelpModal();
        });

    }


    if (modalBackdrop) {

        modalBackdrop.addEventListener("click", function () {
            closeHelpModal();
        });

    }


    /* =====================================================
       ESCAPE KEY
       ===================================================== */

    document.addEventListener("keydown", function (event) {

        if (event.key === "Escape") {

            if (modal && modal.classList.contains("active")) {
                closeHelpModal();
            }

        }

    });


    /* =====================================================
       VOLUNTEER / ACCEPT REQUEST
       ===================================================== */

    /* =====================================================
       VOLUNTEER INTEREST SUBMISSION
       ===================================================== */

    if (modalAction) {

        modalAction.addEventListener("click", function () {

            if (!selectedRequestId) {
                return;
            }

            var requestId = selectedRequestId;

            modalAction.disabled = true;
            modalAction.style.opacity = "0.65";

            modalAction.innerHTML = "<span>SENDING...</span>";

            var form = document.createElement("form");

            form.method = "POST";

            form.action =
                "/volunteer/interest/" +
                encodeURIComponent(requestId);

            document.body.appendChild(form);

            form.submit();

        });

    }



    /* =====================================================
       REQUEST CARD MOUSE LIGHT
       ===================================================== */

    var requestCards = document.querySelectorAll(".request-glass-card");

    requestCards.forEach(function (card) {

        card.addEventListener("mousemove", function (event) {

            var rect = card.getBoundingClientRect();

            var x =
                event.clientX - rect.left;

            var y =
                event.clientY - rect.top;

            var percentX =
                (x / rect.width) * 100;

            var percentY =
                (y / rect.height) * 100;

            card.style.background =
                "radial-gradient(circle at " +
                percentX +
                "% " +
                percentY +
                "%, rgba(99,239,255,0.08), transparent 35%), " +
                "linear-gradient(145deg, rgba(255,255,255,0.09), rgba(255,255,255,0.025))";

        });


        card.addEventListener("mouseleave", function () {

            card.style.background =
                "linear-gradient(145deg, rgba(255,255,255,0.09), rgba(255,255,255,0.025))";

        });

    });


    /* =====================================================
       STAT CARD LIGHT
       ===================================================== */

    var statCards = document.querySelectorAll(".stat-glass-card");

    statCards.forEach(function (card) {

        card.addEventListener("mousemove", function (event) {

            var rect = card.getBoundingClientRect();

            var x =
                event.clientX - rect.left;

            var y =
                event.clientY - rect.top;

            var percentX =
                (x / rect.width) * 100;

            var percentY =
                (y / rect.height) * 100;

            card.style.background =
                "radial-gradient(circle at " +
                percentX +
                "% " +
                percentY +
                "%, rgba(99,239,255,0.07), transparent 38%), " +
                "linear-gradient(145deg, rgba(255,255,255,0.085), rgba(255,255,255,0.025))";

        });


        card.addEventListener("mouseleave", function () {

            card.style.background =
                "linear-gradient(145deg, rgba(255,255,255,0.085), rgba(255,255,255,0.025))";

        });

    });


    /* =====================================================
       HERO ORBIT PARALLAX
       ===================================================== */

    var orbitArea =
        document.querySelector(".volunteer-orbit-area");

    if (orbitArea) {

        document.addEventListener("mousemove", function (event) {

            var width = window.innerWidth;
            var height = window.innerHeight;

            var moveX =
                (event.clientX - width / 2) / width;

            var moveY =
                (event.clientY - height / 2) / height;

            orbitArea.style.transform =
                "translate(" +
                (moveX * 10) +
                "px, " +
                (moveY * 10) +
                "px)";

        });

    }


    /* =====================================================
       INTERSECTION ANIMATION
       ===================================================== */

    var animatedElements = document.querySelectorAll(
        ".stat-glass-card, " +
        ".request-glass-card, " +
        ".journey-step, " +
        ".skills-glass-card, " +
        ".connection-glass"
    );


    if ("IntersectionObserver" in window) {

        var observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(function (entry) {

                        if (entry.isIntersecting) {

                            entry.target.classList.add(
                                "element-visible"
                            );

                            observer.unobserve(
                                entry.target
                            );
                        }

                    });

                },
                {
                    threshold: 0.12
                }
            );


        animatedElements.forEach(function (element) {

            element.style.opacity = "0";
            element.style.transform = "translateY(20px)";

            observer.observe(element);

        });


        var style = document.createElement("style");

        style.textContent = `
            .element-visible {
                opacity: 1 !important;
                transform: translateY(0) !important;
                transition:
                    opacity 0.8s ease,
                    transform 0.8s ease;
            }
        `;

        document.head.appendChild(style);

    }


    /* =====================================================
       FLASH MESSAGE CLOSE
       ===================================================== */

    var flashCloseButtons =
        document.querySelectorAll(".flash-close");


    flashCloseButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            var flash =
                button.closest(".flash-message");

            if (!flash) {
                return;
            }

            flash.style.opacity = "0";
            flash.style.transform = "translateX(30px)";

            setTimeout(function () {

                flash.remove();

            }, 350);

        });

    });


    /* =====================================================
       AUTO HIDE FLASH MESSAGES
       ===================================================== */

    var flashMessages =
        document.querySelectorAll(".flash-message");


    flashMessages.forEach(function (message) {

        setTimeout(function () {

            if (!message.parentNode) {
                return;
            }

            message.style.opacity = "0";
            message.style.transform = "translateX(30px)";

            setTimeout(function () {

                if (message.parentNode) {
                    message.remove();
                }

            }, 350);

        }, 6000);

    });


    /* =====================================================
       SMOOTH ANCHOR LINKS
       ===================================================== */

    var anchorLinks =
        document.querySelectorAll('a[href^="#"]');


    anchorLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            var targetId =
                link.getAttribute("href");

            if (!targetId || targetId === "#") {
                return;
            }

            var target =
                document.querySelector(targetId);

            if (!target) {
                return;
            }

            event.preventDefault();

            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        });

    });


    /* =====================================================
       FORM SUBMISSION LOADING STATE
       ===================================================== */

    var volunteerForm =
        document.querySelector(".volunteer-form");


    if (volunteerForm) {

        volunteerForm.addEventListener("submit", function () {

            var submitButton =
                volunteerForm.querySelector(
                    ".mission-button"
                );

            if (!submitButton) {
                return;
            }

            submitButton.disabled = true;

            submitButton.style.opacity = "0.7";

            var buttonText =
                submitButton.querySelector(
                    ".button-text"
                );

            if (buttonText) {
                buttonText.textContent =
                    "CONNECTING...";
            }

        });

    }


    /* =====================================================
       VISIBILITY PERFORMANCE
       ===================================================== */

    document.addEventListener(
        "visibilitychange",
        function () {

            var animatedBackground =
                document.querySelectorAll(
                    ".aurora, " +
                    ".floating-orb, " +
                    ".star-field, " +
                    ".orbit-ring"
                );


            animatedBackground.forEach(
                function (element) {

                    if (
                        document.hidden
                    ) {

                        element.style.animationPlayState =
                            "paused";

                    } else {

                        element.style.animationPlayState =
                            "running";

                    }

                }
            );

        }
    );


    /* =====================================================
       ACCESSIBILITY
       ===================================================== */

    helpButtons.forEach(function (button) {

        if (!button.getAttribute("aria-label")) {

            button.setAttribute(
                "aria-label",
                "Volunteer to help with this request"
            );

        }

    });


    if (modalClose) {

        modalClose.setAttribute(
            "aria-label",
            "Close volunteer request"
        );

    }


    /* =====================================================
       CONSOLE CHECK
       ===================================================== */

    console.log(
        "CharityBridge Volunteer Mission Hub loaded successfully."
    );

});