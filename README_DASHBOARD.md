# VSE Regenerative Braking Dashboard

An interactive Streamlit dashboard for the A/B/C regenerative-braking simulation.

## Run it in VS Code (Windows)

1. Extract this folder somewhere convenient, for example `C:\Users\YourName\Desktop\vse_dashboard_project`.
2. Open VS Code → **File → Open Folder…** → select the extracted folder.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

5. Activate it in PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt terminal instead and run:

   ```bat
   .venv\Scripts\activate.bat
   ```

6. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Start the dashboard:

   ```powershell
   streamlit run app.py
   ```

8. Your browser should open automatically. If it does not, copy the local URL printed in the terminal (usually `http://localhost:8501`) into your browser.

## What is included

- **Overview:** project purpose, cycle profile, and quick comparison.
- **Live simulator:** compare battery-accepted energy, friction braking, final SOC, and capacitor metrics.
- **How it works:** pipeline, A/B/C definitions, and core equations.
- **Model assumptions:** reads the parameter register from `parameters.py`.
- **Results & limitations:** current-run comparison, CSV export, and limitations to disclose.

The starting SOC and battery temperature controls are in the sidebar and update the simulation results.

## Important model notes

The current project uses a short illustrative 0–40–0 km/h cycle and several assumed parameters. Results are model outputs, not validated real-vehicle performance. Configuration A uses a fixed 50 kW cap; B sends available regenerative power to the battery model; C adds a supercapacitor buffer. The app keeps remaining capacitor energy separate from battery-accepted energy.
