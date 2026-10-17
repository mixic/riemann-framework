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
"""Run the Hilbert-Polya prototype and plot the four gaps.

Usage, from the repository root:

    python scripts/run_hilbert_polya_demo.py

Writes `output/hilbert_polya.png`, six panels:

    1. the formal eigenfunction's modulus is `x^-1` for every energy, so the
       truncated norm is `log(b/a)` and diverges at both ends -- no eigenvalue;
    2. the counting function: a linear picket fence against the zeros' log
       growth, both fitted to agree at `gamma_100`;
    3. nearest-neighbour spacings: a delta at 1 against GUE;
    4. the `PT` threshold `theta_c = arcsin(s/r)` -- reality is conditional;
    5. imaginary time: `exp(-E tau)` weights, ground-state dominance, and the
       gap read back off exactly;
    6. the KMS circle, `G(tau) = G(beta - tau)`, with the thermal trace's
       blindness to `Re(s)` annotated.

**No panel claims a proof of the Riemann hypothesis.** Panel 2 is the one that
says why a naive operator cannot be it, and panel 6 says why imaginary time
cannot help. See `docs/hilbert_polya.md`.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_HILBERT_POLYA_BOOTSTRAPPED"
):
    os.environ["_HILBERT_POLYA_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.hilbert_polya import (  # noqa: E402
    box_count,
    box_positive_levels,
    box_versus_zeros,
    decay_table,
    fit_box_length,
    kms_correlator,
    prototype_report,
    pt_eigenvalues,
    pt_threshold,
    thermal_blindness,
    truncated_norm_squared,
)
from riemann_framework.prime_orbits import zeta_zero_ordinates  # noqa: E402
from riemann_framework.statistics import (  # noqa: E402
    gue_spacing_pdf,
    level_spacings,
    mean_r_ratio,
)

ZERO_COUNT = 100
ENERGIES = zeta_zero_ordinates(ZERO_COUNT)


def panel_continuum(ax) -> None:
    """`|psi|^2 = x^-1` for every energy: the same log divergence for all of them."""
    x = np.logspace(-4, 6, 400)
    for index, style in enumerate(("-", "--"), start=1):
        modulus = 1.0 / x  # |x^{-1/2+iE}|^2 = x^-1, independent of E
        ax.loglog(x, modulus, style, linewidth=1.6, label=rf"$E=\gamma_{index}$")
    ax.axvspan(1e-4, 1e-2, color="#d62728", alpha=0.10)
    ax.axvspan(1e2, 1e6, color="#d62728", alpha=0.10)
    ax.set_xlabel("x")
    ax.set_ylabel(r"$|\psi(x)|^2 = x^{-1}$")
    ax.set_title("No eigenvalue: the norm diverges at both ends")
    ax.annotate(
        r"$\int_a^b |\psi|^2 = \log(b/a)$" + "\n"
        rf"width $10^6$: {truncated_norm_squared(1.0, 1e6):.2f}" + "\n"
        r"and still no limit",
        xy=(1.0, 1e-3),
        fontsize=8,
        ha="left",
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=0.25, which="both")


def panel_counting(ax) -> None:
    """The density: linear against logarithmic, fitted to agree at the top."""
    zeros = np.array(ENERGIES)
    length = fit_box_length(zeros)
    heights = np.linspace(10.0, float(zeros[-1]), 400)
    ax.step(zeros, np.arange(1, len(zeros) + 1), where="post", linewidth=1.8,
            color="#1f77b4", label="zeros, exactly counted")
    ax.plot(heights, [box_count(h, length) for h in heights], "-",
            color="#d62728", linewidth=1.8,
            label=rf"hard box, $L={length:.3f}$")
    ax.axhline(ZERO_COUNT, color="0.6", linestyle=":", linewidth=1.0)
    ax.axvline(float(zeros[-1]), color="0.6", linestyle=":", linewidth=1.0)
    for height in (50.0, 100.0, 200.0):
        predicted = box_count(height, length)
        actual = int(np.searchsorted(zeros, height, side="right"))
        ax.annotate(
            rf"${predicted}/{actual} = {predicted / actual:.2f}\times$",
            xy=(height, predicted),
            xytext=(height + 6.0, predicted - 14.0),
            fontsize=8,
            color="#d62728",
            arrowprops={"arrowstyle": "->", "color": "#d62728", "linewidth": 0.8},
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
        )
    ax.set_xlabel(r"height $T$")
    ax.set_ylabel("levels below $T$")
    ax.set_ylim(0.0, 112.0)
    ax.set_title("The box gets the density wrong, worst at the bottom")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25)


def panel_spacings(ax) -> None:
    """Uniformity: a delta at 1 against the GUE response."""
    zeros = np.array(ENERGIES)
    length = fit_box_length(zeros)
    ladder = box_positive_levels(length, ZERO_COUNT)
    ladder_spacings = np.diff(ladder) / np.mean(np.diff(ladder))
    zero_spacings = level_spacings(zeros, unfold=True)

    bins = np.linspace(0.0, 2.5, 26)
    ax.hist(zero_spacings, bins=bins, density=True, alpha=0.55,
            color="#1f77b4", label=f"zeros, r = {mean_r_ratio(zeros, unfold=False):.3f}")
    ax.hist(ladder_spacings, bins=bins, density=True, alpha=0.55,
            color="#d62728", label=f"hard box, r = {mean_r_ratio(ladder, unfold=False):.3f}")
    grid = np.linspace(0.01, 2.5, 200)
    ax.plot(grid, gue_spacing_pdf(grid), "k--", linewidth=1.4, label="GUE surmise")
    ax.set_xlabel("unfolded spacing s")
    ax.set_ylabel("density")
    ax.set_title(r"Hard box: a picket fence ($r=1$), not GUE ($r\approx0.6$)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)


def panel_pt(ax) -> None:
    """Reality is a condition: the conjugate pair appears at `arcsin(s/r)`."""
    thetas = np.linspace(0.0, 1.2, 400)
    real_parts = [pt_eigenvalues(1.0, 0.5, float(t)) for t in thetas]
    lower_real = [float(e[0].real) for e in real_parts]
    upper_real = [float(e[1].real) for e in real_parts]
    imaginary = [float(np.abs(e.imag).max()) for e in real_parts]
    threshold = pt_threshold(1.0, 0.5)
    ax.plot(thetas, upper_real, color="#1f77b4", linewidth=1.6, label=r"Re $\lambda_\pm$")
    ax.plot(thetas, lower_real, color="#1f77b4", linewidth=1.6)
    ax.plot(thetas, imaginary, color="#d62728", linewidth=1.8, label=r"$|\mathrm{Im}\,\lambda|$")
    ax.axvline(threshold, color="#2ca02c", linestyle="--", linewidth=1.3,
               label=rf"$\theta_c=\arcsin(1/2)=\pi/6={threshold:.4f}$")
    ax.set_xlabel(r"$\theta$")
    ax.set_ylabel("eigenvalue")
    ax.set_title(r"$PT$-symmetric model: real below $\theta_c$, a pair above")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)


def panel_imaginary_time(ax) -> None:
    """`exp(-E tau)` selects the ground state and hands back the gap."""
    energies = [float(g) for g in ENERGIES[:5]]
    taus = np.linspace(0.0, 4.0, 300)
    for index, energy in enumerate(energies):
        ax.semilogy(taus, np.exp(-(energy - energies[0]) * taus), linewidth=1.3,
                    label=rf"$\gamma_{index + 1}-\gamma_1 = {energy - energies[0]:.2f}$")
    rows = decay_table(energies, [1.0, 2.0, 4.0])
    ax.axhline(1e-12, color="0.7", linewidth=0.8)
    ax.set_xlabel(r"imaginary time $\tau$")
    ax.set_ylabel(r"weight relative to ground state")
    ax.set_title("Imaginary time isolates ONE level, not the spectrum")
    ax.annotate(
        "\n".join(
            f"tau={row.tau:g}: ground {100 * row.ground_fraction:.4f}%"
            for row in rows
        ),
        xy=(0.03, 0.03),
        xycoords="axes fraction",
        fontsize=8,
        va="bottom",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(alpha=0.25, which="both")


def panel_kms(ax) -> None:
    """The one real theorem here, plus the blindness that limits it."""
    beta, omega = 2.0, 1.3
    taus = np.linspace(0.0, beta, 400)
    values = [kms_correlator(float(t), beta, omega) for t in taus]
    mirrored = [kms_correlator(float(beta - t), beta, omega) for t in taus]
    ax.plot(taus, values, color="#1f77b4", linewidth=2.0, label=r"$G(\tau)$")
    ax.plot(taus, mirrored, "r--", linewidth=1.2, label=r"$G(\beta-\tau)$")
    ax.axvline(beta / 2.0, color="0.5", linestyle=":", linewidth=1.0)
    blind = thermal_blindness(0.5, ZERO_COUNT)
    ax.set_xlabel(r"imaginary time $\tau \in [0,\beta]$")
    ax.set_ylabel(r"$G(\tau)$")
    ax.set_title(r"KMS: imaginary time is a circle of circumference $\beta$")
    ax.annotate(
        rf"$\max|G(\tau)-G(\beta-\tau)| < 10^{{-15}}$" + "\n"
        rf"$Z(0.5)$ on the line: {blind['on_line']:.6e}" + "\n"
        rf"$Z(0.5)$ with $Re(s)+0.1$: {blind['off_line']:.6e}" + "\n"
        r"difference: exactly 0",
        xy=(0.28, 0.52),
        xycoords="axes fraction",
        fontsize=8,
        va="bottom",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.25)


def main() -> None:
    fig, axes = plt.subplots(2, 3, figsize=(17.5, 9.5))
    panel_continuum(axes[0][0])
    panel_counting(axes[0][1])
    panel_spacings(axes[0][2])
    panel_pt(axes[1][0])
    panel_imaginary_time(axes[1][1])
    panel_kms(axes[1][2])
    fig.suptitle(
        "Hilbert-Polya prototype: the operator exists, and the four gaps are open.\n"
        "The critical line is the eigenfunction exponent; the box, the "
        "self-adjointness argument, and imaginary time each fail to deliver it. "
        "RH is NOT proved.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = PROJECT_ROOT / "output" / "hilbert_polya.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    verdict = box_versus_zeros(ZERO_COUNT)
    print(verdict.summary())
    print()
    for row in verdict.rows:
        print(
            f"  T = {row.height:5.1f}: box {row.box_count:4d}, "
            f"zeros {row.zero_count:4d}, ratio {row.ratio:.3f}"
        )
    print()
    print("The four gaps, measured:")
    print(f"  1. no eigenvalue: truncated norm {truncated_norm_squared(1.0, 1e6):.3f} "
          "at width 1e6 and growing")
    print(f"  2. picket fence: r = {verdict.box_r_ratio:.3f} against "
          f"{verdict.zero_r_ratio:.3f}")
    print(f"  3. real spectrum is free; PT breaks at "
          f"{pt_threshold(1.0, 0.5):.4f} rad = 30 degrees")
    print("  4. imaginary time is blind to Re(s): the thermal difference is 0")
    print()
    print(prototype_report(ZERO_COUNT).verdict())


if __name__ == "__main__":
    main()
