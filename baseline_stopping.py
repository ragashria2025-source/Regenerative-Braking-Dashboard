"""
Configuration A: baseline stopping event.

Regeneration uses a FIXED power cap and ignores battery charge limits
(no SOC or temperature feedback). Whatever the battery cannot accept
is wasted. Friction braking supplies the rest of the braking force.

Same scenario as simulate_stopping.py so the two results compare fairly.
"""

from parameters import PARAMETERS
from regen_model import regenerative_braking
from battery_model import charge_battery, battery_resistance


def p(name):
    return PARAMETERS[name]["value"]


def simulate_baseline(
    initial_speed=30.0,
    braking_force=4000.0,
    initial_soc=0.20,
    temperature_c=25.0,
    regen_power_cap_w=50000.0,
    dt=0.01,
):
    mass, crr, cd = p("m"), p("Crr"), p("Cd")
    area, rho, g = p("A"), p("rho"), p("g")

    if initial_speed < 0 or braking_force < 0 or dt <= 0 or regen_power_cap_w < 0:
        raise ValueError("Invalid speed, braking force, power cap, or time step.")

    speed = initial_speed
    soc = initial_soc
    time = 0.0
    distance = 0.0
    steps = 0
    max_steps = 200000
    initial_ke = 0.5 * mass * speed**2

    energy = {
        "wheel_braking_J": 0.0,
        "friction_braking_J": 0.0,
        "regen_wheel_J": 0.0,
        "generated_electrical_J": 0.0,
        "battery_accepted_J": 0.0,
        "battery_wasted_J": 0.0,
        "battery_loss_J": 0.0,
        "battery_stored_J": 0.0,
        "gear_and_generator_loss_J": 0.0,
        "aero_loss_J": 0.0,
        "rolling_loss_J": 0.0,
    }

    while speed > 1e-8 and steps < max_steps:
        rolling_force = crr * mass * g
        aero_force = 0.5 * rho * cd * area * speed**2
        deceleration = (braking_force + rolling_force + aero_force) / mass

        dt_step = min(dt, speed / deceleration)
        new_speed = max(speed - deceleration * dt_step, 0.0)
        v_avg = (speed + new_speed) / 2.0

        # Regen the motor could deliver, then clipped to the fixed cap.
        regen = regenerative_braking(speed, braking_force)
        p_elec_available = regen["P_elec_W"]
        p_elec_cmd = min(p_elec_available, regen_power_cap_w)
        ratio = p_elec_cmd / p_elec_available if p_elec_available > 0 else 0.0

        regen_force = regen["F_regen_wheel_N"] * ratio
        friction_force = max(braking_force - regen_force, 0.0)

        # Battery accepts what its limits allow; the rest is wasted.
        battery = charge_battery(
            soc=soc,
            temperature_c=temperature_c,
            requested_power_w=p_elec_cmd,
            dt=dt_step,
        )
        accepted_J = battery["accepted_terminal_power_W"] * dt_step
        generated_J = p_elec_cmd * dt_step
        battery_loss_J = battery["battery_loss_W"] * dt_step
        stored_J = battery["stored_power_W"] * dt_step

        energy["wheel_braking_J"] += braking_force * v_avg * dt_step
        energy["friction_braking_J"] += friction_force * v_avg * dt_step
        energy["regen_wheel_J"] += regen_force * v_avg * dt_step
        energy["generated_electrical_J"] += generated_J
        energy["battery_accepted_J"] += accepted_J
        energy["battery_wasted_J"] += max(generated_J - accepted_J, 0.0)
        energy["battery_loss_J"] += battery_loss_J
        energy["battery_stored_J"] += stored_J
        energy["gear_and_generator_loss_J"] += regen_force * v_avg * dt_step - generated_J
        energy["aero_loss_J"] += aero_force * v_avg * dt_step
        energy["rolling_loss_J"] += rolling_force * v_avg * dt_step

        soc = battery["SOC_new"]
        distance += v_avg * dt_step
        speed = new_speed
        time += dt_step
        steps += 1

    final_ke = 0.5 * mass * speed**2
    energy["kinetic_energy_lost_J"] = initial_ke - final_ke

    # Braking energy must go to friction, gear/generator loss, wasted
    # energy, battery loss, or stored energy.
    accounted = (
        energy["friction_braking_J"]
        + energy["gear_and_generator_loss_J"]
        + energy["battery_wasted_J"]
        + energy["battery_loss_J"]
        + energy["battery_stored_J"]
    )
    recovery_residual = energy["wheel_braking_J"] - accounted

    return {
        "stopping_time_s": time,
        "stopping_distance_m": distance,
        "final_speed_m_s": speed,
        "final_SOC": soc,
        "steps": steps,
        "recovery_energy_residual_J": recovery_residual,
        "recovery_tolerance_J": 1e-3 * energy["wheel_braking_J"],
        **energy,
    }


def main():
    result = simulate_baseline()

    print("\nBASELINE (CONFIGURATION A) STOPPING SIMULATION")
    print("=" * 55)
    for key, value in result.items():
        if key.endswith("_J"):
            print(f"{key}: {value:.2f} J ({value / 1000:.2f} kJ)")
        else:
            print(f"{key}: {value:.6f}")

    assert result["final_speed_m_s"] == 0.0
    assert abs(result["recovery_energy_residual_J"]) < result["recovery_tolerance_J"]
    print("\nBaseline energy balance passed.")


if __name__ == "__main__":
    main()
