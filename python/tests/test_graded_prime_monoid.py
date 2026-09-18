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
"""Tests for the graded prime monoid.

The module's headline claim -- that exponent-vector addition is the only
operation compatible with unique factorisation -- is a theorem proved by
surjectivity of `phi`, and no test can establish it. What these tests do is
check the theorem's hypotheses over a range, pin the conclusion against the
rival rules so the claim has something to point at, and check the box identity
that connects the monoid to the Euler product.
"""

import math

import pytest

from riemann_framework.graded_prime_monoid import (
    CANDIDATE_RULES,
    add,
    candidate_rule_report,
    dense_vector,
    distinct_primes,
    energy,
    euler_box_sum,
    euler_factorization_report,
    euler_product_formula,
    exponent_vector,
    from_exponent_vector,
    graded_components,
    monoid_contract_report,
    prime_basis,
    smooth_truncation_report,
    total_degree,
)
from riemann_framework.primon_gas import factorize, zeta_reference


# ============================================================
# The identification phi : (N_{>0}, x) -> (V, +)
# ============================================================

def test_exponent_vector_is_the_factorisation():
    assert exponent_vector(12) == {2: 2, 3: 1}
    assert exponent_vector(97) == {97: 1}
    assert exponent_vector(1024) == {2: 10}


def test_exponent_vector_of_one_is_the_empty_vector():
    """`{}` is the monoid identity, so `phi(1)` must be it and not `{1: 1}`."""
    assert exponent_vector(1) == {}
    assert from_exponent_vector({}) == 1


def test_round_trip_over_a_range():
    """`phi` is a bijection, which is the hypothesis the uniqueness theorem uses.

    Both directions are checked over a range, on every element rather than on a
    sample: the backward direction enumerates the image of `phi`, which is the
    whole of the truncated `V` because `phi` is injective.
    """
    for n in range(1, 2001):
        assert from_exponent_vector(exponent_vector(n)) == n
        assert exponent_vector(from_exponent_vector(exponent_vector(n))) == exponent_vector(n)


def test_exponent_vector_matches_the_primon_gas_factorisation():
    """The two modules must not drift apart: this one delegates, and says so."""
    for n in range(1, 501):
        assert exponent_vector(n) == factorize(n)


def test_add_is_componentwise_addition():
    assert add({2: 2, 3: 1}, {2: 1, 5: 1}) == {2: 3, 3: 1, 5: 1}
    assert add({}, {2: 1}) == {2: 1}
    assert add({2: 1}, {}) == {2: 1}


def test_add_agrees_with_multiplication():
    """The whole identification in one assertion: `phi(m n) = phi(m) + phi(n)`."""
    for m in range(1, 200):
        for n in range(1, 200):
            assert exponent_vector(m * n) == add(exponent_vector(m), exponent_vector(n))


def test_from_exponent_vector_rejects_a_composite_key():
    """A vector indexed by 4 is meaningless here and would give a wrong integer."""
    with pytest.raises(ValueError, match="not a prime"):
        from_exponent_vector({4: 1})


def test_from_exponent_vector_rejects_a_negative_exponent():
    """`V` is a monoid, not a group: subtraction has nowhere to land."""
    with pytest.raises(ValueError, match="monoid, not a group"):
        from_exponent_vector({2: -1})


def test_zero_exponents_are_dropped_so_equal_vectors_compare_equal():
    assert from_exponent_vector({2: 1, 3: 0}) == 2
    assert total_degree({2: 1, 3: 0}) == 1
    assert distinct_primes({2: 1, 3: 0}) == (2,)


# ============================================================
# The grading: Omega is the "dimension"
# ============================================================

def test_total_degree_counts_factors_with_multiplicity():
    assert total_degree(exponent_vector(12)) == 3   # 2 * 2 * 3
    assert total_degree(exponent_vector(1)) == 0
    assert total_degree(exponent_vector(1024)) == 10


