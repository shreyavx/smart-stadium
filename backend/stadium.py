
# backend/stadium.py

STADIUM_ZONES = {
    "GATE_A": {
        "name": "Gate A",
        "type": "entrance",
        "capacity": 1000,
        "current_count": 450,
        "inflow": 15,
        "outflow": 8
    },
    "GATE_B": {
        "name": "Gate B",
        "type": "entrance",
        "capacity": 1000,
        "current_count": 300,
        "inflow": 10,
        "outflow": 6
    },
    "MAIN_CONCOURSE": {
        "name": "Main Concourse",
        "type": "corridor",
        "capacity": 3000,
        "current_count": 1100,
        "inflow": 20,
        "outflow": 18
    },
    "NORTH_STAND": {
        "name": "North Stand",
        "type": "seating",
        "capacity": 5000,
        "current_count": 2500,
        "inflow": 12,
        "outflow": 10
    },
    "SOUTH_STAND": {
        "name": "South Stand",
        "type": "seating",
        "capacity": 5000,
        "current_count": 2200,
        "inflow": 10,
        "outflow": 8
    },
    "FOOD_COURT": {
        "name": "Food Court",
        "type": "facility",
        "capacity": 1200,
        "current_count": 500,
        "inflow": 18,
        "outflow": 12
    },
    "RESTROOM_CORRIDOR": {
        "name": "Restroom Corridor",
        "type": "corridor",
        "capacity": 800,
        "current_count": 250,
        "inflow": 8,
        "outflow": 6
    },
    "CENTRAL_EXIT": {
        "name": "Central Exit",
        "type": "exit",
        "capacity": 1500,
        "current_count": 150,
        "inflow": 5,
        "outflow": 20
    }
}


# Bidirectional connections.
# Distance is the estimated walking distance in metres.

CONNECTIONS = [
    ("GATE_A", "MAIN_CONCOURSE", 80),
    ("GATE_B", "MAIN_CONCOURSE", 100),
    ("MAIN_CONCOURSE", "NORTH_STAND", 60),
    ("MAIN_CONCOURSE", "SOUTH_STAND", 70),
    ("MAIN_CONCOURSE", "FOOD_COURT", 45),
    ("NORTH_STAND", "CENTRAL_EXIT", 90),
    ("SOUTH_STAND", "RESTROOM_CORRIDOR", 40),
    ("FOOD_COURT", "RESTROOM_CORRIDOR", 35),
    ("RESTROOM_CORRIDOR", "CENTRAL_EXIT", 65)
]


def get_stadium_graph():
    """Build an undirected graph of stadium connections."""

    graph = {zone_id: [] for zone_id in STADIUM_ZONES}

    for source, destination, distance in CONNECTIONS:
        graph[source].append({
            "destination": destination,
            "distance": distance,
            "closed": False
        })

        graph[destination].append({
            "destination": source,
            "distance": distance,
            "closed": False
        })

    return graph
