
"""
Step 2: Longitudinal vehicle model.
Reference parameters are loaded from parameters.py.
Speed: m/s, force: N, time: s, acceleration: m/s^2.
"""

from parameters import PARAMETERS


def get_value(name):
    return PARAMETERS[name]["value"]


def step_vehicle(v, F_brake, dt):
    """
    Advance vehicle speed by one Euler time step.

    v       : current speed (m/s)
    F_brake : commanded braking force (N), non-negative
    dt      : time step (s)

    Returns:
    v_new   : updated speed (m/s)
    a       : acceleration (m/s^2), negative while slowing
    """

    if v < 0 or F_brake < 0 or dt <= 0:
        raise ValueError("Speed and braking force must be non-negative; dt must be positive.")

    m = get_value("m")
    Crr = get_value("Crr")
    Cd = get_value("Cd")
    A = get_value("A")
    rho = get_value("rho")
    g = get_value("g")

    # Resistive forces oppose forward motion only.
    if v > 0:
        F_roll = Crr * m * g
        F_aero = 0.5 * rho * Cd * A * v**2
    else:
        F_roll = 0.0
        F_aero = 0.0

    # Net acceleration before enforcing the zero-speed boundary.
    a = -(F_roll + F_aero + F_brake) / m

    # Euler update; do not allow reverse motion.
    v_new = max(v + a * dt, 0.0)

    # If the vehicle reaches rest during this step, report
    # average acceleration over the step rather than continued deceleration.
    if v_new == 0.0 and v > 0.0:
        a = -v / dt

    return v_new, a


def simulate(initial_speed, F_brake, duration, dt=0.01):
    """Simulate vehicle speed and acceleration over time."""

    if duration <= 0 or dt <= 0:
        raise ValueError("Duration and dt must be positive.")

    steps = round(duration / dt)
    if abs(steps * dt - duration) > 1e-9:
        raise ValueError("Duration must be an exact multiple of dt.")

    time = [0.0]
    speed = [initial_speed]
    acceleration = []

    v = initial_speed

    for i in range(steps):
        v, a = step_vehicle(v, F_brake, dt)
        acceleration.append(a)
        time.append((i + 1) * dt)
        speed.append(v)

    return time, speed, acceleration
