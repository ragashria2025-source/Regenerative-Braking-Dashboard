"""
Configuration C: adaptive braking with a supercapacitor buffer.

Stop phase:
  - Regeneration is limited by motor output and by what the battery AND the
    capacitor can absorb. Generated power the battery rejects goes into the
    capacitor via the converter, up to the capacitor's energy and power limits.
  - Friction braking supplies the rest of the demand.

Transfer phase (after the stop, at rest):
  - The capacitor delivers energy to the battery at the battery's own charge
    acceptance limit, until the capacitor reaches V_min or the battery stops
    accepting charge.

Energy is tracked by source so nothing is counted twice:
  energy left in the capacitor at the end is reported separately.
"""

from parameters import PARAMETERS
from regen_model import regenerative_braking
from battery_model import charge_battery, battery_resistance
from supercap_model import (
    cap_energy,
    cap_voltage,
    max_charge_power,
    max_discharge_power,
)


def p(name):
    return PARAMETERS[name]["value"]


def simulate_config_c(
    initial_speed=30.0,
    braking_force=4000.0,
    initial_soc=0.20,
    temperature_c=25.0,
    dt=0.01,
    transfer_dt=0.1,
    max_transfer_s=3600.0,
):
    mass, crr, cd = p("m"), p("Crr"), p("Cd")
    area, rho, g = p("A"), p("rho"), p("g")
    eta_in, eta_out = p("eta_dc_in"), p("eta_dc_out")
    R = p("R_sc")
    E_min = cap_energy(p("V_sc_min"))
    E_max = cap_energy(p("V_sc_max"))

    if initial_speed < 0 or braking_force < 0 or dt <= 0:
        raise ValueError("Invalid speed, braking force, or time step.")

    speed = initial_speed
    soc = initial_soc
    E = E_min  # capacitor starts at the bottom of its usable window
    time = 0.0
    distance = 0.0
    steps = 0
    max_steps = 200000
    initial_ke = 0.5 * mass * speed**2

    e = {
        "wheel_braking_J": 0.0,
        "friction_braking_J": 0.0,
        "regen_wheel_J": 0.0,
        "gear_and_generator_loss_J": 0.0,
        "battery_accepted_stop_J": 0.0,
        "battery_loss_J": 0.0,
        "battery_stored_J": 0.0,
        "cap_converter_in_loss_J": 0.0,
        "cap_esr_in_loss_J": 0.0,
        "cap_net_in_J": 0.0,
        "cap_drawn_out_J": 0.0,
        "cap_esr_out_loss_J": 0.0,
        "cap_converter_out_loss_J": 0.0,
        "battery_accepted_transfer_J": 0.0,
        "aero_loss_J": 0.0,
        "rolling_loss_J": 0.0,
    }

    # ---------- Stop phase ----------
    while speed > 1e-8 and steps < max_steps:
        rolling_force = crr * mass * g
        aero_force = 0.5 * rho * cd * area * speed**2
        deceleration = (braking_force + rolling_force + aero_force) / mass

        dt_step = min(dt, speed / deceleration)
        new_speed = max(speed - deceleration * dt_step, 0.0)
        v_avg = (speed + new_speed) / 2.0

        regen = regenerative_braking(speed, braking_force)
        p_gen = regen["P_elec_W"]

        # Battery acceptance for the full generated power.
        probe = charge_battery(soc, temperature_c, p_gen, dt_step)
        b_acc_request = min(probe["accepted_terminal_power_W"], p_gen)

        # Excess generated power goes to the capacitor, within its limits.
        excess = max(p_gen - b_acc_request, 0.0)
        V = cap_voltage(E)
        p_cap_in_limit = max_charge_power(max(E_max - E, 0.0), dt_step, V)
        cap_gen_used = min(excess, p_cap_in_limit / eta_in)
        p_cap_in = cap_gen_used * eta_in

        p_used = b_acc_request + cap_gen_used
        ratio = p_used / p_gen if p_gen > 0 else 0.0
        regen_force = regen["F_regen_wheel_N"] * ratio
        friction_force = max(braking_force - regen_force, 0.0)

        # Commit the battery step.
        bat = charge_battery(soc, temperature_c, b_acc_request, dt_step)
        soc = bat["SOC_new"]

        # Commit the capacitor charge step.
        I_in = p_cap_in / V if V > 0 else 0.0
        esr_in = I_in**2 * R
        cap_net_in = (p_cap_in - esr_in) * dt_step
        E = E + cap_net_in

        e["wheel_braking_J"] += braking_force * v_avg * dt_step
        e["friction_braking_J"] += friction_force * v_avg * dt_step
        e["regen_wheel_J"] += regen_force * v_avg * dt_step
        e["gear_and_generator_loss_J"] += regen_force * v_avg * dt_step - p_used * dt_step
        e["battery_accepted_stop_J"] += bat["accepted_terminal_power_W"] * dt_step
        e["battery_loss_J"] += bat["battery_loss_W"] * dt_step
        e["battery_stored_J"] += bat["stored_power_W"] * dt_step
        e["cap_converter_in_loss_J"] += cap_gen_used * (1 - eta_in) * dt_step
        e["cap_esr_in_loss_J"] += esr_in * dt_step
        e["cap_net_in_J"] += cap_net_in
        e["aero_loss_J"] += aero_force * v_avg * dt_step
        e["rolling_loss_J"] += rolling_force * v_avg * dt_step

        distance += v_avg * dt_step
        speed = new_speed
        time += dt_step
        steps += 1

    stop_time = time
    stop_soc = soc
    E_after_stop = E

    # ---------- Transfer phase (at rest) ----------
    t_tr = 0.0
    transfer_steps = 0
    while t_tr < max_transfer_s:
        avail = E - E_min
        if avail <= 1e-9:
            break
        V = cap_voltage(E)
        p_cap_max = max_discharge_power(avail, transfer_dt, V)
        if p_cap_max <= 0:
            break

        bat = charge_battery(soc, temperature_c, p_cap_max * eta_out, transfer_dt)
        acc = bat["accepted_terminal_power_W"]
        if acc <= 1e-6:
            break  # battery accepts nothing (cold, or SOC cutoff)

        p_in = acc / eta_out          # power drawn at capacitor terminals
        I_out = p_in / V
        esr_out = I_out**2 * R
        drawn = (p_in + esr_out) * transfer_dt
        soc = bat["SOC_new"]
        E = E - drawn

        e["battery_accepted_transfer_J"] += acc * transfer_dt
        e["battery_loss_J"] += bat["battery_loss_W"] * transfer_dt
        e["battery_stored_J"] += bat["stored_power_W"] * transfer_dt
        e["cap_drawn_out_J"] += drawn
        e["cap_esr_out_loss_J"] += esr_out * transfer_dt
        e["cap_converter_out_loss_J"] += (p_in - acc) * transfer_dt

        t_tr += transfer_dt
        transfer_steps += 1

    final_ke = 0.5 * mass * speed**2
    e["kinetic_energy_lost_J"] = initial_ke - final_ke

    # Braking energy must be accounted for by: friction, gear/generator loss,
    # battery losses, battery stored energy, converter and ESR losses,
    # and energy still left in the capacitor.
    still_in_cap = E - E_min
    accounted = (
        e["friction_braking_J"]
        + e["gear_and_generator_loss_J"]
        + e["battery_loss_J"]
        + e["battery_stored_J"]
        + e["cap_converter_in_loss_J"]
        + e["cap_esr_in_loss_J"]
        + e["cap_esr_out_loss_J"]
        + e["cap_converter_out_loss_J"]
        + still_in_cap
    )
    recovery_residual = e["wheel_braking_J"] - accounted

    # Capacitor state balance: net energy in minus energy out equals change.
    cap_residual = (e["cap_net_in_J"] - e["cap_drawn_out_J"]) - (E - E_min)

    tol = 1e-3 * e["wheel_braking_J"]
    return {
        "stop_time_s": stop_time,
        "stop_distance_m": distance,
        "stop_final_SOC": stop_soc,
        "final_SOC": soc,
        "transfer_time_s": t_tr,
        "energy_left_in_cap_J": still_in_cap,
        "recovery_residual_J": recovery_residual,
        "cap_residual_J": cap_residual,
        "recovery_tolerance_J": tol,
        "battery_total_J": e["battery_stored_J"] + 0.0,
        "battery_accepted_total_J": e["battery_accepted_stop_J"] + e["battery_accepted_transfer_J"],
        **e,
    }


def main():
    r = simulate_config_c()
    print("\nCONFIGURATION C: ADAPTIVE + SUPERCAPACITOR")
    print("=" * 60)
    for key, value in r.items():
        if key.endswith("_J"):
            print(f"{key}: {value:.2f} J ({value / 1000:.2f} kJ)")
        else:
            print(f"{key}: {value:.6f}")

    assert abs(r["recovery_residual_J"]) < r["recovery_tolerance_J"], "recovery balance failed"
    assert abs(r["cap_residual_J"]) < r["recovery_tolerance_J"], "capacitor balance failed"
    print("\nConfiguration C energy balances passed.")


if __name__ == "__main__":
    main()
