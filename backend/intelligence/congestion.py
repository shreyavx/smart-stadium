
class CongestionDetector:

    def __init__(self):
        self.previous_occupancy = {}

    def analyze(self, snapshot):
        results = {}

        for zone_id, zone in snapshot.items():
            occupancy = zone["occupancy"]

            # Calculate occupancy change since the previous update.
            previous = self.previous_occupancy.get(
                zone_id, occupancy
            )

            occupancy_change = round(
                occupancy - previous, 2
            )

            # Classify congestion.
            if occupancy >= 85:
                status = "CRITICAL"
            elif occupancy >= 70:
                status = "HIGH"
            elif occupancy >= 50:
                status = "MODERATE"
            else:
                status = "NORMAL"

            # Detect rapidly increasing occupancy.
            if occupancy_change >= 3:
                trend = "RISING_FAST"
            elif occupancy_change > 0:
                trend = "RISING"
            elif occupancy_change < 0:
                trend = "FALLING"
            else:
                trend = "STABLE"

            results[zone_id] = {
                "zone_id": zone_id,
                "zone_name": zone["zone_name"],
                "occupancy": occupancy,
                "status": status,
                "occupancy_change": occupancy_change,
                "trend": trend
            }

            self.previous_occupancy[zone_id] = occupancy

        return results
