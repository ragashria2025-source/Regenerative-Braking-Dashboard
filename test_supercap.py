
from parameters import PARAMETERS
from supercap_model import (
    cap_energy,
    cap_voltage,
    usable_window_J,
    max_charge_power,
    max_discharge_power,
)
from configuration_c import simulate_config_c
from simulate_stopping import simulate_stopping


def p(name):
    return PARAMETERS[name]["value"]


def main():
    # Test 1: usable window equals only the energy above half voltage.
    expected = 0.5 * p("C_sc") * (p("V_sc_max") ** 2 - p("V_sc_min") ** 2)
    assert abs(usable_window_J() - expected) < 1e-6
    assert abs(cap_voltage(cap_energy(300.0)) - 300.0) < 1e-9
    print(f"TEST 1: usable window = {usable_window_J() / 1e3:.1f} kJ  PASSED")

    # Test 2: power limits respect the energy budget exactly.
    V, R, dt = 300.0, p("R_sc"), 0.1
    avail = 2000.0  # 20 kW over 0.1 s, below the converter rating
    pd = max_discharge_power(avail, dt, V)
    drawn = (pd + (pd / V) ** 2 * R) * dt
    assert pd < p("P_sc_max") and abs(drawn - avail) < 1e-6
    pc = max_charge_power(avail, dt, V)
    stored = (pc - (pc / V) ** 2 * R) * dt
    assert pc < p("P_sc_max") and abs(stored - avail) < 1e-6
    print("TEST 2: power limits use exactly the available energy  PASSED")

    # Test 3: configuration C balances (recovery and capacitor state).
    for soc, temp in ((0.20, 25.0), (0.90, 25.0), (0.95, 10.0)):
        r = simulate_config_c(initial_soc=soc, temperature_c=temp)
        tol = r["recovery_tolerance_J"]
        assert abs(r["recovery_residual_J"]) < tol, (soc, temp, r["recovery_residual_J"])
        assert abs(r["cap_residual_J"]) < tol, (soc, temp, r["cap_residual_J"])
    print("TEST 3: energy and capacitor balances close  PASSED")

    # Test 4: the capacitor never leaves its usable voltage window.
    E_min = cap_energy(p("V_sc_min"))
    E_max = cap_energy(p("V_sc_max"))
    r = simulate_config_c(initial_soc=0.90, temperature_c=25.0)
    assert -1e-6 <= r["energy_left_in_cap_J"] <= E_max - E_min + 1e-6
    print("TEST 4: capacitor stays inside its voltage window  PASSED")

    # Test 5: cold battery stores nothing in the battery; energy stays in the capacitor.
    cold = simulate_config_c(initial_soc=0.20, temperature_c=-5.0)
    assert cold["battery_stored_J"] == 0.0
    assert cold["energy_left_in_cap_J"] > 0.9 * (E_max - E_min)
    print("TEST 5: cold battery leaves energy in capacitor, not in battery  PASSED")

    # Test 6: configuration C never stores less than B in the battery.
    for soc, temp in ((0.20, 25.0), (0.50, 10.0), (0.90, 25.0)):
        c = simulate_config_c(initial_soc=soc, temperature_c=temp)["battery_stored_J"]
        b = simulate_stopping(initial_soc=soc, temperature_c=temp)["battery_stored_energy_J"]
        assert c >= b - 1e-6, (soc, temp, c, b)
    print("TEST 6: C battery energy >= B battery energy in tested cases  PASSED")

    print("\nALL SUPERCAPACITOR TESTS PASSED.")


if __name__ == "__main__":
    main()
