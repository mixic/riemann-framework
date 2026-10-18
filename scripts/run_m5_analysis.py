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
"""Run the M5 analysis: the decisive test for the Dimension-Shift Hypothesis.

Usage, from the repository root:

    python scripts/run_m5_analysis.py

Writes `output/m5_verdict.txt`, `output/m5_criterion1.png` and
`output/m5_criterion2.png`.

The grid is computed **once** and both the verdict and the figures are derived from
those same `ParameterPoint` objects. Recomputing for the plots would let a figure
disagree with the verdict it illustrates, which is the class of defect this
milestone exists to remove.

Cost: at 300 seeds per point, `d = 100` takes about 2.5 s and `d = 200` about 24 s,
so the default grid runs for roughly three to four minutes. Progress is printed as
each point completes.
"""

from __future__ import annotations

import os
import runpy
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_M5_BOOTSTRAPPED"
):
    os.environ["_M5_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.m5_analysis import (  # noqa: E402
    D_MIN,
    GOE_WINDOW,
    GUE_WINDOW,
    N_SEEDS,
    POISSON_WINDOW,
    R_GOE,
    R_GUE,
    ParameterPoint,
    run_m5_analysis,
)

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

#: The grid. `d = 150` is omitted for runtime; the Std-vs-size study in
#: `falsification_test.size_scaling_study` covers the trend between these two, and
#: the verdict does not depend on it (see `docs/m5_verdict.md`).
GRID_DIMS = [D_MIN, 200]
GRID_COUPLINGS = [0.5, 1.0, 2.0, 5.0]


def _plot_criterion_1(points: list[ParameterPoint]) -> None:
    """Sector means against coupling, one panel per class, from the data used."""
    classes = sorted({point.matrix_class for point in points})
    figure, axes = plt.subplots(1, len(classes), figsize=(7 * len(classes), 5.5),
                                squeeze=False, constrained_layout=True)
    markers = {D_MIN: "o", 150: "s", 200: "^", 250: "D"}
    for axis, matrix_class in zip(axes[0], classes):
        subset = [point for point in points if point.matrix_class == matrix_class]
        axis.axhspan(*GOE_WINDOW, color="orange", alpha=0.12,
                     label=f"GOE window {GOE_WINDOW}")
        axis.axhspan(*GUE_WINDOW, color="green", alpha=0.12,
                     label=f"GUE window {GUE_WINDOW}")
        for dimension in sorted({point.dim_per_sector for point in subset}):
            rows = sorted(
                (point for point in subset if point.dim_per_sector == dimension),
                key=lambda point: point.coupling,
            )
            couplings = [point.coupling for point in rows]
            marker = markers.get(dimension, "o")
            axis.errorbar(
                couplings, [point.sector_plus.mean_r for point in rows],
                yerr=[point.sector_plus.std_r / np.sqrt(point.sector_plus.n_seeds) for point in rows],
                fmt=f"{marker}-", color="teal", capsize=3, markersize=7,
                label=f"sector +1, d={dimension}",
            )
            axis.errorbar(
                couplings, [point.sector_minus.mean_r for point in rows],
                yerr=[point.sector_minus.std_r / np.sqrt(point.sector_minus.n_seeds) for point in rows],
                fmt=f"{marker}--", color="darkorange", capsize=3, markersize=7,
                label=f"sector -1, d={dimension}",
            )
            axis.plot(
                couplings, [point.full_spectrum_mean for point in rows],
                f"{marker}:", color="darkblue", markersize=6,
                label=f"full spectrum, d={dimension}",
            )
        axis.axhline(R_GOE, color="orange", linestyle=":", linewidth=1.0)
        axis.axhline(R_GUE, color="green", linestyle="-", linewidth=1.0)
        axis.set_xlabel("inter-sector coupling")
        axis.set_ylabel(r"sector mean $\langle r\rangle$ (error bars: sem)")
        axis.set_title(f"criterion (1) with {matrix_class.upper()} blocks")
        axis.set_ylim(0.33, 0.66)
        axis.grid(alpha=0.25)
    axes[0][0].legend(fontsize=6, ncol=2, loc="lower right", framealpha=0.9)
    figure.suptitle(
        f"Criterion (1) at {N_SEEDS} seeds per point: the sectors follow the input "
        "block class,\nso 'all sectors GOE' holds for GOE blocks and fails for GUE "
        "blocks. A class-conditional criterion is criterion (2).",
        fontsize=10,
    )
    figure.savefig(OUTPUT_DIR / "m5_criterion1.png", dpi=150)
    plt.close(figure)


