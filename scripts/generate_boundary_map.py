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
"""Generate the boundary map: `output/boundary_map.png` and `output/boundary_map.csv`.

Usage, from the repository root:

    python scripts/generate_boundary_map.py

The figure has three panels:

* (a) per-class accuracy against the sector count, one curve per statistic, with the
  0.8 threshold and the chance line. The boundary of a statistic is the last count whose
  accuracy clears the threshold.
* (b) balanced accuracy at telling one sector count from another, two classes at a time:
  the question a statistic can answer without naming the count.
* (c) `Sigma^2(20)` per sector count, with the Poisson control.

Every number is computed here. The console output is the table the note transcribes.
"""

from __future__ import annotations

import csv
import io
import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_BOUNDARY_MAP_BOOTSTRAPPED"
):
    os.environ["_BOUNDARY_MAP_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.boundary_map import (  # noqa: E402
    DEFAULT_SECTORS,
    DEFAULT_STATISTICS,
    DEFAULT_THRESHOLD,
    boundary_of,
    build_spectrum,
    measure,
    number_variance,
    pairwise_accuracy,
    poisson_spectrum,
)

OUTPUT_DIR = PROJECT_ROOT / "output"

#: Training and test spectra per class.
TRAIN = 80
TEST = 80

#: Pairs the pairwise panel compares, and the statistics it compares them for.
PAIRS = ((2, 3), (3, 6), (4, 6))
PAIRWISE_STATISTICS = ("mean_r", "hosr_family", "number_variance")

#: Labels drawn on the figure.
LABELS = {
    "mean_r": "mean ratio (manuscript)",
    "hosr_1": "order 1 mean",
    "hosr_3": "order 3 mean",
    "hosr_6": "order 6 mean",
    "hosr_family": "orders 1-6 (family)",
    "number_variance": "number variance",
}


