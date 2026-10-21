"""
Step 3: Drive-Cycle Input

This module:
1. Creates a simple test driving cycle.
2. Converts speed from km/h to m/s.
3. Calculates acceleration.
4. Identifies braking periods.
5. Calculates the braking force required during the cycle.

Units:
    Time          : seconds
    Speed         : m/s
    Acceleration  : m/s^2
    Force         : N
"""

from parameters import PARAMETERS


def get_test_cycle():
    """
    Return a simple test driving cycle.

    The speed values are initially given in km/h
    and converted to m/s.
    """

    time = [
        0, 1, 2, 3, 4,
        5, 6, 7, 8, 9, 10
    ]

    speed_kmh = [
        0, 10, 20, 30, 40,
        40, 30, 20, 10, 0, 0
    ]

    # Convert km/h to m/s
    speed_ms = [v / 3.6 for v in speed_kmh]

    return time, speed_ms


def calculate_acceleration(time, speed):
    """
    Calculate acceleration from consecutive speed values.

    Formula:

        a = Δv / Δt
    """

    if len(time) != len(speed):
        raise ValueError(
            "Time and speed arrays must have the same length."
        )

    if len(time) < 2:
        raise ValueError(
            "At least two data points are required."
        )

    acceleration = []

    for i in range(len(time) - 1):

        dt = time[i + 1] - time[i]
        dv = speed[i + 1] - speed[i]

        if dt <= 0:
            raise ValueError(
                "Time values must increase."
            )

        a = dv / dt

        acceleration.append(a)

    # Keep the acceleration array the same length
    # as the speed array.
    acceleration.append(acceleration[-1])

    return acceleration


def identify_braking(acceleration, threshold=-0.05):
    """
    Identify points where the vehicle is decelerating.

    A point is considered a braking point when:

        acceleration < threshold
    """

    braking = []

    for a in acceleration:

        if a < threshold:
            braking.append(True)
        else:
            braking.append(False)

    return braking


def calculate_braking_force(time, speed, acceleration):
    """
    Calculate the mechanical braking force required
    by the vehicle during the drive cycle.

    The vehicle's rolling resistance and aerodynamic
    drag are already slowing the vehicle down.

    Therefore:

        F_brake = m|a| - F_roll - F_aero

    during deceleration.

    Returns:
        braking_force : list of braking forces in Newtons
    """

    # Get vehicle parameters from parameters.py
    m = PARAMETERS["m"]["value"]
    Crr = PARAMETERS["Crr"]["value"]
    Cd = PARAMETERS["Cd"]["value"]
    A = PARAMETERS["A"]["value"]
    rho = PARAMETERS["rho"]["value"]
    g = PARAMETERS["g"]["value"]

    braking_force = []

    for v, a in zip(speed, acceleration):

        # ---------------------------------------------
        # Rolling resistance
        # ---------------------------------------------

        if v > 0:
            F_roll = Crr * m * g
        else:
            F_roll = 0.0

        # ---------------------------------------------
        # Aerodynamic drag
        # ---------------------------------------------

        F_aero = 0.5 * rho * Cd * A * v**2

        # ---------------------------------------------
        # Required braking force
        # ---------------------------------------------

        if a < 0:

            F_brake = (
                m * abs(a)
                - F_roll
                - F_aero
            )

        else:

            F_brake = 0.0

        # Braking force cannot be negative
        F_brake = max(F_brake, 0.0)

        braking_force.append(F_brake)

    return braking_force


def main():

    # --------------------------------------------------
    # 1. Load the drive cycle
    # --------------------------------------------------

    time, speed = get_test_cycle()

    # --------------------------------------------------
    # 2. Calculate acceleration
    # --------------------------------------------------

    acceleration = calculate_acceleration(
        time,
        speed
    )

    # --------------------------------------------------
    # 3. Identify braking periods
    # --------------------------------------------------

    braking = identify_braking(
        acceleration
    )

    # --------------------------------------------------
    # 4. Calculate braking force
    # --------------------------------------------------

    braking_force = calculate_braking_force(
        time,
        speed,
        acceleration
    )

    # --------------------------------------------------
    # 5. Display results
    # --------------------------------------------------

    print("\nTEST DRIVE CYCLE")
    print("=" * 95)

    print(
        f"{'Time':>8}"
        f"{'Speed':>12}"
        f"{'Speed':>14}"
        f"{'Acceleration':>18}"
        f"{'Braking?':>12}"
        f"{'Brake Force':>16}"
    )

    print(
        f"{'(s)':>8}"
        f"{'(m/s)':>12}"
        f"{'(km/h)':>14}"
        f"{'(m/s²)':>18}"
        f"{'':>12}"
        f"{'(N)':>16}"
    )

    print("-" * 95)

    for t, v, a, is_braking, F_brake in zip(
        time,
        speed,
        acceleration,
        braking,
        braking_force
    ):

        speed_kmh = v * 3.6

        print(
            f"{t:8.1f}"
            f"{v:12.3f}"
            f"{speed_kmh:14.1f}"
            f"{a:18.3f}"
            f"{str(is_braking):>12}"
            f"{F_brake:16.2f}"
        )

    print("-" * 95)

    # --------------------------------------------------
    # 6. Summary
    # --------------------------------------------------

    braking_points = sum(braking)

    max_braking_force = max(braking_force)

    print("\nSUMMARY")
    print("=" * 45)

    print(f"Total data points     : {len(time)}")
    print(f"Total duration        : {time[-1]:.1f} s")
    print(f"Maximum speed         : {max(speed) * 3.6:.1f} km/h")
    print(f"Braking points        : {braking_points}")
    print(f"Maximum braking force : {max_braking_force:.2f} N")

    if braking_points > 0:
        print("Braking detected      : YES")
    else:
        print("Braking detected      : NO")


if __name__ == "__main__":
    main()
