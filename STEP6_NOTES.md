# Step 6: A/B/C on the same drive cycle

## Scripts
- `fine_cycle_runs.py`: builds the drive cycle on a 0.01 s grid (linear interpolation of the 1 s test cycle) and runs A, B and C with identical settings.
- `energy_accounting.py`: energy audit on the same grid (three checks, all pass).
- `compare_abc_final.py`: prints the A/B/C table for Step 6.

Run:
    python compare_abc_final.py
    python energy_accounting.py

## Settings (identical for A, B and C)
- Cycle: 0-40-0 km/h test cycle, resampled to dt = 0.01 s
- Initial SOC 0.20, temperature 25 C
- Energy measure: battery-accepted energy
- Configuration A cap: 50 kW (ASSUMED, sensitivity-test this)

## Result (test cycle)
| | A | B | C |
|---|---|---|---|
| Battery accepted, stop (kJ) | 103.315 | 103.315 | 103.315 |
| Battery accepted, incl. transfer (kJ) | 103.315 | 103.315 | 103.573 |
| Friction braking (kJ) | 0.118 | 0.331 | 0.000 |

On this cycle the battery accepts almost all regenerated energy, so the configurations store nearly the same energy. C's gain is 0.27 kJ.

## Correction to earlier figures
The earlier values (A = 127.77 kJ, B = 126.68 kJ) came from a 1 s time step that uses the speed at the start of each step. That overstated power-based energy by about 22%. The fine-grid values above replace them. Do not use the older figures in the report.

## Known limits
- Test cycle only. Replace with UDDS or WLTP before the sensitivity analysis.
- Configuration C on the drive cycle uses the same battery and capacitor assumptions as the stopping model.

## Energy audit (Step 12)
A, B and C pass on the 0–40–0 km/h cycle at SOC 0.20 and 25 °C.
Balance residual: 0.0000 J against a 0.1% tolerance.
Friction force checked on all 1200 regen calls (split error 0, no negative friction).
Timing fix: regen is evaluated at mid-step speed, matching the energy integration.
Earlier figures (A 127.77 kJ, B 126.68 kJ) and the pre-fix values are superseded.