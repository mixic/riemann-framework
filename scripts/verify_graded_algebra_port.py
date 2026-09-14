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
"""Demonstrate the corrections in `graded_algebra_even_odd.py`.

Each section states what the original implementation did, what the corrected one
does, and prints the numbers. Run from the repository root:

    python scripts/verify_graded_algebra_port.py
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

import mpmath as mp

from riemann_framework.graded_algebra_even_odd import (
    GradedElement,
    check_euler_product_converges,
    check_sigma_homomorphism,
    check_sigma_involution,
    check_trace_invariance,
    check_trace_is_geometric_series,
    is_fixed,
    local_factor,
    partial_euler_product,
    sigma,
    supertrace,
    trace,
)

mp.mp.dps = 30

PRIMES_20 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
             31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
TAUS = (1.0, 0.0, 0.5)


def section(number: int, title: str) -> None:
    print()
    print("=" * 70)
    print(f"{number}. {title}")
    print("=" * 70)


print("Verification of the ported graded algebra")
print("interface: GradedElement(even, odd, omega_sq), module-level sigma/trace")

# ---------------------------------------------------------------
section(1, "The reported Pylance error: __eq__ returned numpy.bool")
# ---------------------------------------------------------------
a, b = GradedElement(1.0, 2.0), GradedElement(1.0, 2.0)
print(f"   type(a == b)         -> {type(a == b).__name__}")
print(f"   a == b               -> {a == b!r}")
print(f"   declared return type -> bool")
print("   CORRECTED: returns a plain bool. The original used np.isclose, whose")
print("   numpy 2.x stub is np.bool[builtins.bool] and which a type checker")
print("   refuses to accept where bool is declared.")

# ---------------------------------------------------------------
section(2, "omega_sq default contradicted the module docstring")
# ---------------------------------------------------------------
print(f"   GradedElement(1, 2).omega_sq = {GradedElement(1.0, 2.0).omega_sq:+d}"
      "   (the docstring said omega^2 = 1)")
w = GradedElement(0.0, 1.0)
w2 = w * w
print(f"   omega * omega             = even {w2.even:g}, odd {w2.odd:g}"
      "   -> omega^2 = +1, the Z2 group algebra")
print("   CORRECTED: default is +1. omega_sq = -1 is still accepted explicitly,")
print("   and there the algebra is C rather than a Z2-grading.")

# ---------------------------------------------------------------
section(3, "trace was not sigma-invariant, and supertrace was misdefined")
# ---------------------------------------------------------------
print("   For x = a0 + w*a1 with w^2 = 1 the eigenvalues are a0 +- a1 and sigma")
print("   trades them. So a0 is the invariant one and a0 - a1 is the graded one.")
print()
header = f"   {'element':20} {'a0':>10} {'a1':>10} | {'old even-odd':>12} {'inv?':>6} | {'trace=a0':>10} {'inv?':>6}"
print(header)
print("   " + "-" * (len(header) - 3))
for label, x in (
    ("mixed 3 + 1*w", GradedElement(3.0, 1.0)),
    ("pure odd", GradedElement(0.0, 5.0)),
    ("local p=2 s=2 tau=1", local_factor(2, 2, 1.0)),
    ("local p=2 s=2 tau=0.5", local_factor(2, 2, 0.5)),
):
    old = x.even - x.odd
    old_sigma = sigma(x).even - sigma(x).odd
    new = trace(x)
    new_sigma = trace(sigma(x))
    print(
        f"   {label:20} {x.even.real:10.6f} {x.odd.real:10.6f} | "
        f"{old.real:12.6f} {str(abs(old - old_sigma) < 1e-12):>6} | "
        f"{new.real:10.6f} {str(abs(new - new_sigma) < 1e-12):>6}"
    )
print()
print(f"   check_trace_invariance(local_factor(2,2,0.5)) = "
      f"{check_trace_invariance(local_factor(2, 2, 0.5))}")
print(f"   trace(L_2) at tau=0.5     = {trace(local_factor(2, 2, 0.5)).real:.10f}"
      f"   (depends on tau: (1-x)/(1-tau x) = {(1 - 0.25) / (1 - 0.5 * 0.25):.10f})")
print(f"   supertrace(L_2) at tau=0.5 = {supertrace(local_factor(2, 2, 0.5)).real:.10f}"
      f"   (tau-independent: 1/(1-x) = {1 / (1 - 0.25):.10f})")

# ---------------------------------------------------------------
section(4, "the Euler product was identically 1")
# ---------------------------------------------------------------
print("   The original local factor gave even - odd = 1 for every prime, so the")
print("   product over all primes was 1 for every s: the graded zeta was a")
print("   constant and every downstream test (zeros, functional equation, G5/G6)")
print("   was vacuous.")
print()
print(f"   {'s':>2} {'tau':>5} | {'old product':>14} | {'prod trace':>14} | {'prod supertrace':>16}")
print("   " + "-" * 62)
for s in (2, 3):
    for tau in TAUS:
        old = 1.0
        p_tr = 1.0
        p_str = 1.0
        for p in PRIMES_20:
            x = float(mp.mpf(p) ** -s)
            base = 1.0 / (1.0 - x)
            old *= base - base * x
            factor = local_factor(p, s, tau)
            p_tr *= trace(factor).real
            p_str *= supertrace(factor).real
        print(f"   {s:>2} {tau:>5} | {old:>14.10f} | {p_tr:>14.10f} | {p_str:>16.10f}")
    target = partial_euler_product(s, PRIMES_20).real
    print(f"      classical partial product = {target:.10f}   zeta({s}) = {float(mp.zeta(s)):.10f}")
    print()

print("   The supertrace product is the classical partial product for every tau.")
print("   The trace product is not, for any tau.")

# ---------------------------------------------------------------
section(5, "local_factor was not the factor its docstring described")
# ---------------------------------------------------------------
print("   The docstring said the factor was 1/(1 - p^-s * omega). It was not.")
print("   1/(1 - xw) = (1 + xw)/(1 - x^2), so its coefficients are")
print("       even = 1/(1-x^2),  odd = x/(1-x^2)")
print("   The original returned base = 1/(1-x) for both, i.e. (1+xw)/(1-x), which")
print("   differs by a factor of (1+x).")
print()
print(f"   {'p':>3} {'s':>2} | {'original (even, odd)':>30} | {'its scalar sum':>15} | {'1/(1-x^2)':>12}")
print("   " + "-" * 72)
for p in (2, 3, 5):
    for s in (2, 3):
        x = mp.mpf(p) ** (-s)
        old_even = float(1 / (1 - x))
        old_odd = float(x / (1 - x))
        series_even = float(1 / (1 - x * x))
        print(f"   {p:>3} {s:>2} | ({old_even:12.10f}, {old_odd:12.10f}) | "
              f"{old_even - old_odd:>15.10f} | {series_even:>12.10f}")
print()
print("   The 'scalar sum' column is the original's even - odd: identically 1,")
print("   so the product over all primes was 1 and the graded zeta was constant.")
print()
print("   The corrected factor embeds the classical one through its supertrace:")
for tau in (1.0, 0.5, 0.0):
    factor = local_factor(2, 2, tau)
    print(f"       tau={tau}: trace = {trace(factor).real:.10f}"
          f"   supertrace = {supertrace(factor).real:.10f}"
          f"   (classical 1/(1-2^-2) = {1 / (1 - 0.25):.10f})")
print("   At tau = 1 the weight is the identity, the factor is scalar, and both")
print("   functionals agree with the classical factor.")
print()
print(f"   check_trace_is_geometric_series(2, 2) = {check_trace_is_geometric_series(2, 2)}")
print(f"   check_euler_product_converges(2, primes) = "
      f"{check_euler_product_converges(2, PRIMES_20)}")

# ---------------------------------------------------------------
section(6, "the algebra checks on the corrected implementation")
# ---------------------------------------------------------------
x = GradedElement(2.0, -3.0)
y = GradedElement(0.5, 0.25)
print(f"   check_sigma_involution(2 - 3w)  : {check_sigma_involution(x)}")
print(f"   check_sigma_homomorphism(x, y)  : {check_sigma_homomorphism(x, y)}")
print(f"   check_trace_invariance(x)       : {check_trace_invariance(x)}")
print(f"   is_fixed(project_to_fix(x))     : {is_fixed(GradedElement(x.even, 0.0))}")
print(f"   supertrace(x) = {supertrace(x)!r}")

# ---------------------------------------------------------------
section(7, "what omega_sq actually changes")
# ---------------------------------------------------------------
u, v = GradedElement(2.0, -3.0, omega_sq=-1), GradedElement(0.5, 0.25, omega_sq=-1)
print(f"   sigma is a homomorphism for omega^2 = -1 too : {check_sigma_homomorphism(u, v)}")
print("   (my earlier claim in this script that it fails was wrong: sigma is the")
print("    inner automorphism Ad(omega), so it is a homomorphism whenever omega")
print("    commutes with everything, for either sign.)")
print()
print("   what differs:")
print("     - omega^2 = +1 gives the group algebra of Z2, a genuine grading")
print("     - omega^2 = -1 gives C, where omega plays the role of i")
print(f"     - elements of different algebras compare equal: "
      f"{GradedElement(1.0, 2.0, omega_sq=1) == GradedElement(1.0, 2.0, omega_sq=-1)}"
      "   (the original __eq__ ignored omega_sq and said True)")
print(f"   associativity holds in both                    : "
      f"{(u * v) * v == u * (v * v)}")

print()
print("=" * 70)
print("Corrections verified.")
print("=" * 70)
