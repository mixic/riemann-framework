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
"""Tests for the BB84 implementation layer: source, detectors, and PNS.

The central claim under test is an *indistinguishability*: under photon-number
splitting the gain and the error rate are exactly the honest channel's, while the
eavesdropper's information rises toward one. That is what makes the attack
invisible to the protocol layer, so it is asserted directly rather than inferred
from the formula.
"""

import math

import numpy as np
import pytest

from riemann_framework.bb84 import run_bb84
from riemann_framework.bb84_implementation import (
    dark_count_yield,
    decoy_free_bound,
    decoy_state_report,
    gain_and_error_rate,
    lower_bound_Y1,
    n_photon_yield,
    pns_attack,
    pns_information_fraction,
    poisson_photon_distribution,
    single_photon_contribution,
    source_fractions,
    upper_bound_e1,
)

# A representative short-reach implemented link.
ETA = 0.1
E_DET = 0.01
P_DARK = 1e-6


# ============================================================
# The source
# ============================================================

@pytest.mark.parametrize("mu", [0.1, 0.5, 1.0, 2.0])
def test_poisson_distribution_is_normalised(mu):
    p = poisson_photon_distribution(mu, n_max=60)
    assert p.sum() == pytest.approx(1.0, abs=1e-12)
    assert p[0] == pytest.approx(math.exp(-mu), rel=1e-12)
    assert p[1] == pytest.approx(mu * math.exp(-mu), rel=1e-12)


def test_multi_photon_fraction_has_the_closed_form():
    """`P(n >= 2) = 1 - e^-mu (1 + mu)`, the quantity PNS feeds on."""
    for mu in (0.1, 0.5, 1.0, 2.0):
        expected = 1.0 - math.exp(-mu) * (1.0 + mu)
        assert source_fractions(mu)["multi"] == pytest.approx(expected, rel=1e-12)


def test_source_fractions_are_the_measured_attenuation_numbers():
    """At `mu = 0.5` a real WCP source is mostly vacuum -- 61% / 30% / 9%.

    Pinned because the headline point depends on the multi-photon fraction being
    small but not zero: at `mu = 0.5` nine per cent of pulses carry two or more
    photons, and that is enough to matter.
    """
    fractions = source_fractions(0.5)
    assert fractions["vacuum"] == pytest.approx(0.606531, abs=1e-6)
    assert fractions["single"] == pytest.approx(0.303265, abs=1e-6)
    assert fractions["multi"] == pytest.approx(0.090204, abs=1e-6)
    assert fractions["vacuum"] + fractions["single"] + fractions["multi"] == (
        pytest.approx(1.0, abs=1e-12)
    )


def test_the_idealised_module_cannot_represent_this():
    """`bb84.py` has no photon number at all: every round is one ideal qubit.

    The contrast is the reason this module exists. With no dark counts and no
    source model the idealised run has zero errors and no quantity that could
    carry an eavesdropper's information.
    """
    ideal = run_bb84(n_bits=2000, seed=42)
    assert ideal.ber == 0.0
    assert ideal.sifted_length > 0

    # The implementation layer's gain is a *rate*, not a per-round certainty.
    stats = gain_and_error_rate(0.5, ETA, E_DET, P_DARK)
    assert 0.0 < stats["Q_mu"] < 1.0


# ============================================================
# Detectors and gain
# ============================================================

def test_dark_count_yield_is_exact_not_linearised():
    assert dark_count_yield(0.0) == 0.0
    assert dark_count_yield(1e-6) == pytest.approx(2e-6 - 1e-12, rel=1e-12)
    # The exact form keeps the mu -> 0 limit equal to Y_0 rather than near it.
    # `mu` must stay strictly positive (the module rejects 0), so this uses a
    # value whose photonic contribution is far below the tolerance.
    assert gain_and_error_rate(1e-15, ETA, E_DET, 1e-4)["Q_mu"] == (
        pytest.approx(dark_count_yield(1e-4), rel=1e-12)
    )


