"""
Streamlit dashboard for the EV regenerative braking model.

Run from the project folder:
    streamlit run app.py
"""

import streamlit as st
from dashboard_core import CYCLES, run_scenario

st.set_page_config(page_title="EV regen braking model", layout="wide")
st.title("EV regenerative braking: configurations A, B and C")
st.caption("Reference vehicle: 2024 Tesla Model 3 Long Range AWD (parameters partly assumed; see the report).")

with st.sidebar:
    st.header("Scenario")
    cycle_label = st.selectbox("Drive cycle", list(CYCLES.keys()), index=0)
    soc = st.slider("Initial SOC", 0.05, 0.95, 0.20, 0.05)
    temp = st.slider("Battery temperature (°C)", -5.0, 40.0, 25.0, 1.0)

    st.header("Assumed parameters")
    cap = st.slider("Configuration A regen cap (kW)", 10, 150, 50, 5)
    i_max = st.slider("Charge-current limit (A)", 60, 250, 150, 5)
    r0 = st.slider("Battery resistance at 25 °C (Ω)", 0.05, 0.20, 0.10, 0.01)
    eta_gen = st.slider("Generator efficiency", 0.80, 0.95, 0.90, 0.01)
    c_sc = st.slider("Supercapacitor capacitance (F)", 1.0, 10.0, 5.0, 0.5)

with st.spinner("Running A, B and C..."):
    res = run_scenario(cycle=CYCLES[cycle_label], initial_soc=soc, temperature_c=temp,
                       cap_kw=cap, i_max=i_max, r0_25=r0, eta_gen=eta_gen, c_sc=c_sc)

col1, col2, col3 = st.columns(3)
col1.metric("A battery energy (kJ)", f"{res['battery_kJ']['A']:.3f}")
col2.metric("B battery energy (kJ)", f"{res['battery_kJ']['B']:.3f}")
col3.metric("C battery energy incl. transfer (kJ)", f"{res['battery_kJ']['C']:.3f}")

st.subheader("Battery energy by configuration (kJ)")
st.bar_chart({"A (fixed cap)": [res["battery_kJ"]["A"]],
              "B (adaptive)": [res["battery_kJ"]["B"]],
              "C (adaptive + supercap)": [res["battery_kJ"]["C"]]})

st.subheader("Differences (kJ)")
st.table({
    "Quantity": ["C minus B (battery energy)", "B minus A (battery energy)",
                 "Friction braking, A", "Friction braking, B", "Friction braking, C",
                 "Wasted by battery, A", "C capacitor transfer to battery",
                 "Energy left in capacitor at end"],
    "kJ": [f"{res['C_minus_B_kJ']:+.3f}", f"{res['B_minus_A_kJ']:+.3f}",
           f"{res['friction_kJ']['A']:.3f}", f"{res['friction_kJ']['B']:.3f}",
           f"{res['friction_kJ']['C']:.3f}", f"{res['wasted_kJ']['A']:.3f}",
           f"{res['C_transfer_kJ']:.3f}", f"{res['C_left_kJ']:.3f}"],
})

st.info("Energies are battery-accepted energy over one cycle. Capacitor energy is shown "
        "separately and is never added to the battery total. Each slider is an assumption "
        "or a study choice, not measured data. Changing a value does not make it a validated result.")
if cycle_label.startswith("EPA"):
    st.warning("UDDS runs take longer. Results on UDDS and the test cycle differ: on UDDS the "
               "battery rarely limits charging below SOC 0.95.")