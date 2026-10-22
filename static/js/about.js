/* =========================================================
   CHARITYBRIDGE ABOUT PAGE JAVASCRIPT
========================================================= */


/* =========================================================
   FOUNDER DATA
========================================================= */

const founderData = {

    lakshmi: {

        initials: "LS",

        name: 'Lakshmi <span>S.</span>',

        why:
            "CharityBridge was created with the belief that technology can be used not only to solve technical problems, but also to solve real human problems. The goal is to make helping others easier, faster and more connected.",

        contribution:
            "Passionate about technology, creativity and building meaningful digital solutions that can create positive social impact."

    },


    koushalya: {

        initials: "KA",

        name: 'Koushalya <span>A.</span>',

        why:
            "CharityBridge was created to build a compassionate digital community where people can reach one another when support is needed. Technology can become a bridge between someone who wants to help and someone who needs help.",

        contribution:
            "Focused on creating a compassionate digital community and bringing people together through technology, collaboration and meaningful support."

    }

};



/* =========================================================
   FOUNDER MODAL
========================================================= */

const founderCards =
    document.querySelectorAll(".founder-card");

const founderModal =
    document.getElementById("founderModal");

const modalClose =
    document.getElementById("modalClose");

const modalName =
    document.getElementById("modalName");

const modalAvatar =
    document.getElementById("modalAvatar");

const modalWhy =
    document.getElementById("modalWhy");

const modalContribution =
    document.getElementById("modalContribution");



founderCards.forEach(card => {

    card.addEventListener("click", () => {

        const founder =
            card.dataset.founder;

        const data =
            founderData[founder];

        if (!data) return;


        modalAvatar.textContent =
            data.initials;

        modalName.innerHTML =
            data.name;

        modalWhy.textContent =
            data.why;

        modalContribution.textContent =
            data.contribution;


        founderModal.classList.add("show");

        document.body.style.overflow =
            "hidden";

    });

});



/* =========================================================
   CLOSE MODAL
========================================================= */

function closeFounderModal() {

    founderModal.classList.remove("show");

    document.body.style.overflow =
        "";

}


modalClose.addEventListener(
    "click",
    closeFounderModal
);



/* Click outside */

document
    .querySelector(".modal-backdrop")
    .addEventListener(
        "click",
        closeFounderModal
    );



/* ESC KEY */

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape" &&
            founderModal.classList.contains("show")
        ) {

            closeFounderModal();

        }

    }
);



/* =========================================================
   CONTACT GLASS
========================================================= */

const contactGlass =
    document.getElementById("contactGlass");


contactGlass.addEventListener(
    "click",
    () => {

        contactGlass.classList.toggle(
            "open"
        );

    }
);



/* =========================================================
   FOUNDER CARD TILT EFFECT
========================================================= */

founderCards.forEach(card => {

    card.addEventListener(
        "mousemove",
        event => {

            const rect =
                card.getBoundingClientRect();

            const x =
                event.clientX - rect.left;

            const y =
                event.clientY - rect.top;


            const centerX =
                rect.width / 2;

            const centerY =
                rect.height / 2;


            const rotateX =
                ((y - centerY) / centerY) * -2;


            const rotateY =
                ((x - centerX) / centerX) * 2;


            card.style.transform =
                `perspective(900px)
                 rotateX(${rotateX}deg)
                 rotateY(${rotateY}deg)
                 translateY(-8px)`;

        }
    );


    card.addEventListener(
        "mouseleave",
        () => {

            card.style.transform = "";

        }
    );

});



/* =========================================================
   SCROLL REVEAL
========================================================= */

const revealElements =
    document.querySelectorAll(
        ".mission-section, .footer"
    );


const revealObserver =
    new IntersectionObserver(
        entries => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    entry.target.classList.add(
                        "visible"
                    );

                }

            });

        },
        {
            threshold: 0.15
        }
    );


revealElements.forEach(
    element =>
        revealObserver.observe(element)
);



/* =========================================================
   SMALL PARALLAX EFFECT
========================================================= */

window.addEventListener(
    "scroll",
    () => {

        const scrollY =
            window.scrollY;

        const background =
            document.querySelector(
                ".background"
            );

        if (background) {

            background.style.transform =
                `scale(1.06)
                 translateY(${scrollY * 0.015}px)`;

        }

    }
);