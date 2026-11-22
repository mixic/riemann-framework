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
"""Guards on the split-prime counterexample: the Lean module and the Python check.

The claim this file protects is narrow and it is *negative*: at a split prime, a unit
norm does not force unit local components, so the stratum is strictly smaller than the
norm pre-image it is identified with in Masullo's Section 1.3.2. Three things have to
stay true for that record to be worth keeping:

* the Lean module compiles, with no `sorry` and no axiom of its own;
* the aggregate module imports it, so a plain `lake build` reaches it;
* the Lean file and the exact Python certificate agree on the arithmetic
  (`5 = (2 + i)(2 - i)`, norms 5, neither factor a unit).

If someone weakens the Lean statement to a tautology, or edits the Python check so it
no longer exercises the split case, the record stops being evidence and one of these
fails.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from riemann_framework.lean_runner import check_lean_file

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODULE = PROJECT_ROOT / "lean" / "RiemannFramework" / "IdeleSplit.lean"
AGGREGATE = PROJECT_ROOT / "lean" / "RiemannFramework.lean"
AUDIT_DIR = PROJECT_ROOT / "scripts" / "audit"

requires_lean = pytest.mark.skipif(
    not MODULE.exists() or shutil.which("lake") is None,
    reason="Lean toolchain (lake) not available",
)


@requires_lean
def test_the_module_compiles_sorry_free():
    """It must compile, and it must not smuggle in `sorry` or an axiom."""
    status = check_lean_file(MODULE, PROJECT_ROOT, timeout=1800)
    assert status["compiled"], status["output"]
    assert not status["has_sorry"], status["output"]
    assert not status["has_axiom"], status["output"]
    assert status["success"], status["output"]


@requires_lean
def test_the_declared_axioms_are_the_standard_three():
    """The two theorems must rest on the standard axioms only.

    `#print axioms` lines are in the compiler output, so this reads the same evidence
    the kernel printed rather than trusting the docstring.
    """
    status = check_lean_file(MODULE, PROJECT_ROOT, timeout=1800)
    output = status["output"]
    assert "sorryAx" not in output, output
    for axiom in ("propext", "Classical.choice", "Quot.sound"):
        assert axiom in output, output


def test_the_aggregate_imports_the_module():
    """A file a plain `lake build` never reaches is a file that rots."""
    assert "import RiemannFramework.IdeleSplit" in AGGREGATE.read_text(encoding="utf-8")


def test_the_certificate_agrees_with_the_exact_python_check():
    """The Lean constants and the Python certificate must describe the same pair.

    The Python side is imported from `scripts/audit/three_checks.py`, which is not a
    package module, so it is loaded by path.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "three_checks_for_idele_test", AUDIT_DIR / "three_checks.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    cert = module.split_prime_certificate(5)
    assert cert["product_equals_p"], cert
    assert cert["pi1"] == "2 + 1i", cert
    assert cert["pi2"] == "2 - 1i", cert
    assert cert["norm_pi1"] == cert["norm_pi2"] == 5, cert
    assert not cert["pi1_is_unit"] and not cert["pi2_is_unit"], cert

    lean = MODULE.read_text(encoding="utf-8")
    assert "def pi1 : GaussianInt := ⟨2, 1⟩" in lean
    assert "def pi2 : GaussianInt := ⟨2, -1⟩" in lean
    assert "pi1_mul_pi2" in lean and "split_prime_certificate" in lean
