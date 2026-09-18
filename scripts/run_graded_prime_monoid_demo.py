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
Demonstrate the graded prime-exponent monoid: why zero-padding alone is
arithmetically inert, what multiplication rule fixes that, and how the
resulting structure is the one already underlying primon_gas.py.

Usage (from anywhere):
    python scripts/run_graded_prime_monoid_demo.py

Writes one plot into ``output/``. The mathematics is in
``docs/graded_prime_monoid.md``; nothing here proves anything about the Riemann
Hypothesis.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

import math

import matplotlib.pyplot as plt

from riemann_framework.graded_prime_monoid import (
    bridge_to_primon_gas,
    dimension_of,
    dimension_tower,
    euler_product_from_grading,
    from_int,
    truncated_euler_product,
    verify_monoid_isomorphism,
)
from riemann_framework.primon_gas import trace_exp

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def plot_euler_convergence(s: float = 2.0, prime_limits=(13, 97, 997, 9973, 99991)):
    """The truncated Euler product approaching `zeta(s)` as primes are added.

    This is the `q = 1` side of `euler_product_from_grading`: each new prime
    multiplies in one more local factor `1/(1 - p^{-s})`, so the product climbs
    toward `zeta(s)` from below. Cheap and uncapped -- no monoid enumeration.
    """
    values = [truncated_euler_product(s, limit) for limit in prime_limits]
    reference = math.pi ** 2 / 6 if s == 2.0 else None
    errors = [abs(v - reference) / reference for v in values] if reference else []

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    ax.plot(prime_limits, values, "o-", label="truncated Euler product")
    if reference:
        ax.axhline(reference, color="gray", linestyle="--",
                   label=f"$\\zeta({s:g})$ = {reference:.9f}")
    ax.set_xscale("log")
    ax.set_xlabel("prime limit $P$ (log scale)")
    ax.set_ylabel("value")
    ax.set_title("Local factors multiply toward $\\zeta(s)$")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    if reference:
        ax.plot(prime_limits, errors, "s-", color="darkred")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("prime limit $P$ (log scale)")
    ax.set_ylabel("relative error")
    ax.set_title(f"Gap to $\\zeta({s:g})$")
    ax.grid(True, alpha=0.3, which="both")

    plt.tight_layout()
    out = OUTPUT_DIR / "graded_prime_monoid_convergence.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f" Saved: {out}")


def main() -> None:
    print("=" * 70)
    print("Part 1: padding alone is arithmetically inert")
    print("=" * 70)
    print("The tower 1 -> (1,0) -> (1,0,0) -> ... for n=12, padded from its own")
    print("ambient length up to ambient dimension 6:")
    for elem in dimension_tower(12, max_dim=6):
        print(f"  {elem}")
    print("Every entry decodes back to 12 -- padding changes the ambient space,")
    print("never the number. This is why zero-padding by itself is a container,")
    print("not yet a number system (see the module docstring).")
    print()
    print("For n=35 = 5*7 the same tower starts at length 4, not at dimension 2:")
    for elem in dimension_tower(35, max_dim=6):
        print(f"  {elem}")
    print()

    print("=" * 70)
    print("Part 2: the one multiplication rule unique factorisation forces")
    print("=" * 70)
    a, b = from_int(6), from_int(10)
    product = a * b
    print(f"{a}")
    print(f"  * {b}")
    print(f"  = {product}   (ordinary integer product: 6*10 = {6*10})")
    print()
    print("Dimension is subadditive in general, exactly additive on coprime")
    print("factors -- this is the precise sense in which multiplying a")
    print("k-dimensional and an m-dimensional number gives a (k+m)-dimensional")
    print("one:")
    for x_int, y_int in [(6, 35), (6, 10), (2, 3), (4, 9)]:
        x, y = from_int(x_int), from_int(y_int)
        prod = x * y
        print(
            f"  dim({x_int})={x.dimension}, dim({y_int})={y.dimension}  ->  "
            f"dim({x_int}*{y_int}={prod.to_int()})={prod.dimension}"
        )
    print()

    print("=" * 70)
    print("Part 3: this is exactly (N_{>0}, x) -- checked, not assumed")
    print("=" * 70)
    report = verify_monoid_isomorphism(n_max=200)
    print(report.explanation)
    print()

    print("=" * 70)
    print("Part 4: bridge to primon_gas.py -- same sum, regrouped by dimension")
    print("=" * 70)
    n_max = 20_000
    bridge = bridge_to_primon_gas(n_max)
    print(bridge.explanation)
    direct = trace_exp(2.0, n_max)
    print(f"\nprimon_gas.trace_exp(2.0, {n_max}) = {direct.real:.12f}")
    print("The two agree because they are the same sum computed two ways: this")
    print("checks that the partition by dimension is complete, not that the sum")
    print("factorises. Part 5 does that.")
    print()

    print("=" * 70)
    print("Part 5: the Euler product is this monoid's zeta-like sum")
    print("=" * 70)
    print("Summing q^omega(v) over the exponent-vector monoid must equal the")
    print("product of one local factor per prime. The local factor is")
    print("  sum_a q^omega(p^a) p^-as = 1 + q * p^-s/(1 - p^-s),")
    print("which at q = 1 is exactly 1/(1 - p^-s) -- the Euler factor.")
    for q in (1.0, 0.5):
        r = euler_product_from_grading(2.0, prime_limit=13, degree_cap=6,
                                       grading_weight=q)
        print(f"  q={q}: monoid sum {r.monoid_sum:.12f}  local factors "
              f"{r.product_of_local_factors:.12f}  agrees={r.agrees}")
    print()
    print("And the truncated Euler product approaches zeta(2) as primes are added:")
    reference = math.pi ** 2 / 6
    for limit in (13, 97, 997, 9973, 99991):
        value = truncated_euler_product(2.0, limit)
        print(f"  primes <= {limit:<7} product = {value:.12f}  "
              f"rel err = {abs(value - reference) / reference:.3e}")
    print()
    print("=" * 70)
    print("Conclusion: 'a number system whose dimension increases under")
    print("multiplication' is not a new speculative object once the")
    print("multiplication rule is pinned down -- it is (N_{>0}, x) viewed")
    print("through its prime factorisation, and it is the structure that")
    print("already makes the primon gas's Euler product exact.")
    print("=" * 70)
    print()
    print("Generating the plot...")
    plot_euler_convergence()


if __name__ == "__main__":
    main()
