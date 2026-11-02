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
"""Generate the unequal-sector report: `output/mixed_sector_count.png` and its CSV.

Usage, from the repository root:

    python scripts/generate_mixed_sector_report.py

Three questions, three panels:

* (a) does the count survive a dominant sector? Per-class accuracy of the joint
  `(m, ratio)` posterior's count marginal, one curve per size ratio, against the
  equal-block model applied to the same spectra at the strongest ratio.
* (b) how does the equal-block model fail? Its *mean* count against the truth, one curve
  per ratio: a bias that grows with the ratio is not noise.
* (c) is the size ratio itself recoverable? The ratio's accuracy conditional on the true
  count, which is the fair version of that question.

Every number is computed here, and the console output is the table the note transcribes.
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
    "_MIXED_SECTOR_BOOTSTRAPPED"
):
    os.environ["_MIXED_SECTOR_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.desymmetrisation import (  # noqa: E402
    default_higher_order_model,
)
from riemann_framework.mixed_sector_count import (  # noqa: E402
    DEFAULT_LEVEL,
    DEFAULT_SECTORS,
    DEFAULT_SIZE_RATIOS,
    MixedSectorModel,
    equal_block_bias,
    label_grid,
)

OUTPUT_DIR = PROJECT_ROOT / "output"

#: Spectra per label in the measurement. Two hundred keeps the standard error of an
#: accuracy at about 0.035, which is fine for a table that quotes two decimals.
DRAWS = 200

#: The ratio the figure singles out for the equal-block comparison: the strongest
#: imbalance, where the bias is largest and the joint model's advantage is the point.
STRONGEST = max(DEFAULT_SIZE_RATIOS)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("measuring the unequal-sector posterior")
    print()

    model = MixedSectorModel.fit()
    rows = model.coverage(draws=DRAWS, level=DEFAULT_LEVEL)
    labels = label_grid()
    bias = equal_block_bias(default_higher_order_model(), labels, draws=DRAWS)
    bias_by_label = {row.truth: row for row in bias}

    print(
        "true label".rjust(28)
        + "  count  ratio|count  joint  interval  equal-block  equal mean"
    )
    for row in rows:
        other = bias_by_label[row.truth]
        print(
            f"{row.truth.summary():>28}  {row.count_correct:.3f}  "
            f"{row.ratio_correct:>11.3f}  {row.joint_correct:.3f}  "
            f"{row.joint_covered:>8.3f}  {other.count_correct:>11.3f}  "
            f"{other.mean_count:>10.2f}"
        )

    counts = {
        ratio: {
            m: next(
                row.count_correct
                for row in rows
                if row.truth.n_sectors == m and row.truth.size_ratio == ratio
            )
            for m in DEFAULT_SECTORS
            if m > 1
        }
        for ratio in DEFAULT_SIZE_RATIOS
    }
    equal_counts = {
        ratio: {
            m: next(
                row.count_correct
                for row in bias
                if row.truth.n_sectors == m and row.truth.size_ratio == ratio
            )
            for m in DEFAULT_SECTORS
            if m > 1
        }
        for ratio in DEFAULT_SIZE_RATIOS
    }

    print()
    print("count accuracy against a dominant sector")
    for m in DEFAULT_SECTORS:
        if m == 1:
            continue
        row = "  ".join(
            f"ratio {ratio:g}: {counts[ratio][m]:.3f} vs {equal_counts[ratio][m]:.3f}"
            for ratio in DEFAULT_SIZE_RATIOS
        )
        print(f"  m={m}: {row}")

    csv_path = OUTPUT_DIR / "mixed_sector_count.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "sectors",
                "size_ratio",
                "count_correct",
                "ratio_given_count",
                "joint_correct",
                "interval_coverage",
                "equal_block_count_correct",
                "equal_block_mean_count",
            ]
        )
        for row in rows:
            other = bias_by_label[row.truth]
            writer.writerow(
                [
                    row.truth.n_sectors,
                    f"{row.truth.size_ratio:g}",
                    f"{row.count_correct:.4f}",
                    f"{row.ratio_correct:.4f}",
                    f"{row.joint_correct:.4f}",
                    f"{row.joint_covered:.4f}",
                    f"{other.count_correct:.4f}",
                    f"{other.mean_count:.4f}",
                ]
            )
    print()
    print(f"  wrote {csv_path.relative_to(PROJECT_ROOT)}")

    figure, axes = plt.subplots(1, 3, figsize=(15.5, 4.6), constrained_layout=True)
    measured = [m for m in DEFAULT_SECTORS if m > 1]

    left = axes[0]
    for ratio in DEFAULT_SIZE_RATIOS:
        left.plot(
            measured,
            [counts[ratio][m] for m in measured],
            "o-",
            markersize=5,
            label=f"joint model, ratio {ratio:g}",
        )
    left.plot(
        measured,
        [equal_counts[STRONGEST][m] for m in measured],
        "s--",
        color="black",
        markersize=4,
        linewidth=1.2,
        label=f"equal-block model, ratio {STRONGEST:g}",
    )
    left.axhline(
        1.0 / len(DEFAULT_SECTORS),
        color="gray",
        linestyle=":",
        linewidth=1.0,
        label="chance over five counts",
    )
    left.set_xticks(measured)
    left.set_xlabel("unresolved sectors m")
    left.set_ylabel("count named correctly")
    left.set_ylim(0.0, 1.05)
    left.grid(alpha=0.25)
    left.legend(fontsize=7, loc="lower left")
    left.set_title("(a) does a dominant sector break the count?", fontsize=10)

    middle = axes[1]
    for ratio in DEFAULT_SIZE_RATIOS:
        middle.plot(
            measured,
            [bias_by_label[next(lb for lb in labels if lb.n_sectors == m and lb.size_ratio == ratio)].mean_count for m in measured],
            "o-",
            markersize=5,
            label=f"ratio {ratio:g}",
        )
    middle.plot(measured, measured, "k:", linewidth=1.0, label="unbiased")
    middle.set_xticks(measured)
    middle.set_xlabel("true sector count m")
    middle.set_ylabel("equal-block mean estimate")
    middle.grid(alpha=0.25)
    middle.legend(fontsize=7, loc="upper left")
    middle.set_title("(b) the equal-block model under-counts", fontsize=10)

    right = axes[2]
    positions = np.arange(len(measured))
    width = 0.26
    for offset, ratio in enumerate(DEFAULT_SIZE_RATIOS):
        heights = [
            next(
                row.ratio_correct
                for row in rows
                if row.truth.n_sectors == m and row.truth.size_ratio == ratio
            )
            for m in measured
        ]
        right.bar(
            positions + (offset - 1) * width,
            heights,
            width=width,
            label=f"ratio {ratio:g}",
        )
    right.set_xticks(positions)
    right.set_xticklabels([str(m) for m in measured])
    right.set_xlabel("true sector count m")
    right.set_ylabel("ratio named given the count")
    right.set_ylim(0.0, 1.0)
    right.grid(alpha=0.25, axis="y")
    right.legend(fontsize=7, loc="upper right")
    right.set_title("(c) is the size ratio recoverable?", fontsize=10)

    png_path = OUTPUT_DIR / "mixed_sector_count.png"
    figure.savefig(png_path, dpi=150)
    plt.close(figure)
    print(f"  wrote {png_path.relative_to(PROJECT_ROOT)}")
    print()
    print("Synthetic Gaussian blocks only. No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
