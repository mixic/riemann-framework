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
Run the full quantum chaos analysis and save the results.

Usage (from anywhere):
    python scripts/run_quantum_chaos_analysis.py
"""

from pathlib import Path
import sys
import json

# The importable package lives in `python/`, not at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

import numpy as np
import matplotlib.pyplot as plt

from riemann_framework.quantum_chaos import (
    riemann_zero_heights,
    gue_random_matrix_eigenvalues,
    poisson_eigenvalues,
    analyze_riemann_zeros,
    compare_reference_systems,
)
from riemann_framework.statistics import (
    level_spacings,
    gue_spacing_pdf,
    poisson_spacing_pdf,
    goe_spacing_pdf,
)
from riemann_framework.zeta import set_precision

# `<root>/scripts/…` -> the repository root is `parent.parent`, not
# `parent.parent.parent` (which would be `<root>/..`).
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

set_precision(25)


def plot_spacing_distributions(n=200, seed=42):
    """Plot the level-spacing distributions of the Riemann zeros and references."""
    gammas = riemann_zero_heights(n)
    gue_eigs = gue_random_matrix_eigenvalues(dim=n, seed=seed)
    poisson_eigs = poisson_eigenvalues(n=n, seed=seed)

    spacings_riemann = level_spacings(gammas)
    spacings_gue = level_spacings(gue_eigs)
    spacings_poisson = level_spacings(poisson_eigs)

    s = np.linspace(0.01, 3.0, 200)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(spacings_riemann, bins=30, density=True, alpha=0.5,
            color="blue", label="Riemann zeros")
    ax.hist(spacings_gue, bins=30, density=True, alpha=0.3,
            color="green", label="GUE random matrix")
    ax.hist(spacings_poisson, bins=30, density=True, alpha=0.3,
            color="red", label="Poisson")

    ax.plot(s, gue_spacing_pdf(s), "g-", linewidth=2, label="GUE (theory)")
    ax.plot(s, poisson_spacing_pdf(s), "r--", linewidth=2, label="Poisson (theory)")
    ax.plot(s, goe_spacing_pdf(s), "k:", linewidth=1.5, label="GOE (theory)")

    ax.set_xlabel("Level spacing s")
    ax.set_ylabel("P(s)")
    ax.set_title("Level-spacing distribution: Riemann zeros vs. GUE vs. Poisson")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "quantum_chaos_spacing.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved: {out}")


def main():
    print("=" * 60)
    print("Quantum Chaos Analysis")
    print("=" * 60)

    print("\n[1] Riemann zeros analysis (first 100)")
    result = analyze_riemann_zeros(n=100)
    print(f"    Mean r-ratio: {result['mean_r']:.4f}")
    print(f"    Best fit:     {result['classification']['best_fit']}")
    print(f"    KS to GUE:    {result['ks_gue']['ks_stat']:.4f}")
    print(f"    KS to Poisson:{result['ks_poisson']['ks_stat']:.4f}")

    print("\n[2] Reference systems comparison")
    ref = compare_reference_systems(n=100, seed=42)
    print(f"    Riemann:  {ref['riemann']:.4f}")
    print(f"    GUE:      {ref['gue']:.4f}")
    print(f"    GOE:      {ref['goe']:.4f}")
    print(f"    Poisson:  {ref['poisson']:.4f}")
    print(f"    Reference: {ref['reference_values']}")

    print("\n[3] Generating plots...")
    plot_spacing_distributions(n=200)

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()