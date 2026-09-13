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
Quantum chaos analysis for the Riemann zeros and candidate operators.

Provides tools to compute the level-spacing statistics of the
Riemann zeros and compare them to GUE and Poisson distributions.
"""

import numpy as np
import mpmath as mp

from .statistics import (
    level_spacings,
    mean_r_ratio,
    classify_statistics,
    ks_test_against,
)


def riemann_zero_heights(n):
    """
    Return the imaginary parts gamma_n of the first n non-trivial zeros.

    These are the raw eigenvalues to analyze.
    """
    return np.array([float(mp.im(mp.zetazero(k))) for k in range(1, n + 1)])


def analyze_riemann_zeros(n=100, unfold=True):
    """
    Analyze the level-spacing statistics of the first n Riemann zeros.

    Returns a dict with:
      - mean_r: the mean r-ratio
      - classification: best-fit reference distribution
      - ks_gue: KS test against GUE
      - ks_poisson: KS test against Poisson
    """
    gammas = riemann_zero_heights(n)
    mean_r = mean_r_ratio(gammas, unfold=unfold)
    classification = classify_statistics(gammas, unfold=unfold)
    ks_gue = ks_test_against(gammas, reference="gue", unfold=unfold)
    ks_poisson = ks_test_against(gammas, reference="poisson", unfold=unfold)

    return {
        "n_zeros": n,
        "mean_r": mean_r,
        "classification": classification,
        "ks_gue": ks_gue,
        "ks_poisson": ks_poisson,
    }


def gue_random_matrix_eigenvalues(dim=100, seed=None):
    """
    Generate eigenvalues of a GUE random matrix.

    A GUE matrix H is Hermitian with:
      - diagonal entries: real Gaussian
      - off-diagonal entries: complex Gaussian
    """
    rng = np.random.default_rng(seed)
    n = dim
    # Complex Gaussian matrix
    A = (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))) / np.sqrt(2)
    # Hermitian part
    H = (A + A.conj().T) / 2
    eigenvalues = np.linalg.eigvalsh(H)
    return eigenvalues


def goe_random_matrix_eigenvalues(dim=100, seed=None):
    """Generate eigenvalues of a GOE random matrix (real symmetric)."""
    rng = np.random.default_rng(seed)
    n = dim
    A = rng.standard_normal((n, n))
    H = (A + A.T) / 2
    return np.linalg.eigvalsh(H)


def poisson_eigenvalues(n=100, seed=None):
    """Generate a Poisson-distributed spectrum (integrable system)."""
    rng = np.random.default_rng(seed)
    spacings = rng.exponential(1.0, size=n)
    return np.cumsum(spacings)


def compare_reference_systems(n=100, seed=42):
    """
    Compare the Riemann zeros to GUE, GOE, and Poisson reference systems.

    Returns a dict with mean r-ratios for each.
    """
    gammas = riemann_zero_heights(n)

    gue_eigs = gue_random_matrix_eigenvalues(dim=n, seed=seed)
    goe_eigs = goe_random_matrix_eigenvalues(dim=n, seed=seed)
    poisson_eigs = poisson_eigenvalues(n=n, seed=seed)

    return {
        "riemann": mean_r_ratio(gammas),
        "gue": mean_r_ratio(gue_eigs),
        "goe": mean_r_ratio(goe_eigs),
        "poisson": mean_r_ratio(poisson_eigs),
        "reference_values": {
            "poisson": 0.386,
            "goe": 0.530,
            "gue": 0.599,
        },
    }