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
The graded prime monoid: what "a number system whose dimension increases under
multiplication" means once it is made precise.

The intuition, and where it comes from
--------------------------------------
Extending `R` to `C` added one dimension and unlocked a great deal. If adding a
dimension did that, perhaps a number system whose dimension grows *as you
multiply* would do more. `docs/spherical_number_systems.md` asks the resulting
question in testable form -- "does multiplication of prime objects recover
unique factorization?" -- and this module answers it.

The answer is narrower than the intuition suggests, in the same way and for the
same reason that `docs/dimension_shift_involution.md` section 2.1 narrows the
dimension-shift prototype. That is the point of writing it down.

The identification
------------------
Let `P` be the primes and let

    V = { v : P -> N : v(p) = 0 for all but finitely many p }

be the finitely supported exponent vectors, stored sparsely as `{prime: exp}`.
The fundamental theorem of arithmetic says that

    phi : (N_{>0}, x) -> (V, +),       phi(n) = (v_p(n))_p

is a *bijection*, and it is multiplicative by construction.

So `N_{>0}` under multiplication is the **free commutative monoid on the
primes**. That is the precise content of "dimension increases under
multiplication": multiplying appends generators, and the exponent vector is the
bookkeeping. It is not a `Z_2`-grading, not a sphere, and not an extension of
`C` -- it is the monoid structure ordinary arithmetic already has.

The uniqueness theorem
----------------------
"Exponent-vector addition is the only multiplication rule compatible with
unique factorization" is a theorem, and it is short.

    Theorem. Let phi be as above, and let `star` be ANY operation V x V -> V
    satisfying

        phi(m n) = phi(m) star phi(n)        for all m, n >= 1.

    Then `star` is componentwise addition.

    Proof. phi is surjective, being a bijection. Given v, w in V, choose m, n
    with v = phi(m) and w = phi(n). Then

        v star w = phi(m) star phi(n) = phi(m n) = phi(m) + phi(n) = v + w,

    using multiplicativity of `star` in the middle and `v_p(m n) = v_p(m) +
    v_p(n)` at the end. QED

Note what is *not* assumed: `star` need not be associative, commutative, or
have an identity. Surjectivity of `phi` alone pins it down everywhere, so
associativity and commutativity are consequences rather than hypotheses.

The honest reading is therefore deflationary, and worth stating plainly: the
dimension-increasing multiplication is unique factorization restated. It is not
an alternative arithmetic that could have come out otherwise, and no choice was
made. `monoid_contract_report` checks the hypotheses of the theorem over a range;
`candidate_rule_report` illustrates the conclusion by taking six plausible
"other" rules and showing where each one first breaks.

One of those six deserves advance notice. The literal "the dimension grows"
reading -- concatenate the lists of prime factors -- is *not* a different rule.
It agrees with exponent addition everywhere, because taking a multiset union of
prime factors and adding exponent vectors are the same operation written two
ways. The slogan and the algebra are not merely compatible; they are identical.

The grading
-----------
`V` is graded by total degree

    Omega(v) = sum_p v(p)         and       Omega(m n) = Omega(m) + Omega(n).

`Omega(n)` is the number of prime factors of `n` counted with multiplicity, and
it is the "dimension" in the slogan: the degree of `phi(n)` counts how many
generators went into building `n`. `V` decomposes as the direct sum of the `V_d`
over `d >= 0`, each `V_d` finite.

Why this is exactly what makes the primon gas exact
---------------------------------------------------
`primon_gas.py` builds `H|n> = log(n)|n>` on `l^2(N)` and records
`Tr[e^{-sH}] = zeta(s)`. The reason the trace factorizes into an Euler product
is the monoid structure above, in one line: the energy is a *linear functional
of the exponent vector*,

    log(n) = sum_p v_p(n) log(p) = <lambda, phi(n)>,       lambda_p = log(p),

