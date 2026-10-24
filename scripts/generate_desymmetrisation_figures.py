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
"""Generate the three figures of the desymmetrisation manuscript.

Usage, from the repository root:

    python scripts/generate_desymmetrisation_figures.py

Writes, into `output/`:

* `desymmetrisation_warning.png` -- the full-spectrum mean gap ratio against the number
  of unresolved sectors, one dot per simulated spectrum, with the class references and
  the contamination floor;
* `desymmetrisation_coverage.png` -- the measured coverage of the sector-count posterior
  at a nominal 95% interval, from a fresh simulation rather than from a table typed into
  the plotting code;
* `desymmetrisation_flow.png` -- sector populations under the double-bracket flow, for a
  state that commutes with the involution and one that does not.

Every number in these figures is computed here. That is deliberate: a figure drawn from
a hardcoded table cannot be wrong in a way the tests would notice, so it is not evidence.
The figure at `output/desymmetrisation.png` is the working demo of the same table at 300
seeds; this script is the manuscript's figure set.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_DESYMMETRISATION_FIGURES_BOOTSTRAPPED"
):
    os.environ["_DESYMMETRISATION_FIGURES_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.desymmetrisation import (  # noqa: E402
    CLASS_WINDOWS,
    R_GOE,
    R_GUE,
    R_POISSON,
    SEVERE_THRESHOLD,
    default_sector_count_model,
    superposition_spectrum,
)
from riemann_framework.dimension_shift_chaos import (  # noqa: E402
    build_dimension_shift_hamiltonian,
    sector_swap,
)
from riemann_framework.dynamical_desymmetrisation import (  # noqa: E402
    dynamical_desymmetrise,
)
from riemann_framework.statistics import mean_r_ratio  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "output"

#: Spectra per point in the warning figure, and the per-sector dimension.
WARNING_SEEDS = 300
WARNING_DIMENSION = 60

#: The sector counts shown in the manuscript's Fig. 2.
WARNING_COUNTS = (1, 2, 3, 6)

#: Spectra per row in the coverage figure, and the flow run length.
COVERAGE_DRAWS = 60
FLOW_BETA = 15.0
FLOW_STEPS = 3000


def _colours() -> dict[str, str]:
    return {"goe": "tab:orange", "gue": "tab:green"}


def plot_warning() -> Path:
    """Fig. 2: full-spectrum `mean r` against the number of unresolved sectors."""
    colours = _colours()
    markers = {"goe": "o", "gue": "s"}
    figure, axis = plt.subplots(figsize=(10, 6.5), constrained_layout=True)

    axis.axvspan(*CLASS_WINDOWS["poisson"], color="red", alpha=0.10,
                 label="Poisson window")

    for matrix_class in ("goe", "gue"):
        for count in WARNING_COUNTS:
            values = np.array(
                [
                    mean_r_ratio(
                        superposition_spectrum(
                            count, WARNING_DIMENSION, matrix_class, seed
                        ),
                        unfold=False,
                    )
                    for seed in range(WARNING_SEEDS)
                ]
            )
            offset = 0.16 if matrix_class == "gue" else -0.16
            jitter = np.random.default_rng(12345).normal(0.0, 0.012, values.size)
            axis.scatter(
                values + jitter,
                np.full(values.size, count + offset),
                s=9,
                alpha=0.18,
                color=colours[matrix_class],
                marker=markers[matrix_class],
                linewidths=0,
            )
            axis.scatter(
                [float(values.mean())],
                [count + offset],
                s=90,
                color=colours[matrix_class],
                marker=markers[matrix_class],
                edgecolors="black",
                linewidths=1.2,
                zorder=5,
            )
            axis.annotate(
                f"{values.mean():.3f}",
                xy=(float(values.mean()), count + offset),
                xytext=(8, 0),
                textcoords="offset points",
                fontsize=8,
                va="center",
            )

    axis.axvline(R_POISSON, color="red", linestyle="--", linewidth=1.2,
                 label=f"Poisson {R_POISSON}")
    axis.axvline(R_GOE, color="tab:orange", linestyle=":", linewidth=1.2,
                 label=f"GOE {R_GOE}")
    axis.axvline(R_GUE, color="tab:green", linestyle="-.", linewidth=1.2,
                 label=f"GUE {R_GUE}")
    axis.axvline(SEVERE_THRESHOLD, color="black", linestyle="-", linewidth=1.0,
                 alpha=0.6, label=f"contamination floor {SEVERE_THRESHOLD}")

    axis.set_yticks(list(WARNING_COUNTS))
    axis.set_yticklabels(
        [f"{count} sector" + ("s" if count > 1 else "") for count in WARNING_COUNTS]
    )
    axis.set_xlabel(r"full-spectrum $\langle r \rangle$")
    axis.set_ylabel("unresolved sectors")
    axis.set_title(
        "Full-spectrum $\\langle r \\rangle$ is a property of the superposition\n"
        f"({WARNING_SEEDS} spectra per point, {WARNING_DIMENSION} levels per sector)"
    )
    axis.grid(alpha=0.25)
    axis.legend(fontsize=8, loc="lower left")

    out = OUTPUT_DIR / "desymmetrisation_warning.png"
    figure.savefig(out, dpi=150)
    plt.close(figure)
    return out


def plot_coverage() -> tuple[Path, list[tuple[int | None, float, float]]]:
    """Fig. 3: measured coverage of the posterior, against the nominal level."""
    model = default_sector_count_model()
    rows = model.coverage(draws=COVERAGE_DRAWS)
    labels = [row.truth for row in rows]
    coverage = [row.coverage for row in rows]

    figure, axis = plt.subplots(figsize=(10, 6), constrained_layout=True)
    positions = np.arange(len(labels))
    bars = axis.bar(positions, coverage, color="steelblue", edgecolor="black",
                    linewidth=1.0, alpha=0.85, width=0.65)
    bars[-1].set_color("salmon")
    axis.axhline(0.95, color="red", linestyle="--", linewidth=1.6,
                 label="nominal 95% interval")
    for bar, value in zip(bars, coverage):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            min(value + 0.02, 1.06),
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    axis.set_xticks(positions)
    axis.set_xticklabels(
        ["1", "2", "3", "4", "5", "6", "≥6/poisson"][: len(labels)]
    )
    axis.set_ylim(0.0, 1.15)
    axis.set_xlabel("true number of unresolved sectors")
    axis.set_ylabel("measured coverage")
    axis.set_title(
        "Coverage of the sector-count posterior\n"
        f"nominal 95% interval, {COVERAGE_DRAWS} spectra per row"
    )
    axis.grid(alpha=0.25, axis="y")
    axis.legend(fontsize=9)
    axis.text(
        0.99,
        0.03,
        "the ≥6/poisson row is also the false-positive rate",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        style="italic",
        color="darkred",
    )

    out = OUTPUT_DIR / "desymmetrisation_coverage.png"
    figure.savefig(out, dpi=150)
    plt.close(figure)

    table: list[tuple[int | None, float, float]] = [
        (row.truth, row.coverage, row.posterior_probability) for row in rows
    ]
    return out, table


def plot_flow() -> Path:
    """Fig. 4: sector populations under the double-bracket flow, both kinds of start.

    The commuting start is a mixture with equal mass in the two sectors, built from
    random superpositions *within* each sector. It is therefore not an eigenstate of
    `H` -- the flow does real work on it -- and its populations are still constants of
    the motion, which is the point of panel (a).
    """
    dimension = 4
    hamiltonian = build_dimension_shift_hamiltonian(dimension, 1.0, "gue", seed=0)
    involution = sector_swap(dimension)
    size = 2 * dimension
    rng = np.random.default_rng(0)

    def sector_vector(sign: int) -> np.ndarray:
        projector = (np.eye(size) + sign * involution) / 2.0
        basis, singular, _ = np.linalg.svd(projector)
        rank = int(np.sum(singular > 1e-8))
        coefficients = rng.standard_normal(2) + 1j * rng.standard_normal(2)
        vector = basis[:, :2] @ coefficients
        return vector / np.linalg.norm(vector)

    commuting_state = np.zeros((size, size), dtype=complex)
    for sign in (+1, -1):
        vector = sector_vector(sign)
        commuting_state += 0.5 * np.outer(vector, vector.conj())

    def sector_state(sign: int, index: int) -> np.ndarray:
        projector = (np.eye(size) + sign * involution) / 2.0
        _, basis = np.linalg.eigh(
            projector @ hamiltonian @ projector + 1e6 * (np.eye(size) - projector)
        )
        return basis[:, index]

    vector = (sector_state(+1, 0) + sector_state(-1, 0)) / np.sqrt(2.0)
    cross = np.outer(vector, vector.conj())

    commuting = dynamical_desymmetrise(
        hamiltonian, involution, commuting_state, beta=FLOW_BETA, steps=FLOW_STEPS
    )
    selecting = dynamical_desymmetrise(
        hamiltonian, involution, cross, beta=FLOW_BETA, steps=FLOW_STEPS
    )

    figure, (left, right) = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)

    for axis, report, title in (
        (left, commuting, "(a) commuting start: populations preserved"),
        (right, selecting, "(b) cross-sector start: one sector selected"),
    ):
        axis.plot(report.betas, report.sector_populations[:, 0], color="tab:blue",
                  linewidth=2.0, label="+ sector")
        axis.plot(report.betas, report.sector_populations[:, 1], color="tab:red",
                  linestyle="--", linewidth=2.0, label="− sector")
        axis.set_xlabel(r"$\beta$ (flow time)")
        axis.set_ylabel(r"$\mathrm{tr}(P_\pm \rho)$")
        axis.set_ylim(-0.02, 1.05)
        axis.grid(alpha=0.25)
        axis.legend(fontsize=9, loc="center right")
        axis.set_title(title, fontsize=10)

    figure.suptitle(
        r"sector populations under $d\rho/d\beta = [[\rho, H], \rho]$"
        "\n"
        f"spectrum of rho drifts by {commuting.spectrum_drift:.0e}; the Hamiltonian never evolves",
        fontsize=10,
    )
    out = OUTPUT_DIR / "desymmetrisation_flow.png"
    figure.savefig(out, dpi=150)
    plt.close(figure)
    return out


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("generating the manuscript figures from measured data")
    print()

    warning = plot_warning()
    print(f"  wrote {warning.relative_to(PROJECT_ROOT)}")

    coverage, table = plot_coverage()
    print(f"  wrote {coverage.relative_to(PROJECT_ROOT)}")
    for truth, value, probability in table:
        label = ">=6/poisson" if truth is None else str(truth)
        print(f"    true {label:>10}: coverage {value:.2f}, P(true) {probability:.2f}")

    flow = plot_flow()
    print(f"  wrote {flow.relative_to(PROJECT_ROOT)}")
    print()
    print("No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
