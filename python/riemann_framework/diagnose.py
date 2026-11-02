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
"""One call for the whole diagnostic: verify, split, measure, and say what is concluded.

The pieces of this framework are separate functions: `sector_blocks` splits a matrix by a
list of involutions, `detect_hidden_symmetry` flags a contaminated spectrum,
`sector_count_posterior_higher_order` turns spacing ratios into a posterior over the number
of sectors, and the notes measure which statistic stops where. A user who wants one answer
writes the same six lines every time, and the order matters: a count computed on an
unsplit spectrum is the number this whole framework exists to warn about.

:func:`diagnose` is that one call. It takes either a matrix with its candidate involutions,
or a bare spectrum, and returns a :class:`Diagnosis`: every symmetry check with its
commutator, the sector statistics, the detector's verdict, the count posterior, and a list
of conclusions written from the measurements rather than from the hopes.

Two rules are built into the code, not the documentation:

* **an involution that does not commute is reported, not used.** A failed check appears in
  the report with its commutator and the split ignores that involution, because splitting
  by a non-symmetry mixes sectors and silently produces a meaningless sector statistic.
* **every conclusion is a measurement with its number.** "The full spectrum is
  contaminated" is never printed without the mean ratio, the sector means it is compared
  against, and the threshold. A result that cannot be stated as a number is not stated.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .desymmetrisation import (
    ContaminationWarning,
    SectorCountEstimate,
    detect_hidden_symmetry,
    sector_blocks,
    sector_count_posterior_higher_order,
    size_dependent_floor,
)
from .real_systems import (
    GOE_MEAN_RATIO,
    GUE_MEAN_RATIO,
    POISSON_MEAN_RATIO,
    mean_ratio,
)

#: Reference mean ratios, so the report can place a spectrum without a second import.
REFERENCE = {
    "Poisson": POISSON_MEAN_RATIO,
    "GOE": GOE_MEAN_RATIO,
    "GUE": GUE_MEAN_RATIO,
}

#: Smallest spectrum the report will look at.
MIN_LEVELS = 8


@dataclass(frozen=True)
class SymmetryCheck:
    """One candidate involution: does it commute, and with what residual?"""

    label: str
    commutator: float
    tolerance: float
    verified: bool

    def summary(self) -> str:
        state = "verified" if self.verified else "REJECTED"
        return (
            f"{self.label}: {state}, max |[H, P]| = {self.commutator:.2e} "
            f"(tolerance {self.tolerance:.0e})"
        )


@dataclass(frozen=True)
class Diagnosis:
    """Everything one call can honestly say about one spectrum."""

    title: str
    n_levels: int
    full_mean: float
    sector_means: tuple[float, ...]
    sector_sizes: tuple[int, ...]
    checks: tuple[SymmetryCheck, ...] = ()
    full_verdict: ContaminationWarning | None = None
    sector_verdicts: tuple[ContaminationWarning, ...] = ()
    count_estimate: SectorCountEstimate | None = None
    conclusions: tuple[str, ...] = ()

    @property
    def symmetries_verified(self) -> int:
        return sum(check.verified for check in self.checks)

    @property
    def full_below_every_sector(self) -> bool:
        return bool(self.sector_means) and all(
            self.full_mean < value for value in self.sector_means
        )

    def summary(self) -> str:
        lines = [
            f"{self.title} ({self.n_levels} levels)",
            f"  full spectrum: mean r = {self.full_mean:.4f} "
            f"(Poisson {POISSON_MEAN_RATIO:.3f}, GOE {GOE_MEAN_RATIO:.3f}, "
            f"GUE {GUE_MEAN_RATIO:.3f})",
        ]
        for check in self.checks:
            lines.append("  " + check.summary())
        for mean, size in zip(self.sector_means, self.sector_sizes):
            lines.append(f"  sector ({size} levels): mean r = {mean:.4f}")
        if self.full_verdict is not None:
            lines.append("  " + self.full_verdict.explanation)
        for verdict in self.sector_verdicts:
            if verdict.is_contaminated:
                lines.append(
                    f"  sector below its floor: {verdict.full_mean_r:.4f} "
                    f"(severity {verdict.severity})"
                )
        if self.count_estimate is not None:
            lines.append(f"  count posterior: {self.count_estimate.summary()}")
        for conclusion in self.conclusions:
            lines.append("  " + conclusion)
        return "\n".join(lines)


def _check_symmetry(
    matrix: np.ndarray, involution: np.ndarray, label: str, tolerance: float
) -> SymmetryCheck:
    commutator = float(np.abs(matrix @ involution - involution @ matrix).max())
    square = np.abs(involution @ involution - np.eye(involution.shape[0])).max()
    verified = bool(commutator <= tolerance and square <= tolerance)
    return SymmetryCheck(
        label=label, commutator=commutator, tolerance=tolerance, verified=verified
    )


def _conclusions(
    full_mean: float,
    sector_means: tuple[float, ...],
    verdict: ContaminationWarning | None,
    sector_verdicts: tuple[ContaminationWarning, ...],
    n_levels: int,
    n_verified: int,
) -> tuple[str, ...]:
    """The report's conclusions, each one carrying the number it rests on."""
    out: list[str] = []

    if sector_means:
        lowest = min(sector_means)
        if full_mean < lowest:
            out.append(
                f"the full spectrum ({full_mean:.3f}) is below every sector's "
                f"(lowest {lowest:.3f}): the unsplit statistic is a superposition and "
                "must not be quoted as a sector statistic"
            )
        else:
            out.append(
                f"the full spectrum ({full_mean:.3f}) is not below every sector's "
                f"(lowest {lowest:.3f}): the split does not change the statistic, so "
                "whatever is contaminating the spectrum is not these sectors"
            )
        flagged = [value for value in sector_verdicts if value.is_contaminated]
        if flagged:
            out.append(
                f"{len(flagged)} of {len(sector_verdicts)} sectors are below their own "
                "size-scaled floor, which on a real system is also what finite size and "
                "mixed dynamics produce: treat that as a prompt, not as a count"
            )
    elif n_verified == 0:
        out.append(
            "no involution was verified, so no sector statistic is available here: any "
            "flag is a prompt to look for the commuting symmetries, not a conclusion "
            "about them"
        )

    if verdict is not None:
        if verdict.is_contaminated:
            out.append(
                f"the detector flags the full spectrum ({verdict.severity}) at "
                f"n = {n_levels}"
            )
        else:
            out.append(
                f"the detector clears the full spectrum at n = {n_levels} "
                f"(mean r = {full_mean:.3f} >= floor {size_dependent_floor(n_levels):.3f})"
            )

    if full_mean < POISSON_MEAN_RATIO:
        out.append(
            f"the full mean is at or below the Poisson value ({POISSON_MEAN_RATIO:.3f}), "
            "which an integrable system also produces and which unresolved symmetry "
            "produces: no spacing statistic separates the two"
        )
    return tuple(out)


