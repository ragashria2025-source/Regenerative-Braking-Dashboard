from drive_cycle import (
    get_test_cycle,
    calculate_acceleration,
    identify_braking,
    calculate_braking_force
)

from regen_model import regenerative_braking


# Fixed regenerative power limit
REGEN_POWER_CAP_W = 50000.0


def simulate_configuration_a():

    time, speed = get_test_cycle()

    acceleration = calculate_acceleration(
        time,
        speed
    )

    braking_flags = identify_braking(
        acceleration
    )

    braking_force = calculate_braking_force(
        time,
        speed,
        acceleration
    )

    results = []

    total_regen_energy = 0.0
    total_friction_energy = 0.0

    for i in range(len(time)):

        v = speed[i]
        F_brake = braking_force[i]

        regen_force = 0.0
        friction_force = 0.0
        regen_power = 0.0

        if braking_flags[i] and F_brake > 0:

            regen = regenerative_braking(
                v,
                F_brake
            )

            available_power = regen["P_elec_W"]

            # Fixed power cap
            actual_power = min(
                available_power,
                REGEN_POWER_CAP_W
            )

            if available_power > 0:

                power_ratio = (
                    actual_power /
                    available_power
                )

            else:
                power_ratio = 0.0

            regen_force = (
                regen["F_regen_wheel_N"]
                * power_ratio
            )

            friction_force = max(
                F_brake - regen_force,
                0.0
            )

            regen_power = actual_power

        dt = (
            time[i + 1] - time[i]
            if i < len(time) - 1
            else 0.0
        )

        total_regen_energy += (
            regen_power * dt
        )

        total_friction_energy += (
            friction_force * v * dt
        )

        results.append({
            "time": time[i],
            "speed": v,
            "braking_force": F_brake,
            "regen_force": regen_force,
            "friction_force": friction_force,
            "regen_power": regen_power
        })

    return (
        results,
        total_regen_energy,
        total_friction_energy
    )


if __name__ == "__main__":

    (
        results,
        regen_energy,
        friction_energy
    ) = simulate_configuration_a()

    print("\n")
    print("=" * 100)
    print("CONFIGURATION A - FIXED REGENERATIVE POWER CAP")
    print("=" * 100)

    print(
        f"{'Time':>6} "
        f"{'Speed':>8} "
        f"{'Brake':>10} "
        f"{'Regen':>10} "
        f"{'Friction':>10} "
        f"{'Power':>10}"
    )

    print("-" * 100)

    for r in results:

        print(
            f"{r['time']:6.1f} "
            f"{r['speed']:8.3f} "
            f"{r['braking_force']:10.1f} "
            f"{r['regen_force']:10.1f} "
            f"{r['friction_force']:10.1f} "
            f"{r['regen_power']/1000:10.2f}"
        )

    print("-" * 100)

    print(
        f"Total regenerative energy : "
        f"{regen_energy / 1000:.3f} kJ"
    )

    print(
        f"Total friction energy     : "
        f"{friction_energy / 1000:.3f} kJ"
    )

    print(
        f"Fixed power limit         : "
        f"{REGEN_POWER_CAP_W / 1000:.1f} kW"
    )

    print("=" * 100)