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
"""Adjudicate a claimed formalisation: five probes, one aggregation, four artefacts.

Usage, from the repository root:

    python scripts/adjudicate.py --claim claims/alpoge_2026.json
    python scripts/adjudicate.py --claim claims/alpoge_2026.json --no-lean
    python scripts/adjudicate.py --claim claims/alpoge_2026.json --role "this repository's recording of the dispute (live)"

Writes `report.json`, `report.tex`, `dependency_graph.html` and `gap_statement.md` into
`out/adjudication/<claim>/` (git-ignored) and prints the probe table.

The final verdict is one of the six words the protocol allows, and `validated (term)` is
reachable only when the kernel probe, the dependency trace **and** the review agree while
no vacuity mutant survives. No single probe can promote the report, which is the point:
kernel acceptance is necessary and not sufficient, and the aggregation refuses on the
agent's behalf rather than relying on a reader to remember.

Exit codes: 0 when the artefacts were written, 1 when a claim record could not be loaded
or a mutant anchor was ambiguous. With `--strict`, 1 also when the aggregated verdict is
not `validated (term)`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

from riemann_framework.adjudicator import (  # noqa: E402  (path set above)
    AXIOM_TRAP_NOTE,
    STANDING_POSITION,
    Verdict,
    adjudicate,
    load_mutants,
    write_deliverables,
)
from riemann_framework.claim_audit import Claim  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Five probes on a claimed formalisation, aggregated by the "
                    "protocol's rule. No verdict here means the hypothesis is true.",
    )
    parser.add_argument("--claim", required=True, help="the claim record (JSON)")
    parser.add_argument(
        "--role", default=None,
        help="restrict the mutants to one formal target's role (default: all targets)",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="output directory (default: out/adjudication/<claim id>/)",
    )
    parser.add_argument(
        "--no-lean", action="store_true",
        help="skip compilation: the kernel and mutation probes report `not run`",
    )
    parser.add_argument(
        "--timeout", type=int, default=1800,
        help="seconds allowed for one Lean invocation (default: 1800)",
    )
    parser.add_argument("--quiet", action="store_true", help="write the files, print nothing")
    parser.add_argument(
        "--strict", action="store_true",
        help="exit 1 unless the aggregated verdict is `validated (term)`",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arguments = build_parser().parse_args(argv)
    path = Path(arguments.claim)
    try:
        claim = Claim.from_json(path)
        mutants = load_mutants(path, arguments.role)
    except (OSError, ValueError, KeyError) as error:
        print(f"{path}: {error}", file=sys.stderr)
        return 1
    try:
        result = adjudicate(
            claim,
            PROJECT_ROOT,
            mutants=mutants,
            live_lean=not arguments.no_lean,
            timeout=arguments.timeout,
            role=arguments.role,
        )
    except ValueError as error:
        print(f"{path}: {error}", file=sys.stderr)
        return 1
    out_dir = arguments.out or (
        PROJECT_ROOT / "out" / "adjudication" / claim.id
        / ("target-" + str(arguments.role).split(" (")[0].lower().replace(" ", "-")
           if arguments.role else "all-targets")
    )
    written = write_deliverables(result, out_dir)
    if not arguments.quiet:
        print(f"# Adjudication: {claim.title}")
        if result.role:
            print(f"**Artefact:** {result.role}")
        print()
        print("| probe | verdict | what would change it |")
        print("|:---|:---|:---|")
        for probe in result.probes:
            change = probe.named_computation or "decided"
            print(f"| `{probe.probe.value}` | `{probe.verdict.value}` | {change} |")
        print()
        print(f"**Aggregated verdict** `{result.final_verdict.value}`")
        print()
        counts = result.graph.counts()
        print(
            f"Graph: {counts.get('red', 0)} red, {counts.get('amber', 0)} amber, "
            f"{counts.get('green', 0)} green, {counts.get('grey', 0)} grey."
        )
        print()
        print(f"> {STANDING_POSITION}")
        print()
        print(f"> {AXIOM_TRAP_NOTE}")
    for name, written_path in written.items():
        print(f"wrote {written_path} ({name})", file=sys.stderr)
    if arguments.strict and result.final_verdict is not Verdict.VALIDATED_TERM:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
