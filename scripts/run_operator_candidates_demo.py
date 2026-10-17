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
"""Screen candidate operators, and show what the screening can and cannot see.

Usage, from the repository root:

    python scripts/run_operator_candidates_demo.py

Writes `output/operator_candidates.png`, six panels:

    1. counting functions of the four candidates on one axis -- linear, power
       law, exponential, and the zeros in between;
    2. the zeros' density, rising from `0.278` to `0.543` per unit height, with
       the power law that reproduces the count to 1.33 levels in 100;
    3. the prime-length graph's spectrum against the lattice `pi n / L` it would
       be if the dictionary determined it -- it is a jittered lattice;
    4. spacing histograms: the graph's statistics, which are *closer* to Wigner
       than the zeros' own;
    5. the unitary twin, whose eigenvalues sit exactly on the zeros;
    6. the screening table.

**No panel claims a proof of the Riemann hypothesis.** Panel 4 is the one that
says the statistics cannot settle it, and panel 6 says nothing else can either.
See `docs/operator_candidates.md`.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_OPERATOR_CANDIDATES_BOOTSTRAPPED"
):
    os.environ["_OPERATOR_CANDIDATES_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.hilbert_polya import (  # noqa: E402
    box_count,
    box_versus_zeros,
    fit_box_length,
)
from riemann_framework.operator_candidates import (  # noqa: E402
    density_table,
    graph_report,
    power_law_fit,
    primon_counting,
    screening_table,
    star_edge_lengths,
    star_spectrum,
    twin_report,
    unitary_twin,
    von_mangoldt_table,
    zero_counting,
)
from riemann_framework.prime_orbits import zeta_zero_ordinates  # noqa: E402
from riemann_framework.statistics import gue_spacing_pdf, level_spacings  # noqa: E402

ZERO_COUNT = 100
ZEROS = np.array(zeta_zero_ordinates(ZERO_COUNT))


def panel_counting(ax) -> None:
    """Three density classes and the zeros between two of them."""
    heights = np.linspace(10.0, 40.0, 300)
    ax.semilogx(heights, [zero_counting(h, ZERO_COUNT) for h in heights], "-",
                color="#1f77b4", linewidth=2.2, label="zeros (exact count)")
    length = fit_box_length(ZEROS)
    ax.semilogx(heights, [max(box_count(h, length), 1e-9) for h in heights], "--",
                color="#d62728", linewidth=1.6, label=r"hard box ($\propto T$)")
    fit = power_law_fit(ZERO_COUNT)
    ax.semilogx(heights, [fit.coefficient * h**fit.exponent for h in heights], ":",
                color="#2ca02c", linewidth=2.0,
                label=rf"best power law $T^{{{fit.exponent:.2f}}}$")
    gas_heights = np.linspace(10.0, 12.0, 60)
    ax.semilogx(gas_heights, [float(primon_counting(g)) for g in gas_heights], "-.",
                color="#9467bd", linewidth=1.8, label=r"primon gas ($e^T$)")
    mangoldt = von_mangoldt_table((20.0, 35.0))
    ax.semilogx([r[0] for r in mangoldt], [r[2] for r in mangoldt], "o",
                color="k", markersize=5, label="Riemann-von Mangoldt")
    ax.set_yscale("log")
    ax.set_ylim(0.8, 5e3)
    ax.set_xlim(10.0, 40.0)
    ax.set_xlabel("height")
    ax.set_ylabel("levels below the height (log scale)")
    ax.set_title("Three density classes: the zeros sit between linear and exponential")
    ax.annotate(
        "primon gas leaves this frame:\n"
        f"$e^{{14}} = {primon_counting(14.0):,}$ levels at $T=14$",
        xy=(12.4, 2.2e3),
        fontsize=7,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(alpha=0.25, which="both")


def panel_density(ax) -> None:
    """The density rises -- a logarithm -- and a power law still fits it."""
    rows = density_table()
    centres = [0.5 * (r.lower + r.upper) for r in rows]
    widths = [r.upper - r.lower for r in rows]
    ax.bar(centres, [r.per_unit_height for r in rows], width=widths, alpha=0.55,
           color="#1f77b4", edgecolor="#1f77b4", label=r"measured $dN/dT$")
    grid = np.linspace(14.0, 240.0, 300)
    ax.plot(grid, np.log(grid / (2 * np.pi)) / (2 * np.pi), "-", color="#2ca02c",
            linewidth=1.8, label=r"$\frac{1}{2\pi}\log\frac{T}{2\pi}$")
    fit = power_law_fit(ZERO_COUNT)
    ax.plot(grid, fit.coefficient * fit.exponent * grid ** (fit.exponent - 1), ":",
            color="#d62728", linewidth=2.0,
            label=rf"power law $T^{{{fit.exponent:.2f}}}$")
    ax.set_xlabel("height")
    ax.set_ylabel(r"$dN/dT$")
    ax.set_title("The density is unbounded -- but a power law hides that")
    ax.annotate(
        rf"count reproduced to {fit.max_error_levels:.2f} levels in {fit.zero_count}"
        "\nso density cannot reject a candidate here",
        xy=(0.03, 0.90),
        xycoords="axes fraction",
        fontsize=8,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(alpha=0.25)


def panel_spectrum(ax) -> None:
    """The dictionary-exact graph's levels against the lattice it would need to be."""
    lengths = star_edge_lengths(5, dictionary_exact=True)
    levels = star_spectrum(lengths, 14.0)
    lattice = np.arange(1, 40) * (np.pi / lengths.sum())
    lattice = lattice[lattice < 14.0]
    ax.plot(levels, np.zeros_like(levels), "|", markersize=14, color="#1f77b4",
            label=rf"{len(levels)} levels of $\sum_j\cot(k\ell_j)=0$")
    ax.plot(lattice, np.ones_like(lattice), "|", markersize=14, color="#d62728",
            label=r"equally spaced $\pi n/L$")
    ax.set_ylim(-0.6, 1.6)
    ax.set_yticks([0.0, 1.0], ["graph", "lattice"])
    ax.set_xlim(0.0, 14.0)
    ax.set_xlabel(r"$k$ (the graph's ordinate)")
    ax.set_title("A jittered lattice: dictionary exact, density linear")
    gaps = np.diff(levels)
    ax.annotate(
        f"{len(levels)} graph levels below $k=14$ against "
        f"{len(lattice)} on the lattice;\n"
        f"graph gaps range {gaps.min():.2f} .. {gaps.max():.2f} "
        f"against a constant {np.pi / lengths.sum():.2f}",
        xy=(0.02, 0.04),
        xycoords="axes fraction",
        fontsize=8,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.2, axis="x")


