
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect
)
from backend.auth.dependencies import (
    authenticate_websocket,
    get_authenticated_user_id,
)

from backend.friends.realtime import (
    connect_to_group,
    disconnect_from_group,
    broadcast_to_group
)

from pydantic import BaseModel

from backend.friends.group_manager import (
    create_group,
    join_group,
    get_group_members
)

from backend.friends.location_permissions import (
    set_location_sharing,
    get_location_sharing_status
)

from backend.friends.location_simulator import simulate_next_location
from backend.friends.location_service import get_group_locations


router = APIRouter(prefix="/groups", tags=["Friend Groups"])


# Request models

class CreateGroupRequest(BaseModel):
    group_name: str


class JoinGroupRequest(BaseModel):
    invite_code: str


@router.post("/create")
def create_new_group(
    request: CreateGroupRequest,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        result = create_group(request.group_name, user_id)
        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to create group."
        )


@router.post("/join")
def join_existing_group(
    request: JoinGroupRequest,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        result = join_group(request.invite_code, user_id)
        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to join group."
        )


@router.get("/{group_id}/members")
def view_group_members(
    group_id: int,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        members = get_group_members(group_id, user_id)

        return {
            "group_id": group_id,
            "members": members
        }

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve group members."
        )


@router.post("/{group_id}/sharing/start")
def start_location_sharing(
    group_id: int,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        return set_location_sharing(
            group_id,
            user_id,
            True
        )

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to enable location sharing."
        )


@router.post("/{group_id}/sharing/stop")
def stop_location_sharing(
    group_id: int,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        return set_location_sharing(
            group_id,
            user_id,
            False
        )

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to disable location sharing."
        )


@router.get("/{group_id}/sharing/status")
def check_location_sharing(
    group_id: int,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        return get_location_sharing_status(
            group_id,
            user_id
        )

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve sharing status."
        )



@router.post("/{group_id}/locations/simulate")
async def simulate_friend_location(
    group_id: int,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        result = simulate_next_location(group_id, user_id)

        # Notify connected members of this group
        await broadcast_to_group(
            group_id,
            {
                "type": "location_update",
                "location": result
            }
        )

        return result

    except PermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print("Location simulation error:", error)

        raise HTTPException(
            status_code=500,
            detail="Unable to simulate location."
        )


@router.get("/{group_id}/locations")
def view_friend_locations(
    group_id: int,
    user_id: str = Depends(get_authenticated_user_id),
):
    try:
        locations = get_group_locations(group_id, user_id)

        return {
            "group_id": group_id,
            "locations": locations
        }

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except Exception as error:
        print("Location retrieval error:", error)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve friend locations."
        )


@router.websocket("/{group_id}/live")
async def friend_live_updates(
    websocket: WebSocket,
    group_id: int,
    user_id: str
):
    principal = await authenticate_websocket(
        websocket,
        ("USER", "CONTROLLER"),
    )
    if principal is None:
        return
    if user_id != principal.user_id:
        await websocket.close(code=1008, reason="User ID does not match session.")
        return

    connected = await connect_to_group(
        websocket,
        group_id,
        principal.user_id
    )

    if not connected:
        return

    try:
        # Send the currently shared locations when a user connects
        locations = get_group_locations(group_id, principal.user_id)

        await websocket.send_json({
            "type": "initial_locations",
            "group_id": group_id,
            "locations": locations
        })

        # Keep the connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    finally:
        disconnect_from_group(websocket, group_id)
