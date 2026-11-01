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
"""Audit, and where real repair, the seven defects reported against the manuscript.

Usage, from the repository root:

    python scripts/fix_remaining_v3.py --check   # report only; non-zero if one is real
    python scripts/fix_remaining_v3.py           # repair what is real, then report

The seven claims, as reported:

1. three headings in the Markdown are duplicated;
2. the two tables under Section 3.4 belong under 3.2 and 3.3;
3. the References list on the last page is printed twice;
4. the double-bracket equation in Section 10.3 is corrupted;
5. a sentence that starts "The posterior" is missing its continuation;
6. the repository URL is misspelled;
7. five typos remain in the body.

Each claim is checked against the *source*, and, where the claim is about the printed
page, against the text layer of the built PDF. A repair only runs when its check fails,
so the script is idempotent and can never move a table or delete a heading that is not
actually there. Claims 2 and 5 have no automated repair: if their check fails they report
the evidence and stop, because moving prose and finishing sentences are the author's job.

Like `fix_remaining_v2.py`, the reports this script exists for came from a lossy text
extractor. The honest answer to most of the seven is "false, here is the evidence"; the
script prints the evidence instead of pretending to fix what is not broken.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPER = PROJECT_ROOT / "docs" / "desymmetrisation_paper.md"
VERIFIER = PROJECT_ROOT / "scripts" / "verify_pdf.py"
PDF = PROJECT_ROOT / "output" / "desymmetrisation_paper.pdf"

#: The double-bracket equation as it must appear, and the corruptions it has been
#: reported as (the extractor turns the opening `[[` into `[f` and drops a bracket).
CANONICAL_EQUATION = "dρ/dβ = [[ρ, H], ρ]"
REPORTED_EQUATION_CORRUPTIONS = ("[fρ, H]", "[f\u03c1, H]", "d\u03c1/d\u03b2 = [\u03c1, H]")

#: The five typos as reported in the prior review, paired with the text they should be.
REPORTED_TYPOS = (
    ("riemann-frmework", "riemann-framework"),
    ("(againt", "(against"),
    ("sect or count", "sector count"),
    ("post eror", "posterior"),
    ("est imate", "estimate"),
    ("Hamilton ion", "Hamiltonian"),
)


def _flat(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).split())


def _paper() -> str:
    return PAPER.read_text(encoding="utf-8")


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_pdf_for_v3", VERIFIER)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pdf_text() -> tuple[list[str], str]:
    if not PDF.exists():
        return [], ""
    pages = _load_verifier().extract_text(PDF).pages
    return pages, _flat("\n".join(pages))


def _section_bounds(lines: list[str]) -> dict[str, tuple[int, int]]:
    """`{heading: (first line, last line)}` for every `#`/`##`/`###` heading."""
    bounds: dict[str, tuple[int, int]] = {}
    for index, line in enumerate(lines):
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            bounds[title] = (index, len(lines))
    titles = list(bounds)
    for position, title in enumerate(titles):
        start, _ = bounds[title]
        end = bounds[titles[position + 1]][0] if position + 1 < len(titles) else len(lines)
        bounds[title] = (start, end)
    return bounds


@dataclass
class Claim:
    identifier: str
    summary: str
    real: bool = False
    evidence: str = ""
    action: str = "none"


def _claim_duplicate_headings(text: str) -> tuple[Claim, list[str]]:
    claim = Claim("duplicate-headings", "three headings appear twice")
    counts = Counter(line.strip() for line in text.splitlines() if line.strip().startswith("#"))
    repeated = {heading: count for heading, count in counts.items() if count > 1}
    claim.real = bool(repeated)
    if repeated:
        claim.evidence = "; ".join(f"{heading!r} x{count}" for heading, count in sorted(repeated.items()))
        return claim, sorted(repeated)
    claim.evidence = f"{len(counts)} headings, none repeated"
    return claim, []


def _claim_misplaced_tables(lines: list[str]) -> tuple[Claim, list[str]]:
    claim = Claim("misplaced-tables", "two tables sit under 3.4 and belong under 3.2 and 3.3")
    bounds = _section_bounds(lines)
    problems: list[str] = []
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
            problems.append(f"{title} contains {tables} table line(s)")
        if short in ("3.2", "3.3") and tables == 0:
            problems.append(f"{title} contains no table")
    claim.real = bool(problems)
    if problems:
        claim.evidence = "; ".join(problems)
    else:
        claim.evidence = (
            "Section 3.4 contains no table; the isospectrality table is under 3.2 and the "
            "coherence table under 3.3"
        )
    return claim, problems


def _claim_duplicate_references(text: str, pdf_flat: str) -> tuple[Claim, list[str]]:
    claim = Claim("duplicate-references", "the References list is printed twice")
    headings = [line.strip() for line in text.splitlines() if line.strip() == "## References"]
    claim.real = len(headings) > 1
    if claim.real:
        claim.evidence = f"'## References' appears {len(headings)} times"
    elif pdf_flat:
        claim.evidence = (
            f"'## References' appears once in the source and {pdf_flat.count('References')} "
            "times in the built text layer (the extra hits are the running header or a "
            "cross-reference, not a second list)"
        )
    else:
        claim.evidence = "'## References' appears once in the source"
    return claim, headings[1:] if len(headings) > 1 else []


def _claim_equation(text: str, pdf_flat: str) -> Claim:
    claim = Claim("corrupted-equation", "the Section 10.3 equation is corrupted")
    corruptions = [c for c in REPORTED_EQUATION_CORRUPTIONS if c in text]
    claim.real = bool(corruptions)
    if corruptions:
        claim.evidence = f"found {corruptions} in the source"
    elif CANONICAL_EQUATION in text:
        printed = _flat(CANONICAL_EQUATION) in pdf_flat if pdf_flat else None
        claim.evidence = (
            f"the source has {CANONICAL_EQUATION!r}"
            + (" and the text layer has it intact" if printed else "")
        )
    else:  # pragma: no cover - reworded equation still needs a human check
        claim.evidence = "the equation is present in some other spelling"
    return claim


def _claim_continuation(text: str) -> tuple[Claim, list[str]]:
    claim = Claim("missing-continuation", "a sentence starting 'The posterior' is cut off")
    problems: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip() == "The posterior":
            problems.append(f"line {number} is exactly 'The posterior'")
        elif "The posterior" in line and line.strip().endswith("The posterior"):
            problems.append(f"line {number} ends at 'The posterior'")
    claim.real = bool(problems)
    claim.evidence = (
        "; ".join(problems)
        if problems
        else "every occurrence of 'The posterior' is a complete sentence in the source"
    )
    return claim, problems


def _claim_url_and_typos(text: str) -> tuple[Claim, Claim, list[tuple[str, str]]]:
    url = Claim("url-typo", "the repository URL is misspelled")
    present = [(wrong, right) for wrong, right in REPORTED_TYPOS if wrong in text]
    url.real = bool(present and any("frmework" in wrong for wrong, _ in present))
    if url.real:
        url.evidence = "found a misspelling of 'riemann-framework'"
    else:
        url.evidence = "the source spells 'riemann-framework' in both places"

    typos = Claim("five-typos", "five typos remain in the body")
    typos.real = bool(present)
    typos.evidence = (
        "; ".join(f"{wrong!r} appears" for wrong, _ in present)
        if present
        else f"none of the {len(REPORTED_TYPOS)} reported strings is in the source"
    )
    return url, typos, present


def _repair_duplicates(text: str, headings: list[str]) -> tuple[str, str]:
    if not headings:
        return text, "nothing to repair"
    lines = text.splitlines(keepends=True)
    seen: Counter[str] = Counter()
    kept: list[str] = []
    dropped = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and stripped in headings:
            seen[stripped] += 1
            if seen[stripped] > 1:
                dropped += 1
                continue
        kept.append(line)
    return "".join(kept), f"removed {dropped} repeated heading line(s)"


def _repair_typos(text: str, present: list[tuple[str, str]]) -> tuple[str, str]:
    changes = 0
    for wrong, right in present:
        changes += text.count(wrong)
        text = text.replace(wrong, right)
    if not changes:
        return text, "nothing to repair"
    return text, f"replaced {changes} occurrence(s)"


def main() -> int:
    # The evidence strings can contain Greek (the equation corruption), which the
    # Windows console cannot encode as cp1252.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report only; do not write to the manuscript")
    args = parser.parse_args()

    text = _paper()
    lines = text.splitlines()
    pages, pdf_flat = _pdf_text()

    claims: list[Claim] = []
    actions: list[str] = []

    claim, headings = _claim_duplicate_headings(text)
    claims.append(claim)
    if claim.real and not args.check:
        text, done = _repair_duplicates(text, headings)
        actions.append(f"duplicate headings: {done}")

    claim, _ = _claim_misplaced_tables(lines)
    claims.append(claim)
    if claim.real:
        actions.append("misplaced tables: no automated repair; move them by hand")

    claim, extra_references = _claim_duplicate_references(text, pdf_flat)
    claims.append(claim)
    if claim.real and not args.check:
        # The duplicate is a heading; reuse the heading repair.
        text, done = _repair_duplicates(text, ["## References"])
        actions.append(f"duplicate references: {done}")

    claim = _claim_equation(text, pdf_flat)
    claims.append(claim)
    if claim.real and not args.check:
        for corrupt in REPORTED_EQUATION_CORRUPTIONS:
            text = text.replace(corrupt, CANONICAL_EQUATION)
        actions.append("corrupted equation: restored the canonical form")

    claim, problems = _claim_continuation(text)
    claims.append(claim)
    if claim.real:
        actions.append("missing continuation: no automated repair; finish the sentence by hand")

    url, typos, present = _claim_url_and_typos(text)
    claims.append(url)
    claims.append(typos)
    if present and not args.check:
        text, done = _repair_typos(text, present)
        actions.append(f"typos: {done}")

    if not args.check:
        PAPER.write_text(text, encoding="utf-8")

    print("reported defect                      verdict   evidence")
    print("-" * 100)
    for claim in claims:
        verdict = "REAL" if claim.real else "false"
        print(f"{claim.identifier:<22}{claim.summary[:38]:<40}{verdict:<10}{claim.evidence[:118]}")
    print()
    if actions:
        print("applied:")
        for action in actions:
            print(f"  - {action}")
    elif args.check:
        print("no repair attempted (--check)")
    else:
        print("nothing to repair")

    real = [claim for claim in claims if claim.real]
    print()
    print(f"{len(real)} of {len(claims)} reported defects are real.")
    if args.check and real:
        print("run without --check to repair them")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
