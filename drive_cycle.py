"""
Drive-cycle input supporting the original toy cycle and EPA UDDS.

Units:
    time: seconds
    speed: m/s
    acceleration: m/s^2
    braking force: N

Default cycle: EPA UDDS, loaded from uddscol.txt.
Set DRIVE_CYCLE = "toy" to use the original short cycle.
"""

from pathlib import Path
from parameters import PARAMETERS

DRIVE_CYCLE = "toy"
UDDS_FILE = Path(__file__).resolve().parent / "uddscol.txt"


def get_test_cycle():
    """Return time (s) and speed (m/s) for the selected cycle."""

    if DRIVE_CYCLE.lower() == "toy":
        time = list(range(11))
        speed_kmh = [0, 10, 20, 30, 40, 40, 30, 20, 10, 0, 0]
        return time, [v / 3.6 for v in speed_kmh]

    if not UDDS_FILE.exists():
        raise FileNotFoundError(
            f"UDDS file not found: {UDDS_FILE}"
        )

    time = []
    speed_ms = []

    with UDDS_FILE.open("r", encoding="utf-8-sig") as file:
        for line in file:
            parts = line.strip().replace(",", " ").split()

            if len(parts) < 2:
                continue

            try:
                t = float(parts[0])
                speed_mph = float(parts[1])
            except ValueError:
                # Skip the text headings at the top of the file.
                continue

            time.append(t)
            speed_ms.append(speed_mph * 0.44704)

    if len(time) < 2:
        raise ValueError(
            "Not enough numeric data found in uddscol.txt."
        )

    if any(time[i + 1] <= time[i] for i in range(len(time) - 1)):
        raise ValueError("UDDS time values must increase strictly.")

    if any(v < 0 for v in speed_ms):
        raise ValueError("UDDS speed cannot be negative.")

    return time, speed_ms


def calculate_acceleration(time, speed):
    """Calculate acceleration using consecutive speed samples."""

    if len(time) != len(speed):
        raise ValueError("Time and speed arrays must have the same length.")

    if len(time) < 2:
        raise ValueError("At least two data points are required.")

    acceleration = []

    for i in range(len(time) - 1):
        dt = time[i + 1] - time[i]

        if dt <= 0:
            raise ValueError("Time values must increase.")

        acceleration.append((speed[i + 1] - speed[i]) / dt)

    acceleration.append(acceleration[-1])
    return acceleration


def identify_braking(acceleration, threshold=-0.05):
    """Identify decelerating samples."""
    return [a < threshold for a in acceleration]


def calculate_braking_force(time, speed, acceleration):
    """Estimate mechanical braking force after road-load resistance."""

    m = PARAMETERS["m"]["value"]
    Crr = PARAMETERS["Crr"]["value"]
    Cd = PARAMETERS["Cd"]["value"]
    A = PARAMETERS["A"]["value"]
    rho = PARAMETERS["rho"]["value"]
    g = PARAMETERS["g"]["value"]

    braking_force = []

    for v, a in zip(speed, acceleration):
        F_roll = Crr * m * g if v > 0 else 0.0
        F_aero = 0.5 * rho * Cd * A * v**2

        if a < 0:
            F_brake = max(0.0, m * abs(a) - F_roll - F_aero)
        else:
            F_brake = 0.0

        braking_force.append(F_brake)

    return braking_force


def main():
    time, speed = get_test_cycle()
    acceleration = calculate_acceleration(time, speed)
    braking = identify_braking(acceleration)
    braking_force = calculate_braking_force(time, speed, acceleration)

    print("\nDRIVE CYCLE CHECK")
    print("=" * 60)
    print(f"Cycle              : {DRIVE_CYCLE}")
    print(f"Data points        : {len(time)}")
    print(f"Duration           : {time[-1] - time[0]:.1f} s")
    print(f"Maximum speed      : {max(speed) * 3.6:.2f} km/h")
    print(f"Braking samples    : {sum(braking)}")
    print(f"Maximum brake force: {max(braking_force):.2f} N")
    print(f"First time samples : {time[:5]}")
    print(f"First speeds (m/s) : {[round(v, 3) for v in speed[:5]]}")


if __name__ == "__main__":
    main()