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
"""Tests for the BB84 detector-blinding model.

The test that matters is the asymmetry: ordinary intercept-resend is caught by the
error-rate statistic and blinding is not. A suite that only checked "the attack
works" would have missed the reason the attack matters.
"""

from __future__ import annotations

import pytest

from riemann_framework.bb84_detector import (
    DEFAULT_BLINDING_THRESHOLD,
    INTERCEPT_RESEND_QBER,
    SECURITY_THRESHOLD,
    DetectorModel,
    attack_comparison,
    blinding_attack,
    detector_report,
    is_blinded,
    power_monitor_roc,
    randomized_efficiency_defence,
)


# ============================================================
# The detector model
# ============================================================

def test_the_blinding_threshold_is_a_step():
    assert not is_blinded(1.0)
    assert not is_blinded(DEFAULT_BLINDING_THRESHOLD - 1.0)
    assert is_blinded(DEFAULT_BLINDING_THRESHOLD)
    assert is_blinded(1.0e6)


def test_a_custom_threshold_moves_the_boundary():
    detector = DetectorModel(blinding_threshold=10.0)
    assert is_blinded(10.0, detector)
    assert not is_blinded(9.0, detector)


def test_detector_validation():
    with pytest.raises(ValueError):
        DetectorModel(efficiency=0.0)
    with pytest.raises(ValueError):
        DetectorModel(efficiency=1.5)
    with pytest.raises(ValueError):
        DetectorModel(dark_count=-0.1)
    with pytest.raises(ValueError):
        DetectorModel(blinding_threshold=0.0)
    with pytest.raises(ValueError):
        is_blinded(-1.0)


# ============================================================
# The attack
# ============================================================

def test_a_blinded_attack_has_zero_error_and_full_information():
    """**The finding.** QBER 0 while Eve holds a full bit per sifted bit."""
    report = blinding_attack(power=1.0e6, rounds=800, seed=0)
    assert report.blinded_fraction == 1.0
    assert report.qber == 0.0
    assert report.eve_information == pytest.approx(1.0)
    assert not report.detected_by_qber
    assert report.compromised


def test_an_unblinded_attempt_behaves_like_intercept_resend():
    """Below the threshold the bright pulse does not help: QBER 0.25, and it is caught."""
    report = blinding_attack(power=1.0, rounds=800, seed=0)
    assert report.blinded_fraction == 0.0
    assert report.qber == pytest.approx(INTERCEPT_RESEND_QBER, abs=0.06)
    assert report.detected_by_qber
    assert not report.compromised


def test_the_attack_loses_the_rounds_where_eve_gets_no_click():
    """Eve's own detector efficiency is the only thing she pays."""
    report = blinding_attack(power=1.0e6, rounds=2000, seed=0)
    assert 0 < report.sifted_rounds < report.rounds


def test_blinding_attack_validation():
    with pytest.raises(ValueError):
        blinding_attack(power=-1.0)
    with pytest.raises(ValueError):
        blinding_attack(rounds=0)


def test_intercept_resend_is_caught_and_blinding_is_not():
    """The asymmetry, in one object: the same statistic, two verdicts."""
    comparison = attack_comparison(power=1.0e6, rounds=800, seed=0)
    assert comparison.intercept_resend_qber >= SECURITY_THRESHOLD
    assert comparison.blinding.qber < SECURITY_THRESHOLD
    assert comparison.blinding.eve_information > 0.99
    text = comparison.summary()
    assert "sees one attack and not the other" in text


# ============================================================
# Countermeasure 1: the power monitor
# ============================================================

def test_the_power_monitor_catches_the_attack():
    for row in power_monitor_roc(thresholds=(10.0, 50.0, 100.0)):
        assert row.attack_alert_rate > 0.95


def test_the_monitor_false_alarm_rate_falls_with_the_threshold():
    rows = power_monitor_roc(thresholds=(1.0, 5.0, 10.0, 50.0))
    rates = [row.honest_false_alarm_rate for row in rows]
    assert rates == sorted(rates, reverse=True)
    assert rows[0].honest_false_alarm_rate > 0.1
    assert rows[-1].honest_false_alarm_rate < 1e-9


def test_the_monitor_separates_the_two_populations_by_orders_of_magnitude():
    """Honest pulses carry 0.5 photons; the attack needs 1e6. That gap is the defence."""
    rows = power_monitor_roc(thresholds=(10.0,), honest_mean=0.5)
    row = rows[0]
    assert row.attack_alert_rate > 0.99
    assert row.honest_false_alarm_rate < 1e-9


def test_power_monitor_validation():
    with pytest.raises(ValueError):
        power_monitor_roc(attack_power=0.0)
    with pytest.raises(ValueError):
        power_monitor_roc(honest_mean=-1.0)


# ============================================================
# Countermeasure 2: randomised efficiency (partial)
# ============================================================

def test_randomised_efficiency_raises_the_error_rate_monotonically():
    rows = randomized_efficiency_defence()
    rates = [row.qber for row in rows]
    assert rates == sorted(rates)
    assert rates[0] == 0.0


def test_large_randomisation_is_needed_before_it_is_detected():
    """A 20% randomisation leaves QBER 0.10, still under the 0.11 abort threshold."""
    rows = {row.randomisation: row for row in randomized_efficiency_defence()}
    assert rows[0.2].qber < SECURITY_THRESHOLD
    assert not rows[0.2].detected
    assert rows[0.5].detected


def test_randomised_efficiency_validation():
    with pytest.raises(ValueError):
        randomized_efficiency_defence(randomisations=(1.5,))


# ============================================================
# The report
# ============================================================

def test_the_report_states_both_halves():
    report = detector_report(power=1.0e6, rounds=600, seed=0)
    assert report.error_rate_blind_to_the_attack
    assert report.monitor_works
    verdict = report.verdict()
    assert "does not see the attack" in verdict
    assert "power monitor" in verdict
    assert "Model, not a security proof" in verdict
    assert "no RH evidence" in verdict


def test_the_constants_are_the_documented_ones():
    assert SECURITY_THRESHOLD == 0.11
    assert INTERCEPT_RESEND_QBER == 0.25
    assert DEFAULT_BLINDING_THRESHOLD == 1.0e3
