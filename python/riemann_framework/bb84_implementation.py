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
The implementation layer of BB84: photon source, detectors, and the attacks that
exist only because real hardware is not an ideal qubit channel.

`bb84.py` models the *protocol*: one photon per round, a perfect source, a
perfect detector. That protocol has been secure since Mayers (1996) and
Shor-Preskill (2000), and no abstract attack will break it. The breaks that
happened in practice happened one layer down, in the hardware:

- **Photon-number splitting (PNS).** A weak laser pulse has a Poisson photon
  number, and pulses with two or more photons let an eavesdropper keep one and
  forward the rest. She then learns the bit when the basis is announced during
  sifting, at no cost in errors. Modelled here.
- Detector blinding (Lydersen et al. 2010), which broke commercial systems by
  driving the detectors into classical mode.
- Timing side channels and Trojan-horse attacks on the source.
- Finite-key statistics: the asymptotic analysis assumes infinitely many rounds.

**What this module covers: the source, the detectors, and PNS.** The other three
are named in `docs/bb84_implementation.md` with what each would need, and are not
implemented. Nothing here is a security proof for or against any deployed system;
it is the standard PNS accounting, written down so the numbers can be checked.

Why PNS is the right first increment
------------------------------------
It is the cleanest case of the general shape. The idealized protocol and the
implemented one are *observationally identical* to Alice and Bob -- the gain and
the error rate are unchanged -- while the eavesdropper's information is not. That
is a statement about the implementation, not about the protocol, and it is exactly
what `bb84.py` cannot see.

The accounting, standard since Brassard-Lütkenhaus-Mor-Mor (2000) and
Lütkenhaus-Jahma (2002):

    p_n     = e^-mu mu^n / n!                    (Poisson source)
    Y_n     = 1 - (1 - Y_0)(1 - eta)^n           (yield of an n-photon pulse)
    Q_mu    = 1 - (1 - Y_0) e^{-eta mu}          (gain)
    Q_mu E_mu = e_0 Y_0 + e_det (Q_mu - Y_0)     (error rate)

with `Y_0 = 1 - (1 - p_dark)^2` the dark-count yield of a two-detector receiver,
`eta` the end-to-end transmittance, `e_0 = 1/2` for dark counts and `e_det` the
misalignment error. The multi-photon gain is `Q_multi = Q_mu - p_0 Y_0 - p_1 Y_1`,
and the fraction of the sifted key the multi-photon pulses contribute is
`f = Q_multi / Q_mu`. Eve knows every one of those bits and causes none of the
errors, so her information per sifted bit is `f` while `E_mu = e_det` is
unchanged.

The consequence is the point: Alice and Bob's *data* are consistent with the
honest channel, so any bound they compute without decoy states is unsound, and
`decoy_free_bound` reports what the worst case consistent with their data is.
The mitigation -- decoy states -- is named and not implemented; see the doc.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

#: A two-detector receiver counts a vacuum event as a dark count with this
#: probability in the standard treatment, since a dark count carries no bit.
DARK_COUNT_ERROR_RATE = 0.5


# ============================================================
# The source: weak coherent pulses, not single photons
# ============================================================

def poisson_photon_distribution(mu: float, n_max: int = 40) -> np.ndarray:
    """`p_n = e^-mu mu^n / n!` for `n = 0..n_max`.

    A weak coherent pulse is not a single photon. This is the distribution that
    makes PNS possible, and it is the first thing `bb84.py` does not model.
    """
    if not 0.0 < mu:
        raise ValueError(f"mu must be > 0, got {mu}")
    if n_max < 1:
        raise ValueError(f"n_max must be >= 1, got {n_max}")
    n = np.arange(n_max + 1, dtype=float)
    log_factorial = np.array([math.lgamma(k + 1) for k in n])
    return np.exp(-mu + n * math.log(mu) - log_factorial)


def source_fractions(mu: float, n_max: int = 40) -> dict:
    """The vacuum, single-photon and multi-photon fractions of the source.

    Exact, and the numbers a real experiment measures a source by. At `mu = 0.5`
    roughly 61% of pulses are vacuum, 30% single-photon and 9% multi-photon; the
    multi-photon fraction is the part PNS feeds on.
    """
    p = poisson_photon_distribution(mu, n_max)
    return {
        "mu": mu,
        "vacuum": float(p[0]),
        "single": float(p[1]),
        "multi": float(1.0 - p[0] - p[1]),
        "total": float(p.sum()),
        "truncation_mass": float(1.0 - p.sum()),
    }


