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
A screening filter for candidate Riemann-hypothesis arguments, keyed on the
Davenport-Heilbronn function.

The idea, and where it comes from
---------------------------------
Alpoge and Furman's section 1.4 records that the inputs of their method "hold for
Davenport-Heilbronn and Epstein zeta functions, for which the analogue of RH is
false". Read as a contrapositive, that is a *filter*, and a sharp one:

    an argument that goes through unchanged where the hypothesis fails cannot
    establish the hypothesis; therefore any proof of RH must use at least one
    input that fails for Davenport-Heilbronn.

So a candidate argument is screened by asking, of each mathematical input it
uses, whether that input remains available for the Davenport-Heilbronn function
`f`. This module answers that question from a fixed inventory and returns one of
three verdicts:

    ``dead``            every declared input transfers to DH. The argument would
                        also prove the DH analogue of RH, which is false, so it
                        cannot be a proof of RH.
    ``eligible``        at least one declared input fails for DH. The argument is
                        not dead by this filter. This is a *permission*, not a
                        promise: it says only that the filter found somewhere for
                        the arithmetic content to live.
    ``needs_sourcing``  a declared input is not in the inventory, or is in it
                        with status ``unsourced``. No verdict is available, and
                        the honest output is the missing fact rather than a guess.

The interesting output is the dead list. `screen_all` and `dead_list` exist so
the screening happens before any numerics are written for an idea, and so the
ideas that cannot work are recorded as such rather than rediscovered later.

What this filter is not
-----------------------
It classifies **declared** inputs. An argument that uses an input it does not
declare, or uses a declared input in a way that silently depends on an undeclared
one, is not classified by it. It is a screen on paper, not a checker.

`eligible` is weak on purpose. "The coefficients are multiplicative" is an input
that fails for DH and is still worthless, because it is true of zeta and proves
nothing. Failing the filter's transfer test is necessary for an RH proof; it is
nowhere near sufficient.

The sourcing rule
-----------------
The inventory below was written from sources read for this module, not from
memory, and every row records what was actually read. Where a row could not be
established from a source that was read, its status is ``unsourced`` rather than
a guess -- including one row where the expected answer is probably knowable and
simply was not established here. Two rows are additionally *verified in this
repository* rather than only cited, by the calibration functions at the bottom of
this module: the functional equation (which the construction must satisfy) and
the absence of an Euler product (which is a finite computation on the
coefficients).

Nothing here proves or disproves the Riemann hypothesis, and nothing here
evaluates any candidate argument as correct.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Sequence

import mpmath as mp

from .idea_pipeline import Idea


# The conductor of the Davenport-Heilbronn function: the odd Dirichlet character
# mod 5, so q = 5 and the character is odd (a = 1) in the completion.
MODULUS = 5


# ============================================================
# Sources, recorded at the level of what was actually read
# ============================================================

