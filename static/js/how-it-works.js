/* =========================================================
   CHARITYBRIDGE
   HOW IT WORKS INTERACTION ENGINE
========================================================= */


/* =========================================================
   ELEMENTS
========================================================= */

const particles =
    document.getElementById("particles");

const glassReveal =
    document.getElementById("glassReveal");

const breakButton =
    document.getElementById("breakButton");

const journey =
    document.getElementById("journey");

const exploreButton =
    document.getElementById("exploreButton");

const launchButton =
    document.getElementById("launchButton");

const startButton =
    document.getElementById("startButton");

const joinButton =
    document.getElementById("joinButton");

const rocketLauncher =
    document.getElementById("rocketLauncher");

const clickRipple =
    document.getElementById("clickRipple");

const glassCore =
    document.getElementById("glassCore");



/* =========================================================
   CREATE PARTICLES
========================================================= */

for (let i = 0; i < 70; i++) {

    const particle =
        document.createElement("div");

    particle.className =
        "particle";

    particle.style.left =
        Math.random() * 100 + "%";

    particle.style.animationDuration =
        5 + Math.random() * 12 + "s";

    particle.style.animationDelay =
        Math.random() * 10 + "s";

    particle.style.opacity =
        Math.random();

    particles.appendChild(
        particle
    );
}



/* =========================================================
   ROCKET
========================================================= */

function launchRocket() {

    rocketLauncher.classList.remove(
        "launch"
    );

    /*
       Forces browser to restart
       the animation every click.
    */

    void rocketLauncher.offsetWidth;

    rocketLauncher.classList.add(
        "launch"
    );

    setTimeout(() => {

        rocketLauncher.classList.remove(
            "launch"
        );

    }, 2300);
}



/* =========================================================
   CLICK RIPPLE
========================================================= */

document.addEventListener(
    "click",
    function(event) {

        clickRipple.style.left =
            event.clientX + "px";

        clickRipple.style.top =
            event.clientY + "px";

        clickRipple.classList.remove(
            "active"
        );

        void clickRipple.offsetWidth;

        clickRipple.classList.add(
            "active"
        );

    }
);



/* =========================================================
   BREAK GLASS
========================================================= */

function breakGlass() {

    /*
       First launch rocket.
    */

    launchRocket();


    /*
       Break the glass.
    */

    glassReveal.classList.add(
        "broken"
    );


    /*
       Wait for glass pieces
       to fly away.
    */

    setTimeout(() => {

        journey.classList.add(
            "visible"
        );

    }, 650);

}



/* =========================================================
   BREAK BUTTON
========================================================= */

breakButton.addEventListener(
    "click",
    function(event) {

        event.stopPropagation();

        breakGlass();

    }
);



/* =========================================================
   EXPLORE HOW IT WORKS
========================================================= */

exploreButton.addEventListener(
    "click",
    function() {

        launchRocket();


        /*
           Scroll to section.
        */

        document
            .getElementById("howSection")
            .scrollIntoView({
                behavior: "smooth"
            });


        /*
           Break after arriving.
        */

        setTimeout(() => {

            breakGlass();

        }, 800);

    }
);



/* =========================================================
   LAUNCH JOURNEY BUTTON
========================================================= */

launchButton.addEventListener(
    "click",
    function() {

        launchRocket();

        setTimeout(() => {

            document
                .getElementById("howSection")
                .scrollIntoView({
                    behavior: "smooth"
                });

        }, 600);

    }
);



/* =========================================================
   JOIN BUTTON
========================================================= */

joinButton.addEventListener(
    "click",
    function() {

        launchRocket();

        setTimeout(() => {

            window.location.href =
                "/register";

        }, 900);

    }
);



/* =========================================================
   FINAL START BUTTON
========================================================= */

startButton.addEventListener(
    "click",
    function() {

        launchRocket();

        setTimeout(() => {

            window.location.href =
                "/register";

        }, 900);

    }
);



/* =========================================================
   JOURNEY CARD INTERACTION
========================================================= */

const cards =
    document.querySelectorAll(
        ".journey-card"
    );


cards.forEach(card => {

    card.addEventListener(
        "click",
        function() {

            launchRocket();


            /*
               Temporary futuristic
               selected effect.
            */

            this.style.borderColor =
                "rgba(0,255,225,0.75)";

            this.style.boxShadow =
                "0 0 50px rgba(0,255,225,0.18)";


            setTimeout(() => {

                this.style.borderColor =
                    "";

                this.style.boxShadow =
                    "";

            }, 700);

        }
    );

});



/* =========================================================
   3D GLASS CORE
========================================================= */

document.addEventListener(
    "mousemove",
    function(event) {

        if (!glassCore) return;


        /*
           Calculate mouse position
           relative to screen center.
        */

        const mouseX =
            (window.innerWidth / 2 -
             event.clientX) / 45;

        const mouseY =
            (window.innerHeight / 2 -
             event.clientY) / 45;


        glassCore.style.transform =

            `rotateY(${-mouseX}deg)
             rotateX(${mouseY}deg)`;

    }
);



/* =========================================================
   RESET GLASS CORE
========================================================= */

document.addEventListener(
    "mouseleave",
    function() {

        if (!glassCore) return;

        glassCore.style.transform =
            "rotateY(0deg) rotateX(0deg)";

    }
);



/* =========================================================
   KEYBOARD ROCKET
========================================================= */

document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" ||
            event.key === " "
        ) {

            launchRocket();

        }

    }
);