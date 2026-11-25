
import sqlite3
import secrets
import string

from backend.friends.database import get_connection


def generate_invite_code(length=8):
    """Generate a random invitation code."""

    characters = string.ascii_uppercase + string.digits

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )


def create_group(group_name, user_id):
    """Create a private group and add its creator as a member."""

    if not group_name or not group_name.strip():
        raise ValueError("Group name cannot be empty.")

    if not user_id or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Generate a unique invitation code
        invite_code = generate_invite_code()

        while True:
            cursor.execute(
                "SELECT group_id FROM friend_groups WHERE invite_code = ?",
                (invite_code,)
            )

            if cursor.fetchone() is None:
                break

            invite_code = generate_invite_code()

        # Create the group
        cursor.execute("""
            INSERT INTO friend_groups
            (group_name, invite_code, created_by)
            VALUES (?, ?, ?)
        """, (group_name.strip(), invite_code, user_id.strip()))

        group_id = cursor.lastrowid

        # Automatically add the creator as a member
        cursor.execute("""
            INSERT INTO group_members
            (group_id, user_id, sharing_enabled)
            VALUES (?, ?, 0)
        """, (group_id, user_id.strip()))

        connection.commit()

        return {
            "group_id": group_id,
            "group_name": group_name.strip(),
            "invite_code": invite_code,
            "created_by": user_id.strip()
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def join_group(invite_code, user_id):
    """Join an existing group using its invitation code."""

    if not invite_code or not user_id:
        raise ValueError("Invitation code and user ID are required.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Find the group
        cursor.execute("""
            SELECT group_id, group_name
            FROM friend_groups
            WHERE invite_code = ?
        """, (invite_code.strip().upper(),))

        group = cursor.fetchone()

        if group is None:
            raise ValueError("Invalid invitation code.")

        group_id = group["group_id"]

        # Check whether the user is already a member
        cursor.execute("""
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id.strip()))

        if cursor.fetchone():
            raise ValueError("You are already a member of this group.")

        # Add the new member
        cursor.execute("""
            INSERT INTO group_members
            (group_id, user_id, sharing_enabled)
            VALUES (?, ?, 0)
        """, (group_id, user_id.strip()))

        connection.commit()

        return {
            "message": "Successfully joined the group.",
            "group_id": group_id,
            "group_name": group["group_name"],
            "user_id": user_id.strip()
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_group_members(group_id, user_id):
    """Return group members only if the requester belongs to the group."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Verify requester membership
        cursor.execute("""
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        if cursor.fetchone() is None:
            raise PermissionError(
                "You are not authorized to view this group's members."
            )

        cursor.execute("""
            SELECT user_id, sharing_enabled, joined_at
            FROM group_members
            WHERE group_id = ?
            ORDER BY joined_at
        """, (group_id,))

        members = [dict(row) for row in cursor.fetchall()]

        return members

    finally:
        connection.close()