def diagnose_matrix(
    matrix: np.ndarray,
    involutions: list[np.ndarray],
    title: str = "Hamiltonian",
    tolerance: float = 1e-8,
    count_level: float = 0.9,
) -> Diagnosis:
    """Diagnose a Hamiltonian and its candidate involutions.

    The involutions are checked one by one. The verified ones are used for the split; a
    rejected one is reported with its commutator and left out, because splitting by an
    operator that does not commute mixes sectors.
    """
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("the Hamiltonian must be square")
    if matrix.shape[0] < MIN_LEVELS:
        raise ValueError(f"need at least {MIN_LEVELS} levels for a spacing statistic")
    if np.abs(matrix - matrix.T).max() > tolerance:
        raise ValueError("the Hamiltonian is not symmetric")

    checks = tuple(
        _check_symmetry(
            matrix, np.asarray(involution, dtype=float), f"P{index + 1}", tolerance
        )
        for index, involution in enumerate(involutions)
    )
    verified = [
        np.asarray(involution, dtype=complex)
        for check, involution in zip(checks, involutions)
        if check.verified
    ]

    levels = np.linalg.eigvalsh(matrix)
    sector_means: tuple[float, ...] = ()
    sector_sizes: tuple[int, ...] = ()
    sector_verdicts: tuple[ContaminationWarning, ...] = ()
    if verified:
        blocks = sector_blocks(matrix.astype(complex), verified)
        sectors = [np.linalg.eigvalsh(block.real) for _, block in sorted(blocks.items())]
        sector_means = tuple(mean_ratio(sector) for sector in sectors)
        sector_sizes = tuple(int(sector.size) for sector in sectors)
        sector_verdicts = tuple(detect_hidden_symmetry(sector) for sector in sectors)

    full_mean = mean_ratio(levels)
    verdict = detect_hidden_symmetry(levels)
    try:
        count: SectorCountEstimate | None = sector_count_posterior_higher_order(
            levels, level=count_level
        )
    except ValueError:
        count = None

    return Diagnosis(
        title=title,
        n_levels=int(levels.size),
        full_mean=full_mean,
        sector_means=sector_means,
        sector_sizes=sector_sizes,
        checks=checks,
        full_verdict=verdict,
        sector_verdicts=sector_verdicts,
        count_estimate=count,
        conclusions=_conclusions(
            full_mean,
            sector_means,
            verdict,
            sector_verdicts,
            int(levels.size),
            len(verified),
        ),
    )


