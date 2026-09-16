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
"""Formal assert: Lean 4 proof without `sorry`."""

from pathlib import Path

import pytest

from riemann_framework.lean_runner import check_lean_file

PROJECT_ROOT = Path(__file__).parent.parent.parent
LEAN_DIR = PROJECT_ROOT / "lean"
RIEMANN_FRAMEWORK_DIR = LEAN_DIR / "RiemannFramework"

# Files to check individually
LEAN_FILES = [
    RIEMANN_FRAMEWORK_DIR / "DimensionShift.lean",
    RIEMANN_FRAMEWORK_DIR / "InvolutionEigenspace.lean",
    RIEMANN_FRAMEWORK_DIR / "ZetaConjecture.lean",
    RIEMANN_FRAMEWORK_DIR / "ZetaBridge.lean",
    RIEMANN_FRAMEWORK_DIR / "RiemannHypothesis.lean",
    RIEMANN_FRAMEWORK_DIR / "RiemannHypothesis_optimized.lean",
    RIEMANN_FRAMEWORK_DIR / "NewIdeaTest.lean",
    RIEMANN_FRAMEWORK_DIR / "SanityChecks.lean",
]

# Files that must be *complete*: compiled, and free of both `sorry` and `axiom`.
# These are the framework's genuine results, and this list is what keeps them honest.
SORRY_FREE_FILES = [
    RIEMANN_FRAMEWORK_DIR / "DimensionShift.lean",
    RIEMANN_FRAMEWORK_DIR / "InvolutionEigenspace.lean",
    RIEMANN_FRAMEWORK_DIR / "ZetaBridge.lean",
]

# Files that state the Riemann Hypothesis target itself. None of these may ever
# report a *complete* proof: the statement is open, so a `sorry` (or an `axiom`)
# must remain. This test exists to turn an accidental "RH is proved" claim into
# a test failure instead of a quietly edited README.
OPEN_RH_FILES = [
    RIEMANN_FRAMEWORK_DIR / "RiemannHypothesis.lean",
    RIEMANN_FRAMEWORK_DIR / "RiemannHypothesis_optimized.lean",
    RIEMANN_FRAMEWORK_DIR / "ZetaConjecture.lean",
]


def test_lean_file_lists_are_current():
    """Every file named in the lists above must actually exist.

    Without this guard a renamed or deleted module surfaces as a confusing Lean
    error ("object file ... does not exist") rather than as the real problem:
    a stale name in this test file.
    """
    listed = set(LEAN_FILES + SORRY_FREE_FILES + OPEN_RH_FILES)
    missing = sorted(f.name for f in listed if not f.exists())
    assert not missing, (
        f"Lean files listed in this test no longer exist: {missing}. "
        f"Update LEAN_FILES / SORRY_FREE_FILES / OPEN_RH_FILES."
    )


@pytest.mark.skipif(
    not RIEMANN_FRAMEWORK_DIR.exists(),
    reason="Lean directory not found",
)
@pytest.mark.parametrize("lean_file", LEAN_FILES)
def test_lean_file_compiles(lean_file):
    """Each Lean file should compile (even with `sorry`)."""
    status = check_lean_file(lean_file, PROJECT_ROOT)
    assert status["compiled"], (
        f"Lean compilation failed for {lean_file.name}:\n{status['output']}"
    )


@pytest.mark.skipif(
    not RIEMANN_FRAMEWORK_DIR.exists(),
    reason="Lean directory not found",
)
@pytest.mark.parametrize("lean_file", SORRY_FREE_FILES)
def test_sorry_free_file_is_complete(lean_file):
    """Each genuinely verified file must be sorry-free, with no `axiom` either."""
    status = check_lean_file(lean_file, PROJECT_ROOT)
    assert status["compiled"], (
        f"Lean compilation failed for {lean_file.name}:\n{status['output']}"
    )
    assert not status["has_sorry"], (
        f"{lean_file.name} contains `sorry`:\n{status['output']}"
    )
    assert not status["has_axiom"], (
        f"{lean_file.name} declares an `axiom`:\n{status['output']}"
    )
    assert status["success"], (
        f"{lean_file.name} is not a complete proof:\n{status['output']}"
    )


@pytest.mark.skipif(
    not RIEMANN_FRAMEWORK_DIR.exists(),
    reason="Lean directory not found",
)
@pytest.mark.parametrize("lean_file", OPEN_RH_FILES)
def test_rh_statement_stays_open(lean_file):
    """Every RH-target file must still be incomplete.

    `compiled` is expected, but `success` (compiled *and* free of
    `sorry`/`axiom`) must not hold, because the Riemann Hypothesis is an open
    problem and this repository does not claim to have proved it.
    """
    status = check_lean_file(lean_file, PROJECT_ROOT)
    assert status["compiled"], (
        f"Lean compilation failed for {lean_file.name}:\n{status['output']}"
    )
    assert status["has_sorry"] or status["has_axiom"], (
        f"{lean_file.name} no longer contains `sorry` or `axiom`. If this is "
        f"deliberate, it would mean the Riemann Hypothesis had been proved -- "
        f"remove this file from OPEN_RH_FILES only after independent "
        f"verification:\n{status['output']}"
    )
    assert not status["success"], (
        f"{lean_file.name} reports a complete proof:\n{status['output']}"
    )