so summing `n^{-s} = exp(-s <lambda, phi(n)>)` over `N_{>0}` is summing
`prod_p x_p^{v_p}` over the free commutative monoid, where `x_p = p^{-s}`. A sum
of a product over a *free commutative* monoid is a product of sums -- that is
what "free commutative" means -- and the product of sums is the Euler product:

    sum_{v in V} prod_p x_p^{v_p}  =  prod_p sum_{a>=0} x_p^a  =  prod_p 1/(1-x_p).

`euler_box_sum` and `euler_product_formula` compute the two sides of the finite
version of that identity -- a box `0 <= v_p <= D` over a finite prime basis --
so the factorization is a checkable identity rather than a slogan. That is the
whole of the claimed connection: the Euler product is exact because it is the
generating function of a free commutative monoid.

What this does NOT do
---------------------
It does not produce a new number system, and it does not touch the zeros. The
eigenvalues of `H` are `log(n)`, not the imaginary parts of the zeta zeros;
`docs/spherical_number_systems.md` section 3.4 is explicit that an operator whose
spectrum *is* the zeros is a separate and still-open construction. Nothing here
proves anything about the Riemann Hypothesis.

Nor does the uniqueness theorem say that `V` is the only possible setting. It
says that *given* unique factorization, the operation is forced. Whether some
richer system could both contain the primes and force the zeros onto a fixed
locus is exactly the open question, and this module does not answer it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product
from typing import Callable, Sequence, TypeAlias

import mpmath as mp
import numpy as np

from .primon_gas import factorize, zeta_reference

#: A prime factorisation, stored sparsely as `{prime: exponent}` with zero
#: exponents omitted. The empty vector `{}` is `phi(1)`, the monoid identity.
ExponentVector: TypeAlias = dict[int, int]

#: A candidate multiplication rule on exponent vectors.
BinaryRule: TypeAlias = Callable[[ExponentVector, ExponentVector], ExponentVector]

#: Upper bound on the number of box terms enumerated by `euler_box_sum`. The
#: enumeration is `(degree_cap + 1) ** len(basis)`, which is exponential, so it
#: is capped rather than left to hang.
_MAX_BOX_TERMS = 200_000


# ============================================================
# Validation
# ============================================================

def _is_prime(n: int) -> bool:
    """Trial-division primality test, used only to validate exponent-vector keys."""
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    candidate = 3
    while candidate * candidate <= n:
        if n % candidate == 0:
            return False
        candidate += 2
    return True


def _validate_vector(v: ExponentVector, name: str = "v") -> ExponentVector:
    """Return a normalised copy of `v`, rejecting anything that is not a vector.

    Keys must be primes -- a "vector indexed by 4" has no meaning in this monoid
    and would make `from_exponent_vector` return a silently wrong integer.
    Exponents must be non-negative integers, since `V` is a monoid and not a
    group. Zero exponents are dropped, so equal vectors compare equal.
    """
    if not isinstance(v, dict):
        raise TypeError(f"{name} must be a dict mapping primes to exponents")
    normalised: ExponentVector = {}
    for key, exponent in v.items():
        if not isinstance(key, (int, np.integer)):
            raise TypeError(f"{name} has a non-integer key {key!r}")
        prime = int(key)
        if not _is_prime(prime):
            raise ValueError(f"{name} has key {prime}, which is not a prime >= 2")
        if not isinstance(exponent, (int, np.integer)):
            raise TypeError(f"{name}[{prime}] must be an integer, got {exponent!r}")
        value = int(exponent)
        if value < 0:
            raise ValueError(
                f"{name}[{prime}] = {value} is negative; V is a monoid, not a group"
            )
        if value:
            normalised[prime] = value
    return normalised


# ============================================================
# The identification: N_{>0} <-> V
# ============================================================

def exponent_vector(n: int) -> ExponentVector:
    """`phi(n)`: the exponent vector of `n`, with `phi(1) = {}`.

    This is the forward half of the identification between `(N_{>0}, x)` and the
    free commutative monoid on the primes. It is unique factorisation, read as a
    statement about a bijection rather than as a statement about integers.
    """
    if not isinstance(n, (int, np.integer)):
        raise TypeError(f"n must be an integer, got {type(n).__name__}")
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    return factorize(int(n))


