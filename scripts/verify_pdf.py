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
"""Verify the built manuscript PDF, including its text layer.

Usage, from the repository root:

    python scripts/verify_pdf.py
    python scripts/verify_pdf.py --pdf output/desymmetrisation_paper.pdf --strict

Why this exists. A PDF can be structurally perfect -- right page count, right page
size, four embedded images -- and still be unusable: it can carry a browser header on
every page, or its text layer can mangle the characters the abstract is made of. Neither
shows up in a byte-level check of the object table, and both are invisible to
`page_count`. So this script extracts the text the way a reader's "copy" would, and
checks the things a reader and a search index actually see.

There is no PDF library on the build machine, so the extractor below is a small one:
objects are uncompressed in the Chrome output, content streams are Flate, and every
subset font carries a `/ToUnicode` CMap. That is enough to recover the text, and the
recovery is exact enough to assert on.

Exit status: 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
import zlib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF = PROJECT_ROOT / "output" / "desymmetrisation_paper.pdf"

#: A4 in PDF points, with a little slack for rounding.
A4 = (594.96, 841.92)
A4_TOLERANCE = 1.5
PAGE_WIDTH = 595.276
TEXT_WIDTH = 595.276 - 2 * (2.1 / 2.54 * 72)  # the LaTeX text block, 476.2pt

#: Strings the submission copy must not contain.
FORBIDDEN = {
    # Naming the licence is normal attribution and appears in the data-availability
    # statement on purpose. What must not appear is the *boilerplate block*, and its
    # first sentence is the signature of that leak.
    "This program is free software": "the licence header belongs to the code, not the paper",
    "A note on this draft": "the corrections section is repository-only",
    "Status.": "the draft banner is repository-only",
    "file:///": "a file URL means the browser printed its own footer",
}

#: A browser header looks like `11/1/26, 8:13 AM`.
HEADER_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*(?:AM|PM)?", re.I)

#: The same thing in the flattened text, where spaces between glyph runs are gone.
HEADER_DATE_FLAT = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4},?\d{1,2}:\d{2}(?:AM|PM)?", re.I)

#: Characters the abstract is made of, checked with whitespace removed because the
#: extractor inserts spaces between text-showing operations.
EXPECTED_GLYPHS = {
    "⟨r⟩": "the mean gap ratio, in angle brackets",
    "≥6/poisson": "the open-ended posterior label",
    "1..1": "the single-sector interval",
    "2..2": "the modal two-sector interval",
    "3..≥6": "the modal three-or-more-sector interval",
}

#: Text that must be present because the paper is not submittable without it.
REQUIRED = {
    "Desymmetrization of Quantum Spectra": "the title",
    "Milan Nikolic": "the author",
    "Independent Researcher": "the affiliation",
    "m_nikolic@yahoo.com": "the contact address",
    # LaTeX numbers the floats itself, so the caption text begins "Figure N:" and the
    # Markdown's own "Fig. N." label is stripped at build time.
    "Figure 1:": "the first figure caption",
    "Figure 2:": "the second figure caption",
    "Figure 3:": "the third figure caption",
    "Figure 4:": "the fourth figure caption",
    "Figure 5:": "the fifth figure caption",
    "github.com/mixic/riemann-framework": "the repository every result is reproduced from",
}


# ============================================================
# A small PDF reader: enough for Chrome's output
# ============================================================

@dataclass
class PdfText:
    pages: list[str]
    pages_without_text: list[int]
    fonts: list[str]

    @property
    def text(self) -> str:
        return "\n".join(self.pages)

    @property
    def flat(self) -> str:
        """The text with whitespace removed and compatibility characters normalised.

        Two things have to be undone before a substring check means anything:

        * the extractor inserts a space between text-showing operations, so a kerned
          word arrives as `Ni k olic`;
        * a TeX math font maps its letters to *mathematical italic* code points, so `\\langle
          r\\rangle` extracts as `⟨𝑟⟩`, not `⟨r⟩`.

        NFKC folds the second, and the whitespace strip handles the first. The result is
        what a reader sees, which is what the assertions are about.
        """
        return re.sub(r"\s+", "", unicodedata.normalize("NFKC", self.text))


def _flat(needle: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", needle))


def _objects(data: bytes) -> dict[int, bytes]:
    """Every `N 0 obj ... endobj` body, keyed by object number."""
    found: dict[int, bytes] = {}
    for match in re.finditer(rb"(\d+)\s+0\s+obj(.*?)endobj", data, re.S):
        found[int(match.group(1))] = match.group(2)
    return found


def _stream(body: bytes) -> bytes | None:
    """The decoded stream of an object body, or None."""
    start = body.find(b"stream")
    if start < 0:
        return None
    start += len(b"stream")
    while start < len(body) and body[start] in (13, 10):
        start += 1
    end = body.find(b"endstream", start)
    if end < 0:
        return None
    raw = body[start:end].rstrip(b"\r\n")
    try:
        return zlib.decompress(raw)
    except zlib.error:
        return raw


def _refs(body: bytes, key: bytes) -> list[int]:
    """Object numbers named by `/key a 0 R` or `/key [a 0 R b 0 R]`."""
    match = re.search(rb"/" + key + rb"\s*(\[[^\]]*\]|\d+\s+0\s+R)", body)
    if not match:
        return []
    return [int(number) for number in re.findall(rb"(\d+)\s+0\s+R", match.group(1))]


def _parse_cmap(stream: bytes) -> dict[bytes, str]:
    """A `/ToUnicode` CMap: `beginbfchar` pairs and `beginbfrange` ranges."""
    mapping: dict[bytes, str] = {}

    for block in re.findall(rb"beginbfchar(.*?)endbfchar", stream, re.S):
        for source, target in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            mapping[bytes.fromhex(source.decode())] = bytes.fromhex(
                target.decode()
            ).decode("utf-16-be")

    for block in re.findall(rb"beginbfrange(.*?)endbfrange", stream, re.S):
        for match in re.finditer(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])",
            block,
        ):
            low = bytes.fromhex(match.group(1).decode())
            high = bytes.fromhex(match.group(2).decode())
            width = len(low)
            start = int.from_bytes(low, "big")
            stop = int.from_bytes(high, "big")
            target = match.group(3)
            if target.startswith(b"["):
                targets = re.findall(rb"<([0-9A-Fa-f]+)>", target)
                for offset, hex_code in enumerate(targets):
                    if start + offset > stop:
                        break
                    mapping[(start + offset).to_bytes(width, "big")] = bytes.fromhex(
                        hex_code.decode()
                    ).decode("utf-16-be")
            else:
                base = bytes.fromhex(target.strip(b"<>").decode())
                base_value = int.from_bytes(base, "big")
                for offset in range(stop - start + 1):
                    code = (start + offset).to_bytes(width, "big")
                    decoded = (base_value + offset).to_bytes(len(base), "big")
                    try:
                        mapping[code] = decoded.decode("utf-16-be")
                    except UnicodeDecodeError:  # pragma: no cover - odd CMaps
                        continue
    return mapping


def _string_literal(payload: bytes) -> bytes:
    """Decode a PDF `(...)` string, honouring the escapes Chrome emits."""
    out = bytearray()
    index = 0
    while index < len(payload):
        byte = payload[index]
        if byte != 0x5C:  # backslash
            out.append(byte)
            index += 1
            continue
        index += 1
        if index >= len(payload):
            break
        escape = payload[index]
        table = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
        if escape in table:
            out.append(table[escape])
            index += 1
        elif 0x30 <= escape <= 0x37:
            digits = payload[index:index + 3]
            taken = 0
            while taken < len(digits) and 0x30 <= digits[taken] <= 0x37:
                taken += 1
            out.append(int(digits[:taken], 8) & 0xFF)
            index += taken
        else:
            out.append(escape)
            index += 1
    return bytes(out)


def _strip_strings(payload: bytes) -> bytes:
    """Remove the contents of PDF strings, so operators inside text are not scanned."""
    return re.sub(rb"\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]+>", b" ", payload)


def image_placements(payload: bytes) -> list[tuple[str, float, float, float, float]]:
    """`(name, inner_width, effective_width, inner_height, effective_height)` per image.

    pdfTeX draws an included figure as `q <scale> cm q <natural> cm /ImN Do Q Q`. The
    effective width is the product; the inner width is what a viewer would draw if it
    ignored the outer matrix. Both matter: a page 6 figure whose natural width exceeded
    the page width rendered as a cropped wall of axis numbers in exactly such a viewer.
    """
    stack: list[tuple[float, float, float, float, float, float]] = []
    ctm = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    last = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    found: list[tuple[str, float, float, float, float]] = []
    pattern = re.compile(
        rb"q\b|Q\b|([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) cm"
        rb"|/([A-Za-z0-9]+) Do"
    )
    for match in pattern.finditer(_strip_strings(payload)):
        token = match.group(0)
        if token == b"q":
            stack.append(ctm)
        elif token == b"Q":
            ctm = stack.pop() if stack else (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        elif match.group(7) is not None:
            name = match.group(7).decode()
            found.append(
                (
                    name,
                    abs(last[0]),
                    abs(ctm[0]),
                    abs(last[3]),
                    abs(ctm[3]),
                )
            )
        else:
            matrix = (
                float(match.group(1)),
                float(match.group(2)),
                float(match.group(3)),
                float(match.group(4)),
                float(match.group(5)),
                float(match.group(6)),
            )
            last = matrix
            ctm = _compose(matrix, ctm)
    return found


def _compose(
    left: tuple[float, float, float, float, float, float],
    right: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    """`left` applied after `right`, in PDF's `a b c d e f` convention."""
    a1, b1, c1, d1, e1, f1 = left
    a2, b2, c2, d2, e2, f2 = right
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )

