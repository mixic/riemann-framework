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
"""What a PT symmetry does to the sector diagnostic, measured.

The diagnostic in the rest of this package needs two things from the symmetry it uses: a
**linear** involution, so that the split is a matrix and the sectors are subspaces, and a
**Hermitian** operator, so that the spectrum is real and has spacing ratios at all. A
PT symmetry supplies neither in the same sense. It is anti-linear, so ``[H, PT] = 0`` is a
statement about a map that is not a matrix; and the operator is not Hermitian, so its
eigenvalues are complex and come in conjugate pairs.

This module measures what happens rather than asserting a correspondence:

* the **dimer**, the two-dimensional model in every PT introduction,
  ``H = [[level + i gamma, g], [g, level - i gamma]]``, whose eigenvalues are
  ``level +/- sqrt(g^2 - gamma^2)``: real below ``gamma / g = 1`` and a conjugate pair
  above it. The exceptional point is exact and is pinned by a test;
* a **random real ensemble** ``H = S + w A`` with ``S`` Gaussian symmetric and ``A``
  Gaussian antisymmetric. Every real matrix is PT-symmetric with respect to complex
  conjugation, so this is the natural ensemble. It is measured to be **broken almost
  surely** for any ``w > 0``: the unbroken phase needs structure, not luck;
* the **pairing**, which is the invariant that does survive. ``conj(E)`` is an eigenvalue
  whenever ``E`` is, and the pairing defect is zero to machine precision even when every
  eigenvalue is complex. That is the property the sector machinery has no representation
  for, because it is not a decomposition into subspaces.

The negative result that the numbers support: applying the adjacent-gap ratio to the real
parts of a broken PT spectrum measures the real parts, not the spectrum. The ratio falls
from the GOE value to the Poisson one as the imaginary parts grow, and a reader who took
that number for a sector count would be reading an artefact of the projection.

No Riemann-hypothesis claim is made here. The dictionary between the critical-line
reflection and a PT-symmetric level pairing is a separate document,
``docs/pt_symmetric_hilbert_polya.md``, and this module adds measurements to it, not
evidence for it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .real_systems import GOE_MEAN_RATIO, POISSON_MEAN_RATIO, mean_ratio

#: Levels of a dimer below this imaginary part count as real.
REAL_TOLERANCE = 1e-9

#: Dimension of the random ensemble the report measures.
DEFAULT_DIMENSION = 120

#: Spectra per point of the ensemble table.
DEFAULT_SEEDS = 40

#: Antisymmetry strengths the report sweeps. Zero is the Hermitian end.
DEFAULT_ANTISYMMETRIES: tuple[float, ...] = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)


# ============================================================
# The dimer: an exact exceptional point
# ============================================================

def pt_dimer(
    gamma: float = 0.5,
    coupling: float = 1.0,
    level: float = 0.0,
) -> np.ndarray:
    """The two-dimensional PT dimer ``[[level + i gamma, g], [g, level - i gamma]]``."""
    if coupling == 0.0:
        raise ValueError("the dimer needs a non-zero coupling")
    if gamma < 0.0:
        raise ValueError("gamma is a gain, so it is non-negative")
    return np.array(
        [
            [level + 1j * gamma, coupling],
            [coupling, level - 1j * gamma],
        ]
    )


def dimer_eigenvalues(
    gamma: float, coupling: float = 1.0, level: float = 0.0
) -> np.ndarray:
    """The closed form ``level +/- sqrt(g^2 - gamma^2)``, sorted by real part.

    Below ``gamma = g`` the square root is real and both levels are real: the PT symmetry
    is unbroken. Above it the square root is imaginary and the two levels are a conjugate
    pair. At ``gamma = g`` they collide, which is the exceptional point.
    """
    root = np.sqrt(complex(coupling**2 - gamma**2))
    values = np.array([level + root, level - root])
    return values[np.lexsort((values.imag, values.real))]


def dimer_table(
    ratios: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0),
    coupling: float = 1.0,
) -> list["DimerRow"]:
    """The exact spectrum as ``gamma / g`` crosses the exceptional point."""
    rows: list[DimerRow] = []
    for ratio in ratios:
        gamma = ratio * coupling
        values = dimer_eigenvalues(gamma, coupling)
        rows.append(
            DimerRow(
                gamma_over_coupling=float(ratio),
                eigenvalues=tuple(complex(value) for value in values),
                unbroken=bool(np.all(np.abs(values.imag) < REAL_TOLERANCE)),
            )
        )
    return rows


@dataclass(frozen=True)
class DimerRow:
    """One point of the dimer's crossover."""

    gamma_over_coupling: float
    eigenvalues: tuple[complex, complex]
    unbroken: bool

    def summary(self) -> str:
        values = ", ".join(
            f"{value.real:+.4f}{value.imag:+.4f}i" for value in self.eigenvalues
        )
        state = "unbroken" if self.unbroken else "broken"
        return f"gamma/g = {self.gamma_over_coupling:.2f}: [{values}] {state}"


# ============================================================
# The random ensemble
# ============================================================

