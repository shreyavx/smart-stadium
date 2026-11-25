from backend.friends.database import get_connection
from backend.friends.location_service import update_location
from backend.stadium import STADIUM_ZONES


def get_zone_coordinates():
    """
    Generate demonstration coordinates for the stadium zones.

    These are placeholder positions, not actual stadium map coordinates.
    They can be replaced with your real SVG map coordinates later.
    """

    zone_ids = list(STADIUM_ZONES.keys())

    if not zone_ids:
        raise ValueError("No stadium zones are configured.")

    total = len(zone_ids)

    columns = max(1, int(total ** 0.5))
    rows = (total + columns - 1) // columns

    coordinates = {}

    for index, zone_id in enumerate(zone_ids):
        column = index % columns
        row = index // columns

        x = (column + 1) * 1000 / (columns + 1)
        y = (row + 1) * 1000 / (rows + 1)

        coordinates[zone_id] = (round(x, 2), round(y, 2))

    return coordinates


def simulate_next_location(group_id, user_id):
    """
    Move one sharing-enabled simulated user to the next stadium zone.
    """

    zone_ids = list(STADIUM_ZONES.keys())

    if not zone_ids:
        raise ValueError("No stadium zones are available.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Find the member's current simulated zone
        cursor.execute("""
            SELECT zone_id
            FROM friend_locations
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        current_location = cursor.fetchone()

    finally:
        connection.close()

    if current_location:
        current_zone = current_location["zone_id"]
        current_index = zone_ids.index(current_zone)
        next_index = (current_index + 1) % len(zone_ids)

    else:
        # Give each demo user a reproducible starting zone
        starting_index = sum(ord(char) for char in user_id) % len(zone_ids)
        next_index = starting_index

    next_zone = zone_ids[next_index]

    coordinates = get_zone_coordinates()
    x, y = coordinates[next_zone]

    return update_location(
        group_id=group_id,
        user_id=user_id,
        zone_id=next_zone,
        x=x,
        y=y
    )
