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
"""Plot the double-bracket flow: what it preserves and what it selects.

Usage, from the repository root:

    python scripts/run_dynamical_desymmetrisation_demo.py

Writes `output/dynamical_desymmetrisation.png`. Two panels, one claim each:

* a state that commutes with the involution keeps `[rho, sigma] = 0` and its sector
  populations for the whole run (the invariance the literature describes);
* a state that does not is driven by the flow to zero coherence and into a single
  sector -- so the flow *selects* a sector rather than preserving one, and in neither
  case does it touch the Hamiltonian.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_DYNAMICAL_DESYMMETRISATION_BOOTSTRAPPED"
):
    os.environ["_DYNAMICAL_DESYMMETRISATION_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from riemann_framework.dimension_shift_chaos import (  # noqa: E402
    build_dimension_shift_hamiltonian,
    sector_swap,
)
from riemann_framework.dynamical_desymmetrisation import (  # noqa: E402
    dynamical_desymmetrise,
    two_copy_expansion,
)

DIMENSION = 4
BETA = 15.0
STEPS = 3000


def main() -> None:
    hamiltonian = build_dimension_shift_hamiltonian(DIMENSION, 1.0, "gue", seed=0)
    involution = sector_swap(DIMENSION)
    size = 2 * DIMENSION

    values, vectors = np.linalg.eigh(hamiltonian)

    thermal = vectors @ np.diag(np.exp(-0.7 * values)) @ vectors.conj().T
    thermal = thermal / np.real(np.trace(thermal))

    def sector_state(sign: int, index: int) -> np.ndarray:
        projector = (np.eye(size) + sign * involution) / 2.0
        _, basis = np.linalg.eigh(
            projector @ hamiltonian @ projector + 1e6 * (np.eye(size) - projector)
        )
        return basis[:, index]

    vector = (sector_state(+1, 0) + sector_state(-1, 0)) / np.sqrt(2.0)
    cross = np.outer(vector, vector.conj())

    symmetric = dynamical_desymmetrise(hamiltonian, involution, thermal, beta=BETA, steps=STEPS)
    selected = dynamical_desymmetrise(hamiltonian, involution, cross, beta=BETA, steps=STEPS)

    figure, (left, right) = plt.subplots(1, 2, figsize=(11, 4.6), constrained_layout=True)

    left.plot(symmetric.betas, symmetric.coherences, color="green", label="commuting state")
    left.plot(selected.betas, selected.coherences, color="orange", label="cross-sector state")
    left.set_xlabel(r"$\beta$ (flow time)")
    left.set_ylabel(r"$\Vert[\rho, \sigma]\Vert_F$")
    left.set_title("coherence with the involution")
    left.set_yscale("symlog", linthresh=1e-8)
    left.grid(alpha=0.25)
    left.legend(fontsize=8)

    right.plot(selected.betas, selected.sector_populations[:, 0], color="orange", label="+ sector")
    right.plot(selected.betas, selected.sector_populations[:, 1], color="purple", label="- sector")
    right.plot(
        symmetric.betas,
        symmetric.sector_populations[:, 0],
        color="orange",
        linestyle=":",
        label="+ sector (commuting start)",
    )
    right.set_xlabel(r"$\beta$ (flow time)")
    right.set_ylabel(r"$\mathrm{tr}(P_\pm \rho)$")
    right.set_title("sector populations: invariant vs selected")
    right.set_ylim(-0.02, 1.02)
    right.grid(alpha=0.25)
    right.legend(fontsize=8)

    figure.suptitle(
        "The double-bracket flow acts on the state, never on the Hamiltonian",
        fontsize=10,
    )
    out = PROJECT_ROOT / "output" / "dynamical_desymmetrisation.png"
    figure.savefig(out, dpi=150)
    plt.close(figure)

    print(f"wrote {out.relative_to(PROJECT_ROOT)}")
    print()
    print("State that commutes with the involution:")
    print("  " + symmetric.summary())
    print()
    print("State that does not:")
    print("  " + selected.summary())
    print()
    print("Invariants along the selected run: spectrum drift "
          f"{selected.spectrum_drift:.1e}, trace drift {selected.trace_drift:.1e}, "
          f"non-Hermiticity {selected.hermiticity_drift:.1e}")
    print()
    print("The Hamiltonian itself: untouched, so no spacing statistic of it changes.")
    print()
    print("The multi-copy identity, measured on the cross-sector state:")
    for generator in ("difference", "swap", "split"):
        expansion = two_copy_expansion(cross, hamiltonian, generator=generator)
        print("  " + expansion.summary())
    print()
    print("  -> the quoted identity needs a vanishing first-order term; none of these")
    print("     circuits has one, and none reproduces +/-[[rho,H],rho] at second order.")
    print("     Reported as unverified, not assumed.")
    print()
    print("No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
