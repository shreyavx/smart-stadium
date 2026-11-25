
from backend.intelligence.congestion import CongestionDetector


def test_congestion_status():
    detector = CongestionDetector()

    snapshot = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 90
        },
        "GATE_B": {
            "zone_name": "Gate B",
            "occupancy": 75
        },
        "FOOD_COURT": {
            "zone_name": "Food Court",
            "occupancy": 40
        }
    }

    results = detector.analyze(snapshot)

    assert results["GATE_A"]["status"] == "CRITICAL"
    assert results["GATE_B"]["status"] == "HIGH"
    assert results["FOOD_COURT"]["status"] == "NORMAL"


def test_occupancy_trend():
    detector = CongestionDetector()

    first_snapshot = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 60
        }
    }

    second_snapshot = {
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 65
        }
    }

    detector.analyze(first_snapshot)
    results = detector.analyze(second_snapshot)

    assert results["GATE_A"]["occupancy_change"] == 5
    assert results["GATE_A"]["trend"] == "RISING_FAST"


def test_falling_occupancy():
    detector = CongestionDetector()

    detector.analyze({
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 70
        }
    })

    results = detector.analyze({
        "GATE_A": {
            "zone_name": "Gate A",
            "occupancy": 60
        }
    })

    assert results["GATE_A"]["trend"] == "FALLING"
