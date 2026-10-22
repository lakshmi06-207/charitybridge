/* =====================================================
   CHARITYBRIDGE FUTURISTIC ANIMATION
===================================================== */


/* =====================================================
   PARTICLE BACKGROUND
===================================================== */

const canvas =
    document.getElementById("particleCanvas");

const ctx =
    canvas.getContext("2d");

let particles = [];

function resizeCanvas() {

    canvas.width =
        window.innerWidth;

    canvas.height =
        window.innerHeight;
}

resizeCanvas();

window.addEventListener(
    "resize",
    resizeCanvas
);


for (let i = 0; i < 90; i++) {

    particles.push({

        x:
            Math.random() *
            window.innerWidth,

        y:
            Math.random() *
            window.innerHeight,

        size:
            Math.random() * 2 + 0.5,

        speedX:
            (Math.random() - .5) * .25,

        speedY:
            (Math.random() - .5) * .25,

        opacity:
            Math.random() * .7 + .2

    });
}


function animateParticles() {

    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );


    particles.forEach(p => {

        p.x += p.speedX;
        p.y += p.speedY;


        if (p.x < 0)
            p.x = canvas.width;

        if (p.x > canvas.width)
            p.x = 0;

        if (p.y < 0)
            p.y = canvas.height;

        if (p.y > canvas.height)
            p.y = 0;


        ctx.beginPath();

        ctx.arc(
            p.x,
            p.y,
            p.size,
            0,
            Math.PI * 2
        );

        ctx.fillStyle =
            `rgba(120,150,255,${p.opacity})`;

        ctx.fill();

    });


    requestAnimationFrame(
        animateParticles
    );
}

animateParticles();


/* =====================================================
   MOUSE PARALLAX
===================================================== */

const orbs =
    document.querySelectorAll(
        ".gradient-orb"
    );

document.addEventListener(
    "mousemove",
    event => {

        const x =
            (event.clientX /
                window.innerWidth -
                .5);

        const y =
            (event.clientY /
                window.innerHeight -
                .5);


        orbs.forEach(
            (orb, index) => {

                const speed =
                    (index + 1) * 15;

                orb.style.transform =
                    `translate(
                        ${x * speed}px,
                        ${y * speed}px
                    )`;

            }
        );

    }
);


/* =====================================================
   SCROLL REVEAL
===================================================== */

const revealElements =
    document.querySelectorAll(
        ".action-card, .story-card, .step, .impact-item"
    );


const observer =
    new IntersectionObserver(
        entries => {

            entries.forEach(
                entry => {

                    if (
                        entry.isIntersecting
                    ) {

                        entry.target.classList.add(
                            "visible"
                        );

                    }

                }
            );

        },
        {
            threshold: .15
        }
    );


revealElements.forEach(
    element => {

        element.classList.add(
            "reveal"
        );

        observer.observe(
            element
        );

    }
);


/* =====================================================
   REAL DATABASE IMPACT DATA
===================================================== */

async function loadImpactData() {

    try {

        const response =
            await fetch(
                "/api/impact"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load impact"
            );

        }


        const data =
            await response.json();


        animateNumber(
            "peopleHelped",
            data.people_helped
        );


        animateNumber(
            "donationCount",
            data.donations
        );


        animateNumber(
            "volunteerCount",
            data.volunteers
        );


        animateCurrency(
            "moneyRaised",
            data.total_donated
        );


        animateNumber(
            "impactPeople",
            data.people_helped
        );


        animateNumber(
            "impactDonations",
            data.donations
        );


        animateNumber(
            "impactVolunteers",
            data.volunteers
        );


        animateNumber(
            "impactRequests",
            data.help_requests
        );


    } catch (error) {

        console.log(
            "Impact data error:",
            error
        );

    }

}


/* =====================================================
   NUMBER ANIMATION
===================================================== */

function animateNumber(
    elementId,
    target
) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element)
        return;


    target =
        Number(target) || 0;


    let current = 0;

    const duration = 1200;

    const start =
        performance.now();


    function update(time) {

        const progress =
            Math.min(
                (time - start) /
                duration,
                1
            );


        current =
            Math.floor(
                progress * target
            );


        element.textContent =
            current.toLocaleString(
                "en-IN"
            );


        if (progress < 1) {

            requestAnimationFrame(
                update
            );

        }

    }


    requestAnimationFrame(
        update
    );
}


/* =====================================================
   CURRENCY ANIMATION
===================================================== */

function animateCurrency(
    elementId,
    target
) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element)
        return;


    target =
        Number(target) || 0;


    let current = 0;

    const duration = 1500;

    const start =
        performance.now();


    function update(time) {

        const progress =
            Math.min(
                (time - start) /
                duration,
                1
            );


        current =
            Math.floor(
                progress * target
            );


        element.textContent =
            "₹" +
            current.toLocaleString(
                "en-IN"
            );


        if (progress < 1) {

            requestAnimationFrame(
                update
            );

        }

    }


    requestAnimationFrame(
        update
    );
}


loadImpactData();