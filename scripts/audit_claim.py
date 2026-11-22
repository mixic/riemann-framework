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
"""Audit a claimed proof of the Riemann hypothesis, and write the report.

Usage, from the repository root:

    python scripts/audit_claim.py --claim claims/alpoge_2026.json
    python scripts/audit_claim.py --all --no-lean
    python scripts/audit_claim.py --claim claims/alpoge_2026.json --lean-root D:\\archives\\alpoge-lean

The report goes to `out/claims/<id>.md` and `out/claims/<id>.json` (git-ignored) and is
printed unless `--quiet`. Nothing printed here is a verdict on the Riemann hypothesis, and
the reports say so on their second line: the agent records what was checked, by which
instrument, with what trust base.

Exit codes: 0 when every report was written, 1 when a claim record could not be loaded or
audited, and, with `--strict`, 1 when any check in any report came back `checked_failed`.
`--strict` is for CI, where a failed check should be red; the default is 0 because a
report that documents a failure has done its job.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

from riemann_framework.claim_audit import (  # noqa: E402  (path set above)
    Claim,
    Status,
    audit_claim,
    load_claims,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit claimed proofs of the Riemann hypothesis: three levels, "
                    "five formal questions, no verdict on the hypothesis.",
    )
    parser.add_argument(
        "--claim", action="append", default=[],
        help="a claim record (JSON); repeatable",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="every record in the claims directory",
    )
    parser.add_argument(
        "--claims-dir", type=Path, default=PROJECT_ROOT / "claims",
        help="where the records live (default: claims/)",
    )
    parser.add_argument(
        "--out", type=Path, default=PROJECT_ROOT / "out" / "claims",
        help="where the reports are written (default: out/claims/)",
    )
    parser.add_argument(
        "--lean-root", type=Path, default=None,
        help="override the formal artefacts' root, for an archive kept elsewhere",
    )
    parser.add_argument(
        "--no-lean", action="store_true",
        help="replay the recorded formal evidence instead of compiling anything",
    )
    parser.add_argument(
        "--timeout", type=int, default=1800,
        help="seconds allowed for one Lean invocation (default: 1800)",
    )
    parser.add_argument("--quiet", action="store_true", help="write the files, print nothing")
    parser.add_argument(
        "--strict", action="store_true",
        help="exit 1 if any check came back checked_failed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # The reports quote Lean output, which contains `∀`, `→` and `ℂ`. A console whose
    # encoding is cp1252 raises on those, and a report that cannot be printed is a
    # report nobody runs; the files themselves are written as UTF-8 either way.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arguments = build_parser().parse_args(argv)
    claims: list[Claim] = [Claim.from_json(Path(item)) for item in arguments.claim]
    if arguments.all:
        claims.extend(load_claims(arguments.claims_dir))
    if not claims:
        print("no claim record given: pass --claim PATH or --all", file=sys.stderr)
        return 1

    arguments.out.mkdir(parents=True, exist_ok=True)
    failures = 0
    seen_claims: set[str] = set()
    for claim in claims:
        if claim.id in seen_claims:
            continue
        seen_claims.add(claim.id)
        report = audit_claim(
            claim,
            PROJECT_ROOT,
            live_lean=not arguments.no_lean,
            lean_root=arguments.lean_root,
            timeout=arguments.timeout,
        )
        markdown = report.render_markdown()
        (arguments.out / f"{claim.id}.md").write_text(markdown, encoding="utf-8")
        (arguments.out / f"{claim.id}.json").write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        failed = [
            finding for finding in report.findings
            if finding.status is Status.CHECKED_FAILED
        ]
        failures += len(failed)
        if not arguments.quiet:
            print(markdown)
        print(
            f"wrote {arguments.out / (claim.id + '.md')}: "
            f"panel `{report.panel.value}`, "
            f"{len(report.findings)} findings, {len(failed)} failed",
            file=sys.stderr,
        )
    if arguments.strict and failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
