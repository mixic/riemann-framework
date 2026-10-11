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
"""Tests for the zeta-containment screen.

The interesting tests here are the two representation identities. They are what
make the screen more than bookkeeping: they check that the declared product
`zeta * L(s, chi)` really does reproduce each number field's own Dirichlet
series, so a declared factorisation is *verified* rather than trusted.

Both identities are classical, and both were also wrong in this module's first
draft for an instructive reason -- the Eisenstein enumeration bound was too
small, which the identity check caught at `n = 3781`. That regression is pinned
below.

Nothing here proves or disproves the Riemann hypothesis, and no test asserts
that any framework is a route to it.
"""

import pytest

from riemann_framework.dh_filter import dh_coefficients
from riemann_framework.zeta_factors import (
    DEFAULT_N_MAX,
    FACTORS,
    FRAMEWORKS,
    Framework,
    FrameworkVerdict,
    chi_minus_3,
    chi_minus_4,
    davenport_heilbronn_coefficients,
    dirichlet_convolution,
    eisenstein_representation_counts,
    factor_coefficients,
    gaussian_representation_counts,
    no_euler_product_list,
    screen_all,
    screen_framework,
    separate_target_list,
    strictly_harder_list,
    unverified_factorizations,
    verify_factorization,
)


def _framework(framework_id: str) -> Framework:
    by_id = {f.id: f for f in FRAMEWORKS}
    assert framework_id in by_id, f"no framework {framework_id!r}"
    return by_id[framework_id]


# ============================================================
# Characters
# ============================================================

def test_chi_minus_4_has_the_documented_pattern():
    """`1, 0, -1, 0, ...` -- the character in the standard introduction."""
    assert [chi_minus_4(n) for n in range(1, 9)] == [1, 0, -1, 0, 1, 0, -1, 0]


def test_chi_minus_3_has_the_documented_pattern():
    """`1, -1, 0, ...`, the character attached to the Eisenstein integers."""
    assert [chi_minus_3(n) for n in range(1, 10)] == [1, -1, 0, 1, -1, 0, 1, -1, 0]


def test_both_characters_are_completely_multiplicative():
    """`chi(ab) = chi(a) chi(b)` with no coprimality condition.

    Complete multiplicativity is what makes the local factor a single Euler
    factor, so it is the property the whole factorisation rests on.
    """
    for chi in (chi_minus_4, chi_minus_3):
        for a in range(1, 60):
            for b in range(1, 60):
                assert chi(a * b) == chi(a) * chi(b), f"chi({a}*{b})"


def test_both_characters_are_odd_and_non_principal():
    """Odd characters, and not the principal one.

    Oddness is why the completed L-functions carry a `Gamma((s+1)/2)` and not
    `Gamma(s/2)` -- the same distinction that fixes the shape of the
    Davenport-Heilbronn completion in `dh_filter`.
    """
    assert chi_minus_4(3) == -1  # -1 mod 4
    assert chi_minus_3(2) == -1  # -1 mod 3
    for chi, modulus in ((chi_minus_4, 4), (chi_minus_3, 3)):
        assert chi(modulus) == 0, "principal characters vanish at the modulus"


# ============================================================
# The two representation identities, which are the real content
# ============================================================

def test_gaussian_counts_satisfy_the_identity():
    """`r2(n)/4 = sum_{d|n} chi_-4(d)` for every `n <= 2000`.

    This is the Gaussian integer splitting law, checked as arithmetic rather
    than asserted. The right-hand side is exactly the Dirichlet convolution of
    `zeta`'s coefficients with `chi_-4`, so this test verifies the declared
    factorisation `zeta_{Q(i)} = zeta * L(s, chi_-4)`.
    """
    n_max = DEFAULT_N_MAX
    counts = gaussian_representation_counts(n_max)
    convolution = dirichlet_convolution(
        factor_coefficients(("zeta",), n_max),
        factor_coefficients(("dirichlet_L_chi4",), n_max),
        n_max,
    )
    assert counts[1:n_max + 1] == convolution[1:n_max + 1]


def test_eisenstein_counts_satisfy_the_identity():
    """`r3(n)/6 = sum_{d|n} chi_-3(d)` for every `n <= 2000`."""
    n_max = DEFAULT_N_MAX
    counts = eisenstein_representation_counts(n_max)
    convolution = dirichlet_convolution(
        factor_coefficients(("zeta",), n_max),
        factor_coefficients(("dirichlet_L_chi3",), n_max),
        n_max,
    )
    assert counts[1:n_max + 1] == convolution[1:n_max + 1]


