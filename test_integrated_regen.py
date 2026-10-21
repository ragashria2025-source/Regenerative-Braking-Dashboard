
from integrated_regen import integrated_braking


def main():
    cases = [
        ("Normal battery", 0.20, 25.0),
        ("Nearly full battery", 0.95, 25.0),
        ("Cold battery", 0.20, -5.0),
    ]

    for name, soc, temperature in cases:
        result = integrated_braking(
            v=30.0,
            F_brake=12000.0,
            soc=soc,
            temperature_c=temperature,
            dt=1.0,
        )

        print(f"\n{name}")
        print("-" * 45)

        for key, value in result.items():
            print(f"{key}: {value:.4f}")

        assert abs(
            result["regen_force_N"]
            + result["friction_force_N"]
            - result["braking_demand_N"]
        ) < 1e-6

    print("\nALL INTEGRATION TESTS PASSED.")


if __name__ == "__main__":
    main()
