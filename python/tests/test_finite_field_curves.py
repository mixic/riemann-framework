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
"""Tests for the Riemann hypothesis over finite fields.

This is the one module in the repository where a test can *prove* the Riemann
hypothesis -- for one curve over one finite field, by exact integer arithmetic.
The tests are written to keep that proportion: the certificates are exact, and
what they do not establish is asserted explicitly rather than left to the reader.

The two findings worth pinning are the ones that came out of measuring rather
than reasoning:

* sweeping all 729 coefficient tuples over `F_3` gave 30 uncertified curves,
  which would be a counterexample to a theorem; all 30 are singular or of degree
  4, and `is_smooth_genus2` is what separates them;
* `GF(3^2)` failing to construct is what exposed an inverted irreducibility test.
"""

import pytest

from riemann_framework.finite_field_curves import (
    NO_TRANSFER_NOTE,
    THEOREM_VS_INSTANCE,
    EllipticCertificate,
    FiniteField,
    alpha_pair,
    certify_elliptic,
    certify_genus2,
    count_from_alphas,
    count_projective_points,
    elliptic_rhs,
    hyperelliptic_rhs,
    is_smooth_genus2,
    point_counts,
    quadratic_roots_within_bound,
    sweep_elliptic,
    weil_bound_rows,
)


# ============================================================
# Finite fields
# ============================================================

@pytest.mark.parametrize("p,n", [(2, 1), (3, 1), (2, 2), (3, 2), (5, 2), (2, 3), (3, 3), (7, 3)])
def test_every_nonzero_element_has_order_dividing_q_minus_one(p, n):
    """`a^(q-1) = 1` for every `a != 0`.

    This is an independent check that the modulus found by trial division really
    is irreducible: the identity fails in a ring with zero divisors. It is the
    check that would have caught the inverted irreducibility test immediately.
    """
    field = FiniteField(p, n)
    assert all(field.pow(a, field.size - 1) == 1 for a in range(1, field.size))


@pytest.mark.parametrize("p,n", [(3, 2), (2, 3), (5, 2)])
def test_field_axioms_hold(p, n):
    """Commutativity, distributivity, and inverses, on a sample."""
    field = FiniteField(p, n)
    sample = list(range(min(field.size, 12)))
    for a in sample:
        assert field.add(a, 0) == a
        assert field.mul(a, 1) == a
        for b in sample:
            assert field.mul(a, b) == field.mul(b, a)
            assert field.add(a, b) == field.add(b, a)
            assert field.sub(field.add(a, b), b) == a
            for c in sample:
                assert field.mul(a, field.add(b, c)) == field.add(
                    field.mul(a, b), field.mul(a, c)
                )


def test_inverses_exist_for_every_nonzero_element():
    field = FiniteField(3, 2)
    for a in range(1, field.size):
        inverse = field.pow(a, field.size - 2)
        assert field.mul(a, inverse) == 1


def test_frobenius_is_an_automorphism_and_its_orbits_partition():
    """`x -> x^p` fixes `F_p` and its orbits are the conjugacy classes."""
    field = FiniteField(3, 2)
    for a in range(field.size):
        for b in range(field.size):
            assert field.frobenius(field.add(a, b)) == field.add(
                field.frobenius(a), field.frobenius(b)
            )
            assert field.frobenius(field.mul(a, b)) == field.mul(
                field.frobenius(a), field.frobenius(b)
            )
    # Every element of the prime field is fixed.
    assert all(field.frobenius(a) == a for a in range(field.p))
    orbits = field.frobenius_orbits()
    flat = sorted(x for orbit in orbits for x in orbit)
    assert flat == list(range(field.size))


def test_size_cap_is_enforced():
    """`GF(13^4)` is 28561 elements and is refused rather than run slowly."""
    with pytest.raises(ValueError, match="brute-force cap"):
        FiniteField(13, 4)


def test_composite_modulus_is_refused():
    with pytest.raises(ValueError, match="not prime"):
        FiniteField(9, 1)


# ============================================================
# Point counting and the exact Hasse certificate
# ============================================================

