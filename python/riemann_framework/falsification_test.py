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
"""Multi-seed falsification test for the Dimension-Shift Hypothesis (DSH).

The version of this module that shipped until now quantified nothing. It ran one
seed per parameter point, took the maximum mean `r`-ratio over a 90-point grid,
and reported "supported" if that maximum fell inside `[0.58, 0.62]`. Both halves
of that are broken, and the measurements are in `docs/lessons_learned.md`:

* **The maximum of a noisy statistic passes any window eventually.** At
  `2d = 20` the per-seed standard deviation of the mean `r`-ratio is `0.075`, and
  `14%` of *pure GOE* draws land inside the "GUE window" `[0.58, 0.62]` under the
  settings the old grid used (`23%` with `unfold=False`; the unfolding choice
  moves the number, which is another reason not to calibrate a window on a single
  draw). With 90 grid points the window is hit about a dozen times by chance
  alone. The reported point -- `d = 10, coupling = 0.5, sb = 2.0`,
  `mean r = 0.6117` -- has a 300-seed mean of `0.5226 +- 0.0694`: it is a
  `+1.3 sigma` fluctuation of a GOE model.
* **A single seed cannot carry a verdict.** Every function here reports a mean
  over at least `SEEDS_MIN` seeds with the standard deviation, the standard
  error, and the observed range.

The verdict vocabulary is fixed by the specification and implemented literally:

======================  ==========================================================
``supported_multi_seed``  a parameter point has ``mean r`` in ``[0.58, 0.62]`` with
                          per-seed ``std < 0.02``
``goe_only``              every point has ``mean r`` in ``[0.51, 0.55]``
``poisson_only``          every point has ``mean r`` in ``[0.36, 0.41]``
``mixed``                 every point has ``mean r < 0.55`` but some single
                          ``sigma``-sector lands in ``[0.58, 0.62]``
``inconclusive``          none of the above
======================  ==========================================================

The ``std < 0.02`` threshold is implemented as written and is **unreachable at
mathematical-plausible sizes**: measured per-seed `std` is `0.069` at `2d = 20`,
`0.046` at `2d = 100` and `0.031` at `2d = 200`, and it scales like
`1/sqrt(2d)`. Reaching `0.02` needs a few hundred levels, which is reported as a
finding about the criterion rather than worked around by redefining `std`. The
standard error of the mean at 300 seeds is reported next to it, because that is
the quantity a mean should be judged by.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from .dimension_shift_chaos import (
    MATRIX_CLASSES,
    analyze_dimension_shift,
)
from .statistics import classify_statistics, ks_test_against, mean_r_ratio


# ============================================================
# Reference values and windows
# ============================================================

R_POISSON = 0.386
R_GOE = 0.530
R_GUE = 0.599

GUE_WINDOW = (0.58, 0.62)
GOE_WINDOW = (0.51, 0.55)
POISSON_WINDOW = (0.36, 0.41)

#: Specification minimum. Anything below this is not a verdict.
SEEDS_MIN = 300

#: Threshold on the per-seed standard deviation, as specified.
STD_THRESHOLD = 0.02

VERDICTS = (
    "supported_multi_seed",
    "goe_only",
    "poisson_only",
    "mixed",
    "inconclusive",
)


def classify_verdict(mean_r: float) -> str:
    """Classify one mean `r`-ratio into a regime (single number, no statistics)."""
    if GUE_WINDOW[0] <= mean_r <= GUE_WINDOW[1]:
        return "gue"
    if GOE_WINDOW[0] <= mean_r <= GOE_WINDOW[1]:
        return "goe"
    if POISSON_WINDOW[0] <= mean_r <= POISSON_WINDOW[1]:
        return "poisson"
    return "intermediate"


# ============================================================
# One seed: retained, but it is not a verdict
# ============================================================

@dataclass
class FalsificationResult:
    """One parameter point at one seed.

    Kept for diagnostics and for the per-seed distributions. **It is not a
    verdict**; use `run_point_multiseed` for anything reported.
    """

    dim_per_sector: int
    coupling: float
    matrix_class: str
    mean_r_full: float
    mean_r_plus: float
    best_fit: str
    ks_gue: float
    ks_poisson: float
    verdict: str


def run_single(
    dim_per_sector: int,
    coupling: float,
    matrix_class: str = "gue",
    seed: int = 42,
) -> FalsificationResult:
    """Run one parameter point at one seed."""
    analysis = analyze_dimension_shift(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        matrix_class=matrix_class,
        seed=seed,
    )
    return FalsificationResult(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        matrix_class=matrix_class,
        mean_r_full=analysis["mean_r_full"],
        mean_r_plus=analysis["mean_r_plus"],
        best_fit=analysis["classification_full"]["best_fit"],
        ks_gue=analysis["ks_gue_full"],
        ks_poisson=analysis["ks_poisson_full"],
        verdict=classify_verdict(analysis["mean_r_full"]),
    )


# ============================================================
# Many seeds: the unit of evidence
# ============================================================

@dataclass(frozen=True)
class MultiSeedPoint:
    """One parameter point over many seeds, with everything needed to judge it."""

    dim_per_sector: int
    coupling: float
    matrix_class: str
    seeds: int
    sigma_commutator_ratio: float

    mean_full: float
    std_full: float
    min_full: float
    max_full: float
    fraction_full_in_gue_window: float

    mean_plus: float
    std_plus: float
    mean_minus: float
    std_minus: float

    @property
    def sem_full(self) -> float:
        return self.std_full / float(np.sqrt(self.seeds))

    @property
    def std_is_below_threshold(self) -> bool:
        return self.std_full < STD_THRESHOLD

    @property
    def mean_in_gue_window(self) -> bool:
        return GUE_WINDOW[0] <= self.mean_full <= GUE_WINDOW[1]

    @property
    def sector_reaches_gue(self) -> bool:
        return any(
            GUE_WINDOW[0] <= value <= GUE_WINDOW[1]
            for value in (self.mean_plus, self.mean_minus)
        )

    @property
    def sector_above_window(self) -> bool:
        """A sector mean above `0.62`: reported, never promoted to a verdict."""
        return any(
            value > GUE_WINDOW[1] for value in (self.mean_plus, self.mean_minus)
        )

    @property
    def classifications(self) -> dict[str, str]:
        """`classify_verdict` applied to the full spectrum and to each sector.

        Reported per point so a reader can see *which* spectrum a label came from;
        the verdict itself is computed from the sector means (see `_label`).
        """
        return {
            "full": classify_verdict(self.mean_full),
            "sector_plus": classify_verdict(self.mean_plus),
            "sector_minus": classify_verdict(self.mean_minus),
        }

    def summary(self) -> str:
        return (
            f"d={self.dim_per_sector:3d} coupling={self.coupling:4.2f} "
            f"{self.matrix_class}: full {self.mean_full:.4f} +- {self.std_full:.4f} "
            f"(sem {self.sem_full:.4f}, n={self.seeds}), "
            f"sector+ {self.mean_plus:.4f} +- {self.std_plus:.4f}, "
            f"sector- {self.mean_minus:.4f} +- {self.std_minus:.4f}, "
            f"||[H,sigma]||/||H|| = {self.sigma_commutator_ratio:.0e}"
        )

    def classified_summary(self) -> str:
        labels = self.classifications
        return (
            f"d={self.dim_per_sector:3d} c={self.coupling:4.2f} {self.matrix_class}: "
            f"full {self.mean_full:.4f} [{labels['full']}], "
            f"sector+ {self.mean_plus:.4f} [{labels['sector_plus']}], "
            f"sector- {self.mean_minus:.4f} [{labels['sector_minus']}]"
        )


def run_point_multiseed(
    dim_per_sector: int,
    coupling: float,
    matrix_class: str = "gue",
    seeds: int = SEEDS_MIN,
    seed_offset: int = 0,
    unfold: bool = False,
) -> MultiSeedPoint:
    """`seeds` independent realisations of one parameter point.

    Every realisation is a fresh Hamiltonian; the seeds are `seed_offset ..
    seed_offset + seeds - 1`, so the whole study is reproducible from two
    integers.
    """
    if seeds < 2:
        raise ValueError("a multi-seed point needs at least 2 seeds")
    if seeds < SEEDS_MIN:
        raise ValueError(
            f"seeds must be at least {SEEDS_MIN}: a verdict from fewer is exactly "
            "the artefact this module exists to replace"
        )
    if matrix_class not in MATRIX_CLASSES:
        raise ValueError(f"matrix_class must be one of {MATRIX_CLASSES}")

    full: list[float] = []
    plus: list[float] = []
    minus: list[float] = []
    ratio = float("nan")

    for seed in range(seed_offset, seed_offset + seeds):
        analysis = analyze_dimension_shift(
            dim_per_sector=dim_per_sector,
            coupling=coupling,
            matrix_class=matrix_class,
            seed=seed,
            unfold=unfold,
        )
        ratio = analysis["sigma_commutator_ratio"]
        full.append(analysis["mean_r_full"])
        plus.append(analysis["mean_r_plus"])
        minus.append(analysis["mean_r_minus"])

    full_array = np.array(full)
    return MultiSeedPoint(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        matrix_class=matrix_class,
        seeds=seeds,
        sigma_commutator_ratio=ratio,
        mean_full=float(full_array.mean()),
        std_full=float(full_array.std(ddof=1)),
        min_full=float(full_array.min()),
        max_full=float(full_array.max()),
        fraction_full_in_gue_window=float(
            np.mean((full_array >= GUE_WINDOW[0]) & (full_array <= GUE_WINDOW[1]))
        ),
        mean_plus=float(np.mean(plus)),
        std_plus=float(np.std(plus, ddof=1)),
        mean_minus=float(np.mean(minus)),
        std_minus=float(np.std(minus, ddof=1)),
    )


def run_multiseed_grid(
    dim_per_sector_values: tuple[int, ...] = (10, 20, 40),
    coupling_values: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0),
    matrix_classes: tuple[str, ...] = MATRIX_CLASSES,
    seeds: int = SEEDS_MIN,
    seed_offset: int = 0,
) -> list[MultiSeedPoint]:
    """The full grid, every point at `seeds` seeds.

    `coupling = 0` is **excluded**: with no inter-sector block the two diagonal
    blocks coincide, every level is exactly doubly degenerate, and the mean
    `r`-ratio is `0` -- a degenerate spectrum, not a chaos class. It is kept as a
    control in `tests/test_falsification.py` and in
    `dimension_shift_chaos.sigma_control` instead of being averaged into a
    verdict.
    """
    if any(coupling <= 0.0 for coupling in coupling_values):
        raise ValueError(
            "coupling = 0 gives an exactly degenerate spectrum (r = 0); run it as "
            "a control, not as a grid point"
        )
    points: list[MultiSeedPoint] = []
    for dim in dim_per_sector_values:
        for coupling in coupling_values:
            for matrix_class in matrix_classes:
                points.append(
                    run_point_multiseed(
                        dim_per_sector=dim,
                        coupling=coupling,
                        matrix_class=matrix_class,
                        seeds=seeds,
                        seed_offset=seed_offset,
                    )
                )
    return points


# ============================================================
# The verdict
# ============================================================

@dataclass(frozen=True)
class MultiSeedVerdict:
    """The five-label verdict, with the evidence attached to it."""

    verdict: str
    seeds: int
    n_points: int
    explanation: str
    gue_points: list[MultiSeedPoint] = field(default_factory=list)
    mean_std_full: float = float("nan")
    std_threshold_reachable: bool = False
    mean_fraction_in_gue_window: float = float("nan")
    per_class: dict[str, "MultiSeedVerdict"] = field(default_factory=dict)
    sectors_in_window: list[str] = field(default_factory=list)
    sectors_outside_window: list[str] = field(default_factory=list)
    full_spectrum_anomaly: bool = False

    def summary(self) -> str:
        lines = [
            f"verdict: {self.verdict}",
            f"seeds per point: {self.seeds}",
            f"parameter points: {self.n_points}",
            f"mean per-seed std of r: {self.mean_std_full:.4f} "
            f"(threshold {STD_THRESHOLD} reachable: {self.std_threshold_reachable})",
            f"explanation: {self.explanation}",
        ]
        if self.sectors_in_window:
            lines.append(
                "sectors inside [0.58, 0.62]: " + ", ".join(self.sectors_in_window)
            )
        if self.sectors_outside_window:
            lines.append(
                "sectors ABOVE 0.62 (reported, not promoted to a verdict): "
                + ", ".join(self.sectors_outside_window)
            )
        if self.full_spectrum_anomaly:
            lines.append(
                "STRUCTURAL ANOMALY: a full spectrum landed inside the GUE window, "
                "which contradicts the sector-superposition prediction"
            )
        for name, sub in sorted(self.per_class.items()):
            lines.append(f"  class {name}: {sub.verdict} -- {sub.explanation}")
        return "\n".join(lines)


def _label(points: list[MultiSeedPoint]) -> tuple[str, str]:
    """Apply the specification's table to a set of points: `(verdict, explanation)`."""
    full_means = [point.mean_full for point in points]
    sector_rows = [
        (point, label, mean, std)
        for point in points
        for label, mean, std in (
            ("sector+", point.mean_plus, point.std_plus),
            ("sector-", point.mean_minus, point.std_minus),
        )
    ]
    sector_means = [row[2] for row in sector_rows]

    # `supported_multi_seed` is a claim about a SECTOR, because the DSH's object is
    # a spectral subsequence, not the whole superposition. The `std` clause is
    # applied as written; it is unreachable at these matrix sizes (measured
    # 0.084 at 2d = 20 down to 0.026 at 2d = 200) and is not relaxed here.
    qualifying = [
        row
        for row in sector_rows
        if GUE_WINDOW[0] <= row[2] <= GUE_WINDOW[1] and row[3] < STD_THRESHOLD
    ]
    if qualifying:
        point, label, mean, std = max(qualifying, key=lambda row: row[2])
        return "supported_multi_seed", (
            f"{len(qualifying)} of {2 * len(points)} sector means are in "
            f"[{GUE_WINDOW[0]}, {GUE_WINDOW[1]}] with per-seed std below "
            f"{STD_THRESHOLD}; the strongest is {label} at d={point.dim_per_sector}, "
            f"coupling={point.coupling}, class={point.matrix_class}: "
            f"{mean:.4f} +- {std:.4f}."
        )
    if all(GOE_WINDOW[0] <= mean <= GOE_WINDOW[1] for mean in sector_means):
        return "goe_only", (
            f"every sector mean is in [{GOE_WINDOW[0]}, {GOE_WINDOW[1]}] "
            f"(range {min(sector_means):.4f} .. {max(sector_means):.4f}): the model "
            "is in the time-reversal-symmetric class, and no sector reaches GUE."
        )
    if all(POISSON_WINDOW[0] <= mean <= POISSON_WINDOW[1] for mean in sector_means):
        return "poisson_only", (
            f"every sector mean is in [{POISSON_WINDOW[0]}, {POISSON_WINDOW[1]}]: "
            "the model is integrable across the tested parameters."
        )
    if all(mean < 0.55 for mean in full_means) and any(
        point.sector_reaches_gue for point in points
    ):
        sectors = sorted({point.matrix_class for point in points if point.sector_reaches_gue})
        return "mixed", (
            f"the full spectrum never reaches GUE (means {min(full_means):.4f} .. "
            f"{max(full_means):.4f}, a superposition of two sectors), while a single "
            f"sigma-sector does -- in classes {sectors}. The sector class is "
            "inherited from the input blocks, so this shows the construction can "
            "carry GUE statistics, not that it produces them."
        )
    return "inconclusive", (
        f"the sector means ({min(sector_means):.4f} .. {max(sector_means):.4f}) and "
        f"the full-spectrum means ({min(full_means):.4f} .. {max(full_means):.4f}) "
        "match no reference window cleanly."
    )


