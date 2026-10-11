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
"""Simulate and plot the checkable claims from a popular account of Dirichlet
characters, Miller-Rabin and lattice cryptography.

Usage, from the repository root:

    python scripts/run_number_theory_claims_demo.py

Writes `output/number_theory_claims.png`, four panels:

    1. the prime race mod 4, with the real crossing at 26861 and the value 2946
       that this repository first recorded from memory and which is not a
       crossing at all;
    2. the logarithmic density of the lead, climbing slowly toward the
       Rubinstein-Sarnak limit of about 0.9959 -- shown as a trend, not as an
       equality, because the convergence is far too slow to reach it here;
    3. Miller-Rabin's liar fraction against the unconditional 1/4 bound, with
       n = 9 attaining it, and the 4^-k error decay;
    4. the good-basis / bad-basis asymmetry on one 2D lattice.

What is deliberately NOT plotted: Shor's algorithm, the surface code, quantum
hardware, or anything about the security of ML-KEM. Those are not simulable here,
and a figure that appeared to demonstrate them would be asserting a conclusion
its method cannot reach. See `docs/number_theory_claims.md`.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

# Re-exec from the repository root if invoked from elsewhere (frozen bootstrap
# so the runpy re-run does not recurse).
if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_NT_CLAIMS_BOOTSTRAPPED"
):
    os.environ["_NT_CLAIMS_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.lattice_reduction import (  # noqa: E402
    basis_quality,
    good_and_bad_basis,
    lattice_points,
    shortest_vector,
)
from riemann_framework.miller_rabin import (  # noqa: E402
    is_prime_unconditional,
    liar_fraction,
    max_liar_fraction,
)
from riemann_framework.prime_races import (  # noqa: E402
    FIRST_CROSSING_MOD_4,
    lead_logarithmic_density,
    prime_race,
)

RACE_LIMIT = 200_000
DENSITY_LIMITS = (10**3, 3 * 10**3, 10**4, 3 * 10**4, 10**5, 3 * 10**5, 10**6, 3 * 10**6)
LIAR_LIMIT = 3000
RUBINSTEIN_SARNAK_LIMIT = 0.9959
WRONG_CONSTANT = 2946


def panel_prime_race(ax) -> None:
    xs, diffs = prime_race(RACE_LIMIT, 4, 3, 1)
    xs_arr = np.array(xs)
    diffs_arr = np.array(diffs)
    ax.axhline(0.0, color="0.6", linewidth=0.8)
    ax.plot(xs_arr, diffs_arr, linewidth=1.0, color="#1f77b4")
    ax.axvline(
        FIRST_CROSSING_MOD_4,
        color="#d62728",
        linewidth=1.0,
        linestyle="--",
        label=f"first crossing at {FIRST_CROSSING_MOD_4}",
    )
    ax.axvline(
        WRONG_CONSTANT,
        color="#2ca02c",
        linewidth=1.0,
        linestyle=":",
        label=f"{WRONG_CONSTANT} (recorded wrongly; not a crossing)",
    )
    ax.set_xscale("log")
    ax.set_xlabel("x (log scale)")
    ax.set_ylabel(r"$\pi(x;4,3) - \pi(x;4,1)$")
    ax.set_title("The prime race mod 4: 3 mod 4 leads almost always")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.25)


def panel_log_density(ax) -> None:
    limits = list(DENSITY_LIMITS)
    densities_4 = [lead_logarithmic_density(n, 4, 3, 1) for n in limits]
    densities_3 = [lead_logarithmic_density(n, 3, 2, 1) for n in limits]
    ax.axhline(0.5, color="0.6", linewidth=0.8, label="no bias (1/2)")
    ax.axhline(
        RUBINSTEIN_SARNAK_LIMIT,
        color="#d62728",
        linewidth=1.0,
        linestyle="--",
        label=f"Rubinstein-Sarnak limit ~{RUBINSTEIN_SARNAK_LIMIT}",
    )
    ax.plot(limits, densities_4, "o-", label="mod 4: 3 mod 4 ahead", color="#1f77b4")
    ax.plot(limits, densities_3, "s-", label="mod 3: 2 mod 3 ahead", color="#ff7f0e")
    ax.set_xscale("log")
    ax.set_ylim(0.45, 1.02)
    ax.set_xlabel("x (log scale)")
    ax.set_ylabel("logarithmic density of the lead")
    ax.set_title("Chebyshev's bias, and how slowly it converges")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.25)


def panel_miller_rabin(ax) -> None:
    ns = []
    fractions = []
    for n in range(9, LIAR_LIMIT + 1, 2):
        if is_prime_unconditional(n):
            continue
        ns.append(n)
        fractions.append(liar_fraction(n))
    scan = max_liar_fraction(LIAR_LIMIT)
    ax.axhline(0.25, color="#d62728", linewidth=1.2, label="unconditional bound 1/4")
    ax.scatter(ns, fractions, s=4, alpha=0.35, color="#1f77b4", label="liar fraction")
    ax.scatter(
        [scan.worst_n],
        [scan.worst_fraction],
        s=60,
        color="#d62728",
        zorder=5,
        label=f"attained at n = {scan.worst_n}",
    )
    ax.set_xlabel("odd composite n")
    ax.set_ylabel("liars / (n - 1)")
    ax.set_title("Miller-Rabin: the 1/4 bound is attained, at n = 9")
    ax.set_ylim(0, 0.3)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.25)


def panel_lattice(ax) -> None:
    """One lattice, two bases -- with the bad basis made visible.

    The stretch is 3 rather than something dramatic so that both basis vectors
    fit in frame. A larger stretch would make the picture more striking and the
    bad vectors invisible, which is worse.
    """
    good, bad = good_and_bad_basis(3)
    points = lattice_points(good, 9)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.scatter(xs, ys, s=12, color="#1f77b4", label="lattice points")

    # The good basis parallelogram, drawn as a closed path.
    g0, g1 = good
    gsum = (g0[0] + g1[0], g0[1] + g1[1])
    path = [g0, gsum, g1, (0, 0)]
    ax.plot(
        [p[0] for p in path],
        [p[1] for p in path],
        color="#1f77b4",
        linewidth=1.6,
        label=f"good basis {g0}, {g1}",
    )

    b0, b1 = bad
    for vector, style in ((b0, "--"), (b1, ":")):
        ax.annotate(
            "",
            xy=vector,
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color="#ff7f0e", linewidth=1.6,
                            linestyle=style),
        )
    ax.plot([], [], color="#ff7f0e", linewidth=1.6, linestyle="--",
            label=f"bad basis {b0}, {b1}")

    sv = shortest_vector(bad)
    ax.annotate(
        "",
        xy=sv,
        xytext=(0, 0),
        arrowprops=dict(arrowstyle="->", color="#d62728", linewidth=2.2),
    )
    ax.text(sv[0] + 0.4, sv[1] + 0.4, f"shortest {sv}", color="#d62728", fontsize=8)
    ax.set_aspect("equal")
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_title("One lattice, two bases (dimension 2 only)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.25)


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    panel_prime_race(axes[0][0])
    panel_log_density(axes[0][1])
    panel_miller_rabin(axes[1][0])
    panel_lattice(axes[1][1])

    scan = max_liar_fraction(LIAR_LIMIT)
    fig.suptitle(
        "Checkable claims: prime races, Miller-Rabin, and 2D lattices\n"
        "Not shown, because not simulable here: Shor's algorithm, surface codes, "
        "quantum hardware, ML-KEM security",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    out = PROJECT_ROOT / "output" / "number_theory_claims.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    print(f"prime race crossing mod 4 : {FIRST_CROSSING_MOD_4}")
    print(f"log density mod 4 at 3e6  : {lead_logarithmic_density(3 * 10**6, 4, 3, 1):.5f}")
    print(f"  (literature limit ~{RUBINSTEIN_SARNAK_LIMIT}, approached slowly)")
    print(f"worst liar fraction       : {scan.summary()}")
    good, bad = good_and_bad_basis(20)
    print(f"good basis quality        : {basis_quality(*good).summary()}")
    print(f"bad  basis quality        : {basis_quality(*bad).summary()}")
    print()
    print("Nothing here is evidence about the Riemann hypothesis, and nothing")
    print("here is a statement about the security of any deployed system.")


if __name__ == "__main__":
    main()
