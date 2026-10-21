from __future__ import annotations

import streamlit as st
import pandas as pd

from parameters import PARAMETERS
from fine_cycle_runs import build_fine_grid, run_a, run_b, run_c
from battery_model import battery_resistance


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Regenerative Braking | VSE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME
# ============================================================

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&'
      'family=DM+Sans:wght@400;500;600;700&'
      'family=Manrope:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Manrope', sans-serif;
        letter-spacing: -0.025em;
    }

    h1 {
        font-size: 2.45rem !important;
        font-weight: 800 !important;
    }

    h2 {
        font-size: 1.65rem !important;
    }

    h3 {
        font-size: 1.15rem !important;
    }

    [data-testid="stAppViewContainer"] {
        background: #f4f2ec;
    }

    [data-testid="stSidebar"] {
        background: #17352d;
    }

    [data-testid="stSidebar"] * {
        color: #f5f1e8 !important;
    }

    [data-testid="stMetric"] {
        background: #fffefa;
        border: 1px solid #e4e0d5;
        padding: 15px;
        border-radius: 9px;
    }

    [data-testid="stMetricValue"] {
        font-family: 'DM Mono', monospace;
        font-size: 1.4rem;
    }

    .kicker {
        font-family: 'DM Mono', monospace;
        text-transform: uppercase;
        letter-spacing: .13em;
        font-size: .72rem;
        color: #52766a;
    }

    .hero {
        background: #17352d;
        color: #f5f1e8;
        padding: 30px;
        border-radius: 13px;
        margin-bottom: 22px;
    }

    .hero h1 {
        color: #f5f1e8 !important;
    }

    .hero p {
        color: #d3dfd7;
        font-size: 1rem;
        line-height: 1.7;
    }

    .smallprint {
        color: #6c716a;
        font-size: .84rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONSTANTS AND HELPERS
# ============================================================

STRATEGIES = {
    "A — Power-limited": run_a,
    "B — Direct regeneration": run_b,
    "C — Supercapacitor-assisted": run_c,
}


def number(result, key, default=0.0):
    """Return a numeric result without hiding missing values."""
    value = result.get(key, default)

    if value is None:
        return float(default)

    return float(value)


def simulate_all(soc, temperature):
    """Run every strategy with identical starting conditions."""
    return {
        name: function(
            initial_soc=float(soc),
            temperature_c=float(temperature),
        )
        for name, function in STRATEGIES.items()
    }


def energy_kj(value_j):
    return value_j / 1000.0


def energy_table(results):
    """Build a comparison table using explicitly defined units."""
    rows = []

    for strategy, result in results.items():
        rows.append({
            "Strategy": strategy,
            "Battery energy accepted (kJ)": energy_kj(
                number(result, "battery_accepted_J")
            ),
            "Estimated energy stored (kJ)": energy_kj(
                number(result, "battery_stored_J")
            ),
            "Electrical energy reported (kJ)": energy_kj(
                number(result, "electrical_J")
            ),
            "Friction braking work (kJ)": energy_kj(
                number(result, "friction_J")
            ),
            "Wheel regenerative work (kJ)": energy_kj(
                number(result, "wheel_regen_J")
            ),
            "Total wheel braking work (kJ)": energy_kj(
                number(result, "wheel_braking_J")
            ),
            "Final SOC (%)": 100.0 * number(
                result, "final_soc"
            ),
        })

    return pd.DataFrame(rows).set_index("Strategy")


def make_cycle_dataframe():
    """Get the actual cycle used by the simulation."""
    times, speeds, braking, force, dts = build_fine_grid()

    return pd.DataFrame({
        "Time (s)": times,
        "Speed (km/h)": [v * 3.6 for v in speeds],
        "Braking force demand (N)": force,
        "Braking phase": [
            "Braking" if item else "Not braking"
            for item in braking
        ],
    })


def show_line_chart(data, x_col, y_cols, title, x_label, y_label):
    st.markdown(f"#### {title}")

    chart_data = data.set_index(x_col)[y_cols]

    st.line_chart(
        chart_data,
        x_label=x_label,
        y_label=y_label,
        height=320,
    )


def show_grouped_energy_chart(data, columns, title):
    """Compare energy quantities without stacking them."""
    st.markdown(f"#### {title}")

    chart_data = data[columns]

    st.bar_chart(
        chart_data,
        stack=False,
        x_label="Strategy",
        y_label="Energy (kJ)",
        height=350,
    )

    st.caption(
        "Vertical axis: energy in kJ. Bars are grouped rather than "
        "stacked; the different energy quantities are not added together."
    )


def parameter_table():
    """Display values directly from parameters.py."""
    rows = []

    for name, details in PARAMETERS.items():
        rows.append({
            "Parameter": name,
            "Value": details.get("value", "Not specified"),
            "Unit": details.get("unit", "Not specified"),
            "Source / status": details.get(
                "source", "Source not specified"
            ),
        })

    return pd.DataFrame(rows)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## ⚡ REGENERATIVE BRAKING")
    st.caption("VEHICLE SYSTEMS ENGINEERING")

    page = st.radio(
        "WORKSPACE",
        [
            "Overview",
            "Interactive simulator",
            "How it works",
            "Literature review & references",
            "Model assumptions",
            "Results & limitations",
        ],
    )

    st.markdown("---")
    st.markdown("**SIMULATION INPUTS**")

    soc_percent = st.slider(
        "Starting battery SOC (%)",
        min_value=5,
        max_value=95,
        value=20,
        step=5,
        help="Starting state of charge, expressed as a percentage.",
    )

    temperature = st.slider(
        "Battery temperature (°C)",
        min_value=-5,
        max_value=40,
        value=25,
        step=5,
        help=(
            "Temperature supplied to the simplified battery model. "
            "Charging is disabled below 0 °C by the current model."
        ),
    )

    soc = soc_percent / 100.0

    st.markdown("---")
    st.caption(
        "Numerical simulation only. This is not a live vehicle measurement."
    )


# ============================================================
# SIMULATION
# ============================================================

current_inputs = (soc, float(temperature))

if st.session_state.get("last_inputs") != current_inputs:
    with st.spinner("Calculating simulation results..."):
        st.session_state["simulation_results"] = simulate_all(
            soc, temperature
        )
        st.session_state["last_inputs"] = current_inputs

results = st.session_state["simulation_results"]
comparison = energy_table(results)
cycle_df = make_cycle_dataframe()

result_a = results["A — Power-limited"]
result_b = results["B — Direct regeneration"]
result_c = results["C — Supercapacitor-assisted"]


# ============================================================
# PAGE 1: OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown(
        """
        <div class="hero">
            <div class="kicker" style="color:#a8c9b5">
                VEHICLE SYSTEMS ENGINEERING
            </div>
            <h1>Regenerative Braking</h1>
            <p>
            An interactive study of braking-energy recovery in an
            electric vehicle. Compare power-limited regeneration,
            direct battery regeneration, and a supercapacitor-assisted
            approach under common starting conditions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Project overview")

    st.write(
        "Regenerative braking allows an electric traction motor to operate "
        "as a generator during deceleration. Some of the vehicle's mechanical "
        "energy can then be converted to electrical energy and accepted by "
        "an energy-storage system. Friction braking supplies the remaining "
        "braking demand in this simplified model."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Starting SOC", f"{soc_percent}%")
    col2.metric("Battery temperature", f"{temperature} °C")
    col3.metric("Strategies compared", "3")

    st.markdown("### Energy comparison")

    show_grouped_energy_chart(
        comparison,
        [
            "Battery energy accepted (kJ)",
            "Estimated energy stored (kJ)",
        ],
        "Battery energy accepted versus estimated energy stored",
    )

    st.markdown("### Friction braking")

    st.bar_chart(
        comparison[["Friction braking work (kJ)"]],
        x_label="Strategy",
        y_label="Friction braking work (kJ)",
        height=300,
    )

    st.markdown("### Drive-cycle speed")

    show_line_chart(
        cycle_df,
        "Time (s)",
        ["Speed (km/h)"],
        "Speed versus time",
        "Time (s)",
        "Speed (km/h)",
    )

    st.info(
        "The simulation uses the short illustrative cycle defined in "
        "drive_cycle.py. It should not be described as a standard WLTP "
        "or UDDS cycle unless that file is replaced with a documented "
        "version of the standard cycle."
    )


# ============================================================
# PAGE 2: INTERACTIVE SIMULATOR
# ============================================================

elif page == "Interactive simulator":

    st.markdown(
        '<div class="kicker">SIMULATION / 02</div>',
        unsafe_allow_html=True,
    )
    st.title("Interactive simulator")

    st.write(
        "Change the starting SOC and temperature using the sidebar. "
        "All three strategies are recalculated with the same selected inputs."
    )

    st.markdown("### Battery results")

    cols = st.columns(3)

    for col, (name, result) in zip(cols, results.items()):
        col.metric(
            name,
            f"{energy_kj(number(result, 'battery_accepted_J')):.3f} kJ",
            f"Final SOC: {100 * number(result, 'final_soc'):.4f}%",
        )

    st.markdown("### Strategy comparison")

    show_grouped_energy_chart(
        comparison,
        [
            "Battery energy accepted (kJ)",
            "Estimated energy stored (kJ)",
        ],
        "Battery energy",
    )

    show_grouped_energy_chart(
        comparison,
        [
            "Wheel regenerative work (kJ)",
            "Friction braking work (kJ)",
        ],
        "Braking-work components",
    )

    st.caption(
        "These are separately reported model outputs. Their definitions "
        "must be checked against the implementation before using them "
        "as a closed energy balance."
    )

    st.markdown("### Detailed numerical results")

    st.dataframe(
        comparison.style.format("{:.5f}"),
        use_container_width=True,
    )

    st.download_button(
        label="Download results as CSV",
        data=comparison.to_csv().encode("utf-8"),
        file_name="regenerative_braking_results.csv",
        mime="text/csv",
    )

    st.markdown("### Difference between A and B")

    difference_ab = (
        comparison.loc["A — Power-limited"]
        - comparison.loc["B — Direct regeneration"]
    )

    st.dataframe(
        difference_ab.rename("A minus B").to_frame(),
        use_container_width=True,
    )

    st.markdown("### Difference between B and C")

    difference_bc = (
        comparison.loc["B — Direct regeneration"]
        - comparison.loc["C — Supercapacitor-assisted"]
    )

    st.dataframe(
        difference_bc.rename("B minus C").to_frame(),
        use_container_width=True,
    )

    st.markdown("### Starting SOC sensitivity")

    soc_points = [5, 20, 40, 60, 80, 95]
    soc_rows = []

    for point in soc_points:
        result = run_b(
            initial_soc=point / 100.0,
            temperature_c=float(temperature),
        )

        soc_rows.append({
            "Starting SOC (%)": point,
            "Energy accepted (kJ)": energy_kj(
                number(result, "battery_accepted_J")
            ),
            "Energy stored (kJ)": energy_kj(
                number(result, "battery_stored_J")
            ),
            "Final SOC (%)": 100.0 * number(
                result, "final_soc"
            ),
        })

    soc_df = pd.DataFrame(soc_rows)

    show_line_chart(
        soc_df,
        "Starting SOC (%)",
        ["Energy accepted (kJ)", "Energy stored (kJ)"],
        "Effect of starting SOC",
        "Starting SOC (%)",
        "Energy (kJ)",
    )

    st.dataframe(
        soc_df.style.format("{:.4f}"),
        use_container_width=True,
    )

    st.markdown("### Battery temperature sensitivity")

    temperature_points = [-5, 0, 10, 25, 35, 40]
    temperature_rows = []

    for point in temperature_points:
        result = run_b(
            initial_soc=soc,
            temperature_c=float(point),
        )

        temperature_rows.append({
            "Battery temperature (°C)": point,
            "Energy accepted (kJ)": energy_kj(
                number(result, "battery_accepted_J")
            ),
            "Energy stored (kJ)": energy_kj(
                number(result, "battery_stored_J")
            ),
            "Final SOC (%)": 100.0 * number(
                result, "final_soc"
            ),
        })

    temperature_df = pd.DataFrame(temperature_rows)

    show_line_chart(
        temperature_df,
        "Battery temperature (°C)",
        ["Energy accepted (kJ)", "Energy stored (kJ)"],
        "Effect of battery temperature",
        "Temperature (°C)",
        "Energy (kJ)",
    )

    st.dataframe(
        temperature_df.style.format("{:.4f}"),
        use_container_width=True,
    )

    st.markdown("### Supercapacitor results")

    cap1, cap2, cap3 = st.columns(3)

    cap1.metric(
        "Energy left in capacitor",
        f"{energy_kj(number(result_c, 'cap_left_J')):.4f} kJ",
    )

    cap2.metric(
        "Energy transferred to battery",
        f"{energy_kj(number(result_c, 'transfer_J')):.4f} kJ",
    )

    cap3.metric(
        "Reported capacitor residual",
        f"{number(result_c, 'cap_residual_J'):.4f} J",
    )

    st.caption(
        "Capacitor residual is the value calculated by the current "
        "simulation. It should not be treated as proof of complete "
        "system energy conservation until all input, output, and "
        "conversion-loss terms have been checked."
    )


# ============================================================
# PAGE 3: HOW IT WORKS
# ============================================================

elif page == "How it works":

    st.markdown(
        '<div class="kicker">MODEL GUIDE / 03</div>',
        unsafe_allow_html=True,
    )
    st.title("How regenerative braking works")

    st.write(
        "During deceleration, the traction motor can act as a generator. "
        "The simulation estimates braking demand, regenerative electrical "
        "power, battery acceptance and friction braking."
    )

    stages = [
        (
            "01 — Drive cycle",
            "Vehicle speed is interpolated onto a fine time grid. "
            "The model identifies intervals where speed decreases."
        ),
        (
            "02 — Braking-force demand",
            "The code estimates braking force from vehicle mass, "
            "deceleration, rolling resistance and aerodynamic drag."
        ),
        (
            "03 — Regenerative conversion",
            "The regenerative model calculates available electrical "
            "power and the corresponding regenerative wheel force."
        ),
        (
            "04 — Battery acceptance",
            "The battery model calculates open-circuit voltage, internal "
            "resistance, charging current, terminal power, internal losses "
            "and the SOC update."
        ),
        (
            "05 — Energy-routing strategies",
            "A applies a 50 kW electrical power cap, B requests available "
            "regenerative power from the battery model, and C uses a "
            "supercapacitor buffer and subsequent transfer."
        ),
        (
            "06 — Energy accounting",
            "The simulation reports electrical energy, battery-accepted "
            "energy, estimated stored energy, friction work and capacitor "
            "quantities separately."
        ),
    ]

    for heading, explanation in stages:
        with st.container(border=True):
            st.markdown(f"**{heading}**")
            st.write(explanation)

    st.markdown("### Fundamental equations")

    st.latex(r"E_k = \frac{1}{2}mv^2")

    st.caption(
        "Kinetic energy in joules, where mass is in kilograms "
        "and speed is in metres per second."
    )

    st.latex(r"P = Fv")

    st.caption(
        "Mechanical power in watts, where force is in newtons "
        "and speed is in metres per second."
    )

    st.latex(r"E_C = \frac{1}{2}CV^2")

    st.caption(
        "Ideal capacitor energy in joules, where capacitance is in "
        "farads and voltage is in volts."
    )

    st.latex(r"P_{\mathrm{terminal}} = V_{\mathrm{terminal}}I")

    st.caption("Battery terminal power in watts.")

    st.latex(
        r"\Delta SOC = \frac{I\Delta t}{3600Q_{\mathrm{Ah}}}"
    )

    st.caption(
        "Simplified SOC change for charging current in amperes, "
        "time in seconds and battery capacity in ampere-hours."
    )

    st.warning(
        "These equations describe the general physical principles. "
        "The accuracy of numerical outputs also depends on the particular "
        "component models, parameter values, control rules and time-step "
        "implementation used by this project."
    )


# ============================================================
# PAGE 4: LITERATURE REVIEW AND REFERENCES
# ============================================================

elif page == "Literature review & references":

    st.markdown(
        '<div class="kicker">RESEARCH / 04</div>',
        unsafe_allow_html=True,
    )
    st.title("Literature review & references")

    st.markdown("### 1. Regenerative-braking systems")

    st.write(
        "Published reviews describe regenerative braking as a means of "
        "converting part of the vehicle's kinetic energy into electrical "
        "energy during deceleration. Actual recovery depends on the motor, "
        "power electronics, battery acceptance limits, operating conditions "
        "and coordination with friction brakes."
    )

    st.markdown("### 2. Regenerative-braking control strategies")

    st.write(
        "Different control strategies distribute braking demand between "
        "regenerative and friction braking differently. Comparing multiple "
        "strategies under identical starting conditions is useful, provided "
        "the same physical assumptions and energy definitions are applied."
    )

    st.markdown("### 3. Battery operating conditions")

    st.write(
        "Battery SOC, temperature, voltage, internal resistance and current "
        "limits can influence charge acceptance. This project represents "
        "these effects with a simplified battery model. Its assumed "
        "temperature relationship is not a measured battery characterisation."
    )

    st.markdown("### 4. Supercapacitor-assisted energy recovery")

    st.write(
        "A supercapacitor can provide a high-power energy buffer, but a "
        "real system also depends on converter efficiency, capacitor voltage "
        "limits, equivalent series resistance and control strategy. The "
        "current implementation is a simplified numerical study rather "
        "than a validated hardware design."
    )

    st.markdown("### Research contribution")

    st.write(
        "This project provides an interactive comparison of three simplified "
        "energy-routing approaches and lets the user explore how starting SOC "
        "and temperature affect calculated results. Its contribution is a "
        "transparent educational simulation, not a claim of experimentally "
        "proven recovery efficiency."
    )

    st.markdown("### References")

    st.markdown(
        """
        **1. Yang, C., Sun, T., Wang, W., Li, Y., Zhang, Y., & Zha, M. (2024).**  
        *Regenerative braking system development and perspectives for electric
        vehicles: An overview.* Renewable and Sustainable Energy Reviews,
        198, 114389.  
        [https://doi.org/10.1016/j.rser.2024.114389](https://doi.org/10.1016/j.rser.2024.114389)

        **2. Saiteja, P., Ashok, B., Wagh, A. S., & Farrag, M. E. (2022).**  
        *Critical review on optimal regenerative braking control system
        architecture, calibration parameters and development challenges for
        EVs.* International Journal of Energy Research, 46(14), 20146–20179.  
        [https://doi.org/10.1002/er.8306](https://doi.org/10.1002/er.8306)

        **3. An overview of regenerative braking systems. (2022).**  
        Journal of Energy Storage, 52, 105033.  
        [https://doi.org/10.1016/j.est.2022.105033](https://doi.org/10.1016/j.est.2022.105033)

        **4. Szumska, E. M. (2025).**  
        *Regenerative braking systems in electric vehicles: A comprehensive
        review of design, control strategies, and efficiency challenges.*
        Energies, 18(10), 2422.  
        [https://doi.org/10.3390/en18102422](https://doi.org/10.3390/en18102422)
        """
    )

    st.caption(
        "Before final submission, verify each reference's bibliographic "
        "details and read the original publication. These references provide "
        "background for the modelling approach; they do not independently "
        "validate this project's numerical outputs."
    )


# ============================================================
# PAGE 5: MODEL ASSUMPTIONS
# ============================================================

elif page == "Model assumptions":

    st.markdown(
        '<div class="kicker">MODEL REGISTER / 05</div>',
        unsafe_allow_html=True,
    )
    st.title("Model parameters and assumptions")

    st.write(
        "The table below reads parameter values and source notes directly "
        "from parameters.py. A parameter without a documented source should "
        "not be presented as a manufacturer-confirmed value."
    )

    st.dataframe(
        parameter_table(),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Battery model")

    try:
        resistance = battery_resistance(float(temperature))
        st.metric(
            "Estimated battery resistance",
            f"{resistance:.6f} Ω",
        )
    except (ValueError, KeyError, TypeError):
        st.warning(
            "The resistance value could not be calculated from the "
            "current battery model and selected temperature."
        )

    st.markdown("### Current model assumptions")

    st.markdown(
        """
        - Battery open-circuit voltage is approximated from SOC.
        - Battery resistance increases at temperatures below 25 °C
          according to the formula in battery_model.py.
        - Charging is disabled below 0 °C.
        - Charging is disabled at SOC values of 0.99 or higher.
        - A has an assumed 50 kW regenerative electrical power cap.
        - The drive cycle is the test cycle implemented in drive_cycle.py.
        - The battery, vehicle and supercapacitor are not connected to
          physical measurement hardware.
        - The supercapacitor and converter parameters are model inputs,
          not verified specifications for a particular commercial system.
        """
    )

    st.info(
        "These assumptions are part of the current model definition. "
        "They should not be described as universal characteristics of "
        "all electric vehicles or lithium-ion batteries."
    )


# ============================================================
# PAGE 6: RESULTS AND LIMITATIONS
# ============================================================

elif page == "Results & limitations":

    st.markdown(
        '<div class="kicker">INTERPRETATION / 06</div>',
        unsafe_allow_html=True,
    )
    st.title("Results and limitations")

    st.markdown("### Simulation results")

    st.dataframe(
        comparison.style.format("{:.5f}"),
        use_container_width=True,
    )

    st.markdown("### Why A and B may be similar")

    st.write(
        "Strategy A applies a 50 kW cap to the requested regenerative "
        "electrical power. Strategy B requests the available regenerative "
        "power from the battery model. If the available power never exceeds "
        "50 kW, A's cap will not bind. If both strategies are limited by "
        "battery charge acceptance, their calculated results can also be "
        "very similar."
    )

    st.warning(
        "The current simulation results do not include a complete time "
        "history of the power-cap activation state. Therefore, the dashboard "
        "does not claim that the 50 kW limit is inactive in every run. "
        "That must be confirmed by instrumenting fine_cycle_runs.py."
    )

    st.markdown("### Interpretation of energy quantities")

    st.markdown(
        """
        - **Battery energy accepted:** electrical energy accepted at the
          battery terminals, as accumulated by the model.
        - **Estimated energy stored:** the integral of the model's stored
          power, which excludes the battery's modelled internal losses.
        - **Wheel regenerative work:** mechanical work attributed to
          regenerative braking at the wheels.
        - **Friction braking work:** mechanical work attributed to friction
          braking.
        - **Energy transferred:** energy accepted by the battery during the
          supercapacitor transfer phase.
        """
    )

    st.markdown("### Validation requirements")

    st.markdown(
        """
        1. Check the braking-force balance for every simulation strategy.
        2. Verify the relationship between wheel regenerative work and
           electrical energy after conversion losses.
        3. Confirm that terminal energy, stored energy and battery losses
           use consistent definitions and time steps.
        4. Verify the supercapacitor energy balance, including converter
           losses, equivalent series resistance and residual energy.
        5. Log the maximum regenerative power and count how often A's
           50 kW cap activates.
        6. Check SOC and temperature edge cases against the model's stated
           limits.
        7. Compare against a documented standard drive cycle and component
           specifications before making real-vehicle performance claims.
        """
    )

    st.markdown("### Energy audit reference")

    st.write(
        "The previously run configuration-B audit reported that electrical "
        "energy did not exceed wheel-side regenerative energy, that wheel "
        "braking work equalled regenerative plus friction work under its "
        "implemented definitions, and that the kinetic-energy closure "
        "residual was within its configured tolerance."
    )

    st.caption(
        "Those checks are useful internal-consistency checks for configuration "
        "B. They do not establish that every strategy passes the same checks "
        "or that the assumptions match a physical vehicle."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Regenerative Braking Simulation | Vehicle Systems Engineering | "
    "Educational numerical model — not a certified vehicle model."
)
