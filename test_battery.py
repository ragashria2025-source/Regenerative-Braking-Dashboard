
from battery_model import charge_battery


def show_test(title, result):
    print(f"\n{title}")
    print("-" * 45)

    for key, value in result.items():
        print(f"{key}: {value:.4f}")


def main():
    # Same 100 kW requested charging power in each test.
    low_soc = charge_battery(
        soc=0.20,
        temperature_c=25.0,
        requested_power_w=100000.0,
        dt=10.0,
    )

    high_soc = charge_battery(
        soc=0.95,
        temperature_c=25.0,
        requested_power_w=100000.0,
        dt=10.0,
    )

    cold = charge_battery(
        soc=0.20,
        temperature_c=-5.0,
        requested_power_w=100000.0,
        dt=10.0,
    )

    show_test("TEST 1: 20% SOC, 25 C", low_soc)
    show_test("TEST 2: 95% SOC, 25 C", high_soc)
    show_test("TEST 3: 20% SOC, -5 C", cold)

    # Basic validity checks.
    for result in (low_soc, high_soc, cold):
        assert 0.0 <= result["SOC_new"] <= 1.0
        assert result["charging_current_A"] >= 0.0
        assert result["terminal_voltage_V"] <= result["voltage_limit_V"] + 1e-8

        # Terminal electrical power = stored chemical power + resistive loss.
        assert abs(
            result["accepted_terminal_power_W"]
            - result["stored_power_W"]
            - result["battery_loss_W"]
        ) < 1e-6

    assert low_soc["charging_current_A"] > 0.0
    assert cold["charging_current_A"] == 0.0

    print("\nALL BATTERY TESTS PASSED.")


if __name__ == "__main__":
    main()
