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
An exact certificate for the first million primes.

This is the one place in the repository where a simulation *proves* rather than
supports. The reason is that the claim is finite: "the first million primes are
these numbers, and no prime is missing between them" is a statement about finitely
many integers, and a finite check with a certificate is a proof of it. Nothing here
bears on the Riemann hypothesis, which is a universal statement and is not
reachable by any finite computation.

What is certified
-----------------
For `n = 1_000_000` and `limit = p_n = 15_485_863`:

1. **Every listed number is prime.** Verified by a *deterministic* Miller-Rabin
   test, not a probabilistic one. The bases `2..37` are a proven-correct set for
   every `n < 3.317e24` (Sorenson and Webster), and the values here are below
   `1.6e7`, so a pass is a proof for that number rather than a probability.
2. **No prime is missing.** Two independently written sieves -- one using
   `bytearray` slice assignment, one a plain nested loop -- must agree exactly. The
   point is that they fail differently: a coding error in the slice-stride
   arithmetic does not reproduce itself in a loop that marks multiples by repeated
   addition.
3. **The sieve invariant holds.** For every listed prime `p <= sqrt(limit)`, every
   multiple of `p` from `p^2` upward is composite, which catches a sieve that never
   marked them. It does **not** catch a prime missing from the list -- the scan
   iterates over the list it is given -- so completeness rests on items 2 and 4.
   The limitation is pinned by a test rather than left as prose.
4. **The published landmark.** `p_1_000_000 = 15_485_863` and `pi(limit) =
   1_000_000`, which are numbers anyone can check against the literature. If the
   certificate disagrees with them, the certificate is wrong.

The digest
----------
`certify_first_n_primes` returns a SHA-256 over the packed list, so a later run in
a different environment can be compared without shipping the list. The digest is
not a proof of anything by itself; it is what makes the claim reproducible.

