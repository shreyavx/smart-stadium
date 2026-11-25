
from backend.friends.database import get_connection
from backend.stadium import STADIUM_ZONES


def update_location(group_id, user_id, zone_id, x, y):
    """
    Save the latest simulated location of a group member.
    Only members who enabled sharing can publish locations.
    """

    if zone_id not in STADIUM_ZONES:
        raise ValueError("Invalid stadium zone.")

    if not (0 <= x <= 1000 and 0 <= y <= 1000):
        raise ValueError("Coordinates must be between 0 and 1000.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Verify group membership and sharing permission
        cursor.execute("""
            SELECT sharing_enabled
            FROM group_members
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        member = cursor.fetchone()

        if member is None:
            raise PermissionError("You are not a member of this group.")

        if not member["sharing_enabled"]:
            raise PermissionError(
                "Enable location sharing before publishing your location."
            )

        # Insert or update the latest location
        cursor.execute("""
            INSERT INTO friend_locations
            (group_id, user_id, zone_id, x, y, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT(group_id, user_id)
            DO UPDATE SET
                zone_id = excluded.zone_id,
                x = excluded.x,
                y = excluded.y,
                updated_at = CURRENT_TIMESTAMP
        """, (group_id, user_id, zone_id, x, y))

        connection.commit()

        return {
            "group_id": group_id,
            "user_id": user_id,
            "zone_id": zone_id,
            "x": x,
            "y": y,
            "message": "Simulated location updated successfully."
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_group_locations(group_id, requester_id):
    """
    Retrieve locations shared by members of the same group.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Verify that the requester belongs to this group
        cursor.execute("""
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
        """, (group_id, requester_id))

        if cursor.fetchone() is None:
            raise PermissionError(
                "You are not authorized to view this group's locations."
            )

        # Return only members who enabled sharing
        cursor.execute("""
            SELECT
                locations.user_id,
                locations.zone_id,
                locations.x,
                locations.y,
                locations.updated_at

            FROM friend_locations AS locations

            INNER JOIN group_members AS members
                ON locations.group_id = members.group_id
                AND locations.user_id = members.user_id

            WHERE locations.group_id = ?
            AND members.sharing_enabled = 1
        """, (group_id,))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()
