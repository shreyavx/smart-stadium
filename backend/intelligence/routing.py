import heapq
from typing import Dict, List, Optional, Tuple, Any

from backend.stadium import get_stadium_graph, STADIUM_ZONES


def calculate_edge_cost(
    distance: float,
    target_occupancy: float,
    congestion_weight: float = 1.5
) -> float:
    """
    Calculate dynamic edge traversal cost.
    Base cost is physical distance in meters.
    As target zone occupancy rises, cost increases proportionally:
    effective_cost = distance * (1 + congestion_weight * (occupancy / 100))
    """
    occupancy_factor = max(0.0, float(target_occupancy)) / 100.0
    return distance * (1.0 + congestion_weight * occupancy_factor)


def find_dynamic_route(
    start_zone: str,
    destination_zone: str,
    snapshot_data: Dict[str, Any],
    closed_connections: Optional[List[Tuple[str, str]]] = None,
    graph: Optional[Dict[str, List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """
    Find the optimal route between start_zone and destination_zone using
    Dijkstra's algorithm, taking live crowd occupancy and closed edges into account.
    """
    if start_zone not in STADIUM_ZONES:
        raise ValueError(f"Invalid start zone: '{start_zone}'")

    if destination_zone not in STADIUM_ZONES:
        raise ValueError(f"Invalid destination zone: '{destination_zone}'")

    if start_zone == destination_zone:
        start_info = snapshot_data.get(start_zone, {})
        return {
            "route": [start_zone],
            "total_distance": 0.0,
            "total_cost": 0.0,
            "explanation": f"Already at destination '{start_zone}'.",
            "segments": []
        }

    # Normalize closed connections set (bidirectional)
    closed_set = set()
    if closed_connections:
        for u, v in closed_connections:
            closed_set.add((u, v))
            closed_set.add((v, u))

    if graph is None:
        graph = get_stadium_graph()

    # Priority queue stores tuples: (current_cost, current_zone)
    priority_queue: List[Tuple[float, str]] = []
    heapq.heappush(priority_queue, (0.0, start_zone))

    best_costs: Dict[str, float] = {start_zone: 0.0}
    previous_nodes: Dict[str, Optional[str]] = {start_zone: None}
    edge_distances: Dict[str, float] = {start_zone: 0.0}

    while priority_queue:
        current_cost, current_node = heapq.heappop(priority_queue)

        if current_node == destination_zone:
            break

        if current_cost > best_costs.get(current_node, float("inf")):
            continue

        for neighbor in graph.get(current_node, []):
            dest = neighbor["destination"]
            base_dist = float(neighbor.get("distance", 1.0))
            is_closed = neighbor.get("closed", False) or (current_node, dest) in closed_set

            if is_closed:
                continue

            target_zone_info = snapshot_data.get(dest, {})
            target_occupancy = float(target_zone_info.get("occupancy", 0.0))

            edge_cost = calculate_edge_cost(base_dist, target_occupancy)
            total_neighbor_cost = current_cost + edge_cost

            if total_neighbor_cost < best_costs.get(dest, float("inf")):
                best_costs[dest] = total_neighbor_cost
                previous_nodes[dest] = current_node
                edge_distances[dest] = base_dist
                heapq.heappush(priority_queue, (total_neighbor_cost, dest))

    if destination_zone not in previous_nodes:
        raise ValueError(f"No available path found from '{start_zone}' to '{destination_zone}'.")

    # Reconstruct shortest path
    route: List[str] = []
    curr: Optional[str] = destination_zone
    while curr is not None:
        route.append(curr)
        curr = previous_nodes[curr]
    route.reverse()

    # Calculate total physical distance and breakdown segment details
    total_physical_distance = 0.0
    segments = []
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        dist = edge_distances[v]
        total_physical_distance += dist
        v_info = snapshot_data.get(v, {})
        v_occ = float(v_info.get("occupancy", 0.0))
        segments.append({
            "from": u,
            "to": v,
            "distance": round(dist, 1),
            "destination_occupancy": round(v_occ, 1)
        })

    explanation = (
        f"Route from {start_zone} to {destination_zone} via {' -> '.join(route)}. "
        f"Total walking distance: {round(total_physical_distance, 1)}m."
    )

    return {
        "route": route,
        "total_distance": round(total_physical_distance, 1),
        "total_cost": round(best_costs[destination_zone], 2),
        "explanation": explanation,
        "segments": segments
    }