def test_closed_form_gain_matches_the_explicit_poisson_sum():
    """Independent check: `Q_mu = sum_n p_n Y_n` recomputed by brute force.

    The implementation uses the closed form `1 - (1 - Y_0) e^{-eta mu}`. Summing
    the Poisson weights against the per-n yields is a different computation, so
    agreement is evidence rather than a tautology.
    """
    for mu in (0.1, 0.5, 1.0, 2.0):
        p = poisson_photon_distribution(mu, n_max=80)
        y_0 = dark_count_yield(P_DARK)
        brute = sum(
            p[n] * (y_0 if n == 0 else n_photon_yield(n, ETA, P_DARK))
            for n in range(len(p))
        )
        assert gain_and_error_rate(mu, ETA, E_DET, P_DARK)["Q_mu"] == (
            pytest.approx(brute, rel=1e-9)
        )


def test_gain_and_error_limits():
    """`mu -> 0`: dark counts only, so `E_mu -> 1/2`. Large `eta mu`: `E_mu -> e_det`.

    The `mu` values are chosen against `eta`: `Q_mu = 1 - (1 - Y_0) e^{-eta mu}`
    reaches 1 only when `eta mu` is large, so the large-`mu` end uses `mu = 200`
    at `eta = 0.1` rather than a merely big-looking number.
    """
    tiny = gain_and_error_rate(1e-12, ETA, E_DET, P_DARK)
    assert tiny["E_mu"] == pytest.approx(0.5, abs=1e-6)
    assert tiny["Q_mu"] == pytest.approx(tiny["Y_0"], rel=1e-9)

    large = gain_and_error_rate(200.0, ETA, E_DET, 0.0)
    assert large["Q_mu"] == pytest.approx(1.0, abs=1e-8)
    assert large["E_mu"] == pytest.approx(E_DET, rel=1e-8)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"mu": 0.0, "eta": ETA}, "mu"),
        ({"mu": -1.0, "eta": ETA}, "mu"),
        ({"mu": 0.5, "eta": 1.5}, "eta"),
        ({"mu": 0.5, "eta": ETA, "e_det": 0.9}, "e_det"),
    ],
)
def test_gain_rejects_impossible_parameters(kwargs, match):
    """`eta` is supplied every time: it is required, and omitting it raises
    `TypeError` rather than the `ValueError` this test is about."""
    with pytest.raises(ValueError, match=match):
        gain_and_error_rate(**kwargs)


def test_single_photon_error_rate_is_below_the_overall_one():
    """`e_1 < E_mu`: single-photon pulses are less error-prone than the average.

    The average is dragged up by dark counts, which are random. This is why the
    single-photon fraction is the resource a decoy analysis is trying to isolate.
    """
    stats = gain_and_error_rate(0.5, ETA, E_DET, P_DARK)
    single = single_photon_contribution(0.5, ETA, E_DET, P_DARK)
    assert single["e_1"] < stats["E_mu"]


# ============================================================
# PNS: the attack the protocol layer cannot see
# ============================================================

def test_pns_introduces_no_errors_and_leaves_the_observables_alone():
    """The indistinguishability claim, asserted rather than inferred.

    Eve's forwarded photons are the state Alice prepared, so the measured gain and
    error rate are *exactly* the honest channel's. Nothing in Alice and Bob's data
    changes.
    """
    for mu in (0.1, 0.5, 1.0, 2.0):
        honest = gain_and_error_rate(mu, ETA, E_DET, P_DARK)
        attack = pns_attack(mu, ETA, E_DET, P_DARK)
        assert attack.additional_qber == 0.0
        assert attack.Q_mu == honest["Q_mu"]
        assert attack.E_mu == honest["E_mu"]


def test_pns_information_rises_with_mu_while_the_error_rate_does_not():
    """The decisive table: information grows, the observable does not move.

    Sweeping `mu` from 0.1 to 5 raises Eve's information from about 0.09 to about
    0.99, while `E_mu` stays within 1e-3 of `e_det` across the whole sweep. A
    detector watching the error rate sees a healthy channel throughout.
    """
    mus = (0.1, 0.3, 0.5, 1.0, 2.0, 5.0)
    fractions = [pns_information_fraction(mu, ETA, E_DET, P_DARK) for mu in mus]
    errors = [pns_attack(mu, ETA, E_DET, P_DARK).E_mu for mu in mus]

    assert fractions == sorted(fractions), fractions
    assert fractions[0] == pytest.approx(0.09, abs=0.01)
    assert fractions[-1] > 0.99
    assert max(errors) - min(errors) < 1e-3
    assert all(abs(e - E_DET) < 1e-3 for e in errors)


