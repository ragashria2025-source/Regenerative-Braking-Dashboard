"""
Step 7: Final A/B/C graphs on the SAME 0-40-0 km/h test cycle used in Step 6.

The script forces the toy cycle, checks the numbers against the Step 6 table,
and then writes two figures:

  step7_abc_battery_energy.png     battery energy (absolute) + gain vs A
  step7_abc_energy_breakdown.png   wheel braking split (full scale) + small flows (zoomed)

Run:  py plot_step7_abc.py
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

import drive_cycle

# Step 6 and Step 7 must use the same cycle. Set it BEFORE the runs.
drive_cycle.DRIVE_CYCLE = "toy"

from fine_cycle_runs import run_a, run_b, run_c  # noqa: E402


COLORS = {"A": "#8A9BA8", "B": "#1B2A41", "C": "#0FA3B1"}
NAMES = ["A  Baseline", "B  Adaptive", "C  Adaptive + supercap"]

# Step 6 table (kJ), used as a check so the graphs cannot drift from it.
STEP6_TABLE = {
    "stop":     (103.560, 103.560, 103.560),
    "total":    (103.560, 103.560, 103.831),
    "friction": (0.127, 0.346, 0.000),
}
TOL_KJ = 0.001


def kj(x):
    return x / 1000.0


def collect():
    runs = {"A": run_a(), "B": run_b(), "C": run_c()}
    data = {}
    for k, r in runs.items():
        data[k] = {
            "stop": kj(r["stop_only_battery_J"]),
            "total": kj(r["total_battery_J"]),
            "transfer": kj(r["transfer_J"]),
            "friction": kj(r["friction_J"]),
            "cap_left": kj(r["cap_left_J"]),
            "wheel": kj(r["wheel_braking_J"]),
            "wasted": kj(r["wasted_J"]),
        }
    return data


def check_against_step6(d):
    for i, k in enumerate(["A", "B", "C"]):
        for key in ("stop", "total", "friction"):
            want = STEP6_TABLE[key][i]
            got = d[k][key]
            if abs(got - want) > TOL_KJ:
                raise SystemExit(
                    f"MISMATCH {k} {key}: got {got:.3f} kJ, Step 6 table {want:.3f} kJ. "
                    "Check drive cycle and code version before plotting."
                )
    print("Check passed: numbers match the Step 6 table.")


def plot_battery_energy(d, path="step7_abc_battery_energy.png"):
    keys = ["A", "B", "C"]
    stop = [d[k]["stop"] for k in keys]
    total = [d[k]["total"] for k in keys]
    gain = [d[k]["total"] - d["A"]["total"] for k in keys]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [1.1, 1]})
    x = list(range(3))

    # Left: absolute battery energy, axis from zero.
    ax1.bar(x, stop, color=[COLORS[k] for k in keys], width=0.55, label="Stop-only battery energy")
    transfer = [t - s for t, s in zip(total, stop)]
    ax1.bar(x, transfer, bottom=stop, color="white", edgecolor=COLORS["C"],
            hatch="///", width=0.55, label="Capacitor-to-battery transfer")
    for i, v in enumerate(total):
        ax1.annotate(f"{v:.2f} kJ", (i, v), xytext=(0, 5), textcoords="offset points",
                     ha="center", fontsize=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(NAMES, fontsize=9)
    ax1.set_ylabel("Battery-accepted energy (kJ)")
    ax1.set_ylim(0, max(total) * 1.15)
    ax1.set_title("Battery energy (axis from zero)")
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=8)
    ax1.grid(axis="y", alpha=0.25)
    ax1.set_axisbelow(True)

    # Right: the actual gap, magnified.
    ax2.bar(x, gain, color=[COLORS[k] for k in keys], width=0.55)
    for i, g in enumerate(gain):
        ax2.annotate(f"{g:+.2f} kJ", (i, g), xytext=(0, 4), textcoords="offset points",
                     ha="center", fontsize=10)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(NAMES, fontsize=9)
    ax2.set_ylabel("Gain relative to A (kJ)")
    top = max(max(gain), 0.1)
    ax2.set_ylim(-0.05, top * 1.6)
    ax2.set_title("Gain vs A (magnified, zero-based)")
    ax2.grid(axis="y", alpha=0.25)
    ax2.set_axisbelow(True)

    fig.suptitle(
        "A/B/C battery energy | 0-40-0 km/h test cycle | SOC 0.20 | 25 C\n"
        "C total includes capacitor transfer after the stop",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_breakdown(d, path="step7_abc_energy_breakdown.png"):
    keys = ["A", "B", "C"]
    x = list(range(3))

    # ---- Left panel: full-scale stacked split of wheel braking work ----
    segments = [
        ("Battery accepted (stop)", [d[k]["stop"] for k in keys], "#1B2A41"),
        ("Capacitor transfer", [d[k]["total"] - d[k]["stop"] for k in keys], "#0FA3B1"),
        ("Friction braking", [d[k]["friction"] for k in keys], "#C0392B"),
        ("Battery rejected", [d[k]["wasted"] for k in keys], "#8E44AD"),
        ("Energy left in capacitor", [d[k]["cap_left"] for k in keys], "#F5B041"),
    ]
    wheel = [d[k]["wheel"] for k in keys]
    accounted = [sum(seg[1][i] for seg in segments) for i in range(3)]
    losses = [w - a for w, a in zip(wheel, accounted)]
    segments.append(("Drivetrain, generator and converter losses (residual)", losses, "#BDC3C7"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={"width_ratios": [1, 1]})

    bottom = [0.0, 0.0, 0.0]
    for label, vals, color in segments:
        ax1.bar(x, vals, bottom=bottom, color=color, width=0.55, label=label)
        bottom = [b + v for b, v in zip(bottom, vals)]

    for i, w in enumerate(wheel):
        ax1.annotate(f"wheel work {w:.2f} kJ", (i, w), xytext=(0, 5),
                     textcoords="offset points", ha="center", fontsize=9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(NAMES, fontsize=9)
    ax1.set_ylabel("Energy at the wheels (kJ)")
    ax1.set_ylim(0, max(wheel) * 1.15)
    ax1.set_title("Wheel braking energy, full scale")
    ax1.grid(axis="y", alpha=0.25)
    ax1.set_axisbelow(True)

    # ---- Right panel: small flows, zoomed, every value printed ----
    small = [
        ("Friction braking", "friction", "#C0392B"),
        ("Battery rejected", "wasted", "#8E44AD"),
        ("Capacitor transfer", None, "#0FA3B1"),
        ("Energy left in capacitor", "cap_left", "#F5B041"),
    ]

    def small_value(k, key):
        if key is None:
            return d[k]["total"] - d[k]["stop"]
        return d[k][key]

    width = 0.2
    n = len(small)
    all_vals = []
    for j, (label, key, color) in enumerate(small):
        offs = [xi + (j - (n - 1) / 2) * width for xi in x]
        vals = [small_value(k, key) for k in keys]
        all_vals.extend(vals)
        ax2.bar(offs, vals, width=width, color=color, label=label)
        for xo, v in zip(offs, vals):
            ax2.annotate(f"{v:.2f}", (xo, v), xytext=(0, 3), textcoords="offset points",
                         ha="center", fontsize=8)

    ax2.set_xticks(x)
    ax2.set_xticklabels(NAMES, fontsize=9)
    ax2.set_ylabel("Energy (kJ)")
    ax2.set_ylim(0, max(all_vals) * 1.3 if max(all_vals) > 0 else 1.0)
    ax2.set_title("Small flows, zoomed (values printed)")
    ax2.grid(axis="y", alpha=0.25)
    ax2.set_axisbelow(True)

    # One shared legend for both panels, placed under the figure.
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, 0.0), frameon=False, fontsize=8)
    fig.suptitle("Where the braking energy goes | 0-40-0 km/h test cycle | SOC 0.20 | 25 C",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0.12, 1, 0.93])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    d = collect()
    check_against_step6(d)

    print("\nBattery accepted, stop only (kJ):  A %.3f | B %.3f | C %.3f"
          % (d["A"]["stop"], d["B"]["stop"], d["C"]["stop"]))
    print("Battery accepted, incl. transfer:   A %.3f | B %.3f | C %.3f"
          % (d["A"]["total"], d["B"]["total"], d["C"]["total"]))
    print("Battery rejected (kJ):              A %.3f | B %.3f | C %.3f"
          % (d["A"]["wasted"], d["B"]["wasted"], d["C"]["wasted"]))

    print("\nSaved:", plot_battery_energy(d))
    print("Saved:", plot_breakdown(d))
    print("\nStep 7 graphs written. Labels and totals match the Step 6 table.")


if __name__ == "__main__":
    main()