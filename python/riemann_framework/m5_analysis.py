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
"""M5: the decisive test for the Dimension-Shift Hypothesis.

Two falsification criteria, both from the roadmap. If **either** holds, the DSH is
abandoned -- and that is the result, not a failure.

Criterion (1), structural GOE
    At every `d >= 100` and every coupling, does each `sigma`-sector's mean `r`
    stay inside the GOE window `[0.51, 0.55]` once 300 seeds are used? If yes the
    construction is structurally GOE and cannot carry the zeros' class.

Criterion (2), inherited class
    Is the sector class inherited under every admissible choice of input blocks?
    If yes, any GUE result is an assumption rather than a consequence.

Three corrections to the sketch this module was written from
------------------------------------------------------------
**`block_class` does not exist.** The model takes `matrix_class` (values `"gue"`,
`"goe"`); passing `block_class` raises `TypeError`. This module uses
`matrix_class` and names the field `matrix_class`.

**Criterion (1) is class-conditional, and reporting it without a class would be the
original error wearing a different hat.** The sketch evaluates criterion (1) with
GOE blocks only, labelled "the strictest test". It is the reverse: with GOE blocks
the sectors are GOE *because GOE was put in*, so the criterion would "hold" by
construction and would abandon the DSH on the strength of an input choice. The
admissible family includes GUE blocks -- the hypothesis demands GUE statistics --
so criterion (1) is evaluated for **both** classes and reported per class. Measured
outcome: it holds for `"goe"` and fails for `"gue"`, which makes it a restatement of
criterion (2) rather than independent evidence. That could not be seen under the
sketch's formulation.

**KS tests are per seed, not pooled.** The sketch concatenates eigenvalues from the
last 10 seeds and runs one KS test on the pooled multiset. Pooling independent
spectra into one array creates artificial spacings at the seams, so the statistic
measures the concatenation. Here each seed gets its own KS statistic and the mean
over the last `KS_SEEDS` seeds is reported.

The sector split is also verified rather than assumed: `extract_sectors` goes
through `dimension_shift_chaos.desymmetrise`, which raises when `[H, sigma] != 0`,
and cross-checks the result against `spec(H[:d,:d] +- H[:d,d:])`.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from .dimension_shift_chaos import (
    MATRIX_CLASSES,
    build_dimension_shift_hamiltonian,
    desymmetrise,
    sigma_commutator_ratio,
)
from .statistics import ks_test_against, mean_r_ratio


# ============================================================
# Reference windows
# ============================================================

R_POISSON = 0.386
R_GOE = 0.531
R_GUE = 0.600
R_RIEMANN = 0.610

GOE_WINDOW = (0.51, 0.55)
GUE_WINDOW = (0.58, 0.62)
POISSON_WINDOW = (0.36, 0.41)

#: Required by the specification; a point below this is refused.
N_SEEDS = 300

#: The roadmap's floor for criterion (1).
D_MIN = 100

#: How many seeds contribute to the averaged KS statistic.
KS_SEEDS = 10


# ============================================================
# Result types
# ============================================================

@dataclass
class SectorStatistics:
    """Statistics for one `sigma`-sector of one parameter point."""

    sector: str
    mean_r: float
    std_r: float
    stderr_r: float
    n_seeds: int
    ks_gue: float
    ks_poisson: float
    classification: str

    def summary(self) -> str:
        return (
            f"sector {self.sector}: {self.mean_r:.4f} +- {self.std_r:.4f} "
            f"(sem {self.stderr_r:.4f}, n={self.n_seeds}), "
            f"KS(GUE) {self.ks_gue:.4f}, class {self.classification}"
        )


@dataclass
class ParameterPoint:
    """Statistics for one `(d, coupling, matrix_class)` parameter point."""

    dim_per_sector: int
    coupling: float
    matrix_class: str
    sigma_commutator_ratio: float
    full_spectrum_mean: float
    full_spectrum_std: float
    sector_plus: SectorStatistics
    sector_minus: SectorStatistics

    @property
    def sectors(self) -> tuple[SectorStatistics, SectorStatistics]:
        return (self.sector_plus, self.sector_minus)

    @property
    def full_spectrum_is_gue(self) -> bool:
        return GUE_WINDOW[0] <= self.full_spectrum_mean <= GUE_WINDOW[1]

    def summary(self) -> str:
        return (
            f"d={self.dim_per_sector:3d} c={self.coupling:4.2f} {self.matrix_class}: "
            f"full {self.full_spectrum_mean:.4f} +- {self.full_spectrum_std:.4f}, "
            f"{self.sector_plus.summary()}; {self.sector_minus.summary()}"
        )


@dataclass
class Criterion1Result:
    """Criterion (1), with the per-class split that makes it interpretable."""

    holds: bool
    per_class_holds: dict[str, bool]
    n_sectors_tested: int
    n_sectors_in_goe: int
    n_sectors_in_gue: int
    max_sector_mean: float
    max_sector_mean_point: dict = field(default_factory=dict)
    full_spectrum_never_gue: bool = True
    points: list[ParameterPoint] = field(default_factory=list)
    explanation: str = ""


@dataclass
class Criterion2Result:
    """Criterion (2): is the sector class inherited?"""

    holds: bool
    gue_blocks_lead_to_gue_sectors: int
    goe_blocks_lead_to_gue_sectors: int
    points: list[ParameterPoint] = field(default_factory=list)
    explanation: str = ""


@dataclass
class M5Verdict:
    """The final verdict of the M5 analysis."""

    criterion1: Criterion1Result
    criterion2: Criterion2Result
    dsh_abandoned: bool
    verdict: str
    summary: str


# ============================================================
# Sector extraction
# ============================================================

def extract_sectors(hamiltonian: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Eigenvalues of the `sigma = +1` and `sigma = -1` sectors.

    `sigma`-symmetry forces `H = [[A, C], [C^dagger, A]]`, so the sectors are
    `spec(A + C)` and `spec(A - C)`. The split here goes through
    `desymmetrise`, which raises if `[H, sigma] != 0`, and then checks the
    structural formula against the numerical basis change -- so a broken matrix is
    reported rather than silently returning two blocks.
    """
    matrix = np.asarray(hamiltonian)
    d = matrix.shape[0] // 2
    if matrix.shape != (2 * d, 2 * d):
        raise ValueError("hamiltonian must be of the form (2d, 2d)")

    block_plus, block_minus = desymmetrise(matrix)
    eigenvalues_plus = np.linalg.eigvalsh(block_plus)
    eigenvalues_minus = np.linalg.eigvalsh(block_minus)

    block_a = matrix[:d, :d]
    block_c = matrix[:d, d:]
    expected_plus = np.linalg.eigvalsh(block_a + block_c)
    expected_minus = np.linalg.eigvalsh(block_a - block_c)
    if not np.allclose(eigenvalues_plus, expected_plus, atol=1e-8):
        raise ValueError("sigma=+1 sector does not match spec(A + C)")
    if not np.allclose(eigenvalues_minus, expected_minus, atol=1e-8):
        raise ValueError("sigma=-1 sector does not match spec(A - C)")
    return eigenvalues_plus, eigenvalues_minus