def test_pns_can_take_everything_as_mu_grows():
    """In the large-`mu` limit the source is all multi-photon and Eve knows all.

    `mu = 50` rather than a round small number: the residual is `p_1 Y_1 / Q_mu`
    with `p_1 = mu e^-mu`, which is about `1e-20` there.
    """
    report = pns_attack(50.0, ETA, E_DET, P_DARK)
    assert report.eve_knows_everything
    assert report.information_fraction == pytest.approx(1.0, abs=1e-9)


def test_multi_photon_gain_is_a_subset_of_the_total_gain():
    for mu in (0.1, 0.5, 1.0, 2.0):
        report = pns_attack(mu, ETA, E_DET, P_DARK)
        assert 0.0 <= report.Q_multi <= report.Q_mu
        assert 0.0 <= report.information_fraction <= 1.0


def test_pns_report_says_what_was_measured_and_what_was_learned():
    report = pns_attack(0.5, ETA, E_DET, P_DARK)
    assert "no errors" in report.explanation
    assert f"{report.information_fraction:.4f}" in report.explanation


# ============================================================
# What Alice and Bob can conclude
# ============================================================

def test_decoy_free_bound_is_positive_under_the_honest_assumption():
    bound = decoy_free_bound(0.5, ETA, E_DET, P_DARK)
    assert bound["rate_if_channel_honest"] > 0.0


def test_decoy_free_bound_is_not_valid_for_all_consistent_channels():
    """The finding: the number a decoy-free implementation reports is an assumption.

    Eve's blocking of single-photon pulses changes `Q_1` without changing `Q_mu` or
    `E_mu`, so the observed data permit `Q_1 / Q_mu = 0`. The rate computed at the
    honest value is positive; the worst case consistent with the data is negative.
    A bound that fails for an admissible channel is not a bound.
    """
    for mu in (0.1, 0.3, 0.5, 1.0):
        bound = decoy_free_bound(mu, ETA, E_DET, P_DARK)
        assert bound["rate_if_channel_honest"] > 0.0, mu
        assert bound["worst_case_rate"] < 0.0, mu
        assert bound["assumption_is_load_bearing"], mu


def test_the_bound_and_the_attack_disagree_by_construction():
    """Alice and Bob's rate says "secure"; the attack says otherwise, at once.

    Not a contradiction -- it is the difference between a protocol result and an
    implementation result. The rate is computed from an assumption the attack
    invalidates, and the attack supplies the information the rate assumes away.
    """
    bound = decoy_free_bound(0.5, ETA, E_DET, P_DARK)
    report = pns_attack(0.5, ETA, E_DET, P_DARK)
    assert bound["rate_if_channel_honest"] > 0.0
    assert report.information_fraction > 0.3
    assert bound["pns_information_fraction"] == pytest.approx(
        report.information_fraction, rel=1e-12
    )


def test_worst_case_rate_is_monotone_in_the_error_rate():
    """With `Q_1` unknown, the rate is `-(1/2) f_ec Q_mu H_2(E_mu)`: worse as errors rise."""
    low = decoy_free_bound(0.5, ETA, e_det=0.001, p_dark=P_DARK)
    high = decoy_free_bound(0.5, ETA, e_det=0.05, p_dark=P_DARK)
    assert high["worst_case_rate"] < low["worst_case_rate"] <= 0.0


def test_poisson_truncation_mass_is_reported_and_negligible():
    """`source_fractions` reports the mass it left out rather than hiding it."""
    for mu in (0.5, 2.0, 5.0):
        fractions = source_fractions(mu, n_max=60)
        assert fractions["truncation_mass"] < 1e-12
        assert np.isclose(
            fractions["vacuum"] + fractions["single"] + fractions["multi"],
            1.0,
        )


