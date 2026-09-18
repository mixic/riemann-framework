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
Run the DSIN simulation, compare it against the BB84 baseline, and plot.

Usage (from anywhere):
    python scripts/run_dsin_verification.py

Writes plots into ``output/``. Every number here comes from a toy model; none
of it is a security proof.
"""

import os
from pathlib import Path
import sys

import runpy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

# The plots are written relative to the repository root, so re-exec from there
# when invoked from elsewhere. The environment variable stops the re-run from
# recursing.
if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_DSIN_VERIFICATION_BOOTSTRAPPED"
):
    os.environ["_DSIN_VERIFICATION_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit()

import numpy as np
import matplotlib.pyplot as plt

from riemann_framework.dsin import (
    run_simulation,
    build_sigma,
    build_channel_hamiltonian,
    commutator_norm,
)
from riemann_framework.bb84 import (
    DEFAULT_DETECTION_THRESHOLD as DEFAULT_BB84_THRESHOLD,
    run_bb84,
)

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# Plot 1: BER vs noise
# ============================================================

def plot_ber_vs_noise():
    """Plot the bit error rate as a function of noise strength."""
    noise_levels = np.linspace(0.0, 1.0, 11)
    ber_depol, ber_phase, ber_amp = [], [], []

    for p in noise_levels:
        ber_depol.append(run_simulation(
            n_bits=500, noise_type="depolarizing",
            noise_param=p, seed=42).ber)
        ber_phase.append(run_simulation(
            n_bits=500, noise_type="phase",
            noise_param=p * np.pi, seed=42).ber)
        ber_amp.append(run_simulation(
            n_bits=500, noise_type="amplitude",
            noise_param=p, seed=42).ber)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(noise_levels, ber_depol, "o-", label="Depolarizing")
    ax.plot(noise_levels, ber_phase, "s-", label="Phase (symmetry-breaking)")
    ax.plot(noise_levels, ber_amp, "^-", label="Amplitude damping")
    ax.axhline(0.5, color="gray", linestyle="--", label="Random guess")
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
# Plot 2: Attack analysis
# ============================================================

def plot_attack_analysis():
    """Plot the BER and detection rate under attack."""
    attack_strengths = np.linspace(0.0, 1.0, 11)
    bers, detections = [], []

    for eps in attack_strengths:
        r = run_simulation(
            n_bits=500, attack_type="symmetry_breaking",
            attack_param=eps, seed=42)
        bers.append(r.ber)
        detections.append(r.detection_rate)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(attack_strengths, bers, "o-", color="red", label="BER")
    ax.plot(attack_strengths, detections, "s-", color="blue",
            label="Detection rate")
    ax.axhline(0.5, color="gray", linestyle="--", label="Random guess")
    ax.set_xlabel("Attack strength")
    ax.set_ylabel("Rate")
    ax.set_title("DSIN: BER and detection under symmetry-breaking attack")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = OUTPUT_DIR / "dsin_attack_analysis.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


# ============================================================
# Plot 3: DSIN vs BB84
# ============================================================

def plot_dsin_vs_bb84():
    """
    Compare DSIN with BB84 under depolarizing noise.

    The two protocols do not detect eavesdropping the same way. DSIN watches a
    per-round symmetry observable, so its detection rate is a genuine per-round
    frequency. BB84 has no per-round detection event: it estimates the error
    rate on the sifted key and aborts if it exceeds a threshold. The right-hand
    panel therefore plots DSIN's detection rate against BB84's sifted-key error
    rate -- the statistic BB84 actually thresholds -- not BB84's 0/1 verdict.
    """
    noise_levels = np.linspace(0.0, 0.5, 11)
    dsin_ber, bb84_ber = [], []
    dsin_det, bb84_qber = [], []

    for p in noise_levels:
        d = run_simulation(
            n_bits=500, noise_type="depolarizing",
            noise_param=p, seed=42)
        b = run_bb84(
            n_bits=1000, noise_type="depolarizing",
            noise_param=p, seed=42)
        dsin_ber.append(d.ber)
        bb84_ber.append(b.ber)
        dsin_det.append(d.detection_rate)
        bb84_qber.append(b.ber)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    ax.plot(noise_levels, dsin_ber, "o-", label="DSIN")
    ax.plot(noise_levels, bb84_ber, "s-", label="BB84 (sifted-key QBER)")
    ax.set_xlabel("Depolarizing noise")
    ax.set_ylabel("BER")
    ax.set_title("BER: DSIN vs BB84")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(noise_levels, dsin_det, "o-", label="DSIN symmetry-break rate")
    ax.plot(noise_levels, bb84_qber, "s-", label="BB84 sifted-key QBER")
    ax.axhline(DEFAULT_BB84_THRESHOLD, color="gray", linestyle="--",
               label=f"BB84 abort threshold ({DEFAULT_BB84_THRESHOLD})")
    ax.set_xlabel("Depolarizing noise")
    ax.set_ylabel("Rate")
    ax.set_title("What each protocol measures")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "dsin_vs_bb84.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


# ============================================================
# Plot 4: Commutator norm
# ============================================================

def plot_commutator_norm():
    """Verify that [H, sigma] = 0 for the channel Hamiltonian.

    The norms come out exactly ``0.0`` at machine precision, which a log axis
    cannot render, so they are plotted against a floor and the floor is stated
    in the legend. If the channel ever stopped commuting, the curve would lift
    off the floor immediately.
    """
    dims = [2, 4, 6, 8, 10, 12]
    norms = []
    for d in dims:
        H = build_channel_hamiltonian(d, coupling=1.0, seed=42)
        sigma = build_sigma(d)
        norms.append(commutator_norm(H, sigma))

    floor = 1e-18
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dims, [max(n, floor) for n in norms], "o-", color="darkgreen",
            label=rf"$\|[H, \sigma]\|_F$ (floored at {floor:.0e})")
    ax.set_xlabel("Sector dimension d")
    ax.set_ylabel(r"$\|[H, \sigma]\|_F$")
    ax.set_title(
        f"DSIN: Channel commutes with the involution "
        f"(max norm = {max(norms):.1e})"
    )
    ax.set_yscale("log")
    ax.set_ylim(bottom=floor / 10)
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
    print("=" * 70)
    print("DSIN Verification Simulation")
    print("=" * 70)

    print("\n[1] Ideal channel")
    r = run_simulation(n_bits=1000, seed=42)
    print(f"    BER:            {r.ber:.4f}")
    print(f"    Detection rate: {r.detection_rate:.4f}")
    print(f"    Mean fidelity:  {r.mean_fidelity:.4f}")

    print("\n[2] Depolarizing noise")
    for p in [0.1, 0.3, 0.5]:
        r = run_simulation(n_bits=500, noise_type="depolarizing",
                           noise_param=p, seed=42)
        print(f"    p = {p:.2f}: BER = {r.ber:.4f}, "
              f"detection = {r.detection_rate:.4f}")

    print("\n[3] Symmetry-breaking attack")
    for eps in [0.1, 0.5, 1.0]:
        r = run_simulation(n_bits=500, attack_type="symmetry_breaking",
                           attack_param=eps, seed=42)
        print(f"    eps = {eps:.2f}: BER = {r.ber:.4f}, "
              f"detection = {r.detection_rate:.4f}")

    print("\n[4] Intercept-resend attack (mean over 5 seeds)")
    runs = [run_simulation(n_bits=1000, attack_type="intercept_resend", seed=s)
            for s in range(5)]
    print(f"    BER:            {np.mean([r.ber for r in runs]):.4f}")
    print(f"    Detection rate: {np.mean([r.detection_rate for r in runs]):.4f}")

    print("\n[5] DSIN vs BB84 (depolarizing noise)")
    for p in [0.0, 0.1, 0.2, 0.3]:
        d = run_simulation(n_bits=500, noise_type="depolarizing",
                           noise_param=p, seed=42)
        b = run_bb84(n_bits=1000, noise_type="depolarizing",
                     noise_param=p, seed=42)
        print(f"    p = {p:.2f}: DSIN BER = {d.ber:.4f}, "
              f"BB84 QBER = {b.ber:.4f}, BB84 detected = {b.detected}")

    print("\n[6] Commutator norm")
    for d in [2, 4, 6, 8]:
        H = build_channel_hamiltonian(d, coupling=1.0, seed=42)
        sigma = build_sigma(d)
        print(f"    d = {d}: ||[H, sigma]||_F = "
              f"{commutator_norm(H, sigma):.2e}")

    print("\n[7] Generating plots...")
    plot_ber_vs_noise()
    plot_attack_analysis()
    plot_dsin_vs_bb84()
    plot_commutator_norm()

    print("\n Verification complete.")


if __name__ == "__main__":
    main()