# ============================================================
# One parameter point
# ============================================================

def classify_mean(mean_r: float) -> str:
    """Classify a mean `r`-ratio into a universality class."""
    if GOE_WINDOW[0] <= mean_r <= GOE_WINDOW[1]:
        return "goe"
    if GUE_WINDOW[0] <= mean_r <= GUE_WINDOW[1]:
        return "gue"
    if POISSON_WINDOW[0] <= mean_r <= POISSON_WINDOW[1]:
        return "poisson"
    return "intermediate"


def analyze_point(
    dim_per_sector: int,
    coupling: float,
    matrix_class: str = "gue",
    n_seeds: int = N_SEEDS,
    seed_base: int = 0,
) -> ParameterPoint:
    """`n_seeds` independent realisations of one parameter point.

    Seeds are `seed_base .. seed_base + n_seeds - 1`, so the study is reproducible
    from two integers.
    """
    if n_seeds < N_SEEDS:
        raise ValueError(
            f"criterion tests need at least {N_SEEDS} seeds, got {n_seeds}: a "
            "verdict from fewer is the artefact this milestone exists to settle"
        )
    if matrix_class not in MATRIX_CLASSES:
        raise ValueError(f"matrix_class must be one of {MATRIX_CLASSES}")

    full_means: list[float] = []
    plus_means: list[float] = []
    minus_means: list[float] = []
    plus_ks: list[float] = []
    plus_ks_poisson: list[float] = []
    minus_ks: list[float] = []
    minus_ks_poisson: list[float] = []
    ratio = float("nan")

    for index in range(n_seeds):
        seed = seed_base + index
        hamiltonian = build_dimension_shift_hamiltonian(
            dim_per_sector=dim_per_sector,
            coupling=coupling,
            matrix_class=matrix_class,
            seed=seed,
        )
        ratio = sigma_commutator_ratio(hamiltonian)

        if index == 0:
            # Verify the split once per point: `extract_sectors` goes through
            # `desymmetrise` and cross-checks `spec(A +- C)`. Repeating that on
            # all 300 seeds would double the runtime of a five-minute study to
            # re-establish a property of the construction, so the remaining seeds
            # use the verified structural formula.
            eigenvalues_plus, eigenvalues_minus = extract_sectors(hamiltonian)
        else:
            block = hamiltonian[:dim_per_sector, :dim_per_sector]
            inter = hamiltonian[:dim_per_sector, dim_per_sector:]
            eigenvalues_plus = np.linalg.eigvalsh(block + inter)
            eigenvalues_minus = np.linalg.eigvalsh(block - inter)

        full_means.append(mean_r_ratio(np.linalg.eigvalsh(hamiltonian), unfold=False))
        plus_means.append(mean_r_ratio(eigenvalues_plus, unfold=False))
        minus_means.append(mean_r_ratio(eigenvalues_minus, unfold=False))

        if index >= n_seeds - KS_SEEDS:
            plus_ks.append(ks_test_against(eigenvalues_plus, reference="gue", unfold=False)["ks_stat"])
            plus_ks_poisson.append(ks_test_against(eigenvalues_plus, reference="poisson", unfold=False)["ks_stat"])
            minus_ks.append(ks_test_against(eigenvalues_minus, reference="gue", unfold=False)["ks_stat"])
            minus_ks_poisson.append(ks_test_against(eigenvalues_minus, reference="poisson", unfold=False)["ks_stat"])

    def _sector(name: str, means: list[float], ks: list[float], ks_p: list[float]) -> SectorStatistics:
        array = np.array(means)
        return SectorStatistics(
            sector=name,
            mean_r=float(array.mean()),
            std_r=float(array.std(ddof=1)),
            stderr_r=float(array.std(ddof=1) / np.sqrt(array.size)),
            n_seeds=int(array.size),
            ks_gue=float(np.mean(ks)),
            ks_poisson=float(np.mean(ks_p)),
            classification=classify_mean(float(array.mean())),
        )

    return ParameterPoint(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        matrix_class=matrix_class,
        sigma_commutator_ratio=ratio,
        full_spectrum_mean=float(np.mean(full_means)),
        full_spectrum_std=float(np.std(full_means, ddof=1)),
        sector_plus=_sector("+1", plus_means, plus_ks, plus_ks_poisson),
        sector_minus=_sector("-1", minus_means, minus_ks, minus_ks_poisson),
    )


