import hmac
import re
import sqlite3
import time
from dataclasses import dataclass

from backend.auth.config import (
    get_auth_settings,
    require_auth_secret,
)
from backend.auth.security import (
    generate_otp,
    generate_session_token,
    generate_user_id,
    hash_otp,
    hash_password,
    hash_session_token,
    validate_password,
    verify_password,
)
from backend.auth.sms import (
    SmsDeliveryError,
    SmsNotConfigured,
    is_sms_configured,
    send_verification_code,
)
from backend.friends.database import get_connection, initialize_database


_E164_PATTERN = re.compile(r"^\+[1-9][0-9]{7,14}$")
_USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,64}$")
_VALID_OTP_PURPOSES = {"signup", "login"}


class InvalidCredentials(RuntimeError):
    pass


class InvalidOtp(RuntimeError):
    pass


class OtpCooldown(RuntimeError):
    pass


class AccountConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: str
    role: str
    phone_number: str | None
    must_change_password: bool


@dataclass(frozen=True)
class CreatedSession:
    token: str
    principal: AuthPrincipal
    expires_at: int


def normalize_phone_number(phone_number: str) -> str:
    normalized = phone_number.strip()
    if not _E164_PATTERN.fullmatch(normalized):
        raise ValueError("Phone number must use E.164 format.")
    return normalized


