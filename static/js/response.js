```javascript
/* ============================================================
   CHARITYBRIDGE
   LIQUID GLASS RESPONSE PAGE
   RESPONSE.JS
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    /* ========================================================
       ELEMENTS
       ======================================================== */

    const modal = document.getElementById("responseModal");
    const modalClose = document.getElementById("modalClose");
    const modalOk = document.getElementById("modalOk");
    const modalBackdrop = document.querySelector(".modal-backdrop");

    const modalTitle = document.getElementById("modalTitle");
    const modalDescription = document.getElementById("modalDescription");

    const responseButtons = document.querySelectorAll(
        ".view-response-button"
    );

    const responseCards = document.querySelectorAll(
        ".response-card"
    );


    /* ========================================================
       PAGE ENTRANCE
       ======================================================== */

    document.body.classList.add("response-page-ready");


    /* ========================================================
       RESPONSE CARD ENTRANCE
       ======================================================== */

    responseCards.forEach(function (card, index) {

        card.style.opacity = "0";
        card.style.transform = "translateY(25px) scale(0.985)";

        window.setTimeout(function () {

            card.style.transition =
                "opacity 0.8s ease, transform 0.8s ease";

            card.style.opacity = "1";
            card.style.transform = "translateY(0) scale(1)";

        }, 250 + (index * 130));

    });


    /* ========================================================
       OPEN RESPONSE MODAL
       ======================================================== */

    function openModal(card) {

        if (!modal || !card) {
            return;
        }

        const category = card.querySelector(
            ".response-category h3"
        );

        const description = card.querySelector(
            ".response-message p"
        );

        if (modalTitle) {

            if (category) {
                modalTitle.textContent =
                    category.textContent.trim();
            } else {
                modalTitle.textContent = "Response";
            }

        }

        if (modalDescription) {

            if (description) {
                modalDescription.textContent =
                    description.textContent.trim();
            } else {
                modalDescription.textContent =
                    "No response details available.";
            }

        }

        modal.classList.add("active");

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.style.overflow = "hidden";


        /* Liquid glass entrance */

        const modalGlass = modal.querySelector(
            ".modal-glass"
        );

        if (
            modalGlass &&
            typeof modalGlass.animate === "function"
        ) {

            modalGlass.animate(
                [
                    {
                        transform:
                            "translateY(20px) scale(0.94)"
                    },
                    {
                        transform:
                            "translateY(-3px) scale(1.015)"
                    },
                    {
                        transform:
                            "translateY(0) scale(1)"
                    }
                ],
                {
                    duration: 500,
                    easing: "cubic-bezier(.2,.8,.2,1)"
                }
            );

        }

    }


    /* ========================================================
       CLOSE RESPONSE MODAL
       ======================================================== */

    function closeModal() {

        if (!modal) {
            return;
        }

        modal.classList.remove("active");

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.style.overflow = "";


        if (modalTitle) {
            modalTitle.textContent = "Response";
        }

        if (modalDescription) {
            modalDescription.textContent =
                "Response details will appear here.";
        }

    }


    /* ========================================================
       VIEW RESPONSE BUTTONS
       ======================================================== */

    responseButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const card = button.closest(
                ".response-card"
            );

            openModal(card);

        });

        button.setAttribute(
            "aria-label",
            "View response details"
        );

    });


    /* ========================================================
       CLOSE BUTTON
       ======================================================== */

    if (modalClose) {

        modalClose.addEventListener(
            "click",
            closeModal
        );

    }


    /* ========================================================
       MODAL OK BUTTON
       ======================================================== */

    if (modalOk) {

        modalOk.addEventListener(
            "click",
            closeModal
        );

    }


    /* ========================================================
       BACKDROP CLICK
       ======================================================== */

    if (modalBackdrop) {

        modalBackdrop.addEventListener(
            "click",
            closeModal
        );

    }


    /* ========================================================
       ESC KEY
       ======================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape" &&
                modal &&
                modal.classList.contains("active")
            ) {

                closeModal();

            }

        }
    );


    /* ========================================================
       LIQUID MOUSE LIGHT
       ======================================================== */

    responseCards.forEach(function (card) {

        card.addEventListener(
            "mousemove",
            function (event) {

                const rect =
                    card.getBoundingClientRect();

                const x =
                    event.clientX - rect.left;

                const y =
                    event.clientY - rect.top;

                card.style.setProperty(
                    "--mouse-x",
                    x + "px"
                );

                card.style.setProperty(
                    "--mouse-y",
                    y + "px"
                );

            }
        );


        card.addEventListener(
            "mouseleave",
            function () {

                card.style.removeProperty(
                    "--mouse-x"
                );

                card.style.removeProperty(
                    "--mouse-y"
                );

            }
        );

    });


    /* ========================================================
       SOFT PARALLAX FOR RESPONSE ORB
       ======================================================== */

    const orb = document.querySelector(
        ".response-orb"
    );

    const orbSection = document.querySelector(
        ".response-orb-section"
    );


    if (
        orb &&
        orbSection &&
        window.matchMedia("(pointer: fine)").matches
    ) {

        orbSection.addEventListener(
            "mousemove",
            function (event) {

                const rect =
                    orbSection.getBoundingClientRect();

                const centerX =
                    rect.left + (rect.width / 2);

                const centerY =
                    rect.top + (rect.height / 2);

                const moveX =
                    (event.clientX - centerX) / 25;

                const moveY =
                    (event.clientY - centerY) / 25;

                orb.style.transform =
                    "translate(" +
                    moveX +
                    "px, " +
                    moveY +
                    "px)";

            }
        );


        orbSection.addEventListener(
            "mouseleave",
            function () {

                orb.style.transform = "";

            }
        );

    }


    /* ========================================================
       INTERSECTION OBSERVER
       ======================================================== */

    const animatedElements =
        document.querySelectorAll(
            ".summary-card, .connection-glass"
        );


    if (
        "IntersectionObserver" in window &&
        animatedElements.length > 0
    ) {

        const observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(
                        function (entry) {

                            if (
                                entry.isIntersecting
                            ) {

                                entry.target.classList.add(
                                    "visible"
                                );

                                observer.unobserve(
                                    entry.target
                                );

                            }

                        }
                    );

                },
                {
                    threshold: 0.12
                }
            );


        animatedElements.forEach(
            function (element) {

                observer.observe(element);

            }
        );

    }


    /* ========================================================
       PAGE VISIBILITY
       ======================================================== */

    document.addEventListener(
        "visibilitychange",
        function () {

            const particles =
                document.querySelectorAll(
                    ".particle, .aurora, .stars"
                );


            particles.forEach(
                function (element) {

                    if (document.hidden) {

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


    /* ========================================================
       INITIAL PAGE MESSAGE
       ======================================================== */

    console.log(
        "CharityBridge Response Space loaded."
    );

});
```
