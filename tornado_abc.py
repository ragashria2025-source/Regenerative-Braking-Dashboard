"""
Step 10: Tornado analysis on the 0-40-0 km/h test cycle.

Baseline: configuration B at the Step 6 settings (SOC 0.20, 25 C).
Each parameter is set to a low and a high value, all else fixed.
Output: change in battery-accepted energy (kJ) relative to the baseline,
sorted by swing (high minus low).

Capacitance only affects configuration C, so it is measured on a C baseline
and is shown separately in the table and plot.

Every run must pass the energy checks.

Outputs:
  tornado_results.csv   - one row per parameter
  step10_tornado.png    - tornado plot (labelled)

Run:  py tornado_abc.py
"""

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import drive_cycle

# Same cycle as Steps 6-9. Set BEFORE the runs.
drive_cycle.DRIVE_CYCLE = "toy"

from parameters import PARAMETERS  # noqa: E402
from fine_cycle_runs import run_b, run_c  # noqa: E402

BASE_SOC = 0.20
BASE_TEMP = 25.0

# (label, parameter key or None, low, high, mode, config, assumption note)
#   mode "scale": low/high are multipliers of the baseline value
#   mode "abs":   low/high are absolute values
#   key None:     SOC or temperature, handled separately
SPECS = [
    ("Battery internal resistance", "R0_25", 0.7, 1.3, "scale", "B",
     "ASSUMED value; +/-30%"),
    ("Charge-current limit", "i_max", 0.7, 1.3, "scale", "B",
     "ASSUMED value; +/-30%"),
    ("Motor regen power limit", "P_max", 0.7, 1.3, "scale", "B",
     "Spec-sheet value applied to one axle (known limitation); +/-30%"),
    ("Generator efficiency", "eta_gen", 0.85, 0.95, "abs", "B",
     "ASSUMED value; +/-0.05 absolute"),
    ("Initial SOC", None, 0.05, 0.35, "abs", "B",
     "Study choice: baseline 0.20 +/-0.15"),
    ("Battery temperature", None, 10.0, 40.0, "abs", "B",
     "Study choice: baseline 25 C +/-15 C"),
    ("Supercap capacitance (C only)", "C_sc", 0.7, 1.3, "scale", "C",
     "ASSUMED value; +/-30%; affects C only"),
]


def kj(x):
    return x / 1e3


def check_energy(res, label):
    closure = abs(res["wheel_braking_J"] - (res["friction_J"] + res["wheel_regen_J"]))
    if closure > 1e-3:
        raise AssertionError(f"{label}: braking work != friction + regen (off by {closure:.6f} J)")
    if res["electrical_J"] > res["wheel_regen_J"] + 1e-3:
        raise AssertionError(f"{label}: electrical regen exceeds wheel-side regen")
    if "cap_residual_J" in res and abs(res["cap_residual_J"]) >= 1.0:
        raise AssertionError(f"{label}: capacitor balance off by {res['cap_residual_J']:.6f} J")


def run_config(config, soc, temp, overrides=None):
    """Run B or C with temporary parameter overrides; always restore them."""
    overrides = overrides or {}
    original = {k: PARAMETERS[k]["value"] for k in overrides}
    try:
        for k, v in overrides.items():
            PARAMETERS[k]["value"] = v
        runner = run_b if config == "B" else run_c
        res = runner(initial_soc=soc, temperature_c=temp)
    finally:
        for k, v in original.items():
            PARAMETERS[k]["value"] = v
    check_energy(res, f"{config} run {overrides or 'baseline'} SOC={soc} T={temp}")
    return kj(res["total_battery_J"])


def baseline_values():
    return {
        "B": run_config("B", BASE_SOC, BASE_TEMP),
        "C": run_config("C", BASE_SOC, BASE_TEMP),
    }