# ============================================================
# Channel and detectors
# ============================================================

def dark_count_yield(p_dark: float) -> float:
    """`Y_0 = 1 - (1 - p_dark)^2`: at least one of two detectors fires on vacuum.

    Using the exact form rather than `2 p_dark` keeps the `mu -> 0` limit of
    `gain_and_error_rate` equal to `Y_0` instead of approximately so, which
    matters because that limit is used as a check.
    """
    if not 0.0 <= p_dark <= 1.0:
        raise ValueError(f"p_dark must be in [0, 1], got {p_dark}")
    return 1.0 - (1.0 - p_dark) ** 2


def n_photon_yield(n: int, eta: float, p_dark: float = 0.0) -> float:
    """`Y_n`: probability Bob registers a click given `n` photons arrived.

    A click is missed only if no photon is detected *and* no dark count occurs,
    which is why the two factors multiply: `1 - Y_n = (1 - Y_0)(1 - eta)^n`.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    if not 0.0 <= eta <= 1.0:
        raise ValueError(f"eta must be in [0, 1], got {eta}")
    return 1.0 - (1.0 - dark_count_yield(p_dark)) * (1.0 - eta) ** n


def gain_and_error_rate(
    mu: float, eta: float, e_det: float = 0.0, p_dark: float = 0.0,
    n_max: int = 40,
) -> dict:
    """The observed gain `Q_mu` and error rate `E_mu` of the implemented channel.

    Closed form, and the quantities Alice and Bob actually measure. Nothing here
    can distinguish an honest channel from one under PNS, and that indistinguish-
    ability is the whole problem.

    Limits worth checking, and checked in the tests: `mu -> 0` gives
    `Q_mu -> Y_0` and `E_mu -> 1/2` (dark counts dominate and are random), while
    large `mu` gives `Q_mu -> 1` and `E_mu -> e_det`.
    """
    if not mu > 0.0:
        raise ValueError(f"mu must be > 0, got {mu}")
    if not 0.0 <= e_det <= 0.5:
        raise ValueError(f"e_det must be in [0, 1/2], got {e_det}")
    if not 0.0 <= eta <= 1.0:
        raise ValueError(f"eta must be in [0, 1], got {eta}")

    y_0 = dark_count_yield(p_dark)
    q_mu = 1.0 - (1.0 - y_0) * math.exp(-eta * mu)
    # Errors: dark counts are random (rate e_0), the photonic part is misaligned.
    e_mu = (DARK_COUNT_ERROR_RATE * y_0 + e_det * (q_mu - y_0)) / q_mu
    return {
        "mu": mu,
        "eta": eta,
        "e_det": e_det,
        "p_dark": p_dark,
        "Y_0": y_0,
        "Q_mu": q_mu,
        "E_mu": e_mu,
    }


def single_photon_contribution(
    mu: float, eta: float, e_det: float = 0.0, p_dark: float = 0.0
) -> dict:
    """`Q_1` and `e_1`: what the single-photon pulses alone contribute.

    These are the quantities a decoy-state analysis bounds from the data. Without
    decoys they are *not* measurable, which is what makes the attack below work.
    """
    if not mu > 0.0:
        raise ValueError(f"mu must be > 0, got {mu}")
    y_0 = dark_count_yield(p_dark)
    y_1 = n_photon_yield(1, eta, p_dark)
    q_1 = mu * math.exp(-mu) * y_1
    e_1 = (DARK_COUNT_ERROR_RATE * y_0 + e_det * (y_1 - y_0)) / y_1
    return {"Y_1": y_1, "Q_1": q_1, "e_1": e_1}


# ============================================================
# The attack
# ============================================================

@dataclass
class PNSReport:
    """Outcome of the photon-number-splitting attack."""

    mu: float
    eta: float
    e_det: float
    p_dark: float
    Q_mu: float
    E_mu: float
    Q_multi: float
    information_fraction: float
    additional_qber: float
    explanation: str

    @property
    def eve_knows_everything(self) -> bool:
        """True when the single-photon contribution has effectively vanished.

        In the limit `mu -> inf` the source emits only multi-photon pulses, so
        every sifted bit is one Eve holds a copy of. The tolerance is for the
        finite `mu` at which this is tested; `p_1 = mu e^-mu` falls off fast.
        """
        return self.information_fraction >= 1.0 - 1e-9


def pns_attack(
    mu: float, eta: float = 0.1, e_det: float = 0.01, p_dark: float = 0.0,
    n_max: int = 40,
) -> PNSReport:
    """Photon-number splitting: keep one photon from every multi-photon pulse.

    Eve measures the photon number without disturbing it (a quantum non-demolition
    measurement; in practice she exploits loss and beam splitting). On a pulse with
    `n >= 2` she keeps one photon and forwards the rest, so she learns the bit with
    certainty once the basis is announced in sifting. On `n = 1` she forwards the
    pulse and learns nothing.

    Her information on the sifted key is therefore the fraction of detections that
    came from multi-photon pulses, and the error rate she introduces is *zero*: the
    forwarded photons are in the state Alice prepared. The reported `E_mu` is the
    honest channel's, unchanged.
    """
    stats = gain_and_error_rate(mu, eta, e_det, p_dark, n_max)
    single = single_photon_contribution(mu, eta, e_det, p_dark)

    p_0 = math.exp(-mu)
    y_0 = stats["Y_0"]
    q_multi = stats["Q_mu"] - p_0 * y_0 - single["Q_1"]
    fraction = max(0.0, q_multi) / stats["Q_mu"]

    return PNSReport(
        mu=mu,
        eta=eta,
        e_det=e_det,
        p_dark=p_dark,
        Q_mu=stats["Q_mu"],
        E_mu=stats["E_mu"],
        Q_multi=q_multi,
        information_fraction=fraction,
        additional_qber=0.0,
        explanation=(
            f"mu={mu:g}: Q_mu={stats['Q_mu']:.6f}, E_mu={stats['E_mu']:.6f}. "
            f"The multi-photon pulses contribute Q_multi={q_multi:.6f} of the "
            f"gain, so Eve learns {fraction:.4f} of the sifted key in full and "
            "introduces no errors at all. Alice and Bob's measured Q_mu and E_mu "
            "are exactly the honest channel's."
        ),
    )


def pns_information_fraction(
    mu: float, eta: float = 0.1, e_det: float = 0.01, p_dark: float = 0.0
) -> float:
    """Eve's information per sifted bit under PNS, for sweeps."""
    return pns_attack(mu, eta, e_det, p_dark).information_fraction


