from drive_cycle_battery import simulate_drive_cycle


def simulate_configuration_b():

    results, final_soc, regen_energy, battery_energy, friction_energy = (
        simulate_drive_cycle()
    )

    print("\n")
    print("=" * 105)
    print("CONFIGURATION B - ADAPTIVE BATTERY-AWARE REGENERATIVE BRAKING")
    print("=" * 105)

    print(
        f"{'Time':>6} "
        f"{'Speed':>8} "
        f"{'Brake':>10} "
        f"{'Regen':>10} "
        f"{'Friction':>10} "
        f"{'Regen P':>10} "
        f"{'Batt P':>10} "
        f"{'SOC':>8}"
    )

    print("-" * 105)

    for r in results:

        print(
            f"{r['time_s']:6.1f} "
            f"{r['speed_mps']:8.3f} "
            f"{r['braking_force_N']:10.1f} "
            f"{r['regen_force_N']:10.1f} "
            f"{r['friction_force_N']:10.1f} "
            f"{r['regen_power_W']/1000:10.2f} "
            f"{r['battery_power_W']/1000:10.2f} "
            f"{r['soc']:8.4f}"
        )

    print("-" * 105)

    print(
        f"Final SOC                 : "
        f"{final_soc:.6f}"
    )

    print(
        f"Regenerative energy      : "
        f"{regen_energy / 1000:.3f} kJ"
    )

    print(
        f"Battery accepted energy  : "
        f"{battery_energy / 1000:.3f} kJ"
    )

    print(
        f"Friction braking energy  : "
        f"{friction_energy / 1000:.3f} kJ"
    )

    print("=" * 105)


if __name__ == "__main__":
    simulate_configuration_b()