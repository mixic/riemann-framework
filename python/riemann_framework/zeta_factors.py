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
A screen for frameworks whose zeta function contains `zeta` as a factor.

The companion to `dh_filter`, asking a different question. `dh_filter` asks
whether a candidate's *inputs* survive the change from `zeta` to a function whose
RH-analogue is false. This module asks whether a proposed framework's zeta
function is a **superset of `zeta`** -- because if it is, then proving the
framework's RH-analogue proves RH as a special case, which makes the framework
strictly harder than the problem it was meant to simplify.

    zeta_{Q(i)}(s) = zeta(s) * L(s, chi_-4)
    zeta_{Q(sqrt -3)}(s) = zeta(s) * L(s, chi_-3)

Both are products, and the check below verifies the declared factorisation
against each framework's own Dirichlet series rather than taking it on trust.

The three outcomes, and what each does and does not mean
-------------------------------------------------------
``strictly_harder``
    ``Z = zeta * W``. A proof of RH-for-``Z`` implies RH, so this is a *valid*
    target -- but a dominated one. Any proof of RH-for-``Z`` contains a proof of
    RH as a special case, so passing to ``Z`` cannot have made the problem
    easier. It is a route that has made the problem strictly bigger.

``separate_target``
    no declared factor contains ``zeta``. Proving RH-for-``Z`` does **not**
    imply RH, so the framework does not deliver the goal at all. What is needed
    is a separate transfer step from ``Z`` back to ``zeta``, and that step is
    the whole content of the proposal. A framework with no transfer step
    recorded is reported as exactly that.

``no_euler_product``
    the object has no Euler product, so factor containment is not even
    well-posed. This is the Davenport-Heilbronn / Epstein family -- the one the
    repository's other filter is built on.

``is_the_base_case``
    ``Z = zeta``. The control, included so the screen is not vacuous: it must
    recognise the target itself. Note that ``zeta`` trivially "is a factor of
    itself", which is why this needs its own verdict rather than being reported
    as strictly harder.

What this screen is not
-----------------------
It does not find routes. Neither ``strictly_harder`` nor ``separate_target`` is
an endorsement; the first is dominated and the second is incomplete. What the
screen does is force the transfer step into the open, which is the step that
ideas in this family almost always leave implicit.

Sourcing
--------
The two factorisations are standard, but the general theorem was not read from a
source in this session, so it is not cited as if it had been. What *is* done here
is stronger for the two instances that matter: `verify_factorization` checks each
declared product against the framework's own series over the first
`DEFAULT_N_MAX` coefficients. `r2(n)/4 = sum_{d|n} chi_-4(d)` and
`r3(n)/6 = sum_{d|n} chi_-3(d)` are classical representation identities; they are
verified rather than quoted.

The Epstein row is different: it is cited, not verified -- see its record.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Sequence

from .dh_filter import dh_coefficients


#: How many Dirichlet coefficients the factorisation check compares by default.
#: Two thousand is far more than enough to catch a wrong local factor at any
#: prime, and it keeps the whole screen under a second.
DEFAULT_N_MAX = 2000


# ============================================================
# Characters and representation counts
# ============================================================

def chi_minus_4(n: int) -> int:
    """The odd character mod 4: `1, 0, -1, 0, 1, 0, -1, 0, ...`.

    The unique non-principal character mod 4. This is the character in the
    table quoted when Dirichlet L-functions are introduced, and it is the one
    attached to the Gaussian integers.
    """
    if n % 2 == 0:
        return 0
    return 1 if n % 4 == 1 else -1


def chi_minus_3(n: int) -> int:
    """The odd character mod 3: `1, -1, 0, 1, -1, 0, ...`.

    Attached to the Eisenstein integers, `Z[omega]`.
    """
    if n % 3 == 0:
        return 0
    return 1 if n % 3 == 1 else -1


