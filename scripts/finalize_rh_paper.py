# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC

"""Package the gap-closing artefact suite that accompanies the evaluation paper.

This script never invents an archive closure. It copies the gap-closer's archive and
local-control reports, reruns the reproducible control, and archives raw command output. The
finalizer paper was merged into the evaluation paper (`paper/evaluation_protocol.tex`), so this
script produces artefacts only; there is one paper in the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "rh_paper_finalizer"


def python_command() -> str:
    """Prefer `python` when it resolves; use the Windows launcher otherwise."""
    probe = subprocess.run(
        ["python", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return "python" if probe.returncode == 0 else "py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_capture(command: list[str], cwd: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    destination.write_text(
        "$ " + " ".join(command) + "\n\n"
        + "exit_code: " + str(result.returncode) + "\n\n"
        + "[stdout]\n" + (result.stdout or "")
        + "\n[stderr]\n" + (result.stderr or ""),
        encoding="utf-8",
    )


def copy_gap_outputs(out_dir: Path) -> None:
    """Copy the freshest gap-closer report: `out/` when a run has produced one, else `docs/`."""
    fresh = ROOT / "out" / "gap_closer" / "alpoge_2026"
    archived = ROOT / "docs" / "gap_closer" / "alpoge_2026"
    source = fresh if (fresh / "closure_crossvalidated.json").is_file() else archived
    for name in (
        "closure_deps.txt",
        "closure_laud.txt",
        "closure_crossvalidated.json",
        "load_bearing.json",
        "dependency_graph.html",
        "gap_statement.md",
    ):
        shutil.copy2(source / name, out_dir / name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    archive = ROOT / "docs" / "gap_closer" / "alpoge_2026"
    control = ROOT / "docs" / "gap_closer" / "alpoge_2026-control"
    if not archive.is_dir():
        raise SystemExit("missing archive gap-closer outputs")
    if not control.is_dir():
        raise SystemExit("missing local-control gap-closer outputs")

    # Refresh the executable local control and capture its raw process output.
    run_capture(
        [python_command(), "-m", "pytest", "python/tests/test_gap_closer.py", "-q"],
        ROOT,
        out_dir / "probe_logs" / "pytest_gap_closer.txt",
    )
    run_capture(
        [
            python_command(),
            "scripts/audit/rh_gap_closer.py",
            "--local-control",
            "--claim",
            "alpoge_2026",
        ],
        ROOT,
        out_dir / "probe_logs" / "control_gap_closer.txt",
    )
    run_capture(
        [
            python_command(),
            "scripts/audit/rh_gap_closer.py",
            "--claim",
            "alpoge_2026",
            "--archive",
            "external/alpoge-lean",
        ],
        ROOT,
        out_dir / "probe_logs" / "archive_gap_closer.txt",
    )

    copy_gap_outputs(out_dir)

    # The control report is evidence for the method and negative-control shape,
    # but it is separate from the archive report.
    control_dir = out_dir / "probe_logs" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "closure_deps.txt",
        "closure_laud.txt",
        "closure_crossvalidated.json",
        "load_bearing.json",
        "dependency_graph.html",
        "gap_statement.md",
        "manifest.json",
    ):
        shutil.copy2(control / name, control_dir / name)

    # A8: reproduce the suite from the archive's public source. Linux/macOS only: the Windows
    # Lean toolchain cannot build the archive (260-character path limit on auxiliary olean files).
    (out_dir / "reproduction.sh").write_text(
        """#!/usr/bin/env bash
# A8: reproduce the artefact suite and the paper's verdict.
# Linux/macOS. The Windows Lean toolchain cannot build the archive: Lean writes files such as
# `<Module>.olean.private.hash` beside each olean, and the longest module exceeds the 260-character
# path limit the Windows file API enforces for the toolchain.
#
# Usage:  bash reproduction.sh [WORKDIR]
set -euo pipefail

WORKDIR="${1:-alpoge-work}"
ARCHIVE_COMMIT="1cc42d2c900ba764cb63e3c36383c720f30a77ca"
ARCHIVE_URL="https://github.com/Deicyde/riemann-hypothesis"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$WORKDIR"
cd "$WORKDIR"
if [[ ! -d alpoge-lean/.git ]]; then
  git clone "$ARCHIVE_URL" alpoge-lean
fi
git -C alpoge-lean checkout "$ARCHIVE_COMMIT"
git -C alpoge-lean log -1 --format='archive commit %H %ad' --date=iso

command -v elan >/dev/null || { echo "elan is required: https://leanprover.github.io/elan/" >&2; exit 1; }
(
  cd alpoge-lean
  lake update
  lake exe cache get
  lake build Main
)

python3 "$HERE/scripts/audit/rh_gap_closer.py" --claim alpoge_2026 \\
  --archive "$(cd alpoge-lean && pwd)" --theorem Main.riemannHypothesis --module Main --timeout 7200

# The fresh report is packaged by the finalizer; copy it over the archived copy first.
cp -f "$HERE/out/gap_closer/alpoge_2026/"*.json "$HERE/out/gap_closer/alpoge_2026/"*.txt \\
      "$HERE/out/gap_closer/alpoge_2026/"*.html "$HERE/out/gap_closer/alpoge_2026/"*.md \\
      "$HERE/docs/gap_closer/alpoge_2026/" 2>/dev/null || true
python3 "$HERE/scripts/finalize_rh_paper.py"
python3 "$HERE/scripts/audit/verify_manifest.py" "$HERE/output/rh_paper_finalizer"
python3 "$HERE/scripts/audit/paper_readiness.py" "$HERE/output/rh_paper_finalizer"

echo
echo "Reproduction complete. Compare output/rh_paper_finalizer/ with the committed suite."
""",
        encoding="utf-8",
    )

    named = [
        "closure_deps.txt",
        "closure_laud.txt",
        "closure_crossvalidated.json",
        "load_bearing.json",
        "dependency_graph.html",
        "gap_statement.md",
        "reproduction.sh",
    ]
    manifest_lines = []
    for name in named:
        path = out_dir / name
        if path.is_file():
            manifest_lines.append(f"{sha256(path)}  {name}")
    for path in sorted((out_dir / "probe_logs").rglob("*")):
        if path.is_file():
            manifest_lines.append(f"{sha256(path)}  probe_logs/{path.relative_to(out_dir / 'probe_logs').as_posix()}")
    (out_dir / "MANIFEST.sha256").write_text(
        "\n".join(sorted(manifest_lines)) + "\n",
        encoding="utf-8",
    )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
