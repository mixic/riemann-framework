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
"""Tests for the stage screening.

The load-bearing facts are that the shared input is recorded as `unsourced` in the
inventory and that every claim declares it: either one changing would let the stage be
screened as something other than what it is. The list itself is pinned by length so a
claim cannot be dropped without the count moving.
"""

from __future__ import annotations

import pytest

from riemann_framework.dh_filter import DHVerdict, InputStatus, screen_inputs
from riemann_framework.stage_screen import (
    CLAIMS,
    SPECTRAL_INPUT,
    SpectralClaim,
    inventory_status,
    screen_stage,
    stage_summary,
    verdict_counts,
    zeta_claims,
)


def test_the_stage_declares_five_claims():
    assert len(CLAIMS) == 5
    assert len({claim.key for claim in CLAIMS}) == 5


def test_every_claim_declares_the_spectral_input():
    for claim in CLAIMS:
        assert claim.inputs == (SPECTRAL_INPUT,), claim.key


def test_the_shared_input_is_unsourced_in_the_inventory():
    """The premise of the whole note: the input this stage rests on has no source."""
    assert inventory_status() is InputStatus.UNSOURCED


def test_every_claim_screens_as_needs_sourcing():
    rows = screen_stage()
    assert [row.result.verdict for row in rows] == [DHVerdict.NEEDS_SOURCING] * len(CLAIMS)
    assert verdict_counts(rows)["needs_sourcing"] == len(CLAIMS)


def test_no_claim_is_dead_or_eligible():
    """The filter must not hand the stage a permission it has not earned."""
    counts = verdict_counts(screen_stage())
    assert counts["dead"] == 0
    assert counts["eligible"] == 0


def test_no_claim_asserts_something_about_the_zeros():
    assert zeta_claims() == []
    for claim in CLAIMS:
        assert claim.about_zeros is False, claim.key


def test_an_undeclared_claim_would_be_unscreened():
    """The declaration is load-bearing: without it the filter has nothing to screen."""
    undeclared = SpectralClaim(
        key="nothing", statement="declares nothing", inputs=(), about_zeros=False
    )
    result = screen_inputs(undeclared.key, list(undeclared.inputs))
    assert result.verdict is DHVerdict.NEEDS_SOURCING
    assert "No inputs declared" in result.summary


def test_the_summary_names_the_inventory_row():
    text = stage_summary()
    assert SPECTRAL_INPUT in text
    assert "unsourced" in text
    assert "5 claims" in text
