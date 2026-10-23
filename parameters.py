
"""
Step 1: Reference Vehicle Parameters
Reference: 2024 Tesla Model 3 Long Range AWD
ASSUMED values are simulation assumptions, not verified manufacturer data.
"""

PARAMETERS = {
    "Vehicle": {
        "value": "2024 Tesla Model 3 Long Range AWD",
        "unit": "text",
        "source": "Reference vehicle selected for simulation"
    },
    "m": {
        "value": 2000.0,
        "unit": "kg",
        "source": "ASSUMED: loaded simulation mass"
    },
    "m_curb": {
        "value": 1851.0,
        "unit": "kg",
        "source": "EV Specifications: reference curb-mass figure; verify exact variant"
    },
    "Cd": {
        "value": 0.23,
        "unit": "dimensionless",
        "source": "Published Model 3 aerodynamic specification; verify model year"
    },
    "A": {
        "value": 2.22,
        "unit": "m^2",
        "source": "ASSUMED: frontal area estimate"
    },
    "Crr": {
        "value": 0.010,
        "unit": "dimensionless",
        "source": "ASSUMED: passenger-car tyre rolling resistance"
    },
    "r": {
        "value": 0.334,
        "unit": "m",
        "source": "ASSUMED: effective wheel radius; verify tyre configuration"
    },
    "G": {
        "value": 9.03,
        "unit": "dimensionless",
        "source": "UNVERIFIED: gearbox ratio not confirmed by spec sources checked; verify against a primary source"
    },
    "T_max": {
        "value": 493.0,
        "unit": "N*m",
        "source": "Combined all-wheel torque, 2024 Model 3 LR AWD (autotijd.be spec sheet); regen envelope applied to one axle-equivalent (limitation)"
    },
    "P_max": {
        "value": 366000.0,
        "unit": "W",
        "source": "Combined all-wheel output, 2024 Model 3 LR AWD (autotijd.be spec sheet); regen envelope applied to one axle-equivalent (limitation)"
    },
    "Q": {
        "value": 82.1,
        "unit": "kWh",
        "source": "Gross battery capacity, 2024 Model 3 LR AWD (evspecifications.com); usable capacity is lower, so this overstates usable energy"
    },
    "V_nom": {
        "value": 360.0,
        "unit": "V",
        "source": "Nominal pack voltage, 2024 Model 3 LR AWD (evspecifications.com)"
    },
    "R0_25": {
        "value": 0.10,
        "unit": "ohm",
        "source": "ASSUMED: pack internal resistance at 25 degC"
    },
    "rho": {
        "value": 1.2,
        "unit": "kg/m^3",
        "source": "ASSUMED: air density"
    },
    "g": {
        "value": 9.81,
        "unit": "m/s^2",
        "source": "Standard gravitational acceleration"
    },
    "eta_gear": {
        "value": 0.97,
        "unit": "dimensionless",
        "source": "ASSUMED: gearbox efficiency"
    },
    "eta_gen": {
        "value": 0.90,
        "unit": "dimensionless",
        "source": "ASSUMED: regenerative generation efficiency"
    },
    "C_sc": {
        "value": 5.0,
        "unit": "F",
        "source": "ASSUMED: supercapacitor bank capacitance; sensitivity-test this"
    },
    "V_sc_max": {
        "value": 360.0,
        "unit": "V",
        "source": "ASSUMED: bank voltage ceiling matched to 360 V pack"
    },
    "V_sc_min": {
        "value": 180.0,
        "unit": "V",
        "source": "Usable window: half of V_max, so only the energy above it is used (E = 1/2 C V^2)"
    },
    "R_sc": {
        "value": 0.05,
        "unit": "ohm",
        "source": "ASSUMED: bank equivalent series resistance"
    },
    "P_sc_max": {
        "value": 100000.0,
        "unit": "W",
        "source": "ASSUMED: DC-DC converter power rating"
    },
    "eta_dc_in": {
        "value": 0.95,
        "unit": "dimensionless",
        "source": "ASSUMED: converter efficiency, battery bus to capacitor"
    },
    "eta_dc_out": {
        "value": 0.95,
        "unit": "dimensionless",
        "source": "ASSUMED: converter efficiency, capacitor to battery bus"
    },
    "i_max": {
        "value": 150.0,
        "unit": "A",
        "source": "ASSUMED: maximum charging current; not manufacturer data; sensitivity-test this"
    },
}


def print_parameter_table():
    print("\nREFERENCE VEHICLE: 2024 Tesla Model 3 Long Range AWD")
    print("-" * 110)
    print(f"{'Parameter':<12} {'Value':<15} {'Unit':<18} Source")
    print("-" * 110)

    for name, item in PARAMETERS.items():
        print(
            f"{name:<12} {str(item['value']):<15} "
            f"{item['unit']:<18} {item['source']}"
        )

    print("-" * 110)


if __name__ == "__main__":
    print_parameter_table()
