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
"""Controlled symmetry breaking and the diagnostic's degradation curve.

The static diagnostic assumes that the sectors are exact: ``[H, sigma] = 0`` to
machine precision. A real device has manufacturing tolerances, stray fields and
finite measurement resolution, so the symmetry is only approximate. This module
adds the missing stress test,

    H(g) = H0 + g * Delta * V,

where ``H0`` is block diagonal in the sectors, ``V`` is a full random matrix of
the same symmetry class, ``Delta`` is the mean level spacing of ``H0`` and ``g``
is the **dimensionless** perturbation strength. Scaling by ``Delta`` is the
point: ``g`` is the ratio of the mixing matrix element to the level spacing,
and it is the quantity that governs the crossover. A raw ``epsilon`` is not
comparable across matrix sizes, because ``Delta`` shrinks with the dimension.

The module measures what happens to the diagnostic, not what a hand argument
says should happen:

* the mean adjacent-gap ratio moves from the two-sector value toward the GOE
  value as ``g`` grows;
* the contamination flag stops firing once the perturbation is strong enough
  to make the sectors genuinely mixed;
* the first-order Markov posterior loses accuracy and coverage, and
  :func:`critical_g` reports the first grid point at which it does.

The thresholds in :func:`critical_g` are stipulated (accuracy below ``0.5`` or
coverage below ``0.8``) and are arguments, not hidden constants.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .desymmetrisation import (
    SectorCountModel,
    default_sector_count_model,
    detect_hidden_symmetry,
    sector_count_posterior,
)
from .statistics import mean_r_ratio

#: Default dimensionless perturbation grid. ``g = 0`` is the exact symmetry;
#: ``g = 1`` means the mixing matrix element equals the mean level spacing.
DEFAULT_G_VALUES: tuple[float, ...] = (
    0.0,
    0.05,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.75,
    1.0,
    2.0,
    5.0,
    10.0,
)


def random_hermitian(
    dimension: int, matrix_class: str = "goe", rng: np.random.Generator | None = None
) -> np.ndarray:
    """A GOE (real symmetric) or GUE (complex Hermitian) random matrix."""
    generator = rng if rng is not None else np.random.default_rng()
    if matrix_class == "goe":
        matrix = generator.normal(size=(dimension, dimension))
        return (matrix + matrix.T) / 2.0
    if matrix_class == "gue":
        matrix = generator.normal(size=(dimension, dimension)) + 1j * generator.normal(
            size=(dimension, dimension)
        )
        return (matrix + matrix.conj().T) / 2.0
    raise ValueError("matrix_class must be 'goe' or 'gue'")


def block_hamiltonian(
    n_sectors: int,
    levels_per_sector: int,
    matrix_class: str = "goe",
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """A block-diagonal ``H0`` with ``n_sectors`` chaotic sectors of equal size."""
    if n_sectors < 1:
        raise ValueError("need at least one sector")
    if levels_per_sector < 2:
        raise ValueError("need at least two levels per sector")
    generator = rng if rng is not None else np.random.default_rng()
    dimension = n_sectors * levels_per_sector
    hamiltonian = np.zeros((dimension, dimension), dtype=complex)
    for sector in range(n_sectors):
        start = sector * levels_per_sector
        stop = start + levels_per_sector
        hamiltonian[start:stop, start:stop] = random_hermitian(
            levels_per_sector, matrix_class, generator
        )
    return hamiltonian


def sector_involution(n_sectors: int, levels_per_sector: int) -> np.ndarray:
    """The diagonal involution whose blocks are the sectors of ``H0``."""
    if n_sectors != 2:
        raise ValueError("the diagnostic is written for a Z2 involution, so use two sectors")
    signs = np.concatenate(
        [np.ones(levels_per_sector), -np.ones(levels_per_sector)]
    )
    return np.diag(signs).astype(complex)


def mean_level_spacing(levels: np.ndarray) -> float:
    """Mean spacing over the central 80 % of a spectrum, where the density is smooth."""
    ordered = np.sort(np.asarray(levels, dtype=float))
    if ordered.size < 3:
        raise ValueError("need at least three levels")
    low = int(0.1 * ordered.size)
    high = int(0.9 * ordered.size)
    window = ordered[low:high]
    return float(np.mean(np.diff(window)))


def perturbed_spectrum(
    hamiltonian: np.ndarray,
    perturbation: np.ndarray,
    g: float,
    spacing: float,
    circular: bool = False,
) -> np.ndarray:
    """Eigenvalues of ``H0 + g * spacing * V``."""
    if g < 0.0:
        raise ValueError("g must be non-negative")
    if hamiltonian.shape != perturbation.shape:
        raise ValueError("the perturbation must have the Hamiltonian's shape")
    eigenvalues = np.linalg.eigvalsh(hamiltonian + g * spacing * perturbation)
    return np.sort((eigenvalues + 2.0 * np.pi) % (2.0 * np.pi)) if circular else eigenvalues


@dataclass(frozen=True)
class BreakingRow:
    """One point of the degradation curve."""

    g: float
    mean_r: float
    flag_rate: float
    accuracy: float
    coverage: float
    draws: int

    def summary(self) -> str:
        return (
            f"g = {self.g:5.2f}: mean r {self.mean_r:.3f}, "
            f"flag {self.flag_rate:.2f}, MAP {self.accuracy:.2f}, "
            f"coverage {self.coverage:.2f}"
        )


@dataclass(frozen=True)
class DegradationCurve:
    """The measured curve and the first grid point that fails the threshold."""

    rows: tuple[BreakingRow, ...]
    true_count: int
    nominal_level: float
    critical_g: float | None
    accuracy_threshold: float
    coverage_threshold: float

    def summary(self) -> str:
        critical = (
            "not reached on the grid" if self.critical_g is None else f"{self.critical_g:g}"
        )
        return (
            f"{len(self.rows)} points, truth {self.true_count}, "
            f"critical g = {critical} "
            f"(accuracy < {self.accuracy_threshold} or coverage < {self.coverage_threshold})"
        )


def degradation_curve(
    g_values: tuple[float, ...] = DEFAULT_G_VALUES,
    n_sectors: int = 2,
    levels_per_sector: int = 120,
    matrix_class: str = "goe",
    draws: int = 40,
    seed: int = 0,
    model: SectorCountModel | None = None,
    level: float = 0.95,
    accuracy_threshold: float = 0.5,
    coverage_threshold: float = 0.8,
) -> DegradationCurve:
    """Measure the diagnostic along the symmetry-breaking crossover.

    Each draw uses one ``H0`` and one ``V``; every ``g`` is evaluated on that
    same pair, so the curve is paired in the perturbation. The posterior is the
    one fitted by :class:`SectorCountModel` on exact sectors; it is not retrained
    on broken spectra, which is the point of the stress test.
    """
    if n_sectors != 2:
        raise ValueError("this diagnostic uses a Z2 involution; use two sectors")
    if draws < 2:
        raise ValueError("need at least two draws for a rate")
    if any(g < 0.0 for g in g_values):
        raise ValueError("g values must be non-negative")
    total_levels = n_sectors * levels_per_sector
    active_model = model if model is not None else default_sector_count_model(total_levels)
    generator = np.random.default_rng(seed)

    records: dict[float, list[tuple[float, bool, bool, bool]]] = {
        g: [] for g in g_values
    }
    for _ in range(draws):
        hamiltonian = block_hamiltonian(
            n_sectors, levels_per_sector, matrix_class, generator
        )
        perturbation = random_hermitian(total_levels, matrix_class, generator)
        spacing = mean_level_spacing(np.linalg.eigvalsh(hamiltonian))
        for g in g_values:
            eigenvalues = perturbed_spectrum(hamiltonian, perturbation, g, spacing)
            ratio = float(mean_r_ratio(eigenvalues, unfold=False))
            flag = detect_hidden_symmetry(eigenvalues).is_contaminated
            estimate = sector_count_posterior(eigenvalues, model=active_model, level=level)
            accuracy = estimate.map_label == n_sectors
            low, high = estimate.credible_interval
            coverage = (low is None or low <= n_sectors) and (
                high is None or n_sectors <= high
            )
            records[g].append((ratio, flag, accuracy, coverage))

    rows: list[BreakingRow] = []
    for g in g_values:
        values = records[g]
        rows.append(
            BreakingRow(
                g=g,
                mean_r=float(np.mean([value[0] for value in values])),
                flag_rate=float(np.mean([value[1] for value in values])),
                accuracy=float(np.mean([value[2] for value in values])),
                coverage=float(np.mean([value[3] for value in values])),
                draws=len(values),
            )
        )

    critical = next(
        (
            row.g
            for row in rows
            if row.accuracy < accuracy_threshold or row.coverage < coverage_threshold
        ),
        None,
    )
    return DegradationCurve(
        rows=tuple(rows),
        true_count=n_sectors,
        nominal_level=level,
        critical_g=critical,
        accuracy_threshold=accuracy_threshold,
        coverage_threshold=coverage_threshold,
    )
