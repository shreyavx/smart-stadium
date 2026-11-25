import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.auth import service
from backend.auth.security import hash_password, verify_password
from backend.friends import database
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "auth-test.db")
    monkeypatch.setenv("SMART_STADIUM_AUTH_SECRET", "test-auth-secret-" * 3)
    monkeypatch.setenv("SMART_STADIUM_COOKIE_SECURE", "false")
    monkeypatch.delenv("AZURE_COMMUNICATION_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("AZURE_COMMUNICATION_SMS_FROM", raising=False)
    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sms_capture(monkeypatch):
    delivered_codes = []
    monkeypatch.setattr(service, "is_sms_configured", lambda: True)
    monkeypatch.setattr(
        service,
        "send_verification_code",
        lambda phone, code, purpose: delivered_codes.append(
            (phone, code, purpose)
        ),
    )
    return delivered_codes


def _signup(client, sms_capture, phone_number="+14155550123"):
    response = client.post(
        "/auth/visitor/signup",
        json={"phone_number": phone_number},
    )
    assert response.status_code == 202
    code = sms_capture[-1][1]
    verified = client.post(
        "/auth/visitor/signup/verify",
        json={"phone_number": phone_number, "code": code},
    )
    assert verified.status_code == 200
    return verified.json()


def test_sms_unconfigured_is_reported_without_revealing_an_otp(
    client,
    monkeypatch,
):
    monkeypatch.setattr(service, "is_sms_configured", lambda: False)

    response = client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550123"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "SMS delivery is not configured."
    assert "code" not in response.json()


def test_otp_expiry_and_single_use(client, sms_capture, monkeypatch):
    current_time = [1_800_000_000]
    monkeypatch.setattr(service.time, "time", lambda: current_time[0])

    signup = client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550124"},
    )
    assert signup.status_code == 202
    code = sms_capture[-1][1]

    current_time[0] += 301
    expired = client.post(
        "/auth/visitor/signup/verify",
        json={"phone_number": "+14155550124", "code": code},
    )
    assert expired.status_code == 401

    current_time[0] += 1
    client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550124"},
    )
    code = sms_capture[-1][1]
    valid = client.post(
        "/auth/visitor/signup/verify",
        json={"phone_number": "+14155550124", "code": code},
    )
    reused = client.post(
        "/auth/visitor/signup/verify",
        json={"phone_number": "+14155550124", "code": code},
    )

    assert valid.status_code == 200
    assert reused.status_code == 401


def test_invalid_otp_attempts_are_limited(client, sms_capture):
    client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550125"},
    )
    actual_code = sms_capture[-1][1]
    invalid_code = "000000" if actual_code != "000000" else "000001"

    responses = [
        client.post(
            "/auth/visitor/signup/verify",
            json={
                "phone_number": "+14155550125",
                "code": invalid_code,
            },
        )
        for _ in range(5)
    ]

    assert all(response.status_code == 401 for response in responses)
    assert client.post(
        "/auth/visitor/signup/verify",
        json={
            "phone_number": "+14155550125",
            "code": actual_code,
        },
    ).status_code == 401


def test_otp_resend_cooldown(client, sms_capture):
    first = client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550126"},
    )
    second = client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550126"},
    )

    assert first.status_code == 202
    assert second.status_code == 429
    assert len(sms_capture) == 1


def test_visitor_can_login_with_a_new_otp(client, sms_capture):
    signup = _signup(client, sms_capture, "+14155550130")
    client.post("/auth/logout")

    requested = client.post(
        "/auth/visitor/login",
        json={"phone_number": "+14155550130"},
    )
    assert requested.status_code == 202
    code = sms_capture[-1][1]
    verified = client.post(
        "/auth/visitor/login/verify",
        json={"phone_number": "+14155550130", "code": code},
    )

    assert verified.status_code == 200
    assert verified.json() == {
        "user_id": signup["user_id"],
        "role": "USER",
    }


def test_password_hashing_and_invalid_controller_credentials(
    client,
):
    password = "ControllerPassword!2026"
    encoded = hash_password(password)

    assert encoded != password
    assert verify_password(password, encoded)
    assert not verify_password("wrong-password", encoded)

    response = client.post(
        "/auth/controller/login",
        json={"user_id": "missing", "password": password},
    )
    assert response.status_code == 401


