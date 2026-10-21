import matplotlib.pyplot as plt
import numpy as np

def plot_tornado():
    parameters = [
        'Battery SOC Range (20%-95%)',
        'Battery Temp (-5°C to 25°C)',
        'Battery Current Limit',
        'Supercap Capacitance',
        'Supercap Power Limit',
        'Regen Power Limit',
        'Generator Efficiency',
        'DC-DC Efficiency'
    ]
    
    # Sensitivity swings / energy recovery impact in kJ
    impacts = [180.0, 243.0, 110.0, 95.0, 60.0, 85.0, 45.0, 40.0]

    # Sort parameters by impact magnitude
    sorted_indices = np.argsort(impacts)
    sorted_params = [parameters[i] for i in sorted_indices]
    sorted_impacts = [impacts[i] for i in sorted_indices]

    plt.figure(figsize=(9, 6))
    bars = plt.barh(sorted_params, sorted_impacts, color='tab:purple')
    plt.xlabel('Energy Recovery Impact / Swing (kJ)')
    plt.title('Parameter Sensitivity Tornado Plot (Energy Recovery Impact)')
    plt.grid(axis='x', linestyle='--', alpha=0.7)

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 3, bar.get_y() + bar.get_height()/2.0, f'{width:.1f} kJ', ha='left', va='center')

    plt.tight_layout()
    plt.savefig('plot_8_tornado.png')
    plt.show()

if __name__ == '__main__':
    plot_tornado()