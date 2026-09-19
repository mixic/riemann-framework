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
"""
Tests for the graded prime-exponent monoid.

The central claims under test: (1) padding alone (`pad_to`) never changes
which integer an element represents -- it is arithmetically inert; (2) the
one multiplication rule compatible with unique factorisation (exponent-vector
addition) is exactly ordinary integer multiplication, checked by brute force
over a real range rather than asserted; (3) dimension is subadditive in
general and exactly additive on coprime elements, which is where "dimension
increases under multiplication" becomes a precise, checkable statement
instead of a metaphor.
"""

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from riemann_framework.graded_prime_monoid import (
    CANDIDATE_RULES,
    ONE,
    GradedPrimeNumber,
    bridge_to_primon_gas,
    candidate_rule_report,
    dimension_of,
    dimension_tower,
    euler_product_from_grading,
    from_int,
    truncated_euler_product,
    verify_monoid_isomorphism,
)


def test_one_is_the_zero_dimensional_identity():
    assert ONE.dimension == 0
    assert ONE.to_int() == 1
    assert from_int(1) == ONE


@pytest.mark.parametrize(
    "n, expected_dim",
    [(1, 0), (2, 1), (4, 1), (6, 2), (12, 2), (30, 3), (2 * 3 * 5 * 7, 4)],
)
def test_dimension_is_number_of_distinct_prime_factors(n, expected_dim):
    assert dimension_of(n) == expected_dim


def test_round_trip_from_int_to_int():
    for n in range(1, 500):
        assert from_int(n).to_int() == n


def test_padding_never_changes_the_encoded_integer():
    """Padding alone -- `1 -> (1,0) -> (1,0,0) -> ...` -- is arithmetically
    inert: it changes the ambient dimension but never the integer, which is
    exactly the property that makes zero-padding, by itself, not yet a
    number system (see this module's docstring)."""
    x = from_int(60)
    for k in range(x.dimension, x.dimension + 5):
        padded = x.pad_to(k)
        assert padded.to_int() == 60
        assert padded == x  # equality ignores trailing-zero padding


def test_padding_down_is_rejected():
    x = from_int(60)  # dimension 3: (2,1,1)
    with pytest.raises(ValueError):
        x.pad_to(x.dimension - 1)


def test_multiplication_matches_integer_multiplication_directly():
    a, b = from_int(6), from_int(10)
    product = a * b
    assert product.to_int() == 60
    assert product == from_int(60)


def test_multiplication_is_commutative_and_has_identity():
    for a_int in range(1, 30):
        a = from_int(a_int)
        assert a * ONE == a
        assert ONE * a == a
        for b_int in range(1, 30):
            b = from_int(b_int)
            assert a * b == b * a


def test_multiplication_dimension_is_subadditive_and_exact_on_disjoint_support():
    """Dimension is subadditive in general (shared prime factors don't add a
    new dimension) and exactly additive when the two factors are coprime --
    this is the precise sense in which multiplying two "k-dimensional" and
    "m-dimensional" numbers can produce a "(k+m)-dimensional" one."""
    # Disjoint support: dim(6)=2 [primes 2,3], dim(35)=2 [primes 5,7] ->
    # product 210 = 2*3*5*7 has dimension exactly 4.
    a, b = from_int(6), from_int(35)
    assert dimension_of(a.to_int()) == 2
    assert dimension_of(b.to_int()) == 2
    assert (a * b).dimension == 4

    # Shared support: dim(6)=2, dim(10)=2, but 6*10=60=2^2*3*5 has dimension 3,
    # not 4 -- strictly subadditive because the prime 2 is shared.
    a2, b2 = from_int(6), from_int(10)
    assert (a2 * b2).dimension == 3
    assert (a2 * b2).dimension <= a2.dimension + b2.dimension


def test_verify_monoid_isomorphism_reports_no_mismatches():
    report = verify_monoid_isomorphism(n_max=80)
    assert report.mismatches == []
    assert report.round_trip_ok


