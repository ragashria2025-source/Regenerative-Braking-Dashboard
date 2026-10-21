"""
Step 8: SOC sensitivity for A, B and C on the same 0-40-0 km/h test cycle.

Sweeps starting SOC at 25 C and records battery-accepted energy for each
configuration. Each point is one full run and must pass the energy checks.

Outputs:
  step8_soc_sweep.csv          - all numbers, one row per SOC
  step8_soc_battery_energy.png - battery-accepted energy against SOC
  step8_soc_gap.png            - C minus B and B minus A against SOC (labelled)

Run:  py sweep_soc_abc.py
"""

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import drive_cycle

# Same cycle as Step 6 and Step 7. Set BEFORE the runs.
drive_cycle.DRIVE_CYCLE = "toy"

from fine_cycle_runs import run_a, run_b, run_c  # noqa: E402

SOC_VALUES = [0.20, 0.50, 0.80, 0.90, 0.95]
TEMPERATURE_C = 25.0


def kj(x):
    return x / 1e3


def check_energy(res, label):
    """Per-run checks: the same bookkeeping as energy_accounting.py, plus the capacitor balance."""
    closure = abs(res["wheel_braking_J"] - (res["friction_J"] + res["wheel_regen_J"]))
    if closure > 1e-3:
        raise AssertionError(f"{label}: braking work != friction + regen (off by {closure:.6f} J)")
    if res["electrical_J"] > res["wheel_regen_J"] + 1e-3:
        raise AssertionError(f"{label}: electrical regen exceeds wheel-side regen")
    if "cap_residual_J" in res and abs(res["cap_residual_J"]) >= 1.0:
        raise AssertionError(f"{label}: capacitor balance off by {res['cap_residual_J']:.6f} J")


def run_sweep():
    rows = []
    for soc in SOC_VALUES:
        a = run_a(initial_soc=soc, temperature_c=TEMPERATURE_C)
        b = run_b(initial_soc=soc, temperature_c=TEMPERATURE_C)
        c = run_c(initial_soc=soc, temperature_c=TEMPERATURE_C)
        check_energy(a, f"A at SOC {soc}")
        check_energy(b, f"B at SOC {soc}")
        check_energy(c, f"C at SOC {soc}")

        rows.append({
            "soc": soc,
            "A_battery_kJ": kj(a["total_battery_J"]),
            "B_battery_kJ": kj(b["total_battery_J"]),
            "C_stop_kJ": kj(c["stop_only_battery_J"]),
            "C_battery_kJ": kj(c["total_battery_J"]),
            "C_transfer_kJ": kj(c["transfer_J"]),
            "C_left_in_cap_kJ": kj(c["cap_left_J"]),
            "A_rejected_kJ": kj(a["wasted_J"]),
            "B_friction_kJ": kj(b["friction_J"]),
            "C_friction_kJ": kj(c["friction_J"]),
            "C_minus_B_kJ": kj(c["total_battery_J"] - b["total_battery_J"]),
            "B_minus_A_kJ": kj(b["total_battery_J"] - a["total_battery_J"]),
            "final_soc_C": c["final_soc"],
        })
    return rows


def save_csv(rows, path="step8_soc_sweep.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    return path


def plot_battery(rows, path="step8_soc_battery_energy.png"):
    soc = [r["soc"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(soc, [r["A_battery_kJ"] for r in rows], "o-", color="#8A9BA8", label="A  Baseline")
    ax.plot(soc, [r["B_battery_kJ"] for r in rows], "s-", color="#1B2A41", label="B  Adaptive")
    ax.plot(soc, [r["C_battery_kJ"] for r in rows], "^-", color="#0FA3B1",
            label="C  Adaptive + supercap (incl. transfer)")
    ax.set_xlabel("Starting SOC")
    ax.set_ylabel("Battery-accepted energy (kJ)")
    ax.set_title("SOC sensitivity: battery-accepted energy, 0-40-0 km/h cycle, 25 C")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left")
    fig.text(0.5, 0.01, "Test cycle only (0-40-0 km/h). Replace with UDDS before drawing conclusions.",
             ha="center", fontsize=9, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_gap(rows, path="step8_soc_gap.png"):
    """Grouped bars at evenly spaced SOC positions, every value printed.
    Left: full scale. Right: B minus A zoomed, because it is only ~0.1 kJ."""
    labels = [f"{r['soc']:.2f}" for r in rows]
    x = list(range(len(rows)))
    w = 0.38

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1.2, 1]})

    cmb = [r["C_minus_B_kJ"] for r in rows]
    bma = [r["B_minus_A_kJ"] for r in rows]

    ax1.bar([i - w / 2 for i in x], cmb, width=w, color="#0FA3B1", label="C minus B")
    ax1.bar([i + w / 2 for i in x], bma, width=w, color="#1B2A41", label="B minus A")
    for i, v in enumerate(cmb):
        ax1.annotate(f"{v:+.2f}", (i - w / 2, v), xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=8)
    for i, v in enumerate(bma):
        ax1.annotate(f"{v:+.2f}", (i + w / 2, v), xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=8)
    ax1.axhline(0, color="black", linewidth=0.8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_xlabel("Starting SOC")
    ax1.set_ylabel("Difference in battery-accepted energy (kJ)")
    ax1.set_title("Gap between configurations (full scale)")
    ax1.legend(loc="upper left", frameon=False)
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_axisbelow(True)

    ax2.bar(x, bma, width=0.5, color="#1B2A41")
    for i, v in enumerate(bma):
        ax2.annotate(f"{v:+.2f} kJ", (i, v), xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=9)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_xlabel("Starting SOC")
    ax2.set_ylabel("B minus A (kJ)")
    top = max(max(bma), 0.1)
    ax2.set_ylim(-0.02, top * 1.5)
    ax2.set_title("B minus A, zoomed")
    ax2.grid(axis="y", alpha=0.3)
    ax2.set_axisbelow(True)

    fig.suptitle("Step 8 gaps | 0-40-0 km/h test cycle | 25 C", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    rows = run_sweep()
    print(f"{'SOC':>5} | {'A':>9} {'B':>9} {'C':>9} | {'C-B':>8} {'B-A':>8} | "
          f"{'A rej':>7} {'C xfer':>7} {'C left':>7}")
    print("-" * 82)
    for r in rows:
        print(f"{r['soc']:5.2f} | {r['A_battery_kJ']:9.3f} {r['B_battery_kJ']:9.3f} "
              f"{r['C_battery_kJ']:9.3f} | {r['C_minus_B_kJ']:8.3f} {r['B_minus_A_kJ']:8.3f} | "
              f"{r['A_rejected_kJ']:7.3f} {r['C_transfer_kJ']:7.3f} {r['C_left_in_cap_kJ']:7.3f}")
    print("\nAll energy checks passed for every point.")
    print("Saved:", save_csv(rows))
    print("Saved:", plot_battery(rows))
    print("Saved:", plot_gap(rows))


if __name__ == "__main__":
    main()