<!--
Riemann Framework
Copyright (C) 2026 MILAN NIKOLIC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

# Build workflow: from Markdown to a verified PDF

The manuscript is written in Markdown (`docs/desymmetrisation_paper.md`) and typeset to
`output/desymmetrisation_paper.pdf`. This document describes the pipeline, what each stage
guarantees, and what has gone wrong before — because every check in it exists in response
to a real failure, and a check without that history is the first kind to be deleted.

```bash
python scripts/build_and_verify.py \
    --author "Milan Nikolic" --affiliation "Independent Researcher" \
    --email "m_nikolic@yahoo.com"
```

That is the whole workflow. It builds the PDF and verifies it, and stops at the first
failure.

## 1. Why a pipeline at all

The repository had no LaTeX on the machine that first built the paper, so the converter
was written by hand: Markdown → LaTeX → `pdflatex`, with a Markdown → HTML → headless
Chrome fallback. Both paths exist because both have been used, and each stage can fail in
a way the next stage cannot see:

| stage | what can fail | what catches it |
|:---|:---|:---|
| Markdown → LaTeX | a character with no mapping, a broken table, a long path into the margin | the build aborts on an unmapped character; `pdflatex`'s log is checked for overfull boxes |
| LaTeX → PDF | figures at the wrong size, floats drifting from their text | `verify_pdf.py` measures the placement; the log is read for float warnings |
| HTML → PDF (fallback) | browser furniture on every page | `verify_pdf.py` searches the text layer for a date header and a `file:///` footer |
| PDF → submission | missing figures, wrong page count, a missing author | `verify_pdf.py`, 27 checks |

## 2. The two scripts

| script | role | command |
|:---|:---|:---|
| `scripts/build_manuscript_pdf.py` | Markdown → LaTeX → PDF (LaTeX backend), or Markdown → HTML → PDF (Chrome fallback) | `--author`, `--affiliation`, `--email`, `--backend`, `--keep-tex`, `--html-only` |
| `scripts/verify_pdf.py` | reads the PDF back and asserts 29 properties | `--pdf`, `--strict`, `--dump-text` |

`scripts/build_and_verify.py` runs the two in order. There is no fix step: a tool that
rewrites prose is a tool that can silently delete a sentence. The guards that catch a bad
edit are tests (`python/tests/test_manuscript_figures.py`,
`test_pdf_verification.py`), and they fail loudly instead of editing.

## 3. What the build guarantees

The converter is deliberately narrow, so that its behaviour is inspectable:

* every non-ASCII character in the manuscript is mapped explicitly to LaTeX
  (`LATEX_CHARACTERS` in the build script), and **a character with no mapping aborts the
  build** — a dropped glyph is worse than a failed build;
* tables are `booktabs`, text-heavy tables get paragraph columns and a resize-to-fit
  guard, and long identifiers get `\allowbreak` so they do not run into the margin; a
  `|`-led block without a separator row **aborts the build** instead of printing its cells
  as running text;
* figures are included at the text width, and each PNG's `pHYs` chunk is rewritten so that
  its *natural* width equals the printed width (see §5);
* the licence header, the draft banner and the "A note on this draft" section are
  stripped; `--keep-draft-note` restores the last one for a review copy;
* `pdflatex` runs twice and its log is inspected: overfull boxes are reported, not hidden.

## 4. What the verifier guarantees

`verify_pdf.py` has no dependencies — it contains a small PDF reader (objects, Flate
streams, per-font `/ToUnicode` CMaps) because there is no PDF library on the build
machine. It asserts, on the PDF as a reader sees it:

* **structure** — 17 pages, A4;
* **figures** — five embedded pictures (distinguishing real images from alpha masks), and
  every placement inside the text block *and* inside the page;
* **text layer** — non-empty on every page, with the title, the author, the affiliation,
  the address, the repository URL and all five captions present; the glyphs the abstract is
  made of (`⟨r⟩`, `≥6/poisson`, `1..1`, `2..2`, `3..≥6`) recoverable after NFKC
  normalisation; the fi/fl/ff ligatures intact (`classifier`, `flag`, `effect`);
* **heading numbering** — no heading carries two numbers (`9.1 D.1` was the failure) and
  the unnumbered Disclaimer is not numbered;
* **absence of furniture** — no browser date header, no `file:///` footer, no licence
  header, no draft note, no `Status.` banner;
* **no page dominated by digits** — a page that is more than half digits is the symptom of
  a figure or table that failed to render.

## 5. The two failures this pipeline exists for

