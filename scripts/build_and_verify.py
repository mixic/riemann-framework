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
"""Build the manuscript PDF and verify it, stopping at the first failure.

Usage, from the repository root:

    python scripts/build_and_verify.py
    python scripts/build_and_verify.py --author "Milan Nikolic" \
        --affiliation "Independent Researcher" --email "m_nikolic@yahoo.com"

Two steps, in order:

1. `scripts/build_manuscript_pdf.py` — Markdown to LaTeX to `pdflatex` (or, without a
   TeX engine, Markdown to HTML to headless Chrome), writing
   `output/desymmetrisation_paper.pdf`;
2. `scripts/verify_pdf.py` — reads the PDF back and asserts 25 properties of it.

There is deliberately no "fix" step. A tool that rewrites prose is a tool that can
silently delete a sentence; the fixes for this manuscript are edits, and the guards that
catch a bad one are tests. What this script adds is the *sequence*: a build that is not
verified is a build of unknown status, and this makes the two commands one.

Exit status is 0 only if the PDF was written and every check passed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD = PROJECT_ROOT / "scripts" / "build_manuscript_pdf.py"
VERIFY = PROJECT_ROOT / "scripts" / "verify_pdf.py"
DEFAULT_PDF = PROJECT_ROOT / "output" / "desymmetrisation_paper.pdf"


def run(name: str, command: list[str], verbose: bool) -> tuple[bool, str]:
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)
    print("  $ " + " ".join(str(part) for part in command))
    print()
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        print("  FAILED: timed out after 900 seconds")
        return False, "TIMEOUT"

    output = result.stdout + result.stderr
    if verbose or result.returncode != 0:
        print(output)
    else:
        for line in output.strip().splitlines()[-25:]:
            print("  " + line)
    return result.returncode == 0, output


def main() -> int:
    # The verifier prints the manuscript's glyphs; a Windows console cannot encode them
    # by default, and the child's UTF-8 output would arrive here as mojibake. `reconfigure`
    # exists on the concrete streams but not on `TextIO`, so reach it through `getattr`.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError, OSError):  # pragma: no cover
                pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", action="append", default=[])
    parser.add_argument("--affiliation", default="Independent Researcher")
    parser.add_argument("--email", default="m_nikolic@yahoo.com")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--skip-build", action="store_true",
                        help="verify the existing PDF only")
    parser.add_argument("--skip-verify", action="store_true",
                        help="build only")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    authors = args.author or ["Milan Nikolic"]
    pdf = args.pdf.resolve()

    print("desymmetrisation manuscript: build and verify")

    if not args.skip_build:
        build_command = [sys.executable, str(BUILD), "--output", str(pdf)]
        for author in authors:
            build_command += ["--author", author]
        if args.affiliation:
            build_command += ["--affiliation", args.affiliation]
        if args.email:
            build_command += ["--email", args.email]
        ok, _ = run("1/2  build", build_command, args.verbose)
        if not ok:
            print()
            print("FAILED at the build. The PDF was not written.")
            return 1

    if not args.skip_verify:
        if not pdf.exists():
            print(f"\nFAILED: no PDF at {pdf}")
            return 1
        ok, output = run("2/2  verify", [sys.executable, str(VERIFY), "--pdf", str(pdf)],
                         args.verbose)
        if not ok:
            print()
            print("FAILED at the verification. The PDF exists but is not submittable.")
            print("The failing checks are listed above; fix the source and re-run.")
            return 1

    print()
    print("=" * 70)
    print("PASSED")
    print("=" * 70)
    print(f"  PDF:  {pdf.relative_to(PROJECT_ROOT)}")
    print(f"  Size: {pdf.stat().st_size // 1024} kB")
    print()
    print("  Not checked by any script: whether the pages look right.")
    print("  Open the PDF once before submitting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
