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
"""Tests for the Davenport-Heilbronn screening filter.

Two things are under test and they fail differently. The *calibration* tests
check that the Davenport-Heilbronn object this module builds really has the
properties the inventory claims, so that the two rows marked `verified_here` are
measured rather than asserted. The *filter* tests check the verdict logic, which
is bookkeeping and should be tested for the precedence it documents rather than
for any mathematical content.

Nothing here is evidence for or against the Riemann hypothesis, and no test
asserts that any argument is correct.
"""

from pathlib import Path

import mpmath as mp
import pytest

from riemann_framework.dh_filter import (
    DH_INPUTS,
    DH_SOURCES,
    DHVerdict,
    FUNCTIONAL_EQUATION_POINTS,
    InputStatus,
    calibrate,
    classify_input,
    dead_list,
    dh_coefficients,
    dh_completed,
    dh_gauss_sum,
    dh_kappa,
    eligible_list,
    functional_equation_residual,
    inventory_table,
    multiplicativity_holds,
    screen_all,
    screen_idea,
    screen_inputs,
    unclassified_inputs,
    unscreened_list,
)
from riemann_framework.idea_pipeline import Idea, load_all_ideas


IDEAS_DIR = Path(__file__).resolve().parents[2] / "ideas"


# ============================================================
# Calibration: the Davenport-Heilbronn object itself
# ============================================================

def test_gauss_sum_has_modulus_one():
    """`|tau(chi) / (i sqrt 5)| = 1`, which is what self-duality needs.

    The whole construction depends on this: `d = c * eps` can only be solved for
    a real kappa when `eps` is on the unit circle.

    The `workdps` block is load-bearing and was written after this test failed
    for the wrong reason. `mpmath` works at the *ambient* precision, so a
    division performed outside the block evaluates `mp.sqrt(5)` at the default 15
    digits and leaves a 1e-16 residue that looks like a mathematical failure and
    is not one. The module was correct; the test was measuring its own
    context.
    """
    with mp.workdps(30):
        eps = dh_gauss_sum() / (mp.mpc(0, 1) * mp.sqrt(5))
        assert abs(abs(eps) - 1) < mp.mpf(10) ** -25


def test_kappa_is_the_value_the_functional_equation_selects():
    """The derived constant, pinned so a change in the derivation is visible.

    This decimal is a *regression* pin, not the evidence: the evidence that the
    derivation is right is
    `test_completed_function_satisfies_the_functional_equation` below, which a
    wrong kappa cannot pass.
    """
    assert float(dh_kappa()) == pytest.approx(0.28407904384041229603, abs=1e-15)


def test_completed_function_satisfies_the_functional_equation():
    """`Lambda(s) = Lambda(1 - s)` to working precision.

    This is the load-bearing check of the whole calibration. It validates the
    character, the conductor, the odd-character gamma factor `(s+1)/2`, and
    kappa simultaneously: get any one of them wrong and the residual is O(1)
    rather than O(1e-30). It is also what caught an inverted sign convention for
    kappa while this module was written, where the residual was 0.7.
    """
    worst = max(
        float(functional_equation_residual(s)) for s in FUNCTIONAL_EQUATION_POINTS
    )
    assert worst < 1e-20


def test_functional_equation_points_are_mostly_off_the_critical_line():
    """The check is not quietly testing only the critical line.

    The functional equation relates `s` to `1 - s` whatever the real part, so
    sampling only on `Re s = 1/2` would test strictly less than it appears to.
    """
    on_line = [s for s in FUNCTIONAL_EQUATION_POINTS if abs(s.real - 0.5) < 1e-12]
    assert len(on_line) <= 1
    assert len(FUNCTIONAL_EQUATION_POINTS) >= 4


def test_dh_coefficients_are_real():
    """Real coefficients, hence `f(conj s) = conj (f s)`."""
    coeffs = dh_coefficients(30)
    for n, value in coeffs.items():
        assert abs(mp.im(value)) < mp.mpf(10) ** -25, f"b({n}) is not real"


