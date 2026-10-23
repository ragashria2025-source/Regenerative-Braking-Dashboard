"""
Supercapacitor buffer model (configuration C helpers).

Energy in the capacitor: E = 1/2 C V^2.
Only the window between V_min and V_max is usable.
Series resistance R causes losses of I^2 R on both charge and discharge.
Converter efficiencies apply on each side of the capacitor.
"""

from parameters import PARAMETERS


def p(name):
    return PARAMETERS[name]["value"]


def cap_energy(V):
    return 0.5 * p("C_sc") * V**2


def cap_voltage(E):
    return (2.0 * max(E, 0.0) / p("C_sc")) ** 0.5


def usable_window_J():
    return cap_energy(p("V_sc_max")) - cap_energy(p("V_sc_min"))


def max_charge_power(energy_headroom_J, dt, V):
    """
    Largest power p (into the capacitor terminals) such that the net energy
    stored over dt, p*dt - (p/V)^2*R*dt, does not exceed energy_headroom_J.
    Solves (R/V^2) p^2 - p + a = 0 with a = headroom / dt.
    """
    R = p("R_sc")
    a = energy_headroom_J / dt
    if a <= 0 or V <= 0:
        return 0.0
    disc = 1.0 - 4.0 * R * a / V**2
    if disc < 0:
        return p("P_sc_max")
    return min(p("P_sc_max"), (V**2 / (2.0 * R)) * (1.0 - disc**0.5))


def max_discharge_power(energy_available_J, dt, V):
    """
    Largest power p (out of the capacitor terminals) such that the energy
    drawn over dt, p*dt + (p/V)^2*R*dt, does not exceed energy_available_J.
    Solves (R/V^2) p^2 + p - a = 0 with a = available / dt.
    """
    R = p("R_sc")
    a = energy_available_J / dt
    if a <= 0 or V <= 0:
        return 0.0
    return min(p("P_sc_max"), (V**2 / (2.0 * R)) * ((1.0 + 4.0 * R * a / V**2) ** 0.5 - 1.0))