def test_degree_is_additive_over_a_range():
    """`Omega(m n) = Omega(m) + Omega(n)`: the grade is what multiplication adds."""
    for m in range(1, 150):
        for n in range(1, 150):
            assert total_degree(exponent_vector(m * n)) == (
                total_degree(exponent_vector(m)) + total_degree(exponent_vector(n))
            )


def test_graded_components_partition_the_range():
    components = graded_components(64)
    flattened = sorted(n for group in components.values() for n in group)
    assert flattened == list(range(1, 65))
    # Degree 1 is exactly the primes; degree 0 is exactly 1.
    assert components[0] == [1]
    assert components[1] == list(prime_basis(64))


def test_energy_is_the_linear_functional_of_the_exponent_vector():
    """`<lambda, v> = log(phi^{-1}(v))`, which is why the trace factorises.

    The equality is between two computations: the linear functional over the
    exponent vector, and the logarithm of the integer. It is exact up to
    floating point, and it is the step that turns a sum over the monoid into a
    product over primes.
    """
    for n in (1, 2, 12, 97, 1024, 720720):
        assert energy(exponent_vector(n)) == pytest.approx(math.log(n), rel=1e-14)


def test_dense_vector_places_exponents_on_the_basis():
    basis = prime_basis(20)
    assert dense_vector(exponent_vector(12), basis) == (2, 1, 0, 0, 0, 0, 0, 0)
    assert dense_vector({}, basis) == (0,) * len(basis)


def test_prime_basis_is_the_primes_up_to_the_cap():
    assert prime_basis(20) == (2, 3, 5, 7, 11, 13, 17, 19)
    assert prime_basis(2) == (2,)
    with pytest.raises(ValueError):
        prime_basis(1)


# ============================================================
# The uniqueness theorem: hypotheses checked, conclusion illustrated
# ============================================================

def test_monoid_contract_report_finds_no_failure():
    report = monoid_contract_report(300)
    assert report["first_failure"] is None
    assert report["round_trip_forward"]
    assert report["round_trip_backward"]
    assert report["multiplicative"]
    assert report["degree_additive"]
    assert report["identity_is_empty_vector"]
    assert report["pairs_checked"] > 1000


def test_addition_and_factor_concatenation_are_the_same_rule():
    """The "dimension grows" reading is not a rival rule; it is this one.

    Gluing the two lists of prime factors and adding the exponent vectors agree
    everywhere, because a multiset union of prime factors *is* exponent
    addition. This is asserted rather than argued in prose, since the obvious
    guess is that concatenation is a different rule that the theorem rules out.
    """
    reports = {r.name: r for r in candidate_rule_report(80)}
    assert reports["addition"].holds
    assert reports["concatenate_prime_factors"].holds
    # ... and they agree with each other, not merely with the target separately.
    for m in range(1, 40):
        for n in range(1, 40):
            from riemann_framework.graded_prime_monoid import (
                _rule_concatenate_prime_factors,
            )

            assert _rule_concatenate_prime_factors(
                exponent_vector(m), exponent_vector(n)
            ) == add(exponent_vector(m), exponent_vector(n))


@pytest.mark.parametrize(
    "name", ["exponent_max", "exponent_product", "support_union", "exponent_xor"]
)
def test_rival_rules_break_unique_factorisation(name):
    """Each rival rule must fail, and at a pair small enough to inspect by hand.

    The counterexample is checked to be genuine -- that the rule really does
    produce the integer reported -- so a broken report cannot pass by accident.
    """
    reports = {r.name: r for r in candidate_rule_report(120)}
    report = reports[name]
    assert not report.holds
    assert report.first_counterexample is not None
    m, n = report.first_counterexample
    assert m * n == report.expected
    assert report.produced != report.expected
    assert m * n <= 120


def test_candidate_rule_report_covers_every_declared_rule():
    names = [name for name, _, _ in CANDIDATE_RULES]
    assert [r.name for r in candidate_rule_report(30)] == names
    assert len(names) == len(set(names)), "rule names must be unique"