def test_admin_provisions_controller_and_role_is_enforced(client):
    service.bootstrap_admin("admin-local", "AdministratorPassword!2026")

    admin_login = client.post(
        "/auth/admin/login",
        json={
            "user_id": "admin-local",
            "password": "AdministratorPassword!2026",
        },
    )
    assert admin_login.status_code == 200
    assert admin_login.json()["role"] == "ADMIN"

    created = client.post(
        "/auth/admin/controllers",
        json={"password": "ControllerPassword!2026"},
    )
    assert created.status_code == 201
    controller_id = created.json()["user_id"]
    assert created.json()["role"] == "CONTROLLER"

    controller_login = client.post(
        "/auth/controller/login",
        json={
            "user_id": controller_id,
            "password": "ControllerPassword!2026",
        },
    )
    assert controller_login.status_code == 200
    assert controller_login.json()["role"] == "CONTROLLER"
    assert client.post(
        "/simulate/surge",
        json={"zone_id": "GATE_A"},
    ).status_code == 200
    assert client.post("/simulate/stop").status_code == 200
    assert client.post(
        "/auth/admin/controllers",
        json={"password": "AnotherControllerPassword!2026"},
    ).status_code == 403


def test_visitor_role_cannot_control_simulation(client, sms_capture):
    visitor = _signup(client, sms_capture)

    assert visitor["role"] == "USER"
    assert client.get("/stadium/snapshot").status_code == 200
    assert client.post(
        "/simulate/surge",
        json={"zone_id": "GATE_A"},
    ).status_code == 403
    assert client.post("/simulate/stop").status_code == 403


def test_session_expiry_and_logout_revoke_access(
    client,
    sms_capture,
    monkeypatch,
):
    current_time = [1_800_000_000]
    monkeypatch.setattr(service.time, "time", lambda: current_time[0])
    _signup(client, sms_capture, "+14155550127")

    assert client.get("/auth/me").status_code == 200
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401

    client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550128"},
    )
    code = sms_capture[-1][1]
    assert client.post(
        "/auth/visitor/signup/verify",
        json={"phone_number": "+14155550128", "code": code},
    ).status_code == 200

    current_time[0] += 12 * 60 * 60
    assert client.get("/auth/me").status_code == 401


def test_session_cookie_is_http_only_secure_and_not_returned(
    client,
    sms_capture,
    monkeypatch,
):
    monkeypatch.setenv("SMART_STADIUM_COOKIE_SECURE", "true")
    response = client.post(
        "/auth/visitor/signup",
        json={"phone_number": "+14155550131"},
    )
    code = sms_capture[-1][1]
    verified = client.post(
        "/auth/visitor/signup/verify",
        json={"phone_number": "+14155550131", "code": code},
    )
    cookie = verified.headers["set-cookie"].lower()

    assert response.status_code == 202
    assert verified.status_code == 200
    assert verified.json()["role"] == "USER"
    assert "token" not in verified.json()
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie


def test_cookie_mutations_reject_untrusted_origins(client, sms_capture):
    visitor = _signup(client, sms_capture, "+14155550132")
    response = client.post(
        "/groups/create",
        headers={
            "X-User-ID": visitor["user_id"],
            "Origin": "https://untrusted.example",
        },
        json={"group_name": "Blocked"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin."


def test_group_identity_comes_from_authenticated_session(
    client,
    sms_capture,
):
    visitor = _signup(client, sms_capture)
    user_id = visitor["user_id"]

    created = client.post(
        "/groups/create",
        headers={"X-User-ID": user_id},
        json={"group_name": "Family"},
    )
    assert created.status_code == 200

    spoofed = client.post(
        "/groups/create",
        headers={"X-User-ID": "another-user"},
        json={"group_name": "Spoofed"},
    )
    assert spoofed.status_code == 403

    database.initialize_database()
    members = client.get(
        f"/groups/{created.json()['group_id']}/members",
        headers={"X-User-ID": user_id},
    )
    assert members.status_code == 200
    assert members.json()["members"][0]["user_id"] == user_id

    group_id = created.json()["group_id"]
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/groups/{group_id}/live?user_id=another-user"
        ):
            pass

    with client.websocket_connect(
        f"/groups/{group_id}/live?user_id={user_id}"
    ) as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "initial_locations"
        assert initial["group_id"] == group_id


def test_stadium_websocket_requires_authenticated_session(client, sms_capture):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/stadium"):
            pass

    _signup(client, sms_capture, "+14155550129")
    with client.websocket_connect("/ws/stadium") as websocket:
        assert websocket.receive_json()["event"] == "stadium_update"
