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
"""Demonstrate where commutativity, associativity, and division-algebra
structure collapse as we double dimension via Cayley-Dickson: R -> C -> H
-> O -> sedenions -> ...

Usage:
    python examples/run_cayley_dickson_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from riemann_framework.cayley_dickson import check_properties


def main() -> None:
    names = {1: "R", 2: "C", 4: "H (quaternions)", 8: "O (octonions)", 16: "sedenions", 32: "32-dim"}

    print("=" * 70)
    print("Cayley-Dickson property collapse, dimension by dimension")
    print("=" * 70)
    for dim in [1, 2, 4, 8, 16, 32]:
        report = check_properties(dim, n_trials=100, seed=0)
        label = names.get(dim, f"dim {dim}")
        print(f"\n{label} (dimension {dim}):")
        print(f"  {report.explanation}")
        if report.zero_divisor_example is not None:
            x, y = report.zero_divisor_example
            print(f"  Example zero divisor found: x={x}, y={y}  (x*y = 0, x!=0, y!=0)")

    print()
    print("This confirms the Hurwitz theorem's consequence numerically: the")
    print("chain of well-behaved number systems (division algebras) stops")
    print("hard at dimension 8. Beyond that, 'number system' in the usual")
    print("sense (where division makes sense) is no longer available --")
    print("any RH-relevant construction beyond dimension 8 needs a different")
    print("kind of object (e.g. an algebra with zero divisors, or a lattice/")
    print("counting structure like in four_squares.py) rather than a number")
    print("system in the sense i, or even the quaternions, exemplify.")


if __name__ == "__main__":
    main()
