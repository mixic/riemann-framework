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
"""Tests for the prime-orbit dictionary.

The load-bearing tests are the two halves of the honest claim: the counting
correspondence holds and is measured (`orbit_count_ratio` tends to 1), and the
error term does *not* become tractable, because resolving `psi(X)` needs on the
order of `N(X)` zeros.

The second half is the one that first came out wrong. `zeros_control_the_error`
was written comparing two single values of `K`, and it returned `False` at
`X = 1000` and `X = 100000` -- correctly, since the truncated zero sum oscillates.
That is now a measured finding rather than a hidden bug.
"""

import mpmath as mp
import pytest

from riemann_framework.prime_certificate import sieve_slice
from riemann_framework.prime_orbits import (
    RELOCATION_NOTE,
    all_orbit_count,
    chebyshev_psi,
    orbit_count_ratio,
    orbit_table,
    prime_orbit_asymptotic,
    primitive_orbit_count,
    psi_from_zeros,
    psi_minus_smooth,
    reconstruction_report,
    topological_entropy,
    zeros_needed_to_resolve,
    zeta_zero_ordinates,
)


# ============================================================
# The counting correspondence, which works
# ============================================================

def test_topological_entropy_is_one():
    """Forced by the orbit periods being `log p`, not chosen."""
    assert topological_entropy() == 1.0


def test_prime_orbit_asymptotic_is_exp_over_T():
    assert prime_orbit_asymptotic(1.0) == pytest.approx(float(mp.e), rel=1e-12)
    for T in (5.0, 10.0, 20.0):
        assert prime_orbit_asymptotic(T) == pytest.approx(
            float(mp.e**T / T), rel=1e-12
        )


def test_primitive_orbit_count_is_pi_of_e_to_the_T():
    """The primes are the primitive orbits, with period `log p`."""
    for T in (6.0, 9.0, 12.0):
        limit = int(mp.floor(mp.e**T))
        assert primitive_orbit_count(T) == len(sieve_slice(limit))


def test_all_orbits_count_prime_powers():
    """A trace formula sums over repetitions, so prime powers enter too."""
    for T in (6.0, 9.0, 12.0):
        limit = int(mp.floor(mp.e**T))
        expected = sum(
            1
            for p in sieve_slice(limit)
            for k in range(1, 100)
            if p**k <= limit
        )
        assert all_orbit_count(T) == expected
        assert all_orbit_count(T) >= primitive_orbit_count(T)


def test_orbit_ratio_approaches_one():
    """The prime orbit theorem with `h = 1`, measured.

    This is the part of the dictionary that is exact: the count matches the
    Anosov asymptotic at first order. Convergence is slow, which is why the
    assertion is about the trend rather than a threshold.
    """
    ratios = [orbit_count_ratio(T) for T in (6.0, 9.0, 12.0, 15.0)]
    assert all(r > 1.0 for r in ratios)
    assert all(ratios[i] > ratios[i + 1] for i in range(len(ratios) - 1))
    assert ratios[-1] < ratios[0]
    assert ratios[-1] < 1.09


def test_orbit_table_agrees_with_the_individual_counters():
    rows = orbit_table([6.0, 9.0])
    for row in rows:
        assert row.primitive_count == primitive_orbit_count(row.T)
        assert row.all_count == all_orbit_count(row.T)
        assert row.ratio == pytest.approx(
            row.primitive_count / row.asymptotic, rel=1e-12
        )
        assert "primes" in row.summary()


def test_primitive_orbit_count_refuses_an_unaffordable_T():
    """A silent wrong answer would be worse than a refusal."""
    with pytest.raises(ValueError):
        primitive_orbit_count(25.0)


# ============================================================
# The arithmetic side
# ============================================================