def _plot_criterion_2(points: list[ParameterPoint]) -> None:
    """The two admissible input classes side by side, from the data used."""
    figure, axis = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    axis.axhspan(*GOE_WINDOW, color="orange", alpha=0.12,
                 label=f"GOE window {GOE_WINDOW}")
    axis.axhspan(*GUE_WINDOW, color="green", alpha=0.12,
                 label=f"GUE window {GUE_WINDOW}")
    axis.axhspan(*POISSON_WINDOW, color="red", alpha=0.08,
                 label=f"Poisson window {POISSON_WINDOW}")
    for point in points:
        axis.scatter(
            [point.coupling], [point.sector_plus.mean_r], marker="o", s=70,
            color="teal" if point.matrix_class == "gue" else "darkorange",
        )
        axis.scatter(
            [point.coupling], [point.sector_minus.mean_r], marker="s", s=70,
            color="teal" if point.matrix_class == "gue" else "darkorange",
        )
        axis.annotate(
            f"{point.matrix_class}",
            (point.coupling, point.sector_plus.mean_r),
            textcoords="offset points", xytext=(6, 6), fontsize=7,
        )
    axis.plot([], [], "o", color="teal", label="GUE input blocks")
    axis.plot([], [], "o", color="darkorange", label="GOE input blocks")
    axis.axhline(R_GOE, color="orange", linestyle=":", linewidth=1.0)
    axis.axhline(R_GUE, color="green", linestyle="-", linewidth=1.0)
    axis.set_xlabel("inter-sector coupling")
    axis.set_ylabel(r"sector mean $\langle r\rangle$")
    axis.set_title("criterion (2): the sector class follows the input blocks")
    axis.set_ylim(0.48, 0.64)
    axis.grid(alpha=0.25)
    axis.legend(fontsize=8, loc="center right")
    figure.savefig(OUTPUT_DIR / "m5_criterion2.png", dpi=150)
    plt.close(figure)