def from_exponent_vector(v: ExponentVector) -> int:
    """`phi^{-1}(v)`: the integer whose factorisation is `v`, with `phi^{-1}({}) = 1`."""
    vector = _validate_vector(v)
    result = 1
    for prime, exponent in vector.items():
        result *= prime ** exponent
    return result


def add(u: ExponentVector, v: ExponentVector) -> ExponentVector:
    """Componentwise addition -- the monoid operation, and (see the module
    docstring) the only operation compatible with unique factorisation."""
    left = _validate_vector(u, "u")
    right = _validate_vector(v, "v")
    result = dict(left)
    for prime, exponent in right.items():
        total = result.get(prime, 0) + exponent
        if total:
            result[prime] = total
        else:
            result.pop(prime, None)
    return result


def total_degree(v: ExponentVector) -> int:
    """`Omega(v)`: the grading, i.e. the number of prime factors with multiplicity."""
    return sum(_validate_vector(v).values())


def distinct_primes(v: ExponentVector) -> tuple[int, ...]:
    """The support of `v`, ascending: which primes actually occur."""
    return tuple(sorted(_validate_vector(v)))


def prime_basis(n_max: int) -> tuple[int, ...]:
    """Every prime `<= n_max`, ascending -- the generators used up to `n_max`."""
    if not isinstance(n_max, (int, np.integer)):
        raise TypeError("n_max must be an integer")
    if n_max < 2:
        raise ValueError(f"n_max must be >= 2, got {n_max}")
    return tuple(p for p in range(2, int(n_max) + 1) if _is_prime(p))


def dense_vector(v: ExponentVector, basis: Sequence[int]) -> tuple[int, ...]:
    """`v` as a tuple of exponents over a fixed `basis`, for display and comparison."""
    vector = _validate_vector(v)
    for prime in basis:
        if not _is_prime(int(prime)):
            raise ValueError(f"basis contains {prime}, which is not a prime >= 2")
    return tuple(vector.get(int(prime), 0) for prime in basis)


def energy(v: ExponentVector) -> float:
    """`<lambda, v> = sum_p v_p log(p)`, the primon-gas energy of the vector.

    This is `log(phi^{-1}(v))` evaluated through the *linear* functional, which
    is the form that matters: the energy is linear in the exponent vector, and
    that linearity is why the trace factorises.
    """
    return math.fsum(exponent * math.log(prime) for prime, exponent in sorted(_validate_vector(v).items()))


# ============================================================
# The grading
# ============================================================

def graded_components(n_max: int) -> dict[int, list[int]]:
    """Group `1..n_max` by `Omega`, i.e. by the degree of their exponent vector.

    This is the "dimension" of the slogan made concrete: `V_d` collects the
    vectors of total degree `d`, and multiplying moves from `V_d` to `V_{d + d'}`.
    """
    if not isinstance(n_max, (int, np.integer)):
        raise TypeError("n_max must be an integer")
    if n_max < 1:
        raise ValueError(f"n_max must be >= 1, got {n_max}")
    components: dict[int, list[int]] = {}
    for n in range(1, int(n_max) + 1):
        components.setdefault(total_degree(exponent_vector(n)), []).append(n)
    return components


# ============================================================
# Checking the hypotheses of the uniqueness theorem
# ============================================================