def panel_statistics(ax) -> None:
    """The trap: the graph fits Wigner better than the zeros do."""
    report = graph_report(5, 120.0)
    lengths = star_edge_lengths(5, dictionary_exact=True)
    graph_levels = star_spectrum(lengths, 120.0)
    graph_spacings = level_spacings(graph_levels, unfold=True)
    zero_spacings = level_spacings(ZEROS, unfold=True)
    bins = np.linspace(0.0, 2.5, 26)
    ax.hist(zero_spacings, bins=bins, density=True, alpha=0.5, color="#1f77b4",
            label=rf"zeros: $r={report.zero_r_ratio:.3f}$, KS={report.zero_ks_statistic:.4f}")
    ax.hist(graph_spacings, bins=bins, density=True, alpha=0.5, color="#d62728",
            label=rf"graph: $r={report.r_ratio:.3f}$, KS={report.ks_statistic:.4f}")
    grid = np.linspace(0.01, 2.5, 200)
    ax.plot(grid, gue_spacing_pdf(grid), "k--", linewidth=1.4, label="Wigner surmise")
    ax.set_xlabel("unfolded spacing")
    ax.set_ylabel("density")
    ax.set_title("The graph is CLOSER to Wigner than the zeros are")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.25)


def panel_twin(ax) -> None:
    """Everything matches, because the twin's definition is the zeros."""
    report = twin_report(ZERO_COUNT)
    matrix = unitary_twin(ZEROS, seed=7)
    eigenvalues = np.sort(np.linalg.eigvalsh(matrix))
    ax.plot([ZEROS[0], ZEROS[-1]], [ZEROS[0], ZEROS[-1]], "k--", linewidth=1.0,
            label="identity")
    ax.plot(ZEROS, eigenvalues, "o", markersize=3, color="#d62728",
            label=rf"$U\,\mathrm{{diag}}(\gamma)\,U^\dagger$")
    ax.set_xlabel(r"$\gamma_n$ used to build the twin")
    ax.set_ylabel("computed eigenvalue")
    ax.set_title("The twin passes every test (and proves nothing)")
    ax.annotate(
        rf"$\max|E_n-\gamma_n| = {report.max_eigenvalue_error:.0e}$" + "\n"
        rf"$r = {report.r_ratio:.3f}$, KS $= {report.ks_statistic:.4f}$" + "\n"
        "unitarily equivalent to $\\mathrm{diag}(\\gamma)$",
        xy=(0.05, 0.62),
        xycoords="axes fraction",
        fontsize=8,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)


