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
Dimension-Shift Hamiltonian – chaos analysis pipeline.

This module connects the dimension-shift involution to the quantum
chaos analysis. It builds a family of Hamiltonians parameterized by
the sector coupling, computes their spectra, and classifies them
against GUE / GOE / Poisson statistics.

The goal is to iterate on the model until the spectrum of the
dimension-shift Hamiltonian matches the GUE statistics of the
Riemann zeros.
"""

import numpy as np

from .statistics import (
    mean_r_ratio,
    classify_statistics,
    ks_test_against,
    level_spacings,
)
from .quantum_chaos import riemann_zero_heights


# ============================================================
# The dimension-shift Hamiltonian
# ============================================================

def build_sector_hamiltonian(dim_per_sector, seed=None):
    """
    Build the intra-sector Hamiltonian H0.

    This is the "unperturbed" Hamiltonian within each sector.
    It is a real symmetric random matrix (GOE-like) to start with.
    """
    rng = np.random.default_rng(seed)
    d = dim_per_sector
    A = rng.standard_normal((d, d))
    H0 = (A + A.T) / 2.0
    return H0


def build_coupling_matrix(dim_per_sector, coupling=1.0, seed=None):
    """
    Build the inter-sector coupling V.

    V connects the bosonic and fermionic sectors. The dimension-shift
    involution sigma acts on V by swapping the sectors.

    The parameter `coupling` controls the strength of the mixing
    between sectors. At coupling=0, the sectors decouple; at
    coupling=1, the mixing is maximal.
    """
    rng = np.random.default_rng(seed)
    d = dim_per_sector
    B = rng.standard_normal((d, d))
    V = coupling * B
    return V


def build_dimension_shift_hamiltonian(
    dim_per_sector=20,
    coupling=1.0,
    symmetry_breaking=0.0,
    seed=None,
):
    """
    Build the full dimension-shift Hamiltonian.

    The Hamiltonian acts on the direct sum H = H_b ⊕ H_f:

        H = [[ H_b ,  V  ],
             [ V^T ,  H_f ]]

    where:
      - H_b and H_f are intra-sector Hamiltonians (real symmetric)
      - V is the inter-sector coupling
      - symmetry_breaking adds a small perturbation that breaks
        the exact degeneracy between the sectors

    Parameters:
        dim_per_sector: dimension of each sector
        coupling: strength of the inter-sector mixing
        symmetry_breaking: strength of the sector asymmetry
        seed: random seed for reproducibility

    Returns:
        A real symmetric matrix of size (2*dim_per_sector).
    """
    rng = np.random.default_rng(seed)
    d = dim_per_sector

    H_b = build_sector_hamiltonian(d, seed=rng.integers(0, 2**31))
    H_f = build_sector_hamiltonian(d, seed=rng.integers(0, 2**31))

    # Add asymmetry between the sectors
    if symmetry_breaking > 0:
        H_f = H_f + symmetry_breaking * np.eye(d)

    V = build_coupling_matrix(d, coupling=coupling, seed=rng.integers(0, 2**31))

    H = np.zeros((2 * d, 2 * d))
    H[:d, :d] = H_b
    H[d:, d:] = H_f
    H[:d, d:] = V
    H[d:, :d] = V.T

    # Symmetrize (should already be symmetric)
    H = (H + H.T) / 2.0
    return H


# ============================================================
# Analysis pipeline
# ============================================================

def analyze_dimension_shift(
    dim_per_sector=20,
    coupling=1.0,
    symmetry_breaking=0.0,
    seed=42,
    unfold=True,
):
    """
    Analyze the spectrum of the dimension-shift Hamiltonian.

    Returns a dict with:
      - eigenvalues: the raw eigenvalues
      - mean_r: the mean r-ratio
      - classification: best-fit reference
      - ks_gue, ks_poisson: KS statistics
    """
    H = build_dimension_shift_hamiltonian(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        symmetry_breaking=symmetry_breaking,
        seed=seed,
    )
    eigenvalues = np.linalg.eigvalsh(H)

    mean_r = mean_r_ratio(eigenvalues, unfold=unfold)
    classification = classify_statistics(eigenvalues, unfold=unfold)
    ks_gue = ks_test_against(eigenvalues, reference="gue", unfold=unfold)
    ks_poisson = ks_test_against(eigenvalues, reference="poisson", unfold=unfold)

    return {
        "dim_per_sector": dim_per_sector,
        "coupling": coupling,
        "symmetry_breaking": symmetry_breaking,
        "seed": seed,
        "eigenvalues": eigenvalues,
        "mean_r": mean_r,
        "classification": classification,
        "ks_gue": ks_gue,
        "ks_poisson": ks_poisson,
    }


def sweep_coupling(
    dim_per_sector=20,
    coupling_values=None,
    symmetry_breaking=0.0,
    seed=42,
):
    """
    Sweep over the coupling parameter and analyze the resulting spectra.

    This is the key iteration loop: it shows how the statistics change
    as the dimension-shift coupling is varied.
    """
    if coupling_values is None:
        coupling_values = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]

    results = []
    for c in coupling_values:
        r = analyze_dimension_shift(
            dim_per_sector=dim_per_sector,
            coupling=c,
            symmetry_breaking=symmetry_breaking,
            seed=seed,
        )
        results.append({
            "coupling": c,
            "mean_r": r["mean_r"],
            "best_fit": r["classification"]["best_fit"],
            "ks_gue": r["ks_gue"]["ks_stat"],
            "ks_poisson": r["ks_poisson"]["ks_stat"],
        })
    return results


def sweep_symmetry_breaking(
    dim_per_sector=20,
    symmetry_breaking_values=None,
    coupling=1.0,
    seed=42,
):
    """
    Sweep over the symmetry-breaking parameter.

    This tests whether a small asymmetry between the sectors pushes
    the statistics from GOE toward GUE (as required by the
    time-reversal symmetry breaking of the Riemann zeros).
    """
    if symmetry_breaking_values is None:
        symmetry_breaking_values = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]

    results = []
    for sb in symmetry_breaking_values:
        r = analyze_dimension_shift(
            dim_per_sector=dim_per_sector,
            coupling=coupling,
            symmetry_breaking=sb,
            seed=seed,
        )
        results.append({
            "symmetry_breaking": sb,
            "mean_r": r["mean_r"],
            "best_fit": r["classification"]["best_fit"],
            "ks_gue": r["ks_gue"]["ks_stat"],
            "ks_poisson": r["ks_poisson"]["ks_stat"],
        })
    return results


def compare_to_riemann(
    dim_per_sector=20,
    coupling=1.0,
    symmetry_breaking=0.0,
    seed=42,
    n_riemann=100,
):
    """
    Compare the dimension-shift spectrum to the Riemann zeros.
    """
    ds = analyze_dimension_shift(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        symmetry_breaking=symmetry_breaking,
        seed=seed,
    )
    gammas = riemann_zero_heights(n_riemann)
    riemann_mean_r = mean_r_ratio(gammas)

    return {
        "dimension_shift": {
            "mean_r": ds["mean_r"],
            "best_fit": ds["classification"]["best_fit"],
            "ks_gue": ds["ks_gue"]["ks_stat"],
            "ks_poisson": ds["ks_poisson"]["ks_stat"],
        },
        "riemann": {
            "mean_r": riemann_mean_r,
            "n_zeros": n_riemann,
        },
        "reference_values": {
            "poisson": 0.386,
            "goe": 0.530,
            "gue": 0.599,
        },
    }