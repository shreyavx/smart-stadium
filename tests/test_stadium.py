
from backend.stadium import (
    STADIUM_ZONES,
    CONNECTIONS,
    get_stadium_graph
)


def test_all_zones_have_capacity():
    for zone in STADIUM_ZONES.values():
        assert zone["capacity"] > 0


def test_all_connections_reference_valid_zones():
    for source, destination, distance in CONNECTIONS:
        assert source in STADIUM_ZONES
        assert destination in STADIUM_ZONES
        assert distance > 0


def test_graph_is_bidirectional():
    graph = get_stadium_graph()

    for zone, neighbors in graph.items():
        for neighbor in neighbors:
            destination = neighbor["destination"]

            reverse = [
                edge for edge in graph[destination]
                if edge["destination"] == zone
            ]

            assert len(reverse) > 0


def test_all_zones_are_reachable():
    graph = get_stadium_graph()

    visited = set()
    stack = ["GATE_A"]

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        for edge in graph[current]:
            if not edge["closed"]:
                stack.append(edge["destination"])

    assert visited == set(STADIUM_ZONES.keys())
