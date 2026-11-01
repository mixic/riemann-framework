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
"""Typeset the desymmetrisation manuscript as a submission PDF.

Usage, from the repository root:

    python scripts/build_manuscript_pdf.py \
        --author "Milan Nikolic" \
        --affiliation "Independent researcher" \
        --email "name@example.org"

Writes `output/desymmetrisation_paper.pdf`.

There is no LaTeX or pandoc on the machines this was built for, so the pipeline is:
Markdown -> HTML (a small converter that understands exactly the subset the manuscript
uses) -> headless Chrome/Edge -> PDF. The HTML is self-contained: the figures are
embedded as base64, so the intermediate file can be deleted and the PDF is independent
of the working directory.

What is stripped for a submission copy, per `docs/arxiv_submission.md`:

* the licence comment at the top of the Markdown (it belongs to the code, not the paper);
* the draft-status banner and the "Methods manuscript — draft for submission" line;
* the "A note on this draft" section (use `--keep-draft-note` to retain it).

The abstract used in the PDF is the manuscript's own. It is over the arXiv listing's
word guide; `docs/arxiv_submission.md` holds the 196-word version to paste into the
submission form, because the listing abstract and the paper's abstract need not match.
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = PROJECT_ROOT / "docs" / "desymmetrisation_paper.md"
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "desymmetrisation_paper.pdf"

BROWSERS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

CSS = """
@page { size: A4; margin: 24mm 21mm 24mm 21mm; }
html { font-size: 10.4pt; }
body {
  font-family: "Charter", "Bitstream Charter", "Georgia", "DejaVu Serif", serif;
  line-height: 1.46; text-align: justify; hyphens: auto; color: #111;
  margin: 0; max-width: 100%;
}
header.title { text-align: center; margin: 0 0 2.2em 0; }
header.title h1 { font-size: 19pt; line-height: 1.22; margin: 0 0 0.7em 0; font-weight: 700; }
header.title .authors { font-size: 11.5pt; margin: 0.2em 0 0.1em 0; }
header.title .affiliation { font-size: 9.6pt; color: #333; margin: 0.15em 0; }
header.title .date { font-size: 9.6pt; color: #444; margin-top: 0.9em; }
h1, h2, h3, h4 { font-weight: 700; text-align: left; page-break-after: avoid; }
h2 { font-size: 12.6pt; margin: 1.55em 0 0.5em 0; }
h3 { font-size: 11pt; margin: 1.2em 0 0.4em 0; }
h4 { font-size: 10.4pt; margin: 1em 0 0.35em 0; font-style: italic; }
p { margin: 0 0 0.62em 0; orphans: 2; widows: 2; }
ul, ol { margin: 0.1em 0 0.7em 0; padding-left: 1.5em; }
li { margin: 0.12em 0; }
strong { font-weight: 700; }
code { font-family: "DejaVu Sans Mono", "Consolas", monospace; font-size: 0.9em;
       background: #f4f4f4; padding: 0 0.16em; border-radius: 2px; }
pre { font-family: "DejaVu Sans Mono", "Consolas", monospace; font-size: 8.8pt;
      background: #f6f6f4; border-left: 2.5pt solid #bbb; padding: 0.5em 0.7em;
      margin: 0.5em 0 0.8em 0; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 1em; }
table { border-collapse: collapse; width: 100%; margin: 0.55em 0 0.9em 0;
        font-size: 9.3pt; page-break-inside: avoid; }
thead { border-top: 1.3pt solid #222; border-bottom: 0.7pt solid #222; }
tbody tr:last-child { border-bottom: 1.3pt solid #222; }
th { text-align: left; font-weight: 700; padding: 0.28em 0.45em; vertical-align: bottom; }
td { padding: 0.24em 0.45em; vertical-align: top; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
blockquote { margin: 0.6em 0 0.8em 1.2em; padding-left: 0.8em;
             border-left: 2pt solid #ccc; color: #222; font-style: italic; }
figure { margin: 0.9em 0 1.1em 0; page-break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 108mm; }
figcaption { font-size: 9pt; text-align: justify; margin-top: 0.45em; color: #1a1a1a; }
hr { border: none; border-top: 0.7pt solid #999; margin: 1.6em auto; width: 40%; }
a { color: #111; text-decoration: none; }
.small { font-size: 9pt; }
footer.end { margin-top: 2.4em; font-size: 9pt; color: #333; text-align: center; }
"""


# ============================================================
# Markdown -> HTML, for the subset this manuscript uses
# ============================================================

def strip_front_matter(text: str) -> str:
    """Remove the licence comment, the draft banner, and the note section."""
    text = re.sub(r"\A\s*<!--.*?-->\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"###\s*Methods manuscript.*?\n", "", text, count=1)
    text = re.sub(r"\*\*Status\.\*\*.*?\n\n", "", text, count=1, flags=re.DOTALL)
    return text


def strip_draft_note(text: str) -> str:
    """Drop the "A note on this draft" section, up to the next level-2 heading."""
    return re.sub(
        r"\n## A note on this draft\n.*?(?=\n## )", "\n", text, flags=re.DOTALL
    )


def inline_markup(text: str) -> str:
    """Escape, then apply code spans, emphasis and links."""
    placeholders: list[str] = []

    def stash(match: re.Match[str]) -> str:
        placeholders.append(
            "<code>" + html.escape(match.group(1), quote=False) + "</code>"
        )
        return f"\x00{len(placeholders) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)

    def link(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        if target.endswith(".md") or target.startswith("#"):
            # Repository cross-references have no meaning in the PDF.
            return label
        return f'<a href="{html.escape(target, quote=True)}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    for index, fragment in enumerate(placeholders):
        text = text.replace(f"\x00{index}\x00", fragment)
    return text


def table_rows(lines: list[str]) -> str:
    header = [cell.strip() for cell in lines[0].strip().strip("|").split("|")]
    align = [cell.strip() for cell in lines[1].strip().strip("|").split("|")]
    numeric = [spec.startswith("---:") or spec.endswith(":---") for spec in align]
    out = ["<table>", "<thead><tr>"]
    for cell, is_numeric in zip(header, numeric):
        cls = ' class="num"' if is_numeric else ""
        out.append(f"<th{cls}>{inline_markup(cell)}</th>")
    out.append("</tr></thead><tbody>")
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        out.append("<tr>")
        for index, cell in enumerate(cells):
            is_numeric = numeric[index] if index < len(numeric) else False
            cls = ' class="num"' if is_numeric else ""
            out.append(f"<td{cls}>{inline_markup(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def figure(path: str, caption: str) -> str:
    """Embed the image as base64 so the HTML is self-contained."""
    image_path = (PROJECT_ROOT / path).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"figure not found: {path}")
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return (
        "<figure>"
        f'<img src="data:image/png;base64,{encoded}" alt="{html.escape(caption, quote=True)}">'
        f"<figcaption>{inline_markup(caption)}</figcaption>"
        "</figure>"
    )


def convert(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    index = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append(f"<p>{inline_markup(' '.join(paragraph).strip())}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            block: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            index += 1
            out.append("<pre><code>" + html.escape("\n".join(block)) + "</code></pre>")
            continue

        if stripped.startswith("!["):
            flush_paragraph()
            match = re.match(r"!\[(.*)\]\((.*)\)\s*$", stripped)
            if not match:
                raise ValueError(f"malformed image line: {stripped[:80]}")
            out.append(figure(match.group(2), match.group(1)))
            index += 1
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            out.append(f"<h{level}>{inline_markup(stripped[level:].strip())}</h{level}>")
            index += 1
            continue

        if stripped == "---":
            flush_paragraph()
            out.append("<hr>")
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and re.match(
            r"^\|[\s:|-]+\|$", lines[index + 1].strip()
        ):
            flush_paragraph()
            block = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                block.append(lines[index])
                index += 1
            out.append(table_rows(block))
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quoted = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quoted.append(lines[index].strip().lstrip(">").strip())
                index += 1
            out.append(f"<blockquote>{inline_markup(' '.join(quoted))}</blockquote>")
            continue

        list_match = re.match(r"^(\s*)([-*]|\d+\.)\s+", line)
        if list_match:
            flush_paragraph()
            ordered = bool(re.match(r"^\s*\d+\.", line))
            tag = "ol" if ordered else "ul"
            items: list[str] = []
            while index < len(lines):
                match = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[index])
                if not match:
                    if lines[index].strip() and lines[index].startswith("  "):
                        items[-1] = items[-1] + " " + lines[index].strip()
                        index += 1
                        continue
                    break
                items.append(match.group(3).strip())
                index += 1
            body = "".join(f"<li>{inline_markup(item)}</li>" for item in items)
            out.append(f"<{tag}>{body}</{tag}>")
            continue

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    return "\n".join(out)


def find_browser(explicit: str | None) -> str:
    if explicit:
        if Path(explicit).exists() or shutil.which(explicit):
            return explicit
        raise FileNotFoundError(f"browser not found: {explicit}")
    for candidate in BROWSERS:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError(
        "no Chrome or Edge found; pass --browser with the executable path"
    )


def build_html(markdown: str, authors: list[str], affiliation: str | None,
               email: str | None, date: str | None) -> str:
    title_match = re.search(r"^# (.+)$", markdown, flags=re.MULTILINE)
    if not title_match:
        raise ValueError("the manuscript has no level-1 title")
    title = title_match.group(1).strip()
    body_markdown = markdown.replace(title_match.group(0), "", 1)

    author_line = ", ".join(authors)
    details = ""
    if affiliation:
        details += f'<div class="affiliation">{html.escape(affiliation)}</div>'
    if email:
        details += f'<div class="affiliation">{html.escape(email)}</div>'
    date_line = f'<div class="date">{html.escape(date)}</div>' if date else ""

    header = (
        '<header class="title">'
        f"<h1>{inline_markup(title)}</h1>"
        f'<div class="authors">{html.escape(author_line)}</div>'
        f"{details}{date_line}"
        "</header>"
    )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(title)}</title>"
        f"<style>{CSS}</style></head><body>"
        f"{header}{convert(body_markdown)}"
        "</body></html>"
    )


def print_to_pdf(browser: str, html_path: Path, pdf_path: Path) -> None:
    """Print with a headless Chromium.

    The browser needs a profile directory it can write. `tempfile.TemporaryDirectory`
    is avoided on purpose: on Windows sandboxes its cleanup calls `chmod`, which is
    denied, and the failure surfaces as a `PermissionError` *after* the PDF has been
    written. A directory next to the output is used instead and removed on a best-effort
    basis, so a locked file cannot fail the build.
    """
    profile = pdf_path.parent / ".pdf-profile"
    profile.mkdir(parents=True, exist_ok=True)
    command = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-first-run",
        "--disable-extensions",
        "--disable-dev-shm-usage",
        f"--user-data-dir={profile}",
        "--virtual-time-budget=15000",
        f"--print-to-pdf={pdf_path}",
        "--print-to-pdf-no-header",
        html_path.resolve().as_uri(),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=600)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not pdf_path.exists() or pdf_path.stat().st_size < 10_000:
        raise RuntimeError(
            "the browser did not produce a PDF:\n" + result.stdout + result.stderr
        )


def page_count(pdf_path: Path) -> int:
    """Count `/Type /Page` objects without a PDF library."""
    data = pdf_path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--author", action="append", default=[])
    parser.add_argument("--affiliation", default=None)
    parser.add_argument("--email", default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--browser", default=None)
    parser.add_argument("--keep-draft-note", action="store_true")
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="write the HTML and stop (for inspecting the layout without a browser)",
    )
    args = parser.parse_args()

    markdown = args.source.read_text(encoding="utf-8")
    markdown = strip_front_matter(markdown)
    if not args.keep_draft_note:
        markdown = strip_draft_note(markdown)

    authors = args.author or ["[author]"]
    html_text = build_html(markdown, authors, args.affiliation, args.email, args.date)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    html_path = args.output.with_suffix(".html")
    html_path.write_text(html_text, encoding="utf-8")
    print(f"html:    {html_path.relative_to(PROJECT_ROOT)} "
          f"({html_path.stat().st_size // 1024} kB, figures embedded)")
    if args.html_only:
        return

    browser = find_browser(args.browser)
    print(f"browser: {browser}")
    print_to_pdf(browser, html_path, args.output)
    html_path.unlink()

    size = args.output.stat().st_size
    print(f"pdf:     {args.output.relative_to(PROJECT_ROOT)} "
          f"({size // 1024} kB, {page_count(args.output)} pages)")


if __name__ == "__main__":
    sys.exit(main())