def test_dimension_tower_preserves_value_and_increases_ambient_length():
    tower = dimension_tower(12, max_dim=6)
    assert all(elem.to_int() == 12 for elem in tower)
    lengths = [len(elem.exponents) for elem in tower]
    assert lengths == sorted(lengths)
    assert lengths[0] == dimension_of(12)
    assert lengths[-1] == 6


def test_dimension_tower_rejects_max_dim_below_actual_dimension():
    with pytest.raises(ValueError):
        dimension_tower(30, max_dim=1)  # dimension_of(30) == 3


def test_negative_exponent_is_rejected():
    with pytest.raises(ValueError):
        GradedPrimeNumber((1, -1))


def test_bridge_to_primon_gas_reproduces_the_zeta_2_sum():
    """The graded-by-dimension regrouping must sum to the same truncated
    zeta(2) value primon_gas.trace_exp computes directly -- this is the
    checkable half of the claim that this module's structure underlies
    primon_gas.py, not just a suggestive analogy."""
    from riemann_framework.primon_gas import trace_exp

    n_max = 3000
    bridge = bridge_to_primon_gas(n_max)
    direct = trace_exp(2.0, n_max)
    assert bridge.total == pytest.approx(direct.real, rel=1e-9)


def test_bridge_report_dimension_zero_is_just_the_identity():
    bridge = bridge_to_primon_gas(100)
    assert bridge.by_dimension[0] == [1]
    assert bridge.contribution_by_dimension[0] == pytest.approx(1.0)


# ============================================================
# Regressions: the two defects found on review
# ============================================================

def test_no_package_module_imports_sympy():
    """This repository depends only on mpmath/numpy/scipy/matplotlib/pytest.

    `graded_prime_monoid` used to import `factorint`, `prime` and `primerange`
    from sympy, which is neither installed nor declared in `pyproject.toml`. The
    module therefore raised `ModuleNotFoundError` on import and its test file
    failed at *collection*, taking the whole suite down.

    The scan parses import statements rather than searching for the substring:
    two modules mention sympy in prose to explain why it was *removed*, and a
    substring search would flag them.
    """
    package = Path(__file__).resolve().parent.parent / "riemann_framework"
    offenders: list[str] = []
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]]
            if "sympy" in names:
                offenders.append(path.name)
    assert offenders == [], (
        f"{offenders} import sympy, which is not installed or declared; the "
        "modules would fail to import"
    )


@pytest.mark.parametrize("n", [3, 5, 7, 10, 14, 35, 97])
def test_dimension_tower_works_for_elements_with_internal_zeros(n):
    """`dimension_tower` must start at the ambient *length*, not the dimension.

    The two differ whenever the exponent tuple has an internal zero, i.e. for
    every `n` not divisible by every smaller prime. `from_int(97)` has dimension
    1 and length 25, so a tower starting at the dimension called `pad_to(1)` on
    a length-25 tuple and raised `ValueError`. An earlier revision did exactly
    that and crashed for 81 of the first 100 integers; its guard tested the same
    wrong quantity, so it let those calls through. The old tests used 12 and 30,
    which have no internal zeros, and so missed it.
    """
    base = from_int(n)
    assert len(base.exponents) > base.dimension, "not an internal-zero case"

    tower = dimension_tower(n, max_dim=len(base.exponents) + 3)
    assert all(element.to_int() == n for element in tower)
    lengths = [len(element.exponents) for element in tower]
    assert lengths == sorted(lengths)
    assert lengths[0] == len(base.exponents)
    assert lengths[-1] == len(base.exponents) + 3


def test_dimension_tower_guard_uses_the_ambient_length_not_the_dimension():
    """For `n = 97` the dimension is 1 but the tuple needs 25 coordinates.

    A guard phrased in terms of the dimension accepts `max_dim = 2` and then
    fails deeper in `pad_to`; it must reject it up front.
    """
    with pytest.raises(ValueError, match="ambient length"):
        dimension_tower(97, max_dim=2)
    # And the smallest legal request works.
    assert dimension_tower(97, max_dim=25)[0].to_int() == 97