# ============================================================
# What Alice and Bob can conclude
# ============================================================

def binary_entropy(x: float) -> float:
    """`H_2(x) = -x log2 x - (1-x) log2(1-x)`, and 0 at the endpoints."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def decoy_free_bound(
    mu: float, eta: float = 0.1, e_det: float = 0.01, p_dark: float = 0.0,
    f_ec: float = 1.16,
) -> dict:
    """The rate Alice and Bob would compute without decoy states, and why it fails.

    Two numbers, and the gap between them is the finding.

    - `rate_if_channel_honest`: the GLLP rate with the single-photon fraction
      taken at its honest value `Q_1 / Q_mu`. This is what a decoy-free
      implementation reports, and it is positive.
    - `worst_case_rate`: the same expression with `Q_1 / Q_mu` allowed to be zero,
      which is what the *data* permit, because Eve's blocking of single-photon
      pulses changes `Q_1` without changing `Q_mu` or `E_mu`.

    A bound that is not valid for all channels consistent with the observed data is
    not a bound. Without decoy states the observed data do not pin down `Q_1`, so
    the honest number is an assumption and the worst case is what remains.

    `f_ec` is the error-correction inefficiency (1.16 is a common figure).
    """
    stats = gain_and_error_rate(mu, eta, e_det, p_dark)
    single = single_photon_contribution(mu, eta, e_det, p_dark)

    def h2(x: float) -> float:
        return binary_entropy(x)

    q_mu, e_mu = stats["Q_mu"], stats["E_mu"]
    delta_1 = single["Q_1"] / q_mu
    honest = 0.5 * q_mu * (
        -f_ec * h2(e_mu) + delta_1 * (1.0 - h2(single["e_1"]))
    )
    worst = 0.5 * q_mu * (-f_ec * h2(e_mu))

    return {
        "mu": mu,
        "Q_mu": q_mu,
        "E_mu": e_mu,
        "Q_1_over_Q_mu": delta_1,
        "e_1": single["e_1"],
        "rate_if_channel_honest": honest,
        "worst_case_rate": worst,
        "assumption_is_load_bearing": honest > 0.0 >= worst,
        "pns_information_fraction": pns_attack(mu, eta, e_det, p_dark).information_fraction,
    }


# ============================================================
# Decoy states: making the single-photon fraction measurable
# ============================================================
#
# The gap above is that `Q_1` is not determined by the data at one intensity.
# Decoy states close it by measuring the gain at a second, weaker intensity where
# the multi-photon contribution is much smaller.
#
# The two bounds below are the vacuum + weak decoy case of Ma, Qi, Zhao and Lo
# (2005), "Practical decoy state for quantum key distribution". They were read off
# the source rather than recalled -- writing a plausible-looking decoy bound from
# memory and checking it only against its own limits is the failure mode this
# repository avoids. Two independent checks were applied:
#
#   1. the general two-decoy formulas in the same paper reduce to exactly these
#      two expressions at `nu_1 = 0`, and the same pair appears with `nu_1`
#      written out in later work;
#   2. `decoy_state_report` checks both bounds against this module's own channel
#      model, where the true `Y_1` and `e_1` are known. A mis-transcribed exponent
#      would show up there immediately, and `bounds_are_valid` reports it.

def lower_bound_Y1(mu: float, nu: float, Q_mu: float, Q_nu: float, Y_0: float) -> float:
    """`Y_1^L` from a vacuum decoy and a weak decoy of intensity `nu`.

    ```text
    Y_1 >= mu/(mu nu - nu^2) *
             [ Q_nu e^nu - (nu^2/mu^2) Q_mu e^mu - ((mu^2 - nu^2)/mu^2) Y_0 ]
    ```

    The bracket is what the two extra measurements buy: `Q_nu e^nu` bounds the
    low-photon terms from above, `Q_mu e^mu` supplies the normalisation, and
    `Y_0` is measured directly by the vacuum decoy. Subtracting the last two from
    the first leaves a bound on the one- and two-photon contributions, and the
    `nu^2/mu^2` weighting is what isolates `Y_1`.
    """
    if not 0.0 < nu < mu:
        raise ValueError(f"need 0 < nu < mu, got nu={nu}, mu={mu}")
    prefactor = mu / (mu * nu - nu * nu)
    bracket = (
        Q_nu * math.exp(nu)
        - (nu * nu / (mu * mu)) * Q_mu * math.exp(mu)
        - ((mu * mu - nu * nu) / (mu * mu)) * Y_0
    )
    return prefactor * bracket


def upper_bound_e1(
    nu: float, Q_nu: float, E_nu: float, Y_0: float, Y_1_lower: float
) -> float:
    """`e_1^U`, the matching upper bound on the single-photon error rate.

    ```text
    e_1 <= (E_nu Q_nu e^nu - e_0 Y_0) / (nu Y_1^L)
    ```

    Capped at `1/2`, which is where a usable error rate ends: beyond that the
    sifted bits are anti-correlated rather than correlated, and `H_2` is
    decreasing, so the cap is both physically right and conservative.
    """
    if Y_1_lower <= 0.0:
        raise ValueError(
            f"Y_1^L = {Y_1_lower} is not positive, so e_1 has no finite upper "
            "bound from this data: the signal and decoy intensities are too close "
            "together for the bound to separate single-photon events"
        )
    raw = (E_nu * Q_nu * math.exp(nu) - DARK_COUNT_ERROR_RATE * Y_0) / (nu * Y_1_lower)
    return min(raw, 0.5)


@dataclass
class DecoyReport:
    """A vacuum + weak decoy analysis, with the true values alongside for checking."""

    mu: float
    nu: float
    Q_mu: float
    E_mu: float
    Q_nu: float
    E_nu: float
    Y_0: float
    Y_1_lower: float
    Y_1_true: float
    e_1_upper: float
    e_1_true: float
    Q_1_lower: float
    Q_1_true: float
    rate_decoy: float
    rate_decoy_free_honest: float
    rate_decoy_free_worst: float
    bounds_are_valid: bool
    explanation: str

    @property
    def Y_1_is_tight(self) -> float:
        """How close the lower bound is to the truth, as a fraction of it."""
        return self.Y_1_lower / self.Y_1_true if self.Y_1_true else 0.0

    @property
    def bound_is_vacuous(self) -> bool:
        """True when `Y_1^L <= 0`, so no key is extractable from this data.

        The interesting case, not a degenerate one: it is the signature of
        suppressed single-photon events. A protocol should read this as an alarm.
        """
        return self.Y_1_lower <= 0.0


def decoy_state_report(
    mu: float = 0.5,
    nu: float = 0.1,
    eta: float = 0.1,
    e_det: float = 0.01,
    p_dark: float = 0.0,
    f_ec: float = 1.16,
) -> DecoyReport:
    """Decoy analysis with the bounds checked against the model that generated the data.

    The true `Y_1` and `e_1` are included because this is a simulation: a real
    implementation does not have them, and obtaining them *is* the problem decoys
    solve. Having them here is what makes the bounds testable -- `bounds_are_valid`
    is `Y_1^L <= Y_1` and `e_1^U >= e_1`, and a mis-transcribed formula fails it.

    The rate uses the bounds, not the true values, so it is a rate Alice and Bob
    could actually compute. It is *lower* than `rate_decoy_free_honest`, which is
    the point: the decoy-free number was larger because it was unsupported. What
    decoys buy is not a bigger number but a valid one.
    """
    signal = gain_and_error_rate(mu, eta, e_det, p_dark)
    decoy = gain_and_error_rate(nu, eta, e_det, p_dark)
    single = single_photon_contribution(mu, eta, e_det, p_dark)
    y_0 = signal["Y_0"]

    y_1_lower = lower_bound_Y1(mu, nu, signal["Q_mu"], decoy["Q_mu"], y_0)

    if y_1_lower > 0.0:
        e_1_upper = upper_bound_e1(nu, decoy["Q_mu"], decoy["E_mu"], y_0, y_1_lower)
        q_1_lower = mu * math.exp(-mu) * y_1_lower
    else:
        # A non-positive `Y_1^L` is not an error condition. It is what the data look
        # like when single-photon events have been *suppressed* -- which is the
        # thing decoy states exist to detect, so crashing here would be the worst
        # possible failure: a detection tool that dies on the signal it is meant to
        # catch. Reachable, and reproduced in the tests, by depressing `Q_nu`
        # toward `Y_0` while leaving `Q_mu` alone, which is exactly Eve's blocking.
        # The bound is vacuous, so no key is extractable, and the negative rate
        # below reports that.
        e_1_upper = 0.5
        q_1_lower = 0.0

    rate = 0.5 * (
        -signal["Q_mu"] * f_ec * binary_entropy(signal["E_mu"])
        + q_1_lower * (1.0 - binary_entropy(e_1_upper))
    )
    free = decoy_free_bound(mu, eta, e_det, p_dark, f_ec)
    valid = (y_1_lower <= single["Y_1"] + 1e-12) and (e_1_upper >= single["e_1"] - 1e-12)

    return DecoyReport(
        mu=mu,
        nu=nu,
        Q_mu=signal["Q_mu"],
        E_mu=signal["E_mu"],
        Q_nu=decoy["Q_mu"],
        E_nu=decoy["E_mu"],
        Y_0=y_0,
        Y_1_lower=y_1_lower,
        Y_1_true=single["Y_1"],
        e_1_upper=e_1_upper,
        e_1_true=single["e_1"],
        Q_1_lower=q_1_lower,
        Q_1_true=single["Q_1"],
        rate_decoy=rate,
        rate_decoy_free_honest=free["rate_if_channel_honest"],
        rate_decoy_free_worst=free["worst_case_rate"],
        bounds_are_valid=valid,
        explanation=(
            f"mu={mu:g}, nu={nu:g}: Y_1^L={y_1_lower:.6f} (true {single['Y_1']:.6f}), "
            f"e_1^U={e_1_upper:.6f} (true {single['e_1']:.6f}). "
            f"Rate from the bounds {rate:+.6f}, against the decoy-free number "
            f"{free['rate_if_channel_honest']:+.6f} (unsupported) and the worst "
            f"case {free['worst_case_rate']:+.6f}."
        ),
    )
