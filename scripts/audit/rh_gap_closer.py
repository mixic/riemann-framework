"""Execute the gap closer: closure, cross-validation, load-bearing classification, verdict.

Two modes:

    python scripts/audit/rh_gap_closer.py --claim alpoge_2026 --archive external/alpoge-lean
    python scripts/audit/rh_gap_closer.py --claim alpoge_2026 --local-control

The archive mode reports `not run` for every computation when the archive is absent, with the
named computation that would execute it; it never estimates a closure from the paper's prose.
When the archive is present the closure runs with the trace module copied in, and C4 stays
`not run` until vacuous analogues for the flagged declarations are declared from the archive's
own sources (the record's single mutant is marked NOT CHECKED HERE).

The control mode executes C1--C3 on this repository's `Dispute.lean` and records what C4 can and
cannot decide there.

Every artefact is written to `out/gap_closer/<claim>/` with a SHA-256 manifest.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "python"))

from riemann_framework.adjudicator import load_mutants, run_mutant  # noqa: E402
from riemann_framework.claim_audit import Status, TraceRequest, Verdict, dependency_trace  # noqa: E402
from riemann_framework.gap_closer import (  # noqa: E402
    Computation,
    STANDING,
    build_report,
    census_flags,
    write_artefacts,
)

CLAIMS = REPO_ROOT / "claims" / "alpoge_2026.json"
TRACE_MODULE = "RiemannFramework.DependencyTrace"
LIVE_ROLE = "this repository's recording of the dispute (live)"
ARCHIVE_TOOL = (
    "clone https://github.com/Deicyde/riemann-hypothesis into external/alpoge-lean (931 MB; "
    "needs core.longpaths), build it with its own lakefile under Lean v4.33.1 and Mathlib "
    "0df444a3, then re-run this script with --archive external/alpoge-lean"
)


def _not_run(name: str, instrument: str, reason: str, named: str, *, substitute: str | None = None) -> Computation:
    return Computation(
        name=name,
        instrument=instrument,
        status="not_run",
        detail=reason,
        named_computation=named,
        substitute=substitute,
    )


def _trace_pair(project: Path, module: str, theorem: str, suspects: tuple[str, ...], timeout: int, trace_module: str):
    request = TraceRequest(theorem=theorem, suspects=suspects)
    first = dependency_trace(project, module, request, timeout=timeout, trace_module=trace_module, extractor="deps")
    second = dependency_trace(project, module, request, timeout=timeout, trace_module=trace_module, extractor="depsm")
    return first, second


def _computations(first, second, *, c2_note: str) -> tuple[Computation, ...]:
    status1, d1 = first
    status2, d2 = second
    # CHECKED_FAILED means the trace ran and reached a suspect: that is the evidence the probe
    # exists to produce, not a failure to distinguish from "did not run".
    ran1 = status1 in (Status.CHECKED_OK, Status.CHECKED_FAILED) and bool(d1.get("names"))
    ran2 = status2 in (Status.CHECKED_OK, Status.CHECKED_FAILED) and bool(d2.get("names"))
    if ran1:
        c1 = Computation("C1", "#deps (Expr.getUsedConstants)", "checked_ok",
                         f"closure of {len(d1['names'])} names", {"names": d1["names"]})
    else:
        c1 = _not_run("C1", "#deps (Expr.getUsedConstants)", "the trace did not run",
                      "inspect the Lean output and re-run")
    c2 = (
        Computation("C2", "#depsm (structural recursion)", "checked_ok",
                    f"closure of {len(d2['names'])} names", {"names": d2["names"]}, substitute=c2_note)
        if ran2
        else _not_run("C2", "#depsm (structural recursion)", "the second extractor did not run",
                      "inspect the Lean output and re-run", substitute=c2_note)
    )
    n1 = set(d1.get("names", ())) if ran1 else set()
    n2 = set(d2.get("names", ())) if ran2 else set()
    only1 = sorted(n1 - n2)
    only2 = sorted(n2 - n1)
    agree = ran1 and ran2 and not only1 and not only2
    c3 = Computation(
        "C3", "closure comparison",
        "checked_ok" if agree else "checked_failed",
        "the two closures agree" if agree else f"{len(only1)} only in #deps, {len(only2)} only in #depsm",
        {"only_in_deps": only1, "only_in_laud": only2, "agreement": agree},
        named_computation=None if agree else "reconcile the closure mismatch between #deps and #depsm",
    )
    return c1, c2, c3


def archive_mode(archive: Path, *, claim: str, theorem: str, module: str, timeout: int):
    checks = {
        "archive directory": archive.is_dir(),
        "lakefile": (archive / "lakefile.lean").is_file() or (archive / "lakefile.toml").is_file(),
        "lean-toolchain": (archive / "lean-toolchain").is_file(),
    }
    if not all(checks.values()):
        detail = ", ".join(f"{k}: {'ok' if v else 'missing'}" for k, v in checks.items())
        computations = (
            _not_run("C1", "#deps (Expr.getUsedConstants)", f"archive precondition failed ({detail})", ARCHIVE_TOOL),
            _not_run("C2", "#depsm (structural recursion)", f"archive precondition failed ({detail})", ARCHIVE_TOOL,
                     substitute="laud graph is not available; #depsm is the substitute"),
            _not_run("C3", "closure comparison", "no closure to compare", "run C1 and C2"),
            _not_run("C4", "vacuous-analogue mutation", "no flagged declaration was reachable",
                     "run C1--C3, then declare a vacuous analogue from the archive's own source"),
        )
        return (
            build_report(
                claim=claim,
                target=theorem,
                module=module,
                computations=computations,
                kernel=Verdict.VALIDATED_TERM,
                notes=(
                    f"archive not available at {archive}",
                    "the kernel verdict is the recorded replay of 2026-11-22, not a re-execution",
                ),
            ),
            computations[0],
            computations[1],
        )

    target = archive / "Audit" / "DependencyTrace.lean"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO_ROOT / "lean" / "RiemannFramework" / "DependencyTrace.lean", target)
    first, second = _trace_pair(archive, module, theorem, (), timeout, "Audit.DependencyTrace")
    c1, c2, c3 = _computations(first, second, c2_note="laud graph is not available; #depsm is the substitute")
    c4 = _not_run(
        "C4", "vacuous-analogue mutation",
        "no vacuous analogue has been declared from the archive's own sources yet",
        "for every flagged declaration in the closure, replace its body with a vacuous analogue "
        "in a copy of the archive, recompile the target, and record the outcome",
    )
    return (
        build_report(
            claim=claim,
            target=theorem,
            module=module,
            computations=(c1, c2, c3, c4),
            kernel=Verdict.VALIDATED_TERM,
            notes=("C4 not run: the record's only mutant is marked NOT CHECKED HERE",),
        ),
        c1,
        c2,
    )


def control_mode(*, claim: str, timeout: int):
    source = (REPO_ROOT / "lean" / "RiemannFramework" / "Dispute.lean").read_text(encoding="utf-8")
    flags = census_flags(source)
    theorem = "geometry_is_vacuous"
    # The file declares its names inside the RiemannFramework namespace, so the trace needs
    # the fully qualified constant: Environment.find? does not resolve an unqualified name.
    trace_theorem = "RiemannFramework.geometry_is_vacuous"
    module = "RiemannFramework.Dispute"
    first, second = _trace_pair(REPO_ROOT, module, trace_theorem, tuple(flags), timeout, TRACE_MODULE)
    c1, c2, c3 = _computations(
        first, second,
        c2_note="laud graph is not available; #depsm is the repository's second traversal over the same environment",
    )

    outcomes = []
    calibration = ""
    try:
        for mutant in load_mutants(CLAIMS, role=LIVE_ROLE):
            if mutant.theorem.split(".")[-1] == theorem:
                outcome = run_mutant(REPO_ROOT, mutant, timeout=timeout)
                outcomes.append(outcome)
                calibration = (
                    f"{outcome.mutant.id}: {'survived' if outcome.survived else 'killed'}"
                    + (f" ({outcome.reason})" if outcome.reason else "")
                )
    except SystemExit as error:  # pragma: no cover - Lean unavailable
        calibration = str(error)

    c4 = _not_run(
        "C4", "vacuous-analogue mutation",
        "the declared mutants for this theorem are content flips, not vacuous analogues; the flip "
        f"is recorded as engine calibration ({calibration or 'not run'})",
        "declare a vacuous-analogue mutant for each flagged declaration and re-run",
    )
    computations = (c1, c2, c3, c4)
    report = build_report(
        claim=claim,
        target=theorem,
        module=module,
        computations=computations,
        outcomes=outcomes,
        flags=flags,
        closure=first[1].get("names", ()) if c1.ran else (),
        critical_by_inspection=("vacuousGeometry",),
        kernel=Verdict.UNDETERMINED,
        notes=(
            "kernel withheld: the control file contains two deliberate `sorry`s (Dispute.lean), "
            "so this report demonstrates the closure and cross-validation, not the kernel",
            f"content-flip calibration: {calibration or 'not run'}",
        ),
    )
    return report, c1, c2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", default="alpoge_2026")
    parser.add_argument("--archive", type=Path, default=REPO_ROOT / "external" / "alpoge-lean")
    parser.add_argument("--local-control", action="store_true")
    parser.add_argument("--theorem", default="riemannHypothesis")
    parser.add_argument("--module", default="")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "out" / "gap_closer")
    args = parser.parse_args()

    if args.local_control:
        report, first, second = control_mode(claim=args.claim, timeout=args.timeout)
        out_dir = args.out / f"{args.claim}-control"
    else:
        report, first, second = archive_mode(
            args.archive, claim=args.claim, theorem=args.theorem, module=args.module, timeout=args.timeout
        )
        out_dir = args.out / args.claim

    hashes = write_artefacts(report, out_dir, first=first, second=second)
    print(f"claim: {report.claim}")
    print(f"target: {report.target} ({report.module or 'module not recorded'})")
    print(f"verdict: {report.verdict.value}")
    for item in report.computations:
        print(f"  {item.name} {item.status}: {item.detail}")
    for check in report.checks:
        print(f"  audit {'ok  ' if check.ok else 'FAIL'} {check.name}: {check.detail}")
    if report.named_computations:
        print("named computations:")
        for item in report.named_computations:
            print(f"  - {item}")
    print(f"written: {out_dir}")
    for name, digest in hashes.items():
        print(f"  {name} {digest[:16]}")
    print(STANDING)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
