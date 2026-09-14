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
"""Demonstrate the one genuinely real instance of 'higher-dimensional
sphere -> Euler product': Jacobi's four-square theorem and the resulting
Dirichlet series identity sum sigma(n)/n^s = zeta(s) * zeta(s-1).

Usage:
    python examples/run_four_squares_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from riemann_framework.four_squares import verify_jacobi_formula, verify_sigma_dirichlet_series


def main() -> None:
    print("=" * 70)
    print("Part 1: verifying Jacobi's four-square theorem by direct count")
    print("=" * 70)
    result = verify_jacobi_formula(n_max=30)
    print(result.explanation)
    print(f"n:            {result.n_values}")
    print(f"r4 (brute):   {result.r4_brute_values}")
    print(f"r4 (Jacobi):  {result.r4_jacobi_values}")
    print()

    print("=" * 70)
    print("Part 2: the resulting Euler product, verified numerically")
    print("=" * 70)
    euler_result = verify_sigma_dirichlet_series(s=3.0, n_max=200_000)
    print(euler_result.explanation)
    print()

    print("Interpretation: counting integer-lattice points on a 4D sphere")
    print("(the quaternion/Lipschitz-integer norm form) genuinely produces")
    print("an arithmetic function (the divisor sum) whose Dirichlet series")
    print("has an honest Euler product, zeta(s)*zeta(s-1). This is real,")
    print("checkable content -- but it says nothing about *where* zeta's")
    print("own zeros are, which remains the open problem.")


if __name__ == "__main__":
    main()
