"""
Step 11: Supercapacitor plots for configuration C on the 0-40-0 km/h test cycle.

Uses a traced copy of run_c's logic so every time step can be plotted. The
traced totals are checked against run_c before any plot is drawn.

Two starting SOCs are shown:
  0.20 - the Step 6 baseline (the capacitor barely charges)
  0.95 - the high-SOC case where the battery rejects energy and the capacitor works

Checks (must pass):
  - capacitor voltage stays inside the 180-360 V window at every step
  - generator energy into the capacitor = transfer + conversion losses + ESR losses + energy left
  - traced totals equal run_c totals

Outputs:
  step11_cap_timeseries.png - voltage, stored energy and power flows against time
  step11_cap_losses.png     - conversion and ESR losses (bar chart)

Run:  py step11_supercap_plots.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import drive_cycle

# Same cycle as Steps 6-10. Set BEFORE the runs.
drive_cycle.DRIVE_CYCLE = "toy"

from parameters import PARAMETERS  # noqa: E402
from fine_cycle_runs import build_fine_grid, run_c, p  # noqa: E402
from regen_model import regenerative_braking  # noqa: E402
from battery_model import charge_battery  # noqa: E402
from supercap_model import cap_energy, cap_voltage, max_charge_power, max_discharge_power  # noqa: E402

SOC_CASES = [0.20, 0.95]
TEMPERATURE_C = 25.0
V_MIN = p("V_sc_min")
V_MAX = p("V_sc_max")
E_MIN = cap_energy(V_MIN)
E_MAX = cap_energy(V_MAX)


def traced_run_c(initial_soc, temperature_c=TEMPERATURE_C, dt=0.01,
                 transfer_dt=0.1, max_transfer_s=3600.0):
    """Same logic as fine_cycle_runs.run_c, recording every step."""
    times, speed, braking, F, dts = build_fine_grid(dt)
    eta_in, eta_out, R = p("eta_dc_in"), p("eta_dc_out"), p("R_sc")

    E = E_MIN
    soc = initial_soc
    t_end_cycle = times[-1]

    tr = {"t": [], "V": [], "E": [], "p_gen": [], "p_bat": [], "p_cap_in": [],
          "p_cap_out": [], "p_bat_transfer": []}
    tot = {"stop_bat": 0.0, "gen_to_cap": 0.0, "conv_in": 0.0, "esr_in": 0.0,
           "cap_in": 0.0, "transfer": 0.0, "conv_out": 0.0, "esr_out": 0.0, "drawn": 0.0}

    for i, v in enumerate(speed):
        d = dts[i]
        t = times[i]
        if not braking[i] or F[i] <= 0 or d <= 0:
            tr["t"].append(t); tr["V"].append(cap_voltage(E)); tr["E"].append(E)
            tr["p_gen"].append(0.0); tr["p_bat"].append(0.0)
            tr["p_cap_in"].append(0.0); tr["p_cap_out"].append(0.0); tr["p_bat_transfer"].append(0.0)
            continue

        vavg = 0.5 * (v + speed[i + 1]) if i + 1 < len(speed) else v
        reg = regenerative_braking(vavg, F[i])
        p_gen = reg["P_elec_W"]
        probe = charge_battery(soc, temperature_c, p_gen, d)
        b_req = min(probe["accepted_terminal_power_W"], p_gen)
        excess = max(p_gen - b_req, 0.0)
        V = cap_voltage(E)
        p_cap_lim = max_charge_power(max(E_MAX - E, 0.0), d, V)
        cap_gen = min(excess, p_cap_lim / eta_in)
        p_used = b_req + cap_gen
        ratio = p_used / p_gen if p_gen > 0 else 0.0
        regen_force = reg["F_regen_wheel_N"] * ratio  # noqa: F841 (kept for parity with run_c)

        bat = charge_battery(soc, temperature_c, b_req, d)
        soc = bat["SOC_new"]
        p_in = cap_gen * eta_in
        I = p_in / V if V > 0 else 0.0
        esr = I * I * R
        E += (p_in - esr) * d

        tot["stop_bat"] += bat["accepted_terminal_power_W"] * d
        tot["gen_to_cap"] += cap_gen * d
        tot["conv_in"] += cap_gen * (1 - eta_in) * d
        tot["esr_in"] += esr * d
        tot["cap_in"] += p_in * d

        tr["t"].append(t); tr["V"].append(cap_voltage(E)); tr["E"].append(E)
        tr["p_gen"].append(p_gen); tr["p_bat"].append(bat["accepted_terminal_power_W"])
        tr["p_cap_in"].append(p_in); tr["p_cap_out"].append(0.0); tr["p_bat_transfer"].append(0.0)

    # Post-stop transfer to battery, as in run_c.
    t_tr = 0.0
    while t_tr < max_transfer_s:
        avail = E - E_MIN
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
        p_in_out = acc / eta_out
        I = p_in_out / V
        esr = I * I * R
        drawn = (p_in_out + esr) * transfer_dt
        E -= drawn
        soc = bat["SOC_new"]

        tot["transfer"] += acc * transfer_dt
        tot["conv_out"] += (p_in_out - acc) * transfer_dt
        tot["esr_out"] += esr * transfer_dt
        tot["drawn"] += drawn

        t_plot = t_end_cycle + t_tr
        tr["t"].append(t_plot); tr["V"].append(cap_voltage(E)); tr["E"].append(E)
        tr["p_gen"].append(0.0); tr["p_bat"].append(0.0)
        tr["p_cap_in"].append(0.0); tr["p_cap_out"].append(drawn / transfer_dt)
        tr["p_bat_transfer"].append(acc)
        t_tr += transfer_dt

    tot["cap_left"] = E - E_MIN
    tot["cap_stop_end"] = None
    return tr, tot


def check_against_run_c(tot, soc):
    ref = run_c(initial_soc=soc, temperature_c=TEMPERATURE_C)
    pairs = [
        ("stop battery", tot["stop_bat"], ref["stop_only_battery_J"]),
        ("transfer", tot["transfer"], ref["transfer_J"]),
        ("energy left", tot["cap_left"], ref["cap_left_J"]),
    ]
    for name, mine, theirs in pairs:
        if abs(mine - theirs) > 1e-3:
            raise SystemExit(f"SOC {soc}: traced {name} {mine:.3f} J != run_c {theirs:.3f} J")


def check_window(tr, soc):
    vmin, vmax = min(tr["V"]), max(tr["V"])
    if vmin < V_MIN - 1e-6 or vmax > V_MAX + 1e-6:
        raise SystemExit(f"SOC {soc}: voltage left the window ({vmin:.2f} to {vmax:.2f} V)")
    return vmin, vmax


def check_balance(tot, soc):
    lhs = tot["gen_to_cap"]
    rhs = (tot["transfer"] + tot["conv_in"] + tot["esr_in"]
           + tot["conv_out"] + tot["esr_out"] + tot["cap_left"])
    if abs(lhs - rhs) > 1e-3:
        raise SystemExit(f"SOC {soc}: capacitor flows do not add up (off by {lhs - rhs:.6f} J)")
    return lhs - rhs


def plot_timeseries(results, path="step11_cap_timeseries.png"):
    fig, axes = plt.subplots(3, 2, figsize=(13, 11), sharex=True)
    for col, soc in enumerate(SOC_CASES):
        tr = results[soc]["tr"]
        t = tr["t"]
        ax_v, ax_e, ax_p = axes[0][col], axes[1][col], axes[2][col]

        ax_v.axhspan(V_MIN, V_MAX, color="#0FA3B1", alpha=0.08, label="Usable window 180-360 V")
        ax_v.plot(t, tr["V"], color="#1B2A41", linewidth=1.5, label="Capacitor voltage")
        ax_v.axhline(V_MIN, color="#0FA3B1", linestyle="--", linewidth=0.8)
        ax_v.axhline(V_MAX, color="#0FA3B1", linestyle="--", linewidth=0.8)
        ax_v.set_ylim(V_MIN - 20, V_MAX + 20)
        ax_v.set_title(f"SOC {soc:.2f}: capacitor voltage")
        ax_v.set_ylabel("Voltage (V)")
        ax_v.legend(loc="lower right", fontsize=8, frameon=False)

        ax_e.axhspan(E_MIN / 1e3, E_MAX / 1e3, color="#0FA3B1", alpha=0.08)
        ax_e.plot(t, [e / 1e3 for e in tr["E"]], color="#1B2A41", linewidth=1.5)
        ax_e.set_title(f"SOC {soc:.2f}: energy stored in capacitor")
        ax_e.set_ylabel("Energy (kJ)")

        ax_p.plot(t, [x / 1e3 for x in tr["p_gen"]], color="#C0392B", label="Generated (wheel regen)")
        ax_p.plot(t, [x / 1e3 for x in tr["p_bat"]], color="#1B2A41", label="Battery accepted (stop)")
        ax_p.plot(t, [x / 1e3 for x in tr["p_cap_in"]], color="#0FA3B1", label="Into capacitor")
        ax_p.plot(t, [x / 1e3 for x in tr["p_cap_out"]], color="#F5B041", label="Out of capacitor (transfer)")
        ax_p.plot(t, [x / 1e3 for x in tr["p_bat_transfer"]], color="#8E44AD", linestyle=":",
                  label="Battery accepted (transfer)")
        ax_p.set_title(f"SOC {soc:.2f}: power flows")
        ax_p.set_ylabel("Power (kW)")
        ax_p.set_xlabel("Time (s); transfer starts after the cycle ends")
        ax_p.legend(loc="upper right", fontsize=7, frameon=False)

        for ax in (ax_v, ax_e, ax_p):
            ax.axvline(results[soc]["t_end"], color="black", linewidth=0.6, linestyle=":")
            ax.grid(alpha=0.25)
            ax.set_axisbelow(True)

    fig.suptitle("Configuration C: supercapacitor behaviour, 0-40-0 km/h cycle, 25 C", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_losses(results, path="step11_cap_losses.png"):
    cats = ["Conversion in", "ESR in", "Conversion out", "ESR out"]
    keys = ["conv_in", "esr_in", "conv_out", "esr_out"]
    x = list(range(len(cats)))
    w = 0.38
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for j, (soc, color) in enumerate(zip(SOC_CASES, ["#8A9BA8", "#0FA3B1"])):
        tot = results[soc]["tot"]
        vals = [tot[k] / 1e3 for k in keys]
        offs = [xi + (j - 0.5) * w for xi in x]
        ax.bar(offs, vals, width=w, color=color, label=f"SOC {soc:.2f}")
        for xo, v in zip(offs, vals):
            ax.annotate(f"{v:.3f}", (xo, v), xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylabel("Energy lost (kJ)")
    ax.set_title("Configuration C: conversion and ESR losses, 0-40-0 km/h cycle, 25 C")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    results = {}
    for soc in SOC_CASES:
        tr, tot = traced_run_c(soc)
        check_against_run_c(tot, soc)
        vmin, vmax = check_window(tr, soc)
        residual = check_balance(tot, soc)
        t_end = build_fine_grid(0.01)[0][-1]
        results[soc] = {"tr": tr, "tot": tot, "t_end": t_end}
        print(f"SOC {soc:.2f}: voltage {vmin:.2f} to {vmax:.2f} V (window 180-360 V) | "
              f"flow balance residual {residual:.6f} J | "
              f"transfer {tot['transfer']/1e3:.3f} kJ | left {tot['cap_left']/1e3:.3f} kJ | "
              f"losses conv-in {tot['conv_in']/1e3:.3f}, ESR-in {tot['esr_in']/1e3:.3f}, "
              f"conv-out {tot['conv_out']/1e3:.3f}, ESR-out {tot['esr_out']/1e3:.3f} kJ")

    print("\nAll checks passed: window held, flows add up, traced totals equal run_c.")
    print("Saved:", plot_timeseries(results))
    print("Saved:", plot_losses(results))


if __name__ == "__main__":
    main()