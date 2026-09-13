"""
Run the dimension-shift chaos analysis and produce plots.

Usage:
    cd python
    python scripts/run_dimension_shift_chaos.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt

from riemann_framework.dimension_shift_chaos import (
    build_dimension_shift_hamiltonian,
    analyze_dimension_shift,
    sweep_coupling,
    sweep_symmetry_breaking,
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

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
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
    """Compare the dimension-shift spectrum to the Riemann zeros."""
    H = build_dimension_shift_hamiltonian(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        seed=seed,
    )
    eigs = np.linalg.eigvalsh(H)
    gammas = riemann_zero_heights(len(eigs))

    # Unfold both
    from riemann_framework.statistics import unfold_spectrum
    eigs_unfolded = unfold_spectrum(eigs)
    gammas_unfolded = unfold_spectrum(gammas)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.scatter(np.arange(len(eigs_unfolded)), eigs_unfolded,
               s=10, color="blue", label="Dimension-shift")
    ax.scatter(np.arange(len(gammas_unfolded)), gammas_unfolded,
               s=10, color="red", alpha=0.5, label="Riemann zeros")
    ax.set_xlabel("Index n")
    ax.set_ylabel("Unfolded level")
    ax.set_title("Unfolded spectra")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.hist(level_spacings(eigs), bins=20, density=True, alpha=0.5,
            color="blue", label="Dimension-shift")
    ax.hist(level_spacings(gammas), bins=20, density=True, alpha=0.5,
            color="red", label="Riemann zeros")
    s = np.linspace(0.01, 3.0, 200)
    ax.plot(s, gue_spacing_pdf(s), "k-", linewidth=1.5, label="GUE (theory)")
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
    """Plot the mean r-ratio as a function of the coupling."""
    couplings = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]
    results = sweep_coupling(
        dim_per_sector=dim_per_sector,
        coupling_values=couplings,
        seed=seed,
    )

    means = [r["mean_r"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(couplings, means, "o-", color="darkblue", linewidth=2,
            markersize=8, label="Dimension-shift model")

    ax.axhline(R_POISSON, color="red", linestyle="--", linewidth=1.5,
               label=f"Poisson ({R_POISSON})")
    ax.axhline(R_GOE, color="orange", linestyle=":", linewidth=1.5,
               label=f"GOE ({R_GOE})")
    ax.axhline(R_GUE, color="green", linestyle="-.", linewidth=1.5,
               label=f"GUE ({R_GUE})")

    ax.set_xlabel("Inter-sector coupling")
    ax.set_ylabel("Mean r-ratio")
    ax.set_title("Coupling sweep: statistics vs. inter-sector mixing")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "dimension_shift_coupling_sweep.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")

    return results


# ============================================================
# Plot 3: Symmetry-breaking sweep
# ============================================================

def plot_symmetry_breaking_sweep(dim_per_sector=30, coupling=1.0, seed=42):
    """Plot the mean r-ratio as a function of the symmetry-breaking."""
    values = [0.0, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
    results = sweep_symmetry_breaking(
        dim_per_sector=dim_per_sector,
        symmetry_breaking_values=values,
        coupling=coupling,
        seed=seed,
    )

    means = [r["mean_r"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(values, means, "s-", color="darkred", linewidth=2,
            markersize=8, label="Dimension-shift model")

    ax.axhline(R_POISSON, color="red", linestyle="--", linewidth=1.5,
               label=f"Poisson ({R_POISSON})")
    ax.axhline(R_GOE, color="orange", linestyle=":", linewidth=1.5,
               label=f"GOE ({R_GOE})")
    ax.axhline(R_GUE, color="green", linestyle="-.", linewidth=1.5,
               label=f"GUE ({R_GUE})")

    ax.set_xlabel("Symmetry-breaking strength")
    ax.set_ylabel("Mean r-ratio")
    ax.set_title("Symmetry-breaking sweep: from GOE toward GUE?")
    ax.legend()
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
    print("Dimension-Shift Chaos Analysis")
    print("=" * 60)

    print("\n[1] Direct comparison to Riemann zeros")
    cmp = compare_to_riemann(
        dim_per_sector=30,
        coupling=1.0,
        seed=42,
        n_riemann=60,
    )
    print(f"    Dimension-shift: mean r = {cmp['dimension_shift']['mean_r']:.4f}, "
          f"best fit = {cmp['dimension_shift']['best_fit']}")
    print(f"    Riemann zeros:   mean r = {cmp['riemann']['mean_r']:.4f}")
    print(f"    Reference values: {cmp['reference_values']}")

    print("\n[2] Coupling sweep")
    coupling_results = plot_coupling_sweep(dim_per_sector=30)
    print("    coupling | mean r | best fit | KS(GUE) | KS(Poisson)")
    for r in coupling_results:
        print(f"    {r['coupling']:>8.2f} | {r['mean_r']:.4f} | "
              f"{r['best_fit']:>7} | {r['ks_gue']:.4f}  | {r['ks_poisson']:.4f}")

    print("\n[3] Symmetry-breaking sweep")
    sb_results = plot_symmetry_breaking_sweep(dim_per_sector=30, coupling=1.0)
    print("    sym break | mean r | best fit | KS(GUE) | KS(Poisson)")
    for r in sb_results:
        print(f"    {r['symmetry_breaking']:>9.2f} | {r['mean_r']:.4f} | "
              f"{r['best_fit']:>7} | {r['ks_gue']:.4f}  | {r['ks_poisson']:.4f}")

    print("\n[4] Generating spectrum comparison plot...")
    plot_spectrum_comparison(dim_per_sector=30, coupling=1.0)

    print("\n Analysis complete.")


if __name__ == "__main__":
    main()