def classify_multi_seed(points: list[MultiSeedPoint]) -> MultiSeedVerdict:
    """Apply the specification's verdict table to multi-seed evidence.

    The verdict is computed from the **sector** means, because the DSH's object is
    a spectral subsequence and not the whole superposition; the full spectrum is
    reported as the baseline it is. `mixed` is the label that records the
    difference, and it is the one this model actually earns: a `sigma`-symmetric
    spectrum is a superposition of two sectors, lands near `0.42` as a whole, and
    reaches GUE in a sector only when the input blocks were GUE.

    Two reporting anomalies are attached rather than folded into the verdict: a
    sector mean above `0.62` (outside the window, so `supported_multi_seed` is not
    earned) and a *full* spectrum inside the window (which would contradict the
    superposition prediction and means the construction or the window is wrong).

    Note one inconsistency in the specification, resolved here in favour of the
    verdict table: its criterion F1.1 asks that a sector reaching `mean r > 0.62`
    be *reported as* `supported_multi_seed`, while the table requires
    `mean r in [0.58, 0.62]`. Promoting an out-of-window number to a positive
    verdict would repeat exactly the error the single-seed grid made, so the table
    is implemented literally and the excess is reported as
    `sectors_outside_window`.
    """
    if not points:
        raise ValueError("need at least one multi-seed point")
    seeds = {point.seeds for point in points}
    if len(seeds) != 1:
        raise ValueError(f"all points must use the same seed count, got {sorted(seeds)}")
    seed_count = seeds.pop()
    if seed_count < SEEDS_MIN:
        raise ValueError(f"a verdict needs at least {SEEDS_MIN} seeds, got {seed_count}")

    verdict, explanation = _label(points)

    def _anomalies(subset: list[MultiSeedPoint], seed_total: int) -> tuple[list[str], list[str], bool]:
        inside: list[str] = []
        outside: list[str] = []
        for point in subset:
            for label, mean in (
                ("sector+", point.mean_plus),
                ("sector-", point.mean_minus),
            ):
                tag = (
                    f"{label} d={point.dim_per_sector} c={point.coupling:g} "
                    f"{point.matrix_class} ({mean:.4f})"
                )
                if GUE_WINDOW[0] <= mean <= GUE_WINDOW[1]:
                    inside.append(tag)
                elif mean > GUE_WINDOW[1]:
                    outside.append(tag)
        anomaly = any(
            GUE_WINDOW[0] <= point.mean_full <= GUE_WINDOW[1] for point in subset
        )
        return inside, outside, anomaly

    per_class: dict[str, MultiSeedVerdict] = {}
    for matrix_class in sorted({point.matrix_class for point in points}):
        subset = [point for point in points if point.matrix_class == matrix_class]
        class_verdict, class_explanation = _label(subset)
        inside, outside, anomaly = _anomalies(subset, seed_count)
        per_class[matrix_class] = MultiSeedVerdict(
            verdict=class_verdict,
            seeds=seed_count,
            n_points=len(subset),
            explanation=class_explanation,
            gue_points=[
                point
                for point in subset
                if point.mean_in_gue_window and point.std_is_below_threshold
            ],
            mean_std_full=float(np.mean([point.std_full for point in subset])),
            std_threshold_reachable=any(
                point.std_is_below_threshold for point in subset
            ),
            mean_fraction_in_gue_window=float(
                np.mean([point.fraction_full_in_gue_window for point in subset])
            ),
            sectors_in_window=inside,
            sectors_outside_window=outside,
            full_spectrum_anomaly=anomaly,
        )

    inside, outside, anomaly = _anomalies(points, seed_count)
    return MultiSeedVerdict(
        verdict=verdict,
        seeds=seed_count,
        n_points=len(points),
        explanation=explanation,
        gue_points=[
            point
            for point in points
            if point.mean_in_gue_window and point.std_is_below_threshold
        ],
        mean_std_full=float(np.mean([point.std_full for point in points])),
        std_threshold_reachable=any(point.std_is_below_threshold for point in points),
        mean_fraction_in_gue_window=float(
            np.mean([point.fraction_full_in_gue_window for point in points])
        ),
        per_class=per_class,
        sectors_in_window=inside,
        sectors_outside_window=outside,
        full_spectrum_anomaly=anomaly,
    )


