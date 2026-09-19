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
Demonstrate the BB84 implementation layer: the source is not a single photon.

Usage (from anywhere):
    python scripts/run_bb84_implementation_demo.py

Writes one plot into ``output/``. Nothing here is a security proof for or
against any deployed system; it is the standard photon-number-splitting
accounting, written down so the numbers can be checked. See
``docs/bb84_implementation.md`` for what is covered and what is not.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

import numpy as np
import matplotlib.pyplot as plt

from riemann_framework.bb84 import run_bb84
from riemann_framework.bb84_implementation import (
    decoy_free_bound,
    decoy_state_report,
    finite_key_report,
    gain_and_error_rate,
    minimum_rounds,
    pns_attack,
    single_photon_contribution,
    source_fractions,
)

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# A representative short-reach implemented link.
ETA = 0.1
E_DET = 0.01
P_DARK = 1e-6
#: The weak decoy intensity, an order of magnitude below the signal `mu`.
DECOY_INTENSITY = 0.1


def plot_attack_and_bound(mus=None):
    """Three panels: the attack, what decoys recover, and what finite keys cost.

    Left: the error rate Alice and Bob measure against the fraction of the sifted
    key Eve holds. The error rate is flat at `e_det` across the whole sweep while
    Eve's information climbs past 0.99 -- the two curves do not touch.

    Middle: the decoy-free rate at its honest assumption, the worst case the data
    permit, and the rate from the decoy bounds. The third is the only one that is
    both positive and supported.

    Right: the finite-key rate against the number of pulses, with the minimum
    marked. It climbs to the asymptotic value from below.
    """
    if mus is None:
        mus = np.linspace(0.05, 3.0, 40)

    errors = []
    information = []
    honest_rates = []
    worst_rates = []
    decoy_rates = []
    for mu in mus:
        report = pns_attack(float(mu), ETA, E_DET, P_DARK)
        errors.append(report.E_mu)
        information.append(report.information_fraction)
        bound = decoy_free_bound(float(mu), ETA, E_DET, P_DARK)
        honest_rates.append(bound["rate_if_channel_honest"])
        worst_rates.append(bound["worst_case_rate"])
        # The decoy must be *weaker* than the signal -- that is what makes the
        # multi-photon contribution small at `nu` -- so the curve starts where
        # `mu > nu` and is left undefined below, rather than extrapolated.
        if mu > DECOY_INTENSITY:
            decoy_rates.append(
                decoy_state_report(float(mu), DECOY_INTENSITY, ETA, E_DET, P_DARK).rate_decoy
            )
        else:
            decoy_rates.append(float("nan"))

    fig, axes = plt.subplots(1, 3, figsize=(19, 6))

    ax = axes[0]
    ax.plot(mus, information, "-", color="crimson",
            label="fraction of the sifted key Eve holds")
    ax.plot(mus, errors, "-", color="steelblue",
            label="error rate Alice and Bob measure")
    ax.axhline(E_DET, color="gray", linestyle=":", label=f"$e_{{det}}$ = {E_DET}")
    ax.set_xlabel(r"mean photon number $\mu$")
    ax.set_ylabel("fraction")
    ax.set_title("PNS: information grows, the observable does not")
    ax.legend(loc="center right")
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(mus, honest_rates, "-", color="seagreen",
            label="decoy-free, at the honest $Q_1/Q_\\mu$ (assumed)")
    ax.plot(mus, decoy_rates, "--", color="black",
            label=f"decoy bounds (measured, $\\nu$={DECOY_INTENSITY})")
    ax.plot(mus, worst_rates, "-", color="darkred",
            label="worst case the data permit")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel(r"mean photon number $\mu$")
    ax.set_ylabel("secret key rate per sifted bit")
    ax.set_title("Decoys buy a valid number, not a bigger one")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    n_pulses = np.logspace(5.5, 12, 40)
    finite = [finite_key_report(n_pulses=float(n), p_dark=P_DARK)["finite_rate"]
              for n in n_pulses]
    asymptotic = finite_key_report(n_pulses=1e12, p_dark=P_DARK)["all_rounds_asymptotic"]
    n_min = minimum_rounds(p_dark=P_DARK)
    ax.plot(n_pulses, finite, "-", color="purple", label="finite-key rate")
    ax.axhline(asymptotic, color="gray", linestyle="--",
               label=f"asymptotic ({asymptotic:.4f})")
    ax.axvline(n_min, color="darkred", linestyle=":",
               label=f"minimum {n_min:.2g} pulses")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("pulses sent $N$ (log scale)")
    ax.set_ylabel("secret key rate per sifted bit")
    ax.set_title("Finite keys cost rate, and there is a floor on $N$")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "bb84_pns_attack.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


