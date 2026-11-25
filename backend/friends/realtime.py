
from fastapi import WebSocket
from typing import Dict, Set

from backend.friends.database import get_connection


# Store active WebSocket connections by group
active_connections: Dict[int, Set[WebSocket]] = {}


async def connect_to_group(
    websocket: WebSocket,
    group_id: int,
    user_id: str
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
            """,
            (group_id, user_id)
        )

        member = cursor.fetchone()

        if member is None:
            await websocket.close(code=1008)
            return False

    finally:
        connection.close()

    await websocket.accept()

    if group_id not in active_connections:
        active_connections[group_id] = set()

    active_connections[group_id].add(websocket)

    return True


def disconnect_from_group(
    websocket: WebSocket,
    group_id: int
):
    if group_id in active_connections:
        active_connections[group_id].discard(websocket)

        if not active_connections[group_id]:
            del active_connections[group_id]


async def broadcast_to_group(
    group_id: int,
    message: dict
):
    connections = active_connections.get(group_id, set())

    disconnected = []

    for websocket in list(connections):
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)

    for websocket in disconnected:
        disconnect_from_group(websocket, group_id)
