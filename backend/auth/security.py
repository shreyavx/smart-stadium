import base64
import hashlib
import hmac
import secrets
import string


_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_PASSWORD_HASH_BYTES = 64


def validate_password(password: str) -> None:
    if len(password) < 12 or len(password) > 1024:
        raise ValueError("Password must be between 12 and 1024 characters.")


def hash_password(password: str) -> str:
    validate_password(password)
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_PASSWORD_HASH_BYTES,
    )
    return "$".join(
        (
            "scrypt",
            str(_SCRYPT_N),
            str(_SCRYPT_R),
            str(_SCRYPT_P),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_value, digest_value = encoded_hash.split("$")
        if algorithm != "scrypt":
            raise ValueError("Unsupported password hash.")
        if (
            int(n) != _SCRYPT_N
            or int(r) != _SCRYPT_R
            or int(p) != _SCRYPT_P
        ):
            return False
        salt = base64.b64decode(salt_value, altchars=b"-_", validate=True)
        expected = base64.b64decode(
            digest_value,
            altchars=b"-_",
            validate=True,
        )
        if len(salt) != 16 or len(expected) != _PASSWORD_HASH_BYTES:
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(actual, expected)


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(
    phone_number: str,
    purpose: str,
    code: str,
    secret: bytes,
) -> str:
    message = f"{purpose}\0{phone_number}\0{code}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def generate_user_id(prefix: str) -> str:
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(12))
    return f"{prefix}-{suffix}"


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