def diagnose_spectrum(
    eigenvalues,
    title: str = "spectrum",
    count_level: float = 0.9,
) -> Diagnosis:
    """Diagnose a bare spectrum: no symmetry can be verified, and the report says so."""
    levels = np.sort(np.asarray(eigenvalues, dtype=float).ravel())
    if levels.size < MIN_LEVELS:
        raise ValueError(f"need at least {MIN_LEVELS} levels for a spacing statistic")
    if levels.size >= 3 and levels[-1] - levels[0] <= 0.0:
        raise ValueError("the spectrum is degenerate")

    full_mean = mean_ratio(levels)
    verdict = detect_hidden_symmetry(levels)
    try:
        count: SectorCountEstimate | None = sector_count_posterior_higher_order(
            levels, level=count_level
        )
    except ValueError:
        count = None

    return Diagnosis(
        title=title,
        n_levels=int(levels.size),
        full_mean=full_mean,
        sector_means=(),
        sector_sizes=(),
        checks=(),
        full_verdict=verdict,
        sector_verdicts=(),
        count_estimate=count,
        conclusions=_conclusions(
            full_mean, (), verdict, (), int(levels.size), 0
        ),
    )


def diagnose(
    eigenvalues=None,
    matrix: np.ndarray | None = None,
    involutions: list[np.ndarray] | None = None,
    title: str = "",
    count_level: float = 0.9,
) -> Diagnosis:
    """Diagnose either a matrix with candidate involutions, or a bare spectrum.

    Both arguments are accepted so a caller can pass whatever it has: the full matrix when
    it exists (the split is then available), the eigenvalues when it does not (only the
    detector and the count are). Passing both is a caller error rather than a
    precedence puzzle, and passing neither is too.
    """
    if matrix is not None and eigenvalues is not None:
        raise ValueError("give either a matrix or eigenvalues, not both")
    if matrix is not None:
        return diagnose_matrix(
            matrix,
            list(involutions or []),
            title=title or "Hamiltonian",
            count_level=count_level,
        )
    if eigenvalues is None:
        raise ValueError("give a matrix with its involutions, or a spectrum")
    return diagnose_spectrum(
        eigenvalues, title=title or "spectrum", count_level=count_level
    )
