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
"""Run the dimension-shift chaos analysis and produce plots.

Usage, from the repository root:

    python scripts/run_dimension_shift_chaos.py

Writes `output/dimension_shift_spectrum.png`, `dimension_shift_coupling_sweep.png`
and `dimension_shift_symmetry_sweep.png`.

The third figure is a **negative control**, not a feature sweep: it violates
`[H, sigma] = 0`, which puts the model outside the Dimension-Shift Hypothesis
entirely. Its filename is historical; the panel title says what it is.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

import numpy as np
import matplotlib.pyplot as plt

from riemann_framework.dimension_shift_chaos import (
    build_dimension_shift_hamiltonian,
    analyze_dimension_shift,
    sweep_coupling,
    sigma_control,
    compare_to_riemann,
)
from riemann_framework.quantum_chaos import riemann_zero_heights
from riemann_framework.statistics import (
    level_spacings,
    gue_spacing_pdf,
    poisson_spacing_pdf,
    goe_spacing_pdf,
)
from riemann_framework.zeta import set_precision

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

set_precision(25)

# Reference values
R_POISSON = 0.386
R_GOE = 0.530
R_GUE = 0.599


# ============================================================
# Plot 1: Spectrum vs Riemann zeros
# ============================================================

def plot_spectrum_comparison(dim_per_sector=30, coupling=1.0, seed=42):
    """Compare the full spectrum and one sigma-sector to the Riemann zeros."""
    analysis = analyze_dimension_shift(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        seed=seed,
    )
    eigs = analysis["eigenvalues"]
    sector = analysis["sector_plus"]
    gammas = riemann_zero_heights(len(eigs))

    from riemann_framework.statistics import unfold_spectrum

    eigs_unfolded = unfold_spectrum(eigs)
    gammas_unfolded = unfold_spectrum(gammas)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.scatter(np.arange(len(eigs_unfolded)), eigs_unfolded,
               s=10, color="blue", label="full spectrum (both sectors)")
    ax.scatter(np.arange(len(gammas_unfolded)), gammas_unfolded,
               s=10, color="red", alpha=0.5, label="Riemann zeros")
    ax.set_xlabel("Index n")
    ax.set_ylabel("Unfolded level")
    ax.set_title(
        f"Unfolded spectra (sigma-sector mean r = {analysis['mean_r_plus']:.3f})"
    )
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.hist(level_spacings(eigs), bins=20, density=True, alpha=0.5,
            color="blue", label="full spectrum")
    if sector is not None:
        ax.hist(level_spacings(sector), bins=20, density=True, alpha=0.5,
                color="teal", label="single sigma-sector")
    ax.hist(level_spacings(gammas), bins=20, density=True, alpha=0.5,
            color="red", label="Riemann zeros")
    s = np.linspace(0.01, 3.0, 200)
    ax.plot(s, gue_spacing_pdf(s), "k-", linewidth=1.5, label="GUE (theory)")
    ax.plot(s, goe_spacing_pdf(s), "k:", linewidth=1.5, label="GOE (theory)")
    ax.plot(s, poisson_spacing_pdf(s), "k--", linewidth=1.5, label="Poisson (theory)")
    ax.set_xlabel("Level spacing s")
    ax.set_ylabel("P(s)")
    ax.set_title("Level-spacing distributions")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "dimension_shift_spectrum.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


# ============================================================
# Plot 2: Coupling sweep
# ============================================================

def plot_coupling_sweep(dim_per_sector=30, seed=42):
    """The full spectrum against a single sector, across the coupling."""
    couplings = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]
    results = sweep_coupling(
        dim_per_sector=dim_per_sector,
        coupling_values=couplings,
        seed=seed,
    )

    means = [r["mean_r_full"] for r in results]
    sectors = [r["mean_r_plus"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(couplings, means, "o-", color="darkblue", linewidth=2,
            markersize=8, label="full spectrum (superposition of sectors)")
    ax.plot(couplings, sectors, "s--", color="teal", linewidth=1.6,
            markersize=6, label="single sigma-sector")

    ax.axhline(R_POISSON, color="red", linestyle="--", linewidth=1.5,
               label=f"Poisson ({R_POISSON})")
    ax.axhline(R_GOE, color="orange", linestyle=":", linewidth=1.5,
               label=f"GOE ({R_GOE})")
    ax.axhline(R_GUE, color="green", linestyle="-.", linewidth=1.5,
               label=f"GUE ({R_GUE})")

    ax.set_xlabel("Inter-sector coupling (coupling = 0 is exactly degenerate)")
    ax.set_ylabel("Mean r-ratio")
    ax.set_title("Coupling sweep: the full spectrum is mixed, a sector is not")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "dimension_shift_coupling_sweep.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")

    return results


# ============================================================
# Plot 3: Negative control
# ============================================================

def plot_sigma_control(dim_per_sector=30, coupling=1.0, seed=42):
    """The NEGATIVE CONTROL: what happens when `[H, sigma] = 0` is violated.

    This axis used to be called "symmetry breaking" and was swept as if it were a
    tunable feature of the model. It is not: requirement 1 of the DSH is
    `[H, sigma] = 0`, so a broken model is outside the hypothesis and supplies no
    evidence about it. The panel is kept, relabelled, so the failure stays visible.
    """
    values = [0.0, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
    results = sigma_control(
        dim_per_sector=dim_per_sector,
        breaking_values=values,
        coupling=coupling,
        seed=seed,
    )

    means = [r["mean_r_full"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(values, means, "s-", color="darkred", linewidth=2,
            markersize=8, label="violated model (outside the DSH)")

    ax.axhline(R_POISSON, color="red", linestyle="--", linewidth=1.5,
               label=f"Poisson ({R_POISSON})")
    ax.axhline(R_GOE, color="orange", linestyle=":", linewidth=1.5,
               label=f"GOE ({R_GOE})")
    ax.axhline(R_GUE, color="green", linestyle="-.", linewidth=1.5,
               label=f"GUE ({R_GUE})")

    ax.set_xlabel(r"$\sigma$-violation strength (outside the hypothesis)")
    ax.set_ylabel("Mean r-ratio")
    ax.set_title("Negative control: violating [H, sigma] = 0 on purpose")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "dimension_shift_symmetry_sweep.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")

    return results


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("Dimension-Shift Chaos Analysis (sigma-enforced)")
    print("=" * 60)

    print("\n[1] Direct comparison to Riemann zeros")
    comparison = compare_to_riemann(
        dim_per_sector=30,
        coupling=1.0,
        seed=42,
        n_riemann=60,
    )
    print(f"    full spectrum:   mean r = {comparison['model']['mean_r_full']:.4f}")
    print(f"    single sector:   mean r = {comparison['model']['mean_r_plus']:.4f}")
    print(f"    ||[H, sigma]||/||H|| = "
          f"{comparison['model']['sigma_commutator_ratio']:.1e}")
    print(f"    Riemann zeros:   mean r = {comparison['riemann']['mean_r']:.4f}")
    print(f"    Reference values: {comparison['reference_values']}")

    print("\n[2] Coupling sweep")
    coupling_results = plot_coupling_sweep(dim_per_sector=30)
    print("    coupling | full   | sector+ | sector-")
    for row in coupling_results:
        print(f"    {row['coupling']:>8.2f} | {row['mean_r_full']:.4f} | "
              f"{row['mean_r_plus']:.4f} | {row['mean_r_minus']:.4f}")

    print("\n[3] Negative control: sigma violation (NOT part of the hypothesis)")
    control = plot_sigma_control(dim_per_sector=30, coupling=1.0)
    print("    violation | ||[H,sigma]||/||H|| | full mean r | sectors defined")
    for row in control:
        print(f"    {row['sigma_breaking']:>9.2f} | "
              f"{row['sigma_commutator_ratio']:>20.3e} | "
              f"{row['mean_r_full']:.4f} | {row['sector_plus'] is not None}")

    print("\n[4] Generating spectrum comparison plot...")
    plot_spectrum_comparison(dim_per_sector=30, coupling=1.0)

    print("\n Analysis complete.")
    print(" The full spectrum is a superposition of two sectors and is not GUE;")
    print(" a single sector inherits the class of the input blocks. No RH claim.")


if __name__ == "__main__":
    main()
