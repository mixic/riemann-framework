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
"""Simulate the two new pieces of the quantum-chaos picture: imaginary time and
prime orbits.

Usage, from the repository root:

    python scripts/run_quantum_chaos_claims_demo.py

Writes `output/quantum_chaos_claims.png`, four panels:

    1. real time diverges, imaginary time converges -- the same operator, two
       rotations of the time;
    2. the exponentially growing density of states that forces a Hagedorn
       temperature at beta = 1;
    3. the prime orbit theorem with topological entropy h = 1: the count matches
       the Anosov asymptotic;
    4. the error term, where the dictionary stops: the truncated zero sum
       oscillates, and resolving psi(X) needs ~N(X) zeros.

The primon gas itself, and GUE statistics, are already simulated elsewhere in this
repository (`primon_gas.py`, `quantum_chaos.py`) and are not repeated here.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_QC_CLAIMS_BOOTSTRAPPED"
):
    os.environ["_QC_CLAIMS_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mpmath as mp  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.imaginary_time import (  # noqa: E402
    density_ratio,
    oscillatory_growth,
    state_count,
    thermal_convergence,
)
from riemann_framework.prime_orbits import (  # noqa: E402
    orbit_table,
    reconstruction_report,
    zeros_needed_to_resolve,
)

TIMES = [500, 1000, 2000, 4000, 8000, 16000, 32000, 64000]


def panel_real_vs_imaginary(ax) -> None:
    oscillatory = oscillatory_growth(13.0, TIMES)
    thermal = thermal_convergence(2.0, TIMES)
    ax.loglog(TIMES, oscillatory, "o-", color="#d62728",
              label=r"real time: $|\sum_{n\leq N} n^{-it}|/N$")
    ax.loglog(TIMES, thermal, "s-", color="#1f77b4",
              label=r"imaginary time: $|\sum_{n\leq N} n^{-\beta}-\zeta(\beta)|$")
    ax.set_xlabel("N (log scale)")
    ax.set_ylabel("magnitude (log scale)")
    ax.set_title("Time rotated, operator unchanged: one diverges, one converges")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, which="both")


def panel_hagedorn(ax) -> None:
    energies = np.arange(1, 41)
    counts = [state_count(int(E)) for E in energies]
    ax.semilogy(energies, counts, "o-", color="#1f77b4", markersize=3,
                label=r"states below $E$: $\lfloor e^E \rfloor$")
    ratios = [density_ratio(int(E)) for E in energies[3:]]
    twin = ax.twinx()
    twin.plot(energies[3:], ratios, "-", color="#2ca02c", linewidth=1.4,
              label=r"ratio to $E-1$")
    twin.axhline(float(mp.e), color="#2ca02c", linestyle="--", linewidth=0.9)
    twin.set_ylim(1.0, 3.0)
    twin.set_ylabel("ratio (settles at e)", color="#2ca02c", fontsize=9)
    ax.set_xlabel("energy E")
    ax.set_ylabel(r"state count $\lfloor e^E \rfloor$ (log)")
    ax.set_title(r"Density of states $\sim e^E$ $\Rightarrow$ Hagedorn, not BEC")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25, which="both")


def panel_orbit_counting(ax) -> None:
    Ts = [5.0, 7.0, 9.0, 11.0, 13.0, 15.0]
    rows = orbit_table(Ts)
    counts = [r.primitive_count for r in rows]
    asym = [r.asymptotic for r in rows]
    ax.loglog(Ts, counts, "o-", color="#1f77b4", label=r"$\pi(e^T)$ (exact sieve)")
    ax.loglog(Ts, asym, "--", color="#ff7f0e", label=r"$e^{hT}/(hT)$, $h=1$")
    ax.set_xlabel("T  (orbit period; primes have period $\\log p$)")
    ax.set_ylabel("count (log scale)")
    ax.set_title("Prime orbit theorem with entropy 1: the counting matches")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, which="both")
    for row in rows[::2]:
        ax.annotate(f"{row.ratio:.3f}", (row.T, row.primitive_count),
                    textcoords="offset points", xytext=(4, -10), fontsize=7,
                    color="#1f77b4")


def panel_error_term(ax) -> None:
    """The panel that says where the dictionary stops."""
    for X, colour in ((1000, "#1f77b4"), (10000, "#ff7f0e"), (100000, "#2ca02c")):
        report = reconstruction_report(X, [1, 2, 3, 5, 8, 13, 21, 34, 55, 89])
        ax.semilogy(report.zero_counts, report.errors, "o-", color=colour,
                    label=f"X = {X:,}  (needs {report.zeros_needed:,.0f} zeros)")
    ax.set_xlabel("K, zeros used in the explicit formula")
    ax.set_ylabel(r"$|\psi_K(X) - \psi(X)|$  (log)")
    ax.set_title("The error term oscillates: no trend, and K is far below N(X)")
    ax.legend(fontsize=7, loc="lower left")
    ax.grid(alpha=0.25, which="both")


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    panel_real_vs_imaginary(axes[0][0])
    panel_hagedorn(axes[0][1])
    panel_orbit_counting(axes[1][0])
    panel_error_term(axes[1][1])
    fig.suptitle(
        "Quantum-chaos claims: imaginary time, the Hagedorn temperature, and the "
        "prime-orbit dictionary.\n"
        "The counting correspondence is exact at first order; the error term is a "
        "sum over the zeta zeros and does not become tractable.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = PROJECT_ROOT / "output" / "quantum_chaos_claims.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    print("real time  |sum|/N :", [round(v, 4) for v in oscillatory_growth(13.0, TIMES)])
    print("imaginary  errors  :", ["%.1e" % v for v in thermal_convergence(2.0, TIMES)])
    print()
    for row in orbit_table([6.0, 12.0, 15.0]):
        print("  " + row.summary())
    print()
    for X in (1000, 100000):
        print("  " + reconstruction_report(X).summary()[:120])
    print(f"  zeros needed at X = 10^12: {zeros_needed_to_resolve(10**12):,.0f}")
    print()
    print("The primon gas and GUE statistics are already simulated in primon_gas.py")
    print("and quantum_chaos.py, so they are not repeated here.")


if __name__ == "__main__":
    main()
