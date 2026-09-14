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
"""Run the DSH falsification grid and write reproducible result artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
import numpy as np

from riemann_framework.falsification_test import (
    FalsificationResult,
    run_grid,
    summarize_grid,
)
from riemann_framework.quantum_chaos import compare_reference_systems
from riemann_framework.statistics import REFERENCE_R

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def _write_summary(summary, references, path):
    with path.open("w", encoding="utf-8") as output:
        output.write("Falsification Test for the Dimension-Shift Hypothesis\n")
        output.write("=====================================================\n\n")
        output.write("Reference systems (mean r):\n")
        for name in ("poisson", "goe", "gue", "riemann"):
            value = references[name]
            output.write(f"  {name}: {value:.6f}\n")
        output.write("\nGrid summary:\n")
        for key in (
            "n_runs", "n_gue", "n_goe", "n_poisson", "n_intermediate",
            "min_mean_r", "max_mean_r", "verdict",
        ):
            output.write(f"  {key}: {summary[key]}\n")
        output.write("\nMaximum point:\n")
        output.write(f"  {summary['max_mean_r_params']}\n")
        output.write("\nExplanation:\n")
        output.write(f"  {summary['explanation']}\n")


def _plot_artifacts(results: Sequence[FalsificationResult]) -> None:
    dimensions = sorted({result.dim_per_sector for result in results})
    couplings = sorted({result.coupling for result in results})
    symmetry_breaking = sorted({result.symmetry_breaking for result in results})

    _plot_grid(dimensions, couplings, symmetry_breaking, results)
    _plot_distribution(results)


def _plot_grid(
    dimensions: Sequence[int],
    couplings: Sequence[float],
    symmetry_breaking: Sequence[float],
    results: Sequence[FalsificationResult],
) -> None:
    if not dimensions:
        return

    figure: Figure = plt.figure(
        figsize=(5 * len(dimensions), 4), constrained_layout=True
    )
    panel_axes = figure.subplots(1, len(dimensions), squeeze=False)[0]

    # Bound before the loop so the colorbar below cannot reference an unbound
    # name: `dimensions` is non-empty here, but a static analyzer cannot know
    # the loop body ran at least once.
    image: AxesImage | None = None
    for axis, dimension in zip(panel_axes, dimensions):
        values = np.full((len(symmetry_breaking), len(couplings)), np.nan)
        for result in results:
            if result.dim_per_sector != dimension:
                continue
            row = symmetry_breaking.index(result.symmetry_breaking)
            column = couplings.index(result.coupling)
            values[row, column] = result.mean_r
        image = axis.imshow(values, vmin=0.3, vmax=0.65, aspect="auto", cmap="viridis")
        axis.set_title(f"d = {dimension}")
        axis.set_xlabel("Coupling")
        axis.set_ylabel("Symmetry breaking")
        axis.set_xticks(range(len(couplings)), [f"{value:g}" for value in couplings])
        axis.set_yticks(
            range(len(symmetry_breaking)),
            [f"{value:g}" for value in symmetry_breaking],
        )

    if image is not None:
        figure.colorbar(image, ax=list(panel_axes), label="Mean r-ratio")

    figure.suptitle("Dimension-shift falsification grid")
    figure.savefig(OUTPUT_DIR / "falsification_heatmap.png", dpi=150)
    plt.close(figure)


def _plot_distribution(results: Sequence[FalsificationResult]) -> None:
    if not results:
        return

    figure: Figure = plt.figure(figsize=(8, 5))
    axis: Axes = figure.subplots()
    axis.hist(
        [result.mean_r for result in results],
        bins=12,
        color="steelblue",
        edgecolor="white",
    )
    for name, colour in (("Poisson", "red"), ("GOE", "orange"), ("GUE", "green")):
        value = REFERENCE_R[name.lower()]
        axis.axvline(
            value, color=colour, linestyle="--", label=f"{name} ({value:.3f})"
        )
    axis.set_xlabel("Mean r-ratio")
    axis.set_ylabel("Parameter points")
    axis.set_title("Falsification-grid distribution")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "falsification_histogram.png", dpi=150)
    plt.close(figure)


def main():
    print("=" * 70)
    print("Falsification Test for the Dimension-Shift Hypothesis (DSH)")
    print("=" * 70)
    references = compare_reference_systems(n=100, seed=42)
    print("\nReference mean r values:")
    for name in ("poisson", "goe", "gue", "riemann"):
        print(f"  {name:8}: {references[name]:.6f}")

    print("\nRunning grid...")
    results = run_grid(seed=42)
    summary = summarize_grid(results)

    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    print("   d |   coup |     sb |  mean_r | best_fit | verdict")
    print("-" * 70)
    for result in results:
        print(f"{result.dim_per_sector:4d} | {result.coupling:7.2f} | {result.symmetry_breaking:7.2f} | "
              f"{result.mean_r:8.4f} | {result.best_fit:9} | {result.verdict}")

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    for key in ("n_runs", "n_gue", "n_goe", "n_poisson", "n_intermediate", "min_mean_r", "max_mean_r", "verdict"):
        print(f"{key:18}: {summary[key]}")
    print("\nExplanation:\n  " + summary["explanation"])

    _plot_artifacts(results)
    _write_summary(summary, references, OUTPUT_DIR / "falsification_summary.txt")
    print("\nWrote falsification_heatmap.png, falsification_histogram.png, and falsification_summary.txt")


if __name__ == "__main__":
    main()
