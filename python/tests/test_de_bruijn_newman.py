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
"""Tests for the de Bruijn-Newman module.

The load-bearing tests are the ones that check the *sourced* definition against
an independent route: `Phi` and the quadrature against `(1/8) xi(1/2 + i z/2)`,
and the zeros against `2 gamma_k`. Those are what caught the recalled exponents
and the missing `1/8` in the first draft.

Three tests deliberately pin the module's *limits* rather than its successes --
the quadrature drift with height, the flat zero count, and the truncated dynamics
disagreeing with the numerics. A test suite that only recorded the parts that
work would misrepresent what the module can do.

Nothing here proves or disproves the Riemann hypothesis, and no test asserts that
Lambda <= 0.
"""

import mpmath as mp
import pytest

from riemann_framework.de_bruijn_newman import (
    DYNAMICS_NOTE,
    INSENSITIVITY_NOTE,
    LAMBDA_BOUNDS,
    H,
    H_reference,
    doubled_zeta_zero_ordinates,
    flow_operator_coefficients,
    locate_zeros,
    phi,
    toy_constant,
    toy_zeros,
    zero_accuracy_table,
    zero_count_scan,
    zero_velocity_numeric,
    zero_velocity_truncated,
)


# ============================================================
# Phi, and the definition it comes from
# ============================================================

def test_phi_is_even_where_the_sum_converges():
    """`Phi(u) = Phi(-u)`, checked where the negative side is affordable.

    The defining sum converges for negative `u` too, but needs on the order of
    `e^{-u}` terms, so the check stays in the region where it is cheap. The
    integral representation only ever needs `u >= 0`.
    """
    for u in (0.1, 0.25, 0.5):
        assert abs(phi(u) - phi(-u)) < mp.mpf(10) ** -25


def test_phi_matches_the_sourced_values():
    """Pinned values from the sourced definition.

    These are the exponents `9u`, `5u`, `4u`. A draft using `9u/2`, `5u/2`, `2u`
    gives `Phi(2u)` instead, so every value is shifted in `u` -- which is exactly
    how this test first failed, with its expectations copied across from the
    wrong version. Both the module and these numbers were corrected against the
    quadrature check above, not against each other.
    """
    assert float(phi(0)) == pytest.approx(0.446697, abs=1e-6)
    assert float(phi(mp.mpf("0.25"))) == pytest.approx(0.0301887, abs=1e-6)
    assert float(phi(mp.mpf("0.5"))) == pytest.approx(1.37781e-7, rel=1e-4)


def test_phi_decays_super_exponentially():
    """`Phi` is negligible past `u ~ 0.6`, which is why the window is `[0, 1.2]`."""
    assert abs(float(phi(1))) < 1e-60
    assert abs(float(phi(mp.mpf("1.5")))) < 1e-100


# ============================================================
# H_0 against the independent route
# ============================================================

def test_h_zero_matches_the_sourced_reference():
    """`int_0^inf Phi(u) cos(zu) du` equals `(1/8) xi(1/2 + i z/2)`.

    The two sides share no code: one is a quadrature over a precomputed table,
    the other evaluates `zeta` and `gamma` directly. This is the check the first
    draft failed, at the 0.5% level, which located the wrong exponents and the
    missing `1/8` in one go.
    """
    for z in (1.0, 3.0, 7.0, 14.0, 28.0):
        quadrature = float(H(0.0, z)[0])
        reference = H_reference(z).real
        assert abs(quadrature - reference) < 1e-12, f"z = {z}"


def test_h_is_even_in_z():
    """`H_t` is even, so only `z > 0` needs scanning."""
    for t in (0.0, 0.1, -0.1):
        for z in (2.0, 9.0, 30.0):
            assert float(H(t, z)[0]) == pytest.approx(float(H(t, -z)[0]), abs=1e-18)


def test_h_t_reduces_to_the_reference_at_t_zero():
    """`t = 0` is `H_0`; a sign or index error in the flow would break this."""
    assert float(H(0.0, 5.0)[0]) == pytest.approx(H_reference(5.0).real, abs=1e-12)


# ============================================================
# Zeros
# ============================================================

def test_first_zero_is_twice_the_first_zeta_zero():
    """`H_0` vanishes at `z = 2 gamma_1 = 28.269450...`.

    The factor of two comes from the `i z / 2` in the sourced normalisation, so
    this test also catches a normalisation slip that the value check above might
    miss at small `z`.
    """
    zeros = locate_zeros(0.0, z_max=32.0, grid=20000)
    assert zeros, "no zero found"
    assert zeros[0] == pytest.approx(doubled_zeta_zero_ordinates(1)[0], abs=1e-8)


def test_located_zeros_are_positive_and_increasing():
    zeros = locate_zeros(0.0, z_max=70.0, grid=20000)
    assert len(zeros) >= 4
    assert all(z > 0 for z in zeros)
    assert zeros == sorted(zeros)


def test_doubled_zero_ordinates_match_zetazero():
    ordinates = doubled_zeta_zero_ordinates(3)
    assert ordinates[0] == pytest.approx(28.2694502834, abs=1e-9)
    assert ordinates[1] == pytest.approx(42.0440792780, abs=1e-9)
    for k, value in enumerate(ordinates, start=1):
        assert value == pytest.approx(float(2 * mp.zetazero(k).imag), abs=1e-9)