#: One text-showing operand: a `(...)` literal or a `<...>` hex string.
SHOW_PATTERN = re.compile(rb"\((?:[^()\\]|\\.|\((?:[^()\\]|\\.)*\))*\)|<[0-9A-Fa-f\s]+>")

#: A font selection (`/F3 9.96 Tf`) or a text-showing operation, in stream order.
TEXT_TOKEN = re.compile(
    rb"/([A-Za-z0-9]+)\s+[-\d.]+\s+Tf" + rb"|" + SHOW_PATTERN.pattern
)


def _decode_show(token: bytes, table: dict[bytes, str]) -> str:
    if token.startswith(b"<"):
        raw = bytes.fromhex(re.sub(rb"\s+", b"", token.strip(b"<>")).decode())
    else:
        raw = _string_literal(token[1:-1])
    # The CMap may be keyed by one byte or by two; try the longest key first.
    out: list[str] = []
    index = 0
    while index < len(raw):
        for width in (2, 1):
            chunk = raw[index:index + width]
            if chunk in table:
                out.append(table[chunk])
                index += width
                break
        else:
            out.append(chr(raw[index]) if 32 <= raw[index] < 127 else "")
            index += 1
    return "".join(out)


def _resources(body: bytes, objects: dict[int, bytes]) -> bytes:
    """The page's resource dictionary, whether written inline or by reference."""
    indirect = re.search(rb"/Resources\s+(\d+)\s+0\s+R", body)
    if indirect:
        return objects.get(int(indirect.group(1)), b"")
    return body