def gaussian_representation_counts(n_max: int) -> list[int]:
    """`r2(n)/4` for `n = 1..n_max`, indexed from 1.

    `r2(n)` counts representations of `n` as `a^2 + b^2`, weighted by the
    Gaussian-integer units. The claim checked in the tests is
    `r2(n)/4 = sum_{d|n} chi_-4(d)`, so this returns the *normalised* count: the
    declared convolution produces `sum_{d|n} chi_-4(d)` exactly, and returning
    the raw `r2` here would make the check fail against its own declaration.

    The enumeration bound is `sqrt(n_max)`, since `a^2 + b^2 = n` forces
    `|a| <= sqrt(n)`. (The Eisenstein version below needs a larger bound, for a
    reason worth remembering: there the cross term relaxes it.)
    """
    counts = [0] * (n_max + 1)
    bound = int(n_max**0.5) + 1
    for a in range(-bound, bound + 1):
        for b in range(-bound, bound + 1):
            value = a * a + b * b
            if 0 < value <= n_max:
                counts[value] += 1
    for n in range(1, n_max + 1):
        if counts[n] % 4 != 0:
            raise AssertionError(f"r2({n}) = {counts[n]} is not divisible by 4")
        counts[n] //= 4
    return counts


def eisenstein_representation_counts(n_max: int) -> list[int]:
    """`r3(n)/6` for `n = 1..n_max`, where `r3` counts `x^2 + xy + y^2`.

    The claim checked in the tests is `r3(n)/6 = sum_{d|n} chi_-3(d)`.

    The enumeration bound is `sqrt(2 n_max)`, NOT `sqrt(n_max)`. Because of the
    cross term, `x^2 + xy + y^2 >= (x^2 + y^2)/2`, so `|x|` can reach
    `sqrt(2n)`. Using the smaller bound silently produces a wrong table -- it
    was a real bug in this module's first draft, caught by the identity check
    failing at `n = 3781`.

    The division by 6 is asserted rather than floored, for the same reason: a
    silent `//` would hide exactly the kind of incomplete enumeration that
    caused that bug.
    """
    counts = [0] * (n_max + 1)
    bound = int((2 * n_max) ** 0.5) + 2
    for x in range(-bound, bound + 1):
        for y in range(-bound, bound + 1):
            value = x * x + x * y + y * y
            if 0 < value <= n_max:
                counts[value] += 1
    for n in range(1, n_max + 1):
        if counts[n] % 6 != 0:
            raise AssertionError(f"r3({n}) = {counts[n]} is not divisible by 6")
        counts[n] //= 6
    return counts


# ============================================================
# Named factors and Dirichlet convolution
# ============================================================

@dataclass(frozen=True)
class ZetaFactor:
    """One named factor of a proposed zeta function."""

    key: str
    description: str
    #: True when this factor's zeta function has the zeros of `zeta`.
    contains_zeta: bool
    coefficient: Callable[[int], int]
    source: str


def _one_factor(n: int) -> int:
    return 1


def _unit_factor(n: int) -> int:
    return 1 if n == 1 else 0


FACTORS: dict[str, ZetaFactor] = {
    "zeta": ZetaFactor(
        key="zeta",
        description="the Riemann zeta function itself",
        contains_zeta=True,
        coefficient=_one_factor,
        source="definition",
    ),
    "dirichlet_L_chi4": ZetaFactor(
        key="dirichlet_L_chi4",
        description=(
            "L(s, chi_-4) = beta(s), the Dirichlet beta function: the odd "
            "character mod 4, attached to the Gaussian integers"
        ),
        contains_zeta=False,
        coefficient=chi_minus_4,
        source="definition",
    ),
    "dirichlet_L_chi3": ZetaFactor(
        key="dirichlet_L_chi3",
        description=(
            "L(s, chi_-3): the odd character mod 3, attached to the Eisenstein "
            "integers Z[omega]"
        ),
        contains_zeta=False,
        coefficient=chi_minus_3,
        source="definition",
    ),
    "unit": ZetaFactor(
        key="unit",
        description="the trivial factor 1, whose coefficients are (1, 0, 0, ...)",
        contains_zeta=False,
        coefficient=_unit_factor,
        source="definition",
    ),
}