def test_eisenstein_bound_regression_at_3781():
    """The exact value that a too-small enumeration bound gets wrong.

    `x^2 + xy + y^2 >= (x^2 + y^2)/2`, so `|x|` can reach `sqrt(2n)` and not
    just `sqrt(n)`. Enumerating `x, y` only to `sqrt(n_max)` misses
    representations of `3781`, and the identity then fails there. This test
    would pass with the wrong bound if it only went up to `DEFAULT_N_MAX`, so it
    deliberately reaches past it.
    """
    n_max = 4000
    counts = eisenstein_representation_counts(n_max)
    divisors_sum = sum(chi_minus_3(d) for d in range(1, 3781 + 1) if 3781 % d == 0)
    assert counts[3781] == divisors_sum
    assert counts[3781] > 0


def test_gaussian_counts_match_known_values():
    """Spot values, including the primes that do and do not split."""
    counts = gaussian_representation_counts(26)
    assert counts[1] == 1
    assert counts[2] == 1  # 1^2 + 1^2
    assert counts[3] == 0  # 3 is inert
    assert counts[5] == 2  # 2 +- i
    assert counts[13] == 2
    assert counts[25] == 3  # (2+i)^2 (2-i)^2 and 5*5


def test_eisenstein_counts_match_known_values():
    """The hexagonal analogue, where 3 ramifies instead of 2.

    The values follow the splitting law rather than the count of small
    representations: `sum_{d|n} chi_-3(d)` is `1 + chi_-3(n)`, so a prime
    `n = 1 mod 3` gives 2 (it splits), `n = 2 mod 3` gives 0 (it is inert), and
    `n = 0 mod 3` gives 1 (it ramifies). An earlier draft of this test expected
    `r3(7)/6 = 1` by reading `7` as "small, so one representation"; the identity
    check above is what caught it.
    """
    counts = eisenstein_representation_counts(14)
    assert counts[1] == 1
    assert counts[2] == 0  # 2 mod 3, inert
    assert counts[3] == 1  # ramified
    assert counts[7] == 2  # 7 = 2^2 + 2*1 + 1^2, and 7 = 1 mod 3 so it splits
    assert counts[13] == 2


# ============================================================
# Dirichlet convolution
# ============================================================

def test_convolution_with_the_unit_factor_is_the_identity():
    """The `unit` factor really is a multiplicative identity."""
    series = factor_coefficients(("dirichlet_L_chi4",), 200)
    convolved = dirichlet_convolution(factor_coefficients(("unit",), 200), series, 200)
    assert convolved[1:201] == series[1:201]


def test_convolution_is_commutative():
    """`f * g = g * f`, on a nontrivial pair."""
    left = factor_coefficients(("zeta",), 150)
    right = factor_coefficients(("dirichlet_L_chi3",), 150)
    assert dirichlet_convolution(left, right, 150) == dirichlet_convolution(
        right, left, 150
    )


def test_empty_product_is_the_unit_table():
    """The empty product is 1, whose coefficients are `(1, 0, 0, ...)`."""
    empty = factor_coefficients((), 50)
    assert empty[1] == 1
    assert all(empty[n] == 0 for n in range(2, 51))


def test_zeta_alone_has_all_ones_coefficients():
    """`zeta`'s Dirichlet series is `sum n^{-s}`, so every coefficient is 1."""
    assert factor_coefficients(("zeta",), 40)[1:41] == [1] * 40


# ============================================================
# Verification, and the fact that it can fail
# ============================================================

def test_declared_gaussian_factorization_verifies():
    """The screen's headline claim, checked rather than trusted."""
    result = verify_factorization(_framework("dedekind_gaussian"))
    assert result.applicable
    assert result.agrees
    assert result.first_disagreement is None


def test_declared_eisenstein_factorization_verifies():
    result = verify_factorization(_framework("dedekind_eisenstein"))
    assert result.applicable
    assert result.agrees


def test_verification_detects_a_wrong_declaration():
    """A check that cannot fail proves nothing, so this one is made to fail.

    The synthetic framework declares `zeta * L(s, chi_-4)` but supplies `zeta`'s
    own coefficients. The product and the series agree at `n = 1` and at
    `n = 2`, and diverge at `n = 3`, where `sum_{d|3} chi_-4(d) = 0` while
    `zeta` has coefficient 1.
    """
    wrong = Framework(
        id="wrong_declaration",
        description="declares a Gaussian product but supplies zeta's series",
        factors=("zeta", "dirichlet_L_chi4"),
        has_euler_product=True,
        source="constructed in a test",
        series=lambda n_max: [0] + [1] * n_max,
    )
    result = verify_factorization(wrong, 200)
    assert result.applicable
    assert not result.agrees
    assert result.first_disagreement == 3


