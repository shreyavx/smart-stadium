import hmac
from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request, WebSocket

from backend.auth.config import get_auth_settings, is_trusted_origin
from backend.auth.service import AuthPrincipal, get_session_principal


def get_current_principal(request: Request) -> AuthPrincipal:
    settings = get_auth_settings()
    principal = get_session_principal(
        request.cookies.get(settings.cookie_name)
    )
    if principal is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return principal


def require_roles(*roles: str) -> Callable:
    def role_dependency(
        principal: AuthPrincipal = Depends(get_current_principal),
    ) -> AuthPrincipal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role.")
        return principal

    return role_dependency


def get_authenticated_user_id(
    x_user_id: str = Header(..., alias="X-User-ID"),
    principal: AuthPrincipal = Depends(require_roles("USER", "CONTROLLER")),
) -> str:
    if not hmac.compare_digest(x_user_id, principal.user_id):
        raise HTTPException(
            status_code=403,
            detail="X-User-ID must match the authenticated account.",
        )
    return principal.user_id


async def authenticate_websocket(
    websocket: WebSocket,
    allowed_roles: tuple[str, ...],
) -> AuthPrincipal | None:
    settings = get_auth_settings()
    if not is_trusted_origin(websocket.headers.get("origin")):
        await websocket.close(code=1008, reason="Untrusted origin.")
        return None

    principal = get_session_principal(
        websocket.cookies.get(settings.cookie_name)
    )
    if principal is None or principal.role not in allowed_roles:
        await websocket.close(code=1008, reason="Authentication required.")
        return None
    return principal