# ============================================================
# Criterion (1): structural GOE
# ============================================================

def evaluate_criterion_1(
    dims: Optional[list[int]] = None,
    couplings: Optional[list[float]] = None,
    matrix_classes: tuple[str, ...] = MATRIX_CLASSES,
    n_seeds: int = N_SEEDS,
    progress: Optional[Callable[[str], None]] = None,
) -> Criterion1Result:
    """Does every sector stay in the GOE window at `d >= 100`, for *every* class?

    `holds` is `True` only if the answer is yes for every admissible class. The
    per-class results are returned as well, because the answer differs by class and
    that difference is the finding: with GOE blocks the sectors are GOE by
    construction, so a criterion that held only there would be measuring the input.
    """
    if dims is None:
        dims = [D_MIN, 150, 200]
    if couplings is None:
        couplings = [0.5, 1.0, 2.0, 5.0]
    if any(d < D_MIN for d in dims):
        raise ValueError(f"criterion (1) is stated for d >= {D_MIN}")

    per_class_holds: dict[str, bool] = {}
    n_sectors_tested = 0
    n_sectors_in_goe = 0
    n_sectors_in_gue = 0
    max_mean = -np.inf
    max_point: dict = {}
    full_never_gue = True
    points: list[ParameterPoint] = []

    for matrix_class in matrix_classes:
        class_ok = True
        for dimension in dims:
            for coupling in couplings:
                point = analyze_point(
                    dimension, coupling, matrix_class, n_seeds=n_seeds
                )
                points.append(point)
                if progress is not None:
                    progress(
                        f"d={dimension:3d} c={coupling:4.2f} {matrix_class}: "
                        f"full {point.full_spectrum_mean:.4f}, "
                        f"sectors {point.sector_plus.mean_r:.4f}/"
                        f"{point.sector_minus.mean_r:.4f}"
                    )
                if point.sigma_commutator_ratio > 1e-10:
                    raise ValueError(
                        f"model is not sigma-symmetric at d={dimension}, "
                        f"c={coupling}: {point.sigma_commutator_ratio:.2e}"
                    )
                if point.full_spectrum_is_gue:
                    full_never_gue = False
                for sector in point.sectors:
                    n_sectors_tested += 1
                    if GOE_WINDOW[0] <= sector.mean_r <= GOE_WINDOW[1]:
                        n_sectors_in_goe += 1
                    else:
                        class_ok = False
                    if GUE_WINDOW[0] <= sector.mean_r <= GUE_WINDOW[1]:
                        n_sectors_in_gue += 1
                    if sector.mean_r > max_mean:
                        max_mean = sector.mean_r
                        max_point = {
                            "d": dimension,
                            "coupling": coupling,
                            "matrix_class": matrix_class,
                            "sector": sector.sector,
                            "mean_r": sector.mean_r,
                            "std_r": sector.std_r,
                        }
        per_class_holds[matrix_class] = class_ok

    holds = all(per_class_holds.values()) and n_sectors_in_gue == 0

    if holds:
        explanation = (
            f"Criterion (1) HOLDS: all {n_sectors_tested} sectors at d >= {D_MIN} "
            f"stay inside [{GOE_WINDOW[0]}, {GOE_WINDOW[1]}] for every class and "
            "coupling, with none in the GUE window. The construction is structurally "
            "GOE and cannot carry the zeros' class."
        )
    else:
        failing = sorted(name for name, ok in per_class_holds.items() if not ok)
        explanation = (
            f"Criterion (1) does NOT hold as stated: {n_sectors_in_goe} of "
            f"{n_sectors_tested} sector means are in the GOE window and "
            f"{n_sectors_in_gue} are in the GUE window; the failing class"
            f"{'es are' if len(failing) > 1 else ' is'} {failing}. It is "
            "class-conditional: with GOE blocks the sectors are GOE because GOE was "
            "put in, and with GUE blocks they leave the window. A criterion that "
            "depends on the input class is criterion (2), not independent evidence."
        )

    return Criterion1Result(
        holds=holds,
        per_class_holds=per_class_holds,
        n_sectors_tested=n_sectors_tested,
        n_sectors_in_goe=n_sectors_in_goe,
        n_sectors_in_gue=n_sectors_in_gue,
        max_sector_mean=float(max_mean),
        max_sector_mean_point=max_point,
        full_spectrum_never_gue=full_never_gue,
        points=points,
        explanation=explanation,
    )


