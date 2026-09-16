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
Check the σ-symmetry of the Riemann zeros numerically.

This script verifies that for each known zero ρ:
  1. σ(ρ) = 1 - conj(ρ) is also a zero
  2. If Re(ρ) = 1/2, then σ(ρ) = ρ
  3. The quadruple {ρ, 1-ρ, conj ρ, 1-conj ρ} are all zeros
"""

import sys
from pathlib import Path

# The importable package lives in `python/`, not at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

# Windows consoles default to a legacy code page (cp1252) that cannot encode the
# Greek letters in the report below.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import mpmath as mp
from riemann_framework.zeta import set_precision, zeta_zero, zeta

set_precision(30)


def sigma(s):
    """The involution σ(s) = 1 - conj(s)."""
    return 1 - mp.conj(s)


def check_sigma_symmetry(n_zeros=10):
    """Check that σ maps zeros to zeros."""
    print("=" * 70)
    print("σ-Symmetry of Riemann Zeros")
    print("=" * 70)
    print()
    print(f"{'n':>3} | {'ρ':>30} | {'σ(ρ)':>30} | {'ζ(σ(ρ))':>12} | {'σ(ρ)=ρ?':>8}")
    print("-" * 70)

    for n in range(1, n_zeros + 1):
        rho = zeta_zero(n)
        sigma_rho = sigma(rho)
        zeta_at_sigma = zeta(sigma_rho)

        is_fixed = mp.almosteq(sigma_rho, rho, abs_eps=mp.mpf('1e-20'))

        print(f"{n:>3} | {str(rho):>30} | {str(sigma_rho):>30} | "
              f"{abs(zeta_at_sigma):>12.2e} | {str(is_fixed):>8}")

    print()


def check_quadruple(n_zeros=5):
    """Check the quadruple symmetry of zeros."""
    print("=" * 70)
    print("Quadruple Symmetry of Zeros")
    print("=" * 70)
    print()

    for n in range(1, n_zeros + 1):
        rho = zeta_zero(n)
        conj_rho = mp.conj(rho)
        one_sub_rho = 1 - rho
        one_sub_conj = 1 - conj_rho

        print(f"Zero #{n}: ρ = {rho}")
        print(f"  ρ           : ζ = {abs(zeta(rho)):.2e}")
        print(f"  1 - ρ       : ζ = {abs(zeta(one_sub_rho)):.2e}")
        print(f"  conj(ρ)     : ζ = {abs(zeta(conj_rho)):.2e}")
        print(f"  1 - conj(ρ) : ζ = {abs(zeta(one_sub_conj)):.2e}")
        print()


def check_fixed_locus(n_zeros=20):
    """Check that fixed points of σ have Re(s) = 1/2."""
    print("=" * 70)
    print("Fixed Locus of σ")
    print("=" * 70)
    print()
    print(f"{'n':>3} | {'Re(ρ)':>20} | {'σ(ρ)=ρ?':>10} | {'Re=1/2?':>10}")
    print("-" * 50)

    for n in range(1, n_zeros + 1):
        rho = zeta_zero(n)
        sigma_rho = sigma(rho)
        is_fixed = mp.almosteq(sigma_rho, rho, abs_eps=mp.mpf('1e-20'))
        re_is_half = mp.almosteq(mp.re(rho), mp.mpf('0.5'),
                                  abs_eps=mp.mpf('1e-20'))

        print(f"{n:>3} | {mp.re(rho):>20} | {str(is_fixed):>10} | "
              f"{str(re_is_half):>10}")

    print()


if __name__ == "__main__":
    check_sigma_symmetry(n_zeros=10)
    check_quadruple(n_zeros=5)
    check_fixed_locus(n_zeros=20)