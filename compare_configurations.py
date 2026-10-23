from simulate_stopping import simulate_stopping
from baseline_stopping import simulate_baseline
from configuration_c import simulate_config_c


def main():

    print()
    print("=" * 90)
    print("SENSITIVITY ANALYSIS - CONFIGURATIONS A, B AND C")
    print("=" * 90)

    print(
        f"{'SOC':>5} "
        f"{'T(C)':>6} | "
        f"{'A (kJ)':>10} "
        f"{'B (kJ)':>10} "
        f"{'C (kJ)':>10} | "
        f"{'C-B':>10} "
        f"{'Improvement':>12}"
    )

    print("-" * 90)

    for soc in (0.20, 0.50, 0.80, 0.90, 0.95):

        for temp in (-5.0, 10.0, 25.0):

            a = simulate_baseline(
                initial_soc=soc,
                temperature_c=temp
            )["battery_stored_J"] / 1000

            b = simulate_stopping(
                initial_soc=soc,
                temperature_c=temp
            )["battery_stored_energy_J"] / 1000

            c_run = simulate_config_c(
                initial_soc=soc,
                temperature_c=temp
            )

            c = c_run["battery_stored_J"] / 1000

            improvement = c - b

            if b > 0:
                improvement_percent = (
                    improvement / b
                ) * 100
            else:
                improvement_percent = 0.0

            print(
                f"{soc:5.2f} "
                f"{temp:6.1f} | "
                f"{a:10.1f} "
                f"{b:10.1f} "
                f"{c:10.1f} | "
                f"{improvement:10.1f} "
                f"{improvement_percent:11.1f}%"
            )

    print("-" * 90)

    print()
    print("Interpretation:")
    print("A = fixed regenerative braking")
    print("B = battery-aware adaptive braking")
    print("C = adaptive braking + supercapacitor")
    print()
    print("Higher C-B means the supercapacitor provides")
    print("greater additional energy recovery compared with B.")
    print("=" * 90)


if __name__ == "__main__":
    main()