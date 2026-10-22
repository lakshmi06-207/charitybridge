/* =========================================================
   CHARITYBRIDGE
   FOUNDER IMPACT OBSERVATORY
========================================================= */

(function () {
    "use strict";


    /* =====================================================
       HELPERS
    ====================================================== */

    function parseArray(value, fallback) {
        if (!value) {
            return fallback;
        }

        try {
            var parsed = JSON.parse(value);

            if (Array.isArray(parsed)) {
                return parsed;
            }

            return fallback;
        } catch (error) {
            console.warn("Unable to parse chart data:", error);
            return fallback;
        }
    }


    function getImpactData() {
        var element = document.getElementById("impactData");

        if (!element) {
            return {
                userGrowthLabels: [],
                userGrowthValues: [],
                moneyGrowthLabels: [],
                moneyGrowthValues: [],
                donationCategoryLabels: [],
                donationCategoryValues: [],
                requestStatusLabels: [],
                requestStatusValues: [],
                activityLabels: [],
                activityDonations: [],
                activityRequests: [],
                activityVolunteers: []
            };
        }

        return {
            userGrowthLabels: parseArray(
                element.dataset.userGrowthLabels,
                []
            ),

            userGrowthValues: parseArray(
                element.dataset.userGrowthValues,
                []
            ),

            moneyGrowthLabels: parseArray(
                element.dataset.moneyGrowthLabels,
                []
            ),

            moneyGrowthValues: parseArray(
                element.dataset.moneyGrowthValues,
                []
            ),

            donationCategoryLabels: parseArray(
                element.dataset.donationCategoryLabels,
                []
            ),

            donationCategoryValues: parseArray(
                element.dataset.donationCategoryValues,
                []
            ),

            requestStatusLabels: parseArray(
                element.dataset.requestStatusLabels,
                []
            ),

            requestStatusValues: parseArray(
                element.dataset.requestStatusValues,
                []
            ),

            activityLabels: parseArray(
                element.dataset.activityLabels,
                []
            ),

            activityDonations: parseArray(
                element.dataset.activityDonations,
                []
            ),

            activityRequests: parseArray(
                element.dataset.activityRequests,
                []
            ),

            activityVolunteers: parseArray(
                element.dataset.activityVolunteers,
                []
            )
        };
    }


    /* =====================================================
       CHART DEFAULTS
    ====================================================== */

    function createChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,

            animation: {
                duration: 1500,
                easing: "easeOutQuart"
            },

            interaction: {
                intersect: false,
                mode: "index"
            },

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    backgroundColor: "rgba(5, 8, 24, 0.94)",
                    titleColor: "#ffffff",
                    bodyColor: "rgba(255,255,255,0.72)",
                    borderColor: "rgba(125,234,255,0.20)",
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 12
                }
            },

            scales: {
                x: {
                    border: {
                        display: false
                    },

                    grid: {
                        color: "rgba(255,255,255,0.045)"
                    },

                    ticks: {
                        color: "rgba(255,255,255,0.42)",
                        font: {
                            size: 9
                        }
                    }
                },

                y: {
                    beginAtZero: true,

                    border: {
                        display: false
                    },

                    grid: {
                        color: "rgba(255,255,255,0.045)"
                    },

                    ticks: {
                        color: "rgba(255,255,255,0.42)",
                        font: {
                            size: 9
                        }
                    }
                }
            }
        };
    }


    /* =====================================================
       EMPTY CHART MESSAGE
    ====================================================== */

    function showEmptyChart(canvasId, message) {
        var canvas = document.getElementById(canvasId);

        if (!canvas) {
            return;
        }

        var parent = canvas.parentElement;

        parent.classList.add("chart-empty");

        var existing = parent.querySelector(".empty-chart-message");

        if (existing) {
            return;
        }

        var messageElement = document.createElement("div");

        messageElement.className = "empty-chart-message";
        messageElement.textContent = message;

        parent.appendChild(messageElement);
    }


    /* =====================================================
       USER GROWTH CHART
    ====================================================== */

    function createUserGrowthChart(data) {
        var canvas = document.getElementById("userGrowthChart");

        if (!canvas) {
            return;
        }

        if (
            data.userGrowthLabels.length === 0 ||
            data.userGrowthValues.length === 0
        ) {
            showEmptyChart(
                "userGrowthChart",
                "No user growth data available yet."
            );
            return;
        }

        new Chart(
            canvas,
            {
                type: "line",

                data: {
                    labels: data.userGrowthLabels,

                    datasets: [
                        {
                            label: "Users",
                            data: data.userGrowthValues,

                            borderColor: "#78e9ff",
                            backgroundColor:
                                "rgba(120,233,255,0.08)",

                            borderWidth: 2,

                            fill: true,

                            tension: 0.42,

                            pointRadius: 3,

                            pointHoverRadius: 6,

                            pointBackgroundColor: "#ffffff",

                            pointBorderColor: "#78e9ff",

                            pointBorderWidth: 2
                        }
                    ]
                },

                options: createChartOptions()
            }
        );
    }


    /* =====================================================
       MONEY DONATION CHART
    ====================================================== */

    function createMoneyGrowthChart(data) {
        var canvas = document.getElementById("moneyGrowthChart");

        if (!canvas) {
            return;
        }

        if (
            data.moneyGrowthLabels.length === 0 ||
            data.moneyGrowthValues.length === 0
        ) {
            showEmptyChart(
                "moneyGrowthChart",
                "No successful money donations available yet."
            );
            return;
        }

        var options = createChartOptions();

        options.scales.y.ticks.callback = function (value) {
            return "₹" + value;
        };

        new Chart(
            canvas,
            {
                type: "line",

                data: {
                    labels: data.moneyGrowthLabels,

                    datasets: [
                        {
                            label: "Money Donated",
                            data: data.moneyGrowthValues,

                            borderColor: "#ffd36d",

                            backgroundColor:
                                "rgba(255,211,109,0.08)",

                            borderWidth: 2,

                            fill: true,

                            tension: 0.42,

                            pointRadius: 3,

                            pointHoverRadius: 6,

                            pointBackgroundColor: "#ffffff",

                            pointBorderColor: "#ffd36d",

                            pointBorderWidth: 2
                        }
                    ]
                },

                options: options
            }
        );
    }


    /* =====================================================
       DONATION CATEGORY CHART
    ====================================================== */

    function createDonationCategoryChart(data) {
        var canvas = document.getElementById(
            "donationCategoryChart"
        );

        if (!canvas) {
            return;
        }

        if (
            data.donationCategoryLabels.length === 0 ||
            data.donationCategoryValues.length === 0
        ) {
            showEmptyChart(
                "donationCategoryChart",
                "No item donation data available yet."
            );
            return;
        }

        new Chart(
            canvas,
            {
                type: "doughnut",

                data: {
                    labels: data.donationCategoryLabels,

                    datasets: [
                        {
                            data: data.donationCategoryValues,

                            backgroundColor: [
                                "#6de4ff",
                                "#9d7cff",
                                "#ff82ca",
                                "#ffd36d",
                                "#73e6b4",
                                "#8ba9ff",
                                "#d7d7e8"
                            ],

                            borderColor:
                                "rgba(5,7,22,0.9)",

                            borderWidth: 2,

                            hoverOffset: 8
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    cutout: "66%",

                    animation: {
                        duration: 1500
                    },

                    plugins: {
                        legend: {
                            position: "bottom",

                            labels: {
                                color:
                                    "rgba(255,255,255,0.58)",

                                padding: 14,

                                boxWidth: 9,

                                font: {
                                    size: 9
                                }
                            }
                        },

                        tooltip: {
                            backgroundColor:
                                "rgba(5,8,24,0.94)",

                            titleColor: "#ffffff",

                            bodyColor:
                                "rgba(255,255,255,0.72)",

                            borderColor:
                                "rgba(125,234,255,0.20)",

                            borderWidth: 1,

                            padding: 12,

                            cornerRadius: 12
                        }
                    }
                }
            }
        );
    }


    /* =====================================================
       REQUEST STATUS CHART
    ====================================================== */

    function createRequestStatusChart(data) {
        var canvas = document.getElementById(
            "requestStatusChart"
        );

        if (!canvas) {
            return;
        }

        if (
            data.requestStatusLabels.length === 0 ||
            data.requestStatusValues.length === 0
        ) {
            showEmptyChart(
                "requestStatusChart",
                "No help request data available yet."
            );
            return;
        }

        new Chart(
            canvas,
            {
                type: "doughnut",

                data: {
                    labels: data.requestStatusLabels,

                    datasets: [
                        {
                            data: data.requestStatusValues,

                            backgroundColor: [
                                "#ffd36d",
                                "#72e7ff",
                                "#73e6b4",
                                "#ff82ca",
                                "#9d7cff",
                                "#aab1c7"
                            ],

                            borderColor:
                                "rgba(5,7,22,0.9)",

                            borderWidth: 2,

                            hoverOffset: 8
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    cutout: "66%",

                    animation: {
                        duration: 1500
                    },

                    plugins: {
                        legend: {
                            position: "bottom",

                            labels: {
                                color:
                                    "rgba(255,255,255,0.58)",

                                padding: 14,

                                boxWidth: 9,

                                font: {
                                    size: 9
                                }
                            }
                        },

                        tooltip: {
                            backgroundColor:
                                "rgba(5,8,24,0.94)",

                            titleColor: "#ffffff",

                            bodyColor:
                                "rgba(255,255,255,0.72)",

                            borderColor:
                                "rgba(125,234,255,0.20)",

                            borderWidth: 1,

                            padding: 12,

                            cornerRadius: 12
                        }
                    }
                }
            }
        );
    }


    /* =====================================================
       COMMUNITY ACTIVITY CHART
    ====================================================== */

    function createCommunityActivityChart(data) {
        var canvas = document.getElementById(
            "communityActivityChart"
        );

        if (!canvas) {
            return;
        }

        if (data.activityLabels.length === 0) {
            showEmptyChart(
                "communityActivityChart",
                "No monthly activity data available yet."
            );
            return;
        }

        new Chart(
            canvas,
            {
                type: "bar",

                data: {
                    labels: data.activityLabels,

                    datasets: [
                        {
                            label: "Donations",
                            data: data.activityDonations,

                            backgroundColor:
                                "rgba(109,228,255,0.65)",

                            borderColor: "#6de4ff",

                            borderWidth: 1,

                            borderRadius: 7
                        },

                        {
                            label: "Requests",
                            data: data.activityRequests,

                            backgroundColor:
                                "rgba(157,124,255,0.65)",

                            borderColor: "#9d7cff",

                            borderWidth: 1,

                            borderRadius: 7
                        },

                        {
                            label: "Volunteers",
                            data: data.activityVolunteers,

                            backgroundColor:
                                "rgba(255,130,202,0.65)",

                            borderColor: "#ff82ca",

                            borderWidth: 1,

                            borderRadius: 7
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    animation: {
                        duration: 1500
                    },

                    plugins: {
                        legend: {
                            position: "top",

                            labels: {
                                color:
                                    "rgba(255,255,255,0.58)",

                                boxWidth: 10,

                                padding: 16,

                                font: {
                                    size: 9
                                }
                            }
                        },

                        tooltip: {
                            backgroundColor:
                                "rgba(5,8,24,0.94)",

                            titleColor: "#ffffff",

                            bodyColor:
                                "rgba(255,255,255,0.72)",

                            borderColor:
                                "rgba(125,234,255,0.20)",

                            borderWidth: 1,

                            padding: 12,

                            cornerRadius: 12
                        }
                    },

                    scales: {
                        x: {
                            stacked: false,

                            border: {
                                display: false
                            },

                            grid: {
                                display: false
                            },

                            ticks: {
                                color:
                                    "rgba(255,255,255,0.42)",

                                font: {
                                    size: 9
                                }
                            }
                        },

                        y: {
                            beginAtZero: true,

                            border: {
                                display: false
                            },

                            grid: {
                                color:
                                    "rgba(255,255,255,0.045)"
                            },

                            ticks: {
                                color:
                                    "rgba(255,255,255,0.42)",

                                font: {
                                    size: 9
                                }
                            }
                        }
                    }
                }
            }
        );
    }


    /* =====================================================
       CHART EMPTY STATE CSS
    ====================================================== */

    function addEmptyChartStyles() {
        var style = document.createElement("style");

        style.textContent = `
            .chart-empty {
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .chart-empty canvas {
                display: none !important;
            }

            .empty-chart-message {
                width: 100%;
                padding: 30px;
                text-align: center;
                color: rgba(255,255,255,0.38);
                font-size: 11px;
                letter-spacing: 0.03em;
            }
        `;

        document.head.appendChild(style);
    }


    /* =====================================================
       GLASS BREAK INTRO
    ====================================================== */

    function startGlassBreak() {
        var glassBreak = document.getElementById("glassBreak");
        var page = document.getElementById("observatoryPage");

        if (!glassBreak || !page) {
            return;
        }

        window.setTimeout(
            function () {
                glassBreak.classList.add("is-hidden");
                page.classList.add("page-visible");
            },
            3200
        );
    }


    /* =====================================================
       CARD LIGHT EFFECT
    ====================================================== */

    function addCardLightEffect() {
        var cards = document.querySelectorAll(
            ".metric-card, .chart-panel, .flow-node"
        );

        cards.forEach(
            function (card) {

                card.addEventListener(
                    "mousemove",
                    function (event) {

                        var rect =
                            card.getBoundingClientRect();

                        var x =
                            event.clientX - rect.left;

                        var y =
                            event.clientY - rect.top;

                        card.style.background =
                            "radial-gradient(circle at " +
                            x +
                            "px " +
                            y +
                            "px, rgba(120,220,255,0.10), rgba(255,255,255,0.035) 45%)";
                    }
                );

                card.addEventListener(
                    "mouseleave",
                    function () {
                        card.style.background = "";
                    }
                );
            }
        );
    }


    /* =====================================================
       IMPACT CORE PARALLAX
    ====================================================== */

    function addCoreParallax() {
        var core = document.querySelector(
            ".impact-core-area"
        );

        if (!core) {
            return;
        }

        document.addEventListener(
            "mousemove",
            function (event) {

                var x =
                    (event.clientX /
                        window.innerWidth -
                        0.5) *
                    8;

                var y =
                    (event.clientY /
                        window.innerHeight -
                        0.5) *
                    8;

                core.style.transform =
                    "translate3d(" +
                    x +
                    "px," +
                    y +
                    "px,0)";
            }
        );
    }


    /* =====================================================
       NUMBER ENTRANCE
    ====================================================== */

    function animateMetricCards() {
        var cards = document.querySelectorAll(
            ".metric-card"
        );

        cards.forEach(
            function (card, index) {

                card.style.opacity = "0";
                card.style.transform =
                    "translateY(20px)";

                window.setTimeout(
                    function () {

                        card.style.transition =
                            "opacity 0.7s ease, transform 0.7s ease";

                        card.style.opacity = "1";
                        card.style.transform =
                            "translateY(0)";

                    },
                    3300 + index * 100
                );
            }
        );
    }


    /* =====================================================
       INITIALIZE
    ====================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        function () {

            addEmptyChartStyles();

            var data = getImpactData();

            if (
                typeof Chart === "undefined"
            ) {
                console.error(
                    "Chart.js was not loaded."
                );
            } else {
                createUserGrowthChart(data);
                createMoneyGrowthChart(data);
                createDonationCategoryChart(data);
                createRequestStatusChart(data);
                createCommunityActivityChart(data);
            }

            startGlassBreak();

            addCardLightEffect();

            addCoreParallax();

            animateMetricCards();

            console.log(
                "CharityBridge Impact Observatory loaded."
            );
        }
    );

})();