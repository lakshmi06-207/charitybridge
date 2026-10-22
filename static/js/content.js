/* =========================================================
   CHARITYBRIDGE - CONTENT PAGE JAVASCRIPT
   Animated + Interactive Content Page
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       PAGE LOAD ANIMATION
    ===================================================== */

    document.body.classList.add("content-page-loaded");


    /* =====================================================
       NAVBAR SCROLL EFFECT
    ===================================================== */

    const navbar = document.querySelector(".navbar");

    if (navbar) {

        window.addEventListener("scroll", function () {

            if (window.scrollY > 40) {

                navbar.classList.add("navbar-scrolled");

            } else {

                navbar.classList.remove("navbar-scrolled");

            }

        });

    }


    /* =====================================================
       SCROLL REVEAL
    ===================================================== */

    const revealElements = document.querySelectorAll(
        ".content-card, " +
        ".content-box, " +
        ".content-section, " +
        ".article-card, " +
        ".story-card, " +
        ".resource-card, " +
        ".content-image, " +
        ".content-text"
    );


    revealElements.forEach(function (element) {

        element.classList.add("content-reveal");

    });


    const revealObserver = new IntersectionObserver(
        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {

                    entry.target.classList.add(
                        "content-reveal-active"
                    );

                    revealObserver.unobserve(
                        entry.target
                    );

                }

            });

        },
        {
            threshold: 0.12
        }
    );


    revealElements.forEach(function (element) {

        revealObserver.observe(element);

    });


    /* =====================================================
       STAGGER CARD ANIMATION
    ===================================================== */

    const cards = document.querySelectorAll(
        ".content-card, " +
        ".article-card, " +
        ".story-card, " +
        ".resource-card"
    );


    cards.forEach(function (card, index) {

        card.style.transitionDelay =
            `${index * 0.08}s`;

    });


    /* =====================================================
       CONTENT CARD HOVER
    ===================================================== */

    const contentCards = document.querySelectorAll(
        ".content-card"
    );


    contentCards.forEach(function (card) {

        card.addEventListener(
            "mouseenter",
            function () {

                this.classList.add(
                    "content-card-hover"
                );

            }
        );


        card.addEventListener(
            "mouseleave",
            function () {

                this.classList.remove(
                    "content-card-hover"
                );

            }
        );

    });


    /* =====================================================
       IMAGE HOVER / ZOOM
    ===================================================== */

    const contentImages = document.querySelectorAll(
        ".content-card img, " +
        ".content-image img, " +
        ".article-card img, " +
        ".story-card img"
    );


    contentImages.forEach(function (image) {

        image.addEventListener(
            "mouseenter",
            function () {

                this.classList.add(
                    "content-image-zoom"
                );

            }
        );


        image.addEventListener(
            "mouseleave",
            function () {

                this.classList.remove(
                    "content-image-zoom"
                );

            }
        );

    });


    /* =====================================================
       CONTENT SEARCH
    ===================================================== */

    const searchInput =
        document.querySelector(
            "#contentSearch"
        );


    const searchableItems =
        document.querySelectorAll(
            ".content-card, " +
            ".article-card, " +
            ".story-card, " +
            ".resource-card"
        );


    if (
        searchInput &&
        searchableItems.length > 0
    ) {

        searchInput.addEventListener(
            "input",
            function () {

                const searchText =
                    this.value
                    .toLowerCase()
                    .trim();


                searchableItems.forEach(
                    function (item) {

                        const content =
                            item.textContent
                            .toLowerCase();


                        if (
                            content.includes(
                                searchText
                            )
                        ) {

                            item.style.display =
                                "";

                            setTimeout(
                                function () {

                                    item.classList.add(
                                        "content-search-visible"
                                    );

                                },
                                10
                            );

                        } else {

                            item.classList.remove(
                                "content-search-visible"
                            );

                            item.style.display =
                                "none";

                        }

                    }
                );

            }
        );

    }


    /* =====================================================
       CATEGORY FILTER
    ===================================================== */

    const filterButtons =
        document.querySelectorAll(
            ".content-filter"
        );


    filterButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                filterButtons.forEach(
                    function (btn) {

                        btn.classList.remove(
                            "active"
                        );

                    }
                );


                this.classList.add(
                    "active"
                );


                const category =
                    this.getAttribute(
                        "data-category"
                    );


                searchableItems.forEach(
                    function (item) {

                        const itemCategory =
                            item.getAttribute(
                                "data-category"
                            );


                        if (
                            category === "all" ||
                            category === itemCategory
                        ) {

                            item.style.display =
                                "";

                            setTimeout(
                                function () {

                                    item.classList.add(
                                        "content-search-visible"
                                    );

                                },
                                20
                            );

                        } else {

                            item.classList.remove(
                                "content-search-visible"
                            );

                            item.style.display =
                                "none";

                        }

                    }
                );

            }
        );

    });


    /* =====================================================
       READ MORE BUTTON
    ===================================================== */

    const readMoreButtons =
        document.querySelectorAll(
            ".read-more-btn"
        );


    readMoreButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function (event) {

                event.preventDefault();


                const card =
                    this.closest(
                        ".content-card, " +
                        ".article-card, " +
                        ".story-card"
                    );


                if (!card) {
                    return;
                }


                const extraContent =
                    card.querySelector(
                        ".extra-content"
                    );


                if (!extraContent) {
                    return;
                }


                extraContent.classList.toggle(
                    "extra-content-visible"
                );


                if (
                    extraContent.classList.contains(
                        "extra-content-visible"
                    )
                ) {

                    this.textContent =
                        "Read Less";

                } else {

                    this.textContent =
                        "Read More";

                }

            }
        );

    });


    /* =====================================================
       LIKE BUTTON
    ===================================================== */

    const likeButtons =
        document.querySelectorAll(
            ".like-btn, " +
            ".content-like"
        );


    likeButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function (event) {

                event.preventDefault();


                this.classList.toggle(
                    "liked"
                );


                const icon =
                    this.querySelector("i");


                if (icon) {

                    icon.classList.add(
                        "content-like-animation"
                    );


                    setTimeout(function () {

                        icon.classList.remove(
                            "content-like-animation"
                        );

                    }, 500);

                }


                const count =
                    this.querySelector(
                        ".like-count"
                    );


                if (count) {

                    let number =
                        parseInt(
                            count.textContent
                        ) || 0;


                    if (
                        this.classList.contains(
                            "liked"
                        )
                    ) {

                        number++;

                    } else {

                        number--;

                    }


                    count.textContent =
                        number;

                }

            }
        );

    });


    /* =====================================================
       SHARE BUTTON
    ===================================================== */

    const shareButtons =
        document.querySelectorAll(
            ".share-btn, " +
            ".content-share"
        );


    shareButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            async function (event) {

                event.preventDefault();


                const card =
                    this.closest(
                        ".content-card, " +
                        ".article-card, " +
                        ".story-card"
                    );


                const title =
                    card
                        ? card.querySelector(
                            "h2, h3, h4, h5"
                        )
                        : null;


                const shareText =
                    title
                        ? title.textContent
                        : "CharityBridge";


                if (navigator.share) {

                    try {

                        await navigator.share({

                            title:
                                "CharityBridge",

                            text:
                                shareText,

                            url:
                                window.location.href

                        });

                    } catch (error) {

                        console.log(
                            "Sharing cancelled."
                        );

                    }

                } else {

                    try {

                        await navigator.clipboard.writeText(
                            window.location.href
                        );

                        showContentMessage(
                            "Link copied successfully!"
                        );

                    } catch (error) {

                        showContentMessage(
                            "Unable to copy link."
                        );

                    }

                }

            }
        );

    });


    /* =====================================================
       BOOKMARK BUTTON
    ===================================================== */

    const bookmarkButtons =
        document.querySelectorAll(
            ".bookmark-btn, " +
            ".content-bookmark"
        );


    bookmarkButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function (event) {

                event.preventDefault();


                this.classList.toggle(
                    "bookmarked"
                );


                if (
                    this.classList.contains(
                        "bookmarked"
                    )
                ) {

                    showContentMessage(
                        "Content saved!"
                    );

                } else {

                    showContentMessage(
                        "Content removed from saved items."
                    );

                }

            }
        );

    });


    /* =====================================================
       CONTENT NOTIFICATION
    ===================================================== */

    function showContentMessage(message) {

        const oldMessage =
            document.querySelector(
                ".content-message"
            );


        if (oldMessage) {

            oldMessage.remove();

        }


        const messageBox =
            document.createElement(
                "div"
            );


        messageBox.className =
            "content-message";


        messageBox.textContent =
            message;


        document.body.appendChild(
            messageBox
        );


        setTimeout(function () {

            messageBox.classList.add(
                "show"
            );

        }, 10);


        setTimeout(function () {

            messageBox.classList.remove(
                "show"
            );


            setTimeout(function () {

                messageBox.remove();

            }, 300);

        }, 2500);

    }


    /* =====================================================
       CONTENT STATISTICS COUNTER
    ===================================================== */

    const counters =
        document.querySelectorAll(
            "[data-count]"
        );


    function animateCounter(element) {

        const target =
            parseInt(
                element.getAttribute(
                    "data-count"
                )
            );


        if (isNaN(target)) {
            return;
        }


        let current = 0;

        const duration = 1600;

        const frames = 60;

        const increment =
            target / frames;


        const timer =
            setInterval(function () {

                current += increment;


                if (current >= target) {

                    current = target;

                    clearInterval(timer);

                }


                element.textContent =
                    Math.floor(current)
                    .toLocaleString();

            }, duration / frames);

    }


    const counterObserver =
        new IntersectionObserver(
            function (entries) {

                entries.forEach(function (entry) {

                    if (
                        entry.isIntersecting &&
                        !entry.target.dataset.animated
                    ) {

                        entry.target.dataset.animated =
                            "true";

                        animateCounter(
                            entry.target
                        );

                        counterObserver.unobserve(
                            entry.target
                        );

                    }

                });

            },
            {
                threshold: 0.5
            }
        );


    counters.forEach(function (counter) {

        counterObserver.observe(
            counter
        );

    });


    /* =====================================================
       FLOATING ELEMENTS
    ===================================================== */

    const floatingElements =
        document.querySelectorAll(
            ".floating-heart, " +
            ".floating-icon, " +
            ".content-floating"
        );


    floatingElements.forEach(
        function (element, index) {

            const duration =
                3 + index * 0.4;


            const delay =
                index * 0.25;


            element.style.animation =
                `contentFloat ${duration}s ease-in-out ${delay}s infinite`;

        }
    );


    /* =====================================================
       HERO MOUSE PARALLAX
    ===================================================== */

    const contentHero =
        document.querySelector(
            ".content-hero"
        );


    const contentVisual =
        document.querySelector(
            ".content-hero-visual"
        );


    if (
        contentHero &&
        contentVisual &&
        window.innerWidth > 768
    ) {

        contentHero.addEventListener(
            "mousemove",
            function (event) {

                const rect =
                    contentHero.getBoundingClientRect();


                const x =
                    event.clientX -
                    rect.left;


                const y =
                    event.clientY -
                    rect.top;


                const moveX =
                    (x / rect.width - 0.5) * 12;


                const moveY =
                    (y / rect.height - 0.5) * 12;


                contentVisual.style.transform =
                    `translate(${moveX}px, ${moveY}px)`;

            }
        );


        contentHero.addEventListener(
            "mouseleave",
            function () {

                contentVisual.style.transform =
                    "translate(0, 0)";

            }
        );

    }


    /* =====================================================
       SMOOTH SCROLL
    ===================================================== */

    const smoothLinks =
        document.querySelectorAll(
            'a[href^="#"]'
        );


    smoothLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const targetId =
                    this.getAttribute(
                        "href"
                    );


                if (
                    !targetId ||
                    targetId === "#"
                ) {

                    return;

                }


                const target =
                    document.querySelector(
                        targetId
                    );


                if (target) {

                    event.preventDefault();


                    target.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                }

            }
        );

    });


    /* =====================================================
       MOBILE NAVBAR
    ===================================================== */

    const navLinks =
        document.querySelectorAll(
            ".navbar-nav .nav-link"
        );


    const navbarMenu =
        document.querySelector(
            ".navbar-collapse"
        );


    navLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function () {

                if (
                    window.innerWidth < 992 &&
                    navbarMenu &&
                    navbarMenu.classList.contains(
                        "show"
                    )
                ) {

                    const collapse =
                        bootstrap.Collapse
                        .getInstance(
                            navbarMenu
                        );


                    if (collapse) {

                        collapse.hide();

                    }

                }

            }
        );

    });


    /* =====================================================
       BACK TO TOP
    ===================================================== */

    const backToTop =
        document.querySelector(
            ".back-to-top"
        );


    if (backToTop) {

        window.addEventListener(
            "scroll",
            function () {

                if (
                    window.scrollY > 500
                ) {

                    backToTop.classList.add(
                        "show"
                    );

                } else {

                    backToTop.classList.remove(
                        "show"
                    );

                }

            }
        );


        backToTop.addEventListener(
            "click",
            function () {

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

            }
        );

    }


    /* =====================================================
       PAGE READY
    ===================================================== */

    console.log(
        "💜 CharityBridge Content Page Loaded Successfully!"
    );

});