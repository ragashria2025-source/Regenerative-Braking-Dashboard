import matplotlib.pyplot as plt

from drive_cycle_battery import simulate_drive_cycle


def main():

    # Run battery-aware simulation
    result = simulate_drive_cycle(
        initial_soc=0.20,
        temperature_c=25.0
    )

    records = result[0]

    # Extract data
    time = [r["time_s"] for r in records]
    speed = [r["speed_mps"] * 3.6 for r in records]

    braking_force = [r["braking_force_N"] for r in records]
    regen_force = [r["regen_force_N"] for r in records]
    friction_force = [r["friction_force_N"] for r in records]

    regen_power = [r["regen_power_W"] / 1000 for r in records]
    battery_power = [r["battery_power_W"] / 1000 for r in records]

    soc = [r["soc"] * 100 for r in records]

    # ---------------------------------------------------------
    # 1. SPEED
    # ---------------------------------------------------------

    plt.figure()
    plt.plot(time, speed)

    plt.xlabel("Time (s)")
    plt.ylabel("Speed (km/h)")
    plt.title("Vehicle Speed vs Time")

    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # 2. BRAKING FORCE
    # ---------------------------------------------------------

    plt.figure()

    plt.plot(
        time,
        braking_force,
        label="Total Braking Force"
    )

    plt.plot(
        time,
        regen_force,
        label="Regenerative Force"
    )

    plt.plot(
        time,
        friction_force,
        label="Friction Force"
    )

    plt.xlabel("Time (s)")
    plt.ylabel("Force (N)")
    plt.title("Braking Force Distribution")

    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # 3. REGENERATIVE POWER
    # ---------------------------------------------------------

    plt.figure()

    plt.plot(
        time,
        regen_power,
        label="Regenerative Power"
    )

    plt.plot(
        time,
        battery_power,
        label="Battery Accepted Power"
    )

    plt.xlabel("Time (s)")
    plt.ylabel("Power (kW)")
    plt.title("Regenerative and Battery Power")

    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # 4. BATTERY SOC
    # ---------------------------------------------------------

    plt.figure()

    plt.plot(time, soc)

    plt.xlabel("Time (s)")
    plt.ylabel("SOC (%)")
    plt.title("Battery State of Charge")

    plt.grid(True)

    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("DRIVE CYCLE RESULTS")
    print("=" * 60)

    print(f"Initial SOC                : {soc[0]:.4f}%")
    print(f"Final SOC                  : {soc[-1]:.4f}%")
    print(f"SOC increase               : {soc[-1] - soc[0]:.4f}%")

    print(
        f"Total regenerative energy : "
        f"{result[2] / 1000:.3f} kJ"
    )

    print(
        f"Battery accepted energy   : "
        f"{result[3] / 1000:.3f} kJ"
    )

    print(
        f"Friction braking energy   : "
        f"{result[4] / 1000:.3f} kJ"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