**Browser furniture.** The Chrome build printed its own header and footer on every page —
a date (`11/1/26, 9:34AM`) and the `file:///` path. The flag in the script was
`--print-to-pdf-no-header`, which Chrome 120+ silently ignores; the current flag is
`--no-pdf-header-footer`. The page count, page size and image list were all correct while
this was happening: only the text layer showed it.

**Figure scaling.** The first LaTeX build embedded a 1500-pixel figure declared at 150 dpi
— natural width 720 pt — inside a 0.66 scale group, so the *effective* width was the text
block but the *natural* width was larger than the page. A viewer that did not carry the
outer matrix drew it at 720 pt, cropped to its lower-left corner: page 6 became a wall of
axis numbers in steps of 0.2. The fix rewrites each PNG's `pHYs` chunk so the natural
width equals the printed width, leaving a scale of 1.0 that renders identically in any
viewer. The verifier now measures both widths.

## 6. Diagnosing a failure

| symptom | look at | fix |
|:---|:---|:---|
| the build aborts with `no LaTeX mapping for U+…` | the character named in the error | add it to `LATEX_CHARACTERS`, or rewrite the sentence without it |
| a figure is missing or blank | `verify_pdf.py`'s "embedded figures" line | `python scripts/generate_desymmetrisation_figures.py`, then rebuild |
| a page is a wall of numbers | `verify_pdf.py`'s "figures fit the page" and "no page of numbers" | check the figure's `pHYs`/scale; the build now sets it |
| page 1 shows a date or a URL | `verify_pdf.py`'s "no browser header"/"file:///" | the Chrome fallback lost its `--no-pdf-header-footer` flag |
| the text layer is mojibake | the fonts line of the verifier | per-font `/ToUnicode` tables were merged into one; codes collide between fonts |
| a table runs into the margin | `pdflatex`'s log (`Overfull \hbox`) | the column widths in `latex_table` |

## 7. What no script checks

* whether the figures look right;
* whether the page breaks fall in sensible places;
* whether the tables align, or a caption is split;
* whether the prose is correct.

Open the PDF once before submitting. That is the one step the pipeline cannot take.

### 7.1 Review reports, and the ones that are the extractor

Review reports about this PDF have repeatedly described defects that the file does not
contain: duplicated headings, a section number inside a sentence, misspelled paths, a
page of numbers where a figure should be. Each one so far has been an artefact of the
reader's text extractor, which inserts spaces between glyph runs (`Hamilton ian`,
`sect or`, `est imate`), drops a character now and then, and concatenates a heading with
the paragraph that follows it, so the page appears to print the heading twice. The
extractor used here does the same thing, which is why every text assertion in
`verify_pdf.py` runs on whitespace-free, NFKC-normalised text.

One reported text-layer problem was real. The `fi`/`fl`/`ff` ligatures were absent from
the PDF's `/ToUnicode` map because `cmap` loaded after `fontenc`, so `classifier`
extracted as `classi er` and `flag` as `ag`. Loading `cmap` before `fontenc` and setting
`\pdfgentounicode=1` fixes it, and the verifier now fails if any of the ligature-bearing
words (`classifier`, `flag`, `effect`, `difference`, `fidelity`, `reflects`) does not
extract.

`scripts/fix_remaining_v2.py` checks a set of reported defects against the source and
against the built PDF, repairs only the ones that are real, and prints the evidence for
the ones that are not:

```bash
python scripts/fix_remaining_v2.py --check   # report only, non-zero if one is real
python scripts/fix_remaining_v2.py           # repair what is real
```

It is safe to run twice: a repair only fires when its check fails, and the
duplicate-heading repair counts before it deletes, so a heading that occurs once is never
touched. `--dump-text` prints whole pages for the same reason a forensic dump exists at
all; an earlier version printed the first 2000 characters, which hid a heading that sat
past the cut and made a present appendix look missing.

## 8. The commands, without the orchestrator

```bash
python scripts/build_manuscript_pdf.py \
    --author "Milan Nikolic" --affiliation "Independent Researcher" \
    --email "m_nikolic@yahoo.com"          # writes output/desymmetrisation_paper.pdf
python scripts/verify_pdf.py                # 29 checks, non-zero exit on failure
python scripts/verify_pdf.py --dump-text    # what the text layer actually says
cd python && python -m pytest tests/test_pdf_verification.py \
    tests/test_manuscript_figures.py -q    # the guards, in the suite
```

The suite is the outer ring: `pytest tests/` includes the PDF checks, so a broken build
fails CI even if nobody runs the workflow by hand. `scripts/build_and_verify.py` is for
the moment before a submission, when the question is "is *this* PDF submittable".
