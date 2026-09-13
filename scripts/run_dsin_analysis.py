# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Run the DSIN simulation analysis and produce plots.

Usage:
    cd python
    python scripts/run_dsin_analysis.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt

from riemann_framework.dsin import (
    run_simulation,
    build_sigma,
    build_channel_hamiltonian,
    commutator_norm,
)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# Plot 1: BER vs noise
# ============================================================

def plot_ber_vs_noise():
    """Plot the bit error rate as a function of noise strength."""
    noise_levels = np.linspace(0.0, 1.0, 11)
    ber_depol = []
    ber_phase = []

    for p in noise_levels:
        r1 = run_simulation(
            n_bits=500,
            noise_type="depolarizing",
            noise_param=p,
            seed=42,
        )
        r2 = run_simulation(
            n_bits=500,
            noise_type="phase",
            noise_param=p * np.pi,
            seed=42,
        )
        ber_depol.append(r1.ber)
        ber_phase.append(r2.ber)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(noise_levels, ber_depol, "o-", label="Depolarizing noise")
    ax.plot(noise_levels, ber_phase, "s-", label="Phase noise (symmetry-breaking)")
    ax.axhline(0.5, color="gray", linestyle="--", label="Random guess (0.5)")
    ax.set_xlabel("Noise strength")
    ax.set_ylabel("Bit error rate (BER)")
    ax.set_title("DSIN: BER under noise")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "dsin_ber_vs_noise.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


# ============================================================
# Plot 2: BER and detection vs attack strength
# ============================================================

def plot_attack_analysis():
    """Plot the BER and detection rate under attack."""
    attack_strengths = np.linspace(0.0, 1.0, 11)
    bers = []
    detections = []

    for eps in attack_strengths:
        r = run_simulation(
            n_bits=500,
            attack_type="symmetry_breaking",
            attack_param=eps,
            seed=42,
        )
        bers.append(r.ber)
        detections.append(r.detection_rate)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(attack_strengths, bers, "o-", color="red", label="Bit error rate")
    ax.plot(attack_strengths, detections, "s-", color="blue",
            label="Detection rate")
    ax.axhline(0.5, color="gray", linestyle="--", label="Random guess (0.5)")
    ax.set_xlabel("Attack strength ε")
    ax.set_ylabel("Rate")
    ax.set_title("DSIN: BER and eavesdropping detection under attack")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "dsin_attack_analysis.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


# ============================================================
# Plot 3: Commutator norm
# ============================================================

def plot_commutator_norm():
    """Verify that [H, sigma] = 0 for the channel Hamiltonian."""
    dims = [2, 4, 6, 8, 10]
    norms = []

    for d in dims:
        H = build_channel_hamiltonian(d, coupling=1.0, seed=42)
        sigma = build_sigma(d)
        norms.append(commutator_norm(H, sigma))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dims, norms, "o-", color="darkgreen",
            label=r"$\|[H, \sigma]\|_F$")
    ax.set_xlabel("Sector dimension d")
    ax.set_ylabel(r"$\|[H, \sigma]\|_F$")
    ax.set_title("DSIN: Channel commutes with the involution")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3, which="both")

    plt.tight_layout()
    out = OUTPUT_DIR / "dsin_commutator_norm.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("DSIN Quantum Communication – Simulation Analysis")
    print("=" * 60)

    print("\n[1] Ideal channel (no noise, no attack)")
    r = run_simulation(n_bits=1000, seed=42)
    print(f"    BER:            {r.ber:.4f}")
    print(f"    Detection rate: {r.detection_rate:.4f}")

    print("\n[2] Depolarizing noise (p = 0.1, 0.3, 0.5)")
    for p in [0.1, 0.3, 0.5]:
        r = run_simulation(n_bits=500, noise_type="depolarizing",
                           noise_param=p, seed=42)
        print(f"    p = {p:.2f}:  BER = {r.ber:.4f}, "
              f"detection = {r.detection_rate:.4f}")

    print("\n[3] Symmetry-breaking attack (eps = 0.1, 0.5, 1.0)")
    for eps in [0.1, 0.5, 1.0]:
        r = run_simulation(n_bits=500, attack_type="symmetry_breaking",
                           attack_param=eps, seed=42)
        print(f"    eps = {eps:.2f}:  BER = {r.ber:.4f}, "
              f"detection = {r.detection_rate:.4f}")

    print("\n[4] Intercept-resend attack")
    r = run_simulation(n_bits=500, attack_type="intercept_resend", seed=42)
    print(f"    BER:            {r.ber:.4f}")
    print(f"    Detection rate: {r.detection_rate:.4f}")

    print("\n[5] Channel-involution commutator")
    for d in [2, 4, 6, 8]:
        H = build_channel_hamiltonian(d, coupling=1.0, seed=42)
        sigma = build_sigma(d)
        norm = commutator_norm(H, sigma)
        print(f"    d = {d}:  ||[H, sigma]||_F = {norm:.2e}")

    print("\n[6] Generating plots...")
    plot_ber_vs_noise()
    plot_attack_analysis()
    plot_commutator_norm()

    print("\n Analysis complete.")


if __name__ == "__main__":
    main()