def test_chebyshev_psi_by_hand():
    """`psi(10) = 3 log 2 + 2 log 3 + log 5 + log 7`, one `log p` per prime power.

    Prime powers up to 10 are 2, 4, 8 (three from `p = 2`), 3, 9 (two from
    `p = 3`), 5 and 7. Each contributes `log p`, not `log(p^k)` -- the first
    draft of this test used `log 2 + log 4 + log 8`, which is the latter, and
    expected 11.01 against a correct 7.83.
    """
    expected = float(3 * mp.log(2) + 2 * mp.log(3) + mp.log(5) + mp.log(7))
    assert chebyshev_psi(10) == pytest.approx(expected, rel=1e-12)
    assert chebyshev_psi(10) == pytest.approx(7.83202, abs=1e-4)


def test_chebyshev_psi_of_small_inputs():
    assert chebyshev_psi(1) == 0.0
    assert chebyshev_psi(2) == pytest.approx(float(mp.log(2)), rel=1e-12)


def test_psi_minus_smooth_is_the_deviation():
    X = 1000
    assert psi_minus_smooth(X) == pytest.approx(chebyshev_psi(X) - X, rel=1e-12)


# ============================================================
# The explicit formula, including the constants that were missing
# ============================================================

def test_psi_from_zeros_with_no_zeros_is_the_smooth_part():
    """With `K = 0` the formula is `X - log(2 pi) - (1/2) log(1 - X^-2)`.

    The two constant terms were missing from the first draft of
    `psi_from_zeros`, which is a systematic offset of about `-1.84` -- and a
    systematic offset is exactly what makes a convergence measurement look like
    noise. Pinned here so it cannot go missing again.
    """
    X = 1000
    expected = float(
        mp.mpf(X) - mp.log(2 * mp.pi) - mp.log(1 - mp.mpf(X) ** -2) / 2
    )
    assert psi_from_zeros(X, 0) == pytest.approx(expected, rel=1e-12)
    assert expected < X, "log(2 pi) is subtracted, so the smooth part is below X"


def test_zeta_zero_ordinates_match_mpmath():
    ordinates = zeta_zero_ordinates(3)
    assert ordinates[0] == pytest.approx(14.134725141734695, abs=1e-9)
    for k, gamma in enumerate(ordinates, start=1):
        assert gamma == pytest.approx(float(mp.zetazero(k).imag), abs=1e-9)


# ============================================================
# The finding: the error term does not become tractable
# ============================================================

def test_the_truncated_zero_sum_does_not_converge_usefully():
    """Measured, and it is the module's main negative result.

    Over `K` from 1 to 89 at `X = 100000` the error ranges across a factor of
    tens with no downward trend. The zero sum converges only conditionally, so a
    truncation carries an oscillating tail of size about `X^{1/2}/gamma_K`.
    """
    report = reconstruction_report(100_000)
    assert report.maximum_error / report.minimum_error > 10
    assert not (
        report.errors == sorted(report.errors, reverse=True)
    ), "errors should not fall monotonically"


def test_resolving_psi_needs_far_more_zeros_than_are_used():
    """The number that makes the dictionary's error term useless in practice."""
    report = reconstruction_report(100_000)
    assert report.zeros_needed > 100_000
    assert report.uses_a_negligible_fraction_of_the_needed_zeros
    assert "no downward trend" in report.summary()


def test_zeros_needed_grows_faster_than_X():
    """`(X/2 pi) log(X/2 pi e)`: superlinear, so the gap widens with X."""
    needed = [zeros_needed_to_resolve(X) for X in (10**3, 10**5, 10**7)]
    assert needed == sorted(needed)
    ratios = [needed[i + 1] / needed[i] for i in range(len(needed) - 1)]
    assert all(r > 10 for r in ratios)
    assert zeros_needed_to_resolve(10**12) > 10**12


def test_the_relocation_note_states_the_measured_limit():
    assert "COUNTING" in RELOCATION_NOTE
    assert "reconstructing psi(X)" in RELOCATION_NOTE


def test_zeros_needed_rejects_tiny_X():
    with pytest.raises(ValueError):
        zeros_needed_to_resolve(2)
