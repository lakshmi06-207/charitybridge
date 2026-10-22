/* =========================================================
   CHARITYBRIDGE REQUEST PAGE
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const themeButton =
        document.getElementById("themeButton");

    const themePanel =
        document.getElementById("themePanel");

    const closeTheme =
        document.getElementById("closeTheme");

    const themeOptions =
        document.querySelectorAll(".theme-option");

    const description =
        document.getElementById("description");

    const characterCount =
        document.getElementById("characterCount");

    const requestForm =
        document.getElementById("requestForm");

    const submitButton =
        document.getElementById("submitRequest");


    /* =====================================================
       THEME PANEL
    ====================================================== */

    if (themeButton && themePanel) {

        themeButton.addEventListener("click", function (event) {

            event.stopPropagation();

            themePanel.classList.toggle("show");

        });

    }


    if (closeTheme && themePanel) {

        closeTheme.addEventListener("click", function () {

            themePanel.classList.remove("show");

        });

    }


    document.addEventListener("click", function (event) {

        if (
            themePanel &&
            !themePanel.contains(event.target) &&
            event.target !== themeButton
        ) {
            themePanel.classList.remove("show");
        }

    });


    /* =====================================================
       THEMES
    ====================================================== */

    themeOptions.forEach(function (option) {

        option.addEventListener("click", function () {

            const theme =
                option.getAttribute("data-theme");

            document.body.setAttribute(
                "data-theme",
                theme
            );


            themeOptions.forEach(function (item) {

                item.classList.remove("active");

            });


            option.classList.add("active");

            localStorage.setItem(
                "charitybridge_request_theme",
                theme
            );

        });

    });


    /* =====================================================
       RESTORE THEME
    ====================================================== */

    const savedTheme =
        localStorage.getItem(
            "charitybridge_request_theme"
        );


    if (savedTheme) {

        document.body.setAttribute(
            "data-theme",
            savedTheme
        );


        themeOptions.forEach(function (option) {

            option.classList.remove("active");

            if (
                option.getAttribute("data-theme") ===
                savedTheme
            ) {
                option.classList.add("active");
            }

        });

    }


    /* =====================================================
       CHARACTER COUNT
    ====================================================== */

    if (description && characterCount) {

        function updateCharacterCount() {

            const length =
                description.value.length;

            characterCount.textContent =
                length + " / 1000";

        }


        description.addEventListener(
            "input",
            updateCharacterCount
        );


        updateCharacterCount();

    }


    /* =====================================================
       FORM SUBMIT EFFECT
    ====================================================== */

    if (requestForm && submitButton) {

        requestForm.addEventListener(
            "submit",
            function (event) {

                if (!requestForm.checkValidity()) {
                    return;
                }


                submitButton.disabled = true;


                submitButton.querySelector(
                    ".submit-text"
                ).textContent =
                    "Saving Request...";


                submitButton.querySelector(
                    ".submit-arrow"
                ).textContent =
                    "✦";

            }
        );

    }


    /* =====================================================
       SMOOTH CARD ENTRANCE
    ====================================================== */

    const cards =
        document.querySelectorAll(".history-card");


    cards.forEach(function (card, index) {

        card.style.opacity = "0";

        card.style.transform =
            "translateY(18px)";


        setTimeout(function () {

            card.style.transition =
                "opacity 0.6s ease, transform 0.6s ease";

            card.style.opacity = "1";

            card.style.transform =
                "translateY(0)";

        }, 150 + (index * 90));

    });

});

document.addEventListener("DOMContentLoaded", () => {
    const typeSelect = document.getElementById("request_type");
    const moneyFields = document.getElementById("moneyFields");
    const amountInput = document.getElementById("amount");
    const qrInput = document.getElementById("upi_qr_image");

    function toggleMoneyFields() {
        const isMoney = typeSelect && typeSelect.value === "Money";

        if (moneyFields) {
            moneyFields.hidden = !isMoney;
        }

        if (amountInput) {
            amountInput.disabled = !isMoney;
            amountInput.required = isMoney;

            if (!isMoney) {
                amountInput.value = "";
            }
        }

        if (qrInput) {
            qrInput.disabled = !isMoney;

            if (!isMoney) {
                qrInput.value = "";
            }
        }
    }

    if (typeSelect) {
        typeSelect.addEventListener("change", toggleMoneyFields);
        toggleMoneyFields();
    }
});
