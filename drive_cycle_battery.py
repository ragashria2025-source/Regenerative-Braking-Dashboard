from drive_cycle import (
    get_test_cycle,
    calculate_acceleration,
    identify_braking,
    calculate_braking_force
)

from regen_model import regenerative_braking
from battery_model import charge_battery


def simulate_drive_cycle(
    initial_soc=0.20,
    temperature_c=25.0,
    dt=1.0
):

    # --------------------------------------------------
    # 1. Get drive cycle
    # --------------------------------------------------
    time, speed = get_test_cycle()

    acceleration = calculate_acceleration(time, speed)
    braking_flags = identify_braking(acceleration)

    # --------------------------------------------------
    # 2. Calculate braking force
    # --------------------------------------------------
    braking_force = calculate_braking_force(
        time,
        speed,
        acceleration
    )

    # --------------------------------------------------
    # 3. Initial battery state
    # --------------------------------------------------
    soc = initial_soc

    results = []

    total_regen_energy = 0.0
    total_battery_energy = 0.0
    total_friction_energy = 0.0

    # --------------------------------------------------
    # 4. Simulate drive cycle
    # --------------------------------------------------
    for i in range(len(time)):

        v = speed[i]
        F_brake = braking_force[i]

        regen_force = 0.0
        friction_force = 0.0

        regen_power = 0.0
        battery_power = 0.0

        battery_current = 0.0
        battery_voltage = 0.0
        battery_loss = 0.0

        # --------------------------------------------------
        # 5. Regenerative braking
        # --------------------------------------------------
        if braking_flags[i] and F_brake > 0:

            regen = regenerative_braking(
                v,
                F_brake
            )

            regen_power_available = regen["P_elec_W"]

            # Battery determines how much power it can accept
            battery = charge_battery(
                soc=soc,
                temperature_c=temperature_c,
                requested_power_w=regen_power_available,
                dt=dt
            )

            # Correct keys from battery_model.py
            soc = battery["SOC_new"]

            battery_power = battery["accepted_terminal_power_W"]
            battery_current = battery["charging_current_A"]
            battery_voltage = battery["terminal_voltage_V"]
            battery_loss = battery["battery_loss_W"]

            # --------------------------------------------------
            # 6. Determine actual regenerative braking
            # --------------------------------------------------
            if regen_power_available > 0:

                power_ratio = min(
                    battery_power / regen_power_available,
                    1.0
                )

            else:
                power_ratio = 0.0

            regen_force = (
                regen["F_regen_wheel_N"]
                * power_ratio
            )

            # Remaining braking demand goes to friction brakes
            friction_force = max(
                F_brake - regen_force,
                0.0
            )

            # Actual electrical regenerative power
            regen_power = (
                regen_power_available
                * power_ratio
            )

        # --------------------------------------------------
        # 7. Energy accounting
        # --------------------------------------------------
        total_regen_energy += regen_power * dt

        total_battery_energy += battery_power * dt

        total_friction_energy += (
            friction_force * v * dt
        )

        # --------------------------------------------------
        # 8. Store results
        # --------------------------------------------------
        results.append({
            "time_s": time[i],
            "speed_mps": v,
            "acceleration_mps2": acceleration[i],
            "braking": braking_flags[i],
            "braking_force_N": F_brake,
            "regen_force_N": regen_force,
            "friction_force_N": friction_force,
            "regen_power_W": regen_power,
            "battery_power_W": battery_power,
            "battery_current_A": battery_current,
            "battery_voltage_V": battery_voltage,
            "battery_loss_W": battery_loss,
            "soc": soc
        })

    return (
        results,
        soc,
        total_regen_energy,
        total_battery_energy,
        total_friction_energy
    )


# ==========================================================
# Main program
# ==========================================================

if __name__ == "__main__":

    (
        results,
        final_soc,
        regen_energy,
        battery_energy,
        friction_energy
    ) = simulate_drive_cycle()

    print("\n")
    print("=" * 120)
    print("BATTERY-INTEGRATED REGENERATIVE BRAKING")
    print("=" * 120)

    print(
        f"{'Time':>6} "
        f"{'Speed':>8} "
        f"{'Brake':>9} "
        f"{'Regen':>9} "
        f"{'Friction':>10} "
        f"{'Regen P':>10} "
        f"{'Batt P':>10} "
        f"{'Current':>9} "
        f"{'SOC':>8}"
    )

    print("-" * 120)

    for r in results:

        print(
            f"{r['time_s']:6.1f} "
            f"{r['speed_mps']:8.3f} "
            f"{r['braking_force_N']:9.1f} "
            f"{r['regen_force_N']:9.1f} "
            f"{r['friction_force_N']:10.1f} "
            f"{r['regen_power_W']/1000:10.2f} "
            f"{r['battery_power_W']/1000:10.2f} "
            f"{r['battery_current_A']:9.2f} "
            f"{r['soc']:8.4f}"
        )

    print("-" * 120)

    print("\nSUMMARY")
    print("=" * 60)

    print("Initial SOC              : 0.2000")

    print(
        f"Final SOC                : "
        f"{final_soc:.6f}"
    )

    print(
        f"SOC increase             : "
        f"{(final_soc - 0.20) * 100:.4f}%"
    )

    print(
        f"Total regenerative energy : "
        f"{regen_energy / 1000:.3f} kJ"
    )

    print(
        f"Energy accepted by battery: "
        f"{battery_energy / 1000:.3f} kJ"
    )

    print(
        f"Friction braking energy   : "
        f"{friction_energy / 1000:.3f} kJ"
    )

    print("=" * 60)