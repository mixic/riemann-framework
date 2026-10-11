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
"""Screen every idea in `ideas/` against the Davenport-Heilbronn filter.

Usage, from the repository root:

    python scripts/run_dh_filter.py

The point of the run is the *dead list* at the bottom, and the calibration at the
top that shows the screen is not vacuous. Nothing printed here is a correctness
claim about any idea, and nothing here is evidence for or against the Riemann
hypothesis. A `dead` verdict says an argument would also have established a
statement that is false; an `eligible` verdict says only that the filter found
somewhere for the arithmetic content to live.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

# Re-exec from the repository root if invoked from elsewhere (frozen bootstrap
# so the runpy re-run does not recurse).
if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_DH_FILTER_BOOTSTRAPPED"
):
    os.environ["_DH_FILTER_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

from riemann_framework.dh_filter import (  # noqa: E402
    calibrate,
    dead_list,
    eligible_list,
    inventory_table,
    screen_all,
    unscreened_list,
)
from riemann_framework.idea_pipeline import load_all_ideas  # noqa: E402

_MARK = {"transfers": "==", "fails": "!!", "unsourced": "??"}


def print_calibration() -> None:
    print("=" * 78)
    print("Calibration: the Davenport-Heilbronn object, built and measured")
    print("=" * 78)
    print("The filter is only as good as its inventory, so the two rows this")
    print("repository can check rather than cite are checked here.")
    print()
    report = calibrate()
    print(f"  kappa (derived from self-duality)   {report.kappa:.17g}")
    print(f"  |tau(chi) / (i sqrt 5)|             {report.gauss_sum_modulus:.17g}")
    print(
        "  worst functional-equation residual  "
        f"{report.worst_functional_equation_residual:.3e}"
    )
    print(f"  coefficients are real               {report.coefficients_are_real}")
    print(
        "  coefficients multiplicative         "
        f"{report.coefficients_are_multiplicative}"
    )
    print(
        "  witness                             b(2)b(3) = "
        f"{report.non_multiplicativity_witness[0]:.10f} vs b(6) = "
        f"{report.non_multiplicativity_witness[1]:.10f}"
    )
    print()
    print("  A residual at 1e-30 is the functional equation holding exactly, to")
    print("  working precision: it validates the character, the conductor, the")
    print("  odd-character gamma factor and kappa at once. Non-multiplicativity is")
    print("  the Euler-product row, measured rather than cited.")
    print()


def print_inventory() -> None:
    print("=" * 78)
    print("The inventory: which inputs survive the change from zeta to DH")
    print("=" * 78)
    print(f"{'':3} {'input':34} {'source':18} verified")
    print("-" * 78)
    # `inventory_table` preserves the module's declaration order.
    for row in inventory_table():
        mark = _MARK[row["status"]]
        source = row["source"] or "-"
        verified = "yes" if row["verified_here"] else ""
        print(f"{mark:3} {row['key']:34} {source:18} {verified}")
    print("-" * 78)
    print("  ==  transfers to DH -- the input cannot carry the proof")
    print("  !!  fails for DH     -- using it is what makes an argument eligible")
    print("  ??  unsourced        -- this repository cannot classify it")
    print()


def main() -> None:
    print_calibration()
    print_inventory()

    ideas = load_all_ideas(PROJECT_ROOT / "ideas")
    results = screen_all(ideas)

    print("=" * 78)
    print("Screening")
    print("=" * 78)
    for result in results:
        print(result)
        print()

    print("=" * 78)
    print("The dead list -- the output worth keeping")
    print("=" * 78)
    dead = dead_list(results)
    if dead:
        for idea_id in dead:
            print(f"  DEAD      {idea_id}")
    else:
        print("  (empty)")
    for entry in eligible_list(results):
        print(f"  eligible  {entry}")
    for entry in unscreened_list(results):
        print(f"  unscreened {entry}")
    print()
    print("Every declared input of a dead entry holds for a function whose")
    print("RH-analogue is false, so the argument would have proved a false")
    print("statement. Each such entry is ruled out by logic rather than by")
    print("numerics, which is why it is worth recording before writing any code.")
    print()
    print("Note: 'eligible' is permission, not promise. It says the filter found")
    print("an input DH lacks; it says nothing about whether that input does the")
    print("work. 'unscreened' means the filter has no verdict, not a bad one.")


if __name__ == "__main__":
    main()
