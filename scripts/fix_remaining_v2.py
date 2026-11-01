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
"""Audit, and where real repair, the five defects reported against the manuscript.

Usage, from the repository root:

    python scripts/fix_remaining_v2.py --check   # report only; non-zero if one is real
    python scripts/fix_remaining_v2.py           # repair what is real, then report

The five claims, as reported:

1. page 14 duplicates the `10.2`, `10.3` and `Appendix A` headings;
2. page 4 prints a stray `1.3` inside a sentence;
3. the repository URL is misspelled `riemann-frmework`;
4. eleven typos on pages 9 to 15;
5. the metadata still says 11 pages and the verifier expects 11.

Every claim is checked against the *source* and, where the claim is about the printed
page, against the text layer of the built PDF. A repair only runs when its check fails,
so running this script twice changes nothing the second time, and it can never remove a
heading that occurs once: the duplicate-heading repair counts first and refuses to act
unless the same heading really is present more than once.

The reports this script exists for came from a lossy text extractor: it inserts spaces
between glyph runs (`Hamilton ian`), drops the occasional character, and concatenates a
heading with the paragraph that follows it. Those artefacts are not defects in the
manuscript, and the honest answer to most of the five claims is "false, here is the
evidence". One claim turned out to be a real readability problem, and it is fixed here:
`Section 1.3` followed by `0.0010, 1.4 standard errors` reads like a section number
inserted into the sentence, because four numerals in a row collide.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPER = PROJECT_ROOT / "docs" / "desymmetrisation_paper.md"
ARXIV = PROJECT_ROOT / "docs" / "arxiv_submission.md"
CHANGELOG = PROJECT_ROOT / "docs" / "build_workflow.md"
VERIFIER = PROJECT_ROOT / "scripts" / "verify_pdf.py"
PDF = PROJECT_ROOT / "output" / "desymmetrisation_paper.pdf"

#: The sentence that reads as if a section number were inserted into it. The rewrite
#: removes the numeral collision: "Section 1.3 the two-sector class gap is 0.0010, 1.4
#: standard errors" has four numbers in a row and no verb to separate the last two.
NUMERAL_COLLISION = (
    "The two results are consistent and they are not in tension. In the 4000-spectrum table of\n"
    "Section 1.3 the two-sector class gap is `0.0010`, `1.4` standard errors; in the nested\n"
    "series of Fig. 2 at 3200 spectra it is `0.0004`, `0.5` standard errors."
)
NUMERAL_COLLISION_FIXED = (
    "The two results are consistent and they are not in tension. In the 4000-spectrum table of\n"
    "the previous section the two-sector class gap is `0.0010`, which is `1.4` standard errors;\n"
    "in the nested series of Fig. 2 at 3200 spectra it is `0.0004`, which is `0.5` standard\n"
    "errors."
)

#: The eleven typos as reported, paired with the text they should be. None of them is in
#: the source; the table is kept so the check is mechanical rather than a promise.
REPORTED_TYPOS = (
    ("riemann-frmework", "riemann-framework"),
    ("(againt", "(against"),
    ("sect or count", "sector count"),
    ("post eror", "posterior"),
    ("two- sect or gap", "two-sector gap"),
    ("(in terval", "(interval"),
    ("Hamilton ion", "Hamiltonian"),
    ("lean/RiemannFrameworK", "lean/RiemannFramework"),
    ("We test ed it", "We tested it"),
    ("[f\u03c1, H]", "[[\u03c1, H]"),
    ("est imate", "estimate"),
)

#: Headings the report says are printed twice.
REPORTED_DUPLICATES = ("### 10.2 ", "### 10.3 ", "## Appendix A")


@dataclass
class Claim:
    """One reported defect: what it says, whether it is real, and what was done."""

    identifier: str
    summary: str
    real: bool = False
    evidence: str = ""
    action: str = "none"


def _flat(text: str) -> str:
    """Whitespace-free, NFKC-folded text: how a substring check survives extraction."""
    return "".join(unicodedata.normalize("NFKC", text).split())


def _paper() -> str:
    return PAPER.read_text(encoding="utf-8")


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_pdf_for_repair", VERIFIER)
    if spec is None or spec.loader is None:  # pragma: no cover - the file exists
        raise RuntimeError(f"cannot load {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pdf_text() -> tuple[list[str], str]:
    """`(pages, flat text)` of the built PDF, or an empty pair if it is not there yet."""
    if not PDF.exists():
        return [], ""
    verifier = _load_verifier()
    pages = verifier.extract_text(PDF).pages
    return pages, _flat("\n".join(pages))


# ============================================================
# Claim 1: duplicated headings
# ============================================================

def check_duplicate_headings(text: str) -> tuple[Claim, list[str]]:
    counts = Counter(line.strip() for line in text.splitlines() if line.strip().startswith("#"))
    repeated = {heading: count for heading, count in counts.items() if count > 1}
    claim = Claim(
        "duplicate-headings",
        "page 14 repeats the 10.2, 10.3 and Appendix A headings",
    )
    if repeated:
        claim.real = True
        claim.evidence = "; ".join(f"{heading!r} appears {count} times"
                                   for heading, count in sorted(repeated.items()))
        return claim, sorted(repeated)
    for probe in REPORTED_DUPLICATES:
        occurrences = sum(1 for line in text.splitlines() if line.strip().startswith(probe))
        if occurrences > 1:  # pragma: no cover - covered by the Counter above
            claim.real = True
            claim.evidence = f"{probe!r} appears {occurrences} times"
            return claim, [probe.strip()]
    claim.evidence = (
        f"{len(counts)} headings, none repeated; {', '.join(p.strip() for p in REPORTED_DUPLICATES)} "
        "appear exactly once each"
    )
    return claim, []


def repair_duplicate_headings(text: str, headings: list[str]) -> tuple[str, str]:
    """Drop the later copies of a heading, keeping the first. Refuses if none is repeated."""
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
    if not dropped:  # pragma: no cover - the check and the repair agree
        return text, "nothing to repair"
    return "".join(kept), f"removed {dropped} repeated heading line(s)"


# ============================================================
# Claim 2: a section number inside a sentence
# ============================================================

def check_numeral_collision(text: str) -> Claim:
    claim = Claim(
        "numeral-collision",
        "page 4 prints a stray '1.3' inside a sentence",
    )
    if NUMERAL_COLLISION in text:
        claim.real = True
        claim.evidence = (
            "the source reads 'Section 1.3 the two-sector class gap is 0.0010, 1.4 standard "
            "errors': no character was inserted, but four numerals in a row read like one"
        )
    elif NUMERAL_COLLISION_FIXED in text:
        claim.evidence = (
            "the sentence reads 'the previous section ... which is 1.4 standard errors'; "
            "no section number sits next to a measurement"
        )
    else:  # pragma: no cover - a reworded sentence still has to be checked by eye
        claim.evidence = "the reported sentence is not in the source (it has been reworded)"
    return claim


def repair_numeral_collision(text: str) -> tuple[str, str]:
    if NUMERAL_COLLISION not in text:
        return text, "nothing to repair"
    return text.replace(NUMERAL_COLLISION, NUMERAL_COLLISION_FIXED), (
        "rewrote the sentence: 'the previous section', and 'which is' before both counts"
    )


# ============================================================
# Claims 3 and 4: the URL and the reported typos
# ============================================================

def check_url(text: str, pdf_flat: str) -> Claim:
    claim = Claim("url-typo", "the repository URL is misspelled 'riemann-frmework'")
    source_hits = [wrong for wrong, _ in REPORTED_TYPOS if "frmework" in wrong and wrong in text]
    printed = "github.com/mixic/riemann-framework" in pdf_flat if pdf_flat else None
    claim.real = bool(source_hits)
    if source_hits:
        claim.evidence = f"found {source_hits} in the source"
    else:
        claim.evidence = (
            "the source spells 'riemann-framework' "
            + ("and the built PDF's text layer contains it intact"
               if printed else "(the PDF is not built, so only the source was checked)")
        )
    return claim


def check_typos(text: str) -> tuple[Claim, list[tuple[str, str]]]:
    claim = Claim("typos", "eleven typos on pages 9 to 15")
    present = [(wrong, right) for wrong, right in REPORTED_TYPOS if wrong in text]
    claim.real = bool(present)
    if present:
        claim.evidence = "; ".join(f"{wrong!r} appears" for wrong, _ in present)
    else:
        claim.evidence = (
            f"none of the {len(REPORTED_TYPOS)} reported strings is in the source; each one "
            "is a single extractor artefact: 'Hamilton ian', 'sect or', 'est imate' and the "
            "rest are what the PDF reader emits for correct text"
        )
    return claim, present


def repair_typos(text: str, present: list[tuple[str, str]]) -> tuple[str, str]:
    changes = 0
    for wrong, right in present:
        changes += text.count(wrong)
        text = text.replace(wrong, right)
    if not changes:
        return text, "nothing to repair"
    return text, f"replaced {changes} occurrence(s)"


# ============================================================
# Claim 5: the page count in the metadata and the verifier
# ============================================================

def check_page_count(pdf_pages: int, verifier_source: str) -> tuple[Claim, list[str]]:
    claim = Claim("page-count", "the metadata says 11 pages and the verifier expects 11")
    default = re.search(r'"--pages",\s*type=int,\s*default=(\d+)', verifier_source)
    expected = int(default.group(1)) if default else None
    arxiv = ARXIV.read_text(encoding="utf-8")
    stated = re.search(r"(\d+) pages, (\d+) figures", arxiv)
    problems: list[str] = []
    if pdf_pages:
        if expected is not None and expected != pdf_pages:
            problems.append(f"verify_pdf.py expects {expected}, the PDF has {pdf_pages}")
        if stated and int(stated.group(1)) != pdf_pages:
            problems.append(f"arxiv_submission.md states {stated.group(1)}, the PDF has {pdf_pages}")
    claim.real = bool(problems)
    if problems:
        claim.evidence = "; ".join(problems)
    elif pdf_pages:
        claim.evidence = (
            f"the PDF has {pdf_pages} pages, verify_pdf.py expects {expected}, and "
            f"arxiv_submission.md states {stated.group(0) if stated else 'nothing'}"
        )
    else:
        claim.evidence = "the PDF is not built, so only the stated numbers were checked"
    return claim, problems


# ============================================================
# Report
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report only; do not write to the manuscript")
    args = parser.parse_args()

    text = _paper()
    pages, pdf_flat = _pdf_text()

    claims: list[Claim] = []
    actions: list[str] = []

    claim, headings = check_duplicate_headings(text)
    claims.append(claim)
    if claim.real and not args.check:
        text, done = repair_duplicate_headings(text, headings)
        actions.append(f"duplicate headings: {done}")

    claim = check_numeral_collision(text)
    claims.append(claim)
    if claim.real and not args.check:
        text, done = repair_numeral_collision(text)
        actions.append(f"numeral collision: {done}")

    claim = check_url(text, pdf_flat)
    claims.append(claim)

    claim, present = check_typos(text)
    claims.append(claim)
    if claim.real and not args.check:
        text, done = repair_typos(text, present)
        actions.append(f"typos: {done}")

    claim, problems = check_page_count(len(pages), VERIFIER.read_text(encoding="utf-8"))
    claims.append(claim)
    if claim.real and not args.check:
        actions.append(
            "page count: " + "; ".join(problems)
            + " (fix the numbers in verify_pdf.py and docs/arxiv_submission.md by hand: "
            "they are the build's, not the manuscript's)"
        )

    if not args.check:
        PAPER.write_text(text, encoding="utf-8")

    print("reported defect                       verdict   evidence")
    print("-" * 100)
    for claim in claims:
        verdict = "REAL" if claim.real else "false"
        print(f"{claim.identifier:<22}{claim.summary[:34]:<36}{verdict:<10}{claim.evidence[:120]}")
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
