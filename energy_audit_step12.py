"""
Step 12: final energy audit for configurations A, B and C.

Runs each configuration on the same cycle, SOC and temperature as Step 6
(0-40-0 km/h toy cycle, SOC 0.20, 25 C), then checks:

  1. Per-step force split: regen + friction == braking demand, friction >= 0,
     regen <= demand. Checked on every regen call.
  2. Wheel braking energy = friction + wheel regen.
  3. Battery accepted energy = battery loss + battery stored.
  4. Full balance, per configuration:
       wheel braking = friction + gear/generator loss + battery loss
                       + battery stored + converter losses + ESR losses
                       + wasted (A only) + energy left in capacitor
  5. Residual must be within 0.1% of wheel braking energy.

Run with run_audit_toy.py (it forces DRIVE_CYCLE = "toy").
"""

import fine_cycle_runs as fcr
from fine_cycle_runs import run_a, run_b, run_c
from parameters import PARAMETERS

TOL_FRACTION = 0.001          # 0.1 % of wheel braking energy
FORCE_TOL_N = 1e-6

_real_regen = fcr.regenerative_braking
_step_checks = {"calls": 0, "max_friction_neg_N": 0.0, "max_regen_excess_N": 0.0,
                "max_split_error_N": 0.0}


def _checked_regen(v, F_brake):
    """Wrap the regen call so the friction assertion runs at every time step."""
    r = _real_regen(v, F_brake)
    regen = r["F_regen_wheel_N"]
    fric = r["F_friction_N"]
    _step_checks["calls"] += 1
    _step_checks["max_friction_neg_N"] = max(_step_checks["max_friction_neg_N"], -fric)
    _step_checks["max_regen_excess_N"] = max(_step_checks["max_regen_excess_N"], regen - F_brake)
    _step_checks["max_split_error_N"] = max(_step_checks["max_split_error_N"],
                                            abs(regen + fric - F_brake))
    assert fric >= -FORCE_TOL_N, f"negative friction force {fric} N at v={v}"
    assert regen <= F_brake + FORCE_TOL_N, f"regen {regen} N exceeds demand {F_brake} N"
    assert abs(regen + fric - F_brake) < FORCE_TOL_N, "regen + friction != demand"
    return r


fcr.regenerative_braking = _checked_regen


def kj(x):
    return x / 1e3


def audit_one(name, o):
    """Balance one configuration. Gear/generator loss and the electrical chain are
    computed from the efficiencies and the accumulators, not left as leftovers."""
    W = o["wheel_braking_J"]
    Fr = o["friction_J"]
    Rg = o["wheel_regen_J"]
    elec = o["electrical_J"]
    eta = PARAMETERS["eta_gear"]["value"] * PARAMETERS["eta_gen"]["value"]
    bat_loss = o["battery_loss_J"]
    bat_stored = o["battery_stored_J"]
    bat_stop = o.get("stop_only_battery_J", o["battery_accepted_J"])
    wasted = o.get("wasted_J", 0.0)
    cap_left = o.get("cap_left_J", 0.0)
    cap_in = o.get("cap_in_J", 0.0)
    cap_conv_in = o.get("cap_conv_in_J", 0.0)
    cap_conv_out = o.get("cap_conv_out_J", 0.0)
    cap_esr = o.get("cap_esr_in_J", 0.0) + o.get("cap_esr_out_J", 0.0)

    gear_gen = Rg * (1.0 - eta)                                   # from efficiencies
    c_eta = elec - eta * Rg                                       # generator vs efficiency
    c_chain = elec - (bat_stop + wasted + cap_in + cap_conv_in)   # electrical to sinks
    c_split = W - (Fr + Rg)                                       # wheel work split
    c_batt = o["battery_accepted_J"] - (bat_loss + bat_stored)    # battery split

    rhs = (Fr + gear_gen + bat_loss + bat_stored + cap_conv_in + cap_conv_out
           + cap_esr + wasted + cap_left)
    residual = W - rhs
    tol = TOL_FRACTION * W
    checks_ok = (abs(c_eta) <= tol and abs(c_chain) <= tol
                 and abs(c_split) < 1e-6 and abs(c_batt) < 1e-6)
    return {
        "name": name, "W": W, "friction": Fr, "gear_gen": gear_gen,
        "battery_loss": bat_loss, "battery_stored": bat_stored,
        "converter": cap_conv_in + cap_conv_out, "esr": cap_esr, "wasted": wasted,
        "cap_left": cap_left, "residual": residual, "tol": tol,
        "c_eta": c_eta, "c_chain": c_chain, "c_split": c_split, "c_batt": c_batt,
        "pass": abs(residual) <= tol and checks_ok,
    }


def main():
    results = [audit_one("A", run_a()), audit_one("B", run_b()), audit_one("C", run_c())]

    print("STEP 12 ENERGY AUDIT | 0-40-0 toy cycle | SOC 0.20 | 25 C")
    print("=" * 96)
    cols = ["friction", "gear_gen", "battery_loss", "battery_stored", "converter",
            "esr", "wasted", "cap_left"]
    print(f"{'config':8s}{'W_brake':>12s}" + "".join(f"{c:>15s}" for c in cols)
          + f"{'residual':>12s}{'tol':>10s}  result")
    for r in results:
        print(f"{r['name']:8s}{kj(r['W']):12.4f}"
              + "".join(f"{kj(r[c]):15.4f}" for c in cols)
              + f"{r['residual']:12.4f}{kj(r['tol']):10.4f}  "
              + ("PASS" if r["pass"] else "FAIL"))
    print("(energies in kJ; residual in J)")
    print("-" * 96)
    for r in results:
        print(f"{r['name']}: balance residual {r['residual']:+.3f} J "
              f"({100 * r['residual'] / r['W']:+.4f} % of wheel braking)")
        print(f"    generator vs efficiency: {r['c_eta']:+.3f} J; "
              f"electrical to sinks: {r['c_chain']:+.3f} J; "
              f"wheel split: {r['c_split']:.1e} J; battery split: {r['c_batt']:.1e} J")
    print("-" * 96)
    s = _step_checks
    print(f"Per-step force checks: {s['calls']} regen calls, all passed. "
          f"Max friction deficit {s['max_friction_neg_N']:.2e} N, "
          f"max regen excess {s['max_regen_excess_N']:.2e} N, "
          f"max split error {s['max_split_error_N']:.2e} N.")
    all_ok = all(r["pass"] for r in results)
    print("=" * 96)
    print("ALL CONFIGURATIONS PASS THE STEP 12 AUDIT." if all_ok else "AUDIT FAILED.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())