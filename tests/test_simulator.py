
from backend.simulator.engine import CrowdSimulator


def test_simulator_initializes():
    simulator = CrowdSimulator()

    assert len(simulator.zones) == 8


def test_simulation_updates_counts():
    simulator = CrowdSimulator()

    before = simulator.get_snapshot()
    after = simulator.step()

    assert len(after) == 8

    for zone_id in after:
        assert 0 <= after[zone_id]["current_count"] <= (
            after[zone_id]["capacity"]
        )


def test_surge_increases_target_zone():
    simulator = CrowdSimulator()

    simulator.zones["GATE_A"]["current_count"] = 500
    simulator.trigger_surge("GATE_A", 100)

    before = simulator.zones["GATE_A"]["current_count"]

    # Multiple ticks make the surge measurable despite random movement.
    for _ in range(10):
        simulator.step()

    after = simulator.zones["GATE_A"]["current_count"]

    assert after > before


def test_invalid_surge_zone():
    simulator = CrowdSimulator()

    try:
        simulator.trigger_surge("INVALID_ZONE")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_stop_surge():
    simulator = CrowdSimulator()

    simulator.trigger_surge("GATE_A", 50)
    simulator.stop_surge()

    assert simulator.surge_zone is None
    assert simulator.surge_rate == 0
