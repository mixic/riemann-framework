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
"""Apply the five real fixes the manuscript needs before its next build.

Usage, from the repository root:

    python scripts/fix_reviewer_response.py --check   # report only; non-zero if one is real
    python scripts/fix_reviewer_response.py           # repair what is real, then report

The five issues:

1. a missing sentence: Section 10.5 opens with a bare bullet list and no lead-in;
2. an uncited identity: Section 4 attributes an identity to "the literature" but gives
   no source, and says the circuit was not read;
3. a misplaced section: Section 10 sits after the Conclusion, so the paper does not end
   on the Conclusion; it is moved to an appendix;
4. lab-notebook language: "residue of a larger project", "two mistakes made on the way",
   "a single seed ... once reported", "began as a mistake";
5. the repository URL.

Each fix is idempotent: it checks first and only rewrites what is actually there, so
running the script twice changes nothing the second time.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPER = PROJECT_ROOT / "docs" / "desymmetrisation_paper.md"

REPOSITORY_URL = "https://github.com/mixic/riemann-framework"


@dataclass
class Result:
    name: str
    applied: bool
    detail: str


def _fix_missing_sentence(text: str) -> tuple[str, Result]:
    """Give Section D.5's bullet list the lead-in sentence it is missing."""
    needle = "### D.5 Scope of the claims\n\n* the algorithm itself"
    if needle in text:
        text = text.replace(
            needle,
            "### D.5 Scope of the claims\n\nWhat the manuscript does **not** claim:\n\n* the algorithm itself",
        )
        return text, Result("missing sentence", True, "added a lead-in to the scope list")
    return text, Result("missing sentence", False, "the scope list already has its lead-in")


def _fix_uncited_identity(text: str) -> tuple[str, Result]:
    """Remove the un-citable 'the literature' framing from Section 4."""
    edits = (
        (
            "The literature's description of the multi-copy imaginary-time circuits quotes an identity\n"
            "for the first-order term:",
            "A description of the multi-copy imaginary-time circuits quotes an identity for the\n"
            "first-order term (the description has no citable source):",
        ),
        (
            "We tested it against the three natural generators",
            "The identity is tested against the three natural generators",
        ),
        (
            "The identity is therefore recorded as **unverified from the description available**, not\n"
            "as confirmed and not as refuted:",
            "The identity is therefore recorded as **unverified**, not as confirmed and not as\n"
            "refuted:",
        ),
    )
    applied = False
    for old, new in edits:
        if old in text:
            text = text.replace(old, new)
            applied = True
    return text, Result(
        "uncited identity",
        applied,
        "stated that the identity has no citable source and is tested as quoted",
    )


def _fix_lab_notebook(text: str) -> tuple[str, Result]:
    edits = (
        ("residue of a larger project", "product of a larger project"),
        ("Two mistakes made on the way", "Two errors made during that work"),
        ("once reported \"supported\"", "reported \"supported\""),
        ("began as a mistake made", "began as an error made"),
    )
    applied = 0
    for old, new in edits:
        if old in text:
            text = text.replace(old, new)
            applied += 1
    return text, Result(
        "lab-notebook language",
        applied > 0,
        f"reworded {applied} passage(s)",
    )


def _fix_url(text: str) -> tuple[str, Result]:
    if "riemann-frmework" in text or "riemann-framework" not in text:
        text = text.replace("riemann-frmework", "riemann-framework")
        return text, Result("URL", True, "restored the repository URL spelling")
    return text, Result(
        "URL",
        False,
        f"already correct: {REPOSITORY_URL!r} in both places",
    )


def _move_section_ten(text: str) -> tuple[str, Result]:
    """Move Section 10 (after the Conclusion) to an appendix after Appendix C."""
    lines = text.splitlines(keepends=True)

    section_start = next(
        (i for i, line in enumerate(lines) if line.startswith("## 10. Technical applications")),
        None,
    )
    if section_start is None:
        return text, Result("section move", False, "Section 10 already moved")

    appendix_start = next(
        i for i, line in enumerate(lines) if line.startswith("## Appendix A: The full measured table")
    )
    block = lines[section_start:appendix_start]
    renumbered = []
    for line in block:
        if line.startswith("## 10."):
            line = "## Appendix D: Technical applications and outlook\n"
        elif line.startswith("### 10."):
            line = re.sub(r"^### 10\.(\d)", r"### D.\1", line)
        line = line.replace("This section sketches,", "This appendix sketches,")
        renumbered.append(line)

    head = lines[:section_start]
    tail = lines[appendix_start:]

    # Appendix A, B, C end immediately before "## A note on this draft".
    note_index = next(
        i for i, line in enumerate(tail) if line.startswith("## A note on this draft")
    )
    tail = tail[:note_index] + renumbered + tail[note_index:]

    text = "".join(head + tail)
    text = text.replace(
        "Section 10's device descriptions", "Appendix D's device descriptions"
    )
    return text, Result(
        "section move",
        True,
        "moved Section 10 to Appendix D so the paper ends on the Conclusion",
    )


def _fix_fourth_column(text: str) -> tuple[str, Result]:
    """The scaled-floor column is the fifth, not the fourth (polish, found while fixing)."""
    if "The fourth column keeps the same" in text:
        text = text.replace(
            "The fourth column keeps the same",
            "The fifth column keeps the same",
        )
        return text, Result("column label", True, "fourth -> fifth (the scaled-floor column)")
    return text, Result("column label", False, "already labels the scaled-floor column correctly")


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report only; do not write to the manuscript")
    args = parser.parse_args()

    text = PAPER.read_text(encoding="utf-8")
    original = text
    results: list[Result] = []

    # The section move renames 10.5 to D.5, so it must run before the missing-sentence
    # fix, which targets the moved heading.
    for fix in (
        _fix_uncited_identity,
        _fix_lab_notebook,
        _fix_url,
        _move_section_ten,
        _fix_missing_sentence,
        _fix_fourth_column,
    ):
        text, result = fix(text)
        results.append(result)

    if not args.check and text != original:
        PAPER.write_text(text, encoding="utf-8")

    print("fix                                  applied   detail")
    print("-" * 78)
    for result in results:
        print(f"{result.name:<36}{'yes' if result.applied else 'no':<10}{result.detail}")
    print()

    applied = [r for r in results if r.applied]
    print(f"{len(applied)} of {len(results)} fixes applied.")
    if args.check and applied:
        print("run without --check to apply them")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
