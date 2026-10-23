import matplotlib.pyplot as plt
import numpy as np

def plot_sensitivity():
    # Data from sensitivity analysis
    soc_levels = [0.20, 0.50, 0.80, 0.90, 0.95]
    
    # Recovered energy (kJ) at 25°C for Config B vs Config C
    config_b_25c = [500.4, 537.8, 571.5, 488.6, 282.6]
    config_c_25c = [663.8, 671.9, 679.1, 672.6, 506.5]

    plt.figure(figsize=(9, 5))
    plt.plot(np.array(soc_levels)*100, config_b_25c, marker='o', label='Config B (Battery-Aware)', linewidth=2)
    plt.plot(np.array(soc_levels)*100, config_c_25c, marker='s', label='Config C (Adaptive + Supercap)', linewidth=2)

    plt.xlabel('Initial Battery SOC (%)')
    plt.ylabel('Recovered Energy (kJ)')
    plt.title('Energy Recovery vs. Initial SOC (at 25°C)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig('plot_6_soc_sensitivity.png')
    plt.show()

if __name__ == '__main__':
    plot_sensitivity()