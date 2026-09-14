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
"""Tests for the idea-vetting pipeline and its arithmetic-coupling probe."""

from pathlib import Path

import numpy as np
import pytest

from riemann_framework.idea_pipeline import (
    Idea,
    InvalidIdeaError,
    load_all_ideas,
    load_idea,
    probe_multiplicative_coupling,
    run_pipeline,
)


# ============================================================
# Idea record / registry
# ============================================================

def test_idea_requires_falsification_criterion():
    with pytest.raises(InvalidIdeaError):
        Idea.from_dict({"id": "x", "hypothesis": "h", "expression": "s"})


def test_idea_from_dict_keeps_unknown_fields_in_extra():
    idea = Idea.from_dict(
        {
            "id": "x",
            "hypothesis": "h",
            "expression": "s",
            "falsification_criterion": "fc",
            "operator": {"p1": 2, "p2": 3, "n_max": 50},
        }
    )
    assert idea.extra == {"operator": {"p1": 2, "p2": 3, "n_max": 50}}


# ============================================================
# Stage D probe (the corrected comparison)
# ============================================================

def test_probe_identity_is_p_independent():
    result = probe_multiplicative_coupling("s")
    assert not result.p_dependent_mismatch
    assert result.spread < 1e-9
    # identity commutes with every Euler factor exactly: zero error per prime
    assert all(err < 1e-12 for err in result.max_relative_error_by_prime.values())


def test_probe_reflection_is_p_dependent():
    result = probe_multiplicative_coupling("1 - s_conj")
    assert result.p_dependent_mismatch
    assert result.spread > 0.1


def test_probe_reports_every_prime():
    result = probe_multiplicative_coupling("1 - s_conj")
    assert set(result.max_relative_error_by_prime) == {2, 3, 5, 7, 11, 13}
    assert all(0.0 <= err <= 2.0 for err in result.max_relative_error_by_prime.values())


def test_probe_does_not_overflow_on_large_valued_map():
    # `s + s**2` makes p^{-w(s0)} huge for raw complex pow; mpmath must handle
    # it. The exact spread is irrelevant -- the call must not raise OverflowError.
    result = probe_multiplicative_coupling("s + s**2")
    assert isinstance(result.spread, float)


# ============================================================
# Pipeline: complex-plane ideas
# ============================================================

def _idea(expression: str, **extra) -> Idea:
    return Idea(
        id="probe",
        hypothesis="test",
        expression=expression,
        falsification_criterion="a statement of what would count against it",
        extra=extra,
    )


def test_dimension_shift_stops_at_stage_b():
    verdict = run_pipeline(_idea("1 - s_conj"))
    assert verdict.stage_reached == "B"
    assert not verdict.passed


def test_nonlinear_p_independent_map_reaches_d():
    # |s|^2 is non-affine (clears B) but its probe mismatch is the same for
    # every prime, so it stops at D without p-dependence.
    verdict = run_pipeline(_idea("s*s_conj"))
    assert verdict.stage_reached == "D"
    assert verdict.passed


def test_nonlinear_p_dependent_map_reaches_dplus():
    # 1/(1+s) is non-affine and its probe mismatch genuinely varies with p.
    verdict = run_pipeline(_idea("1/(1 + s)"))
    assert verdict.stage_reached == "D+"
    assert verdict.passed


def test_unparseable_idea_stops_at_stage_a():
    verdict = run_pipeline(_idea("zeta(s)"))  # 'zeta' is a forbidden token
    assert verdict.stage_reached == "A"
    assert not verdict.passed


# ============================================================
# Pipeline: operator-level ideas (Stage D2)
# ============================================================

def test_operator_level_idea_reaches_d2_and_fails_to_commute():
    idea = _idea("s", operator={"p1": 2, "p2": 3, "n_max": 300})
    verdict = run_pipeline(idea)
    # The prime-swap does not commute with the primon Hamiltonian, so it is
    # falsified at D2 -- but it must reach D2, not be stopped at B for its
    # placeholder expression.
    assert verdict.stage_reached == "D2"
    assert not verdict.passed
    assert verdict.details["operator"]["verdict"] == "does_not_commute"


def test_identity_operator_commutes():
    # A diagonal operator (identity) commutes: sanity control for the D2 path.
    import riemann_framework.operator_symmetry as osym

    result = osym.screen_operator(np.eye(50), 50)
    assert result["commutes"]
    assert result["is_diagonal"]


# ============================================================
# Pipeline: Stage C wiring
# ============================================================

def test_pipeline_reports_stage_c_when_spectrum_supplied():
    rng = np.random.default_rng(0)
    a = rng.standard_normal((100, 100)) + 1j * rng.standard_normal((100, 100))
    m = (a + a.conj().T) / 2
    spectrum = np.linalg.eigvalsh(m)

    verdict = run_pipeline(_idea("1/(1 + s)"), spectrum=spectrum)
    assert verdict.details["statistics"] is not None
    assert "Stage C" in verdict.summary


def test_pipeline_skips_stage_c_without_spectrum():
    verdict = run_pipeline(_idea("1/(1 + s)"))
    assert verdict.details["statistics"] is None
    assert "skipped" in verdict.summary


# ============================================================
# JSON loader
# ============================================================

_IDEAS_DIR = Path(__file__).resolve().parent.parent.parent / "ideas"


def test_load_idea_and_load_all_ideas():
    idea = load_idea(_IDEAS_DIR / "dimension_shift_w.json")
    assert idea.id == "dimension_shift_w"
    assert idea.expression == "1 - s_conj"

    ids = [i.id for i in load_all_ideas(_IDEAS_DIR)]
    assert "dimension_shift_w" in ids
    assert "nonlinear_probe_example" in ids
    assert "dimension_shift_w_lifted_to_primon_gas" in ids


def test_load_idea_rejects_invalid_json(monkeypatch):
    # The sandbox denies process-created file writes, so exercise the decode
    # branch by stubbing the file read instead of writing a fixture.
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: "not json")
    with pytest.raises(InvalidIdeaError):
        load_idea("whatever.json")
