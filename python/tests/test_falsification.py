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
"""Tests for the multi-seed falsification test.

The verdict logic is exercised on *synthetic* points so that every one of the five
labels can be reached deliberately -- a suite that only ran the real grid could
never show that `supported_multi_seed` is reachable at all. Two tests then check
the real machinery: a genuine 300-seed point, and the single-seed artefact the
module exists to replace.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.dimension_shift_chaos import build_dimension_shift_hamiltonian
from riemann_framework.falsification_test import (
    GOE_WINDOW,
    GUE_WINDOW,
    SEEDS_MIN,
    STD_THRESHOLD,
    MultiSeedPoint,
    classify_multi_seed,
    classify_verdict,
    reference_statistics,
    run_multiseed_grid,
    run_point_multiseed,
    run_single,
    size_scaling_study,
)
from riemann_framework.quantum_chaos import riemann_zero_heights
from riemann_framework.spectral_density import (
    compare_spectral_density,
    riemann_von_mangoldt_count,
)


def _point(
    mean_full: float,
    std_full: float = 0.05,
    mean_plus: float = 0.53,
    mean_minus: float = 0.53,
    matrix_class: str = "gue",
    seeds: int = SEEDS_MIN,
) -> MultiSeedPoint:
    """A synthetic point, so each verdict label can be reached on purpose."""
    return MultiSeedPoint(
        dim_per_sector=10,
        coupling=1.0,
        matrix_class=matrix_class,
        seeds=seeds,
        sigma_commutator_ratio=0.0,
        mean_full=mean_full,
        std_full=std_full,
        min_full=mean_full - std_full,
        max_full=mean_full + std_full,
        fraction_full_in_gue_window=0.0,
        mean_plus=mean_plus,
        std_plus=std_full,
        mean_minus=mean_minus,
        std_minus=std_full,
    )


# ============================================================
# Single-number classification (kept from the old module)
# ============================================================

def test_classify_verdict_covers_the_windows():
    assert classify_verdict(0.60) == "gue"
    assert classify_verdict(0.53) == "goe"
    assert classify_verdict(0.39) == "poisson"
    assert classify_verdict(0.47) == "intermediate"


def test_a_single_seed_reports_no_statistics():
    """`run_single` survives for diagnostics; it cannot produce a verdict."""
    result = run_single(10, 1.0, "gue", seed=42)
    assert result.verdict in ("gue", "goe", "poisson", "intermediate")
    assert 0.0 <= result.mean_r_full <= 1.0
    assert not hasattr(result, "std_full")


# ============================================================
# The seed floor
# ============================================================

def test_a_point_below_the_seed_floor_is_refused():
    with pytest.raises(ValueError, match="at least 300"):
        run_point_multiseed(10, 1.0, "gue", seeds=20)


def test_a_verdict_below_the_seed_floor_is_refused():
    with pytest.raises(ValueError, match="at least 300"):
        classify_multi_seed([_point(0.42, seeds=50)])


def test_mixed_seed_counts_are_refused():
    with pytest.raises(ValueError, match="same seed count"):
        classify_multi_seed([_point(0.42), _point(0.42, seeds=301)])


def test_the_grid_refuses_the_degenerate_coupling():
    """`coupling = 0` gives `r = 0` by degeneracy, not a chaos class."""
    with pytest.raises(ValueError, match="degenerate"):
        run_multiseed_grid(coupling_values=(0.0,), seeds=SEEDS_MIN)


# ============================================================
# The five verdict labels, reached deliberately
# ============================================================

def test_supported_multi_seed_is_reachable():
    verdict = classify_multi_seed([_point(0.60, std_full=0.01)])
    assert verdict.verdict == "supported_multi_seed"
    assert verdict.gue_points
    assert "300" in verdict.summary()


def test_a_gue_mean_with_a_large_std_is_not_supported():
    """The `std < 0.02` clause has teeth: the same mean fails with noise."""
    verdict = classify_multi_seed([_point(0.60, std_full=0.05)])
    assert verdict.verdict != "supported_multi_seed"


def test_goe_only():
    verdict = classify_multi_seed([_point(0.53), _point(0.52)])
    assert verdict.verdict == "goe_only"


def test_poisson_only():
    verdict = classify_multi_seed([_point(0.39, mean_plus=0.39, mean_minus=0.39)])
    assert verdict.verdict == "poisson_only"


def test_mixed_needs_a_sector_in_the_gue_window():
    mixed = classify_multi_seed([_point(0.42, mean_plus=0.60, mean_minus=0.60)])
    assert mixed.verdict == "mixed"
    neutral = classify_multi_seed([_point(0.47, mean_plus=0.50, mean_minus=0.50)])
    assert neutral.verdict == "inconclusive"


def test_the_verdict_carries_seeds_and_dispersion():
    verdict = classify_multi_seed([_point(0.42, std_full=0.04)])
    assert verdict.seeds == SEEDS_MIN
    assert verdict.mean_std_full == pytest.approx(0.04)
    assert verdict.std_threshold_reachable is False


def test_per_class_breakdown_is_attached():
    verdict = classify_multi_seed(
        [
            _point(0.42, mean_plus=0.60, mean_minus=0.60, matrix_class="gue"),
            _point(0.42, mean_plus=0.53, mean_minus=0.53, matrix_class="goe"),
        ]
    )
    assert set(verdict.per_class) == {"gue", "goe"}
    assert verdict.per_class["gue"].verdict == "mixed"
    assert verdict.per_class["goe"].verdict == "inconclusive"


# ============================================================
# The real machinery
# ============================================================

def test_a_real_multiseed_point_has_error_bars():
    point = run_point_multiseed(10, 1.0, "gue", seeds=SEEDS_MIN)
    assert point.seeds == SEEDS_MIN
    assert 0.0 < point.std_full < 0.2
    assert point.sem_full == pytest.approx(point.std_full / np.sqrt(SEEDS_MIN))
    assert point.min_full <= point.mean_full <= point.max_full
    assert point.sigma_commutator_ratio < 1e-10
    assert point.mean_full < 0.55, "the full spectrum is a superposition of sectors"


def _legacy_hamiltonian(
    dim_per_sector: int, coupling: float, symmetry_breaking: float, seed: int
) -> np.ndarray:
    """The **pre-correction** model, rebuilt verbatim so the artefact can be measured.

    It cannot be produced by `build_dimension_shift_hamiltonian` any more, and
    that is the point: the old model drew two *independent* real symmetric blocks
    and a non-symmetric coupling, so it never commuted with `sigma`. Keeping it
    here as a local function means the correction can be checked against the thing
    it replaced instead of being taken on trust.
    """
    rng = np.random.default_rng(seed)
    d = dim_per_sector

    def block(block_seed: int) -> np.ndarray:
        local = np.random.default_rng(block_seed)
        raw = local.standard_normal((d, d))
        return (raw + raw.T) / 2.0

    h_b = block(int(rng.integers(0, 2**31)))
    h_f = block(int(rng.integers(0, 2**31)))
    if symmetry_breaking > 0:
        h_f = h_f + symmetry_breaking * np.eye(d)
    coupling_seed = np.random.default_rng(int(rng.integers(0, 2**31)))
    v = coupling * coupling_seed.standard_normal((d, d))

    hamiltonian = np.zeros((2 * d, 2 * d))
    hamiltonian[:d, :d] = h_b
    hamiltonian[d:, d:] = h_f
    hamiltonian[:d, d:] = v
    hamiltonian[d:, :d] = v.T
    return (hamiltonian + hamiltonian.T) / 2.0


def test_the_single_seed_artefact_this_module_replaces():
    """The old 'supported' point: `0.6117` at one seed, `0.523 +- 0.069` at 300.

    Both halves are re-derived here on the *legacy* model, so the correction is
    checked against the object it replaced rather than against a description of it.
    """
    from riemann_framework.statistics import mean_r_ratio

    legacy = _legacy_hamiltonian(10, 0.5, 2.0, seed=42)
    assert mean_r_ratio(np.linalg.eigvalsh(legacy), unfold=True) == pytest.approx(
        0.6117, abs=0.01
    )

    values = [
        mean_r_ratio(
            np.linalg.eigvalsh(_legacy_hamiltonian(10, 0.5, 2.0, seed=seed)),
            unfold=True,
        )
        for seed in range(SEEDS_MIN)
    ]
    assert np.mean(values) == pytest.approx(0.523, abs=0.005)
    assert np.std(values, ddof=1) == pytest.approx(0.069, abs=0.005)
    # a GOE-class model re-enters the "GUE window" from noise, not structure:
    # 14.3% of 300 seeds land there under the legacy unfold=True settings
    # (23.3% with unfold=False, so the choice of unfolding matters for the number)
    fraction = np.mean(
        (np.array(values) >= GUE_WINDOW[0]) & (np.array(values) <= GUE_WINDOW[1])
    )
    assert 0.10 < fraction < 0.20


def test_reference_statistics_are_sampled_with_dispersion():
    references = reference_statistics(size=50, samples=40, unfold=False)
    goe_mean, goe_std = references["goe"]
    gue_mean, gue_std = references["gue"]
    assert goe_mean == pytest.approx(0.53, abs=0.02)
    assert gue_mean == pytest.approx(0.60, abs=0.02)
    assert goe_std > 0.0 and gue_std > 0.0
    assert references["asymptotic_gue"][0] == 0.599


def test_breaking_the_hypothesis_moves_the_statistic_toward_the_gue_window():
    """**The old grid's "support" came from the sigma-violating region.**

    Violating `[H, sigma] = 0` decouples the two blocks, and the superposition
    then lands near `0.52` instead of `0.42` -- so the *violated* model is the one
    that approaches the window the old verdict was looking for. The old best point
    had `symmetry_breaking = 2.0`, i.e. it was found outside the hypothesis.
    """
    from riemann_framework.dimension_shift_chaos import analyze_dimension_shift

    intact = [
        analyze_dimension_shift(20, 1.0, "goe", seed=seed)["mean_r_full"]
        for seed in range(40)
    ]
    broken = [
        analyze_dimension_shift(20, 1.0, "goe", seed=seed, sigma_breaking=5.0)["mean_r_full"]
        for seed in range(40)
    ]
    assert np.mean(intact) < 0.47
    assert np.mean(broken) > np.mean(intact) + 0.08
    assert np.mean(np.array(broken) >= GUE_WINDOW[0]) > 0.0


def test_the_windows_and_threshold_are_the_documented_ones():
    assert GUE_WINDOW == (0.58, 0.62)
    assert GOE_WINDOW == (0.51, 0.55)
    assert STD_THRESHOLD == 0.02


def test_size_scaling_shows_the_std_threshold_is_out_of_reach():
    """`std` shrinks like `1/sqrt(size)`, so `std < 0.02` is not met here."""
    rows = size_scaling_study((20, 100), seeds=12)
    (small_size, _, small_std), (large_size, _, large_std) = rows
    assert small_size < large_size
    assert large_std < small_std
    assert large_std > STD_THRESHOLD


# ============================================================
# Spectral-density diagnostics (unchanged, from the old file)
# ============================================================

def test_riemann_von_mangoldt_count_is_finite_and_increasing():
    """The finite-height RvM reference is a valid cumulative-count baseline."""
    heights = np.array([20.0, 50.0, 100.0, 200.0])
    counts = riemann_von_mangoldt_count(heights)
    assert np.all(np.isfinite(counts))
    assert np.all(np.diff(counts) > 0)


def test_spectral_density_report_compares_model_and_reference():
    """M3 reports finite-range density errors without claiming convergence."""
    model = np.linalg.eigvalsh(
        build_dimension_shift_hamiltonian(
            dim_per_sector=20,
            coupling=1.0,
            seed=42,
        )
    )
    reference = riemann_zero_heights(30)
    report = compare_spectral_density(model, reference, grid_size=10)
    assert report["grid"].shape == (10,)
    assert report["scale"] > 0.0
    assert np.all(np.isfinite(report["model_fraction"]))
    assert np.all(np.isfinite(report["model_vs_rvm_rmse"]))
    assert report["model_vs_reference_rmse"] >= 0.0
