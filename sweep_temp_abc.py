"""
Step 9: Temperature sensitivity for A, B and C on the 0-40-0 km/h test cycle.

Temperatures from the plan: 40, 25, 10 and -5 C, at a fixed mid SOC of 0.50.
Every point is one full run and must pass the energy checks.

Outputs:
  step9_temp_sweep.csv                  - all numbers, one row per temperature
  step9_temp_battery_energy.png         - battery-accepted energy against temperature
  step9_temp_capacitor_stranded.png     - C: transferred vs left in capacitor (labelled)

Run:  py sweep_temp_abc.py
"""

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import drive_cycle

# Same cycle as Step 6, 7 and 8. Set BEFORE the runs.
drive_cycle.DRIVE_CYCLE = "toy"

from fine_cycle_runs import run_a, run_b, run_c  # noqa: E402

TEMPERATURES_C = [40.0, 25.0, 10.0, -5.0]
INITIAL_SOC = 0.50


def kj(joules):
    return joules / 1000.0


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
    for temp in TEMPERATURES_C:
        a = run_a(initial_soc=INITIAL_SOC, temperature_c=temp)
        b = run_b(initial_soc=INITIAL_SOC, temperature_c=temp)
        c = run_c(initial_soc=INITIAL_SOC, temperature_c=temp)
        check_energy(a, f"A at {temp:g} C")
        check_energy(b, f"B at {temp:g} C")
        check_energy(c, f"C at {temp:g} C")

        rows.append({
            "temperature_C": temp,
            "initial_SOC": INITIAL_SOC,
            "A_battery_accepted_kJ": kj(a["total_battery_J"]),
            "B_battery_accepted_kJ": kj(b["total_battery_J"]),
            "C_battery_accepted_total_kJ": kj(c["total_battery_J"]),
            "C_battery_accepted_during_stop_kJ": kj(c["stop_only_battery_J"]),
            "C_capacitor_transfer_to_battery_kJ": kj(c["transfer_J"]),
            "C_energy_left_in_capacitor_kJ": kj(c["cap_left_J"]),
            "C_capacitor_energy_balance_residual_J": c["cap_residual_J"],
            "C_minus_B_battery_energy_kJ": kj(c["total_battery_J"] - b["total_battery_J"]),
            "B_minus_A_battery_energy_kJ": kj(b["total_battery_J"] - a["total_battery_J"]),
            "A_battery_rejected_kJ": kj(a["wasted_J"]),
            "A_final_SOC": a["final_soc"],
            "B_final_SOC": b["final_soc"],
            "C_final_SOC": c["final_soc"],
        })
    return rows


def save_csv(rows, path="step9_temp_sweep.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    return path


def plot_battery_energy(rows, path="step9_temp_battery_energy.png"):
    temps = [r["temperature_C"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(temps, [r["A_battery_accepted_kJ"] for r in rows], "o-", color="#8A9BA8", label="A  Baseline")
    ax.plot(temps, [r["B_battery_accepted_kJ"] for r in rows], "s-", color="#1B2A41", label="B  Adaptive")
    ax.plot(temps, [r["C_battery_accepted_total_kJ"] for r in rows], "^-", color="#0FA3B1",
            label="C  Adaptive + supercap (incl. transfer)")
    ax.set_xlabel("Battery temperature (C)")
    ax.set_ylabel("Battery-accepted energy (kJ)")
    ax.set_title("Temperature sensitivity at initial SOC = 0.50, 0-40-0 km/h cycle")
    ax.set_xticks(temps)
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_capacitor_stranded(rows, path="step9_temp_capacitor_stranded.png"):
    """Grouped bars at evenly spaced temperatures, every value printed."""
    labels = [f"{r['temperature_C']:g} C" for r in rows]
    x = list(range(len(rows)))
    w = 0.38
    transfer = [r["C_capacitor_transfer_to_battery_kJ"] for r in rows]
    stranded = [r["C_energy_left_in_capacitor_kJ"] for r in rows]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar([i - w / 2 for i in x], transfer, width=w, color="#0FA3B1", label="Transferred to battery")
    ax.bar([i + w / 2 for i in x], stranded, width=w, color="#F5B041", label="Left in capacitor")
    for i, v in enumerate(transfer):
        ax.annotate(f"{v:.2f}", (i - w / 2, v), xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=9)
    for i, v in enumerate(stranded):
        ax.annotate(f"{v:.2f}", (i + w / 2, v), xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Battery temperature")
    ax.set_ylabel("Energy (kJ)")
    top = max(max(transfer), max(stranded), 1.0)
    ax.set_ylim(0, top * 1.15)
    ax.set_title("Configuration C: capacitor energy after the stop (SOC 0.50)")
    ax.legend(loc="upper right", frameon=False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    rows = run_sweep()
    print("STEP 9 - TEMPERATURE SENSITIVITY | initial SOC = 0.50 | 0-40-0 km/h cycle")
    print("Energy values in kJ")
    print("Temp |       A |       B | C total | C transfer | C cap left | cap residual (J)")
    print("-" * 83)
    for r in rows:
        print(f"{r['temperature_C']:>4.0f} | {r['A_battery_accepted_kJ']:>7.3f} | "
              f"{r['B_battery_accepted_kJ']:>7.3f} | {r['C_battery_accepted_total_kJ']:>7.3f} | "
              f"{r['C_capacitor_transfer_to_battery_kJ']:>10.3f} | "
              f"{r['C_energy_left_in_capacitor_kJ']:>10.3f} | "
              f"{r['C_capacitor_energy_balance_residual_J']:>14.6f}")
    print("\nAll energy checks passed for every point.")
    print("\nSaved:", save_csv(rows))
    print("Saved:", plot_battery_energy(rows))
    print("Saved:", plot_capacitor_stranded(rows))
    print("\nNote: charging is disabled below 0 C in the battery model, so at -5 C nothing reaches "
          "the battery and C's energy stays in the capacitor.")


if __name__ == "__main__":
    main()