# ============================================================
# Criterion (2): inherited class
# ============================================================

def evaluate_criterion_2(
    dim_per_sector: int = D_MIN,
    coupling: float = 1.0,
    n_seeds: int = N_SEEDS,
) -> Criterion2Result:
    """Is the sector class inherited from the input blocks?

    Holds when GUE blocks give GUE sectors **and** GOE blocks give no GUE sector.

    The two points are keyed by class name, not by position. `MATRIX_CLASSES` is
    `("goe", "gue")`, so the first draft's `gue_point = points[0]` silently named
    the GOE point "gue" and inverted this criterion -- it reported the class as *not*
    inherited, i.e. it exonerated the hypothesis. Keying by name, and the
    `points[i].matrix_class` assertions in the tests, is what stops that recurring.
    """
    by_class = {
        matrix_class: analyze_point(
            dim_per_sector, coupling, matrix_class, n_seeds=n_seeds
        )
        for matrix_class in MATRIX_CLASSES
    }
    points = [by_class[name] for name in MATRIX_CLASSES]
    gue_point = by_class["gue"]
    goe_point = by_class["goe"]

    gue_leads = sum(1 for sector in gue_point.sectors if sector.classification == "gue")
    goe_leads = sum(1 for sector in goe_point.sectors if sector.classification == "gue")

    holds = gue_leads == len(gue_point.sectors) and goe_leads == 0

    if holds:
        explanation = (
            f"Criterion (2) HOLDS: the sector class is inherited. GUE blocks give "
            f"{gue_leads}/{len(gue_point.sectors)} GUE sectors; GOE blocks give "
            f"{goe_leads}/{len(goe_point.sectors)}. Any GUE result is therefore an "
            "assumption about the input, not a consequence of the sigma structure."
        )
    else:
        explanation = (
            f"Criterion (2) does NOT hold: GUE blocks -> {gue_leads} GUE sectors, "
            f"GOE blocks -> {goe_leads} GUE sectors."
        )

    return Criterion2Result(
        holds=holds,
        gue_blocks_lead_to_gue_sectors=gue_leads,
        goe_blocks_lead_to_gue_sectors=goe_leads,
        points=points,
        explanation=explanation,
    )


# ============================================================
# The verdict
# ============================================================

def run_m5_analysis(
    n_seeds: int = N_SEEDS,
    progress: Optional[Callable[[str], None]] = None,
) -> M5Verdict:
    """Run both criteria and settle the question.

    The DSH is abandoned if *either* criterion holds.
    """
    criterion1 = evaluate_criterion_1(n_seeds=n_seeds, progress=progress)
    criterion2 = evaluate_criterion_2(n_seeds=n_seeds)
    abandoned = criterion1.holds or criterion2.holds

    if abandoned:
        reasons = []
        if criterion1.holds:
            reasons.append("the construction is structurally GOE")
        if criterion2.holds:
            reasons.append("the sector class is inherited, not produced")
        verdict = "abandoned"
        summary = (
            "DSH is ABANDONED. Reason(s): " + "; ".join(reasons) + ". This is the "
            "result, not a failure."
        )
    else:
        verdict = "survives"
        summary = (
            "DSH SURVIVES both criteria: neither structural GOE nor inherited class "
            "is confirmed. The hypothesis remains open."
        )

    return M5Verdict(
        criterion1=criterion1,
        criterion2=criterion2,
        dsh_abandoned=abandoned,
        verdict=verdict,
        summary=summary,
    )
