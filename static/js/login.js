/* =====================================================
   CHARITYBRIDGE DONATION SYSTEM
===================================================== */

document.addEventListener("DOMContentLoaded", () => {


    /* =================================================
       ELEMENTS
    ================================================= */

    const typeButtons =
        document.querySelectorAll(".type-btn");

    const donationForms =
        document.querySelectorAll(".donation-form");

    const amountButtons =
        document.querySelectorAll(".amount-btn");

    const customAmount =
        document.getElementById("customAmount");

    const summaryValue =
        document.getElementById("summaryValue");

    const summaryIcon =
        document.getElementById("summaryIcon");

    const summaryType =
        document.getElementById("summaryType");

    const summaryDescription =
        document.getElementById("summaryDescription");

    const impactText =
        document.getElementById("impactText");

    const donateNow =
        document.getElementById("donateNow");

    const successModal =
        document.getElementById("successModal");

    const closeModal =
        document.getElementById("closeModal");

    const successMessage =
        document.getElementById("successMessage");


    let currentType = "money";

    let currentAmount = 1000;


    /* =================================================
       DONATION DATA
    ================================================= */

    const donationData = {

        money: {

            title: "Money",

            icon: "₹",

            description:
                "Financial support for people and communities in need.",

            impact:
                "Community Support"

        },

        food: {

            title: "Food",

            icon: "🍱",

            description:
                "Nutritious food and groceries for families who need them.",

            impact:
                "Meals & Groceries"

        },

        blood: {

            title: "Blood",

            icon: "♥",

            description:
                "Help connect blood donors with patients who need urgent support.",

            impact:
                "Life Saving"

        },

        clothes: {

            title: "Clothes",

            icon: "👕",

            description:
                "Clean and usable clothing for children, adults and families.",

            impact:
                "Essential Clothing"

        },

        furniture: {

            title: "Furniture",

            icon: "⌂",

            description:
                "Furniture and home essentials to help create comfortable homes.",

            impact:
                "Home Essentials"

        }

    };


    /* =================================================
       SWITCH DONATION TYPE
    ================================================= */

    typeButtons.forEach(button => {

        button.addEventListener("click", () => {

            typeButtons.forEach(btn => {
                btn.classList.remove("active");
            });

            button.classList.add("active");


            currentType =
                button.dataset.type;


            donationForms.forEach(form => {
                form.classList.remove("active-form");
            });


            const selectedForm =
                document.getElementById(
                    currentType + "-form"
                );


            if (selectedForm) {

                selectedForm.classList.add(
                    "active-form"
                );

            }


            updateSummary();

        });

    });


    /* =================================================
       MONEY AMOUNTS
    ================================================= */

    amountButtons.forEach(button => {

        button.addEventListener("click", () => {

            amountButtons.forEach(btn => {
                btn.classList.remove("active");
            });

            button.classList.add("active");


            currentAmount =
                Number(button.dataset.amount);


            customAmount.value = "";


            updateMoneySummary();

        });

    });


    /* =================================================
       CUSTOM MONEY
    ================================================= */

    customAmount.addEventListener("input", () => {

        const amount =
            Number(customAmount.value);


        if (amount > 0) {

            amountButtons.forEach(btn => {
                btn.classList.remove("active");
            });


            currentAmount = amount;

            updateMoneySummary();

        }

    });


    /* =================================================
       UPDATE MONEY SUMMARY
    ================================================= */

    function updateMoneySummary() {

        summaryValue.textContent =
            "₹" +
            Number(currentAmount)
                .toLocaleString("en-IN");


        if (currentType === "money") {

            summaryIcon.textContent = "₹";

        }

    }


    /* =================================================
       UPDATE SUMMARY
    ================================================= */

    function updateSummary() {

        const data =
            donationData[currentType];


        summaryType.textContent =
            data.title;


        summaryIcon.textContent =
            data.icon;


        summaryDescription.textContent =
            data.description;


        impactText.textContent =
            data.impact;


        if (currentType === "money") {

            updateMoneySummary();

        }

        else if (currentType === "food") {

            const quantity =
                document.getElementById(
                    "foodQuantity"
                ).value || 10;


            summaryValue.textContent =
                quantity + " Units";

        }

        else if (currentType === "blood") {

            summaryValue.textContent =
                "1 Unit";

        }

        else if (currentType === "clothes") {

            const quantity =
                document.getElementById(
                    "clothesQuantity"
                ).value || 5;


            summaryValue.textContent =
                quantity + " Items";

        }

        else if (currentType === "furniture") {

            summaryValue.textContent =
                "1 Item";

        }

    }


    /* =================================================
       LIVE QUANTITY UPDATES
    ================================================= */

    const quantityFields = [

        "foodQuantity",
        "clothesQuantity"

    ];


    quantityFields.forEach(id => {

        const element =
            document.getElementById(id);


        if (element) {

            element.addEventListener(
                "input",
                updateSummary
            );

        }

    });


    /* =================================================
       DONATE BUTTON
    ================================================= */

    donateNow.addEventListener("click", () => {


        const name =
            document.getElementById(
                "donorName"
            ).value.trim();


        const phone =
            document.getElementById(
                "donorPhone"
            ).value.trim();


        const email =
            document.getElementById(
                "donorEmail"
            ).value.trim();


        /* BASIC VALIDATION */

        if (!name) {

            alert(
                "Please enter your full name."
            );

            document.getElementById(
                "donorName"
            ).focus();

            return;

        }


        if (!phone) {

            alert(
                "Please enter your phone number."
            );

            document.getElementById(
                "donorPhone"
            ).focus();

            return;

        }


        /* MONEY */

        if (currentType === "money") {

            if (!currentAmount || currentAmount <= 0) {

                alert(
                    "Please select a donation amount."
                );

                return;

            }

            successMessage.textContent =
                "Thank you, " +
                name +
                ". Your ₹" +
                Number(currentAmount)
                    .toLocaleString("en-IN") +
                " donation is ready to continue.";

        }


        /* FOOD */

        else if (currentType === "food") {

            const quantity =
                document.getElementById(
                    "foodQuantity"
                ).value;

            const food =
                document.getElementById(
                    "foodType"
                ).value;

            successMessage.textContent =
                "Thank you, " +
                name +
                ". Your donation of " +
                quantity +
                " units of " +
                food +
                " has been prepared.";

        }


        /* BLOOD */

        else if (currentType === "blood") {

            const group =
                document.getElementById(
                    "bloodGroup"
                ).value;

            if (!group) {

                alert(
                    "Please select your blood group."
                );

                return;

            }

            successMessage.textContent =
                "Thank you, " +
                name +
                ". Your " +
                group +
                " blood donation registration is ready.";

        }


        /* CLOTHES */

        else if (currentType === "clothes") {

            const quantity =
                document.getElementById(
                    "clothesQuantity"
                ).value;

            const type =
                document.getElementById(
                    "clothesType"
                ).value;

            successMessage.textContent =
                "Thank you, " +
                name +
                ". You are donating " +
                quantity +
                " " +
                type +
                " items.";

        }


        /* FURNITURE */

        else if (currentType === "furniture") {

            const furniture =
                document.getElementById(
                    "furnitureType"
                ).value;

            successMessage.textContent =
                "Thank you, " +
                name +
                ". Your " +
                furniture +
                " donation has been prepared for pickup.";

        }


        successModal.classList.add("show");

    });


    /* =================================================
       CLOSE MODAL
    ================================================= */

    closeModal.addEventListener("click", () => {

        successModal.classList.remove("show");

    });


    successModal.addEventListener(
        "click",
        event => {

            if (event.target === successModal) {

                successModal.classList.remove(
                    "show"
                );

            }

        }
    );


    /* =================================================
       INITIAL STATE
    ================================================= */

    updateSummary();

});