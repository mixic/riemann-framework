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
"""Compile Lean 4 files and check for `sorry` and axioms."""

import subprocess
from pathlib import Path


def check_lean_file(lean_file: Path, project_root: Path, timeout: int = 600) -> dict:
    """
    Compile a Lean 4 file and check for `sorry`.

    Returns:
        {
            "success": bool,      # compiles without errors AND without sorry
            "has_sorry": bool,
            "output": str,
        }
    """
    result = subprocess.run(
        ["lake", "env", "lean", str(lean_file)],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = result.stdout + result.stderr
    has_sorry = "declaration uses 'sorry'" in output
    success = (result.returncode == 0) and not has_sorry

    return {
        "success": success,
        "has_sorry": has_sorry,
        "output": output,
    }