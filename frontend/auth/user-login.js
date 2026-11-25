(() => {
    const page = document.querySelector(".auth-page[data-auth-mode]");
    if (!page) {
        return;
    }

    const mode = page.dataset.authMode;
    const isSignup = mode === "signup";
    if (!isSignup && mode !== "login") {
        throw new Error("Unknown visitor authentication mode.");
    }

    const apiBase = document
        .querySelector('meta[name="api-base-url"]')
        ?.getAttribute("content")
        ?.trim()
        .replace(/\/+$/, "");
    if (!apiBase) {
        throw new Error("The authentication API base URL is not configured.");
    }

    const phoneStep = document.getElementById("phone-step");
    const otpStep = document.getElementById("otp-step");
    const phoneForm = document.getElementById("phone-form");
    const otpForm = document.getElementById("otp-form");
    const phoneInput = document.getElementById("phone-number");
    const otpInput = document.getElementById("otp-code");
    const phoneDisplay = document.getElementById("phone-display");
    const phoneError = document.getElementById("phone-error");
    const otpError = document.getElementById("otp-error");
    const message = document.getElementById("form-message");
    const requestButton = document.getElementById("request-otp");
    const verifyButton = document.getElementById("verify-otp");
    const resendButton = document.getElementById("resend-otp");
    const changePhoneButton = document.getElementById("change-phone");
    const resendCooldown = Number(page.dataset.resendCooldown);
    const phonePattern = /^\+[1-9][0-9]{7,14}$/;
    const otpPattern = /^[0-9]{6}$/;

    let activePhone = "";
    let countdownTimer = null;

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

    function formatPhoneNumber(value) {
        return value.replace(/[\s()-]/g, "");
    }

    function setButtonBusy(button, busy, busyText) {
        const label = button.querySelector("span");
        if (busy) {
            button.dataset.originalLabel = label.textContent;
            label.textContent = busyText;
            button.disabled = true;
        } else {
            label.textContent = button.dataset.originalLabel || label.textContent;
            button.disabled = false;
        }
    }

    function startResendCountdown() {
        if (!Number.isInteger(resendCooldown) || resendCooldown < 1) {
            throw new Error("The backend resend cooldown is not configured.");
        }

        window.clearInterval(countdownTimer);
        let secondsRemaining = resendCooldown;
        resendButton.disabled = true;
        resendButton.textContent = `Resend code in ${secondsRemaining}s`;

        countdownTimer = window.setInterval(() => {
            secondsRemaining -= 1;
            if (secondsRemaining <= 0) {
                window.clearInterval(countdownTimer);
                countdownTimer = null;
                resendButton.disabled = false;
                resendButton.textContent = "Resend code";
                return;
            }
            resendButton.textContent = `Resend code in ${secondsRemaining}s`;
        }, 1000);
    }

    async function postJson(path, payload, expectedStatus) {
        let response;
        try {
            response = await fetch(`${apiBase}${path}`, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
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

        if (response.status !== expectedStatus) {
            const detail =
                typeof body.detail === "string" && body.detail
                    ? body.detail
                    : `Request failed with HTTP ${response.status}.`;
            const error = new Error(detail);
            error.status = response.status;
            throw error;
        }

        return body;
    }

    function otpRequestPath() {
        return isSignup ? "/auth/visitor/signup" : "/auth/visitor/login";
    }

    function otpVerifyPath() {
        return isSignup
            ? "/auth/visitor/signup/verify"
            : "/auth/visitor/login/verify";
    }

    async function requestCode(phoneNumber, isResend = false) {
        const button = isResend ? resendButton : requestButton;
        if (!isResend) {
            setButtonBusy(
                requestButton,
                true,
                "Sending code..."
            );
        } else {
            resendButton.disabled = true;
            resendButton.textContent = "Sending code...";
        }
        clearMessage();

        try {
            const result = await postJson(
                otpRequestPath(),
                { phone_number: phoneNumber },
                202
            );
            activePhone = phoneNumber;
            phoneDisplay.textContent = phoneNumber;
            phoneStep.hidden = true;
            otpStep.hidden = false;
            otpInput.value = "";
            setFieldError(otpError, otpInput, "");
            showMessage(
                result.message ||
                    "If the phone number is eligible, a verification code was sent."
            );
            startResendCountdown();
            otpInput.focus();
        } catch (error) {
            showMessage(error.message, "error");
            if (error.status === 429) {
                startResendCountdown();
            } else if (isResend) {
                resendButton.disabled = false;
                resendButton.textContent = "Resend code";
            }
        } finally {
            if (!isResend) {
                setButtonBusy(requestButton, false, "");
            } else if (!resendButton.disabled) {
                resendButton.textContent = "Resend code";
            }
            if (isResend && button.disabled && !countdownTimer) {
                button.disabled = false;
            }
        }
    }

    phoneForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearMessage();
        setFieldError(phoneError, phoneInput, "");

        const phoneNumber = formatPhoneNumber(phoneInput.value);
        if (!phonePattern.test(phoneNumber)) {
            setFieldError(
                phoneError,
                phoneInput,
                "Enter a valid phone number in E.164 format, including + and country code."
            );
            phoneInput.focus();
            return;
        }

        await requestCode(phoneNumber);
    });

    otpForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearMessage();
        setFieldError(otpError, otpInput, "");

        const code = otpInput.value.trim();
        if (!otpPattern.test(code)) {
            setFieldError(otpError, otpInput, "Enter the 6-digit code from your SMS.");
            otpInput.focus();
            return;
        }

        setButtonBusy(verifyButton, true, "Verifying...");
        try {
            const result = await postJson(
                otpVerifyPath(),
                { phone_number: activePhone, code },
                200
            );
            if (result.role !== "USER" || typeof result.user_id !== "string") {
                throw new Error(
                    "The backend did not confirm a visitor account. Please try again."
                );
            }
            showMessage("Phone verified. Opening your dashboard...");
            window.location.assign("../index.html");
        } catch (error) {
            showMessage(error.message, "error");
            if (error.status === 401) {
                otpInput.value = "";
                otpInput.focus();
            }
        } finally {
            setButtonBusy(verifyButton, false, "");
        }
    });

    otpInput.addEventListener("input", () => {
        otpInput.value = otpInput.value.replace(/[^0-9]/g, "").slice(0, 6);
        if (otpInput.value.length === 6) {
            setFieldError(otpError, otpInput, "");
        }
    });

    resendButton.addEventListener("click", async () => {
        if (!activePhone || resendButton.disabled) {
            return;
        }
        await requestCode(activePhone, true);
    });

    changePhoneButton.addEventListener("click", () => {
        window.clearInterval(countdownTimer);
        countdownTimer = null;
        activePhone = "";
        otpStep.hidden = true;
        phoneStep.hidden = false;
        otpInput.value = "";
        setFieldError(otpError, otpInput, "");
        setFieldError(phoneError, phoneInput, "");
        clearMessage();
        resendButton.disabled = true;
        resendButton.textContent = `Resend code in ${resendCooldown}s`;
        phoneInput.focus();
    });
})();
