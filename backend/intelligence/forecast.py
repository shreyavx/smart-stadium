
from collections import defaultdict, deque


class CrowdForecaster:

    def __init__(
        self,
        forecast_minutes=5,
        tick_seconds=2,
        history_size=30
    ):
        self.forecast_ticks = (
            forecast_minutes * 60
        ) // tick_seconds

        self.history = defaultdict(
            lambda: deque(maxlen=history_size)
        )

        self.minimum_readings = 5

    def forecast(self, snapshot):
        results = {}

        for zone_id, zone in snapshot.items():
            current = float(zone["occupancy"])

            readings = self.history[zone_id]
            readings.append(current)

            predicted = current
            trend = "INSUFFICIENT_DATA"

            if len(readings) >= self.minimum_readings:
                values = list(readings)
                n = len(values)

                # Calculate the least-squares trend.
                x_mean = (n - 1) / 2
                y_mean = sum(values) / n

                numerator = sum(
                    (i - x_mean) * (value - y_mean)
                    for i, value in enumerate(values)
                )

                denominator = sum(
                    (i - x_mean) ** 2
                    for i in range(n)
                )

                slope = (
                    numerator / denominator
                    if denominator else 0
                )

                predicted = current + (
                    slope * self.forecast_ticks
                )

                predicted = max(
                    0,
                    min(100, predicted)
                )

                change = predicted - current

                if change >= 5:
                    trend = "RISING"
                elif change <= -5:
                    trend = "FALLING"
                else:
                    trend = "STABLE"

            results[zone_id] = {
                "zone_id": zone_id,
                "zone_name": zone["zone_name"],
                "current_occupancy": round(current, 2),
                "predicted_occupancy": round(predicted, 2),
                "predicted_change": round(
                    predicted - current, 2
                ),
                "forecast_minutes": 5,
                "trend": trend
            }

        return results