A note on what "independent" is worth here
------------------------------------------
The two sieves are independent as *implementations*, not as *mathematics*: they
encode the same algorithm and would share a conceptual error, such as a wrong
bound for the sieve. The mathematical content is carried by items 3 and 4, which
check the invariant and the known values. Item 1 is the strongest of the four,
because deterministic Miller-Rabin is a theorem for this range, not a heuristic.
"""

from __future__ import annotations

import hashlib
from array import array
from dataclasses import dataclass, field

#: Bases for which Miller-Rabin is *proven* correct below
#: 3_317_044_064_679_887_385_961_981 (Sorenson and Webster 2015). Every value
#: certified here is under 1.6e7, so no probabilistic reading is required.
DETERMINISTIC_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)

#: The millionth prime, and the count it certifies.
KNOWN_MILLIONTH_PRIME = 15_485_863
KNOWN_PRIME_COUNT = 1_000_000


def sieve_slice(limit: int) -> list[int]:
    """Primes `<= limit` by `bytearray` slice assignment.

    The stride trick assigns every multiple of `p` in one operation, which is the
    fast form and also the one where an off-by-one in the stride arithmetic hides.
    """
    if limit < 2:
        return []
    flags = bytearray([1]) * (limit + 1)
    flags[0:2] = b"\x00\x00"
    for p in range(2, int(limit ** 0.5) + 1):
        if flags[p]:
            start = p * p
            flags[start::p] = b"\x00" * len(range(start, limit + 1, p))
    return [i for i in range(2, limit + 1) if flags[i]]


def sieve_loop(limit: int) -> list[int]:
    """Primes `<= limit` by a plain nested loop, marking multiples by addition.

    Deliberately a different code path from `sieve_slice`: no slicing, no stride,
    just repeated addition. It is slower and it fails differently.
    """
    if limit < 2:
        return []
    composite = bytearray(limit + 1)
    for p in range(2, int(limit ** 0.5) + 1):
        if not composite[p]:
            multiple = p * p
            while multiple <= limit:
                composite[multiple] = 1
                multiple += p
    return [i for i in range(2, limit + 1) if not composite[i]]


def is_prime_deterministic(n: int) -> bool:
    """Exact primality by deterministic Miller-Rabin over `DETERMINISTIC_MR_BASES`.

    For `n < 3.317e24` the listed bases decide primality with certainty, so a
    `True` here is a proof that `n` is prime and not a probable-prime verdict.
    """
    if n < 2:
        return False
    for small in DETERMINISTIC_MR_BASES:
        if n == small:
            return True
        if n % small == 0:
            return False

    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for base in DETERMINISTIC_MR_BASES:
        x = pow(base, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def check_sieve_invariant(limit: int, primes: list[int]) -> tuple[bool, int | None]:
    """Every multiple of every listed prime `p <= sqrt(limit)`, from `p^2`, is composite.

    This catches the failure the sieve is most likely to have: multiples that were
    never marked, and so survive as composites in the list. A sieve that lost a
    prime's multiples leaves `p^2, p^2+p, ...` marked prime, and this finds them at
    the source.

    **It cannot detect a missing prime.** The scan iterates over the list it is
    given, so deleting an entry makes the check strictly weaker and it still
    passes. Completeness, therefore, rests on the two-sieve agreement and the
    published landmark, not on this check -- which is why the certificate has four
    chains and not three. Pinned by
    `test_a_missing_prime_is_not_caught_by_the_invariant_check`.

    Returns `(ok, first_failing_prime)`.
    """
    prime_set = set(primes)
    for p in primes:
        if p * p > limit:
            break
        multiple = p * p
        while multiple <= limit:
            if multiple in prime_set:
                return False, p
            multiple += p
    return True, None


@dataclass
class PrimeCertificate:
    """The outcome of certifying a prefix of the primes."""

    n: int
    limit: int
    count: int
    last_prime: int
    digest: str
    all_prime_deterministic: bool
    sieves_agree: bool
    invariant_holds: bool
    matches_published_landmark: bool
    first_composite_passed_off_as_prime: int | None = None
    first_failing_sieve_prime: int | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def certified(self) -> bool:
        """True only when every chain of the certificate passed."""
        return (
            self.all_prime_deterministic
            and self.sieves_agree
            and self.invariant_holds
            and self.matches_published_landmark
        )

    def summary(self) -> str:
        state = "CERTIFIED" if self.certified else "NOT CERTIFIED"
        return (
            f"{state}: p_{self.n} = {self.last_prime}, count = {self.count}, "
            f"sha256 = {self.digest[:16]}...  "
            f"[prime={self.all_prime_deterministic} "
            f"sieves_agree={self.sieves_agree} "
            f"invariant={self.invariant_holds} "
            f"landmark={self.matches_published_landmark}]"
        )


def list_digest(primes: list[int]) -> str:
    """SHA-256 over the primes packed as 8-byte little-endian unsigned integers."""
    packed = array("Q", primes)
    return hashlib.sha256(packed.tobytes()).hexdigest()


def certify_first_n_primes(n: int = KNOWN_PRIME_COUNT) -> PrimeCertificate:
    """Certify that the first `n` primes are exactly the list produced, and complete.

    `limit` is taken from the sieve run itself, so the certificate does not assume
    the millionth prime -- it derives it and then compares against the published
    value. Deriving first and comparing afterwards is what makes the last check a
    test rather than a tautology.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    # Derive the range first. Bertrand's postulate makes 16n log n a safe bound for
    # the n-th prime for every n >= 1; for n = 10**6 it is far above 1.55e7.
    import math

    limit = 2 if n == 1 else int(16 * n * (math.log(n) + math.log(math.log(n)))) + 16
    primes = sieve_slice(limit)
    while len(primes) < n:
        limit *= 2
        primes = sieve_slice(limit)
    primes = primes[:n]
    last_prime = primes[-1]

    # Truncating at `n` means the sieve bound was generous; the invariant is
    # checked against the full range up to the last prime actually used.
    invariant_limit = last_prime

    checks: list[str] = []
    first_composite = None
    for p in primes:
        if not is_prime_deterministic(p):
            first_composite = p
            break
    all_prime = first_composite is None
    if not all_prime:
        checks.append(
            f"deterministic Miller-Rabin rejected {first_composite}, which the "
            "sieve listed as prime"
        )

    other = sieve_loop(invariant_limit)
    sieves_agree = other == primes
    if not sieves_agree:
        checks.append(
            "the two sieves disagree; the smaller-count side is truncated to the "
            "first n primes, so a disagreement means one of them is wrong"
        )

    invariant_ok, failing_prime = check_sieve_invariant(invariant_limit, primes)
    if not invariant_ok:
        checks.append(
            f"multiples of {failing_prime} were not all marked composite"
        )

    landmark = (n != KNOWN_PRIME_COUNT) or (
        last_prime == KNOWN_MILLIONTH_PRIME and len(primes) == KNOWN_PRIME_COUNT
    )
    if not landmark:
        checks.append(
            f"derived p_{n} = {last_prime}, but the published value is "
            f"{KNOWN_MILLIONTH_PRIME}"
        )

    return PrimeCertificate(
        n=n,
        limit=invariant_limit,
        count=len(primes),
        last_prime=last_prime,
        digest=list_digest(primes),
        all_prime_deterministic=all_prime,
        sieves_agree=sieves_agree,
        invariant_holds=invariant_ok,
        matches_published_landmark=landmark,
        first_composite_passed_off_as_prime=first_composite,
        first_failing_sieve_prime=failing_prime,
        notes=checks,
    )