def test_verification_is_not_applicable_without_factors():
    """No product means nothing to check, reported rather than passed."""
    result = verify_factorization(_framework("davenport_heilbronn"))
    assert not result.applicable
    assert not result.agrees
    assert "no Euler product" in result.explanation


def test_verification_is_not_applicable_for_a_cited_factorization():
    """A cited factorisation is reported as unverified, not as passing.

    This is the honesty guard: `epstein_rectangular` has no series implemented
    here, and the difference between "checked" and "taken from the literature"
    has to survive into the output.
    """
    cited = Framework(
        id="cited",
        description="a zeta factor taken from the literature",
        factors=("zeta", "dirichlet_L_chi3"),
        has_euler_product=True,
        source="cited",
        series=None,
    )
    result = verify_factorization(cited)
    assert not result.applicable
    assert not result.agrees
    assert "cited, not verified" in result.explanation


# ============================================================
# Framework validation
# ============================================================

def test_factors_without_an_euler_product_are_rejected():
    """The two declarations are contradictory and must not be silently merged."""
    with pytest.raises(ValueError, match="no Euler product"):
        Framework(
            id="contradiction",
            description="declares factors but no Euler product",
            factors=("zeta",),
            has_euler_product=False,
            source="test",
        )


def test_unknown_factor_keys_are_rejected():
    """A typo must fail loudly rather than screen as a separate target."""
    with pytest.raises(ValueError, match="unknown factor"):
        Framework(
            id="typo",
            description="misspelled factor",
            factors=("zetaa",),
            has_euler_product=True,
            source="test",
        )


def test_factor_chain_is_printable():
    assert _framework("dedekind_gaussian").factor_chain() == "zeta * dirichlet_L_chi4"
    assert _framework("davenport_heilbronn").factor_chain() == "(no Euler product)"


def test_every_registered_factor_is_reachable():
    """No orphan rows in the factor registry."""
    used = {key for f in FRAMEWORKS for key in f.factors}
    assert set(FACTORS) >= used


# ============================================================
# The screen's verdicts
# ============================================================

def test_zeta_itself_is_its_own_case():
    """The control: `zeta` is trivially a factor of `zeta`.

    Without a separate verdict, the screen would call the target "strictly
    harder than itself", which is the kind of vacuous output that makes a screen
    untrustworthy.
    """
    result = screen_framework(_framework("riemann_zeta"))
    assert result.verdict is FrameworkVerdict.IS_THE_BASE_CASE


def test_gaussian_dedekind_zeta_is_strictly_harder():
    """The screen's answer to the Gaussian-integer proposal."""
    result = screen_framework(_framework("dedekind_gaussian"))
    assert result.verdict is FrameworkVerdict.STRICTLY_HARDER
    assert result.zeta_factors == ["zeta"]
    assert "implies RH" in result.summary
    assert "strictly bigger" in result.summary


def test_eisenstein_dedekind_zeta_is_strictly_harder():
    result = screen_framework(_framework("dedekind_eisenstein"))
    assert result.verdict is FrameworkVerdict.STRICTLY_HARDER


def test_a_lone_l_function_is_a_separate_target():
    """No zeta factor: success does not deliver RH, and no transfer is recorded."""
    result = screen_framework(_framework("dirichlet_L_chi4_alone"))
    assert result.verdict is FrameworkVerdict.SEPARATE_TARGET
    assert result.zeta_factors == []
    assert "does not imply RH" in result.summary
    assert "transfer step" in result.summary


def test_a_recorded_transfer_step_is_quoted_in_the_summary():
    """The transfer step is the content of such a proposal, so it is surfaced."""
    with_transfer = Framework(
        id="with_transfer",
        description="a lone L-function plus a stated transfer",
        factors=("dirichlet_L_chi4",),
        has_euler_product=True,
        source="test",
        series=lambda n_max: [0] + [chi_minus_4(n) for n in range(1, n_max + 1)],
        transfer_step="a positivity statement on beta that forces zeta's zeros",
    )
    result = screen_framework(with_transfer)
    assert result.verdict is FrameworkVerdict.SEPARATE_TARGET
    assert "a positivity statement on beta" in result.summary
    assert "No transfer step is recorded" not in result.summary


