
from backend.intelligence.alerts import AlertGenerator


def test_critical_congestion_alert():
    generator = AlertGenerator()

    congestion = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 90,
            "status": "CRITICAL"
        }
    }

    forecasts = {
        "GATE_A": {
            "predicted_occupancy": 95
        }
    }

    alerts = generator.generate(congestion, forecasts)

    assert len(alerts) == 1
    assert alerts[0]["severity"] == "CRITICAL"
    assert alerts[0]["zone_id"] == "GATE_A"


def test_forecast_warning():
    generator = AlertGenerator()

    congestion = {
        "FOOD_COURT": {
            "zone_name": "Food Court",
            "occupancy": 60,
            "status": "MODERATE"
        }
    }

    forecasts = {
        "FOOD_COURT": {
            "predicted_occupancy": 88
        }
    }

    alerts = generator.generate(congestion, forecasts)

    assert len(alerts) == 1
    assert alerts[0]["severity"] == "WARNING"


def test_no_alert_for_normal_zone():
    generator = AlertGenerator()

    congestion = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 30,
            "status": "NORMAL"
        }
    }

    forecasts = {
        "GATE_A": {
            "predicted_occupancy": 40
        }
    }

    alerts = generator.generate(congestion, forecasts)

    assert alerts == []


def test_duplicate_alert_suppression():
    generator = AlertGenerator()

    congestion = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 90,
            "status": "CRITICAL"
        }
    }

    forecasts = {
        "GATE_A": {
            "predicted_occupancy": 95
        }
    }

    first = generator.generate(congestion, forecasts)
    second = generator.generate(congestion, forecasts)

    assert len(first) == 1
    assert len(second) == 0

def test_alert_does_not_repeat_for_same_condition():
    generator = AlertGenerator()

    congestion = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 90,
            "status": "CRITICAL"
        }
    }

    forecasts = {
        "GATE_A": {
            "predicted_occupancy": 100
        }
    }

    first = generator.generate(congestion, forecasts)

    # Occupancy changes, but the condition remains critical.
    congestion["GATE_A"]["occupancy"] = 95

    second = generator.generate(congestion, forecasts)

    assert len(first) == 1
    assert len(second) == 0


def test_alert_triggers_on_escalation():
    generator = AlertGenerator()

    congestion = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 60,
            "status": "MODERATE"
        }
    }

    forecasts = {
        "GATE_A": {
            "predicted_occupancy": 88
        }
    }

    first = generator.generate(congestion, forecasts)

    congestion["GATE_A"]["occupancy"] = 90
    congestion["GATE_A"]["status"] = "CRITICAL"

    second = generator.generate(congestion, forecasts)

    assert len(first) == 1
    assert len(second) == 1
    assert second[0]["condition"] == "CURRENT_CRITICAL"
