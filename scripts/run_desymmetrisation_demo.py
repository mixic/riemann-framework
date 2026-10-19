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
"""Plot the contamination table: mean r against the number of unresolved sectors.

Usage, from the repository root:

    python scripts/run_desymmetrisation_demo.py

Writes `output/desymmetrisation.png`. The panel is the evidence for the warning's
thresholds, and it shows both limits at once: the two curves are on top of each
other from two sectors on (so the class is unreadable), and from three sectors on
the value is at the Poisson level (so the sector count is unrecoverable).
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_DESYMMETRISATION_BOOTSTRAPPED"
):
    os.environ["_DESYMMETRISATION_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.desymmetrisation import (  # noqa: E402
    MULTI_SECTOR_CEILING,
    R_GOE,
    R_GUE,
    R_POISSON,
    SINGLE_SECTOR_FLOOR,
    TWO_SECTOR_BAND,
    calibration_table,
    estimate_sector_count,
)

SECTOR_COUNTS = (1, 2, 3, 4, 6)
SEEDS = 300


def main() -> None:
    rows = calibration_table(SECTOR_COUNTS, dimension=60, seeds=SEEDS)
    table = calibration_table((1, 2, 3, 4), dimension=60, seeds=SEEDS)

    figure, axis = plt.subplots(figsize=(10, 6), constrained_layout=True)
    axis.axhspan(*TWO_SECTOR_BAND, color="orange", alpha=0.10,
                 label=f"two-sector band {TWO_SECTOR_BAND}")
    axis.axhline(SINGLE_SECTOR_FLOOR, color="0.4", linestyle="--", linewidth=1.0,
                 label=f"single-sector floor {SINGLE_SECTOR_FLOOR}")
    axis.axhline(MULTI_SECTOR_CEILING, color="0.4", linestyle=":", linewidth=1.0,
                 label=f"multi-sector ceiling {MULTI_SECTOR_CEILING}")

    for matrix_class, colour, marker in (("goe", "orange", "o"), ("gue", "green", "s")):
        subset = sorted(
            (row for row in rows if row.matrix_class == matrix_class),
            key=lambda row: row.n_sectors,
        )
        axis.errorbar(
            [row.n_sectors for row in subset],
            [row.mean_r for row in subset],
            yerr=[row.std_r for row in subset],
            fmt=f"{marker}-", color=colour, capsize=4, markersize=8,
            label=f"{matrix_class.upper()} blocks",
        )

    axis.axhline(R_GOE, color="orange", linestyle=":", linewidth=1.0, label=f"GOE {R_GOE}")
    axis.axhline(R_GUE, color="green", linestyle="-.", linewidth=1.0, label=f"GUE {R_GUE}")
    axis.axhline(R_POISSON, color="red", linestyle="--", linewidth=1.2,
                 label=f"Poisson {R_POISSON}")

    goe_one = next(
        row for row in rows if row.matrix_class == "goe" and row.n_sectors == 1
    )
    gue_one = next(
        row for row in rows if row.matrix_class == "gue" and row.n_sectors == 1
    )
    axis.annotate(
        "one sector: the class is readable\n"
        f"GOE {goe_one.mean_r:.2f} vs GUE {gue_one.mean_r:.2f}",
        xy=(1.0, 0.55), fontsize=8, ha="left",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    axis.annotate(
        "two sectors: the curves meet,\nthe class information is gone",
        xy=(2.0, 0.43), xytext=(2.3, 0.50), fontsize=8,
        arrowprops={"arrowstyle": "->", "linewidth": 0.8},
    )
    axis.annotate(
        "three or more: at the Poisson level,\nso the count is unrecoverable",
        xy=(4.0, 0.395), xytext=(3.3, 0.34), fontsize=8,
        arrowprops={"arrowstyle": "->", "linewidth": 0.8},
    )

    axis.set_xlabel("unresolved independent sectors")
    axis.set_ylabel(r"mean adjacent-gap ratio $\langle r \rangle \pm$ std")
    axis.set_xticks(list(SECTOR_COUNTS))
    axis.set_ylim(0.32, 0.66)
    axis.set_title(
        f"Desymmetrise before testing the class ({SEEDS} seeds per point)\n"
        "a single spectrum cannot count the sectors, and at two it cannot name the class"
    )
    axis.grid(alpha=0.25)
    axis.legend(fontsize=7, ncol=2, loc="center right")

    out = PROJECT_ROOT / "output" / "desymmetrisation.png"
    figure.savefig(out, dpi=150)
    plt.close(figure)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    for row in rows:
        print("  " + row.summary())
    print()
    print("The two limits, measured:")
    print("  two sectors: GOE and GUE differ by "
          f"{abs(rows[1].mean_r - rows[6].mean_r):.4f}, below their own std")
    estimates = [
        estimate_sector_count(row.mean_r, table, row.matrix_class) for row in rows
    ]
    print("  the same mean inverted for a sector count gives: "
          + ", ".join(f"{value:.1f}" for value in estimates))
    print("  -> the count saturates and is not recoverable; the warning is a flag,")
    print("     not a classifier.")
    print()
    print("No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
