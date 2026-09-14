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
"""Demonstrate the primon gas as a concrete arithmetic anchor:

1. Show Tr_N[e^{-sH}] converging to zeta(s) as N grows (an exact,
   provable statement, not a statistical resemblance).
2. Test the "lift sigma to l^2(N) via prime-swap" idea against the
   Hamiltonian directly, and show why it fails, structurally.
3. As a control, show that the identity operator (trivially) commutes.

Usage, from the repository root:
    python python/examples/run_primon_gas_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from riemann_framework.primon_gas import trace_convergence
from riemann_framework.operator_symmetry import (
    build_prime_swap_involution,
    screen_operator,
)


def main() -> None:
    print("=" * 70)
    print("Part 1: Tr_N[e^{-sH}] -> zeta(s), an exact convergence statement")
    print("=" * 70)
    result = trace_convergence(s=2.0)
    print(f"  At s=2, Tr_N[e^-sH] -> zeta(2) = {result['zeta_reference']:.6f}")
    print(f"  relative errors: {[f'{e:.2e}' for e in result['relative_errors']]}")
    print(f"  errors strictly decreasing: {result['errors_decrease']}")
    print()

    print("=" * 70)
    print("Part 2: does the prime-swap lift of sigma commute with H?")
    print("=" * 70)
    N = 2000
    W = build_prime_swap_involution(N, p1=2, p2=3)
    verdict = screen_operator(W, N)
    print(f"N = {N}, primes swapped: (2, 3)")
    print(verdict["explanation"])
    print()

    print("Checking whether the commutator shrinks as N grows "
          "(it should not, if the failure is structural):")
    for N_test in [200, 500, 1000, 2000, 4000]:
        W_test = build_prime_swap_involution(N_test, p1=2, p2=3)
        v = screen_operator(W_test, N_test)
        print(f"  N={N_test:5d}  ||[W,H]||_F = {v['commutator_norm']:.4f}")
    print()

    print("=" * 70)
    print("Part 3: control -- the identity operator commutes trivially")
    print("=" * 70)
    N = 500
    identity_verdict = screen_operator(np.eye(N), N)
    print(identity_verdict["explanation"])


if __name__ == "__main__":
    main()