def dirichlet_convolution(
    left: Sequence[int], right: Sequence[int], n_max: int
) -> list[int]:
    """Dirichlet convolution of two coefficient tables indexed from 1.

    `(f * g)(n) = sum_{d | n} f(d) g(n/d)`, which is what multiplication of
    Dirichlet series does to coefficients. Both inputs are read at indices
    `1..n_max` and the result is returned in the same form.
    """
    out = [0] * (n_max + 1)
    for d in range(1, n_max + 1):
        coefficient = left[d]
        if coefficient == 0:
            continue
        for m in range(1, n_max // d + 1):
            out[d * m] += coefficient * right[m]
    return out


def factor_coefficients(keys: Sequence[str], n_max: int) -> list[int]:
    """Coefficients of the product of the named factors, by convolution."""
    table = [0] * (n_max + 1)
    table[1] = 1
    for key in keys:
        factor = FACTORS[key]
        series = [0] + [factor.coefficient(n) for n in range(1, n_max + 1)]
        table = dirichlet_convolution(table, series, n_max)
    return table


# ============================================================
# Frameworks
# ============================================================

class FrameworkVerdict(str, Enum):
    """What the containment screen concluded about one framework."""

    IS_THE_BASE_CASE = "is_the_base_case"
    STRICTLY_HARDER = "strictly_harder"
    SEPARATE_TARGET = "separate_target"
    NO_EULER_PRODUCT = "no_euler_product"


@dataclass(frozen=True)
class Framework:
    """A proposed zeta function, with its declared factorisation.

    `factors` is the declaration: the screen checks it rather than trusting it.
    `series` supplies the framework's own Dirichlet coefficients when they can
    be computed here; `None` means the factorisation is cited rather than
    verified, and the screen says so instead of implying a check happened.

    `transfer_step` is where a framework without a `zeta` factor has to earn its
    place: the argument by which its RH-analogue would say anything about `zeta`.
    An empty string is reported as the missing piece, not as a defect.
    """

    id: str
    description: str
    factors: tuple[str, ...]
    has_euler_product: bool
    source: str
    series: Callable[[int], list[int]] | None = None
    transfer_step: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.has_euler_product and self.factors:
            raise ValueError(
                f"{self.id}: declares factors {self.factors} but has no Euler "
                "product. A factorisation is a multiplicative statement; the "
                "two cannot both hold, and silently ignoring one would make the "
                "screen's verdict arbitrary."
            )
        for key in self.factors:
            if key not in FACTORS:
                raise ValueError(f"{self.id}: unknown factor {key!r}")

    def factor_chain(self) -> str:
        """The declared product as a printable string."""
        if not self.factors:
            return "(no Euler product)"
        return " * ".join(self.factors)


FRAMEWORKS: tuple[Framework, ...] = (
    Framework(
        id="riemann_zeta",
        description="the Riemann zeta function, the target itself",
        factors=("zeta",),
        has_euler_product=True,
        source="definition",
        series=lambda n_max: [0] + [1] * n_max,
    ),
    Framework(
        id="dedekind_gaussian",
        description=(
            "zeta_{Q(i)}, the Dedekind zeta function of the Gaussian integers: "
            "prime ideals of Z[i], equivalently the square lattice"
        ),
        factors=("zeta", "dirichlet_L_chi4"),
        has_euler_product=True,
        source="standard factorisation; verified here over the coefficient range",
        series=gaussian_representation_counts,
        notes=(
            "The three splitting cases -- p = 1 mod 4 splits, p = 3 mod 4 is "
            "inert, p = 2 ramifies -- ARE the local factors of this product. "
            "The declared factorisation is checked against r2(n)/4 below."
        ),
    ),
    Framework(
        id="dedekind_eisenstein",
        description=(
            "zeta_{Q(sqrt -3)}, the Dedekind zeta function of the Eisenstein "
            "integers Z[omega]"
        ),
        factors=("zeta", "dirichlet_L_chi3"),
        has_euler_product=True,
        source="standard factorisation; verified here over the coefficient range",
        series=eisenstein_representation_counts,
        notes=(
            "Ramified at 3 rather than at 2, and otherwise the same story as "
            "the Gaussian case."
        ),
    ),
    Framework(
        id="dirichlet_L_chi4_alone",
        description="L(s, chi_-4) = beta(s) on its own, with no zeta factor",
        factors=("dirichlet_L_chi4",),
        has_euler_product=True,
        source="definition",
        series=lambda n_max: [0] + [chi_minus_4(n) for n in range(1, n_max + 1)],
        notes=(
            "A separate target. RH for beta(s) is not known and does not imply "
            "RH, so this framework needs a transfer step to be a route to RH."
        ),
    ),
    Framework(
        id="davenport_heilbronn",
        description=(
            "the Davenport-Heilbronn function, the standard counterexample "
            "whose RH-analogue is false"
        ),
        factors=(),
        has_euler_product=False,
        source="LeClair-Mussardo; see docs/dh_filter.md",
        notes=(
            "No Euler product, so it has no local factors and containment is not "
            "well-posed. Its coefficients are independently available from "
            "dh_filter.dh_coefficients, which the tests compare against."
        ),
    ),
    Framework(
        id="epstein_rectangular",
        description=(
            "the Epstein zeta function of a rectangular lattice with period "
            "ratio lambda != 1"
        ),
        factors=(),
        has_euler_product=False,
        source="Potter-Titchmarsh (1935); McPhedran, arXiv:1601.01724",
        notes=(
            "CITED, NOT VERIFIED: no rectangular-lattice series is implemented "
            "here, so unlike the two number-field rows this one's lack of an "
            "Euler product is taken from the literature rather than checked. "
            "Note the contrast with the square lattice, which IS the Gaussian "
            "row above because r2 is multiplicative."
        ),
    ),
)


# ============================================================
# Verification
# ============================================================

@dataclass(frozen=True)
class VerificationResult:
    """Whether a declared factorisation reproduces the framework's own series."""

    applicable: bool
    agrees: bool
    n_max: int
    first_disagreement: int | None
    explanation: str


def verify_factorization(
    framework: Framework, n_max: int = DEFAULT_N_MAX
) -> VerificationResult:
    """Check the declared product against the framework's own Dirichlet series.

    This is what stops the screen from being bookkeeping. A wrong local factor
    at any prime shows up as a disagreement in the coefficients, so a declared
    factorisation is *checked* over `1..n_max` rather than accepted.

    Returns `applicable=False` when there is nothing to check -- either the
    framework declares no factors, or its own series is not computable here.
    """
    if not framework.factors:
        return VerificationResult(
            applicable=False,
            agrees=False,
            n_max=n_max,
            first_disagreement=None,
            explanation=(
                "No declared factorisation: the framework has no Euler product, "
                "so there is no product to compare against."
            ),
        )
    if framework.series is None:
        return VerificationResult(
            applicable=False,
            agrees=False,
            n_max=n_max,
            first_disagreement=None,
            explanation=(
                "The factorisation is cited, not verified: this framework's own "
                "series is not implemented here. Reported as unverified rather "
                "than as passing."
            ),
        )

    product = factor_coefficients(framework.factors, n_max)
    own = framework.series(n_max)
    for n in range(1, n_max + 1):
        if product[n] != own[n]:
            return VerificationResult(
                applicable=True,
                agrees=False,
                n_max=n_max,
                first_disagreement=n,
                explanation=(
                    f"Declared product {framework.factor_chain()} gives "
                    f"{product[n]} at n = {n}, but the framework's own series "
                    f"gives {own[n]}."
                ),
            )
    return VerificationResult(
        applicable=True,
        agrees=True,
        n_max=n_max,
        first_disagreement=None,
        explanation=(
            f"Declared product {framework.factor_chain()} reproduces the "
            f"framework's own coefficients for every n <= {n_max}."
        ),
    )


# ============================================================
# The screen
# ============================================================

@dataclass
class FrameworkScreenResult:
    """The containment screen's full output for one framework."""

    framework_id: str
    verdict: FrameworkVerdict
    factor_chain: str
    verification: VerificationResult
    summary: str
    #: The declared factors that carry `zeta`. Empty for a separate target.
    zeta_factors: list[str] = field(default_factory=list)
    notes: str = ""

    def __str__(self) -> str:
        lines = [
            f"Framework: {self.framework_id}",
            f"Declared product: {self.factor_chain}",
            f"Verdict: {self.verdict.value}",
            f"Factorization check: {self.verification.explanation}",
            f"Summary: {self.summary}",
        ]
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)


