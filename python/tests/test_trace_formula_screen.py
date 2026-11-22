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
"""Tests for the Davenport-Heilbronn screen of the Masullo draft.

The screen is only worth having if it is (a) actually eligible for the reason claimed,
(b) capable of firing when it should, and (c) unable to be talked into a verdict by
inventing vocabulary. Each of those is asserted here, against the real filter rather
than against a stub, so a change in `dh_filter`'s inventory cannot silently turn the
verdict into something the documentation does not say.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from riemann_framework.dh_filter import DHVerdict, screen_inputs
from riemann_framework.idea_pipeline import load_idea
from riemann_framework.trace_formula_screen import (
    DECLARED,
    IDEA_ID,
    NOT_DECLARED,
    declared_keys,
    inventory_check,
    reading,
    screen,
    undeclared_table,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RECORD = REPO_ROOT / "ideas" / f"{IDEA_ID}.json"


def test_the_screen_is_eligible() -> None:
    """The draft uses inputs DH does not have, so the contrapositive does not fire."""
    result = screen()
    assert result.verdict is DHVerdict.ELIGIBLE
    assert result.idea_id == IDEA_ID
    assert "permission, not promise" in result.summary


def test_the_failing_inputs_are_the_arithmetic_ones() -> None:
    """Named, not merely counted: these two are why the verdict is what it is.

    `euler_product` and `explicit_formula_prime_side` are the two inventory rows that
    fail for DH. If either were dropped or reclassified, the verdict would change, and
    the documentation would need to change with it.
    """
    assert set(screen().failing_inputs) == {
        "euler_product",
        "explicit_formula_prime_side",
    }


def test_the_filter_can_still_fire_on_a_purely_analytic_input_set() -> None:
    """Non-vacuity: the same filter *does* reject a set that transfers.

    A functional equation alone is the classic dead case -- DH has one, and its zeros
    are off the line -- so this asserts the filter still fires, which is what makes the
    `eligible` verdict above a fact about the draft rather than about a filter that
    cannot reject anything.
    """
    assert screen_inputs("probe", ["functional_equation"]).verdict is DHVerdict.DEAD
    assert (
        screen_inputs("probe", ["functional_equation", "real_coefficients"]).verdict
        is DHVerdict.DEAD
    )


def test_the_rh_equivalent_criterion_is_not_declared_and_would_not_have_helped() -> None:
    """`li_positivity` is absent because the paper says so, not because it would fail.

    Li's criterion fails for DH, so declaring it would have produced the *same* verdict
    word from an RH-equivalent input: permission bought with circularity. The filter
    sees transfer, not circularity, so this is the sharpest limit of the screen, and
    the honest reason the draft's own section 1.4.6 is quoted instead.
    """
    assert "li_positivity" not in declared_keys()
    probe = screen_inputs("probe", ["li_positivity"])
    assert probe.verdict is DHVerdict.ELIGIBLE
    assert any("positivity" in item.why for item in NOT_DECLARED if item.key == "li_positivity")


def test_an_invented_input_cannot_make_the_verdict_eligible() -> None:
    """A fifth, made-up input degrades the screen rather than passing it.

    The filter reports an unknown key as `needs_sourcing`, so vocabulary cannot be
    stretched into a verdict. This is the failure mode a reader should worry about when
    a paper is described in the paper's own terms.
    """
    result = screen_inputs(IDEA_ID, ["euler_product", "orbital_schauder_basis"])
    assert result.verdict is DHVerdict.ELIGIBLE  # the failing input still decides
    assert screen_inputs(IDEA_ID, ["orbital_schauder_basis"]).verdict is (
        DHVerdict.NEEDS_SOURCING
    )


def test_every_declared_input_is_in_the_inventory_and_names_a_location() -> None:
    """A typo would degrade the verdict silently, so the keys are checked.

    Each declaration must also carry the section reference that shows the draft uses
    it; a declaration without a location would be an opinion about a paper this screen
    has not read.
    """
    assert inventory_check() == []
    for item in DECLARED:
        assert item.where.strip(), item.key
        assert len(item.why.split()) > 8, item.key


def test_the_idea_record_matches_the_module() -> None:
    """The JSON record and the module declare the same inputs.

    Two declarations of the same thing is a drift hazard, so they are compared rather
    than trusted. The record is also the thing `scripts/run_dh_filter.py` screens.
    """
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    assert data["dh_inputs"] == declared_keys()

    idea = load_idea(RECORD)
    from riemann_framework.dh_filter import screen_idea

    assert screen_idea(idea).verdict is DHVerdict.ELIGIBLE


def test_the_reading_states_its_own_ceiling() -> None:
    """The paragraph a reader will quote must bound itself.

    Three sentences are load-bearing: that the verdict is permission rather than
    promise, that it says nothing about the draft's correctness, and that the
    placeholder at Chapter 13 is what the filter cannot see.
    """
    text = reading()
    assert "permission, not promise" in text
    assert "nothing about whether the draft is correct" in text
    assert "placeholder" in text

    undeclared = dict(undeclared_table())
    assert set(undeclared) == {"li_positivity", "gue_pair_correlation", "hadamard_product"}
    assert "positivity" in undeclared["li_positivity"]
    assert [item.key for item in NOT_DECLARED] == list(undeclared)