def test_dh_coefficient_pattern_has_period_five():
    """`b(n) = (1, kappa, -kappa, -1, 0)` for `n = 1, 2, 3, 4, 0 (mod 5)`.

    Derived in the module from the linear combination of the two L-series, so
    this pins the derivation rather than quoting a table.

    Everything happens inside one `workdps` block, and that is load-bearing
    rather than stylistic. `mpmath` evaluates at the *ambient* precision, and --
    less obviously -- its unary negation rounds to the ambient precision too: the
    first version of this test formed `-kappa` at the default 15 digits, which
    silently replaced a 102-bit value with a 53-bit one, and the assertion failed
    by 2.5e-17 while `coeffs[3] + kappa` was exactly zero. Subtracting the two
    originals was exact; negating one of them was not.
    """
    with mp.workdps(40):
        coeffs = dh_coefficients(30)
        kappa = dh_kappa()
        expected = {1: mp.mpf(1), 2: kappa, 3: -kappa, 4: mp.mpf(-1), 0: mp.mpf(0)}
        for n in range(1, 31):
            err = abs(coeffs[n] - expected[n % 5])
            assert err < mp.mpf(10) ** -25, f"b({n}) differs by {mp.nstr(err, 5)}"


def test_comparisons_against_high_precision_values_survive_at_precision():
    """The property the test above relies on, stated on its own.

    Rather than pinning mpmath's rounding behaviour -- which would fail
    spuriously if it were ever fixed -- this pins the thing under our control:
    work done at 40 digits agrees, and work done at the ambient precision of this
    test does not.

    Two traps are recorded here, both of which bit this test. First, the
    comparison uses the raw `coeffs[3]` rather than `mp.mpf(coeffs[3])`: the
    constructor rounds to the ambient precision as well, so wrapping it collapses
    both sides to the same 53-bit value and the check passes for the wrong
    reason. Second, the ambient precision is set explicitly rather than assumed,
    because it is *not* stable across the test session -- see
    `test_ambient_mpmath_precision_is_not_what_this_module_assumes`.
    """
    saved = mp.mp.dps
    try:
        mp.mp.dps = 15
        kappa = dh_kappa()
        coeffs = dh_coefficients(30)
        # At 40 digits the negation is lossless and the two values agree.
        with mp.workdps(40):
            assert -kappa == coeffs[3]
        # At the ambient precision the negation is context-rounded and the
        # equality is lost, even though the two values agree to 30 digits.
        # Recorded so the `workdps` blocks here and above do not look removable.
        assert -kappa != coeffs[3]
    finally:
        mp.mp.dps = saved


def test_ambient_mpmath_precision_is_not_what_this_module_assumes():
    """A defect elsewhere in the suite, pinned so it is not forgotten.

    `tests/test_graded_algebra.py` and `tests/test_graded_algebra_even_odd.py`
    both assign `mp.mp.dps = 30` at *module import time*, which changes the global
    mpmath precision for every test that runs after them. A test of this module
    that assumed the default 15 digits therefore passed on its own and failed in
    the full suite.

    This test does not assert the leak: that would make it fail the moment the
    leak is fixed, which is the opposite of useful. It asserts only that the
    module's own functions are unaffected, because they work inside `workdps`
    blocks, so that the fix for the leak elsewhere is free to happen.
    """
    kappa = dh_kappa()
    coeffs = dh_coefficients(30)
    with mp.workdps(40):
        assert -kappa == coeffs[3]
    assert float(kappa) == pytest.approx(0.28407904384041229603, abs=1e-15)


def test_dh_coefficients_are_not_multiplicative():
    """The decisive check that DH has no Euler product.

    `b(2) b(3) = -kappa^2 = -0.0807...` while `b(6) = 1`. This is the inventory's
    `euler_product` row verified rather than cited, and it needs no asymptotic
    argument: one failure of multiplicativity settles it.
    """
    coeffs = dh_coefficients(30)
    product = coeffs[2] * coeffs[3]
    assert float(product) == pytest.approx(-0.080700903149306, abs=1e-12)
    assert float(coeffs[6]) == pytest.approx(1.0, abs=1e-25)
    assert abs(product - coeffs[6]) > mp.mpf("0.5")
    assert not multiplicativity_holds(coeffs, 30)


def test_multiplicativity_check_has_a_positive_control():
    """The predicate must return True for a genuinely multiplicative table.

    Without this, `not multiplicativity_holds(dh_coefficients(...))` would be
    consistent with the check being broken -- always returning False -- rather
    than with DH failing it. `c(n) = 1` is the coefficient table of zeta itself,
    which is multiplicative.
    """
    unit = {n: mp.mpf(1) for n in range(1, 31)}
    assert multiplicativity_holds(unit, 30)


def test_calibration_reports_the_measured_facts():
    """`calibrate` runs clean and agrees with the individual checks."""
    report = calibrate()
    assert report.gauss_sum_modulus == pytest.approx(1.0, abs=1e-25)
    assert report.worst_functional_equation_residual < 1e-20
    assert report.coefficients_are_real
    assert not report.coefficients_are_multiplicative
    assert report.verified_inputs == (
        "functional_equation",
        "real_coefficients",
        "euler_product",
    )
    assert "multiplicative: False" in report.summary()