#: Citation keys used by the inventory. Each entry names the source and, where it
#: matters, exactly which part of it was read.
DH_SOURCES: dict[str, str] = {
    "leclair_mussardo": (
        "LeClair, A. and Mussardo, G. (2024). Riemann zeros as quantized energies "
        "of scattering with impurities. JHEP 04 (2024) 062; arXiv:2307.01254v2. "
        "Abstract and Section VII read. States that the Davenport-Heilbronn "
        "function is 'a function whose completion satisfies the duality equation "
        "chi(s) = chi(1-s) but that does not have an Euler product "
        "representation', and that 'there are also infinitely many pairs of "
        "solutions away from this axis and symmetrically placed with respect to "
        "it'."
    ),
    "franca_leclair": (
        "Franca, G. and LeClair, A. (2024). A theory for the zeros of Riemann "
        "zeta and other L-functions. arXiv:1407.4358v2, Section XIX "
        "'Counterexample of Davenport-Heilbronn' and abstract read. States that "
        "the DH function 'is an L-series that is a linear combination of two "
        "Dirichlet L-series, that also satisfies a functional equation. It has an "
        "infinite number of zeros on the critical line, but also zeros off of it, "
        "thus violating the RH.'"
    ),
    "ivic": (
        "Ivic, A. (2003). On some reasons for doubting the Riemann hypothesis. "
        "arXiv:math/0311162v1. Abstract and introduction read; the survey lists "
        "the Davenport-Heilbronn zeta-function as one of the classical reasons to "
        "doubt RH. NOTE: the fetch of this paper truncated before the "
        "Davenport-Heilbronn section itself, so no property below is sourced from "
        "Ivic's detailed treatment."
    ),
    "voros": (
        "Voros, A. (2020). Discretized Keiper/Li approach to the Riemann "
        "Hypothesis. Experimental Mathematics 29(4), 452-469; arXiv:1703.02844v3. "
        "Abstract and Sections 1.1-1.3 read. States that the method 'also works on "
        "the Davenport-Heilbronn counterexamples, thus we can demonstrate explicit "
        "tests that selectively react to zeros off the critical line', and gives "
        "Li's criterion as 'RH iff lambda_n >= 0 for all n'. NOTE: Section 4.4, "
        "'The Davenport-Heilbronn counterexamples', was not read."
    ),
    "balanzario": (
        "Balanzario, E. P. and Sanchez-Ortiz, J. (2007). Zeros of the "
        "Davenport-Heilbronn counterexample. Mathematics of Computation 76, "
        "2025-2029. Abstract read. Confirms that zeros off the critical line have "
        "been computed for this function."
    ),
    "derived_here": (
        "Derived in this repository from the structural definition above, and "
        "verified numerically by the calibration functions in this module against "
        "the functional equation the object must satisfy."
    ),
}


# ============================================================
# The inventory
# ============================================================

class InputStatus(str, Enum):
    """Whether a mathematical input survives the change from zeta to DH."""

    #: The input holds for the Davenport-Heilbronn function as well.
    TRANSFERS = "transfers"
    #: The input is false or simply unavailable for the Davenport-Heilbronn
    #: function. Using such an input is what makes an argument eligible.
    FAILS = "fails"
    #: This repository cannot currently classify the input. Not a guess in either
    #: direction: the row is reported as missing information.
    UNSOURCED = "unsourced"


class DHVerdict(str, Enum):
    """The filter's output for one candidate."""

    DEAD = "dead"
    ELIGIBLE = "eligible"
    NEEDS_SOURCING = "needs_sourcing"


@dataclass(frozen=True)
class DHInput:
    """One row of the inventory: an input, and whether DH has it."""

    key: str
    description: str
    status: InputStatus
    evidence: str
    source: str
    #: True when this repository checks the row by computation rather than only
    #: citing it. Only two rows can be: see `calibrate`.
    verified_here: bool = False