def _page_fonts(body: bytes, objects: dict[int, bytes]) -> dict[str, int]:
    """`{resource name: font object number}` for one page."""
    resources = _resources(body, objects)
    inner = re.search(rb"/Font\s*<<(.*?)>>", resources, re.S)
    if inner is None:
        inner = re.search(rb"/Font\s*<<(.*?)>>", body, re.S)
    if inner is None:
        return {}
    return {
        name.decode(): int(number)
        for name, number in re.findall(rb"/([A-Za-z0-9]+)\s+(\d+)\s+0\s+R", inner.group(1))
    }


def _font_table(font_object: int, objects: dict[int, bytes]) -> dict[bytes, str]:
    """The `/ToUnicode` table of one font. Per font, never merged: LaTeX uses several
    one-byte fonts whose codes collide, and a merged table garbles the text."""
    body = objects.get(font_object, b"")
    table: dict[bytes, str] = {}
    for reference in _refs(body, b"ToUnicode"):
        stream = _stream(objects.get(reference, b""))
        if stream:
            table.update(_parse_cmap(stream))
    return table


def extract_text(pdf: Path) -> PdfText:
    data = pdf.read_bytes()
    objects = _objects(data)

    fonts: list[str] = []
    for body in objects.values():
        if re.search(rb"/Type\s*/Font", body):
            name = re.search(rb"/BaseFont\s*/([A-Za-z0-9+\-]+)", body)
            if name:
                label = name.group(1).decode()
                if label not in fonts:
                    fonts.append(label)

    pages: list[str] = []
    empty: list[int] = []
    for number, body in objects.items():
        if not re.search(rb"/Type\s*/Page\b(?!s)", body):
            continue
        payload = b""
        for reference in _refs(body, b"Contents"):
            payload += _stream(objects.get(reference, b"")) or b""
        page_fonts = _page_fonts(body, objects)
        tables = {
            name: _font_table(font_object, objects)
            for name, font_object in page_fonts.items()
        }

        pieces: list[str] = []
        table: dict[bytes, str] = {}
        for match in TEXT_TOKEN.finditer(payload):
            if match.group(1) is not None:
                table = tables.get(match.group(1).decode(), {})
                continue
            pieces.append(_decode_show(match.group(0), table))

        page_text = re.sub(r"[ \t]+", " ", " ".join(pieces))
        pages.append(page_text)
        if not page_text.strip():
            empty.append(len(pages))

    return PdfText(pages=pages, pages_without_text=empty, fonts=sorted(fonts))


