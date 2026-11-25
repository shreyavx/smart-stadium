
from backend.intelligence.forecast import CrowdForecaster


def make_snapshot(occupancy):
    return {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": occupancy
        }
    }


def test_forecast_waits_for_enough_readings():
    forecaster = CrowdForecaster()

    result = forecaster.forecast(
        make_snapshot(60)
    )

    assert (
        result["GATE_A"]["trend"]
        == "INSUFFICIENT_DATA"
    )


def test_forecast_detects_rising_crowd():
    forecaster = CrowdForecaster()

    result = None

    for i in range(10):
        result = forecaster.forecast(
            make_snapshot(50 + i * 0.1)
        )

    assert result["GATE_A"]["trend"] == "RISING"
    assert (
        result["GATE_A"]["predicted_occupancy"]
        > result["GATE_A"]["current_occupancy"]
    )


def test_forecast_stays_within_capacity_percentage():
    forecaster = CrowdForecaster()

    result = None

    for i in range(10):
        result = forecaster.forecast(
            make_snapshot(99 + i * 0.1)
        )

    assert (
        result["GATE_A"]["predicted_occupancy"]
        <= 100
    )