def test_point_count_by_hand_over_f5():
    """`y^2 = x^3 + x + 1` over `F_5` has `N_1 = 9`, counted by hand.

    x = 0: rhs = 1, squares {0,1,4} -> two y. x = 1: 3, not a square -> none.
    x = 2: 11 = 1 -> two. x = 3: 31 = 1 -> two. x = 4: 69 = 4 -> two.
    That is 8 affine points plus the point at infinity.
    """
    assert count_projective_points(elliptic_rhs(1, 1), FiniteField(5)) == 9


def test_trace_and_hasse_are_exact_integers():
    certificate = certify_elliptic(1, 1, 5)
    assert certificate.point_count == 9
    assert certificate.trace == 5 + 1 - 9
    assert certificate.trace == -3
    assert certificate.hasse  # (-3)^2 = 9 <= 20
    assert "holds" in certificate.summary()


def test_hasse_test_can_fail():
    """A certificate that could never fail would prove nothing.

    `a^2 <= 4p` is a real test, so here is an input that violates it: a trace
    outside the Hasse interval, constructed directly rather than found, since no
    genuine curve has one.
    """
    assert not EllipticCertificate(a=0, b=1, p=5, point_count=0, trace=5, hasse=5 * 5 <= 20).hasse
    assert not quadratic_roots_within_bound(p=10, r=0, q=1)  # roots 0 and 10, |w| <= 2


def test_sweep_finds_no_violation_of_hasse():
    """Every elliptic curve over `F_p` for small `p`, certified exactly."""
    for p in (5, 7, 11, 13):
        certificates = sweep_elliptic(p)
        assert certificates
        assert all(c.hasse for c in certificates), f"p = {p}"


def test_sweep_excludes_singular_curves():
    """`4a^3 + 27b^2 = 0` gives a singular curve, which has no genus 1."""
    certificates = sweep_elliptic(5)
    assert all(c.discriminant_nonzero for c in certificates)
    assert len(certificates) < 25


# ============================================================
# The alphas, the recurrence, and the Weil bound
# ============================================================

def test_alpha_pair_has_modulus_sqrt_q():
    """`|alpha| = sqrt(q)` exactly when the Hasse test holds."""
    certificate = certify_elliptic(0, 1, 13)
    first, second = alpha_pair(certificate.trace, 13)
    assert abs(first) == pytest.approx(13**0.5, rel=1e-15)
    assert abs(second) == pytest.approx(13**0.5, rel=1e-15)
    assert (first * second).real == pytest.approx(13.0, rel=1e-12)
    assert (first + second).real == pytest.approx(certificate.trace, rel=1e-12)


def test_point_counts_follow_the_recurrence_from_the_alphas():
    """`N_m = q^m + 1 - sum alpha_i^m` reproduces brute-force counts.

    Checking this tests the whole structure, not just the bound: it says the
    counts really are governed by the `2g` numbers `alpha_i`.
    """
    trace = certify_elliptic(0, 1, 13).trace
    alphas = alpha_pair(trace, 13)
    brute = point_counts(elliptic_rhs(0, 1), 13, 3)
    from_alphas = [count_from_alphas(alphas, 13, m) for m in range(1, 4)]
    assert brute == [12, 192, 2268]
    for computed, expected in zip(from_alphas, brute):
        assert computed == pytest.approx(expected, abs=1e-6)


def test_weil_bound_holds_and_is_sometimes_attained():
    """`|N_m - q^m - 1| <= 2g sqrt(q^m)`, and the bound is sharp.

    For `y^2 = x^3 + 1` over `F_5` the deviation at `m = 2` is `+10` against a
    bound of exactly 10, and at `m = 4` it is `-50` against exactly 50. A bound
    that is never attained is not known to be sharp, so the attained cases are
    pinned -- and note the **signs differ**: the bound is attained from both
    sides, which a check on magnitudes alone would not show.
    """
    rows = weil_bound_rows(elliptic_rhs(0, 1), 5, 1, 4)
    assert all(row.within for row in rows)
    assert rows[1].deviation == 10 and rows[1].bound == pytest.approx(10.0)
    assert rows[3].deviation == -50 and rows[3].bound == pytest.approx(50.0)
    assert abs(rows[3].deviation) == pytest.approx(rows[3].bound)


