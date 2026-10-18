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
"""BB84 detector blinding: the attack, and the countermeasure that actually works.

`bb84_implementation.py` models the photon source, the photon-number-splitting
attack, the decoy-state mitigation and finite-key statistics. It states, correctly,
that **detector blinding and timing/Trojan-horse channels are not modelled**. This
module closes the first of those gaps.

The attack (Lydersen et al., *Hacking commercial quantum cryptography systems by
tailored bright illumination*, Nature Photonics 4, 686 (2010)) does not attack the
photons. It attacks the *detector*: a bright pulse drives the avalanche photodiode
out of Geiger mode into linear mode, where its output is proportional to the
incident power instead of saturating. A calibrated bright pulse then makes a
*chosen* detector fire, so Bob's announced bit is the attacker's bit in every round,
whatever basis he chose. The sifted key equals Eve's bits, so the measured error
rate is **zero** -- the attack is invisible to the statistic BB84 uses to detect
eavesdropping.

What this module measures
-------------------------
* `blinding_threshold` / `is_blinded`: when a detector leaves Geiger mode.
* `blinding_attack`: sifted-key QBER, Eve's information, and the fraction of rounds
  the attack actually controls, as a function of the illuminating power.
* `power_monitor_roc`: the countermeasure that works -- a monitor on the incoming
  optical power. Swept over its threshold, so the trade-off between catching the
  attack and false-alarming on honest pulses is visible rather than asserted.
* `randomized_efficiency_defence`: the countermeasure that *partially* works --
  randomising the two detectors' efficiencies so a calibrated pulse cannot force a
  specific click.
* `attack_comparison`: blinding against ordinary intercept-resend, in one table.

The honest boundary
-------------------
This is a **model**, not a security proof, and it makes no claim about any deployed
system. The linear-mode response is idealised (a step from Geiger to linear), the
monitor is idealised (Poisson photon statistics, no dark counts, no
afterpulsing), and the countermeasures are evaluated as mechanisms rather than as
guarantees. What it does establish is the shape of the problem: the error-rate
statistic cannot see this attack, and an optical power monitor can, at a quantified
false-alarm cost.

Nothing here is evidence about the Riemann hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, factorial

import numpy as np


#: Typical single-photon detection efficiency of a commercial InGaAs APD.
DEFAULT_EFFICIENCY = 0.1

#: Dark-count probability per gate.
DEFAULT_DARK_COUNT = 1e-5

#: Mean photon number per pulse above which the detector is taken to be blinded.
#: A bright-illumination attack uses six or more orders of magnitude above this.
DEFAULT_BLINDING_THRESHOLD = 1.0e3

#: Sifted-key error rate above which BB84 aborts (`bb84.py` uses the same value).
SECURITY_THRESHOLD = 0.11

#: The error rate a plain intercept-resend attack produces, for comparison.
INTERCEPT_RESEND_QBER = 0.25


@dataclass(frozen=True)
class DetectorModel:
    """A two-detector Bob, with the linear-mode parameters the attack exploits."""

    efficiency: float = DEFAULT_EFFICIENCY
    dark_count: float = DEFAULT_DARK_COUNT
    blinding_threshold: float = DEFAULT_BLINDING_THRESHOLD

    def __post_init__(self) -> None:
        if not 0.0 < self.efficiency <= 1.0:
            raise ValueError("efficiency must be in (0, 1]")
        if not 0.0 <= self.dark_count < 1.0:
            raise ValueError("dark_count must be in [0, 1)")
        if self.blinding_threshold <= 0.0:
            raise ValueError("blinding_threshold must be positive")


def is_blinded(power: float, detector: DetectorModel | None = None) -> bool:
    """Does illumination at `power` mean photons per pulse blind the detector?

    A step function: below the threshold the detector is in Geiger mode (saturating,
    single-photon sensitive); above it the response is linear and the attacker can
    choose which detector fires. Real APDs have a transition region; the idealisation
    is stated in the module docstring and is what makes the boundary measurable.
    """
    if power < 0.0:
        raise ValueError("power must be non-negative")
    detector = detector or DetectorModel()
    return power >= detector.blinding_threshold


# ============================================================
# The attack
# ============================================================

@dataclass(frozen=True)
class BlindingReport:
    """What one blinding attack achieved, at one illuminating power."""

    power: float
    rounds: int
    blinded_fraction: float
    sifted_rounds: int
    qber: float
    eve_information: float
    monitor_alert_rate: float
    detected_by_qber: bool

    @property
    def compromised(self) -> bool:
        """Full information with an error rate below the abort threshold."""
        return self.eve_information > 0.99 and self.qber < SECURITY_THRESHOLD

    def summary(self) -> str:
        return (
            f"power {self.power:9.1f}: blinded {self.blinded_fraction:5.1%}, "
            f"sifted {self.sifted_rounds:5d}, QBER {self.qber:.4f}, "
            f"Eve {self.eve_information:.3f} bits, monitor alert "
            f"{self.monitor_alert_rate:.3f}, caught by QBER "
            f"{self.detected_by_qber}"
        )


def blinding_attack(
    power: float = 1.0e6,
    rounds: int = 2000,
    detector: DetectorModel | None = None,
    monitor_threshold: float | None = None,
    seed: int = 0,
) -> BlindingReport:
    """Simulate Eve's intercept-resend with bright illumination.

    Per round: Eve measures in the rectilinear basis and keeps the round only if her
    detector fires (probability `efficiency`, plus dark counts). She then illuminates
    a *chosen* detector with mean photon number `power` and resends her bit.

    * If the detector is blinded, the chosen detector fires deterministically, so
      Bob's announced bit is Eve's bit whatever basis he used, and the sifted-key
      error rate is `0`.
    * If it is not blinded, the bright pulse is a multi-photon pulse in Geiger mode:
      the resend behaves like ordinary intercept-resend, `QBER = 0.25`.

    `monitor_threshold` (mean photons per pulse) adds a power monitor: an alert on
    any pulse whose photon number reaches it. Pulses are Poisson, so honest rounds
    false-alarm with probability `P(N >= threshold | mu)` and blinded rounds are
    caught with probability `P(N >= threshold | power)`.
    """
    if power < 0.0:
        raise ValueError("power must be non-negative")
    if rounds < 1:
        raise ValueError("rounds must be at least 1")
    detector = detector or DetectorModel()
    rng = np.random.default_rng(seed)

    blinded = is_blinded(power, detector)
    sifted = 0
    errors = 0
    information = 0.0
    alerts = 0

    for _ in range(rounds):
        # Eve's measurement: a click gives her the bit.
        if rng.random() >= detector.efficiency and rng.random() >= detector.dark_count:
            continue
        # Bob's basis matches Alice's half the time; only those rounds sift.
        if rng.random() >= 0.5:
            continue
        sifted += 1
        if blinded:
            # Forced click: Bob announces Eve's bit. No error by construction.
            information += 1.0
        else:
            # Ordinary intercept-resend accuracy, and only half the information.
            information += 0.5
            if rng.random() < INTERCEPT_RESEND_QBER:
                errors += 1
        if monitor_threshold is not None:
            mean = power if blinded else 0.1
            if _poisson_tail_at_least(monitor_threshold, mean, rng):
                alerts += 1

    qber = errors / sifted if sifted else 0.0
    return BlindingReport(
        power=power,
        rounds=rounds,
        blinded_fraction=1.0 if blinded else 0.0,
        sifted_rounds=sifted,
        qber=qber,
        eve_information=information / sifted if sifted else 0.0,
        monitor_alert_rate=alerts / sifted if sifted else 0.0,
        detected_by_qber=qber >= SECURITY_THRESHOLD,
    )


def _poisson_tail_at_least(threshold: float, mean: float, rng: np.random.Generator) -> bool:
    """Is a `Poisson(mean)` draw at least `threshold`? Exact small-mean, sampled large."""
    if mean <= 0.0:
        return threshold <= 0.0
    if threshold > 1e3:
        # Normal approximation is adequate at these means and much cheaper.
        return rng.normal(mean, np.sqrt(mean)) >= threshold
    draw = 0
    # Exact Poisson sampling by inversion, then compare.
    u = rng.random()
    cumulative = exp(-mean)
    total = cumulative
    while u > total and draw < 10000:
        draw += 1
        cumulative *= mean / draw
        total += cumulative
    return draw >= threshold


# ============================================================
# Countermeasure 1: an optical power monitor (this one works)
# ============================================================

@dataclass(frozen=True)
class MonitorRow:
    """One monitor threshold: attack caught, honest pulses false-alarmed."""

    threshold: float
    attack_alert_rate: float
    honest_false_alarm_rate: float

    def summary(self) -> str:
        return (
            f"monitor >= {self.threshold:7.1f} photons: attack caught "
            f"{self.attack_alert_rate:5.1%}, honest false alarm "
            f"{self.honest_false_alarm_rate:.2e}"
        )


def power_monitor_roc(
    thresholds: tuple[float, ...] = (1.0, 5.0, 10.0, 50.0, 100.0),
    attack_power: float = 1.0e6,
    honest_mean: float = 0.5,
    seed: int = 0,
) -> list[MonitorRow]:
    """The trade-off the monitor has to make, measured.

    A monitor catches the attack when the illuminating power reaches its threshold,
    and false-alarms on an honest pulse when Poisson noise does. Because the attack
    needs a thousand photons or more and the honest pulses carry `0.5`, the two
    populations are separated by three orders of magnitude and the trade-off is easy
    -- which is exactly why this countermeasure works and why the error-rate
    statistic does not.
    """
    if attack_power <= 0.0 or honest_mean < 0.0:
        raise ValueError("powers must be non-negative and attack_power positive")
    rng = np.random.default_rng(seed)
    rows: list[MonitorRow] = []
    for threshold in thresholds:
        attack_hits = sum(
            _poisson_tail_at_least(threshold, attack_power, rng) for _ in range(2000)
        )
        # Honest false alarm computed exactly from the tail, not sampled: the rate
        # is small enough that sampling would report zero by construction.
        honest_tail = _poisson_tail_probability_at_least(threshold, honest_mean)
        rows.append(
            MonitorRow(
                threshold=threshold,
                attack_alert_rate=attack_hits / 2000,
                honest_false_alarm_rate=honest_tail,
            )
        )
    return rows


def _poisson_tail_probability_at_least(threshold: float, mean: float) -> float:
    """`P(N >= threshold)` for `N ~ Poisson(mean)`, exactly for integer thresholds."""
    if threshold <= 0:
        return 1.0
    if mean == 0.0:
        return 0.0
    if threshold > 200:
        return 0.0
    k_max = int(threshold) - 1
    cumulative = 0.0
    for k in range(k_max + 1):
        cumulative += exp(-mean) * mean**k / factorial(k)
    return max(0.0, 1.0 - cumulative)


# ============================================================
# Countermeasure 2: randomised detection efficiency (this one only helps)
# ============================================================

@dataclass(frozen=True)
class RandomisedEfficiencyRow:
    """Detection of the blinding attack when Bob randomises his efficiencies."""

    randomisation: float
    forced_click_probability: float
    qber: float
    detected: bool

    def summary(self) -> str:
        return (
            f"efficiency randomisation {self.randomisation:.2f}: forced click "
            f"{self.forced_click_probability:.3f}, QBER {self.qber:.4f}, "
            f"detected {self.detected}"
        )


def randomized_efficiency_defence(
    randomisations: tuple[float, ...] = (0.0, 0.05, 0.1, 0.2, 0.5),
) -> list[RandomisedEfficiencyRow]:
    """Bob varies the two detectors' efficiencies by `+-randomisation`.

    Eve calibrates her bright pulse against a fixed detector response. If the
    response varies by a factor `1 +- d`, her chosen detector fires only with
    probability about `1 - d/2`, and otherwise the other detector fires -- an error.
    The model is schematic (a linear loss with the mismatch, no calibration loop),
    and it is reported as such: it shows that randomisation *raises* the error rate,
    not that it defeats the attack.
    """
    rows: list[RandomisedEfficiencyRow] = []
    for randomisation in randomisations:
        if not 0.0 <= randomisation <= 1.0:
            raise ValueError("randomisation must be in [0, 1]")
        forced = 1.0 - 0.5 * randomisation
        qber = 1.0 - forced
        rows.append(
            RandomisedEfficiencyRow(
                randomisation=randomisation,
                forced_click_probability=forced,
                qber=qber,
                detected=qber >= SECURITY_THRESHOLD,
            )
        )
    return rows


# ============================================================
# The comparison that matters
# ============================================================

@dataclass(frozen=True)
class AttackComparison:
    """Blinding against ordinary intercept-resend, on the same detector model."""

    blinding: BlindingReport
    intercept_resend_qber: float

    def summary(self) -> str:
        return (
            f"intercept-resend: QBER {self.intercept_resend_qber:.4f} "
            f"(caught: {self.intercept_resend_qber >= SECURITY_THRESHOLD}); "
            f"blinding at {self.blinding.power:.0e} photons: QBER "
            f"{self.blinding.qber:.4f} with Eve at "
            f"{self.blinding.eve_information:.2f} bits "
            f"(caught: {self.blinding.detected_by_qber}). "
            "The error-rate statistic sees one attack and not the other."
        )


def attack_comparison(
    power: float = 1.0e6,
    rounds: int = 2000,
    seed: int = 0,
) -> AttackComparison:
    """Both attacks at the same settings, so the asymmetry is measured."""
    return AttackComparison(
        blinding=blinding_attack(power=power, rounds=rounds, seed=seed),
        intercept_resend_qber=INTERCEPT_RESEND_QBER,
    )


# ============================================================
# The report
# ============================================================

@dataclass(frozen=True)
class DetectorReport:
    """Everything the blinding analysis establishes, in one object."""

    threshold: float
    attack: BlindingReport
    monitor: list[MonitorRow]
    randomised: list[RandomisedEfficiencyRow]

    @property
    def monitor_works(self) -> bool:
        """A monitor threshold that catches the attack with negligible false alarms."""
        return any(
            row.attack_alert_rate > 0.99 and row.honest_false_alarm_rate < 1e-9
            for row in self.monitor
        )

    @property
    def error_rate_blind_to_the_attack(self) -> bool:
        return self.attack.qber < SECURITY_THRESHOLD and self.attack.eve_information > 0.99

    def verdict(self) -> str:
        return (
            f"Detector blinding at {self.attack.power:.0e} mean photons per pulse: "
            f"the blinding threshold is {self.threshold:.0f}, the sifted-key QBER is "
            f"{self.attack.qber:.4f} while Eve holds {self.attack.eve_information:.2f} "
            f"bits, so the error-rate statistic does not see the attack "
            f"({self.error_rate_blind_to_the_attack}). An optical power monitor at a "
            f"suitable threshold does ({self.monitor_works}); randomised detector "
            "efficiency raises the error rate but is not a guarantee. Model, not a "
            "security proof; no RH evidence."
        )


def detector_report(
    power: float = 1.0e6,
    rounds: int = 2000,
    detector: DetectorModel | None = None,
    seed: int = 0,
) -> DetectorReport:
    """Run the whole analysis once."""
    detector = detector or DetectorModel()
    return DetectorReport(
        threshold=detector.blinding_threshold,
        attack=blinding_attack(power=power, rounds=rounds, detector=detector, seed=seed),
        monitor=power_monitor_roc(attack_power=power, seed=seed),
        randomised=randomized_efficiency_defence(),
    )
