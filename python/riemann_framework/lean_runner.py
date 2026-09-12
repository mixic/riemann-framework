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