def test_davenport_heilbronn_is_not_a_product():
    result = screen_framework(_framework("davenport_heilbronn"))
    assert result.verdict is FrameworkVerdict.NO_EULER_PRODUCT


def test_epstein_rectangular_is_not_a_product():
    result = screen_framework(_framework("epstein_rectangular"))
    assert result.verdict is FrameworkVerdict.NO_EULER_PRODUCT


def test_verdicts_are_exactly_four():
    """No soft fourth verdict, and no path that reports 'promising'."""
    assert {v.value for v in FrameworkVerdict} == {
        "is_the_base_case",
        "strictly_harder",
        "separate_target",
        "no_euler_product",
    }


def test_the_screen_fires_on_the_registry():
    """Non-vacuity: at least one framework is caught by containment."""
    assert strictly_harder_list(screen_all())


def test_unverified_factorizations_reports_a_cited_zeta_factor():
    """A `strictly_harder` verdict resting on a citation is weaker than it looks."""
    cited = Framework(
        id="cited_zeta_factor",
        description="contains zeta, but the product is taken from the literature",
        factors=("zeta", "dirichlet_L_chi3"),
        has_euler_product=True,
        source="cited",
        series=None,
    )
    results = screen_all([cited])
    assert unverified_factorizations(results) == ["cited_zeta_factor"]


def test_verified_frameworks_are_not_listed_as_unverified():
    """The two verified rows must not appear, or the list is noise."""
    assert unverified_factorizations(screen_all()) == []


# ============================================================
# The lists partition, and the cross-check with dh_filter
# ============================================================

def test_the_three_lists_partition_the_registry():
    """Every framework lands in exactly one list."""
    results = screen_all()
    classified = (
        strictly_harder_list(results)
        + separate_target_list(results)
        + no_euler_product_list(results)
    )
    # `is_the_base_case` is outside the three, so the base case is excluded.
    assert len(classified) == len(results) - 1
    assert "riemann_zeta" not in " ".join(classified)


def test_davenport_heilbronn_coefficients_match_dh_filter():
    """The no-Euler-product row is checked against the module that derives them.

    Reimplementing the coefficients here would allow the two modules to drift
    apart while both looking self-consistent.
    """
    table = dh_coefficients(60)
    mine = davenport_heilbronn_coefficients(60)
    assert len(mine) == 61
    for n in range(1, 61):
        assert abs(mine[n] - float(table[n])) < 1e-15


def test_davenport_heilbronn_coefficients_are_not_integers():
    """A guard on the rounding bug this helper had in its first draft.

    `b(n)` takes the values `(1, kappa, -kappa, -1, 0)`, and `kappa` is
    irrational, so rounding to integers would erase two of the five residue
    classes while still leaving a table that looks like coefficients.
    """
    mine = davenport_heilbronn_coefficients(30)
    assert any(abs(v - round(v)) > 1e-9 for v in mine[1:31])
    assert mine[1] == pytest.approx(1.0)
    assert mine[2] == pytest.approx(0.28407904384041229603, abs=1e-15)
    assert mine[3] == pytest.approx(-0.28407904384041229603, abs=1e-15)


def test_davenport_heilbronn_coefficients_are_not_multiplicative():
    """The arithmetic reason the framework row has no Euler product.

    Same witness as `dh_filter` uses: `b(2) b(3) != b(6)`. Stated here too so
    the `no_euler_product` verdict does not rest only on a citation.

    Note the failure is *not* witnessed by every pair, which is why the witness
    is named rather than assumed. `b` is periodic mod 5 with values
    `(1, kappa, -kappa, -1, 0)`, so `b(2) b(4) = -kappa = b(8)` holds by
    accident of the period: the pair tests multiplicativity at `n = 8` and `8`
    lands on residue 3, exactly where `2 * 4` lands. An earlier draft of this
    test asserted that *all* pairs in `2..5` fail, and `(2, 4)` refuted it.
    """
    table = davenport_heilbronn_coefficients(30)

    def fails(m: int, n: int) -> bool:
        return abs(table[m] * table[n] - table[m * n]) > 1e-9

    assert fails(2, 3)
    assert abs(table[2] * table[3] - table[6]) > 0.5

    failing = [(m, n) for m in range(2, 21) for n in range(2, 21) if m * n <= 30 and fails(m, n)]
    assert failing, "coefficients would be multiplicative, contradicting no Euler product"
    assert len(failing) >= 5

    # The accident, pinned so the witness above is understood as necessary
    # rather than as one of a uniform family.
    assert not fails(2, 4)
