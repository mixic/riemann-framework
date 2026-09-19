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
"""Tests for the certificates behind the two proportion theorems.

These pin the *elementary* components: the constant chain and the two finite
inequalities. They are evidence that the linear algebra and the arithmetic are
right. They are not evidence for either theorem, and nothing here is evidence for
the Riemann hypothesis -- see the module docstring for why the second claim is not
a matter of caution but a consequence of the papers' own sharpness statements.

Each inequality is checked on explicit tight cases and by random search. The
explicit cases matter more: a random search that finds nothing is weak evidence,
whereas a hand-checkable case that must be tight pins the constants in the kernel.
"""

import numpy as np
import pytest

from riemann_framework.proportion_certificates import (
    constant_chain_matches_paper,
    cos_square_kernel,
    montgomery_taylor_constants,
    proposition_2_1_holds,
    proposition_2_1_search,
    random_conjugation_invariant_multiset,
    rank_trace_holds,
    rank_trace_search,
)


# ============================================================
# The constant chain
# ============================================================

def test_indicator_window_gives_the_headline_constants():
    """`2 - 4/3 = 2/3` and `(3 - 4/3)/2 = 5/6`, exactly.

    These are the constants the abstract advertises, so an error here would be an
    error in the headline. Exact rather than approximate: both are rational.
    """
    constants = montgomery_taylor_constants()
    assert constants["simple_indicator"] == pytest.approx(2.0 / 3.0, abs=1e-15)
    assert constants["distinct_indicator"] == pytest.approx(5.0 / 6.0, abs=1e-15)


def test_montgomery_taylor_window_gives_lamzouris_constants():
    """`c_MT^{-1} = 1/2 + (1/sqrt2)cot(1/sqrt2)`, and the two derived figures.

    The same two numbers appear in both papers -- `0.67250...` and `0.83625...` --
    which is not a coincidence: `R(psi_MT)` here equals Lamzouri's `C_0` through
    `C_0 = 2 - c_MT^{-1}`. Asserting the cross-paper identity is what makes this
    a check of the *relationship* rather than of a decimal string.
    """
    constants = montgomery_taylor_constants()
    c_mt_inverse = constants["c_MT_inverse"]
    assert c_mt_inverse == pytest.approx(1.3274992963, abs=1e-9)
    assert 2.0 - c_mt_inverse == pytest.approx(0.6725007037, abs=1e-9)
    assert (3.0 - c_mt_inverse) / 2.0 == pytest.approx(0.8362503518, abs=1e-9)
    assert constants["simple_montgomery_taylor"] > 0.6725
    assert constants["distinct_montgomery_taylor"] > 0.8362


def test_constant_chain_reports_every_check_passing():
    assert all(constant_chain_matches_paper().values())


# ============================================================
# Lamzouri's kernel
# ============================================================

def test_kernel_is_normalised_at_the_origin():
    """`K(0) = eta^2_hat(0) = int eta^2 = 1`, the admissibility condition."""
    assert complex(cos_square_kernel(0.0)) == pytest.approx(1.0 + 0.0j, abs=1e-14)


@pytest.mark.parametrize("lam", [0.5, 1.0, 2.5])
def test_kernel_scales_as_K_lam_of_xi_equals_K_1_of_lam_xi(lam):
    """The dilation law, which is what lets one `eta` cover every bandwidth.

    `eta_lam(u) = lam^{-1/2} eta_1(u/lam)`, so its squared Fourier transform is
    `K_1(lam xi)`. Checked at complex arguments too, since Proposition 2.1
    evaluates `K` off the real axis.
    """
    for zeta in (0.3, 1.7, 0.5 + 0.3j, -2.0 + 1.1j):
        assert complex(cos_square_kernel(zeta, lam)) == pytest.approx(
            complex(cos_square_kernel(lam * zeta, 1.0)), rel=1e-12, abs=1e-14
        )


def test_kernel_rejects_a_nonpositive_bandwidth():
    with pytest.raises(ValueError, match="lam"):
        cos_square_kernel(0.0, 0.0)


# ============================================================
# Proposition 2.1
# ============================================================

def test_a_single_simple_real_point_is_the_tight_case():
    """`Z = {x}`: both inequalities are equalities, margin exactly zero.

    This is the sharpness the papers refer to, seen on the smallest possible
    input: `s = 1`, `2N - K(0)^2 = 2 - 1 = 1`. If the kernel normalisation or the
    quadratic form were off by anything, this would not come out tight.
    """
    report = proposition_2_1_holds(np.array([1.5]))
    assert report["size"] == 1 and report["simple_real"] == 1
    assert report["quadratic_form"] == pytest.approx(1.0, abs=1e-12)
    assert report["margin_2_4"] == pytest.approx(0.0, abs=1e-12)
    assert report["margin_2_5"] == pytest.approx(0.0, abs=1e-12)


def test_a_pure_conjugate_pair_has_no_simple_real_points_and_still_holds():
    """`Z = {z, conj z}` off the axis: `s = 0`, so the bound must come from `K^2`.

    `|K(2i Im z)| >= 1` is what makes this work; it is the reason the kernel is
    evaluated off the real axis at all.
    """
    report = proposition_2_1_holds(np.array([0.3 + 0.4j, 0.3 - 0.4j]))
    assert report["simple_real"] == 0
    assert report["quadratic_form"] > 1.0
    assert report["holds_2_4"] and report["holds_2_5"]


