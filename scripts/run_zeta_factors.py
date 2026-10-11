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
"""Screen proposed zeta-function frameworks for containment of `zeta`.

Usage, from the repository root:

    python scripts/run_zeta_factors.py

Answers one question about each framework: does its zeta function have `zeta` as
a factor? If yes, a proof of its RH-analogue would imply RH -- but would prove
strictly more, so the target is strictly bigger and cannot be the easier path.
If no, the framework does not deliver RH at all without a separate transfer step,
which is the thing worth writing down.

Nothing printed here is a correctness claim and nothing here proves or disproves
the Riemann hypothesis.
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
    "_ZETA_FACTORS_BOOTSTRAPPED"
):
    os.environ["_ZETA_FACTORS_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

from riemann_framework.zeta_factors import (  # noqa: E402
    FACTORS,
    FRAMEWORKS,
    no_euler_product_list,
    screen_all,
    separate_target_list,
    strictly_harder_list,
    unverified_factorizations,
    verify_factorization,
)

_MARK = {
    "is_the_base_case": "  ",
    "strictly_harder": "!!",
    "separate_target": "--",
    "no_euler_product": "??",
}


def print_factors() -> None:
    print("=" * 78)
    print("Named factors")
    print("=" * 78)
    for factor in FACTORS.values():
        carries = "carries zeta" if factor.contains_zeta else "no zeta"
        print(f"  {factor.key:22s} {carries}")
    print()


def print_screening() -> list:
    results = screen_all()
    print("=" * 78)
    print("Screening")
    print("=" * 78)
    for result in results:
        print(result)
        print()
    return results


def print_verification() -> None:
    print("=" * 78)
    print("What the factorisation check actually verified")
    print("=" * 78)
    print("A declared product is checked against the framework's own Dirichlet")
    print("series, so it is verified rather than trusted.")
    print()
    for framework in FRAMEWORKS:
        if not framework.factors:
            continue
        result = verify_factorization(framework)
        status = "verified" if result.agrees else (
            "UNVERIFIED" if not result.applicable else "DISAGREES"
        )
        print(f"  {framework.id:26s} {status}")
    print()


def main() -> None:
    print_factors()
    print_verification()
    results = print_screening()

    print("=" * 78)
    print("Summary")
    print("=" * 78)
    for entry in strictly_harder_list(results):
        print(f"  !! strictly harder  {entry}")
    for entry in separate_target_list(results):
        print(f"  -- separate target  {entry}")
    for entry in no_euler_product_list(results):
        print(f"  ?? no Euler product {entry}")
    unverified = unverified_factorizations(results)
    if unverified:
        print()
        print("  Containment verdicts resting on a CITED rather than verified")
        print(f"  factorisation: {', '.join(unverified)}")
    print()
    print("  !!  contains zeta: a proof here implies RH, and proves more, so the")
    print("      target is strictly bigger. A valid route that is dominated.")
    print("  --  no zeta factor: a proof here does NOT imply RH. The missing piece")
    print("      is the transfer step back to zeta, and it is the whole proposal.")
    print("  ??  no Euler product, so containment is not well-posed. This is the")
    print("      Davenport-Heilbronn / Epstein family the other filter is built on.")
    print()
    print("Neither '!!' nor '--' is an endorsement. The screen does not find")
    print("routes; it forces the transfer step into the open.")


if __name__ == "__main__":
    main()
