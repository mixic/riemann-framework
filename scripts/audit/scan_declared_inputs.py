"""Reconcile a claim's textual mentions against its declared inputs.

The screens read declarations, and section 6 of the paper records the failure mode: an
omitted input moves the verdict without changing the argument. `input_omission` scans the
primary document's own text for the inventory's vocabulary and reports every mention the
declaration does not account for, either as declared or as excluded with a reason.

The output is a reconciliation, not a verdict: a mention is not a use, and a paraphrase that
avoids every listed phrase is invisible to the scan. An `unreconciled` row is the one that
matters, and it is a request for a decision about the argument, not a finding about it.

Usage (from the repository root):

    python scripts/audit/scan_declared_inputs.py
    python scripts/audit/scan_declared_inputs.py --pdf references/<document>.pdf --json out/x.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))

from riemann_framework.input_omission import PHRASES, ledger, reconcile  # noqa: E402


DEFAULT_PDF = Path("references/masullo_music_of_the_primes_2026-11-20.pdf")
CACHE = Path("out/audit/masullo_text.txt")


def extract_text(pdf: Path, cache: Path) -> str:
    """Text of the PDF, cached, because 940 pages take a while to extract."""
    if cache.is_file() and cache.stat().st_size > 0:
        return cache.read_text(encoding="utf-8", errors="replace")
    exe = shutil.which("pdftotext")
    if exe is None:
        raise SystemExit(
            "pdftotext not found. Install poppler-utils, or pass --text with a text extract."
        )
    cache.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [exe, "-enc", "UTF-8", str(pdf), str(cache)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return cache.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--text", type=Path, default=None, help="a text extract instead of the PDF")
    parser.add_argument("--json", type=Path, default=None, help="write the report as JSON")
    args = parser.parse_args()

    if args.text is not None:
        text = args.text.read_text(encoding="utf-8", errors="replace")
        source = args.text
    else:
        if not args.pdf.is_file():
            raise SystemExit(f"no document at {args.pdf}")
        text = extract_text(args.pdf, CACHE)
        source = CACHE

    report = reconcile(text)
    rows = [
        ("declared", report.declared),
        ("excluded", report.excluded),
        ("unreconciled", report.unreconciled),
    ]
    print(f"document: {source} ({len(text):,} characters)")
    print(f"{'class':<14}{'hypothesis':<32}{'mentions':>9}")
    for role, mentions in rows:
        for item in mentions:
            print(f"{role:<14}{item.key:<32}{item.count:>9}")
    print(f"\nstatus: {report.status}; mentions: {report.total_mentions}")
    details = ledger()
    for item in (*report.declared, *report.excluded):
        print(f"  {item.key}: {details[item.key]['where']}")
    if report.unmentioned:
        print("inventory hypotheses the text never names:")
        for key in report.unmentioned:
            print(f"  {key}  (phrases: {', '.join(PHRASES[key])})")
    if report.status == "unreconciled":
        print("\nAn unreconciled mention is not a verdict: resolve it as declared, or as")
        print("excluded with a reason, before the declaration is used by a screen.")

    payload = {
        "document": str(source),
        "characters": len(text),
        "phrases": {key: list(value) for key, value in PHRASES.items()},
        "report": report.summary(),
    }
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