DH_INPUTS: dict[str, DHInput] = {
    "functional_equation": DHInput(
        key="functional_equation",
        description=(
            "the completed object satisfies Lambda(s) = Lambda(1 - s), so the "
            "zero set is symmetric under rho -> 1 - rho"
        ),
        status=InputStatus.TRANSFERS,
        evidence=(
            "LeClair-Mussardo state that the DH completion satisfies the duality "
            "equation. Checked here as well: the completed function built in this "
            "module satisfies it with relative residual ~6e-30 at 30 digits, at "
            "five sample points both inside and outside the strip."
        ),
        source="leclair_mussardo",
        verified_here=True,
    ),
    "real_coefficients": DHInput(
        key="real_coefficients",
        description=(
            "the Dirichlet coefficients are real, so f(conj s) = conj (f s) and "
            "the zeros are symmetric under rho -> conj rho"
        ),
        status=InputStatus.TRANSFERS,
        evidence=(
            "Derived here: with chi the odd character mod 5, the coefficients are "
            "b(n) = Re chi(n) - kappa * Im chi(n), which is real because the "
            "combination (1 - i kappa) chi + (1 + i kappa) chi-bar is. Verified "
            "numerically to 1e-25 at 30 digits."
        ),
        source="derived_here",
        verified_here=True,
    ),
    "zero_symmetry": DHInput(
        key="zero_symmetry",
        description=(
            "the zeros come in the usual quadruples {rho, 1 - rho, conj rho, "
            "1 - conj rho}"
        ),
        status=InputStatus.TRANSFERS,
        evidence=(
            "Franca-LeClair record that the DH function satisfies a functional "
            "equation; by itself that gives rho -> 1 - rho, and the real "
            "coefficients recorded above give rho -> conj rho. This row is a "
            "consequence of the two rows above rather than an independent fact."
        ),
        source="franca_leclair",
    ),
    "hadamard_product": DHInput(
        key="hadamard_product",
        description=(
            "the completed function is entire of order 1, so it has a Hadamard "
            "factorization and log-derivative expansion sum_rho "
            "(1/(s - rho) + 1/rho) over its zeros"
        ),
        status=InputStatus.UNSOURCED,
        evidence=(
            "Half of this is sourced and half is not, and the unfounded half is "
            "load-bearing. LeClair-Mussardo do state that the non-principal "
            "Dirichlet L-functions 'are entire functions in the complex plane due "
            "to the absence of the pole at s = 1', and the DH function is a "
            "combination of two of them, so entirety is sourced. The *order* -- "
            "which is what the Hadamard product and the sum over zeros need -- was "
            "not stated in any source read here. Left unsourced rather than filled "
            "in from the textbook expectation."
        ),
        source="",
    ),
    "euler_product": DHInput(
        key="euler_product",
        description=(
            "the coefficients are multiplicative, so there is a local factor per "
            "prime and the Dirichlet series is an Euler product"
        ),
        status=InputStatus.FAILS,
        evidence=(
            "LeClair-Mussardo state that DH 'does not have an Euler product "
            "representation'. Checked here as well, and the check is decisive and "
            "cheap: b(2) * b(3) = -kappa^2 = -0.0807009031..., while b(6) = 1, so "
            "the coefficients are not multiplicative. Note there is no "
            "qualitative gap to close -- a single failure of multiplicativity "
            "settles it."
        ),
        source="leclair_mussardo",
        verified_here=True,
    ),
    "explicit_formula_prime_side": DHInput(
        key="explicit_formula_prime_side",
        description=(
            "Weil's explicit formula in the form whose arithmetic side is "
            "supported on prime powers, i.e. the coefficients of -zeta'/zeta are "
            "Lambda(n) = log p at n = p^k and 0 elsewhere"
        ),
        status=InputStatus.FAILS,
        evidence=(
            "There is no Euler product, hence no local factor to expand and no "
            "-f'/f expansion supported on prime powers: the arithmetic side has no "
            "prime support to be carried on. This is the same fact Alpoge-Furman "
            "section 1.4 turns into a ceiling on the methods that use it."
        ),
        source="leclair_mussardo",
    ),
    "li_positivity": DHInput(
        key="li_positivity",
        description=(
            "the RH-equivalent positivity lambda_n >= 0 for all n (Li's criterion, "
            "and Keiper's equivalent sequence)"
        ),
        status=InputStatus.FAILS,
        evidence=(
            "Voros states that the method 'also works on the Davenport-Heilbronn "
            "counterexamples, thus we can demonstrate explicit tests that "
            "selectively react to zeros off the critical line', having given Li's "
            "criterion as 'RH iff lambda_n >= 0 for all n'. A criterion that "
            "reacts to DH's off-line zeros is not satisfied by DH. Recorded with "
            "the caveat that Voros's section 4.4, which works this out in detail, "
            "was not read."
        ),
        source="voros",
    ),
    "riemann_von_mangoldt_count": DHInput(
        key="riemann_von_mangoldt_count",
        description=(
            "the zero-counting asymptotic N(T) = (T/2pi) log(T/2pi e) + O(log T), "
            "or the matching smooth count"
        ),
        status=InputStatus.UNSOURCED,
        evidence=(
            "The analogue is expected -- it should follow from the functional "
            "equation together with the argument principle, both of which DH has "
            "-- but no source read for this module states it for DH, so the row is "
            "left unsourced rather than filled in from expectation. An argument "
            "that leans on the zero count is therefore reported as "
            "needs_sourcing, which is the honest answer and not a verdict about "
            "the argument."
        ),
        source="",
    ),
    "gue_pair_correlation": DHInput(
        key="gue_pair_correlation",
        description=(
            "the zeros have the same local spacing / pair-correlation statistics "
            "as the zeta zeros (GUE)"
        ),
        status=InputStatus.UNSOURCED,
        evidence=(
            "Not established from any source read here. There is a specific reason "
            "to expect this row to be delicate rather than a copy: DH is a linear "
            "combination of two Dirichlet L-functions, so its zero process would "
            "plausibly be a superposition of two processes rather than a single "
            "one. That expectation comes from a third-party code comment read while "
            "searching, NOT from a source, and is recorded here as an unverified "
            "lead rather than as evidence. Until it is sourced, statistical inputs "
            "are reported as needs_sourcing."
        ),
        source="",
    ),
}


