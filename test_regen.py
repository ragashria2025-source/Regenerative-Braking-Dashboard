
from regen_model import regenerative_braking
from parameters import PARAMETERS


def p(name):
    return PARAMETERS[name]["value"]


def check_power_conservation():
    """Motor-side power must never exceed wheel-side power during regen."""
    for v in (2.0, 10.0, 30.0):
        for F in (1000.0, 4000.0, 12000.0):
            r = regenerative_braking(v, F)
            wheel_power = r["F_regen_wheel_N"] * v
            assert r["P_mech_W"] <= wheel_power + 1e-6, (
                f"Energy created at v={v}, F={F}: motor {r['P_mech_W']:.1f} W > wheel {wheel_power:.1f} W"
            )
    print("POWER CONSERVATION PASSED.")


def main():
    F_brake = 4000.0

    low = regenerative_braking(2.0, F_brake)
    high = regenerative_braking(30.0, F_brake)
    no_brake = regenerative_braking(30.0, 0.0)

    print("\nTEST 1: LOW SPEED")
    for key, value in low.items():
        print(f"{key}: {value:.3f}")

    print("\nTEST 2: HIGH SPEED")
    for key, value in high.items():
        print(f"{key}: {value:.3f}")

    print("\nTEST 3: NO BRAKING DEMAND")
    print(no_brake)

    # Regen and friction forces must sum to the requested force.
    for result in (low, high):
        total = (
            result["F_regen_wheel_N"]
            + result["F_friction_N"]
        )
        assert abs(total - F_brake) < 1e-8

    assert low["T_regen_motor_Nm"] <= p("T_max")
    assert high["T_regen_motor_Nm"] <= p("T_max")
    assert low["P_mech_W"] <= p("P_max") + 1e-8
    assert high["P_mech_W"] <= p("P_max") + 1e-8

    assert no_brake["P_elec_W"] == 0.0
    assert no_brake["F_friction_N"] == 0.0

    print("\nTEST 4: MOTOR TORQUE AND POWER LIMITS")

    low_speed_hard_braking = regenerative_braking(2.0, 12000.0)
    high_speed_hard_braking = regenerative_braking(30.0, 12000.0)

    print("\nHard braking at low speed:")
    for key, value in low_speed_hard_braking.items():
        print(f"{key}: {value:.3f}")

    print("\nHard braking at high speed:")
    for key, value in high_speed_hard_braking.items():
        print(f"{key}: {value:.3f}")

    assert low_speed_hard_braking["T_regen_motor_Nm"] <= p("T_max") + 1e-8
    assert high_speed_hard_braking["P_mech_W"] <= p("P_max") + 1e-8

    assert abs(
        low_speed_hard_braking["F_regen_wheel_N"]
        + low_speed_hard_braking["F_friction_N"]
        - 12000.0
    ) < 1e-8

    assert abs(
        high_speed_hard_braking["F_regen_wheel_N"]
        + high_speed_hard_braking["F_friction_N"]
        - 12000.0
    ) < 1e-8
    check_power_conservation()
    print("\nALL REGEN TESTS PASSED.")


if __name__ == "__main__":
    main()
