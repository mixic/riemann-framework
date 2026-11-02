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
"""Generate the real-system report: `output/real_systems.png` and its CSV.

Usage, from the repository root:

    python scripts/generate_real_systems_report.py

Three real systems with exact involutions are measured, each with the same statistics the
manuscript uses on synthetic blocks:

* (a) the mean gap ratio of the full spectrum and of each sector, with the Poisson, GOE
  and GUE reference values;
* (b) the same spectra against the detector's size-scaled floor: above it the detector
  clears the spectrum, below it the spectrum is flagged. The full spectra are all flagged,
  which is right; some sectors are flagged too, which is not.

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
    "_REAL_SYSTEMS_BOOTSTRAPPED"
):
    os.environ["_REAL_SYSTEMS_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.desymmetrisation import (  # noqa: E402
    detect_hidden_symmetry,
    size_dependent_floor,
)
from riemann_framework.real_systems import (  # noqa: E402
    DEFAULT_SYSTEMS,
    GOE_MEAN_RATIO,
    GUE_MEAN_RATIO,
    POISSON_MEAN_RATIO,
    default_systems,
)

OUTPUT_DIR = PROJECT_ROOT / "output"

#: Labels on the figure, shorter than the module's names.
SHORT_LABELS = {
    "tfim_free": "Ising\nfree fermions",
    "tfim_interacting": "Ising\ninteracting",
    "heisenberg_chaotic": "Heisenberg\nchaotic",
    "kicked_top": "kicked top",
}


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("measuring the real systems")
    print()

    systems = default_systems()
    rows = []
    for key in DEFAULT_SYSTEMS:
        spectra = systems[key]
        floor = size_dependent_floor(spectra.full.size)
        full_verdict = detect_hidden_symmetry(spectra.full)
        sector_verdicts = [detect_hidden_symmetry(sector) for sector in spectra.sectors]
        sector_means = spectra.sector_means
        sector_floors = [size_dependent_floor(sector.size) for sector in spectra.sectors]
        rows.append(
            {
                "key": key,
                "name": spectra.name,
                "n_full": int(spectra.full.size),
                "full": spectra.full_mean,
                "sectors": sector_means,
                "sector_sizes": [int(sector.size) for sector in spectra.sectors],
                "floor": floor,
                "sector_floors": sector_floors,
                "full_flagged": bool(full_verdict.is_contaminated),
                "full_estimate": full_verdict.estimated_sectors,
                "sector_flags": [bool(v.is_contaminated) for v in sector_verdicts],
                "raises": spectra.split_raises_the_statistic,
                "commutator": spectra.commutator,
            }
        )

    print(
        "system".rjust(24)
        + "  levels  full <r>   sectors"
        + " " * 12
        + " floor  full flag  sector flags"
    )
    for row in rows:
        sectors = ", ".join(f"{value:.3f}" for value in row["sectors"])
        flags = ", ".join("flag" if flag else "clear" for flag in row["sector_flags"])
        print(
            f"{row['name']:>24}  {row['n_full']:>6}  {row['full']:.3f}   {sectors:<16} "
            f"{row['floor']:.3f}  {'yes' if row['full_flagged'] else 'no ':>9}  {flags}"
        )

    flagged_full = sum(row["full_flagged"] for row in rows)
    cleared_sectors = sum(1 for row in rows for flag in row["sector_flags"] if not flag)
    total_sectors = sum(len(row["sector_flags"]) for row in rows)
    raising = [row["key"] for row in rows if row["raises"]]

    print()
    print(f"  the full spectrum is flagged in {flagged_full} of {len(rows)} systems")
    print(f"  {cleared_sectors} of {total_sectors} sectors are cleared by the detector")
    print(f"  the split lowers the statistic in {len(raising)} of {len(rows)}: "
          f"{', '.join(raising)}")
    print()
    print("reference values: Poisson 0.386, GOE 0.531, GUE 0.600")

    csv_path = OUTPUT_DIR / "real_systems.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "system",
                "levels",
                "full_mean_r",
                "sector_mean_r",
                "sector_levels",
                "floor",
                "full_flagged",
                "sectors_flagged",
                "split_raises",
                "commutator",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["key"],
                    row["n_full"],
                    f"{row['full']:.4f}",
                    ";".join(f"{value:.4f}" for value in row["sectors"]),
                    ";".join(str(size) for size in row["sector_sizes"]),
                    f"{row['floor']:.4f}",
                    int(row["full_flagged"]),
                    ";".join(str(int(flag)) for flag in row["sector_flags"]),
                    int(row["raises"]),
                    f"{row['commutator']:.1e}",
                ]
            )
    print(f"  wrote {csv_path.relative_to(PROJECT_ROOT)}")

    figure, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), constrained_layout=True)

    left = axes[0]
    positions = np.arange(len(rows))
    width = 0.26
    for offset, (field, label) in enumerate(
        (("full", "full spectrum"), ("sector_0", "sector 1"), ("sector_1", "sector 2"))
    ):
        if field == "full":
            heights = [row["full"] for row in rows]
        else:
            index = int(field.split("_")[1])
            heights = [row["sectors"][index] for row in rows]
        left.bar(positions + (offset - 1) * width, heights, width=width, label=label)
    for value, label, style in (
        (POISSON_MEAN_RATIO, "Poisson 0.386", ":"),
        (GOE_MEAN_RATIO, "GOE 0.531", "--"),
        (GUE_MEAN_RATIO, "GUE 0.600", "-."),
    ):
        left.axhline(value, color="black", linestyle=style, linewidth=1.0, label=label)
    left.set_xticks(positions)
    left.set_xticklabels([SHORT_LABELS[row["key"]] for row in rows], fontsize=8)
    left.set_ylabel("mean gap ratio")
    left.set_ylim(0.0, 0.75)
    left.grid(alpha=0.25, axis="y")
    left.legend(fontsize=7, loc="upper left", ncol=2)
    left.set_title("(a) full spectrum against its sectors", fontsize=10)

    right = axes[1]
    labels = []
    values = []
    colours = []
    for row in rows:
        labels.append(f"{SHORT_LABELS[row['key']]}\nfull".replace("\n", " "))
        values.append(row["full"] - row["floor"])
        colours.append("salmon" if row["full_flagged"] else "steelblue")
        for index, (mean, floor, flag) in enumerate(
            zip(row["sectors"], row["sector_floors"], row["sector_flags"])
        ):
            labels.append(f"{SHORT_LABELS[row['key']]}\nsector {index + 1}".replace("\n", " "))
            values.append(mean - floor)
            colours.append("salmon" if flag else "steelblue")
    right.barh(np.arange(len(values)), values, color=colours)
    right.axvline(0.0, color="black", linewidth=1.0)
    right.set_yticks(np.arange(len(values)))
    right.set_yticklabels(labels, fontsize=7)
    right.invert_yaxis()
    right.set_xlabel("mean gap ratio minus the size-scaled floor")
    right.grid(alpha=0.25, axis="x")
    right.set_title("(b) below the floor means flagged", fontsize=10)

    png_path = OUTPUT_DIR / "real_systems.png"
    figure.savefig(png_path, dpi=150)
    plt.close(figure)
    print(f"  wrote {png_path.relative_to(PROJECT_ROOT)}")
    print()
    print("No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
