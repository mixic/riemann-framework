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
"""Generate Fig. 2 of the desymmetrisation manuscript: the resolution of the statistic.

Usage, from the repository root:

    python scripts/generate_seed_study_figure.py

Writes `output/desymmetrisation_seeds.png`, two measured panels:

* (a) `mean r` of a two-sector superposition against the number of spectra, on nested
  samples, with the 95% error of the mean and the per-spectrum scatter as a band. The
  mean settles and its error falls as `1 / sqrt(seeds)`; the scatter does not move.
* (b) the two per-spectrum distributions at two sectors, superimposed, with the best
  single-threshold balanced accuracy printed on the axes, and the same measurement at
  one sector for comparison.

The distinction the figure exists for: *more spectra* sharpen a statement about an
ensemble and do not sharpen a statement about one measured spectrum. Every number is
computed here; the console output prints the values the manuscript quotes.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_SEED_STUDY_FIGURE_BOOTSTRAPPED"
):
    os.environ["_SEED_STUDY_FIGURE_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.desymmetrisation import (  # noqa: E402
    R_GOE,
    R_GUE,
    ThresholdSeparation,
    convergence_series,
    mean_gap_separation,
    superposition_spectrum,
)
from riemann_framework.statistics import mean_r_ratio  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "output"

#: The sample sizes in panel (a); the largest is the size of the nested sample.
SEED_COUNTS = (25, 50, 100, 200, 400, 800, 1600, 3200)

#: Spectra per class in the overlap panel.
OVERLAP_SEEDS = 4000

#: The sector count both panels are measured at, and the per-sector dimension.
SECTORS = 2
DIMENSION = 60

#: 95% of a normal sample of the mean.
Z_95 = 1.959963985


def _colours() -> dict[str, str]:
    return {"goe": "tab:orange", "gue": "tab:green"}


def _overlap_samples() -> dict[str, np.ndarray]:
    return {
        matrix_class: np.array(
            [
                float(
                    mean_r_ratio(
                        superposition_spectrum(
                            SECTORS, DIMENSION, matrix_class, 400_000 + index
                        ),
                        unfold=False,
                    )
                )
                for index in range(OVERLAP_SEEDS)
            ]
        )
        for matrix_class in ("goe", "gue")
    }


def build_figure() -> tuple[plt.Figure, dict]:
    """Both panels, from measured data, plus the numbers the manuscript quotes."""
    colours = _colours()
    figure, (left, right) = plt.subplots(1, 2, figsize=(9.6, 4.15), constrained_layout=True)

    series = {
        matrix_class: convergence_series(
            SECTORS, DIMENSION, matrix_class, SEED_COUNTS, seed=0
        )
        for matrix_class in ("goe", "gue")
    }

    for matrix_class, points in series.items():
        counts = np.array([point.seeds for point in points])
        means = np.array([point.mean_r for point in points])
        errors = np.array([Z_95 * point.standard_error for point in points])
        scatter = np.array([point.std_r for point in points])
        colour = colours[matrix_class]
        left.fill_between(
            counts,
            means - scatter,
            means + scatter,
            color=colour,
            alpha=0.13,
            linewidth=0,
            label=f"{matrix_class.upper()} scatter of one spectrum",
        )
        left.errorbar(
            counts,
            means,
            yerr=errors,
            marker="o" if matrix_class == "goe" else "s",
            markersize=5,
            linewidth=1.6,
            color=colour,
            capsize=3,
            label=f"{matrix_class.upper()} mean, 95% error",
        )
    left.axhline(R_GOE, color="tab:orange", linestyle=":", linewidth=1.0, alpha=0.7)
    left.axhline(R_GUE, color="tab:green", linestyle="-.", linewidth=1.0, alpha=0.7)
    left.set_xscale("log")
    left.set_xlabel("spectra per class (log scale)")
    left.set_ylabel(r"two-sector $\langle r \rangle$")
    left.set_ylim(0.372, 0.468)
    left.grid(alpha=0.25, which="both")
    left.legend(fontsize=7.0, loc="center right")
    left.set_title("(a) more spectra sharpen the mean, not the spectrum", fontsize=9.5)

    goe = series["goe"][-1]
    gue = series["gue"][-1]
    gap = abs(goe.mean_r - gue.mean_r)
    combined = float(np.hypot(goe.standard_error, gue.standard_error))
    left.annotate(
        f"{goe.seeds} spectra: gap {gap:.4f}\n"
        f"= {gap / combined:.1f} sigma of the mean,\n"
        f"= {gap / gue.std_r:.2f} of one spectrum's scatter",
        xy=(0.025, 0.05),
        xycoords="axes fraction",
        fontsize=8,
        va="bottom",
        bbox={"facecolor": "white", "edgecolor": "0.8", "alpha": 0.92},
    )

    samples = _overlap_samples()
    bins = np.linspace(0.30, 0.56, 70)
    for matrix_class, sample in samples.items():
        right.hist(
            sample,
            bins=bins,
            density=True,
            histtype="stepfilled",
            alpha=0.45,
            color=colours[matrix_class],
            edgecolor=colours[matrix_class],
            linewidth=1.2,
            label=f"{matrix_class.upper()}, {sample.size} spectra",
        )
    separation: ThresholdSeparation = mean_gap_separation(SECTORS, DIMENSION, seeds=500)
    single = mean_gap_separation(1, DIMENSION, seeds=500)
    right.axvline(
        separation.threshold, color="black", linestyle="--", linewidth=1.4,
        label=f"best threshold {separation.threshold:.4f}",
    )
    right.set_xlabel(r"two-sector $\langle r \rangle$, one spectrum")
    right.set_ylabel("density")
    right.set_xlim(0.30, 0.56)
    right.grid(alpha=0.25)
    right.legend(fontsize=7.0, loc="upper left")
    right.set_title(
        "(b) the classes overlap completely at two sectors", fontsize=9.5
    )
    right.annotate(
        "best accuracy, one spectrum\n"
        f"2 sectors {separation.accuracy:.3f} = chance\n"
        f"1 sector  {single.accuracy:.3f}",
        xy=(0.985, 0.97),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "0.8", "alpha": 0.92},
    )

    summary = {
        "series": series,
        "overlap": separation,
        "single": single,
        "means": {name: float(sample.mean()) for name, sample in samples.items()},
        "stds": {name: float(sample.std(ddof=1)) for name, sample in samples.items()},
        "counts": {name: int(sample.size) for name, sample in samples.items()},
        "gap": gap,
        "gap_sigma": gap / combined,
    }
    return figure, summary


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("measuring the resolution of the mean gap ratio")
    print()

    figure, summary = build_figure()
    out = OUTPUT_DIR / "desymmetrisation_seeds.png"
    figure.savefig(out, dpi=150)
    plt.close(figure)
    print(f"  wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    for matrix_class, points in summary["series"].items():
        print(f"  {matrix_class.upper()}:")
        for point in points:
            print(f"    {point.summary()}")
    print()
    print(f"  two-sector overlap ({summary['counts']['goe']} spectra per class):")
    for matrix_class in ("goe", "gue"):
        print(
            f"    {matrix_class.upper()}: mean {summary['means'][matrix_class]:.4f}, "
            f"scatter {summary['stds'][matrix_class]:.4f}"
        )
    print(f"    gap {summary['gap']:.4f} = {summary['gap_sigma']:.1f} sigma of the mean")
    print(f"    {summary['overlap'].summary()}")
    print(f"    one sector, for comparison: {summary['single'].summary()}")
    print()
    print("No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
