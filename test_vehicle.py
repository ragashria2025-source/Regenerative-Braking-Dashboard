
from parameters import PARAMETERS
from vehicle_model import step_vehicle, simulate


def value(name):
    return PARAMETERS[name]["value"]


def main():
    dt = 0.01
    v0 = 30.0

    m = value("m")
    Crr = value("Crr")
    Cd = value("Cd")
    A = value("A")
    rho = value("rho")
    g = value("g")

    # Test 1: Coast down, no commanded braking
    F_roll = Crr * m * g
    F_aero = 0.5 * rho * Cd * A * v0**2
    a_hand = -(F_roll + F_aero) / m
    v_hand_first_step = max(v0 + a_hand * dt, 0.0)

    v_new, a = step_vehicle(v0, 0.0, dt)

    print("\nTEST 1: COAST-DOWN")
    print(f"Rolling resistance = {F_roll:.2f} N")
    print(f"Aerodynamic drag   = {F_aero:.2f} N")
    print(f"Hand acceleration  = {a_hand:.5f} m/s^2")
    print(f"Model acceleration = {a:.5f} m/s^2")
    print(f"Hand speed after 1 step = {v_hand_first_step:.5f} m/s")
    print(f"Model speed after 1 step = {v_new:.5f} m/s")

    assert abs(v_new - v_hand_first_step) < 1e-10
    assert abs(a - a_hand) < 1e-10

    # Compare the first second with repeated Euler updates.
    time, speed, acceleration = simulate(30.0, 0.0, 1.0, dt)
    print(f"Speed after 1 second = {speed[-1]:.5f} m/s")
    print(f"Speed reduction      = {v0 - speed[-1]:.5f} m/s")

    # Test 2: Apply a known braking force
    F_brake = 4000.0
    a_brake_hand = -(F_roll + F_aero + F_brake) / m
    v_brake, a_brake = step_vehicle(v0, F_brake, dt)

    print("\nTEST 2: BRAKING AT 4000 N")
    print(f"Expected acceleration = {a_brake_hand:.5f} m/s^2")
    print(f"Model acceleration    = {a_brake:.5f} m/s^2")
    print(f"Speed after one step  = {v_brake:.5f} m/s")

    assert abs(a_brake - a_brake_hand) < 1e-10
    assert a_brake < a

    # Test 3: Rest condition
    v_rest, a_rest = step_vehicle(0.0, 4000.0, dt)
    assert v_rest == 0.0

    print("\nTEST 3: REST CONDITION")
    print(f"Speed remains = {v_rest:.2f} m/s")

    print("\nALL STEP 2 TESTS PASSED.")


if __name__ == "__main__":
    main()
