"""Formal assert: Lean 4 proof without `sorry`."""

from pathlib import Path

import pytest

from riemann_framework.lean_runner import check_lean_file

PROJECT_ROOT = Path(__file__).parent.parent.parent
LEAN_FILE = PROJECT_ROOT / "lean" / "RiemannFramework" / "RiemannHypothesis.lean"


@pytest.mark.skipif(
    not LEAN_FILE.exists(),
    reason="Lean file not found",
)
def test_riemann_hypothesis_lean():
    """Check whether the Lean 4 proof is complete (no `sorry`)."""
    status = check_lean_file(LEAN_FILE, PROJECT_ROOT)

    assert not status["has_sorry"], (
        "ERROR: The proof still contains `sorry` – "
        "the Riemann Hypothesis is NOT formally proven."
    )
    assert status["success"], (
        f"ERROR: Lean compilation failed:\n{status['output']}"
    )
    print("Formal RH proof successfully verified.")