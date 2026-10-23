# EV Regenerative Braking Simulation: Physics Core

## 1. Project Overview
This project simulates longitudinal vehicle motion, regenerative braking, battery energy acceptance, and energy flow during a stopping event. It compares two configurations:

- **Configuration A (baseline):** regeneration limited by a fixed power cap, with no battery feedback.
- **Configuration B (adaptive):** regeneration limited by motor and battery acceptance at each time step.
- **Configuration C (adaptive + supercapacitor):** generated power the battery rejects is stored in a supercapacitor, then transferred to the battery after the stop at the battery's acceptance limit.

This is a simplified educational simulation, not a production vehicle control system.

## 2. Modules

- `parameters.py`: vehicle, motor, drivetrain and battery parameters, each with a value, unit and source.
- `vehicle_model.py`: vehicle forces, acceleration and speed updates.
- `regen_model.py`: regenerative braking subject to motor torque and power limits.
- `battery_model.py`: charging current, terminal voltage, SOC changes and resistive losses.
- `integrated_regen.py`: combines regeneration with battery charge-acceptance limits (configuration B).
- `simulate_stopping.py`: full stopping event under configuration B, with energy balance checks.
- `baseline_stopping.py`: full stopping event under configuration A, with energy balance checks.
- `supercap_model.py`: supercapacitor energy, voltage window and power limits (configuration C).
- `configuration_c.py`: stopping event with supercapacitor buffer and post-stop transfer (configuration C).
- `compare_configurations.py`: sweeps SOC and temperature and compares A, B and C.
- `test_vehicle.py`, `test_regen.py`, `test_battery.py`, `test_integrated_regen.py`, `test_supercap.py`: unit tests.

## 3. Requirements
- Python 3. Only the standard library is used.

## 4. Running the Tests
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\test_vehicle.py"
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\test_regen.py"
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\test_battery.py"
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\test_integrated_regen.py"
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\test_supercap.py"
```

`test_regen.py` includes a **power-conservation check**: motor-side power must never exceed wheel-side power during regeneration. This check caught a sign error in the gearbox efficiency (see Section 8).

## 5. Running the Simulations
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\simulate_stopping.py"     # configuration B
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\baseline_stopping.py"     # configuration A
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\configuration_c.py"        # configuration C
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" ".\compare_configurations.py" # A, B, C sweep
```
## 6. Current Results

Cycle: 0–40–0 km/h test cycle (`DRIVE_CYCLE = "toy"`), resampled to dt = 0.01 s.
Configuration A cap: 50 kW (assumed; its results depend on this value).
Energy measure: battery-accepted energy. Capacitor energy is reported separately and is not added to the battery total.

The earlier 30 m/s, 4000 N scenario and the figures from it (500.40 kJ, 127.77 kJ, 126.68 kJ) are superseded and should not be used.

### 6.1 A / B / C at SOC 0.20, 25 °C (Step 6)

| Quantity | A | B | C |
|---|---|---|---|
| Battery accepted, stop only (kJ) | 103.315 | 103.315 | 103.315 |
| Battery accepted, incl. transfer (kJ) | 103.315 | 103.315 | 103.573 |
| Friction braking (kJ) | 0.118 | 0.331 | 0.000 |
| Wasted, rejected by battery (kJ) | 0.186 | 0.000 | – |

C minus B: +0.259 kJ. On this cycle the battery accepts almost all regenerated energy, so the gain from the capacitor is small.

### 6.2 SOC sweep at 25 °C (Step 8)

Battery-accepted energy in kJ, including transfer for C.

| SOC | A | B | C | C − B | B − A |
|---|---|---|---|---|---|
| 0.20 | 103.315 | 103.315 | 103.573 | +0.259 | 0.000 |
| 0.50 | 103.501 | 103.603 | 103.603 | 0.000 | +0.103 |
| 0.80 | 103.501 | 103.603 | 103.603 | 0.000 | +0.103 |
| 0.90 | 102.549 | 102.549 | 103.482 | +0.933 | 0.000 |
| 0.95 | 72.053 | 72.053 | 98.996 | +26.944 | 0.000 |

C's advantage over B is largest at high SOC (0.95). Every point is a full run with the energy checks passing.

