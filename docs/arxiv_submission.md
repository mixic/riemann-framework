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

# arXiv submission metadata

**Status: prepared, not submitted.** There is no arXiv identifier, no submission date, and
no DOI. Everything marked `[ADD]` or `[CHECK]` is a field only the author can fill or
verify — the placeholders are deliberate, because a guessed affiliation or an invented
MSC code is exactly the kind of quiet falsehood this repository's guards exist to prevent.

Manuscript: [`desymmetrisation_paper.md`](desymmetrisation_paper.md). Checklist:
[`submission_checklist.md`](submission_checklist.md). Cover letter:
[`cover_letter.md`](cover_letter.md).

## 1. The fields, for copy-paste

| field | value |
|:---|:---|
| **Title** | Desymmetrization of Quantum Spectra: A Bayesian Sector-Count Diagnostic with Measured Coverage |
| **Authors** | Milan Nikolic — Independent Researcher — `m_nikolic@yahoo.com` — no ORCID given |
| **Primary category** | `quant-ph` |
| **Cross-lists** | `nlin.CD` (chaotic dynamics), `math-ph` (needs MSC codes, §3) `[CHECK: whether the second cross-list is worth the MSC typing]` |
| **Comments** | 17 pages, 5 figures, 4 appendices. Code, tests, figures and Lean verification at `https://github.com/mixic/riemann-framework`. |
| **Journal-ref** | none |
| **DOI** | none |
| **License** | `[CHECK]` arXiv non-exclusive distribution licence (default), or CC BY 4.0. The **code** is GPL-3.0 and stays GPL-3.0; the paper is not, and does not need to be, GPL. |

The abstract field takes plain text with LaTeX math in `$…$`. The abstract below contains
no math, so it can be pasted unmodified.

## 2. Abstract (246 words, 1549 characters)

> Spacing statistics are the standard diagnostic for quantum chaos, but they are measured
> on a superposition whenever the Hamiltonian commutes with an involution. A spectrum that
> appears Poisson-like may instead be a union of unresolved sectors, and the mean gap
> ratio cannot distinguish the two. We present a diagnostic that verifies the symmetries,
> splits the spectrum into joint sectors, flags a contaminated full spectrum, and
> estimates the number of unresolved sectors as a posterior with measured coverage. The
> mean cannot be inverted; the sequence of gap ratios can. A first-order Markov model
> fitted on simulated superpositions yields a posterior over one to six sectors or an
> open-ended label. At a nominal 95% interval, over 400 spectra per row, the measured
> coverage is 0.99, 0.92, 0.91, 0.96, 0.98 at one, two, three, four and six sectors and
> 0.78 for a Poisson spectrum. The single-sector case is decisive; the two-sector case
> yields a lower bound but not a count; from three sectors upward the count is not
> recoverable. Two-sector GOE and GUE are indistinguishable, so a class test on a
> contaminated spectrum is uninformative, and the resolution of that test is measured: the
> best single-spectrum class accuracy is 0.79 at one sector and 0.53, which is chance, at
> two, while the same spectra averaged in thousands converge to within 0.0006. More
> spectra sharpen the mean and leave the single measurement untouched. A companion
> dynamical analysis shows that the double-bracket flow preserves sector populations only
> for a commuting state.

Measured lengths: `246` words, `1549` characters — against arXiv's `1920`-character limit
and its ~200-word recommendation. The manuscript's own abstract is `279` words and is
**over** the Physical Review E guide of ~250; use this one there too, or trim the long one.

Two facts are stated in it because they are the paper's content, and neither should be
softened for the listing: the two-sector case is not a point estimate, and from three
sectors upward the count is not recoverable.

## 3. Classification

`quant-ph` is unambiguous: the subject is a diagnostic for spectra, not a statement about
the zeros.

For the `math-ph` cross-list, arXiv asks for MSC codes. Candidates, to be checked against
the current MSC list before submission:

| code | what it would cover |
|:---|:---|
| `81Q50` | quantum chaos |
| `62F15` | Bayesian inference |
| `11M26` | the zeta and L-functions |

`[CHECK]` — these are candidates, not recommendations from an authority. If the cross-list
is not clearly worth typing, drop it: a wrong MSC code is worse than no second category.

## 4. What must change in the posted version

The repository copy keeps the GPL header and the draft note for consistency with every
other document here. The build strips both for the PDF; the Markdown keeps them.

- [x] the GPL licence header is stripped by the build (it belongs to the **code**, and the
      code is not part of the upload);
- [x] §"A note on this draft" is stripped by the build (`--keep-draft-note` restores it for
      a review copy);
- [x] the author block is set: Milan Nikolic, Independent Researcher, `m_nikolic@yahoo.com`;
- [ ] decide on §4 (the multi-copy identity). My view, unchanged: move it to an appendix.
      As a section it reads as a claim about the cited paper; the honest content is that
      three generators one can build here disagree with the quoted form and the fourth
      was never read;
- [ ] check the figures in greyscale (§3 of the checklist) — Figs. 2 and 4 distinguish
      classes by colour *and* marker style, so they should survive, but this has not been
      looked at.

## 5. The PDF, and how it is produced

MiKTeX is installed, so the default backend is now **LaTeX**, which is what arXiv wants:

```bash
python scripts/build_manuscript_pdf.py \
    --author "Milan Nikolic" \
    --affiliation "Independent Researcher" \
    --email "m_nikolic@yahoo.com"
```