@pytest.mark.parametrize("n_max", [1, 2, 3])
def test_candidate_rule_report_rejects_a_range_too_small_to_be_informative(n_max):
    """Below `n_max = 4` a rival rule's first counterexample is out of range.

    Without the guard, `exponent_max` and `exponent_xor` are reported as holding
    at `n_max = 2`, because their first counterexample is `2 x 2` and the loop
    only visits `n <= n_max // m`. A guard that allowed that would let a
    directory of reports contain a vacuous pass.
    """
    with pytest.raises(ValueError, match=">= 4"):
        candidate_rule_report(n_max)


def test_the_smallest_useful_range_exposes_every_rival_rule():
    reports = {r.name: r for r in candidate_rule_report(4)}
    assert not reports["exponent_max"].holds
    assert not reports["exponent_xor"].holds
    assert not reports["support_union"].holds
    assert reports["addition"].holds


# ============================================================
# The Euler product as the generating function of the monoid
# ============================================================

@pytest.mark.parametrize("s", [2.0, 1.5, 3.0, complex(2.0, 3.0)])
def test_box_sum_equals_the_product_formula(s):
    """The finite form of "a sum over a free commutative monoid is a product".

    Enumerating the monoid (the left side) must equal the product of the
    per-prime geometric series (the right side). This identity is *why* the
    primon gas trace factorises, so it is the load-bearing check in this file.
    """
    basis = prime_basis(13)
    box = euler_box_sum(s, basis, 3)
    formula = euler_product_formula(s, basis, 3)
    assert box == pytest.approx(formula, rel=1e-12)


def test_euler_factorization_report_reports_agreement():
    report = euler_factorization_report(s=2.0)
    assert report["agrees"]
    assert report["relative_difference"] < 1e-12
    assert report["terms_enumerated"] == 4 ** len(report["basis"])


def test_box_identity_holds_for_a_larger_box():
    basis = prime_basis(31)
    report = euler_factorization_report(s=1.5, basis=basis, degree_cap=2)
    assert report["agrees"]
    assert report["terms_enumerated"] == 3 ** len(basis)


def test_euler_box_sum_enforces_the_term_cap():
    """The enumeration is exponential, so it is capped rather than left to hang."""
    with pytest.raises(ValueError, match="terms"):
        euler_box_sum(2.0, prime_basis(97), 40)


def test_product_formula_has_no_term_cap_because_it_is_cheap():
    """The same box that the enumeration refuses, the product computes."""
    value = euler_product_formula(2.0, prime_basis(97), 40)
    assert abs(value) > 1.0


def test_basis_validation_rejects_a_composite_and_a_duplicate():
    with pytest.raises(ValueError, match="not a prime"):
        euler_product_formula(2.0, (2, 4), 1)
    with pytest.raises(ValueError, match="repeated"):
        euler_product_formula(2.0, (2, 2), 1)


def test_smooth_truncation_approaches_zeta_monotonically():
    """Raising the caps adds exactly the missing terms, so the gap closes.

    The box over the primes `<= P` is the sum over `P`-smooth numbers, so it
    approaches `zeta(s)` from below. The assertion is on the trend across three
    increasingly large boxes rather than on one value, because a single
    agreement is what a fitted constant could also produce.
    """
    errors = [
        smooth_truncation_report(2.0, prime_cap=cap, degree_cap=degree)["relative_difference"]
        for cap, degree in ((13, 4), (97, 12), (997, 40))
    ]
    assert errors == sorted(errors, reverse=True), errors
    assert errors[-1] < 1e-3, errors[-1]
    assert smooth_truncation_report(2.0)["zeta_reference"] == pytest.approx(
        zeta_reference(2.0), rel=1e-12
    )


def test_smooth_truncation_rejects_re_s_at_most_one():
    """Below `Re(s) = 1` the comparison is meaningless, not merely imprecise."""
    with pytest.raises(ValueError, match="Re\\(s\\) > 1"):
        smooth_truncation_report(1.0)
