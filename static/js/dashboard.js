/* ============================================================
   CHARITYBRIDGE DASHBOARD JS
============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    /* ========================================================
       RUDDER MENU
    ======================================================== */

    const rudderButton =
        document.getElementById("rudderButton");

    if (rudderButton) {

        rudderButton.addEventListener("click", function () {

            document.body.classList.toggle(
                "menu-collapsed"
            );

        });

    }
    /* ========================================================
   RUDDER SCROLL MOVEMENT
======================================================== */

window.addEventListener("scroll", function () {

    if (!rudderButton) return;

    const moveDown = Math.min(
        window.scrollY * 0.5,
        window.innerHeight - rudderButton.offsetHeight - 20
    );

    rudderButton.style.top = (20 + moveDown) + "px";

});


    /* ========================================================
       THEME BUTTON
    ======================================================== */

    const themeButton =
        document.getElementById("themeButton");

    const themes = [
        "ocean",
        "violet",
        "rose"
    ];

    let currentTheme =
        localStorage.getItem(
            "charitybridge-theme"
        ) || "ocean";

    document.body.dataset.theme =
        currentTheme;


    if (themeButton) {

        themeButton.addEventListener(
            "click",
            function () {

                let index =
                    themes.indexOf(currentTheme);

                index++;

                if (index >= themes.length) {
                    index = 0;
                }

                currentTheme =
                    themes[index];

                document.body.dataset.theme =
                    currentTheme;

                localStorage.setItem(
                    "charitybridge-theme",
                    currentTheme
                );

            }
        );

    }


    /* ========================================================
       REAL IMPACT CHART
    ======================================================== */

    const chartElement =
        document.getElementById("impactChart");


    if (
        chartElement &&
        window.CHARITYBRIDGE_DATA
    ) {

        const labels =
            window.CHARITYBRIDGE_DATA.impactLabels || [];

        const values =
            window.CHARITYBRIDGE_DATA.impactValues || [];


        const ctx =
            chartElement.getContext("2d");


        const gradient =
            ctx.createLinearGradient(
                0,
                0,
                0,
                210
            );


        gradient.addColorStop(
            0,
            "rgba(59, 224, 255, 0.42)"
        );


        gradient.addColorStop(
            1,
            "rgba(70, 107, 255, 0.02)"
        );


        new Chart(ctx, {

            type: "line",

            data: {

                labels: labels,

                datasets: [

                    {
                        data: values,

                        borderColor:
                            "#59eaff",

                        backgroundColor:
                            gradient,

                        borderWidth: 3,

                        pointBackgroundColor:
                            "#ffffff",

                        pointBorderColor:
                            "#55efff",

                        pointBorderWidth: 2,

                        pointRadius: 3.5,

                        pointHoverRadius: 6,

                        fill: true,

                        tension: 0.45
                    }

                ]
            },


            options: {

                responsive: true,

                maintainAspectRatio: false,

                animation: {

                    duration: 1800,

                    easing:
                        "easeOutQuart"
                },


                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        backgroundColor:
                            "rgba(8, 24, 45, 0.94)",

                        borderColor:
                            "rgba(86, 236, 255, 0.4)",

                        borderWidth: 1,

                        titleColor:
                            "#ffffff",

                        bodyColor:
                            "#ffffff",

                        padding: 12,

                        displayColors: false,

                        callbacks: {

                            label: function (context) {

                                return " ₹" +
                                    Number(
                                        context.raw || 0
                                    ).toLocaleString("en-IN");

                            }

                        }

                    }

                },


                scales: {

                    x: {

                        grid: {

                            color:
                                "rgba(255,255,255,0.06)",

                            drawBorder: false
                        },

                        ticks: {

                            color:
                                "rgba(255,255,255,0.72)",

                            font: {
                                size: 11
                            }
                        }

                    },


                    y: {

                        beginAtZero: true,

                        grid: {

                            color:
                                "rgba(255,255,255,0.07)",

                            drawBorder: false
                        },

                        ticks: {

                            color:
                                "rgba(255,255,255,0.65)",

                            font: {
                                size: 10
                            },

                            callback: function (value) {

                                return "₹" +
                                    Number(value)
                                        .toLocaleString("en-IN");

                            }

                        }

                    }

                }

            }

        });

    }


    /* ========================================================
       SLOW CARD ENTRANCE
    ======================================================== */

    const cards =
        document.querySelectorAll(
            ".stat-card, .impact-panel, .activity-panel, .kindness-card"
        );


    cards.forEach(function (card, index) {

        card.style.opacity = "0";

        card.style.transform =
            "translateY(25px)";


        setTimeout(function () {

            card.style.transition =
                "opacity 1s ease, transform 1s cubic-bezier(0.22, 1, 0.36, 1)";

            card.style.opacity = "1";

            card.style.transform =
                "translateY(0)";

        }, 450 + (index * 120));

    });


    /* ========================================================
       MOUSE GLASS MOVEMENT
    ======================================================== */

    const glassPanels =
        document.querySelectorAll(
            ".stat-card, .glass-panel"
        );


    glassPanels.forEach(function (panel) {

        panel.addEventListener(
            "mousemove",
            function (event) {

                const rect =
                    panel.getBoundingClientRect();

                const x =
                    event.clientX - rect.left;

                const y =
                    event.clientY - rect.top;

                const rotateX =
                    ((y / rect.height) - 0.5) * -2;

                const rotateY =
                    ((x / rect.width) - 0.5) * 2;

                panel.style.transform =
                    "perspective(900px) " +
                    "rotateX(" +
                    rotateX +
                    "deg) " +
                    "rotateY(" +
                    rotateY +
                    "deg) " +
                    "translateY(-2px)";

            }
        );


        panel.addEventListener(
            "mouseleave",
            function () {

                panel.style.transform =
                    "";

            }
        );

    });
    
    /* ========================================================
       NOTIFICATIONS NAVIGATION
    ======================================================== */

    const notificationLink =
        document.getElementById("notificationsMenuLink");

    const notificationSection =
        document.getElementById("notifications");

    if (notificationLink && notificationSection) {
        notificationLink.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            notificationSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        });
    }


});