# ============================================================
# The checks
# ============================================================

@dataclass
class Check:
    name: str
    passed: bool
    detail: str

    def line(self) -> str:
        mark = "PASS" if self.passed else "FAIL"
        return f"  [{mark}] {self.name}: {self.detail}"


def check(pdf: Path, expected_pages: int, expected_images: int,
          strict: bool) -> list[Check]:
    data = pdf.read_bytes()
    objects = _objects(data)
    checks: list[Check] = []

    page_objects = re.findall(rb"/Type\s*/Page\b(?!s)", data)
    checks.append(
        Check("page count", len(page_objects) == expected_pages,
              f"{len(page_objects)} pages (expected {expected_pages})")
    )

    boxes = set(re.findall(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", data))
    if not boxes:
        checks.append(Check("page size", False, "no MediaBox found"))
    else:
        okay = all(
            abs(float(width) - A4[0]) <= A4_TOLERANCE
            and abs(float(height) - A4[1]) <= A4_TOLERANCE
            for _, _, width, height in boxes
        )
        checks.append(
            Check("page size", bool(okay),
                  f"A4" if okay else f"unexpected: {sorted(boxes)}")
        )

    images = len(re.findall(rb"/Subtype\s*/Image", data))
    masks = set(re.findall(rb"/SMask\s+(\d+)\s+0\s+R", data))
    # A PNG with an alpha channel becomes an image plus an /SMask image; the figures are
    # the images that are not themselves masks.
    pictures = 0
    for match in re.finditer(rb"(\d+)\s+0\s+obj(.*?)endobj", data, re.S):
        number = int(match.group(1))
        body = match.group(2)
        if re.search(rb"/Subtype\s*/Image", body) and str(number).encode() not in masks:
            pictures += 1
    checks.append(
        Check("embedded figures", pictures == expected_images,
              f"{pictures} pictures ({images} image objects, {len(masks)} masks; "
              f"expected {expected_images})")
    )

    text = extract_text(pdf)
    checks.append(
        Check("text layer", not text.pages_without_text,
              f"{len(text.pages)} pages, {len(text.flat)} characters"
              + (f"; empty pages: {text.pages_without_text}" if text.pages_without_text else ""))
    )

    # A browser header or footer is the failure this script exists for. The check runs on
    # the flattened text: Chrome's footer extracts with spaces between the characters,
    # so a pattern match on the spaced text misses it.
    date_hits = HEADER_DATE.findall(text.text) + HEADER_DATE_FLAT.findall(text.flat)
    checks.append(
        Check("no browser header", not date_hits,
              "no date/time stamp" if not date_hits else f"found {date_hits[:4]}")
    )

    # Figures must be placed inside the text block *and* have a natural size that a viewer
    # ignoring the outer transform would still draw inside the page. The second half is
    # what failed once: a 1500-pixel figure at 150 dpi is 720pt wide, and with the outer
    # scale ignored it was drawn cropped, filling page 6 with axis numbers.
    placements: list[tuple[str, float, float, float, float]] = []
    for number, body in objects.items():
        if not re.search(rb"/Type\s*/Page\b(?!s)", body):
            continue
        payload = b""
        for reference in _refs(body, b"Contents"):
            payload += _stream(objects.get(reference, b"")) or b""
        placements.extend(image_placements(payload))

    too_wide = [
        (name, effective, inner)
        for name, inner, effective, _, _ in placements
        if effective > TEXT_WIDTH + 1.0 or inner > PAGE_WIDTH + 1.0
    ]
    checks.append(
        Check(
            "figures fit the page",
            not too_wide,
            f"{len(placements)} placements within the text block and the page"
            if not too_wide
            else "too wide (name, effective, natural): " + str(too_wide),
        )
    )

    # A page whose text is mostly digits is the symptom of a broken build -- the axis
    # numbers of a mis-scaled figure, or a table rendered as a stream of values.
    floods = []
    for index, page in enumerate(text.pages, start=1):
        visible = [character for character in page if not character.isspace()]
        if len(visible) > 400 and sum(c.isdigit() for c in visible) / len(visible) > 0.5:
            floods.append(index)
    checks.append(
        Check("no page of numbers", not floods,
              "no page is dominated by digits" if not floods else f"pages {floods}")
    )

    for needle, why in FORBIDDEN.items():
        present = _flat(needle) in text.flat
        checks.append(
            Check(f"absent: {needle!r}", not present,
                  "absent" if not present else f"present ({why})")
        )

    for needle, why in REQUIRED.items():
        present = _flat(needle) in text.flat
        checks.append(
            Check(f"present: {needle!r}", present,
                  "present" if present else f"missing ({why})")
        )

    for needle, why in EXPECTED_GLYPHS.items():
        found = _flat(needle) in text.flat
        checks.append(
            Check(f"glyph: {needle}", found,
                  "renders" if found else f"not in the text layer ({why})")
        )

    # The fi/fl/ff ligatures were dropped from the text layer by a `cmap`/`fontenc`
    # ordering bug: "classifier" extracted as "classi er" and "flag" as "ag". The fix is
    # to load `cmap` before `fontenc` and set `\pdfgentounicode=1`; this check pins it.
    ligature_words = ("classifier", "flag", "effect", "difference", "fidelity", "reflects")
    checks.append(
        Check(
            "ligatures extract",
            all(_flat(word) in text.flat for word in ligature_words),
            "fi, fl and ff ligatures survive extraction",
        )
    )

    checks.append(
        Check(
            "figures captioned",
            all(f"Figure{index}:" in text.flat for index in (1, 2, 3, 4, 5)),
            "all five captions found",
        )
    )

    # A heading that carries its own label must not also receive a LaTeX number. When
    # Section 10 moved to an unnumbered appendix, `\subsection{D.1 ...}` printed as
    # "9.1 D.1 ..." (LaTeX numbered it from the last numbered section) and the unnumbered
    # Disclaimer printed as "10 Disclaimer". Both are invisible to a per-glyph check and
    # obvious to a reader, so the doubled label is looked for directly.
    doubled = re.findall(r"\d+\.\d+D\.\d", text.flat)
    numbered_tail = [token for token in ("9Disclaimer", "10Disclaimer", "11Disclaimer")
                     if token in text.flat]
    numbering_ok = not doubled and not numbered_tail
    checks.append(
        Check(
            "headings numbered once",
            numbering_ok,
            "no doubled heading label and no numbered Disclaimer"
            if numbering_ok
            else f"doubled labels: {doubled[:3]}; numbered tail: {numbered_tail}",
        )
    )

    if strict:
        # Report one suspicious pattern as a warning rather than a failure: a dot pair
        # that lost a dot is the known text-layer quirk, and it is worth surfacing.
        collapsed = re.findall(r"\b(\d)\.(\d)\b", text.text)
        checks.append(
            Check("no collapsed intervals", not collapsed,
                  "no `d.d` token" if not collapsed else f"found {collapsed[:4]}")
        )

    return checks


def main() -> int:
    # The manuscript is full of characters a Windows console cannot encode; without this
    # the report itself crashes on the glyph it is meant to check. `reconfigure` exists on
    # the concrete streams but not on `TextIO`, so it is reached through `getattr`.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError, OSError):  # pragma: no cover
                pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--pages", type=int, default=18)
    parser.add_argument("--images", type=int, default=5)
    parser.add_argument("--strict", action="store_true",
                        help="also fail on collapsed interval notation in the text layer")
    parser.add_argument("--dump-text", action="store_true",
                        help="print the extracted text (diagnostics)")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"FAIL: no PDF at {args.pdf}", file=sys.stderr)
        return 1
    args.pdf = args.pdf.resolve()

    checks = check(args.pdf, args.pages, args.images, args.strict)

    text = extract_text(args.pdf)
    if args.dump_text:
        # Whole pages, not a prefix. An earlier version printed the first 2000
        # characters, which is more than a page at this density by luck and less than a
        # page in practice: a heading that sat past the cut looked like a missing
        # heading, and a forensic dump that hides text is worse than none.
        for index, page in enumerate(text.pages, start=1):
            print(f"--- page {index} ({len(page)} characters) ---")
            print(page)
        print(f"--- fonts: {', '.join(text.fonts)}")

    print(f"verifying {args.pdf.relative_to(PROJECT_ROOT)}")
    print(f"  fonts: {', '.join(text.fonts)}")
    print()
    for item in checks:
        print(item.line())

    failures = [item for item in checks if not item.passed]
    print()
    if failures:
        print(f"FAIL: {len(failures)} of {len(checks)} checks failed")
        return 1
    print(f"PASS: all {len(checks)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