The script translates the Markdown to LaTeX (`article`, 11pt, A4, `booktabs` tables,
`graphicx` figures, `hyperref`, `cmap`) and runs `pdflatex` twice. Every non-ASCII
character in the manuscript is mapped to a LaTeX form by an explicit table, and a
character the table does not cover **aborts the build** rather than dropping a glyph.
Output: `output/desymmetrisation_paper.pdf`; the `.tex` is deleted unless `--keep-tex`.

Without a TeX engine the script falls back to Markdown → HTML → headless Chrome. That
path is supported and tested, but it is the fallback.

### 5.1 What the build verifies

`scripts/verify_pdf.py` reads the PDF back — extracting the text layer per font, with a
small PDF reader written for this purpose, because there is no PDF library here — and
asserts 28 things. The current build passes all of them:

```
$ python scripts/verify_pdf.py
[PASS] page count: 17 pages (expected 17)
[PASS] page size: A4
[PASS] embedded figures: 5 pictures (10 image objects, 5 masks; expected 5)
[PASS] text layer: 17 pages, 33288 characters
[PASS] no browser header: no date/time stamp
[PASS] figures fit the page: 5 placements within the text block and the page
[PASS] no page of numbers: no page is dominated by digits
[PASS] absent: 'This program is free software': absent
[PASS] absent: 'A note on this draft': absent
[PASS] absent: 'Status.': absent
[PASS] absent: 'file:///': absent
[PASS] present: 'Desymmetrization of Quantum Spectra': present
[PASS] present: 'Milan Nikolic': present
[PASS] present: 'Independent Researcher': present
[PASS] present: 'm_nikolic@yahoo.com': present
[PASS] present: 'Figure 1:' … 'Figure 5:': present
[PASS] present: 'github.com/mixic/riemann-framework': present
[PASS] glyph: ⟨r⟩ / ≥6/poisson / 1..1 / 2..2 / 3..≥6: render
[PASS] ligatures extract: fi, fl and ff ligatures survive extraction
PASS: all 28 checks passed
```

The `absent` check on the licence text reads the *boilerplate*, not the licence name:
naming GPL-3.0 in the data statement is attribution and is wanted, while the pasted header
block is a leak from the source files.

Two of those checks exist because builds **failed** them:

* the Chrome PDF carried a date/time header (`11/1/26, 9:34AM`) and a `file:///` footer on
  every page — `--print-to-pdf-no-header` is silently ignored by Chrome 120+, and the
  current flag is `--no-pdf-header-footer`;
* the first LaTeX PDF placed each figure with a nested scale, so a viewer ignoring the
  outer matrix drew the coverage figure at 720pt on a 595pt page and page 6 became a wall
  of axis numbers (§5.3).

Both are now measured rather than assumed: `figures fit the page` compares each figure's
effective width with the text block *and* its natural width with the page.

### 5.2 Properties of the current PDF

| property | value |
|:---|:---|
| pages | `17`, A4, numbered (LaTeX default) |
| figures | `5`, captioned; each placed within the text block, with a natural width equal to the printed width (see 5.3) |
| fonts | Computer Modern (CMR10, CMR8, CMR7, CMMI10/8/7, CMSY10, MSBM10), all embedded |
| text layer | complete and searchable (`/ToUnicode` per font) |
| PDF/A | **not** compliant; arXiv accepts non-PDF/A, a venue that requires it needs a Ghostscript pass or a PDF/A class |
| layout | one overfull box of `3.5pt` in the figure-list table; no other overfull or underfull warnings, no float drift (each figure sits within a page of its reference) |

### 5.3 The figure-scaling defect that page 6 exposed

The first LaTeX build embedded the figures with a *nested* scale. A 1500-pixel PNG declared
at 150 dpi has a natural width of 720pt; `width=\linewidth` does not change that natural
size, it wraps it in a `0.66` scale group, so the page contains

```
q 0.66 cm  q 720 cm  /Im3 Do  Q Q
```

The effective width is correct (476pt, the text block). But a viewer that does not carry
the outer matrix draws the image at 720pt on a 595pt page, cropped to its lower-left
corner — for the coverage figure, the y-axis alone, at 28pt: *a page of numbers in steps
of 0.2*. That is the failure a reader reported.

The fix is in `latex_figure`: each PNG's `pHYs` chunk is rewritten so its declared
resolution puts the natural width at exactly the text width. The outer scale becomes
`1.001`, so both readings of the page agree. `verify_pdf.py` now measures both and fails
if either exceeds the page.

Re-running the command regenerates the PDF from the current Markdown; `--keep-tex`
leaves the `.tex` behind, `--keep-draft-note` keeps the corrections section (review copy,
not submission), and `--backend chrome` forces the fallback.

## 6. Pre-flight

- [ ] repository URL resolved and public (the comments field and the data statement cite it)
- [x] PDF generated from the current Markdown, figures embedded, `verify_pdf.py` passing
      28/28 — but **open it once** and check the page breaks by eye, which is the one thing
      a mechanical check cannot do
- [ ] abstract pasted as plain text (246 words), not the long one
- [ ] categories set; MSC added only if the `math-ph` cross-list is kept
- [ ] licence selected, and the code's GPL-3.0 licence stated in the paper's data section
- [ ] endorsement arranged if this is a first submission `[CHECK]`
- [x] the paper's §"A note on this draft" and GPL header absent from the PDF (the build
      strips both)

## 7. After it is live

Add the arXiv identifier to [`README.md`](../README.md), to
[`submission_checklist.md`](submission_checklist.md) and to the bottom of
[`state_of_the_project.md`](state_of_the_project.md). Until that identifier exists, all
three documents say "not submitted", and they should keep saying it.
