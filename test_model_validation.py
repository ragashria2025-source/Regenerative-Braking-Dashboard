import pytest

from fine_cycle_runs import run_a, run_b, run_c


def test_a_matches_b_when_power_cap_is_inactive():
    a = run_a(initial_soc=0.20, temperature_c=25.0)
    b = run_b(initial_soc=0.20, temperature_c=25.0)

    # For this illustrative cycle, the 50 kW cap is not active.
    # Consistent battery acceptance should make A and B match.
    for key in (
        "total_battery_J",
        "battery_stored_J",
        "electrical_J",
        "friction_J",
    ):
        assert a[key] == pytest.approx(
            b[key], rel=1e-8, abs=1e-6
        )


@pytest.mark.parametrize(
    "soc, temperature",
    [
        (0.20, 25.0),
        (0.90, 25.0),
        (0.20, -5.0),
        (0.50, 10.0),
    ],
)
def test_results_are_nonnegative_and_soc_is_bounded(
    soc, temperature
):
    for simulate in (run_a, run_b, run_c):
        result = simulate(
            initial_soc=soc,
            temperature_c=temperature,
        )

        assert 0.0 <= result["final_soc"] <= 1.0

        for key in (
            "total_battery_J",
            "battery_stored_J",
            "electrical_J",
            "friction_J",
        ):
            assert result[key] >= 0.0


def test_supercapacitor_energy_balance():
    result = run_c(
        initial_soc=0.20,
        temperature_c=25.0,
    )

    assert abs(result["cap_residual_J"]) < 1e-3


def test_battery_terminal_energy_exceeds_stored_energy():
    for simulate in (run_a, run_b, run_c):
        result = simulate(
            initial_soc=0.20,
            temperature_c=25.0,
        )

        assert (
            result["total_battery_J"] + 1e-6
            >= result["battery_stored_J"]
        )
