import pytest
from backend.stadium import STADIUM_ZONES, get_stadium_graph
from backend.intelligence.routing import find_dynamic_route, calculate_edge_cost


def create_mock_snapshot(occupancy_map=None):
    """Create a mock snapshot with controllable occupancy values."""
    if occupancy_map is None:
        occupancy_map = {}

    snapshot = {}
    for zone_id, conf in STADIUM_ZONES.items():
        occ = occupancy_map.get(zone_id, 20.0)
        snapshot[zone_id] = {
            "zone_id": zone_id,
            "zone_name": conf["name"],
            "current_count": int(conf["capacity"] * (occ / 100.0)),
            "capacity": conf["capacity"],
            "occupancy": occ,
            "status": "NORMAL" if occ < 70 else "HIGH"
        }
    return snapshot


def test_normal_shortest_path():
    """
    Test routing under low/uniform congestion.
    From GATE_A to CENTRAL_EXIT, normal shortest path is:
    GATE_A -> MAIN_CONCOURSE (80) -> NORTH_STAND (60) -> CENTRAL_EXIT (90) = 230m
    Compared to:
    GATE_A -> MAIN_CONCOURSE (80) -> FOOD_COURT (45) -> RESTROOM_CORRIDOR (35) -> CENTRAL_EXIT (65) = 225m
    """
    snapshot = create_mock_snapshot()
    result = find_dynamic_route("GATE_A", "CENTRAL_EXIT", snapshot)

    assert result["route"][0] == "GATE_A"
    assert result["route"][-1] == "CENTRAL_EXIT"
    assert len(result["route"]) >= 3
    assert result["total_distance"] > 0
    assert "explanation" in result
    assert result["segments"]


def test_same_start_and_destination():
    snapshot = create_mock_snapshot()
    result = find_dynamic_route("NORTH_STAND", "NORTH_STAND", snapshot)

    assert result["route"] == ["NORTH_STAND"]
    assert result["total_distance"] == 0.0
    assert result["total_cost"] == 0.0


def test_congested_route_diversion():
    """
    When NORTH_STAND is heavily congested (e.g. 95%), the router should prefer
    an alternative path (e.g. via FOOD_COURT / RESTROOM_CORRIDOR) to reach CENTRAL_EXIT.
    """
    # Case A: Low congestion on all routes
    snapshot_normal = create_mock_snapshot({
        "NORTH_STAND": 10.0,
        "FOOD_COURT": 95.0,
        "RESTROOM_CORRIDOR": 95.0
    })
    res_normal = find_dynamic_route("GATE_A", "CENTRAL_EXIT", snapshot_normal)
    assert "NORTH_STAND" in res_normal["route"]

    # Case B: NORTH_STAND is congested (98%), alternative path is clear (5%)
    snapshot_congested = create_mock_snapshot({
        "NORTH_STAND": 98.0,
        "FOOD_COURT": 5.0,
        "RESTROOM_CORRIDOR": 5.0
    })
    res_diverted = find_dynamic_route("GATE_A", "CENTRAL_EXIT", snapshot_congested)
    assert "NORTH_STAND" not in res_diverted["route"]
    assert "FOOD_COURT" in res_diverted["route"]
    assert "RESTROOM_CORRIDOR" in res_diverted["route"]


def test_closed_connection_avoidance():
    """
    Test that closed connections are strictly avoided.
    If MAIN_CONCOURSE <-> NORTH_STAND is closed, path must not use it.
    """
    snapshot = create_mock_snapshot()

    closed = [("MAIN_CONCOURSE", "NORTH_STAND")]
    result = find_dynamic_route("GATE_A", "NORTH_STAND", snapshot, closed_connections=closed)

    # Path must still reach NORTH_STAND via remaining open paths:
    # e.g., GATE_A -> MAIN_CONCOURSE -> FOOD_COURT -> RESTROOM_CORRIDOR -> CENTRAL_EXIT -> NORTH_STAND
    assert result["route"][0] == "GATE_A"
    assert result["route"][-1] == "NORTH_STAND"
    # Ensure the closed link is not used in either direction
    for i in range(len(result["route"]) - 1):
        edge = (result["route"][i], result["route"][i + 1])
        assert edge != ("MAIN_CONCOURSE", "NORTH_STAND")
        assert edge != ("NORTH_STAND", "MAIN_CONCOURSE")


def test_unreachable_due_to_closed_connections():
    """If all connections to destination are closed, raises ValueError."""
    snapshot = create_mock_snapshot()

    # CENTRAL_EXIT is connected to NORTH_STAND and RESTROOM_CORRIDOR
    closed = [
        ("NORTH_STAND", "CENTRAL_EXIT"),
        ("RESTROOM_CORRIDOR", "CENTRAL_EXIT")
    ]
    with pytest.raises(ValueError, match="No available path found"):
        find_dynamic_route("GATE_A", "CENTRAL_EXIT", snapshot, closed_connections=closed)


def test_invalid_zone_names():
    snapshot = create_mock_snapshot()
    with pytest.raises(ValueError, match="Invalid start zone"):
        find_dynamic_route("INVALID_ZONE", "NORTH_STAND", snapshot)

    with pytest.raises(ValueError, match="Invalid destination zone"):
        find_dynamic_route("GATE_A", "NON_EXISTENT", snapshot)
