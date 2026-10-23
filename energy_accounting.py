"""
Step 6 energy audit, on the fine-grid cycle (dt = 0.01 s).

Checks:
  1. electrical regen <= wheel-side regen         (no energy created)
  2. wheel braking work = friction + wheel regen  (exact by construction)
  3. kinetic energy lost = braking + aero + rolling work  (physics closure)
"""

from fine_cycle_runs import build_fine_grid, run_b, p


def audit():
    times, speed, braking, F, dts = build_fine_grid(0.01)
    b = run_b()
    m, Cd, A, rho, Crr, g = p("m"), p("Cd"), p("A"), p("rho"), p("Crr"), p("g")

    ke_lost = aero = rolling = 0.0
    for i, v in enumerate(speed):
        if i + 1 >= len(speed) or not braking[i] or F[i] <= 0:
            continue
        v_next = speed[i + 1]
        d = dts[i]
        vavg = 0.5 * (v + v_next)
        ke_lost += 0.5 * m * (v * v - v_next * v_next)
        aero += 0.5 * rho * Cd * A * vavg**3 * d
        rolling += Crr * m * g * vavg * d

    return {
        "wheel_braking_J": b["wheel_braking_J"],
        "wheel_regen_J": b["wheel_regen_J"],
        "electrical_J": b["electrical_J"],
        "friction_J": b["friction_J"],
        "battery_accepted_J": b["battery_accepted_J"],
        "ke_lost_J": ke_lost,
        "aero_J": aero,
        "rolling_J": rolling,
    }


def main():
    a = audit()
    print("ENERGY AUDIT, fine grid (dt = 0.01 s), SOC 0.20, 25 C, configuration B")
    print("=" * 72)
    for k in ("wheel_braking_J", "wheel_regen_J", "electrical_J", "battery_accepted_J",
              "friction_J", "ke_lost_J", "aero_J", "rolling_J"):
        print(f"{k:22s}: {a[k] / 1e3:10.3f} kJ")
    print("-" * 72)

    c1 = a["electrical_J"] <= a["wheel_regen_J"] + 1e-6
    c2 = abs(a["wheel_braking_J"] - (a["friction_J"] + a["wheel_regen_J"])) < 1e-6
    residual = a["ke_lost_J"] - (a["wheel_braking_J"] + a["aero_J"] + a["rolling_J"])
    tol = 1e-3 * a["ke_lost_J"]
    c3 = abs(residual) < tol
    print(f"Check 1 electrical <= wheel regen      : {c1}")
    print(f"Check 2 braking = friction + regen     : {c2}")
    print(f"Check 3 kinetic closure residual       : {residual:.3f} J "
          f"(tolerance {tol:.1f} J, 0.1% of KE lost)  -> {c3}")
    assert c1 and c2 and c3, "Energy audit failed"
    print("\nAll three audit checks passed.")


if __name__ == "__main__":
    main()
