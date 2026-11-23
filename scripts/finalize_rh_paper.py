# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC

"""Package the RH paper-finalizer artefact suite.

This script never invents an archive closure. It copies the gap-closer's
archive and local-control reports, reruns the reproducible control, and
archives raw command output. The final verdict remains protocol-governed:
UNDETERMINED until C1-C4 complete on the real archive.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "rh_paper_finalizer"
PAPER_SOURCE = ROOT / "docs" / "rh_paper_finalizer.md"


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
    for name in (
        "closure_deps.txt",
        "closure_laud.txt",
        "closure_crossvalidated.json",
        "load_bearing.json",
        "dependency_graph.html",
        "gap_statement.md",
    ):
        shutil.copy2(ROOT / "docs" / "gap_closer" / "alpoge_2026" / name, out_dir / name)


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

    shutil.copy2(PAPER_SOURCE, out_dir / "paper.md")

    subprocess.run(
        [
            python_command(),
            "scripts/build_manuscript_pdf.py",
            "--source",
            str(PAPER_SOURCE),
            "--output",
            str(out_dir / "paper.pdf"),
            "--backend",
            "chrome",
            "--author",
            "Milan Nikolic",
            "--affiliation",
            "Independent Researcher",
            "--email",
            "m_nikolic@yahoo.com",
            "--date",
            "23 November 2026",
        ],
        cwd=ROOT,
        check=True,
    )

    # Pinned reproduction command. It exercises the control and archive mode;
    # an absent archive is an expected not_run outcome, not a success-shaped fallback.
    (out_dir / "reproduction.sh").write_text(
        """#!/usr/bin/env sh
set -eu
export LEAN_TOOLCHAIN=leanprover/lean4:v4.33.1
echo "Pinned archive toolchain: $LEAN_TOOLCHAIN"
echo "Repository control toolchain: $(cat lean-toolchain)"
py -m pytest python/tests/test_gap_closer.py -q
py scripts/audit/rh_gap_closer.py --local-control --claim alpoge_2026
py scripts/audit/rh_gap_closer.py --claim alpoge_2026 --archive external/alpoge-lean
py scripts/finalize_rh_paper.py
""",
        encoding="utf-8",
    )

    named = [
        "paper.pdf",
        "paper.md",
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
