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
"""Graph the Riemann hypothesis for curves over finite fields.

Usage, from the repository root:

    python scripts/run_finite_field_curves_demo.py

Writes `output/finite_field_curves.png`, four panels:

    1. the finite-field "sphere": the projective line P^1(F_q) as q+1 points on a
       circle, coloured by Frobenius orbit (the GF(p)-conjugacy classes);
    2. the rational points of an elliptic curve over F_p, showing the
       x -> -x pairing that halves the affine count;
    3. the Hasse bound |a_p| <= 2 sqrt(p) for every curve over each small p;
    4. the zeros of Z(C, T): the alpha_i divided by sqrt(q), sitting on the unit
       circle -- which IS the Riemann hypothesis for that curve, exactly.

Panel 4 is the point of the module. Those points lie on the circle because
alpha_i alpha_i-bar = q, and that is a theorem, certified here by integer
arithmetic for each curve drawn.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_FFC_BOOTSTRAPPED"
):
    os.environ["_FFC_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.finite_field_curves import (  # noqa: E402
    FiniteField,
    alpha_pair,
    certify_elliptic,
    certify_genus2,
    count_projective_points,
    elliptic_rhs,
    sweep_elliptic,
)

CURVE = (0, 1, 5)  # y^2 = x^3 + 1 over F_5


def panel_sphere(ax) -> None:
    """P^1(F_q): the q elements of the field plus the point at infinity.

    Drawn on a circle because that is the standard picture of the projective
    line, and because it makes the Frobenius orbits visible as chords: an element
    and its GF(p)-conjugates sit at the same "height" under the p-power map.
    """
    field = FiniteField(3, 2)
    orbits = field.frobenius_orbits()
    label_of = {}
    for index, orbit in enumerate(orbits):
        for element in orbit:
            label_of[element] = index

    total = field.size + 1  # plus the point at infinity
    angles = np.linspace(0, 2 * np.pi, total, endpoint=False)
    colours = plt.cm.tab10(np.linspace(0, 1, max(len(orbits) + 1, 2)))

    for index, angle in enumerate(angles[:-1]):
        element = index
        colour = colours[label_of[element] % len(colours)]
        ax.plot(np.cos(angle), np.sin(angle), "o", color=colour, markersize=9)
        ax.annotate(str(element), (np.cos(angle) * 1.12, np.sin(angle) * 1.12),
                    ha="center", va="center", fontsize=7)
    ax.plot(np.cos(angles[-1]), np.sin(angles[-1]), "*", color="black", markersize=16)
    ax.annotate(r"$\infty$", (np.cos(angles[-1]) * 1.18, np.sin(angles[-1]) * 1.18),
                ha="center", va="center", fontsize=9)

    # Chords joining each element to its Frobenius image.
    for element in range(field.size):
        image = field.frobenius(element)
        if image != element:
            a, b = angles[element], angles[image]
            ax.plot([np.cos(a), np.cos(b)], [np.sin(a), np.sin(b)],
                    color="0.6", linewidth=0.8, zorder=0)

    ax.set_aspect("equal")
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.axis("off")
    ax.set_title(
        f"The finite-field sphere: $P^1(F_9)$, {total} points\n"
        f"chords join $x$ to $x^3$; colour = Frobenius orbit",
        fontsize=10,
    )


def panel_curve_points(ax) -> None:
    a, b, p = CURVE
    field = FiniteField(p, 1)
    counts = field.square_root_counts()
    xs, ys = [], []
    for x in range(p):
        value = (pow(x, 3, p) + a * x + b) % p
        for y in range(p):
            if (y * y) % p == value:
                xs.append(x)
                ys.append(y)
    ax.scatter(xs, ys, s=70, color="#1f77b4", zorder=3,
               label=f"{len(xs)} affine points")
    for x in range(p):
        column = sorted(y for xx, y in zip(xs, ys) if xx == x)
        for y in column:
            if y < p - y or (y == 0 and p > 1):
                pass
        if len(column) == 2:
            ax.plot([x, x], [column[0], column[1]], color="#ff7f0e", linewidth=1.2,
                    zorder=2)
    ax.plot([], [], color="#ff7f0e", linewidth=1.2, label=r"$x \to -x$ pairing")
    ax.scatter([], [], marker="*", s=140, color="black",
               label=r"+ the point at $\infty$")
    ax.set_xticks(range(p))
    ax.set_yticks(range(p))
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        rf"$y^2 = x^3 + {a}x + {b}$ over $F_{p}$: "
        rf"$N_1 = {count_projective_points(elliptic_rhs(a, b), field)}$ = "
        rf"$p + 1 - a_p$",
        fontsize=10,
    )
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25)


def panel_hasse(ax) -> None:
    for p, colour in ((5, "#1f77b4"), (7, "#ff7f0e"), (11, "#2ca02c"), (13, "#d62728")):
        traces = sorted({c.trace for c in sweep_elliptic(p)})
        ax.plot([p] * len(traces), traces, "o", color=colour, markersize=5, alpha=0.7)
    ps = np.linspace(3.5, 14.5, 200)
    ax.plot(ps, 2 * np.sqrt(ps), "--", color="black", linewidth=1.2,
            label=r"$\pm 2\sqrt{p}$")
    ax.plot(ps, -2 * np.sqrt(ps), "--", color="black", linewidth=1.2)
    ax.axhline(0, color="0.8", linewidth=0.8)
    ax.set_xlabel("p")
    ax.set_ylabel(r"$a_p = p + 1 - N_1$")
    ax.set_title("Hasse's bound, measured: every curve, every trace inside the envelope",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)


def panel_zeros(ax) -> None:
    """The alpha_i / sqrt(q), which is the Riemann hypothesis as a picture."""
    theta = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), "-", color="0.6", linewidth=1.0,
            label=r"$|T| = q^{-1/2}$")

    a, b, p = CURVE
    certificate = certify_elliptic(a, b, p)
    for alpha in alpha_pair(certificate.trace, p):
        scaled = alpha / np.sqrt(p)
        ax.plot(scaled.real, scaled.imag, "o", color="#1f77b4", markersize=11,
                label=rf"$\alpha_i/\sqrt{{q}}$ for $y^2 = x^3+{a}x+{b}$, $F_{p}$")

    genus2 = certify_genus2([2, 1, 0, 1, 0, 1], 3)
    if genus2.certified and genus2.roots is not None:
        for w in genus2.roots:
            # w = alpha + q/alpha with |alpha| = sqrt(q) => alpha solves
            # alpha^2 - w alpha + q = 0, so alpha/sqrt(q) = (w +- sqrt(w^2-4q))/(2 sqrt q).
            disc = complex(w * w - 4 * 3) ** 0.5
            for sign in (1, -1):
                scaled = (w + sign * disc) / (2 * np.sqrt(3))
                ax.plot(scaled.real, scaled.imag, "s", color="#ff7f0e", markersize=9)

    ax.plot([], [], "s", color="#ff7f0e", markersize=9,
            label="genus 2 over $F_3$ (four $\\alpha_i$)")
    ax.set_aspect("equal")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axhline(0, color="0.85", linewidth=0.7)
    ax.axvline(0, color="0.85", linewidth=0.7)
    ax.set_xlabel(r"$\mathrm{Re}(\alpha/\sqrt{q})$")
    ax.set_ylabel(r"$\mathrm{Im}(\alpha/\sqrt{q})$")
    ax.set_title(r"The zeros of $Z(C,T)$: $|\alpha_i| = \sqrt{q}$ exactly", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.25)


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    panel_sphere(axes[0][0])
    panel_curve_points(axes[0][1])
    panel_hasse(axes[1][0])
    panel_zeros(axes[1][1])
    fig.suptitle(
        "The Riemann hypothesis for curves over finite fields: the one case where "
        "it is a theorem, and a computation is a proof.\n"
        "Each curve is certified by exact integer arithmetic. That certifies the "
        "curve; it does not prove Weil's theorem, and it does not transfer to Q.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = PROJECT_ROOT / "output" / "finite_field_curves.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    a, b, p = CURVE
    print("  " + certify_elliptic(a, b, p).summary())
    print("  " + certify_genus2([2, 1, 0, 1, 0, 1], 3).summary())
    print()
    for p in (5, 7, 11, 13, 17, 19):
        certificates = sweep_elliptic(p)
        print(f"  F_{p:>2}: {len(certificates):>4} curves certified, "
              f"{sum(1 for c in certificates if not c.hasse)} violations of Hasse")


if __name__ == "__main__":
    main()