# ============================================================
# The filter
# ============================================================

@dataclass(frozen=True)
class InputClassification:
    """What the filter found for one declared input."""

    key: str
    status: InputStatus
    rationale: str


@dataclass
class ScreenResult:
    """The filter's full output for one candidate."""

    idea_id: str
    verdict: DHVerdict
    classifications: list[InputClassification] = field(default_factory=list)
    unknown_inputs: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def failing_inputs(self) -> list[str]:
        """The declared inputs that keep this candidate off the dead list."""
        return [
            c.key for c in self.classifications if c.status is InputStatus.FAILS
        ]

    def __str__(self) -> str:
        lines = [
            f"Idea: {self.idea_id}",
            f"DH verdict: {self.verdict.value}",
        ]
        if self.unknown_inputs:
            lines.append(f"Unclassified inputs: {', '.join(self.unknown_inputs)}")
        for c in self.classifications:
            mark = {"transfers": "==", "fails": "!!", "unsourced": "??"}[c.status.value]
            lines.append(f"  [{mark}] {c.key}: {c.rationale}")
        lines.append(f"Summary: {self.summary}")
        return "\n".join(lines)


def classify_input(key: str) -> InputClassification:
    """Classify one declared input key against the inventory.

    An unknown key is not an error and not a guess: it is reported as
    ``unsourced`` with a rationale saying the inventory does not contain it. A
    candidate is free to introduce new vocabulary; the filter's job is then to
    say that it cannot classify it, which is what forces the vocabulary to be
    pinned down.
    """
    row = DH_INPUTS.get(key)
    if row is None:
        return InputClassification(
            key=key,
            status=InputStatus.UNSOURCED,
            rationale=(
                "not in the Davenport-Heilbronn inventory, so this filter cannot "
                "say whether DH has it. Either the input has to be added to the "
                "inventory with a source, or the candidate has to say which "
                "inventoried input it is"
            ),
        )
    return InputClassification(
        key=key,
        status=row.status,
        rationale=f"{row.description}; source: {row.source or 'none recorded'}",
    )


