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
"""The sector count when the sectors are not the same size.

The posterior in :mod:`riemann_framework.desymmetrisation` is fitted on equal blocks:
``m`` sectors each of ``total_levels // m`` levels. No real Hamiltonian is that tidy. A
sector can dominate -- an asymmetric double well, one parity class carrying most of the
weight -- and the question this module answers by measurement is whether the count
survives that, and whether the *ratio* of the block sizes can be recovered at all.

The hypothesis space is two-dimensional. A label is ``(n_sectors, size_ratio)``, where the
size ratio is the largest block against the smallest, so ``1`` is the equal case the
manuscript assumes and ``4`` is a dominant sector. The occupancy of the largest block
follows from it: ``ratio / (ratio + n_sectors - 1)``.

Two posteriors are compared on the *same* mixed spectra:

* :class:`MixedSectorModel`, fitted on a grid of ``(m, ratio)`` labels;
* the equal-block :class:`~riemann_framework.desymmetrisation.HigherOrderCountModel`,
  applied unchanged, which is what the framework currently offers.

The measured difference is the point: an estimator whose model does not contain the truth
is not merely less precise, it is biased, and the size of the bias is a number.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .desymmetrisation import (
    COUNT_ORDERS,
    SectorCountEstimate,
    spectrum_features,
)

#: Sector counts the mixed model is fitted at. Five is left out because the manuscript's
#: own grid leaves it out; seven and above are indistinguishable from Poisson.
DEFAULT_SECTORS: tuple[int, ...] = (1, 2, 3, 4, 6)

#: Largest-block-to-smallest-block ratios. One is the equal case, and the other two are a
#: factor of two and a factor of four, which at 240 levels still leave every block large
#: enough (26 or more levels) for six spacing orders.
DEFAULT_SIZE_RATIOS: tuple[float, ...] = (1.0, 2.0, 4.0)

#: Total levels per spectrum, held fixed so the feature vector's noise level is the same
#: for every hypothesis.
DEFAULT_LEVELS = 240

#: Spectra per label in the training and test sets.
DEFAULT_SEEDS = 40

#: Credible level used when a summary is asked for without one.
DEFAULT_LEVEL = 0.9


@dataclass(frozen=True)
class MixedLabel:
    """One hypothesis: ``n_sectors`` blocks, the largest ``size_ratio`` times the smallest."""

    n_sectors: int
    size_ratio: float

    def __post_init__(self) -> None:
        if self.n_sectors < 1:
            raise ValueError("need at least one sector")
        if self.size_ratio < 1.0:
            raise ValueError("the largest block cannot be smaller than the smallest")
        if self.n_sectors == 1 and self.size_ratio != 1.0:
            raise ValueError("a single sector has no size ratio")

    @property
    def occupation(self) -> float:
        """The fraction of levels carried by the largest block.

        ``ratio / (ratio + m - 1)``: with ``m = 2`` and ``ratio = 1`` this is ``1/2``, the
        even split; with ``ratio = 4`` it is ``4/5``, one block carrying eighty per cent.
        """
        if self.n_sectors == 1:
            return 1.0
        return self.size_ratio / (self.size_ratio + self.n_sectors - 1.0)

    def summary(self) -> str:
        if self.n_sectors == 1:
            return "1 sector"
        return f"{self.n_sectors} sectors, size ratio {self.size_ratio:g}"


def block_dimensions(
    n_sectors: int, size_ratio: float, total_levels: int = DEFAULT_LEVELS
) -> tuple[int, ...]:
    """The level count of each block, largest first, summing to ``total_levels``.

    The largest block takes ``size_ratio`` parts and each of the others one, rounded to
    integers and with the rounding remainder handed to the largest block so the total stays
    fixed. A block never gets fewer than four levels, the floor below which a spacing ratio
    has nothing to measure.
    """
    if n_sectors < 1:
        raise ValueError("need at least one sector")
    if size_ratio < 1.0:
        raise ValueError("the largest block cannot be smaller than the smallest")
    if n_sectors == 1:
        if size_ratio != 1.0:
            raise ValueError("a single sector has no size ratio")
        return (total_levels,)
    parts = size_ratio + (n_sectors - 1)
    smallest = int(round(total_levels / parts))
    largest = total_levels - (n_sectors - 1) * smallest
    if smallest < 4 or largest < smallest:
        raise ValueError(
            f"{n_sectors} sectors at ratio {size_ratio:g} cannot be packed into "
            f"{total_levels} levels"
        )
    return (largest,) + (smallest,) * (n_sectors - 1)


def _random_block(
    dimension: int, block_class: str, rng: np.random.Generator
) -> np.ndarray:
    """One sector: eigenvalues of a GOE or GUE matrix of ``dimension``."""
    if block_class == "goe":
        raw = rng.standard_normal((dimension, dimension))
        matrix = (raw + raw.T) / 2.0
    elif block_class == "gue":
        raw = (
            rng.standard_normal((dimension, dimension))
            + 1j * rng.standard_normal((dimension, dimension))
        ) / np.sqrt(2.0)
        matrix = (raw + raw.conj().T) / 2.0
    else:
        raise ValueError("block_class must be 'goe' or 'gue'")
    return np.linalg.eigvalsh(matrix)


def build_mixed_spectrum(
    n_sectors: int,
    size_ratio: float = 1.0,
    total_levels: int = DEFAULT_LEVELS,
    block_class: str = "goe",
    seed: int = 0,
) -> np.ndarray:
    """The sorted union of blocks of unequal size.

    The classes alternate GOE and GUE across the blocks of one spectrum, as in the
    manuscript's model: a hidden symmetry does not care which of the two symmetries the
    blocks carry. ``size_ratio = 1`` reproduces the equal-block construction exactly.
    """
    dimensions = block_dimensions(n_sectors, size_ratio, total_levels)
    rng = np.random.default_rng(seed)
    blocks = [
        _random_block(dimension, block_class, rng) for dimension in dimensions
    ]
    return np.sort(np.concatenate(blocks))


def label_grid(
    sectors: tuple[int, ...] = DEFAULT_SECTORS,
    ratios: tuple[float, ...] = DEFAULT_SIZE_RATIOS,
) -> tuple[MixedLabel, ...]:
    """Every admissible ``(m, ratio)`` pair: one sector has the equal label only."""
    labels: list[MixedLabel] = []
    for n_sectors in sectors:
        for size_ratio in ratios:
            if n_sectors == 1 and size_ratio != 1.0:
                continue
            labels.append(MixedLabel(n_sectors, size_ratio))
    return tuple(labels)


def _label_prior(
    labels: tuple[MixedLabel, ...], sectors: tuple[int, ...]
) -> dict[MixedLabel, float]:
    """A prior that is uniform over the sector counts, not over the labels.

    The grid is ragged -- one label at ``m = 1`` and three at every larger count -- so a
    flat prior over labels would hand the counts with more ratios a larger total mass for
    no reason. Each count gets ``1 / len(sectors)``, split evenly inside the count. The
    marginal posterior over ``m`` is therefore the number a uniform count prior would give.
    """
    counts: dict[int, int] = {}
    for label in labels:
        counts[label.n_sectors] = counts.get(label.n_sectors, 0) + 1
    return {
        label: 1.0 / (len(sectors) * counts[label.n_sectors]) for label in labels
    }


def _count_interval(
    counts: dict[int, float], level: float
) -> tuple[int, int]:
    """The shortest contiguous interval of sector counts carrying at least ``level``.

    A local copy of the manuscript's interval routine rather than an import: that routine
    walks a fixed label list that includes the open-ended label and the count five, and
    this model's label set is neither.
    """
    if not 0.0 < level <= 1.0:
        raise ValueError("level must lie in (0, 1]")
    ordered = sorted(counts)
    best: tuple[int, int] | None = None
    for start in range(len(ordered)):
        total = 0.0
        for stop in range(start, len(ordered)):
            total += counts[ordered[stop]]
            if total >= level:
                if best is None or (stop - start) < (best[1] - best[0]):
                    best = (ordered[start], ordered[stop])
                break
    if best is None:  # pragma: no cover - the posterior sums to one
        return ordered[0], ordered[-1]
    return best


@dataclass(frozen=True)
class MixedPosterior:
    """A joint posterior over ``(m, ratio)``, with the marginals it implies."""

    posterior: dict[MixedLabel, float]
    count_interval: tuple[int, int]
    level: float

    @property
    def map_label(self) -> MixedLabel:
        """The most probable label, ties broken towards fewer sectors and a smaller ratio."""
        return max(
            self.posterior,
            key=lambda label: (
                self.posterior[label],
                -label.n_sectors,
                -label.size_ratio,
            ),
        )

    def count_posterior(self) -> dict[int, float]:
        """The marginal over the sector count: the ratio summed out."""
        marginal: dict[int, float] = {}
        for label, probability in self.posterior.items():
            marginal[label.n_sectors] = marginal.get(label.n_sectors, 0.0) + probability
        return dict(sorted(marginal.items()))

    def ratio_posterior(self) -> dict[float, float]:
        """The marginal over the size ratio, at each correct count."""
        return {
            label.size_ratio: sum(
                probability
                for other, probability in self.posterior.items()
                if other.size_ratio == label.size_ratio
            )
            for label in self.posterior
        }

    def at(self, n_sectors: int) -> dict[float, float]:
        """The ratio posterior conditional on a sector count, renormalised."""
        mass = {
            label.size_ratio: probability
            for label, probability in self.posterior.items()
            if label.n_sectors == n_sectors
        }
        total = sum(mass.values())
        if total <= 0.0:
            return {ratio: 0.0 for ratio in mass}
        return {ratio: probability / total for ratio, probability in mass.items()}

    def summary(self) -> str:
        low, high = self.count_interval
        return (
            f"{self.map_label.summary()} (p = {self.posterior[self.map_label]:.2f}, "
            f"{int(self.level * 100)}% CI {low}..{high} sectors)"
        )


def _test_seed(label: MixedLabel, index: int, base: int) -> int:
    """A deterministic seed that differs across labels, so no two labels share a stream."""
    return base + 1_000 * index + 37 * label.n_sectors + int(10.0 * label.size_ratio)


@dataclass(frozen=True)
class MixedCoverage:
    """Measured behaviour for one true ``(m, ratio)`` label.

    Four numbers, because they answer four different questions: whether the count is named
    correctly; whether the ratio is named correctly *given* the true count, which is the
    fair version of the second question; whether the joint label is named correctly; and
    whether the count's interval covers the truth.
    """

    truth: MixedLabel
    posterior_probability: float
    count_correct: float
    ratio_correct: float
    joint_correct: float
    joint_covered: float
    draws: int

    def summary(self) -> str:
        return (
            f"{self.truth.summary():>28}: P(true) = {self.posterior_probability:.2f}, "
            f"count = {self.count_correct:.2f}, ratio | count = "
            f"{self.ratio_correct:.2f}, joint = {self.joint_correct:.2f}, "
            f"interval = {self.joint_covered:.2f}"
        )


@dataclass(frozen=True)
class EqualBlockBias:
    """How the equal-block posterior behaves when the blocks are not equal."""

    truth: MixedLabel
    count_correct: float
    mean_count: float
    draws: int

    def summary(self) -> str:
        return (
            f"{self.truth.summary():>28}: equal-block model names the count "
            f"{self.count_correct:.2f} of the time, mean estimate {self.mean_count:.2f}"
        )


def _log_gaussian(vector: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> float:
    """Log density of a diagonal Gaussian, normalisation included.

    The normalisation is kept because it is not a constant across labels here: a label
    whose spectra scatter more gets a flatter density, and dropping the ``-log sigma`` term
    would silently prefer it. With one feature per order and six orders, the term is a sum
    of six logs.
    """
    z = (vector - mean) / scale
    return float(
        -0.5 * np.sum(z * z)
        - np.sum(np.log(scale))
        - 0.5 * vector.size * np.log(2.0 * np.pi)
    )


def _log_sum_exp(values: list[float]) -> float:
    """Numerically stable ``log(sum(exp(values)))``."""
    top = max(values)
    return top + float(np.log(np.sum(np.exp(np.asarray(values) - top))))


@dataclass(frozen=True)
class MixedSectorModel:
    """A Gaussian naive-Bayes posterior over ``(m, ratio)`` from the six spacing orders.

    The features are the ones the higher-order count model already uses -- the mean
    spacing ratio at orders one to six -- so the two models are compared on identical
    inputs and the only difference is the hypothesis space.

    Each label carries **one Gaussian per random-matrix class**, and the label's density is
    their equal mixture. That is not decoration. The two classes differ in mean ratio by
    about ``0.07``, which is larger than the difference between two and six unresolved
    sectors (``0.53`` against ``0.39``), so a single Gaussian per label straddles both
    classes and a one-sector GOE spectrum lands next to a two-sector GUE one. Modelling the
    class explicitly, and summing it out, is what makes the count comparable across
    classes; the measurement in ``docs/mixed_sectors.md`` shows the difference.

    With ``ratios=(1.0,)`` this is the equal-block model re-implemented, which is what
    makes the comparison a controlled one; a test pins the agreement at ratio one.
    """

    total_levels: int
    orders: tuple[int, ...]
    labels: tuple[MixedLabel, ...]
    means: dict[MixedLabel, dict[str, np.ndarray]]
    scales: dict[MixedLabel, dict[str, np.ndarray]]
    prior: dict[MixedLabel, float]

    @classmethod
    def fit(
        cls,
        total_levels: int = DEFAULT_LEVELS,
        seeds: int = DEFAULT_SEEDS,
        orders: tuple[int, ...] = COUNT_ORDERS,
        sectors: tuple[int, ...] = DEFAULT_SECTORS,
        ratios: tuple[float, ...] = DEFAULT_SIZE_RATIOS,
        block_class: str | None = None,
    ) -> "MixedSectorModel":
        """Simulate every label and fit one Gaussian per label and class.

        ``block_class`` defaults to ``None``, which fits both classes and mixes them. Fixing
        a class is allowed -- the tests use it to keep their cost down -- but a model fitted
        on one class is wrong for the other.
        """
        if seeds < 8:
            raise ValueError("need at least 8 training spectra per label")
        if not orders or any(order < 1 for order in orders):
            raise ValueError("orders must be a non-empty tuple of positive integers")
        labels = label_grid(sectors, ratios)
        classes = ("goe", "gue") if block_class is None else (block_class,)

        samples: dict[MixedLabel, dict[str, list[np.ndarray]]] = {}
        for label in labels:
            samples[label] = {}
            for matrix_class in classes:
                offset = 0 if matrix_class == "goe" else 500
                samples[label][matrix_class] = [
                    spectrum_features(
                        build_mixed_spectrum(
                            label.n_sectors,
                            label.size_ratio,
                            total_levels,
                            matrix_class,
                            seed=100_000
                            + 1_000 * label.n_sectors
                            + int(10.0 * label.size_ratio)
                            + offset
                            + index,
                        ),
                        orders,
                    )
                    for index in range(seeds)
                ]

        means: dict[MixedLabel, dict[str, np.ndarray]] = {}
        scales: dict[MixedLabel, dict[str, np.ndarray]] = {}
        for label, per_class in samples.items():
            means[label] = {}
            scales[label] = {}
            for matrix_class, group in per_class.items():
                stacked = np.stack(group)
                means[label][matrix_class] = np.mean(stacked, axis=0)
                scales[label][matrix_class] = np.maximum(
                    np.std(stacked, axis=0), 1e-3
                )
        return cls(
            total_levels=total_levels,
            orders=orders,
            labels=labels,
            means=means,
            scales=scales,
            prior=_label_prior(labels, sectors),
        )

    def log_likelihood(self, features) -> dict[MixedLabel, float]:
        """Log density of one feature vector under each label, class summed out."""
        vector = np.asarray(features, dtype=float)
        if vector.shape != (len(self.orders),):
            raise ValueError("feature vector does not match the model's orders")
        out: dict[MixedLabel, float] = {}
        for label in self.labels:
            components = list(self.means[label])
            weight = np.log(1.0 / len(components))
            out[label] = _log_sum_exp(
                [
                    float(weight)
                    + _log_gaussian(
                        vector, self.means[label][name], self.scales[label][name]
                    )
                    for name in components
                ]
            )
        return out

    def posterior(self, features, level: float = DEFAULT_LEVEL) -> MixedPosterior:
        """The joint posterior, normalised, with the count's credible interval."""
        log_likelihood = self.log_likelihood(features)
        largest = max(log_likelihood.values())
        weights = {
            label: self.prior[label] * float(np.exp(value - largest))
            for label, value in log_likelihood.items()
        }
        total = sum(weights.values())
        posterior = {label: weight / total for label, weight in weights.items()}
        counts = {
            count: sum(
                probability
                for label, probability in posterior.items()
                if label.n_sectors == count
            )
            for count in {label.n_sectors for label in self.labels}
        }
        count_interval = _count_interval(
            {count: counts[count] for count in sorted(counts)}, level
        )
        return MixedPosterior(
            posterior=posterior,
            count_interval=count_interval,
            level=level,
        )

    def estimate(self, eigenvalues, level: float = DEFAULT_LEVEL) -> MixedPosterior:
        """The posterior for a spectrum, from its eigenvalues alone."""
        return self.posterior(spectrum_features(eigenvalues, self.orders), level=level)

    def coverage(
        self,
        labels: tuple[MixedLabel, ...] | None = None,
        draws: int = 20,
        level: float = DEFAULT_LEVEL,
        seed: int = 200_000,
    ) -> list[MixedCoverage]:
        """Measure the posterior and both rate estimates against the truth.

        ``count_correct`` is the fraction of spectra whose most probable count is the true
        count, which is the question the manuscript asks; ``ratio_correct`` is the same for
        the size ratio; ``joint_covered`` is the fraction whose count interval contains the
        truth, the honest analogue of a frequentist coverage for the pair.
        """
        if draws < 1:
            raise ValueError("need at least one draw")
        tested = labels if labels is not None else self.labels
        rows: list[MixedCoverage] = []
        for truth in tested:
            count_correct = 0
            ratio_correct = 0
            joint_correct = 0
            covered = 0
            probability = 0.0
            for index in range(draws):
                spectrum = build_mixed_spectrum(
                    truth.n_sectors,
                    truth.size_ratio,
                    self.total_levels,
                    "gue" if index % 2 else "goe",
                    seed=_test_seed(truth, index, seed),
                )
                estimate = self.estimate(spectrum, level=level)
                chosen = estimate.map_label
                count_correct += chosen.n_sectors == truth.n_sectors
                conditional = estimate.at(truth.n_sectors)
                ratio_correct += max(conditional, key=conditional.get) == truth.size_ratio
                joint_correct += chosen == truth
                low, high = estimate.count_interval
                covered += low <= truth.n_sectors <= high
                probability += estimate.posterior.get(truth, 0.0)
            rows.append(
                MixedCoverage(
                    truth=truth,
                    posterior_probability=probability / draws,
                    count_correct=count_correct / draws,
                    ratio_correct=ratio_correct / draws,
                    joint_correct=joint_correct / draws,
                    joint_covered=covered / draws,
                    draws=draws,
                )
            )
        return rows