def screen_framework(
    framework: Framework, n_max: int = DEFAULT_N_MAX
) -> FrameworkScreenResult:
    """Classify one framework by whether its zeta function contains `zeta`.

    Precedence is deliberate. A framework with no Euler product is reported as
    such whatever it declares, because containment is not well-posed without
    local factors. Otherwise the declared factors decide, and `zeta` alone is
    its own case rather than being called strictly harder than itself.
    """
    verification = verify_factorization(framework, n_max)
    chain = framework.factor_chain()
    containing = [k for k in framework.factors if FACTORS[k].contains_zeta]

    if not framework.has_euler_product:
        verdict = FrameworkVerdict.NO_EULER_PRODUCT
        summary = (
            "No Euler product, so there are no local factors to divide and "
            "factor containment is not well-posed. This is the Davenport-"
            "Heilbronn / Epstein family, and the question is not whether the "
            "framework contains zeta but why its zeros leave the line at all."
        )
    elif framework.factors == ("zeta",):
        verdict = FrameworkVerdict.IS_THE_BASE_CASE
        summary = (
            "This IS zeta. Included as the control: a screen for 'contains zeta "
            "as a factor' has to recognise the target itself, since zeta is "
            "trivially a factor of zeta."
        )
    elif containing:
        verdict = FrameworkVerdict.STRICTLY_HARDER
        summary = (
            f"The declared product contains {', '.join(containing)}, so the "
            "zeros of zeta are among the zeros of this framework's zeta "
            "function. A proof of its RH-analogue therefore implies RH -- but "
            "it implies strictly more, so the target is strictly bigger. This "
            "is a valid route that has made the problem harder, not easier: any "
            "proof here contains a proof of RH as a special case."
        )
    else:
        verdict = FrameworkVerdict.SEPARATE_TARGET
        if framework.transfer_step:
            summary = (
                "No declared factor contains zeta, so a proof of this "
                "framework's RH-analogue says nothing about zeta by itself. The "
                f"recorded transfer step is the content: {framework.transfer_step}"
            )
        else:
            summary = (
                "No declared factor contains zeta, so a proof of this "
                "framework's RH-analogue does not imply RH. No transfer step is "
                "recorded, so the framework is currently a separate target "
                "rather than a route to RH. Naming that step is the whole "
                "content of the proposal; its absence is reported, not "
                "penalised."
            )

    return FrameworkScreenResult(
        framework_id=framework.id,
        verdict=verdict,
        factor_chain=chain,
        verification=verification,
        summary=summary,
        zeta_factors=containing,
        notes=framework.notes,
    )


