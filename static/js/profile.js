/* ============================================================
   CHARITYBRIDGE PROFILE JAVASCRIPT
============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    /* ========================================================
       ELEMENTS
    ======================================================== */

    const themeButton = document.getElementById("themeButton");
    const themePanel = document.getElementById("themePanel");

    const profileFab = document.getElementById("profileFab");
    const profileContent = document.getElementById("profileContent");

    const profileImageInput =
        document.getElementById("profileImageInput");


    /* ========================================================
       THEME PANEL
    ======================================================== */

    if (themeButton && themePanel) {

        themeButton.addEventListener("click", function (event) {

            event.stopPropagation();

            themePanel.classList.toggle("show");

        });

    }


    document.addEventListener("click", function (event) {

        if (!themePanel || !themeButton) {
            return;
        }

        if (
            !themePanel.contains(event.target) &&
            !themeButton.contains(event.target)
        ) {
            themePanel.classList.remove("show");
        }

    });


    /* ========================================================
       THEME OPTIONS
    ======================================================== */

    const themeOptions =
        document.querySelectorAll(".theme-option");

    themeOptions.forEach(function (button) {

        button.addEventListener("click", function () {

            const theme = button.dataset.theme;

            document.body.classList.remove(
                "theme-purple",
                "theme-pink",
                "theme-gold"
            );


            if (theme === "purple") {

                document.body.classList.add(
                    "theme-purple"
                );

            }

            else if (theme === "pink") {

                document.body.classList.add(
                    "theme-pink"
                );

            }

            else if (theme === "gold") {

                document.body.classList.add(
                    "theme-gold"
                );

            }


            localStorage.setItem(
                "charitybridge-profile-theme",
                theme
            );


            /* Close theme panel after selection */

            if (themePanel) {
                themePanel.classList.remove("show");
            }

        });

    });


    /* ========================================================
       LOAD SAVED THEME
    ======================================================== */

    const savedTheme =
        localStorage.getItem(
            "charitybridge-profile-theme"
        );


    if (savedTheme === "purple") {

        document.body.classList.add(
            "theme-purple"
        );

    }

    else if (savedTheme === "pink") {

        document.body.classList.add(
            "theme-pink"
        );

    }

    else if (savedTheme === "gold") {

        document.body.classList.add(
            "theme-gold"
        );

    }


    /* ========================================================
       PROFILE FAB
    ======================================================== */

    if (profileFab && profileContent) {

        profileFab.addEventListener("click", function () {

            const collapsed =
                profileContent.classList.toggle(
                    "collapsed"
                );


            profileFab.classList.toggle(
                "collapsed",
                collapsed
            );


            profileFab.setAttribute(
                "aria-expanded",
                String(!collapsed)
            );


            if (!collapsed) {

                setTimeout(function () {

                    profileContent.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                }, 100);

            }

        });

    }


    /* ========================================================
       PROFILE IMAGE PREVIEW
    ======================================================== */

    if (profileImageInput) {

        profileImageInput.addEventListener(
            "change",
            function () {

                const file =
                    profileImageInput.files &&
                    profileImageInput.files[0];


                if (!file) {
                    return;
                }


                /* --------------------------------------------
                   Allowed image types
                -------------------------------------------- */

                const allowedTypes = [
                    "image/png",
                    "image/jpeg",
                    "image/webp"
                ];


                if (!allowedTypes.includes(file.type)) {

                    alert(
                        "Please choose a PNG, JPG, JPEG or WEBP image."
                    );

                    profileImageInput.value = "";

                    return;
                }


                /* --------------------------------------------
                   Maximum 5 MB
                -------------------------------------------- */

                const maxSize =
                    5 * 1024 * 1024;


                if (file.size > maxSize) {

                    alert(
                        "Profile image must be smaller than 5 MB."
                    );

                    profileImageInput.value = "";

                    return;
                }


                /* --------------------------------------------
                   Read image
                -------------------------------------------- */

                const reader =
                    new FileReader();


                reader.onload =
                    function (event) {

                        /*
                         * IMPORTANT:
                         * Find the current preview every time.
                         * This prevents the old-element problem
                         * after the initial letter is replaced.
                         */

                        const currentPreview =
                            document.getElementById(
                                "uploadPreview"
                            );


                        if (!currentPreview) {
                            return;
                        }


                        if (
                            currentPreview.tagName === "IMG"
                        ) {

                            currentPreview.src =
                                event.target.result;

                        }

                        else {

                            const image =
                                document.createElement("img");


                            image.src =
                                event.target.result;


                            image.alt =
                                "Profile photo preview";


                            image.id =
                                "uploadPreview";


                            image.className =
                                currentPreview.className;


                            currentPreview.replaceWith(
                                image
                            );

                        }


                        /*
                         * Also update the large profile
                         * preview at the top if it exists.
                         */

                        const profilePreview =
                            document.getElementById(
                                "profilePreview"
                            );


                        if (profilePreview) {

                            if (
                                profilePreview.tagName === "IMG"
                            ) {

                                profilePreview.src =
                                    event.target.result;

                            }

                            else {

                                const profileImage =
                                    document.createElement("img");


                                profileImage.src =
                                    event.target.result;


                                profileImage.alt =
                                    "Profile photo";


                                profileImage.id =
                                    "profilePreview";


                                profileImage.className =
                                    "profile-photo";


                                profilePreview.replaceWith(
                                    profileImage
                                );

                            }

                        }

                    };


                reader.readAsDataURL(file);

            }
        );

    }


    /* ========================================================
       REAL IMPACT CHART
    ======================================================== */

    const chartCanvas =
        document.getElementById("impactChart");


    const dataElement =
        document.getElementById("profile-data");


    if (
        chartCanvas &&
        dataElement &&
        typeof Chart !== "undefined"
    ) {

        try {

            const profileData =
                JSON.parse(
                    dataElement.textContent.trim()
                );


            let labels =
                Array.isArray(profileData.labels)
                    ? profileData.labels
                    : [];


            let values =
                Array.isArray(profileData.values)
                    ? profileData.values
                    : [];


            /* --------------------------------------------
               Keep arrays equal
            -------------------------------------------- */

            const chartLength =
                Math.min(
                    labels.length,
                    values.length
                );


            labels =
                labels.slice(
                    0,
                    chartLength
                );


            values =
                values
                    .slice(
                        0,
                        chartLength
                    )
                    .map(function (value) {

                        const number =
                            Number(value);


                        return Number.isFinite(number)
                            ? number
                            : 0;

                    });


            /* --------------------------------------------
               Canvas
            -------------------------------------------- */

            const context =
                chartCanvas.getContext("2d");


            if (!context) {
                return;
            }


            /* --------------------------------------------
               No donation data
            -------------------------------------------- */

            if (labels.length === 0) {

                const parent =
                    chartCanvas.parentElement;


                if (parent) {

                    const message =
                        document.createElement("div");


                    message.className =
                        "empty-chart-message";


                    message.textContent =
                        "No successful donations recorded yet.";


                    parent.appendChild(
                        message
                    );

                }

                return;
            }


            /* --------------------------------------------
               Chart gradient
            -------------------------------------------- */

            const gradient =
                context.createLinearGradient(
                    0,
                    0,
                    0,
                    330
                );


            gradient.addColorStop(
                0,
                "rgba(98, 244, 255, 0.25)"
            );


            gradient.addColorStop(
                1,
                "rgba(98, 244, 255, 0.00)"
            );


            /* --------------------------------------------
               Create chart
            -------------------------------------------- */

            new Chart(
                context,
                {
                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [
                            {

                                label:
                                    "Successful Donations",

                                data:
                                    values,

                                borderColor:
                                    "#62f4ff",

                                backgroundColor:
                                    gradient,

                                borderWidth:
                                    2,

                                fill:
                                    true,

                                tension:
                                    0.42,

                                pointRadius:
                                    4,

                                pointHoverRadius:
                                    7,

                                pointBackgroundColor:
                                    "#62f4ff",

                                pointBorderColor:
                                    "#ffffff",

                                pointBorderWidth:
                                    1

                            }
                        ]

                    },


                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,


                        interaction: {

                            intersect:
                                false,

                            mode:
                                "index"

                        },


                        animation: {

                            duration:
                                1400,

                            easing:
                                "easeOutQuart"

                        },


                        plugins: {

                            legend: {

                                display:
                                    false

                            },


                            tooltip: {

                                backgroundColor:
                                    "rgba(4,10,24,0.92)",

                                borderColor:
                                    "rgba(98,244,255,0.25)",

                                borderWidth:
                                    1,

                                titleColor:
                                    "#ffffff",

                                bodyColor:
                                    "rgba(235,245,255,0.75)",

                                padding:
                                    12,

                                displayColors:
                                    false

                            }

                        },


                        scales: {

                            x: {

                                grid: {

                                    color:
                                        "rgba(255,255,255,0.055)",

                                    drawBorder:
                                        false

                                },


                                ticks: {

                                    color:
                                        "rgba(235,245,255,0.48)",

                                    font: {

                                        size:
                                            10

                                    }

                                }

                            },


                            y: {

                                beginAtZero:
                                    true,


                                grid: {

                                    color:
                                        "rgba(255,255,255,0.055)",

                                    drawBorder:
                                        false

                                },


                                ticks: {

                                    color:
                                        "rgba(235,245,255,0.48)",

                                    precision:
                                        0,

                                    font: {

                                        size:
                                            10

                                    }

                                }

                            }

                        }

                    }

                }
            );

        }

        catch (error) {

            console.error(
                "Profile graph error:",
                error
            );

        }

    }


    /* ========================================================
       SLOW CARD ENTRANCE
    ======================================================== */

    const cards =
        document.querySelectorAll(
            ".glass-card, .impact-card"
        );


    cards.forEach(function (card, index) {

        card.style.opacity =
            "0";


        card.style.transform =
            "translateY(24px)";


        setTimeout(function () {

            card.style.transition =
                "opacity 1s ease, transform 1s cubic-bezier(.16,.8,.2,1)";


            card.style.opacity =
                "1";


            card.style.transform =
                "translateY(0)";

        }, 350 + (index * 100));

    });


   
/* ========================================================
   PROFILE FORMS
======================================================== */

const profileForms =
    document.querySelectorAll(".profile-form");

profileForms.forEach(function (form) {

    form.addEventListener("submit", function () {

        const saveButton =
            form.querySelector(".save-button");

        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = "<span>✓</span> Saving...";
        }

    });

});


    /* ========================================================
       PHOTO UPLOAD FORM
    ======================================================== */
const photoForm = document.querySelector("#profilePhotoForm");
console.log("PHOTO FORM FOUND:", !!photoForm);
if (photoForm) {
        console.log("PHOTO FORM FOUND");
  photoForm.addEventListener("submit", function (event) {
    console.log("PHOTO FORM SUBMITTED");

    const fileInput = document.querySelector("#profileImageInput");
    const file = fileInput && fileInput.files[0];

    console.log("UPLOAD URL:", photoForm.action);
    console.log("SELECTED FILE:", file ? file.name : "NO FILE");

    if (!file) {
        event.preventDefault();
        alert("Please choose a profile photo first.");
        return;
    }

        const uploadButton = photoForm.querySelector(".photo-save-button");

        if (uploadButton) {
            uploadButton.disabled = true;
            uploadButton.textContent = "Uploading...";
        }
    });
}
   
});