def test_internal_zeros_do_not_count_towards_dimension():
    """`(0, 0, 1, 1)` is 35 = 5*7 and has dimension 2, not 4.

    Trimming trailing zeros would leave this tuple untouched, so dimension must
    count nonzero entries directly.
    """
    assert from_int(35).exponents == (0, 0, 1, 1)
    assert dimension_of(35) == 2
    assert dimension_of(5) == 1
    assert from_int(97).exponents.count(0) == 24
    assert dimension_of(97) == 1


def test_from_int_rejects_zero_and_negatives():
    for n in (0, -1, -97):
        with pytest.raises(ValueError):
            from_int(n)


def test_equality_with_a_foreign_type_is_not_asserted():
    assert (ONE == 1) is False
    assert (ONE == "1") is False


def test_isomorphism_report_counts_every_pair_it_checks():
    report = verify_monoid_isomorphism(n_max=40)
    assert report.pairs_checked == 40 * 40
    assert report.mismatches == []


def test_bridge_report_checks_itself_against_primon_gas():
    """The comparison with `primon_gas.trace_exp` is performed, not described.

    Note the limit honestly: the two sides are the same sum computed two ways,
    so this checks that the partition by dimension is complete and totalled
    correctly. It does not check that the sum factorises -- that is
    `euler_product_from_grading`.
    """
    bridge = bridge_to_primon_gas(500)
    assert bridge.agrees
    assert bridge.total == pytest.approx(bridge.direct_trace, rel=1e-9)


# ============================================================
# The Euler product as this monoid's generating function
# ============================================================

@pytest.mark.parametrize("grading_weight", [1.0, 0.5, 0.0])
def test_monoid_sum_equals_the_product_of_local_factors(grading_weight):
    """Summing over the monoid equals multiplying one local factor per prime.

    That identity *is* "the Euler product is what this number system's zeta-like
    sum looks like": a sum of a product over a free commutative monoid is a
    product of sums. It is checked here rather than asserted in a docstring.
    """
    report = euler_product_from_grading(
        2.0, prime_limit=13, degree_cap=4, grading_weight=grading_weight
    )
    assert report.agrees, report.explanation
    assert report.relative_difference < 1e-12
    assert len(report.basis) == 6


def test_the_local_factor_at_one_is_the_euler_factor():
    """`sum_a q^{omega(p^a)} p^{-as}` at `q = 1` is `1/(1 - p^{-s})`.

    This is the step that makes the grading by `omega` (distinct primes) give
    the Euler product, and not merely some regrouping. Checked on the factor
    itself, free of any truncation of the product.
    """
    s, degree_cap = 2.0, 400
    for p in (2, 3, 7, 97):
        x = p ** (-s)
        local = 1.0 + sum(x ** a for a in range(1, degree_cap + 1))
        assert local == pytest.approx(1.0 / (1.0 - x), rel=1e-12)


def test_euler_product_from_grading_is_the_truncated_euler_product_at_q_one():
    """At `q = 1` the product of local factors is `prod_p (1 + x/(1-x))`.

    With a degree cap the box drops the exponent tail, so the capped value sits
    strictly *below* `prod_p 1/(1-x)`; raising the cap closes the gap. The
    uncapped side is computed directly, since enumerating the monoid at a large
    cap is not possible and is not needed to see the limit.
    """
    capped = euler_product_from_grading(2.0, prime_limit=13, degree_cap=2)
    ideal = truncated_euler_product(2.0, 13)
    assert capped.product_of_local_factors < ideal
    assert ideal == pytest.approx(capped.ideal_euler_product, rel=1e-12)

    uncapped = 1.0
    for p in capped.basis:
        x = p ** -2.0
        uncapped *= 1.0 + sum(x ** a for a in range(1, 500))
    assert uncapped == pytest.approx(ideal, rel=1e-9)


def test_truncated_euler_product_is_cheap_and_exact():
    """No box, no cap: linear in the number of primes."""
    value = truncated_euler_product(2.0, 1999)
    assert value < math.pi ** 2 / 6, "a truncation undershoots"
    assert value == pytest.approx(math.pi ** 2 / 6, rel=1e-3)


def test_euler_product_from_grading_rejects_an_oversized_box():
    with pytest.raises(ValueError, match="terms"):
        euler_product_from_grading(2.0, prime_limit=97, degree_cap=40)