def test_dh_completed_is_not_identically_zero():
    """A guard against a vacuous functional-equation check.

    `functional_equation_residual` is a *relative* residual, so it would be
    meaningless if the completed function vanished. `|Lambda|` decays steeply with
    height -- it is 1.2 at `s = 0.2 + 1.5i` and 7.7e-17 at `s = 0.8 + 50i`,
    because the gamma factor dominates -- so the assertion is that the values are
    strictly positive with a normalisation of order 1 at the lowest height
    sampled, not that every value is large.
    """
    values = [abs(dh_completed(s)) for s in FUNCTIONAL_EQUATION_POINTS]
    assert all(v > 0 for v in values)
    assert max(values) > mp.mpf("1e-3")
    assert max(values) < mp.mpf("100")


# ============================================================
# The inventory
# ============================================================

def test_inventory_covers_both_outcomes():
    """The inventory has rows on both sides, or it could not discriminate."""
    statuses = {row.status for row in DH_INPUTS.values()}
    assert InputStatus.TRANSFERS in statuses
    assert InputStatus.FAILS in statuses


def test_every_inventoried_row_records_evidence():
    """No row is allowed to be a bare assertion."""
    for key, row in DH_INPUTS.items():
        assert row.key == key
        assert row.description.strip(), f"{key} has no description"
        assert row.evidence.strip(), f"{key} has no evidence"
        assert len(row.evidence) > 80, f"{key} evidence is too thin to check"


def test_unsourced_rows_say_so_and_name_nothing_as_a_source():
    """`unsourced` rows must not cite something they did not use.

    A row with status `unsourced` carrying a citation would read as sourced at a
    glance, which is the failure mode this vocabulary exists to prevent.
    """
    for key, row in DH_INPUTS.items():
        if row.status is InputStatus.UNSOURCED:
            assert row.source == "", f"{key} is unsourced but names a source"
            assert not row.verified_here, f"{key} is unsourced but verified"


def test_sourced_rows_name_a_known_source():
    """Every non-unsourced row points at a citation key that exists."""
    for key, row in DH_INPUTS.items():
        if row.status is not InputStatus.UNSOURCED:
            assert row.source in DH_SOURCES, f"{key} cites unknown source {row.source!r}"


def test_verified_rows_are_exactly_what_calibration_checks():
    """`verified_here` is not a claim the module has to be trusted on.

    Every row marked verified must appear in the calibration's own report, and
    the report must not claim to verify a row the inventory does not mark.
    """
    marked = {key for key, row in DH_INPUTS.items() if row.verified_here}
    assert marked == set(calibrate().verified_inputs)


def test_unsourced_rows_are_reported_not_hidden():
    """The unsourced rows are a fixed, small, intentional part of the inventory.

    Recorded as a number so that adding an unsourced row is a visible decision
    rather than drift. If this count grows, the filter is losing power to
    `needs_sourcing` and the new rows want sourcing first.
    """
    unsourced = [k for k, r in DH_INPUTS.items() if r.status is InputStatus.UNSOURCED]
    assert len(unsourced) == 3, unsourced


def test_inventory_table_matches_the_inventory():
    """The printable view is derived, not maintained separately."""
    table = inventory_table()
    assert len(table) == len(DH_INPUTS)
    by_key = {row["key"]: row for row in table}
    for key, row in DH_INPUTS.items():
        assert by_key[key]["status"] == row.status.value
        assert by_key[key]["dh_holds"] is (row.status is InputStatus.TRANSFERS)


# ============================================================
# The filter's verdict logic
# ============================================================

def test_all_transferring_inputs_are_dead():
    """The filter's whole point: everything transfers, so the argument cannot work."""
    result = screen_inputs("t", ["functional_equation", "zero_symmetry"])
    assert result.verdict is DHVerdict.DEAD
    assert result.failing_inputs == []


def test_one_failing_input_is_enough_for_eligible():
    """Eligibility is existence, not unanimity."""
    result = screen_inputs("t", ["functional_equation", "euler_product"])
    assert result.verdict is DHVerdict.ELIGIBLE
    assert result.failing_inputs == ["euler_product"]