def run_tornado():
    base = baseline_values()
    rows = []
    for label, key, low, high, mode, config, note in SPECS:
        ref = base[config]
        if key is None and label == "Initial SOC":
            low_val, high_val = low, high
            e_low = run_config(config, low_val, BASE_TEMP)
            e_high = run_config(config, high_val, BASE_TEMP)
        elif key is None:  # temperature
            low_val, high_val = low, high
            e_low = run_config(config, BASE_SOC, low_val)
            e_high = run_config(config, BASE_SOC, high_val)
        else:
            base_value = PARAMETERS[key]["value"]
            if mode == "scale":
                low_val, high_val = base_value * low, base_value * high
            else:
                low_val, high_val = low, high
            e_low = run_config(config, BASE_SOC, BASE_TEMP, {key: low_val})
            e_high = run_config(config, BASE_SOC, BASE_TEMP, {key: high_val})

        rows.append({
            "parameter": label,
            "config": config,
            "low_input": low_val,
            "high_input": high_val,
            "baseline_kJ": ref,
            "low_kJ": e_low,
            "high_kJ": e_high,
            "low_delta_kJ": e_low - ref,
            "high_delta_kJ": e_high - ref,
            "swing_kJ": abs(e_high - e_low),
            "note": note,
        })
    rows.sort(key=lambda r: r["swing_kJ"], reverse=True)
    return rows, base


def save_csv(rows, path="tornado_results.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    return path


def plot_tornado(rows, base, path="step10_tornado.png"):
    fig, ax = plt.subplots(figsize=(11, 6.5))
    names = []
    y = list(range(len(rows)))[::-1]  # largest swing at top

    extremes = [0.0]
    for r in rows:
        extremes += [r["low_delta_kJ"], r["high_delta_kJ"]]
    xmin = min(extremes) * 1.3 if min(extremes) < 0 else -0.5
    xmax = max(extremes) * 1.3 if max(extremes) > 0 else 0.5
    span = xmax - xmin

    for yi, r in zip(y, rows):
        lo, hi = r["low_delta_kJ"], r["high_delta_kJ"]
        ax.barh(yi, lo, color="#8A9BA8", height=0.55)
        ax.barh(yi, hi, color="#0FA3B1", height=0.55)

        if abs(lo) < 0.02 * span and abs(hi) < 0.02 * span:
            # Near-zero rows: one label, placed to the right, so nothing overlaps.
            ax.annotate(f"low {lo:+.3f} / high {hi:+.3f} kJ", (0, yi),
                        xytext=(8, 0), textcoords="offset points",
                        va="center", ha="left", fontsize=8)
        else:
            ax.annotate(f"{lo:+.3f}", (lo, yi), xytext=(-4 if lo < 0 else 4, 0),
                        textcoords="offset points", va="center",
                        ha="right" if lo < 0 else "left", fontsize=8)
            ax.annotate(f"{hi:+.3f}", (hi, yi), xytext=(-4 if hi < 0 else 4, 0),
                        textcoords="offset points", va="center",
                        ha="right" if hi < 0 else "left", fontsize=8)
        names.append(f"{r['parameter']} ({r['config']})\n{r['note']}")

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlim(xmin, xmax)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Change in battery-accepted energy vs baseline (kJ)")
    ax.set_title(
        "Tornado: battery-accepted energy, 0-40-0 km/h cycle\n"
        f"Baseline B = {base['B']:.3f} kJ (SOC 0.20, 25 C). "
        "Grey = low value, teal = high value."
    )
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    rows, base = run_tornado()
    print("STEP 10 - TORNADO | baseline B at SOC 0.20, 25 C | 0-40-0 km/h cycle")
    print(f"Baseline B battery energy: {base['B']:.3f} kJ | baseline C: {base['C']:.3f} kJ")
    print("-" * 104)
    print(f"{'Parameter':<32}{'Cfg':>4}{'Low in':>10}{'High in':>10}"
          f"{'Low dE':>11}{'High dE':>11}{'Swing':>10}  Note")
    print("-" * 104)
    for r in rows:
        print(f"{r['parameter']:<32}{r['config']:>4}{r['low_input']:>10.4g}{r['high_input']:>10.4g}"
              f"{r['low_delta_kJ']:>+11.4f}{r['high_delta_kJ']:>+11.4f}{r['swing_kJ']:>10.4f}  {r['note']}")
    print("\nAll energy checks passed for every run.")
    print("Saved:", save_csv(rows))
    print("Saved:", plot_tornado(rows, base))


if __name__ == "__main__":
    main()