def monoid_contract_report(n_max: int = 500) -> dict:
    """Check, over `1..n_max`, everything the uniqueness theorem assumes.

    The theorem is proved by surjectivity of `phi` (see the module docstring),
    which is not something a computation can establish. What a computation can
    do is confirm that its hypotheses hold where it was checked, and that the
    conclusions hold there too:

    - `phi` round-trips in both directions on `1..n_max`;
    - `phi` is multiplicative: `phi(m n) = phi(m) + phi(n)`;
    - `phi(1) = {}`, the monoid identity;
    - `Omega` is additive, so the grading is respected.

    A `first_failure` of `None` means every check passed. It does not mean the
    theorem has been proved by exhaustion.
    """
    if not isinstance(n_max, (int, np.integer)):
        raise TypeError("n_max must be an integer")
    if n_max < 1:
        raise ValueError(f"n_max must be >= 1, got {n_max}")
    n_max = int(n_max)

    forward_failures = [
        n for n in range(1, n_max + 1)
        if from_exponent_vector(exponent_vector(n)) != n
    ]
    backward_failures = [
        n for n in range(1, n_max + 1)
        if exponent_vector(from_exponent_vector(exponent_vector(n))) != exponent_vector(n)
    ]

    multiplicative_failure = None
    degree_failure = None
    pairs_checked = 0
    for m in range(1, n_max + 1):
        for n in range(1, n_max // m + 1):
            pairs_checked += 1
            product_vector = exponent_vector(m * n)
            if multiplicative_failure is None and product_vector != add(
                exponent_vector(m), exponent_vector(n)
            ):
                multiplicative_failure = (m, n)
            if degree_failure is None and total_degree(product_vector) != (
                total_degree(exponent_vector(m)) + total_degree(exponent_vector(n))
            ):
                degree_failure = (m, n)

    return {
        "n_max": n_max,
        "pairs_checked": pairs_checked,
        "round_trip_forward": not forward_failures,
        "round_trip_backward": not backward_failures,
        "multiplicative": multiplicative_failure is None,
        "degree_additive": degree_failure is None,
        "identity_is_empty_vector": exponent_vector(1) == {},
        "first_failure": (
            {"round_trip_forward": forward_failures[:1]} if forward_failures
            else {"round_trip_backward": backward_failures[:1]} if backward_failures
            else {"multiplicative": multiplicative_failure} if multiplicative_failure
            else {"degree_additive": degree_failure} if degree_failure
            else None
        ),
    }


# ============================================================
# The conclusion, illustrated: other rules and where they break
# ============================================================

def _prime_factor_list(v: ExponentVector) -> list[int]:
    """`v` as the sorted list of its prime factors, with multiplicity."""
    out: list[int] = []
    for prime in sorted(v):
        out.extend([prime] * v[prime])
    return out


def _rule_add(u: ExponentVector, v: ExponentVector) -> ExponentVector:
    return add(u, v)


def _rule_concatenate_prime_factors(
    u: ExponentVector, v: ExponentVector
) -> ExponentVector:
    """The literal slogan: glue the two lists of prime factors together.

    Included because it is what "the dimension grows" suggests on first reading,
    and because it turns out to be *the same rule*: recounting the glued list is
    exponent addition. The report says so rather than pretending to refute it.
    """
    out: ExponentVector = {}
    for prime in _prime_factor_list(u) + _prime_factor_list(v):
        out[prime] = out.get(prime, 0) + 1
    return out


def _rule_exponent_max(u: ExponentVector, v: ExponentVector) -> ExponentVector:
    out: ExponentVector = {}
    for prime in set(u) | set(v):
        value = max(u.get(prime, 0), v.get(prime, 0))
        if value:
            out[prime] = value
    return out


def _rule_exponent_product(u: ExponentVector, v: ExponentVector) -> ExponentVector:
    out: ExponentVector = {}
    for prime in set(u) | set(v):
        value = u.get(prime, 0) * v.get(prime, 0)
        if value:
            out[prime] = value
    return out


def _rule_support_union(u: ExponentVector, v: ExponentVector) -> ExponentVector:
    return {prime: 1 for prime in set(u) | set(v)}


def _rule_exponent_xor(u: ExponentVector, v: ExponentVector) -> ExponentVector:
    out: ExponentVector = {}
    for prime in set(u) | set(v):
        value = u.get(prime, 0) ^ v.get(prime, 0)
        if value:
            out[prime] = value
    return out


@dataclass
class RuleReport:
    """Where a candidate multiplication rule first contradicts unique factorisation."""

    name: str
    description: str
    holds: bool
    checked: int
    first_counterexample: tuple[int, int] | None = None
    expected: int | None = None
    produced: int | None = None

    @property
    def summary(self) -> str:
        if self.holds:
            return (
                f"{self.name}: agrees with exponent addition on all "
                f"{self.checked} pairs checked"
            )
        assert self.first_counterexample is not None
        m, n = self.first_counterexample
        return (
            f"{self.name}: fails at {m} x {n} -- unique factorisation requires "
            f"phi({m}) star phi({n}) = phi({m * n}) = {self.expected}, "
            f"but the rule gives {self.produced}"
        )


#: Candidate rules, and why anyone might propose them.
CANDIDATE_RULES: tuple[tuple[str, BinaryRule, str], ...] = (
    ("addition", _rule_add, "componentwise addition of exponents (the theorem's conclusion)"),
    ("concatenate_prime_factors", _rule_concatenate_prime_factors,
     "glue the two lists of prime factors: the literal 'the dimension grows' reading"),
    ("exponent_max", _rule_exponent_max, "keep the larger exponent per prime"),
    ("exponent_product", _rule_exponent_product, "multiply the exponents per prime"),
    ("support_union", _rule_support_union, "take the union of the two supports, exponent 1"),
    ("exponent_xor", _rule_exponent_xor, "xor the exponents per prime"),
)


def candidate_rule_report(n_max: int = 200) -> list[RuleReport]:
    """Run every rule in `CANDIDATE_RULES` and find its first counterexample.

    This *illustrates* the uniqueness theorem; it does not establish it. The
    proof is the surjectivity argument in the module docstring, and no finite
    enumeration could replace it. What the report adds is concreteness: each
    plausible rival rule is shown breaking at a specific small pair, so the claim
    "addition is forced" has something to point at.
    """
    if not isinstance(n_max, (int, np.integer)):
        raise TypeError("n_max must be an integer")
    if n_max < 4:
        raise ValueError(
            f"n_max must be >= 4, got {n_max}. Below that the smallest "
            "counterexamples of the rival rules -- 2 x 2 for `exponent_max` and "
            "`exponent_xor`, 1 x 4 for `support_union` -- lie outside the range, "
            "so a rule would be reported as holding without having been tested "
            "anywhere it fails. A vacuous 'holds' is worse than no report."
        )
    n_max = int(n_max)

    reports: list[RuleReport] = []
    for name, rule, description in CANDIDATE_RULES:
        checked = 0
        counterexample: tuple[int, int] | None = None
        expected: int | None = None
        produced: int | None = None
        for m in range(1, n_max + 1):
            for n in range(1, n_max // m + 1):
                checked += 1
                target = exponent_vector(m * n)
                got = rule(exponent_vector(m), exponent_vector(n))
                if got != target:
                    counterexample = (m, n)
                    expected = m * n
                    produced = from_exponent_vector(got)
                    break
            if counterexample is not None:
                break
        reports.append(
            RuleReport(
                name=name,
                description=description,
                holds=counterexample is None,
                checked=checked,
                first_counterexample=counterexample,
                expected=expected,
                produced=produced,
            )
        )
    return reports


# ============================================================
# The Euler product as the generating function of the monoid
# ============================================================

def _validate_basis(s: complex, basis: Sequence[int], degree_cap: int):
    """Validate a prime basis and a degree cap, without reference to cost.

    Cost is checked separately, and only by `euler_box_sum`: the product formula
    is linear in the number of primes and so has no reason to care how large the
    box would be if it were enumerated.
    """
    primes = tuple(int(p) for p in basis)
    for prime in primes:
        if not _is_prime(prime):
            raise ValueError(f"basis contains {prime}, which is not a prime >= 2")
    if len(set(primes)) != len(primes):
        raise ValueError("basis contains a repeated prime")
    if not isinstance(degree_cap, (int, np.integer)):
        raise TypeError("degree_cap must be an integer")
    if degree_cap < 0:
        raise ValueError(f"degree_cap must be >= 0, got {degree_cap}")
    return primes, int(degree_cap)


def euler_box_sum(s: complex, basis: Sequence[int], degree_cap: int) -> complex:
    """`sum prod_p x_p^{v_p}` over the box `0 <= v_p <= degree_cap`, by enumeration.

    One term per exponent vector in the box, i.e. one term per element of the
    truncation of the monoid `V`. This is the left-hand side of the identity, and
    the only function here whose cost is exponential in the basis size.
    """
    primes, cap = _validate_basis(s, basis, degree_cap)
    terms = (cap + 1) ** len(primes)
    if terms > _MAX_BOX_TERMS:
        raise ValueError(
            f"the box would have {terms} terms, above the cap of {_MAX_BOX_TERMS}; "
            "reduce degree_cap or the size of the basis, or use "
            "euler_product_formula, which computes the same value in linear time"
        )
    x = {prime: mp.mpc(prime) ** (-mp.mpc(complex(s))) for prime in primes}

    total = mp.mpc(0)
    for exponents in product(range(cap + 1), repeat=len(primes)):
        term = mp.mpc(1)
        for prime, exponent in zip(primes, exponents):
            if exponent:
                term *= x[prime] ** exponent
        total += term
    return complex(total)


def euler_product_formula(s: complex, basis: Sequence[int], degree_cap: int) -> complex:
    """The same box sum by the product formula: one geometric series per prime.

    `prod_p (1 - x_p^{D+1}) / (1 - x_p)`. The identity between this and
    `euler_box_sum` is the finite form of "a sum of a product over a free
    commutative monoid is a product of sums", which is what makes the Euler
    product exact for the primon gas. This side is cheap, so it is the one to use
    whenever the box itself is too large to enumerate.
    """
    primes, cap = _validate_basis(s, basis, degree_cap)
    total = mp.mpc(1)
    for prime in primes:
        x = mp.mpc(prime) ** (-mp.mpc(complex(s)))
        total *= sum(x ** a for a in range(cap + 1))
    return complex(total)


def euler_factorization_report(
    s: complex = 2.0, basis: Sequence[int] | None = None, degree_cap: int = 3
) -> dict:
    """Compare the two sides of the box identity and report the difference."""
    if basis is None:
        basis = prime_basis(13)
    primes, cap = _validate_basis(s, basis, degree_cap)
    box = euler_box_sum(s, primes, cap)
    formula = euler_product_formula(s, primes, cap)
    scale = max(abs(box), abs(formula), 1e-300)
    return {
        "s": complex(s),
        "basis": primes,
        "degree_cap": cap,
        "terms_enumerated": (cap + 1) ** len(primes),
        "box_sum": box,
        "product_formula": formula,
        "absolute_difference": abs(box - formula),
        "relative_difference": abs(box - formula) / scale,
        "agrees": abs(box - formula) / scale < 1e-12,
    }


def smooth_truncation_report(
    s: complex = 2.0, prime_cap: int = 997, degree_cap: int = 40
) -> dict:
    """How far the finite box is from `zeta(s)`, and why it closes up.

    The box over the primes `<= prime_cap` is the sum of `n^{-s}` over the
    `prime_cap`-smooth numbers whose exponents are at most `degree_cap`. Raising
    both caps adds terms, so the box approaches `zeta(s)` from below. This is the
    arithmetic reason the primon gas trace *is* `zeta` rather than merely
    resembling it; `primon_gas.trace_convergence` measures the same limit along
    the `n <= N` truncation instead.

    Uses the product formula, so a large basis costs nothing: only the box
    *enumeration* is exponential.
    """
    if complex(s).real <= 1.0:
        raise ValueError(
            "Re(s) > 1 is required: below that the sum does not converge to "
            "zeta(s) without analytic continuation, and the comparison would be "
            "meaningless rather than merely imprecise."
        )
    primes = prime_basis(prime_cap)
    box = euler_product_formula(s, primes, degree_cap)
    reference = zeta_reference(s)
    return {
        "s": complex(s),
        "prime_cap": prime_cap,
        "degree_cap": degree_cap,
        "basis_size": len(primes),
        "box_sum": box,
        "zeta_reference": reference,
        "absolute_difference": abs(box - reference),
        "relative_difference": abs(box - reference) / abs(reference),
    }
