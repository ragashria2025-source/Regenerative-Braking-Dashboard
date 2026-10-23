"""
Drive-Cycle Regenerative Braking Simulation

This file connects:

    drive_cycle.py
            ↓
    braking force demand
            ↓
    regen_model.py
            ↓
    regenerative braking + friction braking

This is the first integration of the drive-cycle
with the regenerative braking model.

Units:
    Time       : seconds
    Speed      : m/s
    Force      : N
    Power      : W
    Torque     : N*m
"""

from drive_cycle import (
    get_test_cycle,
    calculate_acceleration,
    identify_braking,
    calculate_braking_force,
)

from regen_model import regenerative_braking


def simulate_drive_cycle():
    """
    Run the regenerative braking model over the
    complete test drive cycle.
    """

    # --------------------------------------------------
    # 1. Get drive-cycle data
    # --------------------------------------------------

    time, speed = get_test_cycle()

    # --------------------------------------------------
    # 2. Calculate acceleration
    # --------------------------------------------------

    acceleration = calculate_acceleration(
        time,
        speed
    )

    # --------------------------------------------------
    # 3. Identify braking periods
    # --------------------------------------------------

    braking = identify_braking(
        acceleration
    )

    # --------------------------------------------------
    # 4. Calculate required braking force
    # --------------------------------------------------

    braking_force = calculate_braking_force(
        time,
        speed,
        acceleration
    )

    # --------------------------------------------------
    # 5. Run regenerative braking model
    # --------------------------------------------------

    results = []

    for t, v, a, is_braking, F_brake in zip(
        time,
        speed,
        acceleration,
        braking,
        braking_force
    ):

        # If the vehicle is not braking,
        # there is no regenerative braking.
        if not is_braking:

            regen_force = 0.0
            friction_force = 0.0
            electrical_power = 0.0
            motor_torque = 0.0
            motor_speed = 0.0

        else:

            regen = regenerative_braking(
                v=v,
                F_brake=F_brake
            )

            regen_force = regen["F_regen_wheel_N"]
            friction_force = regen["F_friction_N"]
            electrical_power = regen["P_elec_W"]
            motor_torque = regen["T_regen_motor_Nm"]
            motor_speed = regen["omega_motor_rad_s"]

        results.append({
            "time_s": t,
            "speed_m_s": v,
            "acceleration_m_s2": a,
            "braking": is_braking,
            "braking_force_N": F_brake,
            "regen_force_N": regen_force,
            "friction_force_N": friction_force,
            "electrical_power_W": electrical_power,
            "motor_torque_Nm": motor_torque,
            "motor_speed_rad_s": motor_speed,
        })

    return results


def print_results(results):
    """
    Print the drive-cycle regenerative braking results.
    """

    print("\nDRIVE-CYCLE REGENERATIVE BRAKING SIMULATION")
    print("=" * 125)

    print(
        f"{'Time':>7}"
        f"{'Speed':>10}"
        f"{'Accel.':>10}"
        f"{'Brake':>10}"
        f"{'Regen':>10}"
        f"{'Friction':>10}"
        f"{'Power':>12}"
        f"{'Torque':>10}"
        f"{'Braking?':>10}"
    )

    print(
        f"{'(s)':>7}"
        f"{'(m/s)':>10}"
        f"{'(m/s²)':>10}"
        f"{'(N)':>10}"
        f"{'(N)':>10}"
        f"{'(N)':>10}"
        f"{'(kW)':>12}"
        f"{'(Nm)':>10}"
        f"{'':>10}"
    )

    print("-" * 125)

    for result in results:

        print(
            f"{result['time_s']:7.1f}"
            f"{result['speed_m_s']:10.3f}"
            f"{result['acceleration_m_s2']:10.3f}"
            f"{result['braking_force_N']:10.1f}"
            f"{result['regen_force_N']:10.1f}"
            f"{result['friction_force_N']:10.1f}"
            f"{result['electrical_power_W'] / 1000:12.2f}"
            f"{result['motor_torque_Nm']:10.2f}"
            f"{str(result['braking']):>10}"
        )


def print_summary(results):
    """
    Print important summary values.
    """

    braking_results = [
        r for r in results
        if r["braking"]
    ]

    if not braking_results:
        print("\nNo braking events detected.")
        return

    max_braking_force = max(
        r["braking_force_N"]
        for r in braking_results
    )

    max_regen_force = max(
        r["regen_force_N"]
        for r in braking_results
    )

    max_friction_force = max(
        r["friction_force_N"]
        for r in braking_results
    )

    max_power = max(
        r["electrical_power_W"]
        for r in braking_results
    )

    max_torque = max(
        r["motor_torque_Nm"]
        for r in braking_results
    )

    print("\nSUMMARY")
    print("=" * 55)

    print(
        f"Maximum braking demand   : "
        f"{max_braking_force:.2f} N"
    )

    print(
        f"Maximum regenerative force: "
        f"{max_regen_force:.2f} N"
    )

    print(
        f"Maximum friction force   : "
        f"{max_friction_force:.2f} N"
    )

    print(
        f"Maximum electrical power : "
        f"{max_power / 1000:.2f} kW"
    )

    print(
        f"Maximum motor torque     : "
        f"{max_torque:.2f} N*m"
    )


def main():

    results = simulate_drive_cycle()

    print_results(results)

    print_summary(results)


if __name__ == "__main__":
    main()
