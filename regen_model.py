
"""
Step 4: Regenerative braking model.

Inputs:
    v       : vehicle speed (m/s)
    F_brake : requested total wheel braking force (N)

Outputs:
    Dictionary containing motor speed, torque, power,
    regenerative wheel force, and remaining friction force.

Initial model assumptions:
    Constant motor torque and power limits.
    Constant gearbox and generator efficiencies.
"""

from parameters import PARAMETERS


def p(name):
    return PARAMETERS[name]["value"]


def regenerative_braking(v, F_brake):
    if v < 0 or F_brake < 0:
        raise ValueError("Speed and braking force must be non-negative.")

    r = p("r")
    G = p("G")
    T_max = p("T_max")
    P_max = p("P_max")
    eta_gear = p("eta_gear")
    eta_gen = p("eta_gen")

    # Requested motor speed in rad/s.
    omega = (v / r) * G

    # Requested wheel and motor torque.
    T_wheel_requested = F_brake * r
    # In regeneration, power flows wheel -> motor, so the gearbox reduces
    # the power reaching the motor: P_motor = eta_gear * P_wheel.
    T_motor_requested = T_wheel_requested * eta_gear / G

    # Motor torque limit from the constant-torque and constant-power envelope.
    if omega <= 1e-9:
        T_power_limit = float("inf")
    else:
        T_power_limit = P_max / omega

    T_regen_motor = min(
        T_motor_requested,
        T_max,
        T_power_limit
    )

    # Mechanical power absorbed by the motor.
    P_mech = T_regen_motor * omega

    # Electrical power generated.
    P_elec = P_mech * eta_gen

    # Convert motor torque back to the equivalent wheel force.
    F_regen_wheel = T_regen_motor * G / (eta_gear * r)

    # Regen cannot exceed the requested braking force.
    F_regen_wheel = min(F_regen_wheel, F_brake)

    # Remaining braking demand is supplied by friction brakes.
    F_friction = max(F_brake - F_regen_wheel, 0.0)

    return {
        "omega_motor_rad_s": omega,
        "T_motor_requested_Nm": T_motor_requested,
        "T_regen_motor_Nm": T_regen_motor,
        "T_wheel_requested_Nm": T_wheel_requested,
        "P_mech_W": P_mech,
        "P_elec_W": P_elec,
        "F_regen_wheel_N": F_regen_wheel,
        "F_friction_N": F_friction,
    }