def screen_all(
    frameworks: Sequence[Framework] = FRAMEWORKS, n_max: int = DEFAULT_N_MAX
) -> list[FrameworkScreenResult]:
    """Screen every framework in order."""
    return [screen_framework(f, n_max) for f in frameworks]


def strictly_harder_list(results: Sequence[FrameworkScreenResult]) -> list[str]:
    """Frameworks that contain `zeta`, and so are strictly bigger targets."""
    return [
        f"{r.framework_id} ({r.factor_chain})"
        for r in results
        if r.verdict is FrameworkVerdict.STRICTLY_HARDER
    ]


def separate_target_list(results: Sequence[FrameworkScreenResult]) -> list[str]:
    """Frameworks with no `zeta` factor, and whether a transfer step is recorded."""
    return [
        r.framework_id
        for r in results
        if r.verdict is FrameworkVerdict.SEPARATE_TARGET
    ]


def no_euler_product_list(results: Sequence[FrameworkScreenResult]) -> list[str]:
    """Frameworks where containment is not well-posed."""
    return [
        r.framework_id
        for r in results
        if r.verdict is FrameworkVerdict.NO_EULER_PRODUCT
    ]


def unverified_factorizations(
    results: Sequence[FrameworkScreenResult],
) -> list[str]:
    """Frameworks whose declared product could not be checked here.

    The interesting list for honesty's sake: a `strictly_harder` verdict resting
    on a *cited* rather than verified factorisation is weaker than it looks.
    """
    return [
        r.framework_id
        for r in results
        if r.verdict is FrameworkVerdict.STRICTLY_HARDER
        and not r.verification.agrees
    ]


def davenport_heilbronn_coefficients(n_max: int) -> list[float]:
    """`b(1..n_max)` for the Davenport-Heilbronn function, as plain floats.

    Provided so the no-Euler-product row can be compared against the module that
    already derives those coefficients, rather than reimplementing them.

    Returned as floats rather than ints deliberately: `b(n)` takes the values
    `(1, kappa, -kappa, -1, 0)` and `kappa = 0.284079...` is irrational, so a
    rounded integer table would be all zeros in two of the five residue classes
    and would still "look" like a coefficient table.
    """
    table = dh_coefficients(n_max)
    return [0.0] + [float(table[n]) for n in range(1, n_max + 1)]
