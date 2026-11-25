from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel

from backend.auth.config import (
    AuthConfigurationError,
    get_auth_settings,
)
from backend.auth.dependencies import get_current_principal, require_roles
from backend.auth.service import (
    AccountConflict,
    AuthPrincipal,
    InvalidCredentials,
    InvalidOtp,
    OtpCooldown,
    authenticate_password,
    create_controller,
    request_visitor_otp,
    revoke_session,
    verify_visitor_otp,
)
from backend.auth.sms import SmsDeliveryError, SmsNotConfigured


router = APIRouter(prefix="/auth", tags=["Authentication"])


class PhoneRequest(BaseModel):
    phone_number: str


class VerifyOtpRequest(BaseModel):
    phone_number: str
    code: str


class PasswordLoginRequest(BaseModel):
    user_id: str
    password: str


class CreateControllerRequest(BaseModel):
    password: str


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_auth_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.session_lifetime_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"


def _clear_session_cookie(response: Response) -> None:
    settings = get_auth_settings()
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"


def _map_otp_request_error(error: Exception) -> HTTPException:
    if isinstance(error, SmsNotConfigured):
        return HTTPException(
            status_code=503,
            detail="SMS delivery is not configured.",
        )
    if isinstance(error, AuthConfigurationError):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, OtpCooldown):
        return HTTPException(status_code=429, detail=str(error))
    if isinstance(error, SmsDeliveryError):
        return HTTPException(
            status_code=502,
            detail="SMS delivery failed. Please try again later.",
        )
    if isinstance(error, ValueError):
        return HTTPException(status_code=422, detail=str(error))
    raise error


def _request_visitor_otp(phone_number: str, purpose: str) -> dict:
    try:
        request_visitor_otp(phone_number, purpose)
    except (
        SmsNotConfigured,
        AuthConfigurationError,
        OtpCooldown,
        SmsDeliveryError,
        ValueError,
    ) as error:
        raise _map_otp_request_error(error)

    return {
        "message": "If the phone number is eligible, a verification code was sent."
    }


def _complete_visitor_login(
    response: Response,
    phone_number: str,
    code: str,
    purpose: str,
) -> dict:
    try:
        created_session = verify_visitor_otp(phone_number, code, purpose)
    except AuthConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except (InvalidOtp, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired verification code.",
        )

    _set_session_cookie(response, created_session.token)
    return {
        "user_id": created_session.principal.user_id,
        "role": created_session.principal.role,
    }


@router.post("/visitor/signup", status_code=status.HTTP_202_ACCEPTED)
def request_visitor_signup(request: PhoneRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return _request_visitor_otp(request.phone_number, "signup")


@router.post("/visitor/login", status_code=status.HTTP_202_ACCEPTED)
def request_visitor_login(request: PhoneRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return _request_visitor_otp(request.phone_number, "login")


@router.post("/visitor/signup/verify")
def verify_visitor_signup(
    request: VerifyOtpRequest,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return _complete_visitor_login(
        response,
        request.phone_number,
        request.code,
        "signup",
    )


@router.post("/visitor/login/verify")
def verify_visitor_login(
    request: VerifyOtpRequest,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return _complete_visitor_login(
        response,
        request.phone_number,
        request.code,
        "login",
    )


def _password_login(
    request: PasswordLoginRequest,
    response: Response,
    expected_role: str,
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    try:
        created_session = authenticate_password(
            request.user_id,
            request.password,
            expected_role,
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=401,
            detail="Invalid User ID or password.",
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    _set_session_cookie(response, created_session.token)
    return {
        "user_id": created_session.principal.user_id,
        "role": created_session.principal.role,
    }


@router.post("/controller/login")
def controller_login(request: PasswordLoginRequest, response: Response):
    return _password_login(request, response, "CONTROLLER")


@router.post("/admin/login")
def admin_login(request: PasswordLoginRequest, response: Response):
    return _password_login(request, response, "ADMIN")


@router.post(
    "/admin/controllers",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("ADMIN"))],
)
def provision_controller(
    request: CreateControllerRequest,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    try:
        user_id = create_controller(request.password)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except AccountConflict as error:
        raise HTTPException(status_code=409, detail=str(error))
    return {"user_id": user_id, "role": "CONTROLLER"}


@router.get("/me")
def current_account(
    principal: AuthPrincipal = Depends(get_current_principal),
):
    return {
        "user_id": principal.user_id,
        "role": principal.role,
        "phone_number": principal.phone_number,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response):
    settings = get_auth_settings()
    revoke_session(request.cookies.get(settings.cookie_name))
    _clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
