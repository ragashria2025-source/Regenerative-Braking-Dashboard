"""
Step 6 (corrected): run A, B and C on the SAME fine-grid drive cycle.

Why a fine grid: the 1 s toy cycle changes speed by ~2.8 m/s per step. Using the
speed at the START of each 1 s step overstates power-based energy by about
10%, which breaks the kinetic-energy check. Plan Step 3 asks for resampling to a
small time step, so speed is linearly interpolated onto dt = 0.01 s.

Same rules for A, B and C:
  - battery-accepted energy is the reported energy, from the same battery model
  - mechanical work uses average speed over each step
  - starting SOC and temperature are identical
"""

from drive_cycle import get_test_cycle, calculate_acceleration, identify_braking, calculate_braking_force
from regen_model import regenerative_braking
from battery_model import charge_battery
from parameters import PARAMETERS
from supercap_model import cap_energy, cap_voltage, max_charge_power, max_discharge_power

REGEN_POWER_CAP_W = 50000.0  # fixed cap for configuration A (state in README)


def p(name):
    return PARAMETERS[name]["value"]


def build_fine_grid(dt=0.01):
    """Linearly interpolate the 1 s test cycle onto a fine time grid."""
    t_knots, v_knots = get_test_cycle()
    t_end = t_knots[-1]
    n = int(round(t_end / dt))
    times, speeds, accs = [], [], []
    for k in range(n + 1):
        t = k * dt
        # find segment
        j = min(int(t // 1.0), len(t_knots) - 2)
        t0, t1 = t_knots[j], t_knots[j + 1]
        v0, v1 = v_knots[j], v_knots[j + 1]
        frac = (t - t0) / (t1 - t0)
        times.append(t)
        speeds.append(v0 + frac * (v1 - v0))
        accs.append((v1 - v0) / (t1 - t0))
    braking = [a < -0.05 for a in accs]
    F = []
    m, Crr, Cd, A, rho, g = p("m"), p("Crr"), p("Cd"), p("A"), p("rho"), p("g")
    for v, a, b in zip(speeds, accs, braking):
        if not b:
            F.append(0.0)
            continue
        F_roll = Crr * m * g if v > 0 else 0.0
        F_aero = 0.5 * rho * Cd * A * v * v
        F.append(max(m * abs(a) - F_roll - F_aero, 0.0))
    dts = [times[i + 1] - times[i] for i in range(len(times) - 1)] + [0.0]
    return times, speeds, braking, F, dts


def _empty_out():
    return {"battery_accepted_J": 0.0, "wheel_regen_J": 0.0, "friction_J": 0.0,
            "wheel_braking_J": 0.0, "electrical_J": 0.0, "battery_loss_J": 0.0,
            "battery_stored_J": 0.0, "wasted_J": 0.0, "cap_left_J": 0.0,
            "transfer_J": 0.0, "stop_only_battery_J": 0.0, "final_soc": None}

def run_a(initial_soc=0.20, temperature_c=25.0, dt=0.01):
    """Configuration A: power-limited regenerative braking."""
    times, speed, braking, F, dts = build_fine_grid(dt)
    out = _empty_out()
    soc = initial_soc

    for i, v in enumerate(speed):
        d = dts[i]

        if not braking[i] or F[i] <= 0 or d <= 0:
            continue

        vavg = (
            0.5 * (v + speed[i + 1])
            if i + 1 < len(speed)
            else v
        )

        reg = regenerative_braking(vavg, F[i])
        p_available = reg["P_elec_W"]

        # Configuration A's assumed 50 kW electrical power limit.
        p_commanded = min(p_available, REGEN_POWER_CAP_W)

        # Ask the battery model how much power it can actually accept.
        bat = charge_battery(
            soc, temperature_c, p_commanded, d
        )
        soc = bat["SOC_new"]

        p_accepted = min(
            bat["accepted_terminal_power_W"],
            p_commanded,
        )

        # Assign braking force to regeneration only in proportion to
        # the electrical power actually accepted by the battery.
        ratio = (
            min(p_accepted / p_available, 1.0)
            if p_available > 0
            else 0.0
        )

        regen_force = reg["F_regen_wheel_N"] * ratio
        friction_force = max(F[i] - regen_force, 0.0)

        out["electrical_J"] += p_accepted * d
        out["battery_accepted_J"] += p_accepted * d
        out["battery_loss_J"] += bat["battery_loss_W"] * d
        out["battery_stored_J"] += bat["stored_power_W"] * d

        out["wasted_J"] += max(
            p_commanded - p_accepted, 0.0
        ) * d

        out["wheel_regen_J"] += regen_force * vavg * d
        out["friction_J"] += friction_force * vavg * d
        out["wheel_braking_J"] += F[i] * vavg * d

    out["final_soc"] = soc
    out["stop_only_battery_J"] = out["battery_accepted_J"]
    out["total_battery_J"] = out["battery_accepted_J"]

    return out

def run_b(initial_soc=0.20, temperature_c=25.0, dt=0.01):
    times, speed, braking, F, dts = build_fine_grid(dt)
    out = _empty_out()
    soc = initial_soc
    for i, v in enumerate(speed):
        d = dts[i]
        if not braking[i] or F[i] <= 0 or d <= 0:
            continue
        vavg = 0.5 * (v + speed[i + 1]) if i + 1 < len(speed) else v
        reg = regenerative_braking(vavg, F[i])
        p_avail = reg["P_elec_W"]
        bat = charge_battery(soc, temperature_c, p_avail, d)
        soc = bat["SOC_new"]
        acc = bat["accepted_terminal_power_W"]
        ratio = min(acc / p_avail, 1.0) if p_avail > 0 else 0.0
        regen_force = reg["F_regen_wheel_N"] * ratio
        friction = max(F[i] - regen_force, 0.0)
        out["electrical_J"] += p_avail * ratio * d
        out["battery_accepted_J"] += acc * d
        out["battery_loss_J"] += bat["battery_loss_W"] * d
        out["battery_stored_J"] += bat["stored_power_W"] * d
        out["wheel_regen_J"] += regen_force * vavg * d
        out["friction_J"] += friction * vavg * d
        out["wheel_braking_J"] += F[i] * vavg * d
    out["final_soc"] = soc
    out["stop_only_battery_J"] = out["battery_accepted_J"]
    out["total_battery_J"] = out["battery_accepted_J"]
    return out


def run_c(initial_soc=0.20, temperature_c=25.0, dt=0.01, transfer_dt=0.1, max_transfer_s=3600.0):
    times, speed, braking, F, dts = build_fine_grid(dt)
    out = _empty_out()
    eta_in, eta_out, R = p("eta_dc_in"), p("eta_dc_out"), p("R_sc")
    E_min = cap_energy(p("V_sc_min"))
    E_max = cap_energy(p("V_sc_max"))
    E = E_min
    soc = initial_soc
    out.update({"cap_in_J": 0.0, "cap_esr_in_J": 0.0, "cap_conv_in_J": 0.0,
                "cap_drawn_J": 0.0, "cap_esr_out_J": 0.0, "cap_conv_out_J": 0.0})

    for i, v in enumerate(speed):
        d = dts[i]
        if not braking[i] or F[i] <= 0 or d <= 0:
            continue
        vavg = 0.5 * (v + speed[i + 1]) if i + 1 < len(speed) else v
        reg = regenerative_braking(vavg, F[i])
        p_gen = reg["P_elec_W"]
        probe = charge_battery(soc, temperature_c, p_gen, d)
        b_req = min(probe["accepted_terminal_power_W"], p_gen)
        excess = max(p_gen - b_req, 0.0)
        V = cap_voltage(E)
        p_cap_lim = max_charge_power(max(E_max - E, 0.0), d, V)
        cap_gen = min(excess, p_cap_lim / eta_in)
        p_used = b_req + cap_gen
        ratio = p_used / p_gen if p_gen > 0 else 0.0
        regen_force = reg["F_regen_wheel_N"] * ratio
        friction = max(F[i] - regen_force, 0.0)

        bat = charge_battery(soc, temperature_c, b_req, d)
        soc = bat["SOC_new"]
        p_in = cap_gen * eta_in
        I = p_in / V if V > 0 else 0.0
        esr = I * I * R
        E += (p_in - esr) * d

        out["electrical_J"] += p_used * d
        out["battery_accepted_J"] += bat["accepted_terminal_power_W"] * d
        out["battery_loss_J"] += bat["battery_loss_W"] * d
        out["battery_stored_J"] += bat["stored_power_W"] * d
        out["wheel_regen_J"] += regen_force * vavg * d
        out["friction_J"] += friction * vavg * d
        out["wheel_braking_J"] += F[i] * vavg * d
        out["cap_in_J"] += p_in * d
        out["cap_esr_in_J"] += esr * d
        out["cap_conv_in_J"] += cap_gen * (1 - eta_in) * d

    out["stop_only_battery_J"] = out["battery_accepted_J"]

    t_tr = 0.0
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
            break
        p_in = acc / eta_out
        I = p_in / V
        esr = I * I * R
        drawn = (p_in + esr) * transfer_dt
        E -= drawn
        soc = bat["SOC_new"]
        out["battery_accepted_J"] += acc * transfer_dt
        out["battery_loss_J"] += bat["battery_loss_W"] * transfer_dt
        out["battery_stored_J"] += bat["stored_power_W"] * transfer_dt
        out["transfer_J"] += acc * transfer_dt
        out["cap_drawn_J"] += drawn
        out["cap_esr_out_J"] += esr * transfer_dt
        out["cap_conv_out_J"] += (p_in - acc) * transfer_dt
        t_tr += transfer_dt

    out["final_soc"] = soc
    out["cap_left_J"] = E - E_min
    out["total_battery_J"] = out["battery_accepted_J"]
    # Capacitor balance: in minus losses minus drawn equals change in stored energy
    out["cap_residual_J"] = (out["cap_in_J"] - out["cap_esr_in_J"] - out["cap_drawn_J"]) - (E - E_min)
    return out


def main():
    a, b, c = run_a(), run_b(), run_c()
    print("FINE-GRID DRIVE CYCLE, dt = 0.01 s, SOC 0.20, 25 C")
    print("=" * 74)
    print(f"{'':30s}{'A':>12s}{'B':>12s}{'C':>12s}")
    rows = [("battery accepted, stop (kJ)", a["stop_only_battery_J"], b["stop_only_battery_J"], c["stop_only_battery_J"]),
            ("battery accepted, total (kJ)", a["total_battery_J"], b["total_battery_J"], c["total_battery_J"]),
            ("  of which transfer (kJ)", 0.0, 0.0, c["transfer_J"]),
            ("friction braking (kJ)", a["friction_J"], b["friction_J"], c["friction_J"]),
            ("energy left in cap (kJ)", 0.0, 0.0, c["cap_left_J"]),
            ("wheel braking work (kJ)", a["wheel_braking_J"], b["wheel_braking_J"], c["wheel_braking_J"]),
            ("electrical generated (kJ)", a["electrical_J"], b["electrical_J"], c["electrical_J"])]
    for name, x, y, z in rows:
        print(f"{name:30s}{x/1e3:12.3f}{y/1e3:12.3f}{z/1e3:12.3f}")
    print("-" * 74)
    print(f"C capacitor balance residual: {c['cap_residual_J']:.3f} J")
    print(f"A wasted (rejected by battery): {a['wasted_J']/1e3:.3f} kJ")


if __name__ == "__main__":
    main()