def main() -> None:
    print("=" * 72)
    print("BB84 implementation layer: the source is not a single photon")
    print("=" * 72)

    print("\n[1] The source: a weak coherent pulse, not a photon")
    for mu in (0.1, 0.5, 1.0):
        f = source_fractions(mu)
        print(f"    mu={mu:<4g} vacuum={f['vacuum']:.4f}  single={f['single']:.4f}"
              f"  multi={f['multi']:.4f}")
    print("    The multi-photon fraction is what PNS feeds on, and at mu=0.5")
    print("    it is 9% -- small, and far from zero.")

    print("\n[2] What the protocol layer sees, and what it cannot see")
    ideal = run_bb84(n_bits=2000, seed=42)
    stats = gain_and_error_rate(0.5, ETA, E_DET, P_DARK)
    single = single_photon_contribution(0.5, ETA, E_DET, P_DARK)
    print(f"    bb84.py (idealised)      : one photon per round, BER = {ideal.ber:.4f}")
    print(f"    implementation layer     : Q_mu = {stats['Q_mu']:.6f}, "
          f"E_mu = {stats['E_mu']:.6f}")
    print(f"    single-photon part only  : Q_1 = {single['Q_1']:.6f}, "
          f"e_1 = {single['e_1']:.6f}")
    print("    bb84.py has no photon number, so it has no Q_1 to be wrong about.")

    print("\n[3] Photon-number splitting: full information, no errors")
    print(f"    {'mu':>6} {'Q_mu':>10} {'E_mu':>9} {'Eve holds':>10}")
    for mu in (0.1, 0.3, 0.5, 1.0, 2.0, 5.0):
        r = pns_attack(mu, ETA, E_DET, P_DARK)
        print(f"    {mu:>6g} {r.Q_mu:>10.6f} {r.E_mu:>9.6f} "
              f"{r.information_fraction:>10.4f}")
    print("    E_mu is flat at e_det throughout. Eve forwards Alice's own state,")
    print("    so she adds nothing to the error rate while learning the bit from")
    print("    the basis announced during sifting.")

    print("\n[4] What Alice and Bob can conclude without decoy states")
    print(f"    {'mu':>6} {'Q1/Qmu':>8} {'honest rate':>12} {'worst case':>12}")
    for mu in (0.1, 0.3, 0.5, 1.0):
        b = decoy_free_bound(mu, ETA, E_DET, P_DARK)
        print(f"    {mu:>6g} {b['Q_1_over_Q_mu']:>8.4f} "
              f"{b['rate_if_channel_honest']:>+12.6f} {b['worst_case_rate']:>+12.6f}")
    print("    Eve's blocking of single-photon pulses moves Q_1 without moving")
    print("    Q_mu or E_mu, so the data permit Q_1/Q_mu = 0. The positive number")
    print("    is an assumption; the worst case is what the data support.")

    print("\n[5] Decoy states: making the single-photon fraction measurable")
    print("    Bounds from Ma-Qi-Zhao-Lo (2005), vacuum + weak decoy. The true")
    print("    Y_1 is shown only because this is a simulation: knowing it is what")
    print("    makes the bound testable.")
    print(f"    {'mu':>5} {'nu':>5} {'Y1^L':>10} {'Y1 true':>10} {'tight':>7} "
          f"{'decoy rate':>12} {'decoy-free':>12} {'worst':>10} {'valid':>6}")
    for mu, nu in ((0.5, 0.05), (0.5, 0.1), (0.5, 0.2), (1.0, 0.1), (1.0, 0.2)):
        r = decoy_state_report(mu, nu, ETA, E_DET, P_DARK)
        print(f"    {mu:>5g} {nu:>5g} {r.Y_1_lower:>10.6f} {r.Y_1_true:>10.6f} "
              f"{r.Y_1_is_tight:>7.4f} {r.rate_decoy:>+12.6f} "
              f"{r.rate_decoy_free_honest:>+12.6f} {r.rate_decoy_free_worst:>+10.6f} "
              f"{str(r.bounds_are_valid):>6}")
    print("    The decoy rate is the only column that is both positive and")
    print("    supported by data. It sits about 2% below the assumed figure, and")
    print("    it tightens as the decoy weakens: the correction is O(nu^2).")

    print("\n[6] Finite keys: the error rate is estimated, not known")
    print("    Hoeffding gives the slack a finite test sample permits,")
    print("    delta = sqrt(ln(1/eps)/(2k)), so a rate calculation must assume")
    print("    E_mu + delta. This is a correction to the accounting, not an attack.")
    print(f"    {'N pulses':>12} {'test k':>12} {'delta':>9} {'E_mu^U':>9} "
          f"{'finite':>11} {'asymptotic':>11}")
    for n_pulses in (1e6, 1e7, 1e8, 1e9, 1e10, 1e12):
        r = finite_key_report(n_pulses=n_pulses, p_dark=P_DARK)
        print(f"    {n_pulses:>12.0e} {r['test_sample']:>12d} {r['delta']:>9.6f} "
              f"{r['E_mu_upper']:>9.6f} {r['finite_rate']:>+11.6f} "
              f"{r['all_rounds_asymptotic']:>+11.6f}")
    n_min = minimum_rounds(p_dark=P_DARK)
    print(f"    minimum pulses for a positive finite-key rate: {n_min:.4g}")
    print("    Below that there is no security claim to make at these parameters,")
    print("    however good the channel. The slack falls as 1/sqrt(k), so")
    print("    finite-key effects are a small-sample problem, not a small-rate one.")

    print("\n[7] Generating the plot...")
    plot_attack_and_bound()

    print("\n" + "=" * 72)
    print(" This is the implementation layer, not the protocol. BB84 itself has")
    print(" been secure since Mayers (1996) and Shor-Preskill (2000); what fails")
    print(" here is a hardware assumption the protocol does not cover.")
    print(" Not modelled: detector blinding, and timing and Trojan-horse")
    print(" channels. Modelled: the source, the detectors, PNS, and the decoy")
    print(" and finite-key corrections.")
    print("=" * 72)


if __name__ == "__main__":
    main()
