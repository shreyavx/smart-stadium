
class AlertGenerator:

    def __init__(self):
        self.active_alerts = {}

    def generate(self, congestion, forecasts):
        alerts = []
        current_alerts = {}

        priority = {
            "FORECAST_HIGH": 1,
            "CURRENT_HIGH": 2,
            "FORECAST_CRITICAL": 3,
            "CURRENT_CRITICAL": 4
        }

        for zone_id, zone in congestion.items():

            forecast = forecasts.get(zone_id, {})
            occupancy = zone["occupancy"]
            predicted = forecast.get(
                "predicted_occupancy",
                occupancy
            )

            # Identify the strongest condition for this zone.
            candidates = []

            if predicted >= 70:
                candidates.append("FORECAST_HIGH")

            if predicted >= 85:
                candidates.append("FORECAST_CRITICAL")

            if zone["status"] == "HIGH":
                candidates.append("CURRENT_HIGH")

            if zone["status"] == "CRITICAL":
                candidates.append("CURRENT_CRITICAL")

            if not candidates:
                continue

            condition = max(
                candidates,
                key=lambda item: priority[item]
            )

            severity = {
                "FORECAST_HIGH": "INFO",
                "FORECAST_CRITICAL": "WARNING",
                "CURRENT_HIGH": "WARNING",
                "CURRENT_CRITICAL": "CRITICAL"
            }[condition]

            reason = {
                "FORECAST_HIGH": (
                    f"Forecast occupancy is {predicted}% "
                    "in 5 minutes"
                ),
                "FORECAST_CRITICAL": (
                    f"Forecast occupancy is {predicted}% "
                    "in 5 minutes"
                ),
                "CURRENT_HIGH": (
                    f"Current occupancy is {occupancy}%"
                ),
                "CURRENT_CRITICAL": (
                    f"Current occupancy is {occupancy}%"
                )
            }[condition]

            if zone_id in ("GATE_A", "GATE_B"):
                action = (
                    "Redirect incoming fans to "
                    "another available entrance."
                )
            elif zone_id == "FOOD_COURT":
                action = (
                    "Deploy additional staff and manage "
                    "incoming foot traffic."
                )
            elif zone_id in ("NORTH_STAND", "SOUTH_STAND"):
                action = (
                    "Monitor access routes and coordinate "
                    "crowd movement."
                )
            else:
                action = (
                    "Monitor the zone and manage nearby "
                    "crowd movement."
                )

            alert = {
                "zone_id": zone_id,
                "zone_name": zone["zone_name"],
                "severity": severity,
                "condition": condition,
                "reason": reason,
                "recommended_action": action
            }

            current_alerts[zone_id] = condition

            # Emit only when a new condition or escalation occurs.
            previous_condition = self.active_alerts.get(zone_id)

            if previous_condition != condition:
                alerts.append(alert)

        # Keep track of currently active alert conditions.
        self.active_alerts = current_alerts

        return alerts