def request_visitor_otp(phone_number: str, purpose: str) -> bool:
    phone_number = normalize_phone_number(phone_number)
    if purpose not in _VALID_OTP_PURPOSES:
        raise ValueError("Invalid OTP purpose.")
    if not is_sms_configured():
        raise SmsNotConfigured("SMS delivery is not configured.")

    settings = get_auth_settings()
    otp_secret = require_auth_secret(settings)
    now = int(time.time())
    code = generate_otp()
    challenge_id = generate_user_id("OTP")
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT created_at
            FROM auth_otp_challenges
            WHERE phone_number = ? AND purpose = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (phone_number, purpose),
        )
        previous = cursor.fetchone()
        if previous is not None and now - previous["created_at"] < (
            settings.otp_cooldown_seconds
        ):
            raise OtpCooldown("Please wait before requesting another code.")

        if purpose == "signup":
            cursor.execute(
                "SELECT user_id FROM auth_users WHERE phone_number = ?",
                (phone_number,),
            )
            eligible = cursor.fetchone() is None
        else:
            cursor.execute(
                """
                SELECT user_id
                FROM auth_users
                WHERE phone_number = ?
                    AND role = 'USER'
                    AND phone_verified_at IS NOT NULL
                    AND is_active = 1
                """,
                (phone_number,),
            )
            eligible = cursor.fetchone() is not None

        if not eligible:
            connection.rollback()
            return False

        cursor.execute(
            """
            UPDATE auth_otp_challenges
            SET consumed_at = ?
            WHERE phone_number = ? AND purpose = ? AND consumed_at IS NULL
            """,
            (now, phone_number, purpose),
        )
        cursor.execute(
            """
            INSERT INTO auth_otp_challenges (
                challenge_id, phone_number, purpose, code_hash,
                created_at, expires_at, attempts, consumed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, NULL)
            """,
            (
                challenge_id,
                phone_number,
                purpose,
                hash_otp(phone_number, purpose, code, otp_secret),
                now,
                now + settings.otp_lifetime_seconds,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    try:
        send_verification_code(phone_number, code, purpose)
    except (SmsNotConfigured, SmsDeliveryError):
        _delete_challenge(challenge_id)
        raise

    return True


def _delete_challenge(challenge_id: str) -> None:
    connection = get_connection()
    try:
        connection.execute(
            """
            DELETE FROM auth_otp_challenges
            WHERE challenge_id = ?
            """,
            (challenge_id,),
        )
        connection.commit()
    finally:
        connection.close()


def verify_visitor_otp(
    phone_number: str,
    code: str,
    purpose: str,
) -> CreatedSession:
    phone_number = normalize_phone_number(phone_number)
    if purpose not in _VALID_OTP_PURPOSES:
        raise InvalidOtp("Invalid or expired verification code.")
    if not re.fullmatch(r"[0-9]{6}", code):
        raise InvalidOtp("Invalid or expired verification code.")

    settings = get_auth_settings()
    otp_secret = require_auth_secret(settings)
    now = int(time.time())
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT challenge_id, code_hash, expires_at, attempts
            FROM auth_otp_challenges
            WHERE phone_number = ? AND purpose = ? AND consumed_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (phone_number, purpose),
        )
        challenge = cursor.fetchone()
        if challenge is None:
            raise InvalidOtp("Invalid or expired verification code.")

        if now >= challenge["expires_at"]:
            cursor.execute(
                """
                UPDATE auth_otp_challenges
                SET consumed_at = ?
                WHERE challenge_id = ?
                """,
                (now, challenge["challenge_id"]),
            )
            connection.commit()
            raise InvalidOtp("Invalid or expired verification code.")

        expected_hash = hash_otp(phone_number, purpose, code, otp_secret)
        if not hmac.compare_digest(expected_hash, challenge["code_hash"]):
            attempts = challenge["attempts"] + 1
            consumed_at = (
                now if attempts >= settings.otp_max_attempts else None
            )
            cursor.execute(
                """
                UPDATE auth_otp_challenges
                SET attempts = ?, consumed_at = ?
                WHERE challenge_id = ?
                """,
                (attempts, consumed_at, challenge["challenge_id"]),
            )
            connection.commit()
            raise InvalidOtp("Invalid or expired verification code.")

        cursor.execute(
            """
            UPDATE auth_otp_challenges
            SET consumed_at = ?
            WHERE challenge_id = ?
            """,
            (now, challenge["challenge_id"]),
        )

        if purpose == "signup":
            cursor.execute(
                "SELECT user_id FROM auth_users WHERE phone_number = ?",
                (phone_number,),
            )
            if cursor.fetchone() is not None:
                connection.commit()
                raise InvalidOtp("Invalid or expired verification code.")
            try:
                principal = _insert_user(
                    cursor,
                    role="USER",
                    phone_number=phone_number,
                    password_hash_value=None,
                    phone_verified_at=now,
                    must_change_password=False,
                    user_id_prefix="USR",
                    now=now,
                )
            except AccountConflict:
                connection.commit()
                raise InvalidOtp("Invalid or expired verification code.")
        else:
            cursor.execute(
                """
                SELECT user_id, role, phone_number, must_change_password
                FROM auth_users
                WHERE phone_number = ?
                    AND role = 'USER'
                    AND phone_verified_at IS NOT NULL
                    AND is_active = 1
                """,
                (phone_number,),
            )
            user = cursor.fetchone()
            if user is None:
                connection.commit()
                raise InvalidOtp("Invalid or expired verification code.")
            principal = _principal_from_row(user)

        created_session = _insert_session(cursor, principal, now, settings)
        connection.commit()
        return created_session
    finally:
        connection.close()


def _insert_user(
    cursor: sqlite3.Cursor,
    role: str,
    phone_number: str | None,
    password_hash_value: str | None,
    phone_verified_at: int | None,
    must_change_password: bool,
    user_id_prefix: str,
    now: int,
) -> AuthPrincipal:
    for _ in range(5):
        user_id = generate_user_id(user_id_prefix)
        try:
            cursor.execute(
                """
                INSERT INTO auth_users (
                    user_id, phone_number, role, password_hash,
                    phone_verified_at, must_change_password,
                    is_active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    user_id,
                    phone_number,
                    role,
                    password_hash_value,
                    phone_verified_at,
                    int(must_change_password),
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            if phone_number is not None:
                cursor.execute(
                    "SELECT user_id FROM auth_users WHERE phone_number = ?",
                    (phone_number,),
                )
                if cursor.fetchone() is not None:
                    raise AccountConflict("Phone number is already registered.")
            continue

        return AuthPrincipal(
            user_id=user_id,
            role=role,
            phone_number=phone_number,
            must_change_password=must_change_password,
        )

    raise RuntimeError("Unable to generate a unique user ID.")


def _insert_session(
    cursor: sqlite3.Cursor,
    principal: AuthPrincipal,
    now: int,
    settings,
) -> CreatedSession:
    token = generate_session_token()
    expires_at = now + settings.session_lifetime_seconds
    cursor.execute(
        """
        INSERT INTO auth_sessions (token_hash, user_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (hash_session_token(token), principal.user_id, now, expires_at),
    )
    return CreatedSession(token, principal, expires_at)


def authenticate_password(
    user_id: str,
    password: str,
    expected_role: str,
) -> CreatedSession:
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id, role, phone_number, password_hash,
                   must_change_password, is_active
            FROM auth_users
            WHERE user_id = ?
            """,
            (user_id.strip(),),
        )
        user = cursor.fetchone()
        if (
            user is None
            or user["role"] != expected_role
            or not user["is_active"]
            or not user["password_hash"]
            or not verify_password(password, user["password_hash"])
        ):
            raise InvalidCredentials("Invalid user ID or password.")

        principal = _principal_from_row(user)
        settings = get_auth_settings()
        created_session = _insert_session(
            cursor,
            principal,
            int(time.time()),
            settings,
        )
        connection.commit()
        return created_session
    finally:
        connection.close()


def create_controller(password: str) -> str:
    validate_password(password)
    password_hash_value = hash_password(password)
    now = int(time.time())
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        principal = _insert_user(
            connection.cursor(),
            role="CONTROLLER",
            phone_number=None,
            password_hash_value=password_hash_value,
            phone_verified_at=None,
            must_change_password=False,
            user_id_prefix="CTRL",
            now=now,
        )
        connection.commit()
        return principal.user_id
    finally:
        connection.close()


def bootstrap_admin(user_id: str, password: str) -> None:
    normalized_user_id = user_id.strip()
    if not _USER_ID_PATTERN.fullmatch(normalized_user_id):
        raise ValueError("Administrator User ID has an invalid format.")
    validate_password(password)
    password_hash_value = hash_password(password)
    now = int(time.time())
    initialize_database()
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM auth_users WHERE role = 'ADMIN' LIMIT 1")
        if cursor.fetchone() is not None:
            raise AccountConflict("An administrator is already provisioned.")
        cursor.execute(
            "SELECT 1 FROM auth_users WHERE user_id = ?",
            (normalized_user_id,),
        )
        if cursor.fetchone() is not None:
            raise AccountConflict("That administrator User ID is already in use.")
        _insert_user_with_id(
            cursor,
            normalized_user_id,
            password_hash_value,
            now,
        )
        connection.commit()
    finally:
        connection.close()


def _insert_user_with_id(
    cursor: sqlite3.Cursor,
    user_id: str,
    password_hash_value: str,
    now: int,
) -> None:
    cursor.execute(
        """
        INSERT INTO auth_users (
            user_id, phone_number, role, password_hash,
            phone_verified_at, must_change_password, is_active, created_at
        )
        VALUES (?, NULL, 'ADMIN', ?, NULL, 0, 1, ?)
        """,
        (user_id, password_hash_value, now),
    )


def get_session_principal(token: str | None) -> AuthPrincipal | None:
    if not token:
        return None

    now = int(time.time())
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT sessions.expires_at, users.user_id, users.role,
                   users.phone_number, users.must_change_password,
                   users.is_active
            FROM auth_sessions AS sessions
            INNER JOIN auth_users AS users
                ON users.user_id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.revoked_at IS NULL
            """,
            (hash_session_token(token),),
        )
        row = cursor.fetchone()
        if row is None or not row["is_active"]:
            return None
        if now >= row["expires_at"]:
            cursor.execute(
                """
                UPDATE auth_sessions
                SET revoked_at = ?
                WHERE token_hash = ? AND revoked_at IS NULL
                """,
                (now, hash_session_token(token)),
            )
            connection.commit()
            return None
        return _principal_from_row(row)
    finally:
        connection.close()


def revoke_session(token: str | None) -> None:
    if not token:
        return

    connection = get_connection()
    try:
        connection.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = ?
            WHERE token_hash = ? AND revoked_at IS NULL
            """,
            (int(time.time()), hash_session_token(token)),
        )
        connection.commit()
    finally:
        connection.close()


def _principal_from_row(row) -> AuthPrincipal:
    return AuthPrincipal(
        user_id=row["user_id"],
        role=row["role"],
        phone_number=row["phone_number"],
        must_change_password=bool(row["must_change_password"]),
    )
