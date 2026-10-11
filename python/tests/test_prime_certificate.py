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
"""Tests for the exact certificate for the first million primes.

Unlike every other test in this repository, these are not checks on a model. The
million-prime claim is finite, so passing these is a *proof* of it: deterministic
Miller-Rabin is a theorem for this range, and the two sieves plus the invariant
check establish completeness. Nothing here bears on the Riemann hypothesis.
"""

import pytest

from riemann_framework.prime_certificate import (
    DETERMINISTIC_MR_BASES,
    KNOWN_MILLIONTH_PRIME,
    check_sieve_invariant,
    certify_first_n_primes,
    is_prime_deterministic,
    list_digest,
    sieve_loop,
    sieve_slice,
)

FIRST_25 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
            67, 71, 73, 79, 83, 89, 97]


# ============================================================
# The sieves
# ============================================================

def test_both_sieves_reproduce_the_first_primes():
    assert sieve_slice(100) == FIRST_25
    assert sieve_loop(100) == FIRST_25


@pytest.mark.parametrize("limit", [2, 3, 10, 97, 1000, 10_000])
def test_the_two_sieves_agree(limit):
    """Independent implementations, so a coding error in one is unlikely to be
    reproduced in the other. They share the algorithm, which is why they are not
    sufficient on their own -- see the invariant test."""
    assert sieve_slice(limit) == sieve_loop(limit)


def test_sieves_handle_degenerate_limits():
    for limit in (-5, 0, 1):
        assert sieve_slice(limit) == []
        assert sieve_loop(limit) == []


def test_sieve_invariant_holds_and_is_a_real_check():
    """Every multiple of every listed prime, from p^2, must be composite.

    Checked both ways: it passes on a correct sieve, and it fails on a list with a
    composite smuggled in. An earlier version of this test removed a prime from the
    list and expected a failure -- which is wrong, and the failure taught something
    worth recording. The check iterates over the primes it is *given*, so removing
    one makes it strictly weaker and it cannot detect a missing prime at all.
    Completeness therefore rests on the two-sieve agreement and the landmark, not
    on this check.
    """
    primes = sieve_slice(1000)
    assert check_sieve_invariant(1000, primes) == (True, None)

    # 77 = 7 * 11, so 7 is a listed prime whose multiple 77 is now also "prime".
    damaged = sorted([p for p in primes if p <= 100] + [77])
    ok, failing = check_sieve_invariant(1000, damaged)
    assert not ok
    assert failing == 7


def test_a_missing_prime_is_not_caught_by_the_invariant_check():
    """Pinning the limitation rather than leaving it as prose.

    This is why the certificate has four chains: the invariant cannot see a prime
    that is absent, and the two-sieve agreement plus the published landmark are what
    establish completeness.
    """
    primes = sieve_slice(1000)
    missing = [p for p in primes if p != 13]
    assert check_sieve_invariant(1000, missing) == (True, None)


# ============================================================
# Deterministic primality
# ============================================================

@pytest.mark.parametrize("n", FIRST_25)
def test_deterministic_miller_rabin_accepts_primes(n):
    assert is_prime_deterministic(n)


@pytest.mark.parametrize("n", [0, 1, 4, 6, 9, 25, 100, 561, 1105, 1729, 2465])
def test_deterministic_miller_rabin_rejects_composites(n):
    """`561`, `1105`, `1729` and `2465` are Carmichael numbers, which fool the
    Fermat test. They must not fool this one."""
    assert not is_prime_deterministic(n)


def test_the_base_set_is_the_proven_one():
    """The determinism claim rests on this exact base list.

    Sorenson and Webster prove bases `2..37` sufficient below `3.317e24`; dropping
    a base would silently turn a proof into a probable-prime test, so the list is
    pinned rather than trusted.
    """
    assert DETERMINISTIC_MR_BASES == (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    assert 3_317_044_064_679_887_385_961_981 > KNOWN_MILLIONTH_PRIME


# ============================================================
# The certificate
# ============================================================

def test_small_certificate_matches_the_known_primes():
    cert = certify_first_n_primes(25)
    assert cert.count == 25
    assert cert.last_prime == 97
    assert cert.certified


def test_the_million_prime_certificate_passes_every_check():
    """The claim itself. Slow -- about 20 seconds -- and worth it: this is the one
    test in the repository whose passing is a proof rather than a consistency
    check."""
    cert = certify_first_n_primes(1_000_000)
    assert cert.count == 1_000_000
    assert cert.last_prime == KNOWN_MILLIONTH_PRIME
    assert cert.all_prime_deterministic
    assert cert.sieves_agree
    assert cert.invariant_holds
    assert cert.matches_published_landmark
    assert cert.certified
    assert cert.notes == []


def test_the_digest_is_stable_and_content_sensitive():
    """Reproducibility, and a digest that would actually notice a change."""
    a = list_digest([2, 3, 5, 7])
    assert a == list_digest([2, 3, 5, 7])
    assert a != list_digest([2, 3, 5, 11])
    assert a != list_digest([2, 3, 5])
    assert len(a) == 64


def test_certificate_rejects_a_nonpositive_request():
    with pytest.raises(ValueError, match="n must be"):
        certify_first_n_primes(0)
