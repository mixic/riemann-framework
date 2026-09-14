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
"""Test the "dimension lift produces a new Euler product" intuition directly.

Two independent things are checked here:

1. What survives as you double dimension R -> C -> H -> O -> sedenions
   (Cayley-Dickson construction), so the Hurwitz-theorem collapse is seen
   numerically, not just cited.

2. Whether the lift from 2D to 4D produces genuine new Euler-product
   content: Jacobi's four-square theorem, and the resulting Dirichlet
   series identity sum sigma(n)/n^s = zeta(s)*zeta(s-1).

Usage:
    python examples/run_dimension_lift_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from riemann_framework.cayley_dickson import check_properties
from riemann_framework.four_squares import verify_jacobi_formula, verify_sigma_dirichlet_series


def main() -> None:
    print("=" * 70)
    print("Part 1: what survives at each Cayley-Dickson doubling")
    print("=" * 70)
    for dim, label in [(1, "R"), (2, "C"), (4, "H"), (8, "O"), (16, "sedenions")]:
        report = check_properties(dim, n_trials=150)
        print(f"[{label}]  {report.explanation}")
    print()
    print("This is the numerical face of Hurwitz's theorem (1898): a normed")
    print("division algebra over R exists ONLY at dim 1, 2, 4, 8. The circle")
    print("-> sphere -> higher-sphere chain of *clean* number systems")
    print("necessarily stops there.")
    print()

    print("=" * 70)
    print("Part 2: does the 2D -> 4D lift produce genuine Euler-product content?")
    print("=" * 70)
    jacobi = verify_jacobi_formula(n_max=30)
    print(jacobi.explanation)
    print()

    euler = verify_sigma_dirichlet_series(s=3.0, n_max=50_000)
    print(euler.explanation)
    print()

    print("Conclusion: yes -- lifting from 2D (Gaussian integers) to 4D")
    print("(quaternions) genuinely produces a new Dirichlet series with an")
    print("honest Euler-product structure (zeta(s) * zeta(s-1)). The")
    print("dimension-lift intuition is mathematically real at this instance.")
    print()
    print("What this does NOT show: zeta(s)*zeta(s-1) says nothing new about")
    print("*where the zeros of zeta itself are*. That gap -- connecting a")
    print("higher-dimensional construction to the location of zeta's own")
    print("zeros, not just to a related Dirichlet series -- is exactly where")
    print("the open research problem remains.")


if __name__ == "__main__":
    main()
