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
"""Where do spacing statistics stop carrying the sector count?

Three statistics are computed on *identical* spectra:

* the mean adjacent-gap ratio ``<r>`` (the manuscript's statistic, order one,
  summarised by its mean);
* the higher-order spacing ratio ``r^(k)`` (the statistic of Tekur, Bhosale and
  Santhanam, used here as a full histogram rather than a mean);
* the Dyson-Mehta number variance ``Sigma^2(L)`` for ``L = 1 .. L_max``.

A fixed 1-nearest-neighbour classifier is trained on a reference set and tested on an
independent set. The *boundary* of a statistic is the largest ``m`` at which its per-class
accuracy reaches a threshold (0.8 by default). The classifier is the same for all three
statistics, so only the feature vector differs, which is the point of the comparison.

The spectra are synthetic Gaussian blocks: ``m`` independent blocks of the same size and
class. The Riemann zeros are not used, and no claim about them is made.
"""

from __future__ import annotations

import numpy as np

#: Sector counts the map is measured at. Two and three are the interesting cells: the
#: manuscript's adjacent-gap statistic is decisive at one and chance from two upward.
DEFAULT_SECTORS: tuple[int, ...] = (1, 2, 3, 4, 6)

#: Statistics the map compares, as feature-vector recipes.
DEFAULT_STATISTICS: tuple[str, ...] = (
    "mean_r",
    "hosr_1",
    "hosr_3",
    "hosr_6",
    "hosr_family",
    "number_variance",
)

#: Orders of the higher-order family, as used by ``hosr_family``.
ORDERS: tuple[int, ...] = (1, 2, 3, 4, 5, 6)

#: Accuracy a statistic must reach for its boundary to include a sector count.
DEFAULT_THRESHOLD = 0.8


def build_spectrum(
    n_sectors: int,
    total_levels: int = 240,
    block_class: str = "goe",
    seed: int = 0,
) -> np.ndarray:
    """The union of ``n_sectors`` independent blocks, sorted.

    The **total** number of levels is held fixed and the block size is
    ``total_levels // n_sectors``, as in the manuscript's generative model. Holding the
    total fixed is what makes the comparison fair: every statistic gets the same number of
    ratios whatever the sector count, so a classifier cannot read ``m`` off the size of the
    sample instead of off the statistic.
    """
    if n_sectors < 1:
        raise ValueError("need at least one sector")
    levels_per_block = max(4, total_levels // n_sectors)
    rng = np.random.default_rng(seed)
    blocks = []
    for _ in range(n_sectors):
        if block_class == "goe":
            raw = rng.standard_normal((levels_per_block, levels_per_block))
            matrix = (raw + raw.T) / 2.0
            blocks.append(np.linalg.eigvalsh(matrix))
        elif block_class == "gue":
            raw = (
                rng.standard_normal((levels_per_block, levels_per_block))
                + 1j * rng.standard_normal((levels_per_block, levels_per_block))
            ) / np.sqrt(2.0)
            matrix = (raw + raw.conj().T) / 2.0
            blocks.append(np.linalg.eigvalsh(matrix))
        else:
            raise ValueError("block_class must be 'goe' or 'gue'")
    return np.sort(np.concatenate(blocks))


def poisson_spectrum(n_levels: int = 240, seed: int = 0) -> np.ndarray:
    """A Poisson spectrum: exponential spacings, so ``Sigma^2(L) = L`` in theory."""
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.exponential(1.0, n_levels))


