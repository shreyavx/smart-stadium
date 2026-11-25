(() => {
    const form = document.getElementById("controller-login-form");
    if (!form) {
        return;
    }

    const apiBase = document
        .querySelector('meta[name="api-base-url"]')
        ?.getAttribute("content")
        ?.trim()
        .replace(/\/+$/, "");
    if (!apiBase) {
        throw new Error("The authentication API base URL is not configured.");
    }

    const userIdInput = document.getElementById("controller-user-id");
    const passwordInput = document.getElementById("controller-password");
    const userIdError = document.getElementById("user-id-error");
    const passwordError = document.getElementById("password-error");
    const message = document.getElementById("login-message");
    const submitButton = document.getElementById("submit-login");
    const submitLabel = document.getElementById("submit-label");
    const togglePasswordButton = document.getElementById("toggle-password");

    class ApiError extends Error {
        constructor(status, detail) {
            super(detail);
            this.status = status;
        }
    }

    function showMessage(text, state = "info") {
        message.textContent = text;
        message.dataset.state = state;
        message.hidden = false;
        message.setAttribute("role", state === "error" ? "alert" : "status");
    }

    function clearMessage() {
        message.textContent = "";
        message.hidden = true;
        message.removeAttribute("data-state");
        message.setAttribute("role", "status");
    }

    function setFieldError(element, input, text) {
        element.textContent = text;
        input.setAttribute("aria-invalid", text ? "true" : "false");
    }

    function setBusy(busy) {
        submitButton.disabled = busy;
        submitLabel.textContent = busy ? "Checking credentials..." : "Sign in securely";
    }

    function errorMessage(error, phase) {
        if (error instanceof ApiError) {
            if (error.status === 401) {
                return phase === "session"
                    ? "Your controller session could not be established or has expired. Please sign in again."
                    : "Invalid User ID or password.";
            }
            if (error.status === 403) {
                return "This account is not authorized for controller access.";
            }
            if (error.status >= 500) {
                return "The authentication service is unavailable. Please try again later.";
            }
            return error.message || `The request failed with HTTP ${error.status}.`;
        }
        return error.message || "Unable to complete sign in. Please try again.";
    }

    async function requestJson(path, options = {}) {
        let response;
        try {
            response = await fetch(`${apiBase}${path}`, {
                method: options.method || "GET",
                credentials: "include",
                headers: options.payload
                    ? { "Content-Type": "application/json" }
                    : undefined,
                body: options.payload
                    ? JSON.stringify(options.payload)
                    : undefined,
            });
        } catch {
            throw new Error(
                "Could not reach Smart Stadium. Check that the backend is running and this page is served from a trusted origin."
            );
        }

        const contentType = response.headers.get("content-type") || "";
        let body;
        if (contentType.includes("application/json")) {
            try {
                body = await response.json();
            } catch {
                throw new Error(
                    `The backend returned an unreadable response (HTTP ${response.status}).`
                );
            }
        } else {
            const responseText = await response.text();
            body = { detail: responseText.trim() };
        }

        if (response.status !== 200) {
            const detail =
                typeof body.detail === "string" && body.detail
                    ? body.detail
                    : `Request failed with HTTP ${response.status}.`;
            throw new ApiError(response.status, detail);
        }

        return body;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearMessage();
        setFieldError(userIdError, userIdInput, "");
        setFieldError(passwordError, passwordInput, "");

        const userId = userIdInput.value.trim();
        const password = passwordInput.value;
        let valid = true;

        if (!userId) {
            setFieldError(userIdError, userIdInput, "Enter your assigned User ID.");
            valid = false;
        }
        if (!password) {
            setFieldError(passwordError, passwordInput, "Enter your password.");
            valid = false;
        }
        if (!valid) {
            (userId ? passwordInput : userIdInput).focus();
            return;
        }

        setBusy(true);
        let phase = "login";
        try {
            const login = await requestJson("/auth/controller/login", {
                method: "POST",
                payload: { user_id: userId, password },
            });
            if (
                login.role !== "CONTROLLER"
                || typeof login.user_id !== "string"
            ) {
                throw new ApiError(
                    403,
                    "The backend did not confirm a controller account."
                );
            }

            phase = "session";
            const session = await requestJson("/auth/me");
            if (
                session.role !== "CONTROLLER"
                || session.user_id !== login.user_id
            ) {
                throw new ApiError(
                    403,
                    "The authenticated session is not a controller account."
                );
            }

            showMessage("Controller access confirmed. Opening operations...");
            window.location.assign("../operations-dashboard/index.html");
        } catch (error) {
            showMessage(errorMessage(error, phase), "error");
        } finally {
            setBusy(false);
        }
    });

    togglePasswordButton.addEventListener("click", () => {
        const isVisible = passwordInput.type === "text";
        passwordInput.type = isVisible ? "password" : "text";
        togglePasswordButton.textContent = isVisible ? "Show" : "Hide";
        togglePasswordButton.setAttribute("aria-pressed", String(!isVisible));
        togglePasswordButton.setAttribute(
            "aria-label",
            isVisible ? "Show password" : "Hide password"
        );
    });

    for (const [input, errorElement] of [
        [userIdInput, userIdError],
        [passwordInput, passwordError],
    ]) {
        input.addEventListener("input", () => {
            if (input.value.trim()) {
                setFieldError(errorElement, input, "");
            }
        });
    }
})();
