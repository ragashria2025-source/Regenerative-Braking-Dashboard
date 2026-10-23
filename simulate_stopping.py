
"""
Step 7: Full stopping-event simulation and energy accounting.
"""

from parameters import PARAMETERS
from integrated_regen import integrated_braking
from battery_model import battery_resistance


def p(name):
    return PARAMETERS[name]["value"]


def simulate_stopping(
    initial_speed=30.0,
    braking_force=4000.0,
    initial_soc=0.20,
    temperature_c=25.0,
    dt=0.01,
):
    mass = p("m")
    crr = p("Crr")
    cd = p("Cd")
    area = p("A")
    rho = p("rho")
    g = p("g")

    if initial_speed < 0 or braking_force < 0 or dt <= 0:
        raise ValueError("Invalid speed, braking force, or time step.")

    speed = initial_speed
    soc = initial_soc
    time = 0.0

    energy = {
        "kinetic_energy_lost_J": 0.0,
        "wheel_braking_J": 0.0,
        "friction_braking_J": 0.0,
        "regen_mechanical_J": 0.0,
        "regen_electrical_J": 0.0,
        "motor_and_drivetrain_loss_J": 0.0,
        "battery_terminal_energy_J": 0.0,
        "battery_stored_energy_J": 0.0,
        "battery_loss_J": 0.0,
        "aero_loss_J": 0.0,
        "rolling_loss_J": 0.0,
    }

    initial_ke = 0.5 * mass * speed**2
    steps = 0
    max_steps = 200000
    stopping_distance = 0.0

    while speed > 1e-8 and steps < max_steps:
        # Road-load forces at the beginning of this interval.
        rolling_force = crr * mass * g
        aero_force = 0.5 * rho * cd * area * speed**2

        total_resisting_force = braking_force + rolling_force + aero_force
        deceleration = total_resisting_force / mass

        # Shorten the final interval so the vehicle stops exactly at zero.
        dt_step = min(dt, speed / deceleration)
        new_speed = max(speed - deceleration * dt_step, 0.0)
        average_speed = (speed + new_speed) / 2.0

        # Split the requested braking force between regen and friction.
        result = integrated_braking(
            v=speed,
            F_brake=braking_force,
            soc=soc,
            temperature_c=temperature_c,
            dt=dt_step,
        )

        regen_force = result["regen_force_N"]
        friction_force = result["friction_force_N"]
        battery_current = result["battery_current_A"]
        battery_r = battery_resistance(temperature_c)

        # Work done during this interval.
        wheel_braking = braking_force * average_speed * dt_step
        friction_work = friction_force * average_speed * dt_step
        regen_mechanical = regen_force * average_speed * dt_step

        # Electrical energy accepted by the battery.
        # This is the same power reported by the integrated model.
        electrical_energy = (
            result["motor_electrical_power_W"] * dt_step
        )
        terminal_energy = (
            result["battery_accepted_power_W"] * dt_step
        )
        battery_loss = battery_current**2 * battery_r * dt_step
        stored_energy = max(terminal_energy - battery_loss, 0.0)

        # Losses to the surroundings.
        aero_work = aero_force * average_speed * dt_step
        rolling_work = rolling_force * average_speed * dt_step

        # Record energy flows.
        energy["wheel_braking_J"] += wheel_braking
        energy["friction_braking_J"] += friction_work
        energy["regen_mechanical_J"] += regen_mechanical
        energy["regen_electrical_J"] += electrical_energy
        energy["motor_and_drivetrain_loss_J"] += max(
            regen_mechanical - electrical_energy, 0.0
        )
        energy["battery_terminal_energy_J"] += terminal_energy
        energy["battery_stored_energy_J"] += stored_energy
        energy["battery_loss_J"] += battery_loss
        energy["aero_loss_J"] += aero_work
        energy["rolling_loss_J"] += rolling_work
        stopping_distance += average_speed * dt_step
        # Update state.
        soc = result["SOC_new"]
        speed = new_speed
        time += dt_step
        steps += 1

    final_ke = 0.5 * mass * speed**2
    energy["kinetic_energy_lost_J"] = initial_ke - final_ke

    # Full vehicle kinetic-energy balance.
    vehicle_accounted = (
        energy["wheel_braking_J"]
        + energy["aero_loss_J"]
        + energy["rolling_loss_J"]
    )
    vehicle_residual = (
        energy["kinetic_energy_lost_J"] - vehicle_accounted
    )

    # Braking energy goes to friction, drivetrain conversion losses,
    # battery heat, and chemical energy stored in the battery.
    recovery_accounted = (
        energy["friction_braking_J"]
        + energy["motor_and_drivetrain_loss_J"]
        + energy["battery_loss_J"]
        + energy["battery_stored_energy_J"]
    )
    recovery_residual = energy["wheel_braking_J"] - recovery_accounted

    return {
        "stopping_time_s": time,
        "stopping_distance_m": stopping_distance,
        "final_speed_m_s": speed,
        "final_SOC": soc,
        "steps": steps,
        "vehicle_energy_residual_J": vehicle_residual,
        "recovery_energy_residual_J": recovery_residual,
        **energy,
    }


def main():
    result = simulate_stopping()

    print("\nFULL STOPPING SIMULATION")
    print("=" * 55)

    for key, value in result.items():
        if value is None:
            print(f"{key}: not calculated yet")
        elif key.endswith("_J"):
            print(f"{key}: {value:.2f} J ({value / 1000:.2f} kJ)")
        else:
            print(f"{key}: {value:.6f}")

    print("\nENERGY BALANCE CHECKS")
    print("-" * 55)
    print(
        "Vehicle residual:",
        f"{result['vehicle_energy_residual_J']:.6f} J",
    )
    print(
        "Recovery residual:",
        f"{result['recovery_energy_residual_J']:.6f} J",
    )

    assert result["final_speed_m_s"] == 0.0
    tol = 1e-3 * result["wheel_braking_J"]
    assert abs(result["vehicle_energy_residual_J"]) < tol
    assert abs(result["recovery_energy_residual_J"]) < tol
    print("Recovery energy balance passed.")

    print("\nVehicle energy balance passed.")


if __name__ == "__main__":
    main()
