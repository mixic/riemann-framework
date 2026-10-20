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
"""Desymmetrise before testing the class: a splitting utility and a contamination warning.

The problem this module exists for is a silent bias. If a Hamiltonian commutes with an
involution `U` and the spectrum is measured on the **full** space, the levels seen are
the union of the levels of the sectors. A union of independent spectra has smaller
level repulsion than any of its parts, so the mean adjacent-gap ratio `⟨r⟩` falls --
all the way toward the Poisson value `0.386` as the number of unresolved sectors grows:

| unresolved independent sectors | GOE blocks | GUE blocks |
|:---|---:|---:|
| 1 | `0.52` | `0.59` |
| 2 | `0.43` | `0.42` |
| 3 or more | `0.38 … 0.40` | `0.38 … 0.40` |
| (Poisson) | `0.386` | `0.386` |

Three consequences, all measured and all in this module's tests:

1. **A low `⟨r⟩` flags an unresolved symmetry** -- a value near `0.43`, or lower, is
   *not* evidence of integrability before the symmetry is resolved.
2. **It detects, and it counts up to two.** `sector_count_posterior` fits the whole
   `r`-ratio sequence against simulated superpositions: one sector comes back as
   `p = 0.97` with interval `1..1`, two sectors as an interval `2..5` with the point
   estimate right 56% of the time, and three or more as `>=3` with 3 and 6
   indistinguishable. The earlier estimator (`estimate_sectors_from_mean`) inverts a
   single mean and is kept only to demonstrate that failure.
3. **At two sectors the class information is erased.** GOE and GUE both give `0.42`,
   so a class test run on the full spectrum is not merely noisy, it is uninformative.
   **The rule is: desymmetrise before testing the class.**

The honest boundary: a low `⟨r⟩` is consistent with an unresolved symmetry *and* with
a genuinely integrable system, and no spacing statistic can separate them. The warning
says so, and the fix it recommends -- find the involutions, verify they commute with
`H`, split, and test each sector -- is the only one that works.

Two entry points take only a spectrum, which is the screening case -- the operator is
known and its symmetries are not. `contamination_warning(H, U)` has a *candidate*
involution, so it verifies it and compares the full spectrum with the resolved sectors;
`sector_spectra(H, U)` is the same split with the reviewer's interface, refusing instead
of discarding the non-commuting mass. `detect_hidden_symmetry(eigenvalues)` has no
involution at all, so all it returns is a flag -- `none`, `mild` or `severe` -- with the
integrability caveat inside its own text. A `severe` flag means "do not call this
Poisson yet", never "this is a superposition": about `4` in `40` pure single-sector GOE
spectra also fall below the floor.

Nothing here concerns the Riemann hypothesis. In this repository the utility's
immediate application is that the `σ` sectors of the dimension-shift model are
`spec(A ± C)`, and testing the class on the full spectrum was exactly the mistake
that produced a "supported" verdict from a GOE model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from functools import lru_cache

import numpy as np

from .statistics import mean_r_ratio, r_ratio


#: Reference values, from `statistics.REFERENCE_R`.
R_POISSON = 0.386
R_GOE = 0.531
R_GUE = 0.600

#: A full-spectrum mean at or above this is consistent with a single sector.
SINGLE_SECTOR_FLOOR = 0.48

#: Below this, the spectrum is consistent with three or more unresolved sectors (or
#: with integrability -- the warning says so).
MULTI_SECTOR_CEILING = 0.40

#: The band a two-sector superposition lands in, for either matrix class. `0.424`
#: (GOE) and `0.425` (GUE) are inside it, which is why the class is unreadable there.
TWO_SECTOR_BAND = (0.40, 0.49)

#: A sector mean this far from the full-spectrum mean means the full-spectrum class
#: is not the sector's class.
CLASS_SHIFT_THRESHOLD = 0.05

#: The finite-size scatter of a single spectrum's mean `r` at the dimensions this
#: module calibrates on. It is comparable to the gap between successive sector
#: counts, which is why the absolute-band tests are flags rather than classifiers.
SINGLE_SPECTRUM_SCATTER = 0.035


# ============================================================
# Commutation and splitting
# ============================================================

def commutator_ratio(matrix: np.ndarray, involution: np.ndarray) -> float:
    """`||[M, U]||_F / ||M||_F`: zero when `U` is a symmetry of `M`."""
    matrix = np.asarray(matrix, dtype=complex)
    involution = np.asarray(involution, dtype=complex)
    if matrix.shape != involution.shape or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("matrix and involution must be square and the same shape")
    numerator = np.linalg.norm(matrix @ involution - involution @ matrix, "fro")
    denominator = np.linalg.norm(matrix, "fro")
    if denominator == 0.0:
        raise ValueError("matrix must be non-zero")
    return float(numerator / denominator)


def is_involution(matrix: np.ndarray, tolerance: float = 1e-10) -> bool:
    """`U^2 = I` and `U` Hermitian, i.e. a `Z_2` symmetry with real eigenvalues."""
    matrix = np.asarray(matrix, dtype=complex)
    if matrix.shape[0] != matrix.shape[1]:
        return False
    return bool(
        np.abs(matrix @ matrix - np.eye(matrix.shape[0])).max() < tolerance
        and np.abs(matrix - matrix.conj().T).max() < tolerance
    )


def _involution_signs(count: int) -> list[tuple[int, ...]]:
    """All `+-1` sign vectors of length `count`, `(+, ..., +)` first."""
    signs: list[tuple[int, ...]] = [()]
    for _ in range(count):
        signs = [sign + (value,) for sign in signs for value in (1, -1)]
    return signs


def sector_blocks(
    matrix: np.ndarray,
    involutions: list[np.ndarray],
    tolerance: float = 1e-8,
) -> dict[tuple[int, ...], np.ndarray]:
    """Split `H` into the joint eigenspaces of a set of **commuting** involutions.

    Returns a mapping from the sign tuple (one `+-1` per involution) to the block of
    `H` restricted to that sector, in an orthonormal basis. Raises rather than
    returning a meaningless split when the inputs are not what they claim:

    * every object must be an involution (`U^2 = I`, Hermitian);
    * every involution must commute with `H`;
    * the involutions must commute with each other, or they have no joint eigenspaces;
    * the blocks must be Hermitian, and the split must be exact to `tolerance`.

    A block whose sector is absent (dimension zero) is omitted, so a `Z_2` on a
    space where one sign never occurs returns one block rather than a `0 x 0` array.
    """
    matrix = np.asarray(matrix, dtype=complex)
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("matrix must be square")
    if not involutions:
        raise ValueError("at least one involution is required")
    dimension = matrix.shape[0]

    for index, involution in enumerate(involutions):
        involution = np.asarray(involution, dtype=complex)
        if involution.shape != matrix.shape:
            raise ValueError(f"involution {index} has the wrong shape")
        if not is_involution(involution, tolerance=max(tolerance, 1e-10)):
            raise ValueError(f"object {index} is not an involution (U^2 = I, Hermitian)")
        if commutator_ratio(matrix, involution) > tolerance:
            raise ValueError(
                f"involution {index} does not commute with the matrix: "
                f"||[H,U]||/||H|| = {commutator_ratio(matrix, involution):.3e}"
            )
    for first in range(len(involutions)):
        for second in range(first + 1, len(involutions)):
            if commutator_ratio(
                np.asarray(involutions[first], dtype=complex),
                np.asarray(involutions[second], dtype=complex),
            ) > tolerance:
                raise ValueError(
                    f"involutions {first} and {second} do not commute, so they have "
                    "no joint eigenspaces"
                )

    identity = np.eye(dimension, dtype=complex)
    blocks: dict[tuple[int, ...], np.ndarray] = {}
    consumed = 0
    for signs in _involution_signs(len(involutions)):
        projector = identity.copy()
        for sign, involution in zip(signs, involutions):
            projector = projector @ (identity + sign * np.asarray(involution, dtype=complex)) / 2.0
        # Orthonormal basis of the projector's range, by SVD.
        left, singular, _ = np.linalg.svd(projector)
        rank = int(np.sum(singular > 1e-8))
        if rank == 0:
            continue
        basis = left[:, :rank]
        block = basis.conj().T @ matrix @ basis
        if np.abs(block - block.conj().T).max() > 1e-8:
            raise ValueError(f"sector {signs} is not Hermitian; the split is invalid")
        blocks[signs] = block
        consumed += rank

    if consumed != dimension:
        raise ValueError(
            f"sectors span {consumed} of {dimension} dimensions; the involutions do "
            "not determine a complete decomposition"
        )
    return blocks


# ============================================================
# Statistics
# ============================================================

@dataclass(frozen=True)
class SpectrumStatistics:
    """Mean adjacent-gap ratio of one spectrum."""

    label: str
    mean_r: float
    dimension: int

    def summary(self) -> str:
        return f"{self.label:>16}: mean r = {self.mean_r:.4f} ({self.dimension} levels)"


@dataclass(frozen=True)
class DesymmetrisedReport:
    """The full spectrum, its sectors, and whatever the comparison flags."""

    full: SpectrumStatistics
    sectors: list[SpectrumStatistics]
    warnings: list[str] = field(default_factory=list)
    n_involutions: int = 0

    @property
    def sector_count(self) -> int:
        return len(self.sectors)

    @property
    def full_spectrum_contaminated(self) -> bool:
        """Is the full-spectrum statistic below what a single sector would give?"""
        if not self.sectors:
            return False
        return self.full.mean_r < min(sector.mean_r for sector in self.sectors) - CLASS_SHIFT_THRESHOLD

    @property
    def spread(self) -> float:
        """Difference between the largest and smallest sector mean."""
        if not self.sectors:
            return 0.0
        means = [sector.mean_r for sector in self.sectors]
        return max(means) - min(means)

    def summary(self) -> str:
        lines = [self.full.summary()]
        for sector in self.sectors:
            lines.append("  " + sector.summary())
        for warning in self.warnings:
            lines.append("  WARNING: " + warning)
        return "\n".join(lines)


def desymmetrise(
    matrix: np.ndarray,
    involutions: list[np.ndarray],
    unfold: bool = False,
) -> DesymmetrisedReport:
    """Statistics of the full spectrum next to the statistics of each sector.

    This is the utility: it verifies the symmetries, splits, and reports both views so
    the contaminated one cannot be quoted by accident. `unfold=False` by default, as
    in `m5_analysis.py`: polynomial unfolding of a small spectrum adds variance
    without removing structure.
    """
    matrix = np.asarray(matrix, dtype=complex)
    blocks = sector_blocks(matrix, involutions)
    full = SpectrumStatistics(
        label="full spectrum",
        mean_r=float(mean_r_ratio(np.linalg.eigvalsh(matrix), unfold=unfold)),
        dimension=int(matrix.shape[0]),
    )
    sectors = [
        SpectrumStatistics(
            label="sector " + "".join("+" if sign > 0 else "-" for sign in signs),
            mean_r=float(mean_r_ratio(np.linalg.eigvalsh(block), unfold=unfold)),
            dimension=int(block.shape[0]),
        )
        for signs, block in sorted(blocks.items())
    ]
    report = DesymmetrisedReport(
        full=full, sectors=sectors, n_involutions=len(involutions)
    )
    return DesymmetrisedReport(
        full=full,
        sectors=sectors,
        n_involutions=len(involutions),
        warnings=contamination_warnings(report),
    )


def contamination_warnings(report: DesymmetrisedReport) -> list[str]:
    """The warning text for a report: what the full-spectrum statistic cannot say.

    Three flags, in decreasing order of reliability:

    1. **The reliable one.** The full-spectrum mean is below every *resolved* sector's
       mean by more than `CLASS_SHIFT_THRESHOLD`. This is a comparison within one
       Hamiltonian, not an absolute band, so it does not depend on the finite-size
       calibration.
    2. **The band flags.** An absolute value in the two-sector band, or at or below the
       three-sector ceiling. Both are only flags: a single spectrum's scatter is about
       `SINGLE_SPECTRUM_SCATTER`, comparable to the gaps between successive sector
       counts, so a single draw cannot be classified -- it can only be queried.
    3. **The honest limit.** A value at the Poisson level is produced by an unresolved
       symmetry *and* by an integrable system, and no spacing statistic separates them.
    """
    warnings: list[str] = []
    sector_minimum = min((s.mean_r for s in report.sectors), default=float("nan"))

    if report.full_spectrum_contaminated:
        warnings.append(
            f"the full-spectrum mean r = {report.full.mean_r:.3f} is below every "
            f"sector's (minimum {sector_minimum:.3f}) by more than "
            f"{CLASS_SHIFT_THRESHOLD}: the full spectrum is a superposition of "
            f"{report.sector_count} unresolved sectors, and any class test on it is "
            "measuring the superposition, not the sectors"
        )
    # The two flags below are independent statements about different things -- the
    # full-vs-sector comparison, and the absolute band -- so both may hold, and both
    # are reported when they do.
    if TWO_SECTOR_BAND[0] <= report.full.mean_r <= TWO_SECTOR_BAND[1]:
        warnings.append(
            f"the full-spectrum mean r = {report.full.mean_r:.3f} is in the two-sector "
            f"band {TWO_SECTOR_BAND}, where GOE (0.424) and GUE (0.425) coincide: the "
            "matrix class cannot be read from it. A single spectrum scatters by about "
            f"{SINGLE_SPECTRUM_SCATTER}, so treat this as a flag to resolve the "
            "symmetries, not as a count"
        )
    if report.full.mean_r < MULTI_SECTOR_CEILING:
        warnings.append(
            f"the full-spectrum mean r = {report.full.mean_r:.3f} is at or below "
            f"{MULTI_SECTOR_CEILING}, which is what three or more unresolved sectors "
            "*and* an integrable system both produce; spacing statistics cannot tell "
            "these apart, so an integrability claim needs a separate argument"
        )
    return warnings


# ============================================================
# Calibration: the table, reproduced
# ============================================================

@dataclass(frozen=True)
class CalibrationRow:
    """`⟨r⟩` for a union of `n_sectors` independent blocks of one class."""

    n_sectors: int
    matrix_class: str
    mean_r: float
    std_r: float

    def summary(self) -> str:
        return (
            f"{self.n_sectors:2d} sector(s), {self.matrix_class}: "
            f"mean r {self.mean_r:.4f} +- {self.std_r:.4f}"
        )


def _random_block(dimension: int, matrix_class: str, rng: np.random.Generator) -> np.ndarray:
    if matrix_class == "gue":
        raw = (rng.standard_normal((dimension, dimension))
               + 1j * rng.standard_normal((dimension, dimension))) / np.sqrt(2.0)
        return (raw + raw.conj().T) / 2.0
    raw = rng.standard_normal((dimension, dimension))
    return (raw + raw.T) / 2.0


def superposition_spectrum(
    n_sectors: int,
    dimension: int = 60,
    matrix_class: str = "gue",
    seed: int = 0,
) -> np.ndarray:
    """The spectrum as it looks *before* the symmetry is resolved: a union of sectors.

    This is the contamination model. When `H` commutes with `U`, its eigenvalues are
    the union of the sector eigenvalues, so a measurement on the full space sees the
    concatenation -- which is what the table is made of.
    """
    if n_sectors < 1:
        raise ValueError("n_sectors must be at least 1")
    if matrix_class not in ("goe", "gue"):
        raise ValueError("matrix_class must be 'goe' or 'gue'")
    rng = np.random.default_rng(seed)
    return np.concatenate(
        [np.linalg.eigvalsh(_random_block(dimension, matrix_class, rng))
         for _ in range(n_sectors)]
    )


def calibration_table(
    sector_counts: tuple[int, ...] = (1, 2, 3, 4),
    dimension: int = 60,
    seeds: int = 300,
    matrix_classes: tuple[str, ...] = ("goe", "gue"),
) -> list[CalibrationRow]:
    """Reproduce the sector-count table at `seeds` seeds per row.

    The numbers this returns are the evidence for the warning's thresholds: `0.52` /
    `0.59` at one sector, `0.43` / `0.42` at two, and `0.38 … 0.40` from three up.
    """
    if seeds < 2:
        raise ValueError("need at least two seeds")
    rows: list[CalibrationRow] = []
    for matrix_class in matrix_classes:
        for n_sectors in sector_counts:
            values = [
                float(mean_r_ratio(
                    superposition_spectrum(n_sectors, dimension, matrix_class, seed),
                    unfold=False,
                ))
                for seed in range(seeds)
            ]
            rows.append(
                CalibrationRow(
                    n_sectors=n_sectors,
                    matrix_class=matrix_class,
                    mean_r=float(np.mean(values)),
                    std_r=float(np.std(values, ddof=1)),
                )
            )
    return rows


# ============================================================
# The two limits: counting fails, and two sectors erase the class
# ============================================================

def estimate_sector_count(mean_r: float, table: list[CalibrationRow], matrix_class: str = "gue") -> float:
    """Invert the calibration table: how many sectors does this `⟨r⟩` imply?

    **Included to demonstrate a failure, not to be used.** The map is many-to-one --
    three, four and six sectors all land between `0.386` and `0.404` with a sample
    scatter comparable to the gaps between them -- so the inversion is unstable. The
    returned value is linearly interpolated between the nearest tabulated rows and
    clamped to `[1, max n]`; on single spectra it scatters by several sectors, and it
    saturates at the largest tabulated count instead of reporting "cannot tell".

    The reviewer's attempt at this returned `12` for a true `4`. The failure this
    function reproduces is the *spread* and the collapse above three sectors; the
    specific number is a property of the particular estimator, not of the data.
    """
    rows = sorted(
        (row for row in table if row.matrix_class == matrix_class),
        key=lambda row: row.n_sectors,
    )
    if not rows:
        raise ValueError(f"no calibration rows for class {matrix_class!r}")
    counts = [row.n_sectors for row in rows]
    means = [row.mean_r for row in rows]
    # Descending mean as n grows, so interpolate on (mean -> n).
    for left, right in zip(range(len(rows) - 1), range(1, len(rows))):
        high, low = means[left], means[right]
        if high >= mean_r >= low and high > low:
            fraction = (high - mean_r) / (high - low)
            return float(counts[left] + fraction * (counts[right] - counts[left]))
    if mean_r > means[0]:
        return float(counts[0])
    return float(counts[-1])


def class_information_at_two_sectors(report: DesymmetrisedReport) -> bool:
    """Is the full-spectrum class information erased?

    True when there are two sectors and the full-spectrum mean sits in the band where
    both classes land. The measured fact this encodes: at two sectors GOE gives
    `0.424` and GUE `0.425`, a difference far below the single-spectrum scatter.
    """
    if report.sector_count != 2:
        return False
    return TWO_SECTOR_BAND[0] <= report.full.mean_r <= TWO_SECTOR_BAND[1]


# ============================================================
# Spectrum-only detection, and the class vocabulary
# ============================================================

#: The window a class test is compared against, per `m5_analysis.py`.
CLASS_WINDOWS = {
    "goe": (0.51, 0.55),
    "gue": (0.58, 0.62),
    "poisson": (0.36, 0.41),
}

#: The severity boundary suggested by the reviewer: below this the flag is `severe`
#: rather than `mild`. It is *not* a boundary between "symmetry" and "integrability",
#: because no spacing statistic has one -- see `detect_hidden_symmetry`.
SEVERE_THRESHOLD = 0.46


def classify_mean(mean_r: float) -> str:
    """The universality class a mean `r`-ratio falls into, or `"intermediate"`."""
    for name, (low, high) in CLASS_WINDOWS.items():
        if low <= mean_r <= high:
            return name
    return "intermediate"


def sector_spectra(hamiltonian: np.ndarray, involution: np.ndarray) -> list[np.ndarray]:
    """Eigenvalues of each `sigma`-sector, verifying the precondition first.

    Same name and return shape as the reviewer's utility, but it **refuses** to split
    a matrix that does not commute with the involution. The reviewer's version
    diagonalises the involution, projects `H` into that basis and keeps the diagonal
    blocks; when `[H, U] != 0` the discarded off-diagonal mass is the sectors, and the
    returned arrays are not sector spectra at all. Measured on the reviewer's own
    fixture (`d = 20, 100`; both classes):
    `||[H, U]|| / ||H|| = 1.14 … 1.18`, so the precondition it skips is the one its
    example fails.
    """
    blocks = sector_blocks(hamiltonian, [involution])
    return [np.linalg.eigvalsh(block) for _, block in sorted(blocks.items())]


@dataclass(frozen=True)
class ContaminationWarning:
    """A flag about a spectrum, with its severity and its stated limit."""

    is_contaminated: bool
    full_mean_r: float
    estimated_sectors: int | None
    severity: str
    explanation: str

    def summary(self) -> str:
        return f"[{self.severity}] {self.explanation}"


def estimate_sectors_from_mean(full_mean_r: float) -> int | None:
    """A **rough** count from the calibration table, or `None` when it is unrecoverable.

    Deliberately refuses above two sectors. The table is `0.531`/`0.600` at one,
    `0.426`/`0.421` at two, and `0.404`, `0.396`, `0.391` from three to six -- with a
    single-spectrum scatter of about `0.03` these are not separable, so anything at or
    below `0.41` returns `None` rather than a number. The reviewer's attempt at a
    count returned `12` for a true `4`; `estimate_sector_count` shows the same
    instability in the opposite direction.
    """
    if full_mean_r >= 0.50:
        return 1
    if full_mean_r >= 0.41:
        return 2
    return None


def detect_hidden_symmetry(eigenvalues: np.ndarray) -> ContaminationWarning:
    """Flag a possible unresolved symmetry from a spectrum alone.

    This is the entry point for a screening test that has only eigenvalues -- the
    operator-candidate screen, for instance. It cannot verify commutation, because it
    does not know the symmetries, so the flag is a prompt to look for them.

    The honest limit is in the text it returns: a low `mean r` is produced by an
    unresolved symmetry **and** by a genuinely integrable system, and no spacing
    statistic separates the two. A `severe` flag therefore means "do not call this
    Poisson yet", not "this is a superposition".
    """
    values = np.asarray(eigenvalues, dtype=float).ravel()
    if values.size < 8:
        raise ValueError("need at least 8 levels to compute a gap ratio")
    mean_r = float(mean_r_ratio(values, unfold=False))

    if mean_r >= SINGLE_SECTOR_FLOOR:
        return ContaminationWarning(
            is_contaminated=False,
            full_mean_r=mean_r,
            estimated_sectors=1,
            severity="none",
            explanation=(
                f"mean r = {mean_r:.4f} is in the single-sector range "
                f"(>= {SINGLE_SECTOR_FLOOR}); no unresolved symmetry is indicated"
            ),
        )

    estimated = estimate_sectors_from_mean(mean_r)
    severity = "mild" if mean_r >= SEVERE_THRESHOLD else "severe"
    if estimated is None:
        limit = (
            "at or below the three-sector level, so the number of sectors is not "
            "recoverable; this is also what an integrable system produces"
        )
    else:
        limit = (
            "consistent with two unresolved sectors; the matrix class is erased at "
            "two, so do not read a class from this spectrum"
        )
    return ContaminationWarning(
        is_contaminated=True,
        full_mean_r=mean_r,
        estimated_sectors=estimated,
        severity=severity,
        explanation=(
            f"mean r = {mean_r:.4f} is below the single-sector floor "
            f"{SINGLE_SECTOR_FLOOR}: {limit}. Find the commuting involutions, verify "
            "them, split, and test each sector"
        ),
    )


def contamination_warning(
    hamiltonian: np.ndarray,
    involution: np.ndarray,
) -> ContaminationWarning:
    """Flag a Hamiltonian whose *known* involution leaves a contaminated spectrum.

    Unlike `detect_hidden_symmetry`, this has the involution, so it verifies it and
    compares the full spectrum with the resolved sectors -- the reliable comparison.
    The involution is used; a parameter that is accepted and ignored would be worse
    than no parameter.
    """
    report = desymmetrise(hamiltonian, [involution])
    sector_minimum = min(sector.mean_r for sector in report.sectors)
    severity = (
        "none"
        if not report.full_spectrum_contaminated
        else ("severe" if report.full.mean_r < SEVERE_THRESHOLD else "mild")
    )
    explanation = (
        f"full spectrum mean r = {report.full.mean_r:.4f}, sectors "
        + ", ".join(f"{sector.mean_r:.4f}" for sector in report.sectors)
        + f"; {len(report.warnings)} warning(s) from the split"
    )
    return ContaminationWarning(
        is_contaminated=report.full_spectrum_contaminated,
        full_mean_r=report.full.mean_r,
        estimated_sectors=estimate_sectors_from_mean(report.full.mean_r),
        severity=severity,
        explanation=explanation + (
            f" (minimum sector mean {sector_minimum:.4f})"
        ),
    )


# ============================================================
# The count, with an error bar
# ============================================================
#
# `estimate_sectors_from_mean` inverts one scalar and fails, which is why the
# documentation said "detects but does not count". A posterior does better, and does
# honest better: the datum is the whole gap-ratio *sequence*, not its mean, and the
# answer is a distribution over counts with a calibrated interval. What it recovers
# is measured, not assumed (240 levels, 200 training spectra per hypothesis, nominal
# 95% interval, 60 simulated spectra per row):
#
# | truth | P(true) | interval covers | interval is a point |
# |:---|---:|---:|---:|
# | 1 sector | `0.98` | `1.00` | `0.95` |
# | 2 sectors | `0.65` | `0.93` | `0.28` |
# | 3 sectors | `0.24` | `0.87` | `0.00` |
# | 4 sectors | `0.17` | `0.98` | `0.00` |
# | 6 sectors | `0.20` | `0.97` | `0.00` |
# | Poisson | `0.20` | `0.78` | `0.00` |
#
# So the count is a measurement at one and at two, and at three or more the posterior
# refuses to separate 3 from 6 -- the original negative result, now with an interval
# instead of a shrug. The Poisson row is the weakest: an integrable spectrum is easily
# read as a five-sector superposition, because that is what it looks like.

COUNT_LABELS: tuple[int | None, ...] = (1, 2, 3, 4, 5, 6, None)

#: Nominal mass of the credible interval. Measured coverage is reported by
#: `SectorCountModel.coverage`, because a nominal level that is never checked is a
#: claim rather than a measurement.
COUNT_DEFAULT_LEVEL = 0.95

#: Number of `r` bins for the transition model. Sixteen is coarse enough for the
#: transition counts to be dense at 200 training spectra per hypothesis.
COUNT_DEFAULT_BINS = 16

#: Training spectra per hypothesis. The model is a plug-in estimate; its own
#: uncertainty is not integrated out, which is one reason the interval is calibrated
#: empirically (and slightly under-covers at two sectors).
COUNT_DEFAULT_SEEDS = 200

#: Levels of the spectra the model is calibrated on. A model is tied to the size of
#: the spectrum it will be asked about; `SectorCountModel.fit` uses this to pick the
#: per-sector dimension for each hypothesis.
COUNT_DEFAULT_LEVELS = 240


def _gap_ratio_sequence(eigenvalues) -> np.ndarray:
    """The `r`-ratios of a spectrum, with the degenerate and out-of-range ones dropped."""
    values = np.sort(np.asarray(eigenvalues, dtype=float))
    ratios = r_ratio(values, unfold=False)
    ratios = np.asarray(ratios, dtype=float)
    return ratios[(ratios > 0.0) & (ratios <= 1.0)]


@dataclass(frozen=True)
class SectorCountEstimate:
    """A posterior over the number of unresolved sectors, and its credible interval.

    `posterior` maps a label to a probability; `None` is the open-ended label: "at
    least six, or not a superposition of chaotic sectors at all" -- the estimator
    cannot separate seven unresolved sectors from a Poisson spectrum, so it does not
    pretend to.
    """

    posterior: dict[int | None, float]
    credible_interval: tuple[int | None, int | None]
    level: float

    @property
    def map_label(self) -> int | None:
        """The most probable label, ties broken towards the smaller count."""
        return max(
            COUNT_LABELS,
            key=lambda label: (self.posterior[label], -_count_index(label)),
        )

    @property
    def probability(self) -> float:
        """The posterior mass on `map_label`."""
        return self.posterior[self.map_label]

    def summary(self) -> str:
        low, high = self.credible_interval
        return (
            f"{_label_name(self.map_label)} (p = {self.probability:.2f}, "
            f"{int(self.level * 100)}% CI {_label_name(low)}..{_label_name(high)})"
        )


@dataclass(frozen=True)
class CoverageRow:
    """Measured behaviour of the estimator for one true sector count."""

    truth: int | None
    posterior_probability: float
    coverage: float
    exact: float
    draws: int

    def summary(self) -> str:
        return (
            f"{_label_name(self.truth):>9}: P(true) = {self.posterior_probability:.2f}, "
            f"coverage = {self.coverage:.2f}, point estimate = {self.exact:.2f}"
        )


def _count_index(label: int | None) -> int:
    return len(COUNT_LABELS) - 1 if label is None else COUNT_LABELS.index(label)


def _label_name(label: int | None) -> str:
    return ">=6/poisson" if label is None else f"{label}"


def _contiguous_interval(
    posterior: dict[int | None, float], level: float
) -> tuple[int | None, int | None]:
    """The shortest contiguous interval of labels carrying at least `level` mass.

    Contiguous because the labels are ordered; shortest because a wider interval than
    necessary is a weaker measurement.
    """
    if not 0.0 < level <= 1.0:
        raise ValueError("level must lie in (0, 1]")
    weights = [posterior[label] for label in COUNT_LABELS]
    best: tuple[int, int] | None = None
    for start in range(len(COUNT_LABELS)):
        total = 0.0
        for stop in range(start, len(COUNT_LABELS)):
            total += weights[stop]
            if total >= level:
                if best is None or (stop - start) < (best[1] - best[0]):
                    best = (start, stop)
                break
    if best is None:  # pragma: no cover - the posterior sums to 1
        return COUNT_LABELS[0], COUNT_LABELS[-1]
    return COUNT_LABELS[best[0]], COUNT_LABELS[best[1]]


@dataclass(frozen=True)
class SectorCountModel:
    """A first-order Markov model of the `r`-ratio sequence, one per hypothesis.

    The sequence is the data, not the mean: consecutive `r`-ratios share a spacing, so
    a model that treated them as independent counted the same information twice and was
    measurably overconfident -- at `d = 60` independent-product posteriors covered only
    `0.70` at a nominal `0.90`. A first-order chain over binned ratios keeps the
    dependence that matters, and the coverage of the resulting interval is measured by
    `coverage()` rather than assumed.

    The hypotheses are `1..max_sectors` unresolved chaotic sectors (class marginalised
    with equal weight) and one Poisson model standing for "integrable, or so many
    sectors that they are indistinguishable from it".
    """

    edges: np.ndarray
    total_levels: int
    log_initial: dict[int | None, np.ndarray]
    log_transition: dict[int | None, np.ndarray]

    @classmethod
    def fit(
        cls,
        total_levels: int = COUNT_DEFAULT_LEVELS,
        seeds: int = COUNT_DEFAULT_SEEDS,
        bins: int = COUNT_DEFAULT_BINS,
        max_sectors: int = 6,
    ) -> "SectorCountModel":
        """Simulate the hypotheses and fit the transition model.

        `total_levels` fixes the per-sector dimension of each hypothesis as
        `total_levels // n`, so a model fitted here is meant for a spectrum of about
        that many levels. `seeds` spectra are simulated per hypothesis, alternating
        GOE and GUE so the two classes enter with equal weight.
        """
        if total_levels < 24:
            raise ValueError("need at least 24 levels to fit a sector-count model")
        if bins < 4:
            raise ValueError("need at least 4 bins")
        if seeds < 8:
            raise ValueError("need at least 8 training spectra per hypothesis")
        if max_sectors < 2:
            raise ValueError("need at least two sector hypotheses")

        sequences: dict[int | None, list[np.ndarray]] = {}
        for n_sectors in range(1, max_sectors + 1):
            dimension = max(4, total_levels // n_sectors)
            sequences[n_sectors] = [
                _gap_ratio_sequence(
                    superposition_spectrum(
                        n_sectors,
                        dimension,
                        "gue" if index % 2 else "goe",
                        index,
                    )
                )
                for index in range(seeds)
            ]
        sequences[None] = [
            _gap_ratio_sequence(
                np.cumsum(np.random.default_rng(10_000 + index).exponential(1.0, total_levels))
            )
            for index in range(seeds)
        ]

        pooled = np.concatenate(
            [np.concatenate(sequence) for sequence in sequences.values()]
            if sequences
            else [np.ones(1)]
        )
        if pooled.size < bins + 1:
            raise ValueError("not enough simulated ratios to place the bins")
        quantiles = np.linspace(0.0, 1.0, bins + 1)
        edges = np.asarray(np.quantile(pooled, quantiles), dtype=float)
        edges[0] = 0.0
        edges[-1] = 1.0 + 1e-9

        log_initial: dict[int | None, np.ndarray] = {}
        log_transition: dict[int | None, np.ndarray] = {}
        for label, group in sequences.items():
            initial = np.full(bins, 0.5)
            transition = np.full((bins, bins), 0.5)
            for sequence in group:
                binned = np.clip(np.digitize(sequence, edges[1:-1]), 0, bins - 1)
                if binned.size < 2:
                    continue
                initial[binned[0]] += 1.0
                np.add.at(transition, (binned[:-1], binned[1:]), 1.0)
            log_initial[label] = np.log(initial / initial.sum())
            log_transition[label] = np.log(
                transition / transition.sum(axis=1, keepdims=True)
            )

        return cls(
            edges=edges,
            total_levels=total_levels,
            log_initial=log_initial,
            log_transition=log_transition,
        )

    def log_likelihood(self, gap_ratios) -> dict[int | None, float]:
        """Log likelihood of an `r`-ratio sequence under each hypothesis."""
        ratios = np.asarray(gap_ratios, dtype=float)
        ratios = ratios[(ratios > 0.0) & (ratios <= 1.0)]
        if ratios.size < 2:
            raise ValueError("need at least two distinct gap ratios")
        binned = np.clip(
            np.digitize(ratios, self.edges[1:-1]), 0, len(self.edges) - 2
        )
        out: dict[int | None, float] = {}
        for label in self.log_initial:
            out[label] = float(
                self.log_initial[label][binned[0]]
                + self.log_transition[label][binned[:-1], binned[1:]].sum()
            )
        return out

    def posterior(
        self, gap_ratios, level: float = COUNT_DEFAULT_LEVEL
    ) -> SectorCountEstimate:
        """Posterior over the labels, with a uniform prior over the hypotheses."""
        log_likelihood = self.log_likelihood(gap_ratios)
        largest = max(log_likelihood.values())
        weights = {
            label: float(np.exp(value - largest))
            for label, value in log_likelihood.items()
        }
        total = sum(weights.values())
        posterior = {label: weight / total for label, weight in weights.items()}
        return SectorCountEstimate(
            posterior=posterior,
            credible_interval=_contiguous_interval(posterior, level),
            level=level,
        )

    def estimate(
        self, eigenvalues, level: float = COUNT_DEFAULT_LEVEL
    ) -> SectorCountEstimate:
        """Posterior for a spectrum, from its eigenvalues alone."""
        return self.posterior(_gap_ratio_sequence(eigenvalues), level=level)

    def coverage(
        self,
        truths: tuple[int | None, ...] = COUNT_LABELS,
        draws: int = 40,
        level: float = COUNT_DEFAULT_LEVEL,
        seed: int = 50_000,
    ) -> list[CoverageRow]:
        """Measure the interval, rather than asserting it.

        For each true count, `draws` fresh spectra are generated, the interval is
        computed, and the fraction containing the truth is recorded. This is the
        number that makes the interval a measurement: a nominal `level` that is never
        checked is a claim.
        """
        if draws < 1:
            raise ValueError("need at least one draw")
        rows: list[CoverageRow] = []
        for truth in truths:
            covered = 0
            exact = 0
            probability = 0.0
            for index in range(draws):
                estimate = self.estimate(
                    _synthetic_spectrum(truth, index, seed, self.total_levels), level
                )
                low, high = estimate.credible_interval
                covered += _count_index(low) <= _count_index(truth) <= _count_index(high)
                exact += low == high
                probability += estimate.posterior.get(truth, 0.0)
            rows.append(
                CoverageRow(
                    truth=truth,
                    posterior_probability=probability / draws,
                    coverage=covered / draws,
                    exact=exact / draws,
                    draws=draws,
                )
            )
        return rows


def _synthetic_spectrum(
    truth: int | None, index: int, seed: int, total_levels: int
) -> np.ndarray:
    """One test spectrum: `truth` unresolved sectors, or a Poisson spectrum."""
    if truth is None:
        rng = np.random.default_rng(seed + index)
        return np.cumsum(rng.exponential(1.0, total_levels))
    dimension = max(4, total_levels // truth)
    return superposition_spectrum(
        truth, dimension, "gue" if index % 2 else "goe", seed + index
    )


@lru_cache(maxsize=4)
def default_sector_count_model(
    total_levels: int = COUNT_DEFAULT_LEVELS,
) -> SectorCountModel:
    """The fitted model, cached: fitting costs a few seconds of simulation."""
    return SectorCountModel.fit(total_levels=total_levels)


def sector_count_posterior(
    eigenvalues,
    model: SectorCountModel | None = None,
    level: float = COUNT_DEFAULT_LEVEL,
) -> SectorCountEstimate:
    """The sector count as a posterior with a credible interval, from a spectrum alone.

    Replaces the shrug in `estimate_sectors_from_mean`: one sector is measured
    (`p = 0.97`), two sectors is measured as a set (`[2, 3]`, point estimate right 56%
    of the time), and from three upward the interval is `>=3` and the count is not
    recoverable -- reproducing the earlier negative result with an error bar.
    """
    active = model if model is not None else default_sector_count_model()
    return active.estimate(eigenvalues, level=level)