def test_a_failing_input_outranks_an_unsourced_one():
    """Precedence, pinned because it is a judgement and not an obvious one.

    With a failing input in evidence the candidate is `eligible` whatever else is
    declared: the unsourced rows could not make it *more* dead, because one input
    that DH lacks is already enough for the filter's purpose.
    """
    result = screen_inputs("t", ["gue_pair_correlation", "euler_product"])
    assert result.verdict is DHVerdict.ELIGIBLE


def test_an_unsourced_row_gives_needs_sourcing():
    """No failing input, and an unclassified one: no verdict."""
    result = screen_inputs("t", ["functional_equation", "gue_pair_correlation"])
    assert result.verdict is DHVerdict.NEEDS_SOURCING


def test_an_unknown_input_gives_needs_sourcing_and_is_listed():
    """New vocabulary is reported, not guessed at in either direction."""
    result = screen_inputs("t", ["functional_equation", "invented_input"])
    assert result.verdict is DHVerdict.NEEDS_SOURCING
    assert result.unknown_inputs == ["invented_input"]
    assert classify_input("invented_input").status is InputStatus.UNSOURCED


def test_an_undeclared_candidate_is_not_called_dead():
    """An empty declaration is unscreened, not dead.

    This is the difference between a verdict and the absence of evidence, and it
    is the failure mode of a filter that defaults to its most interesting answer.
    """
    result = screen_inputs("t", [])
    assert result.verdict is DHVerdict.NEEDS_SOURCING
    assert "No inputs declared" in result.summary


def test_verdicts_are_exactly_three():
    """No path returns a fourth, softer verdict such as 'likely'."""
    assert {v.value for v in DHVerdict} == {"dead", "eligible", "needs_sourcing"}


def test_dead_verdict_names_davenport_heilbronn_in_its_reason():
    """The dead verdict has to state *why*, since it is a claim about logic."""
    result = screen_inputs("t", ["zero_symmetry"])
    assert "Davenport-Heilbronn" in result.summary


def test_screen_result_str_is_readable():
    """The printed form carries the verdict and the per-input marks."""
    text = str(screen_inputs("some_idea", ["euler_product"]))
    assert "some_idea" in text
    assert "eligible" in text
    assert "euler_product" in text


# ============================================================
# Wiring into the idea records
# ============================================================

def _idea(idea_id: str, extra: dict) -> Idea:
    return Idea(
        id=idea_id,
        hypothesis="h",
        expression="s",
        falsification_criterion="f",
        extra=extra,
    )


def test_screen_idea_reads_the_declaration_from_extra():
    """The declaration rides in `extra`, so old records load unchanged."""
    idea = _idea("x", {"dh_inputs": ["euler_product"]})
    assert screen_idea(idea).verdict is DHVerdict.ELIGIBLE


def test_record_without_a_declaration_screens_as_needs_sourcing():
    """A pre-existing record is unscreened rather than silently dead."""
    assert screen_idea(_idea("x", {})).verdict is DHVerdict.NEEDS_SOURCING


def test_a_bare_string_declaration_is_accepted():
    """`"dh_inputs": "euler_product"` is read as a one-element list.

    A convenience, and a trap worth closing: without it the string would be
    iterated character by character and screen as a pile of unknown inputs.
    """
    idea = _idea("x", {"dh_inputs": "euler_product"})
    result = screen_idea(idea)
    assert result.verdict is DHVerdict.ELIGIBLE
    assert result.unknown_inputs == []


# ============================================================
# The three lists, which are the actual output
# ============================================================

def test_the_three_lists_partition_the_results():
    """Every screened candidate lands in exactly one list."""
    results = screen_all(
        [
            _idea("dead_one", {"dh_inputs": ["zero_symmetry"]}),
            _idea("live_one", {"dh_inputs": ["euler_product"]}),
            _idea("gap_one", {"dh_inputs": ["gue_pair_correlation"]}),
            _idea("undeclared_one", {}),
        ]
    )
    assert dead_list(results) == ["dead_one"]
    assert eligible_list(results) == ["live_one (via euler_product)"]
    unscreened = unscreened_list(results)
    assert len(unscreened) == 2
    assert any("gap_one" in s for s in unscreened)
    assert any("undeclared_one" in s for s in unscreened)


def test_unscreened_list_names_an_inventoried_but_unsourced_input():
    """The list must name the stopping input, not claim there is no declaration.

    `de_bruijn_newman_first_exit` declares `hadamard_product`, which *is* in the
    inventory with status `unsourced`. The first version of `unscreened_list`
    reported only keys missing from the inventory, so it described that record as
    "missing: declaration" -- the opposite of what happened, and a report that
    would send the next reader looking for a declaration that is already there.
    """
    results = screen_all(
        [_idea("declares_an_unsourced_row", {"dh_inputs": ["hadamard_product"]})]
    )
    entry = unscreened_list(results)[0]
    assert "hadamard_product" in entry
    assert "declaration" not in entry