def _write_verdict(path: Path, verdict, elapsed: float) -> None:
    lines: list[str] = []
    lines.append("M5 Analysis: the decisive test for the Dimension-Shift Hypothesis")
    lines.append("=" * 74)
    lines.append("")
    lines.append(f"seeds per parameter point: {N_SEEDS}")
    lines.append(f"dimensions tested: {GRID_DIMS}")
    lines.append(f"couplings tested: {GRID_COUPLINGS}")
    lines.append(f"matrix classes tested: {sorted(verdict.criterion1.per_class_holds)}")
    lines.append(f"wall-clock: {elapsed:.0f} s")
    lines.append("")
    lines.append(f"VERDICT: {verdict.verdict.upper()}")
    lines.append(f"DSH abandoned: {verdict.dsh_abandoned}")
    lines.append("")
    lines.append(verdict.summary)
    lines.append("")
    lines.append("Criterion (1): structural GOE")
    lines.append(f"  holds (all admissible classes): {verdict.criterion1.holds}")
    lines.append(
        "  holds per class: "
        + ", ".join(
            f"{name}={ok}" for name, ok in sorted(verdict.criterion1.per_class_holds.items())
        )
    )
    lines.append(f"  sectors tested: {verdict.criterion1.n_sectors_tested}")
    lines.append(f"  sectors in GOE window: {verdict.criterion1.n_sectors_in_goe}")
    lines.append(f"  sectors in GUE window: {verdict.criterion1.n_sectors_in_gue}")
    lines.append(
        f"  full spectrum never in the GUE window: "
        f"{verdict.criterion1.full_spectrum_never_gue}"
    )
    lines.append(
        f"  max sector mean: {verdict.criterion1.max_sector_mean:.4f} at "
        f"{verdict.criterion1.max_sector_mean_point}"
    )
    lines.append(f"  {verdict.criterion1.explanation}")
    lines.append("")
    lines.append("Criterion (2): inherited class")
    lines.append(f"  holds: {verdict.criterion2.holds}")
    lines.append(
        f"  GUE blocks -> GUE sectors: "
        f"{verdict.criterion2.gue_blocks_lead_to_gue_sectors}/2"
    )
    lines.append(
        f"  GOE blocks -> GUE sectors: "
        f"{verdict.criterion2.goe_blocks_lead_to_gue_sectors}/2"
    )
    lines.append(f"  {verdict.criterion2.explanation}")
    lines.append("")
    lines.append("Per-point table (mean +- per-seed std, 300 seeds):")
    lines.append(
        f"  {'class':>4} {'d':>4} {'coupling':>8} {'full':>18} "
        f"{'sector +1':>18} {'sector -1':>18} {'||[H,o]||/||H||':>16}"
    )
    for point in verdict.criterion1.points:
        lines.append(
            f"  {point.matrix_class:>4} {point.dim_per_sector:4d} "
            f"{point.coupling:8.2f} "
            f"{point.full_spectrum_mean:9.4f}+-{point.full_spectrum_std:.4f} "
            f"{point.sector_plus.mean_r:9.4f}+-{point.sector_plus.std_r:.4f} "
            f"{point.sector_minus.mean_r:9.4f}+-{point.sector_minus.std_r:.4f} "
            f"{point.sigma_commutator_ratio:16.1e}"
        )
    lines.append("")
    lines.append("What is not claimed:")
    lines.append("  - not a proof of the Riemann hypothesis;")
    lines.append("  - not a proof that the DSH is false in every form -- one")
    lines.append("    construction is falsified;")
    lines.append("  - no new evidence for or against RH is produced here.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print("=" * 74)
    print("M5 Analysis: the decisive test for the Dimension-Shift Hypothesis")
    print("=" * 74)
    print(f"\nGrid: d in {GRID_DIMS}, coupling in {GRID_COUPLINGS}, "
          f"{N_SEEDS} seeds each, two matrix classes.")
    print("Expect about three to four minutes; each point prints when it lands.\n")

    start = time.perf_counter()
    verdict = run_m5_analysis(n_seeds=N_SEEDS, progress=lambda line: print("  " + line))
    elapsed = time.perf_counter() - start

    print()
    print("=" * 74)
    print("Criterion (1): structural GOE")
    print("=" * 74)
    print(f"  holds (all classes): {verdict.criterion1.holds}")
    print(f"  per class: {verdict.criterion1.per_class_holds}")
    print(f"  sectors in GOE window: {verdict.criterion1.n_sectors_in_goe}"
          f"/{verdict.criterion1.n_sectors_tested}")
    print(f"  sectors in GUE window: {verdict.criterion1.n_sectors_in_gue}"
          f"/{verdict.criterion1.n_sectors_tested}")
    print(f"  max sector mean: {verdict.criterion1.max_sector_mean:.4f}")
    print(f"  {verdict.criterion1.explanation}")

    print()
    print("=" * 74)
    print("Criterion (2): inherited class")
    print("=" * 74)
    print(f"  holds: {verdict.criterion2.holds}")
    print(f"  GUE blocks -> GUE sectors: "
          f"{verdict.criterion2.gue_blocks_lead_to_gue_sectors}/2")
    print(f"  GOE blocks -> GUE sectors: "
          f"{verdict.criterion2.goe_blocks_lead_to_gue_sectors}/2")
    print(f"  {verdict.criterion2.explanation}")

    print()
    print("=" * 74)
    print(f"VERDICT: {verdict.verdict.upper()}")
    print("=" * 74)
    print(f"  {verdict.summary}")
    print()

    print("Per-point table:")
    for point in verdict.criterion1.points:
        print(f"  {point.summary()}")

    _plot_criterion_1(verdict.criterion1.points)
    _plot_criterion_2(verdict.criterion2.points)
    _write_verdict(OUTPUT_DIR / "m5_verdict.txt", verdict, elapsed)

    print()
    print(f"Wrote m5_verdict.txt, m5_criterion1.png, m5_criterion2.png "
          f"({elapsed:.0f} s)")
    print()
    print("The Riemann hypothesis is not proved or disproved. This settles one")
    print("construction, and the verdict above is the result.")


if __name__ == "__main__":
    main()
