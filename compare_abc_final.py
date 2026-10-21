"""
Step 6: A, B and C on the SAME fine-grid drive cycle, with the SAME starting
SOC (0.20) and temperature (25 C). Battery-accepted energy is the only energy
number compared across configurations.
"""

from fine_cycle_runs import run_a, run_b, run_c


def main():
    a, b, c = run_a(), run_b(), run_c()

    print("STEP 6: A / B / C ON THE SAME DRIVE CYCLE")
    print("Cycle: 0-40-0 km/h test cycle, dt = 0.01 s | SOC 0.20 | 25 C")
    print("=" * 74)
    print(f"{'':34s}{'A':>12s}{'B':>12s}{'C':>12s}")
    print(f"{'Battery accepted, stop only (kJ)':34s}"
          f"{a['stop_only_battery_J']/1e3:12.3f}{b['stop_only_battery_J']/1e3:12.3f}"
          f"{c['stop_only_battery_J']/1e3:12.3f}")
    print(f"{'Battery accepted, incl. transfer (kJ)':34s}"
          f"{a['total_battery_J']/1e3:12.3f}{b['total_battery_J']/1e3:12.3f}"
          f"{c['total_battery_J']/1e3:12.3f}")
    print(f"{'Friction braking (kJ)':34s}"
          f"{a['friction_J']/1e3:12.3f}{b['friction_J']/1e3:12.3f}{c['friction_J']/1e3:12.3f}")
    print(f"{'Rejected by battery, wasted (kJ)':34s}"
          f"{a['wasted_J']/1e3:12.3f}{b['wasted_J']/1e3:12.3f}{'-':>12s}")
    print(f"{'Left in capacitor at end (kJ)':34s}"
          f"{'-':>12s}{'-':>12s}{c['cap_left_J']/1e3:12.3f}")
    print("-" * 74)
    print(f"C minus B, battery total: {(c['total_battery_J'] - b['total_battery_J'])/1e3:+.3f} kJ")
    print(f"A minus B, battery total: {(a['total_battery_J'] - b['total_battery_J'])/1e3:+.3f} kJ")
    print(f"C capacitor balance residual: {c['cap_residual_J']:.3f} J")
    print("=" * 74)
    print("Reading: on this cycle the battery accepts almost all regen, so A, B and C")
    print("store nearly the same energy. C's gain is only the capacitor transfer. Results")
    print("here are for the test cycle only, not for a real driving cycle.")


if __name__ == "__main__":
    main()
