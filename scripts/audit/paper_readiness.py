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
"""Check whether the paper-finalizer precondition is met, and emit the fallback verdict.

The specification of RH-PAPER-FINALIZER makes the paper conditional on an executed, cross-validated
closure and a load-bearing classification for every flagged declaration. If those are absent, the
agent must emit `undetermined` with the named computation "complete RH-GAP-CLOSER first" rather
than write a paper whose Section 7 would be an assertion without an artefact.

This script performs that check mechanically over the archived artefact directory and prints the
verdict. It never edits the artefacts and never writes the paper.

Usage:  python scripts/audit/paper_readiness.py [ARTEFACT_DIR] [--json PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = REPO_ROOT / "output" / "rh_paper_finalizer"
# One paper in the repository: the finalizer's content was merged into it.
FINAL_PAPER = REPO_ROOT / "paper" / "evaluation_protocol.pdf"

FORBIDDEN = (
    "riemann hypothesis is true",
    "riemann hypothesis is proved",
    "riemann hypothesis is proven",
    "proves the riemann hypothesis",
    "settles rh",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _names(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def _asserts_proof(text: str) -> str | None:
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        low = sentence.lower()
        if "riemann hypothesis" not in low and not re.search(r"\brh\b", low):
            continue
        if re.search(r"\b(is|are|was|were|has been|have been)\s+(true|proved|proven|settled)\b", low):
            if not re.search(r"\b(not|no|never|cannot|does not|refuses|withheld)\b", low):
                return sentence.strip()
    return None


def check(directory: Path) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []

    def add(identifier: str, ok: bool, detail: str) -> None:
        checks.append({"id": identifier, "ok": ok, "detail": detail})

    cross = directory / "closure_crossvalidated.json"
    payload: dict = {}
    if cross.is_file():
        try:
            payload = json.loads(cross.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            payload = {"status": f"unreadable: {error}"}
    deps = directory / "closure_deps.txt"
    laud = directory / "closure_laud.txt"
    deps_names = _names(deps) if deps.is_file() else []
    laud_names = _names(laud) if laud.is_file() else []
    common = payload.get("common") or []

    add("A2 closure_deps.txt", bool(deps_names), f"{len(deps_names)} names")
    add("A3 closure_laud.txt", bool(laud_names), f"{len(laud_names)} names")
    add(
        "A4 closure_crossvalidated.json",
        payload.get("status") == "checked_ok" and bool(common),
        f"status {payload.get('status')!r}, common {len(common)} names",
    )

    load = directory / "load_bearing.json"
    declarations: list = []
    if load.is_file():
        try:
            declarations = json.loads(load.read_text(encoding="utf-8")).get("declarations", [])
        except json.JSONDecodeError:
            declarations = []
    classified = [
        item for item in declarations
        if isinstance(item, dict) and item.get("name") and item.get("vacuity_critical") in (True, False)
    ]
    add("A5 load_bearing.json", bool(classified), f"{len(classified)} classified declaration(s)")

    graph = directory / "dependency_graph.html"
    graph_text = graph.read_text(encoding="utf-8", errors="replace") if graph.is_file() else ""
    add(
        "A6 dependency_graph.html",
        all(colour in graph_text for colour in ("red", "amber", "green", "blue", "yellow")),
        "five-colour legend present" if graph_text else "missing",
    )

    gap = directory / "gap_statement.md"
    gap_text = gap.read_text(encoding="utf-8", errors="replace") if gap.is_file() else ""
    add(
        "A7 gap_statement.md",
        "## 4." in gap_text
        and any(line.startswith("- ") for line in gap_text.split("## 4.")[1].splitlines()),
        "has Section 4 with the named computations" if gap_text else "missing",
    )
    add(
        "A8 reproduction.sh",
        (directory / "reproduction.sh").is_file(),
        "present" if (directory / "reproduction.sh").is_file() else "missing",
    )
    logs = directory / "probe_logs"
    log_files = sorted(path for path in logs.rglob("*") if path.is_file()) if logs.is_dir() else []
    add("A9 probe_logs/", len(log_files) >= 3, f"{len(log_files)} log file(s)")

    manifest = directory / "MANIFEST.sha256"
    manifest_ok = False
    if manifest.is_file():
        manifest_ok = True
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            digest, _, name = line.partition("  ")
            path = directory / name
            if not path.is_file() or _sha256(path) != digest:
                manifest_ok = False
                break
    add("A10 MANIFEST.sha256", manifest_ok, "verifies" if manifest_ok else "missing or does not verify")

    add(
        "A1 final paper",
        FINAL_PAPER.is_file(),
        f"{FINAL_PAPER.relative_to(REPO_ROOT).as_posix()} "
        + ("present" if FINAL_PAPER.is_file() else "not written: its Section 7 would lack an executed artefact"),
    )

    executed = bool(deps_names) and bool(laud_names) and payload.get("status") == "checked_ok"
    add("R1 executed closure", executed, "C1 and C2 ran and agree" if executed else "closure not executed on the archive")
    add(
        "R2 per-declaration classification",
        bool(classified) and bool(common),
        f"{len(classified)} declaration(s) classified",
    )
    add(
        "R3 verdict populated",
        payload.get("verdict") in {
            "rejected", "outside domain", "undetermined",
            "validated (finite)", "validated (elementary)", "validated (term)",
        },
        f"verdict {payload.get('verdict')!r}",
    )
    add("R4 falsification stated", "## 4." in gap_text, "gap statement names the computations that move the verdict")
    add("R5 no proof claim", _asserts_proof(gap_text) is None, _asserts_proof(gap_text) or "none")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    directory = args.directory.resolve()
    checks = check(directory)
    blocking = [c for c in checks if not c["ok"]]
    verdict = "undetermined" if blocking else "validated (term)"
    named = (
        ["complete RH-GAP-CLOSER first"]
        if any(c["id"].startswith(("R1", "R2", "R3")) and not c["ok"] for c in checks)
        else []
    )

    for item in checks:
        print(f"[{'ok  ' if item['ok'] else 'FAIL'}] {item['id']}: {item['detail']}")
    print(f"\nverdict: {verdict}")
    for item in named:
        print(f"named computation: {item}")

    record = {
        "artefact_dir": str(directory),
        "checks": checks,
        "blocking": [c["id"] for c in blocking],
        "verdict": verdict,
        "named_computations": named,
        "specification": "RH-PAPER-FINALIZER",
    }
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"written: {args.json}")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
