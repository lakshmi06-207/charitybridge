/* =========================================================
   CHARITYBRIDGE HOME PAGE
   FUTURISTIC ANIMATION + REAL DATABASE COUNTERS
========================================================= */


/* =========================================================
   PAGE LOADED
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* =================================================
           REAL VALUE COUNTERS
        ================================================== */

        const counters =
            document.querySelectorAll(".counter");


        counters.forEach(
            function (counter) {


                const target =
                    parseInt(
                        counter.getAttribute(
                            "data-target"
                        )
                    ) || 0;


                let current = 0;


                const duration = 1800;

                const startTime =
                    performance.now();


                function animateCounter(
                    currentTime
                ) {

                    const progress =
                        Math.min(
                            (
                                currentTime -
                                startTime
                            ) / duration,
                            1
                        );


                    /* Smooth animation */

                    const eased =
                        1 -
                        Math.pow(
                            1 - progress,
                            3
                        );


                    current =
                        Math.floor(
                            eased * target
                        );


                    counter.textContent =
                        current.toLocaleString(
                            "en-IN"
                        );


                    if (progress < 1) {

                        requestAnimationFrame(
                            animateCounter
                        );

                    } else {

                        counter.textContent =
                            target.toLocaleString(
                                "en-IN"
                            );

                    }

                }


                requestAnimationFrame(
                    animateCounter
                );

            }
        );



        /* =================================================
           MOUSE MAGIC
        ================================================== */

        const hero =
            document.querySelector(".hero");

        const background =
            document.querySelector(
                ".hero-image"
            );

        const heroLeft =
            document.querySelector(
                ".hero-left"
            );


        if (
            hero &&
            background &&
            heroLeft
        ) {

            hero.addEventListener(
                "mousemove",
                function (event) {


                    const rect =
                        hero.getBoundingClientRect();


                    const x =
                        event.clientX -
                        rect.left;


                    const y =
                        event.clientY -
                        rect.top;


                    const centerX =
                        rect.width / 2;


                    const centerY =
                        rect.height / 2;


                    const moveX =
                        (
                            x -
                            centerX
                        ) /
                        centerX;


                    const moveY =
                        (
                            y -
                            centerY
                        ) /
                        centerY;


                    /* Background reacts */

                    background.style.transform =
                        `
                        scale(1.06)
                        translate(
                            ${moveX * -10}px,
                            ${moveY * -7}px
                        )
                        `;


                    /* Text reacts slightly */

                    heroLeft.style.transform =
                        `
                        translate(
                            ${moveX * 4}px,
                            ${moveY * 3}px
                        )
                        `;

                }
            );


            hero.addEventListener(
                "mouseleave",
                function () {


                    background.style.transform =
                        "scale(1.03)";


                    heroLeft.style.transform =
                        "translate(0,0)";

                }
            );

        }



        /* =================================================
           GLASS CARD TILT
        ================================================== */

        const cards =
            document.querySelectorAll(
                ".impact-card"
            );


        cards.forEach(
            function (card) {


                card.addEventListener(
                    "mousemove",
                    function (event) {


                        const rect =
                            card.getBoundingClientRect();


                        const x =
                            event.clientX -
                            rect.left;


                        const y =
                            event.clientY -
                            rect.top;


                        const rotateY =
                            (
                                x -
                                rect.width / 2
                            ) /
                            18;


                        const rotateX =
                            (
                                rect.height / 2 -
                                y
                            ) /
                            18;


                        card.style.transform =
                            `
                            perspective(700px)
                            rotateX(${rotateX}deg)
                            rotateY(${rotateY}deg)
                            scale(1.04)
                            `;

                    }
                );


                card.addEventListener(
                    "mouseleave",
                    function () {


                        card.style.transform =
                            "";

                    }
                );

            }
        );



        /* =================================================
           FLOATING PARTICLES
        ================================================== */

        const particleContainer =
            document.querySelector(
                ".particles"
            );


        if (particleContainer) {


            for (
                let i = 0;
                i < 35;
                i++
            ) {


                const particle =
                    document.createElement(
                        "span"
                    );


                particle.className =
                    "particle";


                particle.style.left =
                    Math.random() * 100 +
                    "%";


                particle.style.top =
                    Math.random() * 100 +
                    "%";


                particle.style.animationDuration =
                    (
                        5 +
                        Math.random() * 8
                    ) +
                    "s";


                particle.style.animationDelay =
                    (
                        Math.random() * 5
                    ) +
                    "s";


                particleContainer.appendChild(
                    particle
                );

            }

        }



        /* =================================================
           SMOOTH NAVIGATION
        ================================================== */

        document
            .querySelectorAll(
                'a[href^="#"]'
            )
            .forEach(
                function (link) {


                    link.addEventListener(
                        "click",
                        function (event) {


                            const targetId =
                                this.getAttribute(
                                    "href"
                                );


                            if (
                                targetId ===
                                "#"
                            ) {

                                return;

                            }


                            const target =
                                document.querySelector(
                                    targetId
                                );


                            if (target) {

                                event.preventDefault();


                                target.scrollIntoView(
                                    {
                                        behavior:
                                            "smooth"
                                    }
                                );

                            }

                        }
                    );

                }
            );



        /* =================================================
           NAV ACTIVE STATE
        ================================================== */

        const navLinks =
            document.querySelectorAll(
                ".nav-links a"
            );


        navLinks.forEach(
            function (link) {


                link.addEventListener(
                    "click",
                    function () {


                        navLinks.forEach(
                            function (item) {

                                item.classList.remove(
                                    "active"
                                );

                            }
                        );


                        this.classList.add(
                            "active"
                        );

                    }
                );

            }
        );

    }
);