def _sigma2_at_20(sectors: tuple[int, ...] = DEFAULT_SECTORS) -> dict[int | None, float]:
    """Mean `Sigma^2(20)` per sector count, with the Poisson control at ``None``."""
    values: dict[int | None, float] = {}
    for count in sectors:
        samples = [
            number_variance(build_spectrum(count, 240, seed=5_000 + index))[19]
            for index in range(40)
        ]
        values[count] = float(np.mean(samples))
    poisson = [
        number_variance(poisson_spectrum(240, seed=5_000 + index))[19]
        for index in range(40)
    ]
    values[None] = float(np.mean(poisson))
    return values


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("measuring the boundary map")
    print()

    results = measure(n_train=TRAIN, n_test=TEST)
    print(
        "statistic".rjust(18)
        + " "
        + "  ".join(f"m={m}" for m in DEFAULT_SECTORS)
        + "  boundary"
    )
    for statistic in DEFAULT_STATISTICS:
        row = "  ".join(f"{results[statistic][m]:.3f}" for m in DEFAULT_SECTORS)
        print(f"{statistic:>18} {row}  {boundary_of(results[statistic])}")

    pairwise = {
        (first, second, statistic): pairwise_accuracy(statistic, first, second)
        for first, second in PAIRS
        for statistic in PAIRWISE_STATISTICS
    }
    print()
    print("pairwise balanced accuracy")
    for first, second in PAIRS:
        row = "  ".join(
            f"{statistic}={pairwise[(first, second, statistic)]:.3f}"
            for statistic in PAIRWISE_STATISTICS
        )
        print(f"  {first} vs {second}: {row}")

    sigma2 = _sigma2_at_20()
    print()
    print("Sigma^2(20)")
    for count in DEFAULT_SECTORS:
        print(f"  {count} sectors: {sigma2[count]:.2f}")
    print(f"  Poisson:      {sigma2[None]:.2f}")

    csv_path = OUTPUT_DIR / "boundary_map.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["statistic"] + [f"m={m}" for m in DEFAULT_SECTORS] + ["boundary"]
        )
        for statistic in DEFAULT_STATISTICS:
            writer.writerow(
                [statistic]
                + [f"{results[statistic][m]:.4f}" for m in DEFAULT_SECTORS]
                + [boundary_of(results[statistic])]
            )
        writer.writerow([])
        writer.writerow(
            ["pairwise", ""] + [f"{a}vs{b}" for a, b in PAIRS] + [""]
        )
        for statistic in PAIRWISE_STATISTICS:
            writer.writerow(
                [statistic, ""]
                + [f"{pairwise[(a, b, statistic)]:.4f}" for a, b in PAIRS]
                + [""]
            )
        writer.writerow([])
        writer.writerow(["sigma2_20", ""] + [f"m={m}" for m in DEFAULT_SECTORS] + ["poisson"])
        writer.writerow(
            ["value", ""]
            + [f"{sigma2[m]:.4f}" for m in DEFAULT_SECTORS]
            + [f"{sigma2[None]:.4f}"]
        )
    print()
    print(f"  wrote {csv_path.relative_to(PROJECT_ROOT)}")

    figure, axes = plt.subplots(1, 3, figsize=(15.5, 4.6), constrained_layout=True)

    left = axes[0]
    for statistic in DEFAULT_STATISTICS:
        curve = [results[statistic][m] for m in DEFAULT_SECTORS]
        left.plot(DEFAULT_SECTORS, curve, "o-", markersize=5, label=LABELS[statistic])
    left.axhline(
        DEFAULT_THRESHOLD, color="black", linestyle="--", linewidth=1.0,
        label=f"boundary threshold {DEFAULT_THRESHOLD}",
    )
    left.axhline(
        1.0 / len(DEFAULT_SECTORS), color="gray", linestyle=":", linewidth=1.0,
        label="chance",
    )
    left.set_xticks(list(DEFAULT_SECTORS))
    left.set_xlabel("unresolved sectors m")
    left.set_ylabel("per-class accuracy")
    left.set_ylim(0.0, 1.05)
    left.grid(alpha=0.25)
    left.legend(fontsize=7, loc="upper right")
    left.set_title("(a) can the statistic name the count?", fontsize=10)

    middle = axes[1]
    positions = np.arange(len(PAIRS))
    width = 0.26
    for offset, statistic in enumerate(PAIRWISE_STATISTICS):
        heights = [pairwise[(a, b, statistic)] for a, b in PAIRS]
        middle.bar(
            positions + (offset - 1) * width,
            heights,
            width=width,
            label=LABELS[statistic],
        )
    middle.axhline(0.5, color="gray", linestyle=":", linewidth=1.0, label="chance")
    middle.set_xticks(positions)
    middle.set_xticklabels([f"{a} vs {b}" for a, b in PAIRS])
    middle.set_ylabel("balanced accuracy")
    middle.set_ylim(0.0, 1.0)
    middle.grid(alpha=0.25, axis="y")
    middle.legend(fontsize=7, loc="upper left")
    middle.set_title("(b) can it tell two counts apart?", fontsize=10)

    right = axes[2]
    labels = [str(m) for m in DEFAULT_SECTORS] + ["Poisson"]
    heights = [sigma2[m] for m in DEFAULT_SECTORS] + [sigma2[None]]
    colors = ["steelblue"] * len(DEFAULT_SECTORS) + ["salmon"]
    right.bar(labels, heights, color=colors)
    right.set_xlabel("unresolved sectors m")
    right.set_ylabel(r"$\Sigma^2(20)$")
    right.set_ylim(0.0, max(heights) * 1.15)
    right.grid(alpha=0.25, axis="y")
    right.set_title("(c) number variance at L = 20", fontsize=10)

    png_path = OUTPUT_DIR / "boundary_map.png"
    figure.savefig(png_path, dpi=150)
    plt.close(figure)
    print(f"  wrote {png_path.relative_to(PROJECT_ROOT)}")
    print()
    print("No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