### 6.3 Temperature sweep at initial SOC 0.50 (Step 9)

| Temp (°C) | A | B | C total | C capacitor left (kJ) |
|---|---|---|---|---|
| 40 | 103.501 | 103.603 | 103.603 | 0.000 |
| 25 | 103.501 | 103.603 | 103.603 | 0.000 |
| 10 | 103.501 | 103.603 | 103.603 | 0.000 |
| −5 | 0.000 | 0.000 | 0.000 | 94.863 |

At −5 °C the battery model does not charge, so nothing reaches the battery. C's energy stays in the capacitor and is reported, not lost.

### 6.4 Tornado at baseline B, SOC 0.20, 25 °C (Step 10)

Baseline battery energy: B 103.315 kJ, C 103.573 kJ. Change in B's battery energy, sorted by swing.

| Parameter | Low input | High input | Low ΔE (kJ) | High ΔE (kJ) | Swing (kJ) | Status |
|---|---|---|---|---|---|---|
| Charge-current limit | 105 A | 195 A | −12.18 | +0.29 | 12.47 | Assumed, ±30% |
| Generator efficiency | 0.85 | 0.95 | −5.47 | +4.89 | 10.35 | Assumed, ±0.05 |
| Initial SOC | 0.05 | 0.35 | −0.82 | +0.29 | 1.10 | Study choice, ±0.15 |
| Battery internal resistance | 0.07 Ω | 0.13 Ω | −0.16 | +0.13 | 0.29 | Assumed, ±30% |
| Battery temperature | 10 °C | 40 °C | +0.15 | 0.00 | 0.15 | Study choice, ±15 °C |
| Supercap capacitance (C only) | 3.5 F | 6.5 F | 0.00 | 0.00 | 0.00 | Assumed, ±30% |
| Motor regen power limit | 256 kW | 476 kW | 0.00 | 0.00 | 0.00 | Known limitation: one-axle value |

The motor power limit shows no swing because the spec-sheet value is applied to one axle. Treat this as a known limitation, not a finding that power limits don't matter.

Every number in this section comes from runs of the current code with the timing fix applied.

**Important:** the gains at mid SOC depend on the 50 kW cap chosen for configuration A. A larger cap would narrow or remove the gap. This is a sensitivity question, not a result about adaptive control in general. Report it that way.

### Configuration C (supercapacitor)

Same stopping scenario. The capacitor takes generated power the battery rejects, and transfers it to the battery after the stop.

| Quantity | B | C |
|---|---|---|
| Battery stored energy (stop + transfer) | 500.40 kJ | 663.81 kJ |
| Friction braking energy | 233.41 kJ | 0 kJ |
| Capacitor-to-battery transfer | n/a | 171.29 kJ over 3.5 s |
| Conversion and ESR losses (in and out) | n/a | about 33 kJ |

Battery stored energy across the sweep (C minus B):

| SOC | 10 °C | 25 °C |
|---|---|---|
| 0.20 | +155.8 kJ | +163.4 kJ |
| 0.50 | +127.6 kJ | +134.1 kJ |
| 0.80 | +102.0 kJ | +107.6 kJ |
| 0.90 | +219.0 kJ | +184.0 kJ |
| 0.95 | +224.9 kJ | +223.9 kJ |
| Any | −5 °C: nothing reaches the battery; 243 kJ stays in the capacitor | |

**Sensitivity to capacitor size** (25 °C, SOC 0.20 and 0.90): the gain grows with capacitance and levels off near 5 F, at about 160–185 kJ. Below 2 F the gain falls roughly in proportion to the usable window (243 kJ at 5 F; 97 kJ at 2 F; 49 kJ at 1 F).

**Interpretation and limits of this result:**
- Most of the gain comes from energy that B would have sent to friction brakes, plus energy that B throttled. Stored energy in C is larger partly because C regenerates all of the braking demand.
- The transfer assumes the battery accepts charge at its limit immediately after the stop, with the vehicle at rest and no driving load. Real SOC changes during driving are not modelled.
- Energy in the capacitor at a cold battery is not lost. It is recorded as "left in cap" and would be transferred later when the battery warms.
- The result depends on the assumed capacitance, ESR, converter power and efficiencies. All are labelled ASSUMED in `parameters.py`.

