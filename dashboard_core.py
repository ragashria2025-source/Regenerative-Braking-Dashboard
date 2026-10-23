"""
Dashboard core: runs configurations A, B and C for a set of user-chosen
parameters, then restores every global it changed.
"""

import drive_cycle
import fine_cycle_runs as fcr
from parameters import PARAMETERS
from fine_cycle_runs import run_a, run_b, run_c

CYCLES = {"Test cycle 0-40-0 km/h (toy)": "toy", "EPA UDDS": "UDDS"}


def run_scenario(cycle="toy", initial_soc=0.20, temperature_c=25.0,
                 cap_kw=50.0, i_max=150.0, r0_25=0.10, eta_gen=0.90, c_sc=5.0):
    """Return battery energy (kJ) and related figures for A, B and C."""
    overrides = {"i_max": i_max, "R0_25": r0_25, "eta_gen": eta_gen, "C_sc": c_sc}
    saved_params = {k: PARAMETERS[k]["value"] for k in overrides}
    saved_cycle = drive_cycle.DRIVE_CYCLE
    saved_cap = fcr.REGEN_POWER_CAP_W
    try:
        for k, v in overrides.items():
            PARAMETERS[k]["value"] = v
        drive_cycle.DRIVE_CYCLE = cycle
        fcr.REGEN_POWER_CAP_W = cap_kw * 1000.0

        a = run_a(initial_soc=initial_soc, temperature_c=temperature_c)
        b = run_b(initial_soc=initial_soc, temperature_c=temperature_c)
        c = run_c(initial_soc=initial_soc, temperature_c=temperature_c)
    finally:
        for k, v in saved_params.items():
            PARAMETERS[k]["value"] = v
        drive_cycle.DRIVE_CYCLE = saved_cycle
        fcr.REGEN_POWER_CAP_W = saved_cap

    kj = lambda x: x / 1e3
    return {
        "battery_kJ": {"A": kj(a["total_battery_J"]), "B": kj(b["total_battery_J"]),
                       "C": kj(c["total_battery_J"])},
        "friction_kJ": {"A": kj(a["friction_J"]), "B": kj(b["friction_J"]),
                        "C": kj(c["friction_J"])},
        "wasted_kJ": {"A": kj(a["wasted_J"]), "B": 0.0},
        "C_transfer_kJ": kj(c["transfer_J"]),
        "C_left_kJ": kj(c["cap_left_J"]),
        "C_minus_B_kJ": kj(c["total_battery_J"] - b["total_battery_J"]),
        "B_minus_A_kJ": kj(b["total_battery_J"] - a["total_battery_J"]),
    }


if __name__ == "__main__":
    print(run_scenario())