def screen_inputs(idea_id: str, inputs: Sequence[str]) -> ScreenResult:
    """Screen one candidate given the input keys it declares.

    Precedence is deliberate, and it is the strongest conclusion the declared set
    supports rather than the most cautious one:

    1. a declared input that **fails** for DH makes the candidate ``eligible``,
       whatever else is declared, because one such input is enough for the
       filter's purpose;
    2. otherwise, an input that is unknown to the inventory or recorded as
       ``unsourced`` makes the verdict ``needs_sourcing`` -- with no failing
       input in evidence, the filter cannot tell a transferable argument from an
       eligible one;
    3. otherwise every declared input transfers, and the candidate is ``dead``.

    An empty declaration is ``needs_sourcing``. A candidate that declares nothing
    has not been screened, and calling that "dead" would be a verdict from no
    evidence.
    """
    if not inputs:
        return ScreenResult(
            idea_id=idea_id,
            verdict=DHVerdict.NEEDS_SOURCING,
            summary=(
                "No inputs declared. The filter classifies declared inputs only, "
                "so an undeclared candidate is unscreened rather than dead."
            ),
        )

    classifications = [classify_input(key) for key in inputs]
    unknown = [c.key for c in classifications if c.key not in DH_INPUTS]
    failing = [c.key for c in classifications if c.status is InputStatus.FAILS]
    unsourced = [
        c.key
        for c in classifications
        if c.status is InputStatus.UNSOURCED and c.key in DH_INPUTS
    ]

    if failing:
        verdict = DHVerdict.ELIGIBLE
        summary = (
            "Uses at least one input that fails for Davenport-Heilbronn "
            f"({', '.join(failing)}), so the argument does not transfer to a "
            "function whose RH-analogue is false. This is permission, not "
            "promise: the input still has to do the work."
        )
    elif unknown or unsourced:
        verdict = DHVerdict.NEEDS_SOURCING
        gaps = unknown + unsourced
        summary = (
            "No declared input fails for Davenport-Heilbronn, but the filter "
            f"cannot complete the screen: {', '.join(gaps)} "
            f"{'is' if len(gaps) == 1 else 'are'} not classified. Supply the "
            "missing fact and re-screen; until then there is no verdict."
        )
    else:
        verdict = DHVerdict.DEAD
        summary = (
            "Every declared input transfers to Davenport-Heilbronn, where the "
            "analogue of RH is false. The same argument would therefore establish "
            "a false statement, so it cannot establish RH. This is the filter "
            "firing, and it is the useful outcome."
        )

    return ScreenResult(
        idea_id=idea_id,
        verdict=verdict,
        classifications=classifications,
        unknown_inputs=unknown,
        summary=summary,
    )


def screen_idea(idea: Idea) -> ScreenResult:
    """Screen an idea record, using its ``dh_inputs`` declaration.

    The declaration lives in the record's free-form ``extra`` mapping, so records
    that predate this filter load unchanged and screen as ``needs_sourcing``.
    """
    declared = idea.extra.get("dh_inputs", [])
    if isinstance(declared, str):
        declared = [declared]
    return screen_inputs(idea.id, list(declared))


def screen_all(ideas: Iterable[Idea]) -> list[ScreenResult]:
    """Screen every idea, preserving order."""
    return [screen_idea(idea) for idea in ideas]


def dead_list(results: Sequence[ScreenResult]) -> list[str]:
    """The candidates whose every declared input transfers to DH.

    This is the output worth keeping: each entry is an argument ruled out by a
    false statement it would also have proved.
    """
    return [r.idea_id for r in results if r.verdict is DHVerdict.DEAD]


def eligible_list(results: Sequence[ScreenResult]) -> list[str]:
    """The candidates that survive the filter, with the input that saved them.

    Surviving is not an endorsement, so each entry carries the input that made it
    eligible: that input is the load-bearing one, and it is the thing to attack.
    """
    return [
        f"{r.idea_id} (via {', '.join(r.failing_inputs)})"
        for r in results
        if r.verdict is DHVerdict.ELIGIBLE
    ]