def pt_random(
    dimension: int = DEFAULT_DIMENSION,
    antisymmetry: float = 0.2,
    seed: int = 0,
) -> np.ndarray:
    """``S + w A``: Gaussian symmetric plus ``w`` times Gaussian antisymmetric.

    The result is a real matrix, hence PT-symmetric with respect to complex conjugation,
    and non-Hermitian as soon as ``w != 0``. ``w = 0`` is a GOE matrix and is the
    control.
    """
    if dimension < 4:
        raise ValueError("need a dimension of at least four")
    if antisymmetry < 0.0:
        raise ValueError("the antisymmetry is a strength, so it is non-negative")
    rng = np.random.default_rng(seed)
    symmetric = rng.standard_normal((dimension, dimension))
    symmetric = (symmetric + symmetric.T) / 2.0
    skew = rng.standard_normal((dimension, dimension))
    skew = (skew - skew.T) / 2.0
    return symmetric + antisymmetry * skew


def is_hermitian(matrix: np.ndarray, tolerance: float = 1e-9) -> bool:
    matrix = np.asarray(matrix)
    return bool(np.abs(matrix - matrix.conj().T).max() <= tolerance)


def pairing_defect(eigenvalues) -> float:
    """How far the spectrum is from being closed under conjugation.

    Every eigenvalue of a real matrix has its conjugate in the spectrum. The defect is the
    largest distance between an eigenvalue's conjugate and its nearest partner, so it is a
    direct measurement of the anti-linear symmetry that survives when no linear involution
    exists.
    """
    values = np.asarray(eigenvalues, dtype=complex)
    if values.size == 0:
        return 0.0
    defect = 0.0
    for value in values:
        distances = np.abs(values - np.conj(value))
        defect = max(defect, float(np.min(distances)))
    return defect


def is_unbroken(eigenvalues, tolerance: float = REAL_TOLERANCE) -> bool:
    """True when every eigenvalue is real: the unbroken PT phase."""
    return bool(np.all(np.abs(np.asarray(eigenvalues).imag) <= tolerance))


def imaginary_over_spacing(eigenvalues) -> float:
    """Mean ``|Im E|`` divided by the mean spacing of the real parts.

    Zero in the unbroken phase, and a number that grows past one when the complex pairs
    are further apart than the level spacing: at that point the real parts carry almost no
    information about where the levels are.
    """
    values = np.asarray(eigenvalues, dtype=complex)
    if values.size < 2:
        return float("nan")
    spacings = np.diff(np.sort(values.real))
    spacings = spacings[spacings > 1e-12]
    scale = float(np.mean(spacings)) if spacings.size else 1.0
    return float(np.mean(np.abs(values.imag))) / scale


def real_part_ratio(eigenvalues) -> float:
    """The adjacent-gap ratio of the **real parts**, ignoring the imaginary parts.

    This is the number a user gets by pointing the existing machinery at a broken PT
    spectrum, and it is a measurement of the projection rather than of the spectrum. The
    report's point is the size of the difference, not that the number is undefined.
    """
    values = np.asarray(eigenvalues, dtype=complex)
    return mean_ratio(values.real)


@dataclass(frozen=True)
class PtEnsembleRow:
    """One antisymmetry strength, measured over a set of spectra."""

    antisymmetry: float
    unbroken_fraction: float
    real_part_mean_ratio: float
    imaginary_over_spacing: float
    pairing_defect: float
    seeds: int

    def summary(self) -> str:
        return (
            f"w = {self.antisymmetry:.2f}: unbroken {self.unbroken_fraction:.2f}, "
            f"real-part <r> = {self.real_part_mean_ratio:.4f}, "
            f"|Im|/spacing = {self.imaginary_over_spacing:.3f}, "
            f"pairing defect = {self.pairing_defect:.1e}"
        )


def ensemble_table(
    antisymmetries: tuple[float, ...] = DEFAULT_ANTISYMMETRIES,
    dimension: int = DEFAULT_DIMENSION,
    seeds: int = DEFAULT_SEEDS,
    seed: int = 0,
) -> list[PtEnsembleRow]:
    """Measure every point of the sweep on independent spectra."""
    if seeds < 4:
        raise ValueError("need at least four spectra per point")
    rows: list[PtEnsembleRow] = []
    for strength in antisymmetries:
        unbroken = 0
        ratios: list[float] = []
        imaginary: list[float] = []
        defects: list[float] = []
        for index in range(seeds):
            matrix = pt_random(dimension, strength, seed=seed + 10_000 * index)
            eigenvalues = np.linalg.eigvals(matrix)
            unbroken += is_unbroken(eigenvalues)
            ratios.append(real_part_ratio(eigenvalues))
            imaginary.append(imaginary_over_spacing(eigenvalues))
            defects.append(pairing_defect(eigenvalues))
        rows.append(
            PtEnsembleRow(
                antisymmetry=float(strength),
                unbroken_fraction=unbroken / seeds,
                real_part_mean_ratio=float(np.mean(ratios)),
                imaginary_over_spacing=float(np.mean(imaginary)),
                pairing_defect=float(np.max(defects)),
                seeds=seeds,
            )
        )
    return rows


#: The reference values the ratios are placed against.
REFERENCE = {
    "Poisson": POISSON_MEAN_RATIO,
    "GOE": GOE_MEAN_RATIO,
}
