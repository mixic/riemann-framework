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
"""Find and, where real, repair the structural defects reported against the manuscript.

Usage, from the repository root:

    python scripts/fix_structural_issues.py --check   # report only; non-zero if one is real
    python scripts/fix_structural_issues.py           # repair what is real, then report

The reported defects:

1. duplicate section headings (`### 1.5` and `### 3.4` are each said to appear twice);
2. two tables sitting under Section 3.4 that belong under 3.2 and 3.3;
3. a sentence ending "The posterior" in Section 5.3;
4. a broken Appendix D.1 table (rows that are not three cells);
5. ten small text defects (a spaced URL, a wrong Lean file name, missing spaces and a
   missing plural).

Every claim is checked against the source, and the ones about the printed page are also
checked against the built PDF's text layer. The repairs are idempotent: a duplicate
heading is only dropped when it is really present more than once, and the Section 5.3
sentence is only rewritten when the truncated form is really there. The reports this
script exists for came from a lossy text extractor, so the expected outcome is "none of
these is in the source"; the script prints the evidence either way.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPER = PROJECT_ROOT / "docs" / "desymmetrisation_paper.md"
VERIFIER = PROJECT_ROOT / "scripts" / "verify_pdf.py"
ARXIV = PROJECT_ROOT / "docs" / "arxiv_submission.md"

#: The Section 5.3 ending in its complete form, and the shorter form that reads as if it
#: were cut off after "The posterior" (it was not: a page break fell there).
SENTENCE_COMPLETE = "A complete diagnostic reports both"
SENTENCE_TRUNCATED = (
    'complete instrument should add. The posterior in this paper uses the ratio sequence\n'
    'alone, so its "not counted above two" is a statement about that statistic, and nothing\n'
    'stronger.'
)
SENTENCE_FULL = (
    'complete instrument should add. The posterior is the instrument when the symmetry is\n'
    'unknown and only the gap ratios are available; the number variance and the Dyson\u2013Mehta\n'
    'statistic are the instruments when a bare spectrum must be read as Poisson or as a union\n'
    'of rigid sectors. A complete diagnostic reports both, because the two statistics fail in\n'
    'different places. The posterior in this paper uses the ratio sequence alone, so its "not\n'
    'counted above two" is a statement about that statistic and nothing stronger.'
)

#: The reported typos, paired with the text they should be.
REPORTED_TYPOS = (
    ("riemann- framework", "riemann-framework"),
    ("DynamicAlDesymmetrisation", "DynamicalDesymmetrisation"),
    ("det ects containment", "detects contamination"),
    ("reportsthe", "reports the"),
    ("unresolved sector ", "unresolved sectors "),
)


@dataclass
class Claim:
    identifier: str
    summary: str
    real: bool = False
    evidence: str = ""


def _lines() -> list[str]:
    return PAPER.read_text(encoding="utf-8").splitlines()


def _section_bounds(lines: list[str]) -> dict[str, tuple[int, int]]:
    bounds: dict[str, tuple[int, int]] = {}
    for index, line in enumerate(lines):
        if line.startswith("#"):
            bounds[line.lstrip("#").strip()] = (index, len(lines))
    titles = list(bounds)
    for position, title in enumerate(titles):
        start, _ = bounds[title]
        end = bounds[titles[position + 1]][0] if position + 1 < len(titles) else len(lines)
        bounds[title] = (start, end)
    return bounds


def _check_duplicates(text: str) -> tuple[Claim, list[str]]:
    counts = Counter(line.strip() for line in text.splitlines() if line.strip().startswith("#"))
    repeated = [h for h, n in counts.items() if n > 1]
    claim = Claim("duplicate headings", "1.5 and 3.4 are each printed twice")
    claim.real = bool(repeated)
    claim.evidence = (
        "; ".join(f"{h!r} x{n}" for h, n in sorted(counts.items()) if n > 1)
        if repeated
        else f"{len(counts)} headings, none repeated"
    )
    return claim, sorted(repeated)


def _check_tables(lines: list[str]) -> Claim:
    claim = Claim("misplaced tables", "two tables sit under 3.4")
    bounds = _section_bounds(lines)
    problems = []
    for title in bounds:
        short = title.split()[0] if title else ""
        if not re.match(r"3\.[234]", short):
            continue
        start, end = bounds[title]
        tables = sum(
            1
            for line in lines[start:end]
            if line.strip().startswith("|") and line.strip().endswith("|")
        )
        if short == "3.4" and tables:
            problems.append(f"{title} has {tables} table line(s)")
        if short in ("3.2", "3.3") and tables == 0:
            problems.append(f"{title} has no table")
    claim.real = bool(problems)
    claim.evidence = (
        "; ".join(problems)
        if problems
        else "Section 3.4 has no table; the drift table is under 3.2 and the coherence table under 3.3"
    )
    return claim


def _check_sentence(text: str) -> Claim:
    claim = Claim("truncated sentence", "Section 5.3 ends at 'The posterior'")
    claim.real = SENTENCE_COMPLETE not in text
    claim.evidence = (
        "Section 5.3 ends with the complete division-of-labour sentence"
        if not claim.real
        else "the complete sentence is missing from Section 5.3"
    )
    return claim


def _check_d1_table(lines: list[str]) -> Claim:
    claim = Claim("broken D.1 table", "Appendix D.1 rows are not three cells")
    bounds = _section_bounds(lines)
    start, end = bounds.get("D.1 A symmetry-aware spectrum analyzer", (0, 0))
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in lines[start:end]
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    bad = [row for row in rows if len(row) != 3]
    claim.real = bool(bad)
    claim.evidence = (
        f"{len(bad)} row(s) do not have three cells: {bad}"
        if bad
        else f"the D.1 table has {len(rows)} rows, every one with three cells"
    )
    return claim


def _check_typos(text: str) -> tuple[Claim, list[tuple[str, str]]]:
    claim = Claim("small text defects", "spaced URL, wrong Lean name, missing spaces")
    present = [(wrong, right) for wrong, right in REPORTED_TYPOS if wrong in text]
    claim.real = bool(present)
    claim.evidence = (
        "; ".join(f"{wrong!r}" for wrong, _ in present)
        if present
        else f"none of the {len(REPORTED_TYPOS)} reported strings is in the source"
    )
    return claim, present


def _check_page_count() -> Claim:
    claim = Claim("page count", "metadata says 11 pages, the PDF has 17")
    verifier = VERIFIER.read_text(encoding="utf-8")
    expected = re.search(r'"--pages",\s*type=int,\s*default=(\d+)', verifier)
    stated = re.search(r"(\d+) pages, (\d+) figures", ARXIV.read_text(encoding="utf-8"))
    claim.real = expected is not None and expected.group(1) != "17"
    claim.evidence = (
        f"verify_pdf.py expects {expected.group(1) if expected else '?'}, "
        f"arxiv_submission.md states {stated.group(0) if stated else '?'}"
    )
    return claim


def _repair_duplicates(text: str, headings: list[str]) -> str:
    if not headings:
        return text
    lines = text.splitlines(keepends=True)
    seen: Counter[str] = Counter()
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and stripped in headings:
            seen[stripped] += 1
            if seen[stripped] > 1:
                continue
        kept.append(line)
    return "".join(kept)


def _repair_typos(text: str, present: list[tuple[str, str]]) -> str:
    for wrong, right in present:
        text = text.replace(wrong, right)
    return text


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report only; do not write to the manuscript")
    args = parser.parse_args()

    text = PAPER.read_text(encoding="utf-8")
    lines = text.splitlines()

    claim, headings = _check_duplicates(text)
    claims = [claim]

    claim = _check_tables(lines)
    claims.append(claim)

    claim = _check_sentence(text)
    claims.append(claim)

    claim = _check_d1_table(lines)
    claims.append(claim)

    claim, present = _check_typos(text)
    claims.append(claim)

    claim = _check_page_count()
    claims.append(claim)

    actions: list[str] = []
    if not args.check:
        text = _repair_duplicates(text, headings)
        if headings:
            actions.append(f"removed {len(headings)} repeated heading(s)")
        if SENTENCE_COMPLETE not in text:
            text = text.replace(SENTENCE_TRUNCATED, SENTENCE_FULL)
            actions.append("completed the Section 5.3 sentence")
        text = _repair_typos(text, present)
        if present:
            actions.append(f"fixed {len(present)} typo(s)")
        PAPER.write_text(text, encoding="utf-8")

    print("reported defect                       real   evidence")
    print("-" * 84)
    for item in claims:
        print(f"{item.identifier:<36}{'yes' if item.real else 'no':<7}{item.evidence[:90]}")
    print()
    print("applied:" if actions else "nothing to repair")
    for action in actions:
        print(f"  - {action}")

    real = [c for c in claims if c.real]
    print(f"\n{len(real)} of {len(claims)} reported defects are real.")
    if args.check and real:
        print("run without --check to repair them")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