# ============================================================
# Decoy states: the bounds, checked against the model
# ============================================================

def test_the_vacuum_weak_bound_agrees_with_the_general_two_decoy_formula():
    """The transcription check: two published forms of the same bound must agree.

    Ma-Qi-Zhao-Lo give a general two-decoy expression in `(nu, nu_1)`. Setting
    `nu_1 = 0` -- the vacuum -- must reproduce the vacuum+weak expression the
    module implements. Evaluating both symbolically indepenently here is what
    makes the implemented form attributable to the source rather than recalled.
    """
    def general(mu, nu, nu_1, Q_mu, Q_nu, Q_nu1, Y_0):
        numerator = mu * (
            math.exp(nu) * Q_nu
            - math.exp(nu_1) * Q_nu1
            - (nu**2 - nu_1**2) / mu**2 * (math.exp(mu) * Q_mu - Y_0)
        )
        return numerator / (mu * (nu - nu_1) - (nu**2 - nu_1**2))

    for mu, nu in ((0.5, 0.1), (0.5, 0.2), (1.0, 0.15), (0.8, 0.05)):
        Q_mu = gain_and_error_rate(mu, ETA, E_DET, P_DARK)["Q_mu"]
        Q_nu = gain_and_error_rate(nu, ETA, E_DET, P_DARK)["Q_mu"]
        y_0 = dark_count_yield(P_DARK)
        at_vacuum = general(mu, nu, 0.0, Q_mu, Q_nu, y_0, y_0)
        assert lower_bound_Y1(mu, nu, Q_mu, Q_nu, y_0) == pytest.approx(
            at_vacuum, rel=1e-12
        )


def test_Y1_lower_bound_is_valid_across_a_parameter_sweep():
    """The bound must hold everywhere, and this is what catches a wrong formula.

    `Y_1^L <= Y_1` and `e_1^U >= e_1` are checked against the channel model that
    generated the data -- a real implementation does not know the true values, but
    a simulation does, which is exactly what makes the bound testable. A
    mis-transcribed exponent shows up here immediately rather than in production.
    """
    checked = 0
    for mu in (0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2):
        for nu in (0.05, 0.1, 0.15, 0.2, 0.3):
            if nu >= mu:
                continue
            for eta in (0.01, 0.05, 0.1, 0.3, 0.5):
                for p_dark in (0.0, 1e-6, 1e-4):
                    report = decoy_state_report(mu, nu, eta, E_DET, p_dark)
                    assert report.bounds_are_valid, (mu, nu, eta, p_dark)
                    assert report.Y_1_lower <= report.Y_1_true + 1e-12
                    assert report.e_1_upper >= report.e_1_true - 1e-12
                    assert 0.0 <= report.e_1_upper <= 0.5
                    checked += 1
    assert checked > 400


def test_Y1_lower_bound_tightens_as_the_decoy_weakens():
    """The bound approaches the truth as `nu -> 0`, which is the published limit.

    This is why the source recommends weak decoys: the correction term is
    quadratic in `nu`, so a decoy an order of magnitude below the signal is
    already within a few per cent.
    """
    tightness = [
        decoy_state_report(0.5, nu, ETA, E_DET, P_DARK).Y_1_is_tight
        for nu in (0.05, 0.1, 0.2, 0.3)
    ]
    assert tightness == sorted(tightness, reverse=True), tightness
    assert tightness[0] > 0.98
    assert tightness[-1] < tightness[0]
    assert all(0.0 < t <= 1.0 for t in tightness)


def test_decoy_rate_is_below_the_unsupported_number_and_above_the_worst_case():
    """What decoys buy is a *valid* number, not a bigger one.

    The decoy rate is computed from measured decoy data, so it is sound; it sits
    below the decoy-free figure, which was larger only because it assumed a
    single-photon fraction nobody measured, and far above the worst case.
    """
    report = decoy_state_report(0.5, 0.1, ETA, E_DET, P_DARK)
    assert report.rate_decoy_free_worst < 0.0
    assert 0.0 < report.rate_decoy < report.rate_decoy_free_honest
    assert report.rate_decoy > report.rate_decoy_free_worst
    # ... and it is close to the unsupported figure: decoys cost little rate.
    assert report.rate_decoy > 0.95 * report.rate_decoy_free_honest