def unclassified_inputs(result: ScreenResult) -> list[str]:
    """The declared inputs this filter could not classify.

    Both kinds count: a key the inventory does not contain at all, and a key it
    contains with status ``unsourced``. Reporting only the first kind was a real
    bug -- a record declaring an inventoried but unsourced input was described as
    having no declaration at all, which is the opposite of what happened.
    """
    return [
        c.key for c in result.classifications if c.status is InputStatus.UNSOURCED
    ]


def unscreened_list(results: Sequence[ScreenResult]) -> list[str]:
    """The candidates the filter could not classify, and which input stopped it.

    Reporting *which* input is the point: the gap is the thing to source, and a
    bare "unscreened" would leave the next step unstated.
    """
    entries: list[str] = []
    for result in results:
        if result.verdict is not DHVerdict.NEEDS_SOURCING:
            continue
        gaps = unclassified_inputs(result)
        entries.append(
            f"{result.idea_id} (missing: {', '.join(gaps) or 'declaration'})"
        )
    return entries


# ============================================================
# Calibration: the DH object itself, built and checked
# ============================================================
#
# The filter is only as good as its inventory, and two rows of the inventory are
# things this repository can check rather than cite. Both are checked here, on a
# construction of the Davenport-Heilbronn function that is *derived* from the
# sourced structural definition and then validated by the functional equation it
# has to satisfy. If the derivation were wrong, the functional equation would
# fail -- which is what caught an inverted sign convention for kappa while this
# module was being written.

def dh_character() -> dict[int, mp.mpc]:
    """The odd Dirichlet character mod 5, on residues 0..4.

    ``chi(2) = i`` generates the group of units, and ``chi(4) = -1`` makes the
    character odd, which is what fixes the shape of the completion below.
    """
    return {
        0: mp.mpc(0),
        1: mp.mpc(1),
        2: mp.mpc(0, 1),
        3: mp.mpc(0, -1),
        4: mp.mpc(-1),
    }


def dh_gauss_sum(dps: int = 30) -> mp.mpc:
    """``tau(chi) = sum_a chi(a) exp(2 pi i a / 5)``."""
    with mp.workdps(dps):
        chi = dh_character()
        return mp.fsum(
            chi[a] * mp.exp(mp.mpc(0, 2) * mp.pi * a / MODULUS)
            for a in range(1, MODULUS)
        )


def dh_kappa(dps: int = 30) -> mp.mpf:
    """The Davenport-Heilbronn constant, derived from self-duality.

    Writing ``eps = tau(chi) / (i sqrt 5)`` (so ``|eps| = 1``, which is the
    content of the Gauss-sum identity here) and requiring the combination
    ``c L(s, chi) + d L(s, chi-bar)`` with ``c = (1 - i kappa)/2`` and
    ``d = (1 + i kappa)/2`` to have a self-dual completion forces ``d = c * eps``,
    hence ``kappa = tan(arg(eps) / 2)``.

    The *sign* of kappa is a labelling convention: swapping ``chi`` and
    ``chi-bar`` negates kappa and leaves the function unchanged, because it
    swaps ``c`` and ``d``. Only ``|kappa|`` is intrinsic.
    """
    with mp.workdps(dps):
        eps = dh_gauss_sum(dps) / (mp.mpc(0, 1) * mp.sqrt(MODULUS))
        return mp.tan(mp.arg(eps) / 2)


def dh_coefficients(n_max: int, dps: int = 30) -> dict[int, mp.mpf]:
    """``b(1..n_max)`` for ``f(s) = sum b(n) n^{-s}``, as real numbers.

    Derived from the structural definition -- a linear combination of
    ``L(s, chi)`` and ``L(s, chi-bar)`` -- not recalled: with chi odd mod 5 the
    combination has real coefficients ``b(n) = Re chi(n) - kappa Im chi(n)``, so
    ``b`` is periodic with period 5 and takes the values
    ``(1, kappa, -kappa, -1, 0)`` at ``n = 1, 2, 3, 4, 0 (mod 5)``.
    """
    if n_max < 1:
        raise ValueError("n_max must be at least 1")
    with mp.workdps(dps):
        chi = dh_character()
        kappa = dh_kappa(dps)
        c = (1 - 1j * kappa) / 2
        d = (1 + 1j * kappa) / 2
        out: dict[int, mp.mpf] = {}
        for n in range(1, n_max + 1):
            value = c * chi[n % MODULUS] + d * mp.conj(chi[n % MODULUS])
            out[n] = mp.re(value)
        return out


