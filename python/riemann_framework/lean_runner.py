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
"""Compile Lean 4 files and check for `sorry` and `axiom` declarations."""

import re
import subprocess
from pathlib import Path

# Lean's warning text is `declaration uses 'sorry'` in some versions and
# `declaration uses `sorry`` in others, so both quote styles are accepted.
_SORRY_RE = re.compile(r"declaration uses [`']sorry[`']")


def _declares_axiom(lean_file: Path) -> bool:
    """True when `lean_file` contains an `axiom` (or `constant`) declaration.

    Unlike `sorry` — which Lean itself flags with a `declaration uses ...sorry...`
    warning — an `axiom` compiles silently, so the source must be inspected
    directly. A line whose first non-whitespace characters are `axiom` (or
    `constant`, its synonym) is treated as a declaration.
    """
    source = lean_file.read_text(encoding="utf-8")
    return bool(re.search(r"(?m)^[ \t]*(axiom|constant)\b", source))


def _module_name(lean_file: Path, project_root: Path) -> "str | None":
    """Derive the Lake module name for a file below the library source root.

    `lean/RiemannFramework/SanityChecks.lean` becomes
    `RiemannFramework.SanityChecks`. Returns `None` when `lean_file` does not
    live under `<project_root>/lean`, where `lake build` cannot be used.
    """
    source_dir = (project_root / "lean").resolve()
    try:
        relative = lean_file.resolve().relative_to(source_dir)
    except ValueError:
        return None
    if relative.suffix != ".lean":
        return None
    return ".".join(relative.with_suffix("").parts)


def check_lean_file(lean_file: Path, project_root: Path,
                    timeout: int = 900) -> dict:
    """Compile a Lean 4 file and check for `sorry` and `axiom`.

    The module containing `lean_file` (and therefore its imports) is built
    first, because `lake env lean` resolves project-local imports through the
    object files in `.lake/build/lib` and cannot elaborate a source file whose
    imports have never been compiled.

    Returns:
        {
            "compiled": bool,   # `lake env lean` exited successfully
            "success": bool,    # compiled AND free of sorry/axiom
            "has_sorry": bool,
            "has_axiom": bool,
            "output": str,      # diagnostics for `lean_file` alone
            "build_output": str,  # diagnostics from building the module
        }
    """
    module = _module_name(lean_file, project_root)
    build_output = ""
    if module is not None:
        # Incremental: cheap when the module and its dependencies are current.
        # Its output is kept separate from `output` so that `has_sorry` reflects
        # only `lean_file`, not `sorry`s inside the modules it imports.
        build = subprocess.run(
            ["lake", "build", module],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        build_output = build.stdout + build.stderr

    result = subprocess.run(
        ["lake", "env", "lean", str(lean_file)],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = result.stdout + result.stderr
    compiled = result.returncode == 0
    has_sorry = bool(_SORRY_RE.search(output))
    has_axiom = _declares_axiom(lean_file)
    success = compiled and not has_sorry and not has_axiom

    return {
        "compiled": compiled,
        "success": success,
        "has_sorry": has_sorry,
        "has_axiom": has_axiom,
        "output": output,
        "build_output": build_output,
    }


def build_project(project_root: Path, timeout: int = 1800) -> dict:
    """Run `lake build` on the whole project."""
    result = subprocess.run(
        ["lake", "build"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = result.stdout + result.stderr
    has_sorry = bool(_SORRY_RE.search(output))
    success = (result.returncode == 0) and not has_sorry

    return {
        "success": success,
        "has_sorry": has_sorry,
        "output": output,
    }
