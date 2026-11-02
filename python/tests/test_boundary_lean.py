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
"""Tests for the Lean boundary module and the correction it carries.

Two kinds of check. The mechanical one compiles `Boundary.lean` through the same
`lean_runner` the rest of the suite uses, and it is skipped where no toolchain exists
(the CI Python job installs none; the separate `lean-build` job covers the build).
The other two are documentation guards, because the claim this module replaces was a
*false statement in the docs*: if "equal dimension" ever reappears in
`docs/future_work.md` or the aggregate module stops importing the file, that is the
regression to catch, and it can be caught without Lean.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from riemann_framework.lean_runner import check_lean_file

PROJECT_ROOT = Path(__file__).parent.parent.parent
BOUNDARY_FILE = PROJECT_ROOT / "lean" / "RiemannFramework" / "Boundary.lean"
AGGREGATE = PROJECT_ROOT / "lean" / "RiemannFramework.lean"
FUTURE_WORK = PROJECT_ROOT / "docs" / "future_work.md"
EIGENSPACE_FILE = (
    PROJECT_ROOT / "lean" / "RiemannFramework" / "InvolutionEigenspace.lean"
)

requires_lean = pytest.mark.skipif(
    not BOUNDARY_FILE.exists() or shutil.which("lake") is None,
    reason="Lean toolchain (lake) not available",
)


@requires_lean
def test_the_boundary_module_is_sorry_free():
    """The file must compile with no `sorry` and no `axiom`."""
    status = check_lean_file(BOUNDARY_FILE, PROJECT_ROOT, timeout=1800)
    assert status["compiled"], status["output"]
    assert not status["has_sorry"], status["output"]
    assert not status["has_axiom"], status["output"]
    assert status["success"], status["output"]


def test_the_aggregate_module_imports_the_boundary():
    """A file a plain `lake build` never reaches is a file that rots."""
    assert "import RiemannFramework.Boundary" in AGGREGATE.read_text(encoding="utf-8")


def test_the_false_equal_dimension_claim_is_gone():
    """The regression guard for the correction.

    `docs/future_work.md` listed "finite +1 and -1 eigenspaces have equal dimension"
    as a target. It is false, and the counterexample is now in `Boundary.lean`. If the
    phrase comes back without a counterexample next to it, this fails.
    """
    text = FUTURE_WORK.read_text(encoding="utf-8")
    assert "eigenspaces have equal dimension\n" not in text
    assert "eigenspaces can\n" not in text
    assert "item 3 was **false**" in text
    assert "Boundary.lean" in text
    docstring = EIGENSPACE_FILE.read_text(encoding="utf-8")
    assert "eigenspaces have equal dimension" not in docstring
    assert "eigenspaces_can_differ" in docstring