def test_a_repeated_real_point_does_not_count_as_simple():
    report = proposition_2_1_holds(np.array([2.0, 2.0]))
    assert report["size"] == 2 and report["distinct"] == 1
    assert report["simple_real"] == 0
    assert report["holds_2_4"]


def test_proposition_rejects_a_multiset_that_is_not_conjugation_invariant():
    """The hypothesis is load-bearing, so violating it must raise rather than
    silently return a bound that was never derived."""
    with pytest.raises(ValueError, match="conjugation"):
        proposition_2_1_holds(np.array([0.5 + 0.2j]))


def test_proposition_rejects_an_empty_multiset():
    with pytest.raises(ValueError, match="non-empty"):
        proposition_2_1_holds(np.array([], dtype=complex))


def test_proposition_search_finds_no_violation():
    """A random search over conjugation-invariant multisets, both inequalities.

    Weak evidence on its own -- it can only fail to find a counterexample -- which
    is why the explicit tight cases above carry the weight.
    """
    result = proposition_2_1_search(trials=1500, seed=0)
    assert result["checked"] == 1500
    assert result["violations_2_4"] == 0
    assert result["violations_2_5"] == 0
    assert result["tightest_margin_2_4"] >= -1e-9


def test_random_multisets_really_are_conjugation_invariant():
    """The generator must satisfy the hypothesis, or the search tests nothing."""
    rng = np.random.default_rng(3)
    for _ in range(50):
        values = random_conjugation_invariant_multiset(rng)
        assert np.allclose(np.sort_complex(values), np.sort_complex(values.conj()))


# ============================================================
# Lemma 3.2, the rank-trace inequality
# ============================================================

def test_rank_trace_on_a_rank_one_positive_matrix():
    """The scalar kernel of the inequality: `m^2 >= 2m - 1` at `m = 1`.

    With `Q = 0` and `b = 0`, `rank P1 = 1` and the right-hand side is
    `2 - 1 = 1`, so the inequality is an equality. This is the `m = 1` case of the
    scalar inequality the paper says (1.1) is the matrix form of.
    """
    p1 = np.array([[1.0]])
    q = np.array([[0.0]])
    report = rank_trace_holds(p1, q, b=0)
    assert report.rank == 1
    assert report.right_hand_side == pytest.approx(1.0, abs=1e-12)
    assert report.margin == pytest.approx(0.0, abs=1e-12)
    assert report.holds


def test_rank_trace_accepts_a_slack_bound():
    """`b` may exceed `n_+(Q)`; a larger `b` only weakens the statement."""
    rng = np.random.default_rng(1)
    a = rng.normal(size=(2, 4)) + 1j * rng.normal(size=(2, 4))
    p1 = a.conj().T @ a
    bmat = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
    q = (bmat + bmat.conj().T) / 2.0
    positive = int(np.count_nonzero(np.linalg.eigvalsh(q) > 1e-9))
    assert rank_trace_holds(p1, q, positive).holds
    assert rank_trace_holds(p1, q, positive + 5).holds


def test_rank_trace_rejects_inputs_that_break_its_hypotheses():
    """Each hypothesis is checked, so the inequality is never applied outside its
    domain -- a test that passed on inadmissible input would be worthless."""
    p1 = np.array([[1.0, 0.0], [0.0, 1.0]])
    with pytest.raises(ValueError, match="positive semidefinite"):
        rank_trace_holds(np.array([[1.0, 0.0], [0.0, -1.0]]), np.zeros((2, 2)), b=0)
    with pytest.raises(ValueError, match="Hermitian"):
        rank_trace_holds(p1, np.array([[0.0, 1.0], [0.0, 0.0]]), b=0)
    with pytest.raises(ValueError, match="same shape"):
        rank_trace_holds(p1, np.zeros((3, 3)), b=0)
    # n_+(Q) = 2 with b = 1 violates the hypothesis, and must be refused rather
    # than reported: the inequality is not claimed to hold there.
    with pytest.raises(ValueError, match="exceeds b"):
        rank_trace_holds(p1, np.diag([1.0, 1.0]), b=1)


def test_rank_trace_search_finds_no_violation():
    result = rank_trace_search(trials=8000, seed=0)
    assert result["checked"] == 8000
    assert result["violations"] == 0
    assert result["tightest_margin"] >= -1e-8


# ============================================================
# The standing position
# ============================================================

def test_no_function_here_claims_a_proof_of_rh():
    """A guard on the module's public surface, in the spirit of the repository's
    other anti-goals.

    Nothing in this module may return a verdict on the Riemann hypothesis. The
    explicit denylist is crude but it is the cheap mechanical half of the
    documented position that RH is open; the enforced half is in
    `tests/test_formal_proof.py`.
    """
    import riemann_framework.proportion_certificates as module

    forbidden = ("prove", "proven", "is_true", "riemann_hypothesis_holds")
    public = [name for name in dir(module) if not name.startswith("_")]
    offenders = [
        name for name in public
        if any(word in name.lower() for word in forbidden)
    ]
    assert offenders == [], f"names implying a proof verdict: {offenders}"