def test_unclassified_inputs_reports_both_kinds_of_gap():
    """An unknown key and an inventoried-but-unsourced key are both gaps."""
    result = screen_inputs("t", ["not_in_inventory", "hadamard_product"])
    assert set(unclassified_inputs(result)) == {"not_in_inventory", "hadamard_product"}


def test_eligible_list_names_the_load_bearing_input():
    """Surviving is not an endorsement, so the list says what saved it.

    The named input is where the arithmetic content would have to live, which
    makes it the thing to attack first.
    """
    results = screen_all([_idea("x", {"dh_inputs": ["li_positivity"]})])
    assert eligible_list(results) == ["x (via li_positivity)"]


# ============================================================
# The repository's own records
# ============================================================

def test_every_repository_idea_screens_without_crashing():
    """The screener runs over the real records and returns real verdicts."""
    ideas = load_all_ideas(IDEAS_DIR)
    assert ideas, "no idea records found"
    results = screen_all(ideas)
    assert len(results) == len(ideas)
    for result in results:
        assert result.verdict in set(DHVerdict)
        assert result.summary


def test_the_dimension_shift_record_is_dead():
    """A documented finding, pinned so that changing it is deliberate.

    `dimension_shift_w` proposes an involution of the plane fixing `Re s = 1/2`.
    Every input that record declares -- the functional equation and the zero
    symmetry -- holds for Davenport-Heilbronn, whose zeros are not all on that
    line. So the argument would also fix the critical line of a function that
    violates the hypothesis, and cannot prove it.

    If this test starts failing, either the record's declaration changed or the
    inventory did; both are worth a look rather than a quick fix.
    """
    ideas = {idea.id: idea for idea in load_all_ideas(IDEAS_DIR)}
    assert "dimension_shift_w" in ideas
    result = screen_idea(ideas["dimension_shift_w"])
    assert result.verdict is DHVerdict.DEAD, result.summary


def test_the_primon_gas_lift_is_eligible_through_the_euler_product():
    """The repository's one exactly-arithmetic construction survives the filter.

    `dimension_shift_w_lifted_to_primon_gas` is built on the operator whose trace
    *is* the Euler product. That is precisely the input Davenport-Heilbronn lacks,
    so the filter finds somewhere for the arithmetic content to live. It says
    nothing about whether the operator commutes -- that is the record's own
    falsification criterion and it is separately known to fail.
    """
    ideas = {idea.id: idea for idea in load_all_ideas(IDEAS_DIR)}
    result = screen_idea(ideas["dimension_shift_w_lifted_to_primon_gas"])
    assert result.verdict is DHVerdict.ELIGIBLE
    assert result.failing_inputs == ["euler_product"]


def test_the_weil_compression_is_eligible_through_the_prime_side():
    """The refutation-capable framing survives, and for a checkable reason.

    That record's own text says its trace and Hilbert-Schmidt norm are
    "evaluated on the prime side". DH has no prime side, so the input fails for
    DH and the framing is not automatically dead.
    """
    ideas = {idea.id: idea for idea in load_all_ideas(IDEAS_DIR)}
    result = screen_idea(ideas["weil_positivity_finite_compression"])
    assert result.verdict is DHVerdict.ELIGIBLE
    assert "explicit_formula_prime_side" in result.failing_inputs


def test_declared_inputs_are_all_in_the_inventory():
    """No record may declare an input the inventory cannot classify.

    A typo in a `dh_inputs` list would otherwise surface as a silent
    `needs_sourcing` instead of a mistake.
    """
    for idea in load_all_ideas(IDEAS_DIR):
        declared = idea.extra.get("dh_inputs")
        if not declared:
            continue
        keys = [declared] if isinstance(declared, str) else list(declared)
        unknown = [k for k in keys if k not in DH_INPUTS]
        assert not unknown, f"{idea.id} declares unknown input(s): {unknown}"


def test_the_repository_has_a_nonempty_dead_list():
    """The filter fires on this repository's own material.

    A screen that never fires is worthless, and this is the check that it is not
    vacuous. It is deliberately a weaker statement than naming which records are
    dead -- `test_the_dimension_shift_record_is_dead` does that.
    """
    results = screen_all(load_all_ideas(IDEAS_DIR))
    assert dead_list(results)