def unfold(eigenvalues, degree: int = 5) -> np.ndarray:
    """Unfold to mean spacing 1 with a polynomial fit to the staircase.

    A degree of five is the default in :func:`riemann_framework.statistics.unfold_spectrum`
    for these sizes; the polynomial absorbs the smooth part of the level density and leaves
    the fluctuations.
    """
    levels = np.sort(np.asarray(eigenvalues, dtype=float))
    if levels.size < 3:
        raise ValueError("need at least three levels to unfold")
    fit_degree = min(degree, max(2, levels.size // 10))
    staircase = np.arange(1, levels.size + 1, dtype=float)
    coefficients = np.polyfit(levels, staircase, fit_degree)
    unfolded = np.polyval(coefficients, levels)
    return unfolded - unfolded[0]


def adjacent_gap_ratio(eigenvalues) -> np.ndarray:
    """``r_i = min(s_i, s_(i+1)) / max(s_i, s_(i+1))`` for consecutive spacings."""
    spacings = np.diff(np.sort(np.asarray(eigenvalues, dtype=float)))
    spacings = spacings[spacings > 1e-14]
    if spacings.size < 2:
        return np.array([])
    return np.minimum(spacings[:-1], spacings[1:]) / np.maximum(
        spacings[:-1], spacings[1:]
    )


def higher_order_ratio(eigenvalues, order: int) -> np.ndarray:
    """The order-``k`` spacing ratio, folded to ``(0, 1]``.

    ``s_i^(k) = E_(i+k) - E_i`` and
    ``r_i^(k) = min(s_i^(k), s_(i+1)^(k)) / max(...)``, which is the definition of Tekur,
    Bhosale and Santhanam (Phys. Rev. B **98**, 104305 (2018)). For ``k = 1`` it is exactly
    the adjacent-gap ratio, and a test pins that.
    """
    if order < 1:
        raise ValueError("order must be at least one")
    levels = np.sort(np.asarray(eigenvalues, dtype=float))
    if levels.size <= order + 1:
        return np.array([])
    block = levels[order:] - levels[:-order]
    if block.size < 2:
        return np.array([])
    return np.minimum(block[:-1], block[1:]) / np.maximum(block[:-1], block[1:])


def number_variance(
    eigenvalues,
    L_max: int = 20,
    n_windows: int = 200,
    seed: int = 0,
) -> np.ndarray:
    """``Sigma^2(L)`` for ``L = 1 .. L_max`` on the unfolded spectrum.

    ``n_windows`` random windows of unfolded length ``L`` are drawn and the variance of the
    counts is taken. A Poisson spectrum gives ``Sigma^2(L) = L`` in theory; the polynomial
    unfolding used here absorbs part of that variance, so the measured value is lower (see
    Section 5.3 of the manuscript for the same caveat).
    """
    if L_max < 1:
        raise ValueError("L_max must be at least one")
    if n_windows < 2:
        raise ValueError("need at least two windows")
    unfolded = unfold(eigenvalues)
    low, high = float(unfolded[0]), float(unfolded[-1])
    rng = np.random.default_rng(seed)
    values = np.empty(L_max, dtype=float)
    for index in range(L_max):
        length = index + 1
        if high - low <= length + 1.0:
            values[index] = float("nan")
            continue
        starts = rng.uniform(low, high - length, n_windows)
        counts = np.searchsorted(unfolded, starts + length, side="left") - np.searchsorted(
            unfolded, starts, side="left"
        )
        values[index] = float(np.var(counts))
    return values


#: Bins in the ratio histogram. Thirty is fine for a 60-level block: two ratios per level.
HISTOGRAM_BINS = 30


def _mean_ratio(eigenvalues, order: int) -> float:
    """The mean of the order-``order`` ratio, or NaN when there are too few levels."""
    ratios = higher_order_ratio(eigenvalues, order)
    return float(np.mean(ratios)) if ratios.size else float("nan")


def feature_vector(eigenvalues, statistic: str) -> np.ndarray:
    """A fixed-length feature vector, one recipe per statistic.

    * ``mean_r``: the mean adjacent-gap ratio, one number, which is the manuscript's
      statistic (and identical to ``hosr_1``, a test pins that);
    * ``hosr_k``: the mean ratio at order ``k`` alone, one number;
    * ``hosr_family``: the six means, orders one to six, which is the higher-order family
      with all of its information;
    * ``number_variance``: ``Sigma^2(1 .. 20)``.

    The mean per order is used rather than the full histogram of each order: at 240 levels
    a 30-bin histogram is dominated by counting noise, and the measured boundary with the
    histogram is *worse* than with the mean (see ``docs/boundary_map.md``). The mean is
    also what the higher-order literature reports as the summary of the distribution.
    """
    if statistic == "mean_r":
        return np.array([_mean_ratio(eigenvalues, 1)])

    if statistic.startswith("hosr_"):
        tail = statistic.split("_")[1]
        if tail == "family":
            return np.array([_mean_ratio(eigenvalues, order) for order in ORDERS])
        return np.array([_mean_ratio(eigenvalues, int(tail))])

    if statistic == "number_variance":
        return number_variance(eigenvalues)

    raise ValueError(f"unknown statistic: {statistic!r}")


def ratio_histogram(eigenvalues, order: int = 1) -> np.ndarray:
    """The histogram of the order-``order`` ratio, kept for the comparison in the note.

    It is not part of :data:`DEFAULT_STATISTICS` because it measures worse, but it is the
    feature the task specification first proposed, so the comparison is kept reproducible.
    """
    ratios = higher_order_ratio(eigenvalues, order)
    if ratios.size == 0:
        return np.zeros(HISTOGRAM_BINS)
    histogram, _ = np.histogram(
        ratios, bins=HISTOGRAM_BINS, range=(0.0, 1.0), density=True
    )
    return histogram


def per_class_accuracy(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict[int, float]:
    """Per-class accuracy of a 1-nearest-neighbour classifier.

    The feature vectors are z-scored on the training set and the same mean and scale are
    applied to the test set, so no statistic gets an advantage from its units. Per-class
    accuracy is reported rather than the overall rate, because the sector counts are
    unbalanced (1, 2, 3, 4, 6) and a majority vote would flatter the coarse classes.
    """
    train = np.asarray(X_train, dtype=float)
    test = np.asarray(X_test, dtype=float)
    centre = np.mean(train, axis=0, keepdims=True)
    scale = np.std(train, axis=0, keepdims=True)
    scale[scale < 1e-12] = 1.0
    train = (train - centre) / scale
    test = (test - centre) / scale

    labels = np.unique(y_train)
    correct = {int(label): 0 for label in labels}
    total = {int(label): 0 for label in labels}
    for vector, truth in zip(test, y_test):
        distances = np.linalg.norm(train - vector, axis=1)
        predicted = int(y_train[int(np.argmin(distances))])
        total[int(truth)] += 1
        if predicted == int(truth):
            correct[int(truth)] += 1
    return {
        label: correct[label] / total[label] if total[label] else 0.0 for label in correct
    }


def boundary_of(per_class: dict[int, float], threshold: float = DEFAULT_THRESHOLD) -> int:
    """The largest sector count whose per-class accuracy reaches ``threshold``.

    Zero means no count reaches it. The boundary of the mean ratio is one, which is the
    manuscript's claim in one number.
    """
    reached = [label for label, accuracy in per_class.items() if accuracy >= threshold]
    return max(reached) if reached else 0


def build_datasets(
    sectors: tuple[int, ...] = DEFAULT_SECTORS,
    total_levels: int = 240,
    n_train: int = 60,
    n_test: int = 60,
    block_class: str = "goe",
) -> tuple[dict[int, list[np.ndarray]], dict[int, list[np.ndarray]]]:
    """The training and test spectra, shared by every statistic.

    The same seed sequence is used for all three statistics, which is the comparison's
    precondition: a difference in accuracy must come from the statistic, not from the data.
    """
    train = {
        count: [
            build_spectrum(count, total_levels, block_class, seed=1_000 * count + index)
            for index in range(n_train)
        ]
        for count in sectors
    }
    test = {
        count: [
            build_spectrum(count, total_levels, block_class, seed=10_000 * count + index)
            for index in range(n_test)
        ]
        for count in sectors
    }
    return train, test


def measure(
    statistics: tuple[str, ...] = DEFAULT_STATISTICS,
    sectors: tuple[int, ...] = DEFAULT_SECTORS,
    total_levels: int = 240,
    n_train: int = 60,
    n_test: int = 60,
    block_class: str = "goe",
) -> dict[str, dict[int, float]]:
    """Per-class accuracy of every statistic, at every sector count."""
    train, test = build_datasets(sectors, total_levels, n_train, n_test, block_class)
    results: dict[str, dict[int, float]] = {}
    for statistic in statistics:
        X_train = np.array([feature_vector(s, statistic) for m in sectors for s in train[m]])
        y_train = np.array([m for m in sectors for _ in range(n_train)])
        X_test = np.array([feature_vector(s, statistic) for m in sectors for s in test[m]])
        y_test = np.array([m for m in sectors for _ in range(n_test)])
        results[statistic] = per_class_accuracy(X_train, y_train, X_test, y_test)
    return results


def pairwise_accuracy(
    statistic: str,
    first: int,
    second: int,
    total_levels: int = 240,
    n_train: int = 80,
    n_test: int = 80,
    block_class: str = "goe",
) -> float:
    """Balanced accuracy at telling one sector count from another, two classes only.

    This is the question the manuscript's Section 8 quotes for the higher-order family, and
    it is easier than naming the count: a statistic can separate three sectors from six
    while still failing to place a spectrum in ``{1, 2, 3, 4, 6}``. Reporting both is the
    point of the map.
    """
    train, test = build_datasets(
        (first, second), total_levels, n_train, n_test, block_class
    )
    X_train = np.array([feature_vector(s, statistic) for m in (first, second) for s in train[m]])
    y_train = np.array([m for m in (first, second) for _ in range(n_train)])
    X_test = np.array([feature_vector(s, statistic) for m in (first, second) for s in test[m]])
    y_test = np.array([m for m in (first, second) for _ in range(n_test)])
    per_class = per_class_accuracy(X_train, y_train, X_test, y_test)
    return (per_class[first] + per_class[second]) / 2.0