# ============================================================
# The three limits, pinned rather than hidden
# ============================================================

def test_quadrature_accuracy_degrades_with_height():
    """The documented limit, measured in both directions.

    Low zeros agree with `2 gamma_k` to high accuracy; the ninth does not, by
    about `1e-2` relative. Pinning both ends means a future change that silently
    widens or narrows the usable range is visible.
    """
    rows = zero_accuracy_table(9)
    assert len(rows) == 9
    assert rows[0].relative_error < 1e-9
    assert rows[5].relative_error < 1e-4
    assert rows[8].relative_error > 1e-3
    # And the drift grows, rather than being noise.
    assert rows[8].relative_error > rows[0].relative_error


def test_zero_count_scan_is_flat_and_says_why_that_is_not_evidence():
    """The central honest point of the module.

    A constant count across `t`, including negative `t` where an exit would
    appear if `Lambda < 0`, is *not* support for RH. The module has to report
    that alongside the number, because the number alone reads as reassurance.
    """
    scan = zero_count_scan(t_values=[-0.2, -0.1, 0.0, 0.1, 0.2], z_max=120.0)
    assert scan.is_flat
    assert len(set(scan.counts)) == 1
    assert "NOT evidence" in scan.summary()
    assert "Lehmer" in INSENSITIVITY_NOTE


def test_truncated_dynamics_disagrees_with_the_numeric_derivative():
    """The second limit: equation (5) does not truncate.

    The truncated sum over the computed zeros gives a derivative that disagrees
    with the numerically differentiated zero positions, and the disagreement is
    not small. Recording it prevents the truncated formula from being handed
    around as if it were the paper's equation.
    """
    zeros = locate_zeros(0.0, z_max=70.0, grid=20000)
    numeric = zero_velocity_numeric(0.0, z_max=70.0)
    truncated = zero_velocity_truncated(zeros)
    assert len(numeric) == len(truncated)
    worst = max(abs(a - b) for a, b in zip(numeric, truncated))
    assert worst > 0.1, "if this ever agrees, the note is wrong"
    assert "ALL zeros" in DYNAMICS_NOTE
    assert "cutoffs" in DYNAMICS_NOTE


# ============================================================
# The control, where an exit IS observable
# ============================================================

def test_toy_control_has_lambda_equal_to_half_c():
    """`p(z) = z^2 + c` has `Lambda = c/2`, exactly, and it is attained.

    This is the control for the scan: here an exit *is* in range, so the
    machinery can be seen detecting one. The zeros are non-real for `t < c/2`
    and real for `t >= c/2`, with the crossing exactly at `c/2`.
    """
    c = 1.0
    assert toy_constant(c) == pytest.approx(0.5)
    below = toy_zeros(c, 0.4)
    at = toy_zeros(c, 0.5)
    above = toy_zeros(c, 0.6)
    assert any(isinstance(z, complex) for z in below)
    # Unpacked and narrowed individually: `toy_zeros` returns a union of two
    # tuple types, so iterating gives `float | complex` and `float(z)` does not
    # type-check without the isinstance guard.
    lo, hi = at
    assert isinstance(lo, float) and isinstance(hi, float)
    assert abs(lo) < 1e-12 and abs(hi) < 1e-12
    assert all(isinstance(z, float) for z in above)


def test_toy_control_rejects_a_negative_constant():
    """With `c < 0` the zeros are already real and `Lambda` is not positive."""
    with pytest.raises(ValueError):
        toy_constant(-1.0)


def test_flow_operator_reproduces_the_toy():
    """`exp(-t d^2/dz^2)(z^2 + c) = z^2 + c - 2t`, via the coefficient formula.

    Checks `flow_operator_coefficients` against a case whose answer is known by
    hand, so the recursion is not merely self-consistent.
    """
    c = 3.0
    for t in (0.0, 0.25, 1.5):
        moved = flow_operator_coefficients([c, 1.0], t, 2)
        assert moved[0] == pytest.approx(c - 2 * t)
        assert moved[1] == pytest.approx(1.0)


def test_flow_operator_rejects_an_overlong_request():
    with pytest.raises(ValueError):
        flow_operator_coefficients([1.0, 2.0], 0.0, 5)


# ============================================================
# The stated position
# ============================================================

def test_lambda_bounds_record_the_window():
    """The two bounds that make the window `[0, 0.2]`, with sources."""
    assert LAMBDA_BOUNDS["lower"] == 0.0
    assert LAMBDA_BOUNDS["upper"] == 0.2
    assert "Rodgers-Tao" in str(LAMBDA_BOUNDS["lower_source"])
    assert "Polymath15" in str(LAMBDA_BOUNDS["upper_source"])


def test_the_equivalence_is_stated_as_an_equivalence():
    """`RH <=> Lambda <= 0`, and no function here returns a proof verdict.

    The module must not offer anything that reads as having verified the bound.
    """
    assert "RH <=>" in str(LAMBDA_BOUNDS["equivalence"])
    assert "Lambda = 0" in str(LAMBDA_BOUNDS["equivalence"])
