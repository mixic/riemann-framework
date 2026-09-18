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
Demonstrate the graded prime monoid and print the evidence for its claims.

Usage (from anywhere):
    python scripts/run_graded_prime_monoid_demo.py

Writes one plot into ``output/``. The mathematics is documented in
``docs/graded_prime_monoid.md``; nothing here proves anything about the Riemann
Hypothesis, and the module docstring says why.
"""

import os
from pathlib import Path
import sys

import runpy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

# The plot is written relative to the repository root, so re-exec from there
# when invoked from elsewhere. The environment variable stops the re-run from
# recursing.
if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_GRADED_PRIME_MONOID_BOOTSTRAPPED"
):
    os.environ["_GRADED_PRIME_MONOID_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit()

import matplotlib.pyplot as plt

from riemann_framework.graded_prime_monoid import (
    add,
    candidate_rule_report,
    dense_vector,
    energy,
    euler_factorization_report,
    exponent_vector,
    from_exponent_vector,
    graded_components,
    monoid_contract_report,
    prime_basis,
    smooth_truncation_report,
    total_degree,
)
from riemann_framework.primon_gas import trace_convergence

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# Plot: the box approaches zeta from below
# ============================================================

def plot_truncation_convergence(s: float = 2.0, degree_cap: int = 40):
    """Plot the box sum against the growing prime basis, and its relative error.

    The box over the primes `<= P` is the sum of `n^{-s}` over the `P`-smooth
    numbers with exponents at most `degree_cap`. Every increase in `P` adds
    terms, so the value climbs toward `zeta(s)` from below and the error falls.
    Both panels are the same data: the left shows the approach, the right shows
    the gap on a log-log axis so the rate is visible.
    """
    prime_caps = [13, 31, 97, 199, 499, 997, 1999]
    reports = [
        smooth_truncation_report(s, prime_cap=cap, degree_cap=degree_cap)
        for cap in prime_caps
    ]
    boxes = [r["box_sum"].real for r in reports]
    errors = [r["relative_difference"] for r in reports]
    reference = reports[0]["zeta_reference"].real

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    ax.plot(prime_caps, boxes, "o-", label="box sum over primes $\\leq P$")
    ax.axhline(reference, color="gray", linestyle="--",
               label=f"$\\zeta({s:g})$ = {reference:.9f}")
    ax.set_xscale("log")
    ax.set_xlabel("prime cap $P$ (log scale)")
    ax.set_ylabel("value")
    ax.set_title("The monoid truncation climbs to $\\zeta(s)$ from below")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(prime_caps, errors, "s-", color="darkred")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("prime cap $P$ (log scale)")
    ax.set_ylabel("relative error")
    ax.set_title(f"Gap to $\\zeta({s:g})$, degree cap {degree_cap}")
    ax.grid(True, alpha=0.3, which="both")

    plt.tight_layout()
    out = OUTPUT_DIR / "graded_prime_monoid_convergence.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 72)
    print("Graded prime monoid: (N_{>0}, x)  <->  (V, +)")
    print("=" * 72)

    print("\n[1] The identification")
    display_basis = prime_basis(20)
    for n in (1, 12, 97, 720720):
        v = exponent_vector(n)
        print(f"    phi({n}) = {v}")
        print(f"        dense over primes <= 20: {dense_vector(v, display_basis)}"
              f"   Omega = {total_degree(v)}   phi^-1 -> {from_exponent_vector(v)}")
    print(f"    phi(6) + phi(10) = {add(exponent_vector(6), exponent_vector(10))}"
          f"   phi(60) = {exponent_vector(60)}")

    print("\n[2] The grading: Omega(n) = the number of prime factors with multiplicity")
    components = graded_components(64)
    for degree in sorted(components):
        members = components[degree]
        shown = members[:10]
        suffix = " ..." if len(members) > len(shown) else ""
        print(f"    Omega = {degree}: {len(members):>3} integers up to 64, e.g. {shown}{suffix}")
    print("    Omega(m n) = Omega(m) + Omega(n) for every pair up to 300")

    print("\n[3] The uniqueness theorem: hypotheses, checked over 1..300")
    contract = monoid_contract_report(300)
    for key in ("round_trip_forward", "round_trip_backward", "multiplicative",
                "degree_additive", "identity_is_empty_vector"):
        print(f"    {key:<26} {contract[key]}")
    print(f"    pairs checked: {contract['pairs_checked']}")
    print(f"    first failure: {contract['first_failure']}")
    print("    (The theorem itself is proved by surjectivity of phi; see the")
    print("     module docstring. No enumeration could establish it.)")

    print("\n[4] Rival multiplication rules, and where each first breaks")
    for report in candidate_rule_report(200):
        mark = "ok  " if report.holds else "FAIL"
        print(f"    [{mark}] {report.summary}")

    print("\n[5] Why the Euler product is exact: the box identity")
    report = euler_factorization_report(s=2.0, basis=prime_basis(13), degree_cap=3)
    print(f"    basis {report['basis']}, degree cap {report['degree_cap']}, "
          f"{report['terms_enumerated']} monoid elements")
    print(f"    enumerated box sum : {report['box_sum']:.15f}")
    print(f"    product formula    : {report['product_formula']:.15f}")
    print(f"    relative difference: {report['relative_difference']:.3e}")
    print("    sum over the free commutative monoid = product over primes.")

    print("\n[6] The same box against zeta(2), as the monoid truncation grows")
    for prime_cap, degree_cap in ((13, 4), (97, 12), (997, 40), (1999, 40)):
        r = smooth_truncation_report(2.0, prime_cap=prime_cap, degree_cap=degree_cap)
        print(f"    primes <= {prime_cap:<5} ({r['basis_size']:>3} generators), "
              f"degree cap {degree_cap:<3}  box = {r['box_sum'].real:.12f}  "
              f"rel err = {r['relative_difference']:.3e}")

    print("\n[7] The primon gas tie: the energy is linear in the exponent vector")
    for n in (12, 97, 720720):
        v = exponent_vector(n)
        print(f"    <lambda, phi({n})> = {energy(v):.12f}   log({n}) = "
              f"{__import__('math').log(n):.12f}")
    convergence = trace_convergence(2.0)
    print(f"    Tr_N[e^-sH] -> zeta(s): partials "
          f"{[f'{p:.9f}' for p in convergence['partial_sums']]}")
    print(f"    zeta(2) = {convergence['zeta_reference']:.9f}, "
          f"errors decreasing: {convergence['errors_decrease']}")

    print("\n[8] Generating the plot...")
    plot_truncation_convergence()

    print("\n Demonstration complete.")
    print(" Reminder: the eigenvalues are log(n), not the zeta ordinates.")
    print(" Nothing here proves anything about the Riemann Hypothesis.")


if __name__ == "__main__":
    main()
