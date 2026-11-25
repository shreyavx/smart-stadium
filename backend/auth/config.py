import os
from dataclasses import dataclass
from urllib.parse import urlsplit


class AuthConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthSettings:
    secret: str | None
    otp_lifetime_seconds: int
    otp_cooldown_seconds: int
    otp_max_attempts: int
    session_lifetime_seconds: int
    cookie_name: str
    cookie_secure: bool
    sms_connection_string: str | None
    sms_sender: str | None


def _read_boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise AuthConfigurationError(f"{name} must be true or false.")


def get_auth_settings() -> AuthSettings:
    return AuthSettings(
        secret=os.getenv("SMART_STADIUM_AUTH_SECRET"),
        otp_lifetime_seconds=300,
        otp_cooldown_seconds=60,
        otp_max_attempts=5,
        session_lifetime_seconds=12 * 60 * 60,
        cookie_name="smart_stadium_session",
        cookie_secure=_read_boolean("SMART_STADIUM_COOKIE_SECURE", True),
        sms_connection_string=os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING"),
        sms_sender=os.getenv("AZURE_COMMUNICATION_SMS_FROM"),
    )


def require_auth_secret(settings: AuthSettings) -> bytes:
    secret = (settings.secret or "").encode("utf-8")
    if len(secret) < 32:
        raise AuthConfigurationError(
            "SMART_STADIUM_AUTH_SECRET must contain at least 32 bytes."
        )
    return secret


def get_trusted_origins() -> list[str]:
    configured = os.getenv("SMART_STADIUM_CORS_ORIGINS")
    if configured is None:
        origins = (
            "http://localhost:8765",
            "http://127.0.0.1:8765",
            "http://localhost:8771",
            "http://127.0.0.1:8771",
        )
    else:
        origins = tuple(
            origin.strip()
            for origin in configured.split(",")
            if origin.strip()
        )

    if not origins or "*" in origins:
        raise AuthConfigurationError(
            "SMART_STADIUM_CORS_ORIGINS must contain explicit trusted origins."
        )

    for origin in origins:
        parsed = urlsplit(origin)
        local_http = (
            parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1"}
        )
        if (
            parsed.scheme != "https"
            and not local_http
            or parsed.netloc == ""
            or parsed.path != ""
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise AuthConfigurationError(
                "Trusted origins must be HTTPS, except for localhost development."
            )

    return list(origins)


def is_trusted_origin(origin: str | None) -> bool:
    if origin is None:
        return True
    return origin in get_trusted_origins()
