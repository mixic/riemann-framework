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
"""Simulate `H_t = exp(-t d^2/dz^2) H_0` and plot what can and cannot be seen.

Usage, from the repository root:

    python scripts/run_de_bruijn_newman_demo.py

Writes `output/de_bruijn_newman.png`, four panels:

    1. `H_0(z)` from the quadrature against `(1/8) xi(1/2 + i z/2)` computed
       independently, with the zeros marked;
    2. the quadrature zeros against the exact `2 gamma_k`, on a log scale -- the
       numerical limit of the method, measured;
    3. a control whose constant is known exactly, `p(z) = z^2 + c` with
       `Lambda = c/2`, where an exit from the real axis *is* in range;
    4. the truncated dynamics equation against the numerically differentiated
       zero positions -- the missing tail.

**The panel that is deliberately absent is a verification of `Lambda <= 0`.** It
is equivalent to the Riemann hypothesis and no computation establishes it. See
`docs/de_bruijn_newman.md`.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_DBN_BOOTSTRAPPED"
):
    os.environ["_DBN_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.de_bruijn_newman import (  # noqa: E402
    LAMBDA_BOUNDS,
    H,
    H_reference,
    locate_zeros,
    toy_constant,
    toy_zeros,
    zero_accuracy_table,
    zero_velocity_numeric,
    zero_velocity_truncated,
)

Z_MAX = 70.0


def panel_identity(ax) -> None:
    """Log scale, because the whole point is invisible on a linear one.

    `H_0` decays from 0.0625 at the origin to ~1e-5 by the ninth zero, and every
    zero is a sign change at that scale. Plotted linearly the curve looks like a
    smooth decay to nothing and the zeros do not appear to be crossings at all --
    which is what the first version of this panel looked like.
    """
    zs = np.linspace(0.01, Z_MAX, 600)
    quad = np.abs(H(0.0, zs))
    ref = np.array([abs(H_reference(float(z)).real) for z in zs])
    ax.semilogy(zs, np.maximum(quad, 1e-14), linewidth=1.4,
                label=r"quadrature $\int_0^\infty \Phi(u)\cos(zu)\,du$")
    ax.semilogy(zs, np.maximum(ref, 1e-14), "--", linewidth=1.2,
                label=r"$(1/8)\xi(1/2+iz/2)$")
    zeros = locate_zeros(0.0, z_max=Z_MAX, grid=20000)
    for index, zero in enumerate(zeros, start=1):
        ax.axvline(zero, color="#d62728", linewidth=0.9, alpha=0.55)
    ax.plot([], [], color="#d62728", linewidth=0.9,
            label=f"zeros of $H_0$ (n={len(zeros)})")
    ax.set_ylim(1e-7, 1e-1)
    ax.set_xlabel("z")
    ax.set_ylabel(r"$|H_0(z)|$  (log scale)")
    ax.set_title("Two independent routes to $H_0$, and its zeros")
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=0.25, which="both")


def panel_accuracy(ax) -> None:
    rows = zero_accuracy_table(9)
    ks = [r.index for r in rows]
    errs = [r.relative_error for r in rows]
    ax.semilogy(ks, errs, "o-", color="#1f77b4", label="quadrature vs exact")
    ax.axhline(1e-6, color="#2ca02c", linestyle="--", linewidth=1.0,
               label="1e-6: below this, positions are trustworthy")
    ax.set_xlabel(r"zero index $k$  (exact position $2\gamma_k$)")
    ax.set_ylabel("relative error")
    ax.set_title("The numerical limit, measured: drift grows with height")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, which="both")


def panel_toy(ax) -> None:
    c = 1.0
    lam = toy_constant(c)
    ts = np.linspace(0.0, 0.9, 400)
    real_part, imag_part = [], []
    for t in ts:
        z0, _ = toy_zeros(c, t)
        if isinstance(z0, complex):
            real_part.append(0.0)
            imag_part.append(abs(z0.imag))
        else:
            real_part.append(abs(z0))
            imag_part.append(0.0)
    ax.plot(ts, imag_part, linewidth=1.8, color="#d62728", label="|Im zero|")
    ax.plot(ts, real_part, linewidth=1.8, color="#1f77b4", label="|Re zero|")
    ax.axvline(lam, color="#2ca02c", linestyle="--", linewidth=1.2,
               label=f"Lambda = c/2 = {lam}")
    ax.set_xlabel("t")
    ax.set_ylabel("zero position")
    ax.set_title(r"Control: $p(z)=z^2+c$ has $\Lambda=c/2$, and the exit is visible")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)


def panel_dynamics(ax) -> None:
    zeros = locate_zeros(0.0, z_max=Z_MAX, grid=20000)
    numeric = zero_velocity_numeric(0.0, z_max=Z_MAX)
    truncated = zero_velocity_truncated(zeros)
    ks = np.arange(1, len(zeros) + 1)
    ax.axhline(0.0, color="0.7", linewidth=0.7)
    ax.plot(ks, numeric, "o-", color="#1f77b4", label=r"numeric $dx_k/dt$")
    ax.plot(ks, truncated, "s--", color="#ff7f0e",
            label=r"truncated $2\sum_{j\neq k}1/(x_k-x_j)$")
    ax.set_xlabel("zero index k")
    ax.set_ylabel("velocity")
    ax.set_title("Truncating the dynamics misses the tail (equation does not truncate)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    panel_identity(axes[0][0])
    panel_accuracy(axes[0][1])
    panel_toy(axes[1][0])
    panel_dynamics(axes[1][1])
    fig.suptitle(
        "de Bruijn-Newman: RH <=> Lambda <= 0. Lambda >= 0 (Rodgers-Tao) and "
        "Lambda <= 0.2 (Polymath15).\n"
        "Lambda <= 0 CANNOT be verified numerically -- it IS the Riemann "
        "hypothesis. No panel here claims it.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = PROJECT_ROOT / "output" / "de_bruijn_newman.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    print(f"Lambda in [{LAMBDA_BOUNDS['lower']}, {LAMBDA_BOUNDS['upper']}]; "
          f"{LAMBDA_BOUNDS['equivalence']}")
    rows = zero_accuracy_table(9)
    print(f"zero 1 error {rows[0].relative_error:.2e}   "
          f"zero 9 error {rows[8].relative_error:.2e}  (quadrature limit)")
    print(f"toy control: Lambda = {toy_constant(1.0)} exactly, zeros real for t >= it")
    print()
    print("The flat zero-count scan is NOT evidence for RH -- the first exit, if")
    print("Lambda < 0, lies at Lehmer-pair heights, far above this range.")


if __name__ == "__main__":
    main()
