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
"""Measure the diagnostic along a controlled symmetry-breaking crossover.

Usage, from the repository root:

    python scripts/run_symmetry_breaking.py

Writes `output/symmetry_breaking.csv` and prints the table. The perturbation is
`H(g) = H0 + g * Delta * V`, where `Delta` is the mean level spacing of `H0`, so
`g` is dimensionless and comparable across matrix sizes. The model is trained on
exact sectors and is not retrained on broken spectra.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

from riemann_framework.desymmetrisation import default_sector_count_model  # noqa: E402
from riemann_framework.symmetry_breaking import degradation_curve  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output")
    args = parser.parse_args()

    model = default_sector_count_model(240)
    curve = degradation_curve(
        n_sectors=2,
        levels_per_sector=120,
        draws=args.draws,
        seed=args.seed,
        model=model,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "symmetry_breaking.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["g", "mean_r", "flag_rate", "accuracy", "coverage", "draws"])
        for row in curve.rows:
            writer.writerow(
                [
                    row.g,
                    row.mean_r,
                    row.flag_rate,
                    row.accuracy,
                    row.coverage,
                    row.draws,
                ]
            )

    print("Controlled symmetry breaking: H(g) = H0 + g * Delta * V")
    print("Two GOE sectors, 120 levels each, 60 draws, exact-sector posterior.")
    print()
    print(f"{'g':>6} {'mean r':>8} {'flag':>6} {'MAP':>6} {'cover':>6}")
    for row in curve.rows:
        print(
            f"{row.g:6.2f} {row.mean_r:8.3f} {row.flag_rate:6.2f} "
            f"{row.accuracy:6.2f} {row.coverage:6.2f}"
        )
    print()
    print(curve.summary())
    print(f"CSV: {output}")


if __name__ == "__main__":
    main()