def size_scaling_study(
    sizes: tuple[int, ...] = (20, 50, 100, 200),
    seeds: int = 120,
    seed_offset: int = 0,
) -> list[tuple[int, float, float]]:
    """Per-seed `std` against matrix size, for the `std < 0.02` threshold.

    The threshold in the specification is a statement about a *single* seed's
    noise, so its reachability depends on the matrix size. This measures the
    dependence rather than asserting it: `(size, mean, std)` per row.
    """
    rows: list[tuple[int, float, float]] = []
    for size in sizes:
        values = []
        for seed in range(seed_offset, seed_offset + seeds):
            analysis = analyze_dimension_shift(
                dim_per_sector=size // 2,
                coupling=1.0,
                matrix_class="gue",
                seed=seed,
            )
            values.append(analysis["mean_r_full"])
        rows.append((size, float(np.mean(values)), float(np.std(values, ddof=1))))
    return rows


# ============================================================
# Legacy single-seed helpers, retained only for diagnostics
# ============================================================

def reference_statistics(
    size: int = 100,
    samples: int = 200,
    seed: int = 0,
    unfold: bool = False,
) -> dict[str, tuple[float, float]]:
    """GOE and GUE means measured at the *same* settings as the grid.

    The pre-correction code calibrated its windows against the asymptotic
    constants `R_GUE = 0.599` and `R_GOE = 0.530`, but its own reference call
    (`compare_reference_systems`) drew **one** matrix and reported `0.574`, a
    `-0.8 sigma` fluctuation. That mismatch is one reason the old window
    `[0.58, 0.62]` could accept a GOE outlier while rejecting a genuine GUE
    matrix. Here the references are sampled, with the standard deviation, so a
    window can be checked against what the matrices actually do.
    """
    rng = np.random.default_rng(seed)
    results: dict[str, tuple[float, float]] = {}
    for matrix_class in MATRIX_CLASSES:
        values: list[float] = []
        for _ in range(samples):
            if matrix_class == "gue":
                raw = (
                    rng.standard_normal((size, size))
                    + 1j * rng.standard_normal((size, size))
                ) / np.sqrt(2.0)
                matrix = (raw + raw.conj().T) / 2.0
            else:
                raw = rng.standard_normal((size, size))
                matrix = (raw + raw.T) / 2.0
            values.append(float(mean_r_ratio(np.linalg.eigvalsh(matrix), unfold=unfold)))
        results[matrix_class] = (float(np.mean(values)), float(np.std(values, ddof=1)))
    results["poisson"] = (R_POISSON, 0.0)
    results["asymptotic_gue"] = (R_GUE, 0.0)
    results["asymptotic_goe"] = (R_GOE, 0.0)
    return results
