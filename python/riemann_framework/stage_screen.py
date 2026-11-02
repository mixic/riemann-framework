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
"""Screen this stage's own claims with the Davenport-Heilbronn filter.

The filter in :mod:`riemann_framework.dh_filter` is a contrapositive: an argument that
runs unchanged where RH fails cannot establish RH. It classifies the *declared inputs* of a
candidate, and it is meant to be pointed at other people's proposals. This module points it
at the sector-count programme itself, which is the only way the filter can be shown to
work as designed rather than as advertised.

None of the claims below is a claim about the zeros. They are statements about spectra:
where a spacing statistic stops carrying a sector count, how a dominant sector biases an
equal-block posterior, what a split does on three real systems, what a posterior covers, and
what a PT symmetry leaves measurable. That is why each claim is recorded with
``about_zeros = False``: the filter's contrapositive applies to arguments that conclude
something about the zeros, and none of these does.

For every claim the module still records the one inventory key that *would* have to hold
for the claim to say anything about the zeros: ``gue_pair_correlation``, the conjecture
that the zeros have GUE local statistics. The inventory records that row as ``unsourced``.
The mechanical verdict is therefore ``needs_sourcing`` for every claim in the stage, and the
honest reading is the one the filter exists to produce: the stage inherits an unsourced
input, and it is the statistics of the zeros themselves.

No Riemann hypothesis claim is made here, and none of these measurements is evidence for
one.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dh_filter import (
    DH_INPUTS,
    DHVerdict,
    InputStatus,
    ScreenResult,
    screen_inputs,
)

#: The inventory key every claim in this stage would depend on if it were ever used to say
#: something about the zeros. Recorded as `unsourced` in the inventory, which is the point.
SPECTRAL_INPUT = "gue_pair_correlation"


@dataclass(frozen=True)
class SpectralClaim:
    """One claim this stage makes, and the input it would need to touch the zeros."""

    key: str
    statement: str
    inputs: tuple[str, ...]
    about_zeros: bool

    def summary(self) -> str:
        scope = "claims something about the zeros" if self.about_zeros else "spectra only"
        return f"{self.key}: {self.statement} ({scope})"


#: The stage's claims, one per committed increment.
CLAIMS: tuple[SpectralClaim, ...] = (
    SpectralClaim(
        key="boundary_map",
        statement=(
            "no spacing statistic names a sector count above two, and pairwise "
            "separation is a different question from counting"
        ),
        inputs=(SPECTRAL_INPUT,),
        about_zeros=False,
    ),
    SpectralClaim(
        key="mixed_sectors",
        statement=(
            "an equal-block posterior under-counts by about one sector when one block "
            "carries four times the levels"
        ),
        inputs=(SPECTRAL_INPUT,),
        about_zeros=False,
    ),
    SpectralClaim(
        key="real_systems",
        statement=(
            "on Ising, Heisenberg and kicked-top spectra the full-spectrum statistic "
            "sits below every sector's in three of four cases"
        ),
        inputs=(SPECTRAL_INPUT,),
        about_zeros=False,
    ),
    SpectralClaim(
        key="diagnose",
        statement=(
            "the one-call report verifies its involutions, refuses the ones that do not "
            "commute, and states each conclusion with its number"
        ),
        inputs=(SPECTRAL_INPUT,),
        about_zeros=False,
    ),
    SpectralClaim(
        key="pt_symmetry",
        statement=(
            "a broken PT spectrum has no real spectrum to measure, and the pairing that "
            "survives is not a decomposition into subspaces"
        ),
        inputs=(SPECTRAL_INPUT,),
        about_zeros=False,
    ),
)


@dataclass(frozen=True)
class StageScreenRow:
    """The filter's result for one claim, next to the claim itself."""

    claim: SpectralClaim
    result: ScreenResult

    def summary(self) -> str:
        return (
            f"{self.claim.key:>14}: {self.result.verdict.value:<14} "
            f"inputs={','.join(self.claim.inputs)} "
            f"{'about the zeros' if self.claim.about_zeros else 'spectra only'}"
        )


def screen_stage(claims: tuple[SpectralClaim, ...] = CLAIMS) -> list[StageScreenRow]:
    """Screen every claim with the same filter that screens other people's proposals."""
    return [
        StageScreenRow(claim=claim, result=screen_inputs(claim.key, list(claim.inputs)))
        for claim in claims
    ]


def verdict_counts(rows: list[StageScreenRow]) -> dict[str, int]:
    """How many claims fall to each verdict, so a summary can be quoted without a list."""
    counts: dict[str, int] = {verdict.value: 0 for verdict in DHVerdict}
    for row in rows:
        counts[row.result.verdict.value] += 1
    return counts


def zeta_claims(claims: tuple[SpectralClaim, ...] = CLAIMS) -> list[SpectralClaim]:
    """The claims that assert something about the zeros. Currently none."""
    return [claim for claim in claims if claim.about_zeros]


def inventory_status(key: str = SPECTRAL_INPUT) -> InputStatus:
    """The inventory's status for the shared input, so a test can pin the premise."""
    row = DH_INPUTS.get(key)
    if row is None:
        raise KeyError(f"{key} is not in the Davenport-Heilbronn inventory")
    return row.status


def stage_summary() -> str:
    """The one-paragraph result, built from the rows rather than written by hand."""
    rows = screen_stage()
    counts = verdict_counts(rows)
    unsourced = [row.claim.key for row in rows if row.result.verdict is DHVerdict.NEEDS_SOURCING]
    return (
        f"{len(rows)} claims screened: "
        + ", ".join(f"{value} {name}" for name, value in counts.items() if value)
        + f". {len(unsourced)} of them rest on the inventory row '{SPECTRAL_INPUT}', "
        f"which the inventory records as '{inventory_status().value}'. None of the claims "
        "asserts anything about the zeros, so the filter's contrapositive does not fire; "
        "it reports the unsourced input instead."
    )