# ============================================================
# Genus 2, and the hypotheses that matter
# ============================================================

def test_smoothness_predicate_rejects_what_is_not_genus_2():
    """Degree 4 and repeated roots both put a curve outside the theorem.

    `x^5 + 1` over `F_3` **is** squarefree -- `(x+1)^5` has coefficients
    `1, 2, 1, 1, 2, 1` mod 3, not `1, 0, 0, 0, 0, 1` -- and a first draft of this
    test asserted otherwise. The two cases below really are non-squarefree:
    `x^4 (x+1)` has a repeated root at 0, and `x (x^2+1)^2` has a repeated
    conjugate pair.
    """
    assert is_smooth_genus2([2, 1, 0, 1, 0, 1], 3)          # deg 5, squarefree
    assert is_smooth_genus2([1, 0, 0, 0, 0, 1], 3)          # x^5 + 1, squarefree
    assert not is_smooth_genus2([1, 1, 0, 1, 0, 0], 3)      # deg 4: two points at infinity
    assert not is_smooth_genus2([0, 0, 0, 0, 1, 1], 3)      # x^4 (x+1)
    assert not is_smooth_genus2([0, 1, 0, 2, 0, 1], 3)      # x (x^2+1)^2


def test_genus2_certificates_for_smooth_curves():
    certificate = certify_genus2([2, 1, 0, 1, 0, 1], 3)
    assert certificate.certified
    assert certificate.roots is not None
    limit = 2 * 3**0.5
    assert all(abs(r) <= limit for r in certificate.roots)
    assert "holds" in certificate.summary()


def test_no_smooth_genus2_curve_fails_over_f3():
    """All 324 smooth genus-2 curves over `F_3`, every one certified.

    The first sweep was over *all* 729 tuples and reported 30 uncertified, which
    would be a counterexample to a theorem. All 30 turn out to be singular or of
    degree 4, so the count among genuine curves is zero -- and that zero is the
    content of this test.
    """
    smooth = 0
    for c5 in range(3):
        for c4 in range(3):
            for c3 in range(3):
                for c2 in range(3):
                    for c1 in range(3):
                        for c0 in range(3):
                            coefficients = [c0, c1, c2, c3, c4, c5]
                            if not is_smooth_genus2(coefficients, 3):
                                continue
                            smooth += 1
                            assert certify_genus2(coefficients, 3).certified, coefficients
    assert smooth == 324


def test_quadratic_bound_is_exact_in_both_directions():
    """The integer test for "both roots in `[-2 sqrt(q), 2 sqrt(q)]`"."""
    # w^2 - 3w - 1 over q = 3: roots (3 +- sqrt(13))/2, both within 2 sqrt 3.
    assert quadratic_roots_within_bound(3, -1, 3)
    # w^2 - 100w + 0 over q = 3: roots 0 and 100, far outside.
    assert not quadratic_roots_within_bound(100, 0, 3)
    # Negative discriminant: no real roots at all.
    assert not quadratic_roots_within_bound(0, 10, 3)


# ============================================================
# What these certificates do and do not establish
# ============================================================

def test_the_instance_versus_theorem_caveat_is_stated():
    assert "ONE curve" in THEOREM_VS_INSTANCE
    assert "not a proof of Weil's theorem" in THEOREM_VS_INSTANCE
    assert "universal" in THEOREM_VS_INSTANCE


def test_the_no_transfer_caveat_is_stated():
    """The function-field success does not carry over to Q."""
    assert "etale cohomology" in NO_TRANSFER_NOTE
    assert "No analogue" in NO_TRANSFER_NOTE


def test_no_function_returns_a_verdict_about_the_riemann_hypothesis():
    """The module is about curves over finite fields, and its names say so."""
    import riemann_framework.finite_field_curves as module

    public = [name for name in dir(module) if not name.startswith("_")]
    suspicious = [n for n in public if "riemann_hypothesis" in n.lower()]
    assert suspicious == [], suspicious