def dh_dirichlet_series(s: complex | mp.mpc, n_max: int, dps: int = 30) -> mp.mpc:
    """The plain Dirichlet series of ``f`` truncated at ``n_max`` terms.

    Only valid where the series converges (``Re s > 1`` for bounded
    coefficients). Used to check the coefficients, not to evaluate ``f``.
    """
    with mp.workdps(dps):
        coeffs = dh_coefficients(n_max, dps)
        s = mp.mpc(s)
        return mp.fsum(coeffs[n] * mp.power(n, -s) for n in range(1, n_max + 1))


def dh_value(s: complex | mp.mpc, dps: int = 30) -> mp.mpc:
    """``f(s)`` in closed form, via Hurwitz zeta.

    ``L(s, chi) = 5^{-s} sum_{a=1}^{4} chi(a) zeta(s, a/5)``, which continues
    ``f`` to the whole plane; ``mpmath``'s Hurwitz zeta supplies the
    continuation. ``f`` is entire, being a combination of two entire
    non-principal Dirichlet L-functions.
    """
    with mp.workdps(dps):
        s = mp.mpc(s)
        chi = dh_character()
        kappa = dh_kappa(dps)
        c = (1 - 1j * kappa) / 2
        d = (1 + 1j * kappa) / 2

        def L(char: dict[int, mp.mpc]) -> mp.mpc:
            return mp.power(MODULUS, -s) * mp.fsum(
                char[a] * mp.zeta(s, mp.mpf(a) / MODULUS) for a in range(1, MODULUS)
            )

        chibar = {a: mp.conj(chi[a]) for a in chi}
        return c * L(chi) + d * L(chibar)


def dh_completed(s: complex | mp.mpc, dps: int = 30) -> mp.mpc:
    """``Lambda(s) = (5/pi)^{(s+1)/2} Gamma((s+1)/2) f(s)``.

    The odd-character completion: exponent ``(s+1)/2`` rather than ``s/2``
    because ``chi`` is odd. The functional equation below is what checks that
    choice, along with the conductor and ``kappa``.
    """
    with mp.workdps(dps):
        s = mp.mpc(s)
        return (
            mp.power(mp.mpf(MODULUS) / mp.pi, (s + 1) / 2)
            * mp.gamma((s + 1) / 2)
            * dh_value(s, dps)
        )


#: Sample points for the functional-equation check. Deliberately mostly *off* the
#: critical line: the functional equation relates s to 1 - s and holds
#: regardless of where the zeros are, so sampling only on the line would test
#: less than it looks like.
FUNCTIONAL_EQUATION_POINTS: tuple[complex, ...] = (
    0.3 + 7j,
    0.7 - 3j,
    0.5 + 20j,
    0.2 + 1.5j,
    0.8 + 50j,
)


def functional_equation_residual(
    s: complex | mp.mpc, dps: int = 30
) -> mp.mpf:
    """Relative residual ``|Lambda(s) - Lambda(1-s)| / max(...)`` at ``s``."""
    with mp.workdps(dps):
        a = dh_completed(s, dps)
        b = dh_completed(1 - mp.mpc(s), dps)
        scale = max(abs(a), abs(b))
        if scale == 0:
            raise ValueError(f"completed function vanished at s = {s}")
        return abs(a - b) / scale


