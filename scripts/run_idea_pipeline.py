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
"""Run every idea in `ideas/` through the vetting pipeline and print verdicts.

Usage, from the repository root:

    python scripts/run_idea_pipeline.py

Nothing printed here is a correctness claim: each verdict records how far an
idea got before hitting a known limitation or a genuinely open question.
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
    "_IDEA_PIPELINE_BOOTSTRAPPED"
):
    os.environ["_IDEA_PIPELINE_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import numpy as np

from riemann_framework.idea_pipeline import load_all_ideas, run_pipeline


def _sample_gue(dim: int = 120, seed: int = 1) -> np.ndarray:
    """Eigenvalues of a GUE matrix, used only to demonstrate Stage C wiring."""
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((dim, dim)) + 1j * rng.standard_normal((dim, dim))
    m = (a + a.conj().T) / 2
    return np.linalg.eigvalsh(m)


def main() -> None:
    ideas_dir = PROJECT_ROOT / "ideas"
    ideas = load_all_ideas(ideas_dir)

    gue_spectrum = _sample_gue()

    for index, idea in enumerate(ideas, start=1):
        print("=" * 70)
        print(f"Idea {index}: {idea.id}")
        print("=" * 70)
        # Attach a GUE spectrum to complex-plane ideas that clear stage B, so
        # the run also shows how a real spectrum would be wired into stage C.
        spectrum = gue_spectrum if idea.id != "dimension_shift_w" else None
        verdict = run_pipeline(idea, spectrum=spectrum)
        print(verdict)
        print()

    print("Note: 'not falsified so far' does not mean correct, and 'falsified'")
    print("records exactly which gate an idea failed, so the next attempt can")
    print("be designed to avoid the same trap.")


if __name__ == "__main__":
    main()
