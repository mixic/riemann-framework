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
"""Run the dimension-shift idea (and a contrasting nonlinear example) through
the full vetting pipeline, and print the verdicts.

Usage:
    python examples/run_dimension_shift_example.py
"""

import sys
from pathlib import Path

# Allow running this script directly from the examples/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from riemann_framework.idea_pipeline import load_idea, run_pipeline
from riemann_framework.quantum_chaos import gue_random_matrix_eigenvalues


def main() -> None:
    ideas_dir = Path(__file__).resolve().parent.parent.parent / "ideas"

    print("=" * 70)
    print("Idea 1: dimension_shift_w  (sigma(s) = 1 - conjugate(s))")
    print("=" * 70)
    idea1 = load_idea(ideas_dir / "dimension_shift_w.json")
    verdict1 = run_pipeline(idea1)
    print(verdict1)
    print()

    print("=" * 70)
    print("Idea 2: nonlinear_probe_example  (w(s) = s*conjugate(s) - s)")
    print("=" * 70)
    idea2 = load_idea(ideas_dir / "nonlinear_probe_example.json")
    # Feed it a GUE spectrum just to demonstrate stage C wiring; this has
    # nothing to do with the map itself, it only shows how you would attach
    # a real spectrum if this idea produced a Hamiltonian.
    demo_spectrum = gue_random_matrix_eigenvalues(dim=200, seed=1)
    verdict2 = run_pipeline(idea2, spectrum=demo_spectrum)
    print(verdict2)
    print()

    print("Note: neither verdict claims correctness. 'Stage reached' only")
    print("records how far each idea got before hitting a known limitation")
    print("or genuinely open question.")


if __name__ == "__main__":
    main()
