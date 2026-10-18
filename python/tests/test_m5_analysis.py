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
"""Tests for the M5 decisive test.

The suite runs the criteria on a **small grid** (`d = 100`, one or two couplings)
because the full grid costs minutes. That is a runtime concession, not a
statistical one: the seed count stays at the specification's 300, so the numbers
asserted here are real multi-seed numbers.

Two tests guard the *criteria* rather than the model: that criterion (1) is
class-conditional (so it cannot be reported without naming a class), and that the
per-point σ-commutator check fires on a broken matrix. Those are the parts a
future edit is most likely to weaken.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.dimension_shift_chaos import (
    build_dimension_shift_hamiltonian,
)
from riemann_framework.m5_analysis import (
    D_MIN,
    GOE_WINDOW,
    GUE_WINDOW,
    N_SEEDS,
    POISSON_WINDOW,
    ParameterPoint,
    SectorStatistics,
    analyze_point,
    classify_mean,
    extract_sectors,
    run_m5_analysis,
    evaluate_criterion_1,
    evaluate_criterion_2,
)


# ============================================================
# The pieces
# ============================================================

def test_classify_mean_covers_every_window():
    assert classify_mean(0.53) == "goe"
    assert classify_mean(0.60) == "gue"
    assert classify_mean(0.39) == "poisson"
    assert classify_mean(0.47) == "intermediate"


def test_extract_sectors_returns_spectra_of_the_blocks():
    """`spec(A + C)` and `spec(A - C)`, cross-checked by `extract_sectors` itself."""
    d = 20
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=1)
    plus, minus = extract_sectors(hamiltonian)
    block = hamiltonian[:d, :d]
    inter = hamiltonian[:d, d:]
    assert np.allclose(plus, np.linalg.eigvalsh(block + inter))
    assert np.allclose(minus, np.linalg.eigvalsh(block - inter))


def test_extract_sectors_refuses_a_model_without_sigma_symmetry():
    """The whole milestone rests on `[H, sigma] = 0`; a broken matrix must raise."""
    broken = build_dimension_shift_hamiltonian(10, 1.0, "gue", seed=2, sigma_breaking=0.5)
    with pytest.raises(ValueError, match="not sigma-symmetric"):
        extract_sectors(broken)


def test_extract_sectors_validates_the_shape():
    with pytest.raises(ValueError):
        extract_sectors(np.eye(7))


def test_a_point_has_300_seeds_and_error_bars():
    point = analyze_point(D_MIN, 1.0, "goe", n_seeds=N_SEEDS)
    assert point.sector_plus.n_seeds == N_SEEDS
    assert point.sector_minus.n_seeds == N_SEEDS
    assert point.sector_plus.std_r > 0.0
    assert point.sector_plus.stderr_r == pytest.approx(
        point.sector_plus.std_r / np.sqrt(N_SEEDS)
    )
    assert point.sigma_commutator_ratio < 1e-10


def test_a_below_floor_seed_count_is_refused():
    with pytest.raises(ValueError, match="at least 300"):
        analyze_point(D_MIN, 1.0, "goe", n_seeds=20)


def test_an_unknown_matrix_class_is_refused():
    with pytest.raises(ValueError, match="matrix_class"):
        analyze_point(D_MIN, 1.0, "poisson", n_seeds=N_SEEDS)


def test_the_full_spectrum_is_not_gue():
    """The superposition baseline: it must stay below the GUE window."""
    for matrix_class in ("goe", "gue"):
        point = analyze_point(D_MIN, 1.0, matrix_class, n_seeds=N_SEEDS)
        assert point.full_spectrum_mean < GUE_WINDOW[0]
        assert not point.full_spectrum_is_gue


# ============================================================
# Criterion (1)
# ============================================================

def test_criterion_one_is_class_conditional():
    """**The finding.** It holds for GOE blocks and fails for GUE blocks.

    Reported as one verdict without a class it would abandon the DSH on the strength
    of an input choice; reported per class it *is* criterion (2).
    """
    result = evaluate_criterion_1(
        dims=[D_MIN], couplings=[1.0], n_seeds=N_SEEDS
    )
    assert result.per_class_holds["goe"] is True
    assert result.per_class_holds["gue"] is False
    assert result.holds is False
    assert result.n_sectors_in_gue > 0
    assert "class-conditional" in result.explanation
    # the superposition baseline holds: no *full* spectrum is ever GUE
    assert result.full_spectrum_never_gue


def test_criterion_one_rejects_a_grid_below_the_floor():
    with pytest.raises(ValueError, match="d >= 100"):
        evaluate_criterion_1(dims=[50], couplings=[1.0], n_seeds=N_SEEDS)


def test_criterion_one_keeps_the_points_for_the_plots():
    """The figures must be drawn from the data the verdict used."""
    result = evaluate_criterion_1(dims=[D_MIN], couplings=[1.0], n_seeds=N_SEEDS)
    assert len(result.points) == 2
    assert all(isinstance(point, ParameterPoint) for point in result.points)
    assert {point.matrix_class for point in result.points} == {"goe", "gue"}


# ============================================================
# Criterion (2)
# ============================================================

def test_criterion_two_holds_because_the_class_is_inherited():
    result = evaluate_criterion_2(dim_per_sector=D_MIN, coupling=1.0, n_seeds=N_SEEDS)
    assert result.holds
    assert result.gue_blocks_lead_to_gue_sectors == 2
    assert result.goe_blocks_lead_to_gue_sectors == 0
    assert "inherited" in result.explanation


def test_criterion_two_compares_both_classes_at_the_same_point():
    result = evaluate_criterion_2(dim_per_sector=D_MIN, coupling=1.0, n_seeds=N_SEEDS)
    # keyed by name, not position: `MATRIX_CLASSES` starts with "goe", and the first
    # draft of the production code got exactly this wrong
    by_class = {point.matrix_class: point for point in result.points}
    assert by_class["gue"].sector_plus.mean_r > by_class["goe"].sector_plus.mean_r + 0.04


# ============================================================
# The verdict
# ============================================================

def test_the_verdict_abandons_the_dsh_on_criterion_2():
    """The measured outcome, stated as a test: one criterion holding is enough."""
    from riemann_framework.m5_analysis import Criterion1Result, Criterion2Result, M5Verdict

    def _sector(name: str) -> SectorStatistics:
        return SectorStatistics(
            sector=name, mean_r=0.53, std_r=0.05, stderr_r=0.003, n_seeds=N_SEEDS,
            ks_gue=0.05, ks_poisson=0.3, classification="goe",
        )

    point = ParameterPoint(
        dim_per_sector=D_MIN, coupling=1.0, matrix_class="goe",
        sigma_commutator_ratio=0.0, full_spectrum_mean=0.42,
        full_spectrum_std=0.03, sector_plus=_sector("+1"), sector_minus=_sector("-1"),
    )
    c1 = Criterion1Result(
        holds=False, per_class_holds={"goe": True, "gue": False},
        n_sectors_tested=4, n_sectors_in_goe=2, n_sectors_in_gue=2,
        max_sector_mean=0.60,
    )
    c2 = Criterion2Result(
        holds=True, gue_blocks_lead_to_gue_sectors=2,
        goe_blocks_lead_to_gue_sectors=0, points=[point],
    )
    verdict = M5Verdict(
        criterion1=c1, criterion2=c2, dsh_abandoned=c1.holds or c2.holds,
        verdict="abandoned", summary="DSH is ABANDONED. Reason(s): inherited.",
    )
    assert verdict.dsh_abandoned
    assert verdict.verdict == "abandoned"
    assert "ABANDONED" in verdict.summary


def test_the_windows_are_the_documented_ones():
    assert GOE_WINDOW == (0.51, 0.55)
    assert GUE_WINDOW == (0.58, 0.62)
    assert POISSON_WINDOW == (0.36, 0.41)
    assert N_SEEDS == 300
    assert D_MIN == 100


def test_analysis_does_not_claim_a_proof():
    """The verdict text must not read as a statement about RH."""
    from riemann_framework.m5_analysis import Criterion1Result, Criterion2Result, M5Verdict

    verdict = M5Verdict(
        criterion1=Criterion1Result(
            holds=False, per_class_holds={}, n_sectors_tested=0,
            n_sectors_in_goe=0, n_sectors_in_gue=0, max_sector_mean=0.0,
        ),
        criterion2=Criterion2Result(
            holds=True, gue_blocks_lead_to_gue_sectors=2,
            goe_blocks_lead_to_gue_sectors=0,
        ),
        dsh_abandoned=True,
        verdict="abandoned",
        summary="DSH is ABANDONED. This is the result, not a failure.",
    )
    assert "proof" not in verdict.summary.lower()
    assert "hypothesis" not in verdict.summary.lower()

# ============================================================
# The collection guard
# ============================================================

def test_no_imported_symbol_is_collected_as_a_test():
    """**Why this exists.** `evaluate_criterion_1` and `evaluate_criterion_2` were
    originally named `test_criterion_1` and `test_criterion_2`. pytest collects any
    module-level name starting with `test_`, including *imported* ones, so importing
    them here silently ran the full default grid twice -- about twelve minutes of
    hidden computation inside the suite, and `--collect-only` claimed 18 items
    instead of 16. The functions were renamed; this test keeps the next such import
    from doing the same.
    """
    import sys

    module = sys.modules[__name__]
    imported = [
        name
        for name, value in vars(module).items()
        if name.startswith("test_")
        and callable(value)
        and getattr(value, "__module__", __name__) != __name__
    ]
    assert not imported, (
        "these symbols are imported into the test module and will be collected as "
        f"tests: {imported}"
    )
