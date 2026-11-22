"""Execute the decisive dependency trace against a checked-out archive.

The trace is the paper's decisive computation for the Alp\"oge case, and the archive is not
held here: 931 MB of git blobs, 61.5 GB of export, Lean v4.33.1 against this repository's
v4.34.0-rc2. The record therefore reports `not run`. This script is what turns that report
into an executable step rather than a paragraph: it validates the preconditions, states the
plan, copies the trace module into the archive, and runs both extractors there with the
archive's own toolchain.

`--plan` is safe and offline: it validates what it can and prints the exact steps without
touching the archive, which is what the tests exercise. `--run` performs them.

Usage (from the repository root):

    python scripts/audit/trace_archive.py --archive path/to/archive --plan
    python scripts/audit/trace_archive.py --archive path/to/archive --module <Module> --run

The archive's lakefile must include the directory the trace module is copied into; most
Lean projects use a glob of the form `.**`, which does. A run that fails on an unknown
module says so in the record rather than guessing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "python"))

from riemann_framework.claim_audit import TraceRequest, trace_with_cross_validation  # noqa: E402

#: The version the published archive pins, from its `lean-toolchain`.
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.33.1"
TRACE_SOURCE = REPO_ROOT / "lean" / "RiemannFramework" / "DependencyTrace.lean"
AUDIT_DIR = "Audit"


@dataclass(frozen=True)
class Check:
    """One precondition, and whether its failure blocks the run."""

    name: str
    ok: bool
    detail: str
    blocking: bool = True


def preconditions(
    archive: Path,
    *,
    module: str = "",
    expected_toolchain: str = EXPECTED_TOOLCHAIN,
) -> list[Check]:
    """What the environment must satisfy, reported rather than assumed."""
    checks = [
        Check("archive", archive.is_dir(), str(archive)),
        Check(
            "lakefile",
            (archive / "lakefile.lean").is_file() or (archive / "lakefile.toml").is_file(),
            "lakefile.lean or lakefile.toml in the archive",
        ),
        Check("trace source", TRACE_SOURCE.is_file(), str(TRACE_SOURCE)),
    ]
    toolchain = archive / "lean-toolchain"
    if toolchain.is_file():
        actual = toolchain.read_text(encoding="utf-8").strip()
        checks.append(
            Check(
                "toolchain",
                actual == expected_toolchain,
                f"archive pins {actual}; the trace is calibrated against {expected_toolchain}",
                blocking=False,
            )
        )
    else:
        checks.append(
            Check("toolchain", False, "no lean-toolchain in the archive", blocking=False)
        )
    if module:
        expected_file = archive / Path(*module.split(".")).with_suffix(".lean")
        checks.append(
            Check(
                "module",
                expected_file.is_file(),
                f"expected {expected_file}" if expected_file.is_file() else f"not found: {expected_file}",
                blocking=False,
            )
        )
    return checks


def ready(checks: list[Check]) -> bool:
    return all(check.ok for check in checks if check.blocking)


def plan(archive: Path, module: str, theorem: str) -> list[str]:
    """The exact steps the run performs, in order, with the paths resolved."""
    trace_module = f"{AUDIT_DIR}.DependencyTrace"
    return [
        f"copy {TRACE_SOURCE.name} to {archive / AUDIT_DIR / 'DependencyTrace.lean'}",
        f"import {trace_module} and {module or '<module>'} in a generated driver",
        f"elaborate '#deps {theorem}' and '#depsm {theorem}' with the archive's own lake",
        "compare the two closures; a difference leaves the trace undetermined",
        f"write the record to {archive / 'trace_record.json'}",
    ]


def execute(
    archive: Path,
    module: str,
    theorem: str,
    *,
    suspects: tuple[str, ...] = (),
    timeout: int = 3600,
) -> dict[str, object]:
    """Validate, copy, run both extractors, and return a JSON-safe record."""
    checks = preconditions(archive, module=module)
    record: dict[str, object] = {
        "archive": str(archive),
        "module": module,
        "theorem": theorem,
        "suspects": list(suspects),
        "checks": [
            {"name": c.name, "ok": c.ok, "detail": c.detail, "blocking": c.blocking} for c in checks
        ],
    }
    if not ready(checks):
        record["status"] = "not_run"
        record["reason"] = "precondition failed: " + "; ".join(
            f"{c.name} ({c.detail})" for c in checks if c.blocking and not c.ok
        )
        return record

    target = archive / AUDIT_DIR / "DependencyTrace.lean"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TRACE_SOURCE, target)
    trace_module = f"{AUDIT_DIR}.DependencyTrace"

    status, payload = trace_with_cross_validation(
        archive,
        module,
        TraceRequest(theorem=theorem, suspects=suspects),
        timeout=timeout,
        trace_module=trace_module,
    )
    record["status"] = getattr(status, "value", str(status))
    record["result"] = _jsonable(payload)
    return record


def _jsonable(value: object) -> object:
    """Recursively convert sets and path-like values so the record can be written as JSON."""
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(str(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--module", default="", help="the module that defines the target theorem")
    parser.add_argument("--theorem", default="riemannHypothesis")
    parser.add_argument("--suspects", default="", help="comma-separated names to test for reachability")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--plan", action="store_true", help="validate and print the steps; run nothing")
    parser.add_argument("--run", action="store_true", help="perform the steps")
    args = parser.parse_args()

    suspects = tuple(part.strip() for part in args.suspects.split(",") if part.strip())
    checks = preconditions(args.archive, module=args.module)
    for check in checks:
        label = "ok  " if check.ok else ("RISK" if not check.blocking else "FAIL")
        print(f"[{label}] {check.name}: {check.detail}")
    print()
    for step in plan(args.archive, args.module, args.theorem):
        print(f"  - {step}")

    if not args.run:
        if not ready(checks):
            print("\nstatus: not run (preconditions failed)")
            return 1
        print("\nstatus: planned; pass --run to execute")
        return 0

    record = execute(
        args.archive,
        args.module,
        args.theorem,
        suspects=suspects,
        timeout=args.timeout,
    )
    print(f"\nstatus: {record['status']}")
    if "reason" in record:
        print(f"reason: {record['reason']}")
    out = args.out or (args.archive / "trace_record.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"written: {out}")
    return 0 if record.get("status") != "not_run" else 1


if __name__ == "__main__":
    raise SystemExit(main())
