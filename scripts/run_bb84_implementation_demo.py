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
    gain_and_error_rate,
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


def plot_attack_and_bound(mus=None):
    """The attack in one panel, and what Alice and Bob conclude in the other.

    Left: the error rate Alice and Bob measure against the fraction of the sifted
    key Eve holds. The error rate is flat at `e_det` across the whole sweep while
    Eve's information climbs past 0.99 -- the two curves do not touch.

    Right: the rate a decoy-free implementation reports, computed at the honest
    single-photon fraction, against the worst case the observed data permit. The
    gap between them is the whole finding.
    """
    if mus is None:
        mus = np.linspace(0.05, 3.0, 40)

    errors = []
    information = []
    honest_rates = []
    worst_rates = []
    for mu in mus:
        report = pns_attack(float(mu), ETA, E_DET, P_DARK)
        errors.append(report.E_mu)
        information.append(report.information_fraction)
        bound = decoy_free_bound(float(mu), ETA, E_DET, P_DARK)
        honest_rates.append(bound["rate_if_channel_honest"])
        worst_rates.append(bound["worst_case_rate"])

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    ax.plot(mus, information, "-", color="crimson",
            label="fraction of the sifted key Eve holds")
    ax.plot(mus, errors, "-", color="steelblue",
            label="error rate Alice and Bob measure")
    ax.axhline(E_DET, color="gray", linestyle=":", label=f"$e_{{det}}$ = {E_DET}")
    ax.set_xlabel(r"mean photon number $\mu$")
    ax.set_ylabel("fraction")
    ax.set_title("PNS: the information grows, the observable does not")
    ax.legend(loc="center right")
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(mus, honest_rates, "-", color="seagreen",
            label="rate at the honest single-photon fraction")
    ax.plot(mus, worst_rates, "-", color="darkred",
            label="worst case the observed data permit")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel(r"mean photon number $\mu$")
    ax.set_ylabel("secret key rate per sifted bit")
    ax.set_title("A decoy-free bound is positive only under an assumption")
    ax.legend(loc="lower left")
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

    print("\n[5] Generating the plot...")
    plot_attack_and_bound()

    print("\n" + "=" * 72)
    print(" This is the implementation layer, not the protocol. BB84 itself has")
    print(" been secure since Mayers (1996) and Shor-Preskill (2000); what fails")
    print(" here is a hardware assumption the protocol does not cover.")
    print(" Not modelled: detector blinding, timing and Trojan-horse channels,")
    print(" finite-key statistics, and the decoy-state mitigation.")
    print("=" * 72)


if __name__ == "__main__":
    main()