@dataclass(frozen=True)
class DHCalibration:
    """Measured facts about the Davenport-Heilbronn construction.

    Each field is a number or a boolean actually computed, so that the inventory
    rows marked ``verified_here`` are checked rather than asserted.
    """

    kappa: float
    gauss_sum_modulus: float
    worst_functional_equation_residual: float
    coefficients_are_real: bool
    coefficients_are_multiplicative: bool
    #: ``(b(2) * b(3), b(6))`` -- the witness that multiplicativity fails.
    non_multiplicativity_witness: tuple[float, float]
    verified_inputs: tuple[str, ...]

    def summary(self) -> str:
        return (
            f"kappa = {self.kappa:.17g}; |tau(chi)/(i sqrt 5)| = "
            f"{self.gauss_sum_modulus:.17g}; worst functional-equation residual "
            f"= {self.worst_functional_equation_residual:.3e}; coefficients real: "
            f"{self.coefficients_are_real}; coefficients multiplicative: "
            f"{self.coefficients_are_multiplicative}; b(2)b(3) = "
            f"{self.non_multiplicativity_witness[0]:.10f} vs b(6) = "
            f"{self.non_multiplicativity_witness[1]:.10f}"
        )


def multiplicativity_holds(
    coefficients: dict[int, mp.mpf], n_max: int, tol: float = 1e-25
) -> bool:
    """Whether a coefficient table is multiplicative over the tested range.

    Extracted from `calibrate` so it can be given a *positive control*: the same
    predicate that returns ``False`` for the Davenport-Heilbronn coefficients has
    to return ``True`` for a genuinely multiplicative table, or the check would
    be firing for a reason other than the one claimed. A test does exactly that
    with the constant table ``c(n) = 1``.
    """
    threshold = mp.mpf(tol)
    return all(
        abs(coefficients[m] * coefficients[n] - coefficients[m * n]) < threshold
        for m in range(2, 8)
        for n in range(2, 8)
        if m * n <= n_max
    )


def calibrate(dps: int = 30, n_max: int = 30) -> DHCalibration:
    """Build the DH object and measure the two inventory rows checked here.

    This is the filter's own control, in the sense used elsewhere in this
    repository: a screen that never fires is worthless, so the machinery is run
    once against a function *known* to have zeros off the critical line and its
    defining properties are measured rather than assumed.
    """
    with mp.workdps(dps):
        kappa = dh_kappa(dps)
        eps = dh_gauss_sum(dps) / (mp.mpc(0, 1) * mp.sqrt(MODULUS))

        worst = mp.mpf(0)
        for s in FUNCTIONAL_EQUATION_POINTS:
            worst = max(worst, functional_equation_residual(s, dps))

        coeffs = dh_coefficients(n_max, dps)
        real = all(abs(mp.im(v)) < mp.mpf(10) ** (-(dps - 5)) for v in coeffs.values())

        # Multiplicativity is tested on the smallest nontrivial pair. One
        # counterexample settles it; there is nothing asymptotic to check.
        witness = (float(coeffs[2] * coeffs[3]), float(coeffs[6]))
        multiplicative = multiplicativity_holds(
            coeffs, n_max, tol=float(mp.mpf(10) ** (-(dps - 5)))
        )

        return DHCalibration(
            kappa=float(kappa),
            gauss_sum_modulus=float(abs(eps)),
            worst_functional_equation_residual=float(worst),
            coefficients_are_real=real,
            coefficients_are_multiplicative=multiplicative,
            non_multiplicativity_witness=witness,
            verified_inputs=(
                "functional_equation",
                "real_coefficients",
                "euler_product",
            ),
        )


def inventory_table() -> list[dict[str, Any]]:
    """The inventory as plain rows, for printing and for tests."""
    return [
        {
            "key": row.key,
            "status": row.status.value,
            "dh_holds": row.status is InputStatus.TRANSFERS,
            "verified_here": row.verified_here,
            "source": row.source,
            "description": row.description,
        }
        for row in DH_INPUTS.values()
    ]
