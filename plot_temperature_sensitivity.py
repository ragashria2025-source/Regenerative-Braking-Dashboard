import matplotlib.pyplot as plt

def plot_temperature_sensitivity():
    # Temperatures (°C)
    temperatures = [-5.0, 10.0, 25.0]
    
    # Recovered energy (kJ) at 50% SOC from sensitivity table
    config_b_50pct = [0.0, 535.8, 537.8]
    config_c_50pct = [243.0, 663.4, 671.9] # Note: At -5°C, battery charging is disabled, but Config C captures energy in the supercapacitor

    plt.figure(figsize=(8, 5))
    plt.plot(temperatures, config_b_50pct, marker='o', label='Config B (Battery-Aware)', linewidth=2)
    plt.plot(temperatures, config_c_50pct, marker='s', label='Config C (Adaptive + Supercap)', linewidth=2)

    plt.xlabel('Battery Temperature (°C)')
    plt.ylabel('Recovered Energy (kJ)')
    plt.title('Energy Recovery vs. Battery Temperature (at 50% SOC)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig('plot_7_temp_sensitivity.png')
    plt.show()

if __name__ == '__main__':
    plot_temperature_sensitivity()