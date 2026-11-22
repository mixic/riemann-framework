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
"""Screen the Masullo draft's declared inputs with the Davenport-Heilbronn filter.

The draft under test is `references/masullo_music_of_the_primes_2026-11-20.pdf`, a
940-page typescript on a trace formula for the idelic class group and the zeros of
Hecke L-functions. It cannot be *verified* here -- there is no formalization to compile
and no spectrum to measure -- but one thing about it is decidable with machinery this
repository already has: whether the argument, as described in its own pages, uses any
fact that also holds for the Davenport-Heilbronn function, whose RH-analogue is false.

That question is the whole content of `dh_filter`: an argument that transfers to a
function with off-line zeros cannot establish RH. It takes only *declared inputs*, and
this module declares them from the paper's own text, with a section reference for each,
so that the declaration can be argued with rather than taken on trust.

The result is `eligible`, and the interesting part is *why*: the two inputs that fail
for Davenport-Heilbronn -- the Euler product, and the prime side of Weil's explicit
formula -- are exactly the arithmetic content of the draft. Its analytic input is a
functional equation, which DH also has, and that alone would be dead. So the filter
does not fire, and the honest reading is the filter's own: **permission, not promise**.
Nothing here says the draft is correct, and nothing here says any of its 900 pages of
analysis is right.

What is deliberately *not* declared is as important as what is:

* `li_positivity` is absent because section 1.4.6 of the draft says the argument does
  not use Weil's positivity criterion. Declaring it would have been *wrong about the
  paper*, and it would also have changed the verdict's meaning rather than its word:
  Li's criterion fails for Davenport-Heilbronn, so that screen would read `eligible`
  too -- but the eligibility would come from an input that is RH-equivalent, which is
  circularity, not discrimination. **The filter cannot see circularity, only transfer.**
  That is the sharpest limit of this module, and the reason it is not a validity check;
* `gue_pair_correlation` is absent because the argument is about the zeros themselves,
  not about their statistics;
* `hadamard_product` is absent because the draft states a divisor (Theorem 13.3.1.1)
  rather than an order-1 factorisation, and declaring an unstated input would be
  attributing a hypothesis to the author that he does not make.

The screen says nothing about the placeholder at Chapter 13, about the test-function
restriction `phi(C_F^1) = 0` that the draft says cannot be removed before GRH, or about
whether the trace formula itself is true. Those are recorded in
`docs/masullo_grh_draft.md`, and they are the reasons this module's verdict is much
narrower than a validation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dh_filter import DH_INPUTS, ScreenResult, screen_inputs

#: The record this screen declares inputs for; matches `ideas/<IDEA_ID>.json`.
IDEA_ID = "masullo_music_of_the_primes"


@dataclass(frozen=True)
class DeclaredInput:
    """One input the draft uses, the section that shows it is used, and why.

    The section reference is the point of the dataclass: a declaration without a
    location is an opinion about the paper, and this screen is not entitled to
    opinions about 940 pages it has only partly read.
    """

    key: str
    where: str
    why: str

    def summary(self) -> str:
        return f"{self.key} ({self.where}): {self.why}"


#: The inputs the draft declares and uses, as far as its own text shows.
DECLARED: tuple[DeclaredInput, ...] = (
    DeclaredInput(
        key="euler_product",
        where="§1.4.7 and §14.1.2 (partial Euler products), Appendix B.7",
        why=(
            "the argument is about Hecke L-functions, whose coefficients are "
            "multiplicative and which therefore have a local factor at every prime; "
            "the partial Euler products at §14.1.2 are read directly"
        ),
    ),
    DeclaredInput(
        key="explicit_formula_prime_side",
        where="Theorem 13.3.1.1 (the finite-place sum carries log q_v), Appendix B.4",
        why=(
            "Weil's explicit formulas are used in the form whose arithmetic side is "
            "supported on prime powers, which is the side that carries the Euler "
            "product across to the zeros; the stated Trace Formula has an explicit "
            "sum over finite places weighted by log(q_v)"
        ),
    ),
    DeclaredInput(
        key="functional_equation",
        where="§14.1.1 and Appendix B.4",
        why=(
            "the completed Hecke L-function satisfies Λ(s) = Λ(1 − s), which is what "
            "makes the zero set symmetric and lets the central line be discussed at all"
        ),
    ),
)

#: Inputs that would decide the screen but that the draft does not declare, with why not.
NOT_DECLARED: tuple[DeclaredInput, ...] = (
    DeclaredInput(
        key="li_positivity",
        where="§1.4.6 (explicitly excluded)",
        why=(
            "the draft states that Weil's positivity criterion is *not* used; declaring "
            "it would misstate the paper, and it would not even stiffen the verdict -- "
            "Li's criterion fails for DH, so the filter would still read eligible, on an "
            "RH-equivalent input. Circularity is invisible to this filter"
        ),
    ),
    DeclaredInput(
        key="gue_pair_correlation",
        where="not used",
        why=(
            "the argument is about where the zeros are, not about their spacing "
            "statistics, so the statistical input the sector-count programme needs is "
            "irrelevant to it"
        ),
    ),
    DeclaredInput(
        key="hadamard_product",
        where="Theorem 13.3.1.1 (a divisor, not a product)",
        why=(
            "the spectral side sums over the zeros with multiplicity, which needs "
            "discreteness; the draft supplies that through the divisor of a meromorphic "
            "function, not through an order-1 Hadamard factorisation, and the inventory "
            "row's *order* evidence is unsourced. Declaring it would attribute a "
            "hypothesis the author does not make"
        ),
    ),
)


def declared_keys() -> list[str]:
    """The inventory keys this screen declares, in declaration order."""
    return [d.key for d in DECLARED]


def screen() -> ScreenResult:
    """Run the Davenport-Heilbronn filter on the draft's declared inputs.

    Returns the filter's own result object, not a summary of it, so a caller can see
    the per-input classification rather than a verdict to quote out of context.
    """
    return screen_inputs(IDEA_ID, declared_keys())


def reading() -> str:
    """What the screen's verdict means here, in one paragraph, with its ceiling.

    Written once and pinned by a test because the failure mode this repository keeps
    hitting is a verdict quoted without the sentence that bounds it.
    """
    return (
        "The filter returns eligible: the draft uses at least one input that fails for "
        "Davenport-Heilbronn, so the contrapositive that kills a whole class of RH "
        "arguments does not apply to it. That is permission, not promise. It says the "
        "draft is not of the class this repository can *reject*; it says nothing about "
        "whether the draft is correct, nothing about the trace formula it rests on, and "
        "nothing about the theorem its Chapter 13 leaves as a placeholder. Passing this "
        "filter is also not a certificate of non-circularity: the filter sees transfer, "
        "not circularity, so an RH-equivalent input would pass it too. The draft avoids "
        "that input by its own statement at section 1.4.6, and that statement is the "
        "author's, not this repository's finding."
    )


def undeclared_table() -> list[tuple[str, str]]:
    """`(key, why not declared)` for the inputs a reader might expect to see."""
    return [(d.key, d.why) for d in NOT_DECLARED]


def inventory_check() -> list[str]:
    """Declared keys that are not in the DH inventory.

    Empty for this module, and a test insists on it: an unknown key would silently
    degrade the verdict to `needs_sourcing`, and a typo is not a finding about a paper.
    """
    return [key for key in declared_keys() if key not in DH_INPUTS]