def test_the_analysis_never_raises_over_its_whole_input_domain():
    """The detection tool must survive every legitimate parameter choice.

    `decoy_state_report` is what an operator runs to *find* suppression, so it
    must not raise on any intensity pair, however badly chosen. This sweeps the
    domain, including decoys very close to the signal where the bound is weakest.
    """
    count = 0
    for mu in (0.3, 0.5, 1.0):
        for nu in (0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.45, 0.499):
            if nu >= mu:
                continue
            for eta in (1e-4, 0.01, 0.1, 0.5):
                report = decoy_state_report(mu, nu, eta, E_DET, P_DARK)
                assert isinstance(report.rate_decoy, float)
                count += 1
    assert count >= 60


def test_a_vacuous_bound_yields_a_non_positive_rate_by_construction():
    """The vacuous branch's arithmetic: with `Q_1^L = 0` no key can be extracted.

    Reproducing the branch through the honest channel model is not possible -- an
    unsuppressed channel always gives a positive bound -- so the branch is pinned
    where it is decidable: the bound itself goes negative under suppression, and
    the rate expression with `Q_1^L = 0` is `-(1/2) Q_mu f_ec H_2(E_mu)`, which is
    negative. Together those are what the branch returns.
    """
    y_0 = dark_count_yield(P_DARK)
    q_mu = gain_and_error_rate(0.5, ETA, E_DET, P_DARK)["Q_mu"]
    assert lower_bound_Y1(0.5, 0.1, q_mu, y_0, y_0) < 0.0

    stats = gain_and_error_rate(0.5, ETA, E_DET, P_DARK)
    from riemann_framework.bb84_implementation import binary_entropy

    rate_with_no_singles = 0.5 * (-stats["Q_mu"] * 1.16 * binary_entropy(stats["E_mu"]))
    assert rate_with_no_singles < 0.0

    # And the honest report is *not* vacuous, so the flag discriminates.
    assert decoy_state_report(0.5, 0.1, ETA, E_DET, P_DARK).bound_is_vacuous is False


def test_vacuous_bound_is_still_a_valid_bound():
    """A vacuous lower bound is not a false one: `Y_1^L <= Y_1` still holds."""
    y_0 = dark_count_yield(P_DARK)
    q_mu = gain_and_error_rate(0.5, ETA, E_DET, P_DARK)["Q_mu"]
    assert lower_bound_Y1(0.5, 0.1, q_mu, y_0, y_0) < 0.0
    assert lower_bound_Y1(0.5, 0.1, q_mu, y_0, y_0) <= n_photon_yield(1, ETA, P_DARK)


def test_decoy_helpers_reject_degenerate_intensities():
    with pytest.raises(ValueError, match="0 < nu < mu"):
        lower_bound_Y1(0.5, 0.5, 0.05, 0.01, 1e-6)
    with pytest.raises(ValueError, match="0 < nu < mu"):
        lower_bound_Y1(0.5, 0.6, 0.05, 0.01, 1e-6)
    with pytest.raises(ValueError, match="0 < nu < mu"):
        lower_bound_Y1(0.5, 0.0, 0.05, 0.01, 1e-6)


def test_e1_upper_bound_is_capped_at_one_half():
    """A usable error rate ends at 1/2; past it the bits are anti-correlated.

    The cap is also conservative, since `H_2` is decreasing beyond 1/2 and capping
    therefore lowers the rate rather than raising it.
    """
    assert upper_bound_e1(0.1, 1e-3, 0.9, 1e-9, 1e-6) == 0.5


def test_decoy_report_explains_itself():
    report = decoy_state_report(0.5, 0.1, ETA, E_DET, P_DARK)
    assert "Y_1^L" in report.explanation
    assert f"{report.rate_decoy:+.6f}" in report.explanation