def test_euler_product_from_grading_rejects_a_degenerate_basis():
    with pytest.raises(ValueError, match="no primes"):
        euler_product_from_grading(2.0, prime_limit=1)


# ============================================================
# The uniqueness of the rule, illustrated by the rivals
# ============================================================

def test_the_forced_rule_agrees_with_unique_factorisation():
    reports = {r.name: r for r in candidate_rule_report(60)}
    assert reports["multiplication"].holds
    assert reports["multiplication"].pairs_checked == 60 * 60


def test_concatenating_prime_factors_is_the_same_rule_not_a_rival():
    """The literal "the dimension grows" reading is addition, not an alternative.

    Gluing the two lists of prime factors and adding the exponent vectors agree
    everywhere, because a multiset union of prime factors *is* exponent addition.
    This is asserted rather than argued in prose, since the natural guess is the
    opposite -- that concatenation is the rival the theorem rules out. It is
    checked through the public registry, so no private function is imported.
    """
    rules = {name: rule for name, rule, _ in CANDIDATE_RULES}
    concatenate = rules["concatenate_prime_factors"]

    assert {r.name: r.holds for r in candidate_rule_report(40)}[
        "concatenate_prime_factors"
    ]
    for m in range(1, 30):
        for n in range(1, 30):
            assert concatenate(from_int(m), from_int(n)) == from_int(m * n)
            assert concatenate(from_int(m), from_int(n)) == (
                from_int(m) * from_int(n)
            )


@pytest.mark.parametrize(
    "name, expected_pair",
    [
        ("exponent_max", (2, 2)),
        ("exponent_product", (1, 2)),
        ("support_union", (1, 4)),
        ("exponent_xor", (2, 2)),
    ],
)
def test_rival_rules_fail_unique_factorisation_at_a_checkable_pair(name, expected_pair):
    """Each rival must fail, and at a pair small enough to verify by hand.

    The counterexample is checked to be genuine -- that the rule really does
    produce the integer reported -- so a report that merely *claimed* a failure
    could not pass.
    """
    report = {r.name: r for r in candidate_rule_report(200)}[name]
    assert not report.holds
    # Bind to a local before unpacking: Pyright does not narrow
    # `report.first_counterexample` from an `==` comparison, only from an
    # explicit `is not None` on the expression it is about to unpack.
    pair = report.first_counterexample
    assert pair is not None
    assert pair == expected_pair
    m, n = pair
    assert report.required == m * n
    assert report.produced != report.required


def test_reported_counterexample_matches_what_the_rule_computes():
    rules = {name: rule for name, rule, _ in CANDIDATE_RULES}
    for report in candidate_rule_report(30):
        if report.holds:
            continue
        assert report.first_counterexample is not None
        m, n = report.first_counterexample
        actual = rules[report.name](from_int(m), from_int(n)).to_int()
        assert actual == report.produced
        assert actual != m * n


def test_candidate_rule_report_covers_every_declared_rule():
    declared = [name for name, _, _ in CANDIDATE_RULES]
    assert [r.name for r in candidate_rule_report(20)] == declared
    assert len(declared) == len(set(declared)), "rule names must be unique"


def test_candidate_rule_report_rejects_a_vacuous_range():
    """Below `n_max = 4` the rivals' counterexamples are out of range.

    At `n_max = 2` the loop only reaches `n <= n_max // m`, so `exponent_max` and
    `exponent_xor` -- whose first counterexample is `2 x 2` -- would be reported
    as holding without ever being tested where they fail.
    """
    for n_max in (1, 2, 3):
        with pytest.raises(ValueError, match=">= 4"):
            candidate_rule_report(n_max)
    # n_max = 4 is the smallest range that exposes every rival.
    assert not {r.name: r for r in candidate_rule_report(4)}["exponent_max"].holds


def test_rule_report_summary_says_which_way_it_went():
    for report in candidate_rule_report(20):
        if report.holds:
            assert "agrees" in report.summary
        else:
            assert "fails at" in report.summary
            assert str(report.required) in report.summary