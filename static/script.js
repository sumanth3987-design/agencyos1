/* ============================================================
   AGENCYOS — FRONTEND
============================================================ */


/* ============================================================
   DOM READY
============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    // Close modal when clicking outside its content
    document.querySelectorAll(".modal-overlay").forEach(modal => {

        modal.addEventListener("click", (event) => {

            if (event.target === modal) {
                modal.classList.remove("show");
                document.body.classList.remove("modal-open");
            }

        });

    });


    // Close modals with Escape key
    document.addEventListener("keydown", (event) => {

        if (event.key === "Escape") {
            closeService();
            closeLogin();
        }

    });

});


/* ============================================================
   MOBILE MENU
============================================================ */

function toggleMobileMenu() {

    const menu = document.getElementById("mobile-menu");

    if (!menu) {
        return;
    }

    menu.classList.toggle("show");
}


function closeMobileMenu() {

    const menu = document.getElementById("mobile-menu");

    if (!menu) {
        return;
    }

    menu.classList.remove("show");
}


/* ============================================================
   NAVIGATION
============================================================ */
function scrollToServices() {

    closeMobileMenu();

    const section = document.getElementById("services");

    if (section) {
        section.scrollIntoView({
            behavior: "smooth"
        });
    }
}


function scrollToHowItWorks() {

    closeMobileMenu();

    const section = document.getElementById("how-it-works");

    if (section) {
        section.scrollIntoView({
            behavior: "smooth"
        });
    }
}


/* ============================================================
   SERVICE MODAL
============================================================ */

function openService(slug) {

    const modal = document.getElementById("service-modal");
    const content = document.getElementById("service-modal-content");

    if (!modal || !content) {
        return;
    }

    const service = servicesData.find(
        service => service.slug === slug
    );

    if (!service) {

        content.innerHTML = `
            <div class="modal-service-header">
                <h2>Service not found</h2>
                <p>
                    We could not load the requested service.
                </p>
            </div>
        `;

        modal.classList.add("show");
        document.body.classList.add("modal-open");

        return;
    }


    let packagesHTML = "";

    service.packages.forEach((pkg, index) => {

        const featuresHTML = pkg.features
            .map(feature => `
                <span class="package-feature">
                    ${feature}
                </span>
            `)
            .join("");


        packagesHTML += `
            <div class="package-item">

                <div class="package-top">

                    <h3>
                        ${pkg.name}
                    </h3>

                    <span class="package-price">
                        ₹${formatPrice(pkg.price)}
                    </span>

                </div>

                <p>
                    ${pkg.description}
                </p>

                <div class="package-features">
                    ${featuresHTML}
                </div>

                <button
                    class="btn btn-primary full-width package-select-button"
                    onclick="selectPackage(
                        '${service.slug}',
                        ${pkg.id}
                    )"
                    style="margin-top: 15px;"
                >
                    Select Package
                </button>

            </div>
        `;

    });
    content.innerHTML = `

        <div class="modal-service-header">

            <div class="modal-service-icon">
                ${service.icon}
            </div>

            <h2>
                ${service.name}
            </h2>

            <p>
                ${service.short_description}
            </p>

        </div>


        <div class="package-list">

            ${packagesHTML}

        </div>

    `;


    modal.classList.add("show");

    document.body.classList.add("modal-open");
}


/* ============================================================
   CLOSE SERVICE MODAL
============================================================ */

function closeService() {

    const modal = document.getElementById("service-modal");

    if (!modal) {
        return;
    }

    modal.classList.remove("show");

    document.body.classList.remove("modal-open");
}


/* ============================================================
   PACKAGE SELECTION
============================================================ */

function selectPackage(serviceSlug, packageId) {

    const service = servicesData.find(
        service => service.slug === serviceSlug
    );

    if (!service) {
        return;
    }


    const selectedPackage = service.packages.find(
        pkg => pkg.id === packageId
    );

    if (!selectedPackage) {
        return;
    }


    /*
       We are not creating an order yet.

       In the next development phase this button will lead to:

       Package
          ↓
       Customer Login
          ↓
       Requirements Form
          ↓
       Order
          ↓
       Payment
    */


    closeService();

    showNotification(
        `${selectedPackage.name} selected`
    );
}


/* ============================================================
   LOGIN MODAL
============================================================ */
function openLogin() {

    closeMobileMenu();

    const modal = document.getElementById("login-modal");

    if (!modal) {
        return;
    }

    modal.classList.add("show");

    document.body.classList.add("modal-open");
}


function closeLogin() {

    const modal = document.getElementById("login-modal");

    if (!modal) {
        return;
    }

    modal.classList.remove("show");

    document.body.classList.remove("modal-open");
}


/* ============================================================
   COMING SOON
============================================================ */

function showComingSoon() {

    showNotification(
        "Customer accounts will be available in the next phase."
    );

}


/* ============================================================
   NOTIFICATION
============================================================ */

function showNotification(message) {

    // Remove an existing notification
    const existing = document.querySelector(".agency-notification");

    if (existing) {
        existing.remove();
    }


    const notification = document.createElement("div");

    notification.className = "agency-notification";

    notification.innerHTML = `
        <span class="notification-icon">✓</span>
        <span>${message}</span>
    `;


    document.body.appendChild(notification);


    // Small animation
    requestAnimationFrame(() => {
        notification.classList.add("visible");
    });


    // Automatically remove
    setTimeout(() => {

        notification.classList.remove("visible");

        setTimeout(() => {
            notification.remove();
        }, 250);

    }, 2800);

}


/* ============================================================
   PRICE FORMATTER
============================================================ */

function formatPrice(price) {

    return Number(price).toLocaleString("en-IN");

}