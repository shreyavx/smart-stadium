
from backend.friends.database import get_connection


def set_location_sharing(group_id, user_id, enabled):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        member = cursor.fetchone()

        if member is None:
            raise PermissionError(
                "You are not a member of this group."
            )

        cursor.execute("""
            UPDATE group_members
            SET sharing_enabled = ?
            WHERE group_id = ? AND user_id = ?
        """, (1 if enabled else 0, group_id, user_id))

        # Delete previously stored location when sharing stops
        if not enabled:
            cursor.execute("""
                DELETE FROM friend_locations
                WHERE group_id = ? AND user_id = ?
            """, (group_id, user_id))

        connection.commit()

        return {
            "group_id": group_id,
            "user_id": user_id,
            "sharing_enabled": bool(enabled),
            "message": (
                "Location sharing enabled."
                if enabled
                else "Location sharing disabled."
            )
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_location_sharing_status(group_id, user_id):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT sharing_enabled
            FROM group_members
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        member = cursor.fetchone()

        if member is None:
            raise PermissionError(
                "You are not a member of this group."
            )

        return {
            "group_id": group_id,
            "user_id": user_id,
            "sharing_enabled": bool(member["sharing_enabled"])
        }

    finally:
        connection.close()
