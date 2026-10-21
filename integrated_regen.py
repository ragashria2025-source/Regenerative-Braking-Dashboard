
from regen_model import regenerative_braking
from battery_model import charge_battery


def integrated_braking(v, F_brake, soc, temperature_c, dt=1.0):
    """
    Combine regenerative braking and battery charging limits.
    The remaining braking demand is handled by friction brakes.
    """

    regen = regenerative_braking(v, F_brake)

    # Determine how much electrical power the battery can accept.
    battery = charge_battery(
        soc=soc,
        temperature_c=temperature_c,
        requested_power_w=regen["P_elec_W"],
        dt=dt,
    )

    # Reduce regenerative torque if battery acceptance is lower
    # than the electrical power available from the motor.
    if regen["P_elec_W"] > 0:
        power_ratio = min(
            battery["accepted_terminal_power_W"] / regen["P_elec_W"],
            1.0,
        )
    else:
        power_ratio = 0.0

    regen_force = regen["F_regen_wheel_N"] * power_ratio
    friction_force = max(F_brake - regen_force, 0.0)

    return {
        "speed_m_s": v,
        "braking_demand_N": F_brake,
        "regen_force_N": regen_force,
        "friction_force_N": friction_force,
        "motor_electrical_power_W": regen["P_elec_W"] * power_ratio,
        "battery_accepted_power_W": battery["accepted_terminal_power_W"],
        "battery_current_A": battery["charging_current_A"],
        "SOC_new": battery["SOC_new"],
        "battery_voltage_V": battery["terminal_voltage_V"],
        "temperature_C": temperature_c,
    }
