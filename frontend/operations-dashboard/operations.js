const apiBaseUrl = document
    .querySelector('meta[name="api-base-url"]')
    ?.getAttribute("content")
    ?.trim()
    .replace(/\/+$/, "");
const logoutButton = document.getElementById("dashboard-logout");

async function logoutController() {
    logoutButton.disabled = true;
    try {
        const response = await fetch(`${apiBaseUrl}/auth/logout`, {
            method: "POST",
            credentials: "include"
        });
        if (response.status !== 204) {
            throw new Error(`Logout failed with HTTP ${response.status}.`);
        }
        window.location.replace("../auth/controller-login.html");
    } catch (error) {
        console.error("Could not log out of the Operations Dashboard.", error);
        window.alert("Sign out failed. Please try again.");
        logoutButton.disabled = false;
    }
}

function initializeOperationsDashboard() {
    document.body.classList.remove("auth-pending");
    const sidebar = document.getElementById("operations-sidebar");
    const menuToggle = document.getElementById("menu-toggle");
    const sidebarBackdrop = document.getElementById("sidebar-backdrop");
    const brandHome = document.querySelector(".brand");
    const navigationLinks = [...document.querySelectorAll(".nav-link")];
    const incidentRows = [...document.querySelectorAll("[data-incident-row]")];

    function setNavigationOpen(isOpen) {
        sidebar.classList.toggle("is-open", isOpen);
        sidebarBackdrop.classList.toggle("is-visible", isOpen);
        document.body.classList.toggle("drawer-open", isOpen);
        sidebarBackdrop.setAttribute("aria-hidden", String(!isOpen));
        sidebarBackdrop.tabIndex = isOpen ? 0 : -1;
        menuToggle.setAttribute("aria-expanded", String(isOpen));
        menuToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
    }

    menuToggle.addEventListener("click", () => {
        setNavigationOpen(menuToggle.getAttribute("aria-expanded") !== "true");
    });

    sidebarBackdrop.addEventListener("click", () => setNavigationOpen(false));

    brandHome.addEventListener("click", () => {
        navigationLinks.forEach((link) => {
            link.classList.toggle("is-active", link.getAttribute("href") === "#overview");
        });
        setNavigationOpen(false);
    });

    navigationLinks.forEach((link) => {
        link.addEventListener("click", () => {
            navigationLinks.forEach((item) => item.classList.toggle("is-active", item === link));
            setNavigationOpen(false);
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") setNavigationOpen(false);
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 720) setNavigationOpen(false);
    });

    function updateIncidentCounts() {
        const activeCount = incidentRows.filter((row) => row.dataset.status !== "Resolved").length;
        document.getElementById("active-incident-count").textContent = String(activeCount);
        document.getElementById("nav-incident-count").textContent = String(activeCount);
        document.getElementById("incident-summary").textContent = `${activeCount} active`;
    }

    document.querySelectorAll(".status-select").forEach((select) => {
        select.addEventListener("change", () => {
            const row = select.closest("[data-incident-row]");
            row.dataset.status = select.value;
            select.dataset.status = select.value;
            updateIncidentCounts();
        });
    });

    function updateClock() {
        const now = new Date();
        document.getElementById("current-time").textContent = new Intl.DateTimeFormat(undefined, {
            hour: "2-digit",
            minute: "2-digit"
        }).format(now);
    }

    logoutButton.disabled = false;
    logoutButton.addEventListener("click", logoutController);
    updateIncidentCounts();
    updateClock();
    setInterval(updateClock, 60_000);
}

async function verifyControllerSession() {
    if (!apiBaseUrl) {
        throw new Error("The authentication API base URL is not configured.");
    }

    let response;
    try {
        response = await fetch(`${apiBaseUrl}/auth/me`, {
            credentials: "include"
        });
    } catch {
        throw new Error("Could not reach the authentication service.");
    }

    if (response.status === 401) {
        window.location.replace("../auth/controller-login.html");
        return false;
    }
    if (!response.ok) {
        throw new Error(`Session verification failed with HTTP ${response.status}.`);
    }

    const account = await response.json();
    if (account.role === "USER") {
        window.location.replace("../index.html");
        return false;
    }
    if (account.role !== "CONTROLLER") {
        window.location.replace("../auth/controller-login.html");
        return false;
    }

    return true;
}

verifyControllerSession()
    .then((isController) => {
        if (isController) initializeOperationsDashboard();
    })
    .catch((error) => {
        console.error("Could not verify access to the Operations Dashboard.", error);
        window.alert("Unable to verify your session. Please try again.");
        window.location.replace("../auth/controller-login.html");
    });
