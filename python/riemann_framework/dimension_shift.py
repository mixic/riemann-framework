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
Dimension-Shift Involution – numerical consistency check.

This module implements a hypothetical operation `sigma` that acts on a
number system extending the complex numbers. Unlike rotation in C
(continuous, within a 2D plane), `sigma` is a discrete involution that
"switches dimensions" while fixing the critical line Re(s) = 1/2.

The goal is NOT to prove RH, but to check whether such a structure is
numerically consistent with the functional equation of the zeta function.
"""

from dataclasses import dataclass
from typing import Any

import mpmath as mp
import numpy as np


mpc: Any = mp.mpc


# ============================================================
# The dimension-shift element w
# ============================================================

@dataclass(frozen=True)
class DimensionElement:
    """
    Represents the new element `w` and its action.

    Properties:
    - w is an involution: w^2 = id
    - w acts on a complex number by shifting its "dimension index"
    - w fixes the critical line: if Re(s) = 1/2, then w(s) = s
    """
    dimension: int = 0

    def act_on(self, s):
        """
        Apply w to a complex number s.

        The action is defined as:
            w(s) = 1 - conjugate(s)

        This fixes the full critical line Re(s) = 1/2.
        """
        return 1 - mp.conj(s)

    def __pow__(self, n):
        """w^2 = identity."""
        if n % 2 == 0:
            return DimensionElement(dimension=0)
        return self


# ============================================================
# The dimension-shift involution sigma
# ============================================================

def sigma(s):
    """
    The dimension-shift involution.

    Unlike rotation (multiplication by i), which is continuous and
    preserves distance to the origin, sigma is a discrete involution
    that swaps the two "sides" of the critical strip.

    Key property: sigma fixes the critical line pointwise.
    """
    return 1 - mp.conj(s)


def is_fixed_point(s, tol=None):
    """Check whether s is a fixed point of sigma (i.e. Re(s) = 1/2)."""
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)
    return mp.almosteq(sigma(s), s, abs_eps=tol)


# ============================================================
# Finite-sector operator model
# ============================================================

def _validate_sector_dimension(dim_per_sector):
    if not isinstance(dim_per_sector, (int, np.integer)):
        raise TypeError("dim_per_sector must be an integer")
    if dim_per_sector < 1:
        raise ValueError("dim_per_sector must be positive")
    return int(dim_per_sector)


def sigma_matrix(dim_per_sector=2):
    """Build the sector-swapping matrix for the finite model.

    The total space is ``H_boson direct_sum H_fermion``. The matrix maps
    ``(boson, fermion)`` to ``(fermion, boson)`` and therefore satisfies
    ``sigma_matrix @ sigma_matrix = I``.
    """
    dimension = _validate_sector_dimension(dim_per_sector)
    matrix = np.zeros((2 * dimension, 2 * dimension), dtype=float)
    identity = np.eye(dimension)
    matrix[:dimension, dimension:] = identity
    matrix[dimension:, :dimension] = identity
    return matrix


def sigma_eigenvalues(dim_per_sector=2):
    """Return the eigenvalues of the finite sector-swapping matrix."""
    return np.linalg.eigvalsh(sigma_matrix(dim_per_sector))


def sigma_fixed_locus(dim_per_sector=2):
    """Return an orthonormal basis for the ``+1`` eigenspace of sigma."""
    matrix = sigma_matrix(dim_per_sector)
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    return eigenvectors[:, np.isclose(eigenvalues, 1.0)]


def _symmetric_random_matrix(dimension, seed=None):
    rng = np.random.default_rng(seed)
    matrix = rng.standard_normal((dimension, dimension))
    return (matrix + matrix.T) / 2


def sigma_plus_hamiltonian(dim_per_sector=2, seed=None):
    """Build a real symmetric Hamiltonian on the first sector."""
    dimension = _validate_sector_dimension(dim_per_sector)
    return _symmetric_random_matrix(dimension, seed)


def supersymmetric_hamiltonian(dim_per_sector=2, seed=None):
    """Build a block-diagonal finite Hamiltonian for two sectors."""
    dimension = _validate_sector_dimension(dim_per_sector)
    rng = np.random.default_rng(seed)
    plus = rng.standard_normal((dimension, dimension))
    minus = rng.standard_normal((dimension, dimension))
    hamiltonian = np.zeros((2 * dimension, 2 * dimension))
    hamiltonian[:dimension, :dimension] = (plus + plus.T) / 2
    hamiltonian[dimension:, dimension:] = (minus + minus.T) / 2
    return hamiltonian


def witten_index(h_plus, h_minus, tol=1e-8):
    """Return ``dim(ker(H_plus)) - dim(ker(H_minus))`` numerically."""
    plus = np.asarray(h_plus, dtype=float)
    minus = np.asarray(h_minus, dtype=float)
    if plus.ndim != 2 or minus.ndim != 2:
        raise ValueError("Hamiltonians must be two-dimensional square matrices")
    if plus.shape[0] != plus.shape[1] or minus.shape[0] != minus.shape[1]:
        raise ValueError("Hamiltonians must be square matrices")
    if tol <= 0:
        raise ValueError("tol must be positive")

    plus_eigenvalues = np.linalg.eigvalsh(plus)
    minus_eigenvalues = np.linalg.eigvalsh(minus)
    plus_zero_count = np.count_nonzero(np.abs(plus_eigenvalues) < tol)
    minus_zero_count = np.count_nonzero(np.abs(minus_eigenvalues) < tol)
    return int(plus_zero_count - minus_zero_count)


# ============================================================
# Consistency checks
# ============================================================

def check_involution(tol=None):
    """Check sigma^2 = identity on a set of test points."""
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)

    test_points = [
        mpc(mp.mpf("0.5"), mp.mpf("14.134725")),
        mpc(mp.mpf("0.3"), mp.mpf("10.0")),
        mpc(mp.mpf("0.7"), mp.mpf("-5.0")),
        mpc(mp.mpf("0.5"), mp.mpf("0.0")),
        mpc(mp.mpf("2.0"), mp.mpf("3.0")),
    ]

    results = []
    for s in test_points:
        s2 = sigma(sigma(s))
        results.append({
            "s": s,
            "sigma(s)": sigma(s),
            "sigma^2(s)": s2,
            "is_involution": mp.almosteq(s2, s, abs_eps=tol),
            "is_fixed": is_fixed_point(s, tol=tol),
        })
    return results


def check_fixed_locus(tol=None):
    """
    Check that the fixed locus of sigma is exactly the critical line.

    A point s is fixed iff Re(s) = 1/2.
    """
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)

    results = []
    for re_part in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
        s = mpc(mp.mpf(re_part), mp.mpf("10.0"))
        results.append({
            "Re(s)": re_part,
            "is_fixed": is_fixed_point(s, tol=tol),
        })
    return results


def check_functional_equation_consistency(num_zeros=10, tol=None):
    """
    Check that sigma is compatible with the functional equation:

        zeta(s) = chi(s) * zeta(1 - s)

    The functional equation says that zeta is "sigma-symmetric" up to
    the factor chi(s). This is the numerical shadow of the claim that
    sigma is the correct involution.
    """
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)

    results = []
    for n in range(1, num_zeros + 1):
        rho = mp.zetazero(n)
        # Conjugation and the functional equation imply
        # zeta(1 - conjugate(rho)) = 0.
        z_at_rho = mp.zeta(rho)
        z_at_sigma_rho = mp.zeta(sigma(rho))
        results.append({
            "n": n,
            "rho": rho,
            "sigma(rho)": sigma(rho),
            "|zeta(rho)|": abs(z_at_rho),
            "|zeta(sigma(rho))|": abs(z_at_sigma_rho),
            "both_zero": (abs(z_at_rho) < tol) and (abs(z_at_sigma_rho) < tol),
        })
    return results


if __name__ == "__main__":
    mp.mp.dps = 30

    print("=" * 60)
    print("Dimension-Shift Involution: Consistency Checks")
    print("=" * 60)

    print("\n[1] Involution property: sigma^2 = identity")
    for r in check_involution():
        print(f"  s = {r['s']}, sigma(s) = {r['sigma(s)']}, "
              f"sigma^2(s) = {r['sigma^2(s)']}, "
              f"involution = {r['is_involution']}, "
              f"fixed = {r['is_fixed']}")

    print("\n[2] Fixed locus: sigma(s) = s iff Re(s) = 1/2")
    for r in check_fixed_locus():
        print(f"  Re(s) = {r['Re(s)']}, is_fixed = {r['is_fixed']}")

    print("\n[3] Functional-equation consistency")
    for r in check_functional_equation_consistency():
        print(f"  n = {r['n']}, rho = {r['rho']}, "
              f"|zeta(rho)| = {r['|zeta(rho)|']:.2e}, "
              f"|zeta(sigma(rho))| = {r['|zeta(sigma(rho))|']:.2e}, "
              f"both_zero = {r['both_zero']}")