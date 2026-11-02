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
"""Generate the PT-symmetry report: `output/pt_symmetric.png` and its CSV.

Usage, from the repository root:

    python scripts/generate_pt_symmetric_report.py

Two panels:

* (a) the adjacent-gap ratio of the **real parts** of a broken PT spectrum, against the
  antisymmetry strength, with the GOE and Poisson references. The ratio falls from the GOE
  value toward the Poisson one as the imaginary parts grow, which is a property of the
  projection and not of the spectrum;
* (b) the dimer, whose two levels are real below `gamma / g = 1` and a conjugate pair
  above it. The exceptional point is where the ratio of the two structures stops existing.

Every number is computed here. The console output is the table the note transcribes.
"""

from __future__ import annotations

import csv
import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_PT_SYMMETRIC_BOOTSTRAPPED"
):
    os.environ["_PT_SYMMETRIC_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.pt_symmetric_statistics import (  # noqa: E402
    DEFAULT_DIMENSION,
    GOE_MEAN_RATIO,
    POISSON_MEAN_RATIO,
    dimer_table,
    ensemble_table,
)

OUTPUT_DIR = PROJECT_ROOT / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("measuring the PT-symmetric ensembles")
    print()

    rows = ensemble_table()
    print("random real ensemble S + w A, dimension 120, 40 spectra per point")
    for row in rows:
        print("  " + row.summary())

    dimers = dimer_table()
    print()
    print("the PT dimer, eigenvalues against gamma / g")
    for row in dimers:
        print("  " + row.summary())

    csv_path = OUTPUT_DIR / "pt_symmetric.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "antisymmetry",
                "unbroken_fraction",
                "real_part_mean_ratio",
                "imaginary_over_spacing",
                "pairing_defect",
                "seeds",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    f"{row.antisymmetry:.2f}",
                    f"{row.unbroken_fraction:.4f}",
                    f"{row.real_part_mean_ratio:.4f}",
                    f"{row.imaginary_over_spacing:.4f}",
                    f"{row.pairing_defect:.2e}",
                    row.seeds,
                ]
            )
        writer.writerow([])
        writer.writerow(["gamma_over_coupling", "eigenvalue_1", "eigenvalue_2", "unbroken"])
        for row in dimers:
            writer.writerow(
                [
                    f"{row.gamma_over_coupling:.2f}",
                    f"{row.eigenvalues[0].real:.6f}{row.eigenvalues[0].imag:+.6f}j",
                    f"{row.eigenvalues[1].real:.6f}{row.eigenvalues[1].imag:+.6f}j",
                    int(row.unbroken),
                ]
            )
    print()
    print(f"  wrote {csv_path.relative_to(PROJECT_ROOT)}")

    figure, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), constrained_layout=True)

    left = axes[0]
    strengths = [row.antisymmetry for row in rows]
    ratios = [row.real_part_mean_ratio for row in rows]
    left.plot(strengths, ratios, "o-", markersize=5, label="real parts of the spectrum")
    left.axhline(
        GOE_MEAN_RATIO, color="black", linestyle="--", linewidth=1.0,
        label=f"GOE {GOE_MEAN_RATIO:.3f}",
    )
    left.axhline(
        POISSON_MEAN_RATIO, color="black", linestyle=":", linewidth=1.0,
        label=f"Poisson {POISSON_MEAN_RATIO:.3f}",
    )
    left.set_xlabel("antisymmetry strength w")
    left.set_ylabel("mean gap ratio of the real parts")
    left.set_ylim(0.3, 0.6)
    left.grid(alpha=0.25)
    left.legend(fontsize=8, loc="lower left")
    left.set_title("(a) a broken PT spectrum has no real spectrum", fontsize=10)

    right = axes[1]
    dimer_ratios = [row.gamma_over_coupling for row in dimers]
    real_parts = [[value.real for value in row.eigenvalues] for row in dimers]
    imaginary_parts = [[value.imag for value in row.eigenvalues] for row in dimers]
    right.plot(dimer_ratios, [abs(pair[0]) for pair in real_parts], "o-", label="|Re E|")
    right.plot(dimer_ratios, [abs(pair[0]) for pair in imaginary_parts], "s--",
               label="|Im E|")
    right.axvline(1.0, color="gray", linestyle=":", linewidth=1.0)
    right.text(1.02, 0.75, "exceptional point", fontsize=8, color="gray")
    right.set_xlabel(r"$\gamma / g$")
    right.set_ylabel("distance from the mean level")
    right.grid(alpha=0.25)
    right.legend(fontsize=8)
    right.set_title("(b) the dimer is real only below gamma = g", fontsize=10)

    png_path = OUTPUT_DIR / "pt_symmetric.png"
    figure.savefig(png_path, dpi=150)
    plt.close(figure)
    print(f"  wrote {png_path.relative_to(PROJECT_ROOT)}")
    print()
    print(
        f"  dimension {DEFAULT_DIMENSION}; no Riemann-hypothesis claim is made here."
    )


if __name__ == "__main__":
    main()