def equal_block_bias(
    model,
    labels: tuple[MixedLabel, ...],
    draws: int = 20,
    seed: int = 300_000,
    total_levels: int = DEFAULT_LEVELS,
) -> list[EqualBlockBias]:
    """The equal-block posterior on unequal spectra: how often, and how far off.

    ``model`` is a :class:`~riemann_framework.desymmetrisation.HigherOrderCountModel` or
    any object with an ``estimate`` returning a :class:`SectorCountEstimate`. The mean
    estimate is reported alongside the accuracy because a bias that is wrong in one
    direction every time is worse than a scatter: ``None`` (the open-ended label) is
    counted as ``7`` in that mean, its stated lower bound.
    """
    rows: list[EqualBlockBias] = []
    for label in labels:
        correct = 0
        total = 0.0
        for index in range(draws):
            spectrum = build_mixed_spectrum(
                label.n_sectors,
                label.size_ratio,
                total_levels,
                "gue" if index % 2 else "goe",
                seed=_test_seed(label, index, seed),
            )
            estimate: SectorCountEstimate = model.estimate(spectrum)
            correct += estimate.map_label == label.n_sectors
            total += 7.0 if estimate.map_label is None else float(estimate.map_label)
        rows.append(
            EqualBlockBias(
                truth=label,
                count_correct=correct / draws,
                mean_count=total / draws,
                draws=draws,
            )
        )
    return rows


@lru_cache(maxsize=2)
def default_mixed_model(total_levels: int = DEFAULT_LEVELS) -> MixedSectorModel:
    """The fitted joint model, cached: fitting costs a few seconds of simulation."""
    return MixedSectorModel.fit(total_levels=total_levels)