These are results from specific simulated scenarios, not verified real-world vehicle performance.

## 7. Energy Balance Checks
- **Vehicle residual:** kinetic energy lost against braking, aero and rolling work. Approximately 0 J.
- **Recovery residual:** wheel braking energy against friction, gear and generator loss, battery loss, wasted energy and stored energy. About −0.55 J, within a tolerance of 0.1% of wheel braking energy (about 831 J).

### Final energy audit (Step 12)
- For A, B and C, wheel braking energy equals friction + gear/generator loss + battery loss + battery stored + converter and ESR losses + wasted energy (A only) + energy left in the capacitor.
- Balance residual: 0.0000 J against a tolerance of 0.1% of wheel braking energy.
- Friction force is checked on every regen step (1200 calls on the 0–40–0 cycle): regen + friction equals the braking demand, and friction is never negative.
- The electrical chain is checked against the efficiency product (eta_gear × eta_gen).

These checks confirm the bookkeeping is consistent. They are satisfied by construction and do not test whether the physics is correct. The power-conservation test in `test_regen.py` is the physics check for the regeneration stage.

## 8. Corrections Made
1. **Gearbox efficiency sign (regen_model.py).** The gearbox loss was applied so the motor was credited with more power than the wheels supplied (about 3% energy created). It is now applied on the correct side. Effect on stored energy in this scenario: about −2%.
2. **Battery resistance (battery_model.py).** Resistance previously rose at high temperature. It now rises only below 25 °C, which matches typical lithium-ion behaviour.
3. **Charge-current limit (parameters.py).** The 150 A limit moved from the code into the parameter table, labelled as an assumption.
4. **Parameters updated from sources (parameters.py).** Battery capacity, nominal voltage and motor torque and power now use values from the 2024 Model 3 Long Range AWD spec sheets. The gear ratio is still unverified.
5. **Tolerances tightened (simulate_stopping.py).** Residual tolerance is now 0.1% of braking energy, not a fixed number of joules.
6. **Unused module removed.** `energy_ledger.py` was not called anywhere; `simulate_stopping.py` is the single ledger.
7. **Regen timing (fine_cycle_runs.py, step11_supercap_plots.py).** Regen force and generated power were evaluated at the speed at the start of each step, while wheel work was integrated with mid-step speed. This made generated energy about 0.22% too high and failed the 0.1% energy audit. Regen is now evaluated at mid-step speed. Results before this fix (127.77 kJ, 126.68 kJ, and the earlier Step 6–11 figures) are superseded.

## 9. Assumptions and Limitations
- **Supercapacitor (configuration C).** 5 F, 360 V to 180 V usable window, 0.05 Ω ESR, 100 kW converter, and 95% efficiency in each direction are assumed. Transfer happens at rest after the stop, and the battery is assumed to be at the same SOC and temperature. No DC-DC converter efficiency curve is modelled.
- **Parameters.** Mass (2000 kg), frontal area, rolling resistance, wheel radius, generator efficiency, gearbox efficiency and internal resistance are assumed. The gear ratio is unverified. See `parameters.py` for each source.
- **Motor envelope.** The 493 N·m and 366 kW values are combined all-wheel figures for a dual-motor car. The model applies them to a single regenerative path, which overstates what one axle can absorb. Brake force distribution between axles is not modelled.
- **Battery.** The model is a simplified first-order equivalent circuit with no RC branch. The 150 A limit and the 0 °C cutoff are assumptions. Capacity is gross, so usable energy is lower.
- **Not modelled.** Motor efficiency maps, tyre slip, ABS, road gradient, detailed thermal behaviour, and battery ageing.
- **Scope.** The results describe one stopping scenario unless a sweep is stated. Passing the checks shows internal consistency; it does not prove the model predicts a real vehicle.

## 10. Next Steps
- Sensitivity analysis on the charge-current limit, the configuration A cap, the capacitance, initial SOC, temperature and battery resistance.
- Drive cycle input (UDDS, WLTP), where SOC changes during the cycle.
- Converter efficiency curves and a full thermal model.