def panel_screen_table(ax) -> None:
    """The screening table, as a grid of pass/fail cells."""
    rows = screening_table(ZERO_COUNT)
    criteria = ["independent\ndefinition", "density\nclass", "statistics",
                "reality is a\ntheorem", "identification\nproved"]
    values: list[list[float]] = []
    for row in rows:
        cells = [
            row.independent_definition,
            row.density_class,
            row.statistics,
            row.reality_is_a_theorem,
            row.identification_proved,
        ]
        values.append([2.0 if cell is None else (1.0 if cell else 0.0) for cell in cells])

    matrix = np.array(values)
    ax.imshow(matrix, cmap=_cell_colour_map(), vmin=0.0, vmax=2.0, aspect="auto")
    for i, row in enumerate(rows):
        for j, cell in enumerate([
            row.independent_definition,
            row.density_class,
            row.statistics,
            row.reality_is_a_theorem,
            row.identification_proved,
        ]):
            mark = "n/a" if cell is None else ("yes" if cell else "no")
            ax.text(j, i, mark, ha="center", va="center", fontsize=9,
                    color="black" if cell is not None else "#444444")
    ax.set_xticks(range(len(criteria)))
    ax.set_xticklabels(criteria, fontsize=7)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([row.candidate.replace(" (", "\n(") for row in rows], fontsize=7)
    ax.set_title("Nothing passes: the twin aces\nthe numbers and fails the logic", fontsize=10)
    ax.set_xticks(np.arange(-0.5, len(criteria), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2.0)
    ax.tick_params(which="minor", length=0)


def _cell_colour_map():
    from matplotlib.colors import ListedColormap

    return ListedColormap(["#f4a3a3", "#a8d8a8", "#d8d8c0"])


def main() -> None:
    fig, axes = plt.subplots(2, 3, figsize=(18.0, 10.0))
    panel_counting(axes[0][0])
    panel_density(axes[0][1])
    panel_spectrum(axes[0][2])
    panel_statistics(axes[1][0])
    panel_twin(axes[1][1])
    panel_screen_table(axes[1][2])
    fig.suptitle(
        "Candidate operators for Hilbert-Polya: three new constructions, one "
        "unitary twin, and a screening procedure that cannot tell them apart.\n"
        "The prime-length graph realizes the Gutzwiller dictionary exactly and "
        "matches the zeros' statistics BETTER than the zeros do. RH is NOT proved.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = PROJECT_ROOT / "output" / "operator_candidates.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    report = graph_report(5, 120.0)
    print(report.summary())
    print()
    fit = power_law_fit(ZERO_COUNT)
    print(fit.summary())
    print()
    for row in density_table():
        print(f"  band [{row.lower:6.1f}, {row.upper:6.1f}): {row.count:3d} zeros, "
              f"dN/dT = {row.per_unit_height:.4f}")
    print()
    twin = twin_report(ZERO_COUNT)
    print(twin.summary())
    print()
    box = box_versus_zeros(ZERO_COUNT)
    print(box.summary())
    print()
    print("Screening table (yes/no; n/a = not measurable for this candidate):")
    for row in screening_table(ZERO_COUNT):
        print(
            f"  {row.candidate:34s} "
            f"indep={row.independent_definition!s:5s} dens={row.density_class!s:5s} "
            f"stats={str(row.statistics):5s} real={row.reality_is_a_theorem!s:5s} "
            f"ident={row.identification_proved!s:5s}"
        )
    print()
    print("Survivors (independent definition AND identification proved): none.")
    print("The Riemann hypothesis is not proved, and no candidate here comes close.")


if __name__ == "__main__":
    main()
