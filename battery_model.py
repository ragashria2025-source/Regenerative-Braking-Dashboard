
"""
Step 5: Simplified EV Battery Model

Convention:
- Charging current is positive.
- SOC increases during charging.
- Terminal voltage = OCV + I * R0.
- Below 0 degC, charging is disabled as a conservative assumption.
"""

from parameters import PARAMETERS


def p(name):
    return PARAMETERS[name]["value"]


def battery_ocv(soc):
    """Estimate pack open-circuit voltage from SOC."""
    if not 0.0 <= soc <= 1.0:
        raise ValueError("SOC must be between 0 and 1.")

    # Approximate 96-series-cell equivalent battery.
    n_series = 96
    cell_ocv = 3.0 + 1.2 * soc
    return n_series * cell_ocv


def battery_resistance(temperature_c):
    """Estimate internal resistance; resistance rises in cold weather."""
    if temperature_c < -20 or temperature_c > 60:
        raise ValueError("Temperature outside model range.")

    # Assumed temperature relationship, not measured vehicle data.
    r25 = p("R0_25")
    factor = 1.0 + 0.025 * max(25.0 - temperature_c, 0.0)
    return r25 * factor


def charge_battery(soc, temperature_c, requested_power_w, dt):
    """
    Calculate battery response to requested charging power.

    Returns charging current, voltage, accepted power, losses and new SOC.
    """
    if not 0.0 <= soc <= 1.0:
        raise ValueError("SOC must be between 0 and 1.")
    if requested_power_w < 0 or dt <= 0:
        raise ValueError("Power must be non-negative and dt must be positive.")

    v_oc = battery_ocv(soc)
    r0 = battery_resistance(temperature_c)

    # Approximate pack voltage ceiling from 96 equivalent series cells.
    v_max = 96 * 4.2

    # Approximate battery capacity in Ah from energy / nominal voltage.
    capacity_ah = p("Q") * 1000.0 / p("V_nom")

    # Assumed conservative limits.
    i_max = p("i_max")

    # No charging above the SOC limit or below freezing.
    if soc >= 0.99 or temperature_c < 0.0:
        i_charge = 0.0
    else:
       
        # Solve P = I * (OCV + I * R0), so accepted terminal
        # power cannot exceed the requested charging power.
        if requested_power_w == 0:
            i_requested = 0.0
        else:
            i_requested = (
                2.0 * requested_power_w
                / (
                    v_oc
                    + (v_oc**2 + 4.0 * r0 * requested_power_w) ** 0.5
                )
            )

        # Keep terminal voltage within the pack voltage ceiling.
        i_voltage_limit = max((v_max - v_oc) / r0, 0.0)

        i_charge = min(i_requested, i_max, i_voltage_limit)


    v_terminal = min(v_oc + i_charge * r0, v_max)
    p_terminal = v_terminal * i_charge
    p_stored = v_oc * i_charge
    p_loss = i_charge ** 2 * r0

    # SOC rises with positive charging current.
    soc_new = min(soc + i_charge * dt / (3600.0 * capacity_ah), 1.0)

    return {
        "SOC_initial": soc,
        "SOC_new": soc_new,
        "temperature_C": temperature_c,
        "OCV_V": v_oc,
        "resistance_ohm": r0,
        "charging_current_A": i_charge,
        "terminal_voltage_V": v_terminal,
        "accepted_terminal_power_W": p_terminal,
        "stored_power_W": p_stored,
        "battery_loss_W": p_loss,
        "voltage_limit_V": v_max,
    }
