
import random
from datetime import datetime, timezone

from backend.stadium import STADIUM_ZONES, CONNECTIONS


class CrowdSimulator:

    def __init__(self):
        self.zones = {
            zone_id: {
                **config,
                "inflow": 0,
                "outflow": 0
            }
            for zone_id, config in STADIUM_ZONES.items()
        }

        self.surge_zone = None
        self.surge_rate = 0

        self.evacuation_mode = False
        self.evacuation_destination = None

        self.last_inflow = {
            zone_id: 0 for zone_id in self.zones
        }

        self.last_outflow = {
            zone_id: 0 for zone_id in self.zones
        }

    def trigger_surge(self, zone_id, people_per_tick=30):
        if zone_id not in self.zones:
            raise ValueError("Invalid stadium zone")

        if people_per_tick <= 0:
            raise ValueError("Surge rate must be positive")

        self.surge_zone = zone_id
        self.surge_rate = people_per_tick

    def stop_surge(self):
        self.surge_zone = None
        self.surge_rate = 0

    def start_evacuation(self, destination="CENTRAL_EXIT"):
        if destination not in self.zones:
            raise ValueError(f"Invalid evacuation destination: {destination}")
        self.evacuation_mode = True
        self.evacuation_destination = destination
        self.surge_zone = None
        self.surge_rate = 0

    def stop_evacuation(self):
        self.evacuation_mode = False
        self.evacuation_destination = None

    def step(self):
        """
        Advance simulation by one tick.
        Each tick represents approximately 2 seconds.

        Internal movement is bidirectional.
        External arrivals occur at entrance gates.
        External departures occur at the central exit.
        """

        incoming = {zone: 0 for zone in self.zones}
        outgoing = {zone: 0 for zone in self.zones}

        # 1. Calculate external departures.
        departures = {
            zone: 0 for zone in self.zones
        }

        if self.evacuation_mode:
            # During evacuation, designated exit(s) process heavy outbound flow
            exit_target = self.evacuation_destination or "CENTRAL_EXIT"
            departures[exit_target] = random.randint(40, 75)
        else:
            departures["CENTRAL_EXIT"] = random.randint(0, 4)

        # 2. Generate proposed movement in both directions.
        proposals = []

        for source, destination, distance in CONNECTIONS:

            source_zone = self.zones[source]
            destination_zone = self.zones[destination]

            source_count = source_zone["current_count"]
            destination_count = destination_zone["current_count"]

            source_occupancy = (
                source_count / source_zone["capacity"]
            )

            destination_occupancy = (
                destination_count / destination_zone["capacity"]
            )

            # People preferentially move from more crowded
            # zones toward less crowded connected zones.
            if source_occupancy > destination_occupancy:
                from_zone = source
                to_zone = destination

            elif destination_occupancy > source_occupancy:
                from_zone = destination
                to_zone = source

            else:
                continue

            available = (
                self.zones[from_zone]["current_count"]
                - departures[from_zone]
            )

            if available <= 0:
                continue

            movement = random.randint(
                0,
                min(8, available)
            )

            if movement > 0:
                proposals.append(
                    (from_zone, to_zone, movement)
                )

        # 3. Ensure a zone never sends more people than it has.
        remaining = {
            zone: (
                self.zones[zone]["current_count"]
                - departures[zone]
            )
            for zone in self.zones
        }

        limited_proposals = []

        for source, destination, movement in proposals:

            actual_movement = min(
                movement,
                remaining[source]
            )

            if actual_movement > 0:
                limited_proposals.append(
                    (source, destination, actual_movement)
                )

                remaining[source] -= actual_movement

        # 4. Respect destination capacity.
        # We conservatively calculate free space before
        # crediting outgoing movement.
        free_space = {
            zone: (
                self.zones[zone]["capacity"]
                - self.zones[zone]["current_count"]
                + departures[zone]
            )
            for zone in self.zones
        }

        for source, destination, movement in limited_proposals:

            accepted = min(
                movement,
                max(0, free_space[destination])
            )

            if accepted > 0:
                outgoing[source] += accepted
                incoming[destination] += accepted

                free_space[destination] -= accepted

        # 5. Add external arrivals only at entrance gates.
        arrivals = {
            zone: 0 for zone in self.zones
        }

        if not self.evacuation_mode:
            arrivals["GATE_A"] = random.randint(0, 5)
            arrivals["GATE_B"] = random.randint(0, 5)

        # A surge represents an additional crowd arrival.
        if self.surge_zone is not None:
            arrivals[self.surge_zone] += self.surge_rate

        # 6. Apply all accepted movements and external flows.
        for zone_id, zone in self.zones.items():

            old_count = zone["current_count"]

            new_count = (
                old_count
                - outgoing[zone_id]
                - departures[zone_id]
                + incoming[zone_id]
            )

            # Only accept arrivals that fit within capacity.
            accepted_arrivals = min(
                arrivals[zone_id],
                max(0, zone["capacity"] - new_count)
            )

            new_count += accepted_arrivals

            zone["current_count"] = new_count

            self.last_inflow[zone_id] = (
                incoming[zone_id] + accepted_arrivals
            )

            self.last_outflow[zone_id] = (
                outgoing[zone_id] + departures[zone_id]
            )

        return self.get_snapshot()

    def get_snapshot(self):

        result = {}

        for zone_id, zone in self.zones.items():

            occupancy = (
                zone["current_count"] / zone["capacity"]
            ) * 100

            if occupancy >= 85:
                status = "CRITICAL"
            elif occupancy >= 70:
                status = "HIGH"
            elif occupancy >= 50:
                status = "MODERATE"
            else:
                status = "NORMAL"

            result[zone_id] = {
                "zone_id": zone_id,
                "zone_name": zone["name"],
                "type": zone["type"],
                "current_count": zone["current_count"],
                "capacity": zone["capacity"],
                "inflow": self.last_inflow[zone_id],
                "outflow": self.last_outflow[zone_id],
                "occupancy": round(occupancy, 2),
                "status": status,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat()
            }

        return result
