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
| **Comments** | 12 pages, 4 figures, 3 appendices. Code, tests, figures and Lean verification at `[ADD: repository URL]`. |
| **Journal-ref** | none |
| **DOI** | none |
| **License** | `[CHECK]` arXiv non-exclusive distribution licence (default), or CC BY 4.0. The **code** is GPL-3.0 and stays GPL-3.0; the paper is not, and does not need to be, GPL. |

The abstract field takes plain text with LaTeX math in `$…$`. The abstract below contains
no math, so it can be pasted unmodified.

## 2. Abstract (196 words, 1239 characters)

> Spacing statistics are the standard diagnostic for quantum chaos, but they are measured
> on a superposition whenever the Hamiltonian commutes with an involution. A spectrum that
> appears Poisson-like may instead be a union of unresolved sectors, and the mean gap
> ratio cannot distinguish the two. We present a diagnostic that verifies the symmetries,
> splits the spectrum into joint sectors, flags a contaminated full spectrum, and
> estimates the number of unresolved sectors as a posterior with measured coverage. The
> mean cannot be inverted; the sequence of gap ratios can. A first-order Markov model
> fitted on simulated superpositions yields a posterior over one to six sectors or an
> open-ended label. At a nominal 95% interval the measured coverage is 1.00, 0.93, 0.87,
> 0.98, 0.97 at one, two, three, four and six sectors and 0.78 for a Poisson spectrum. The
> single-sector case is decisive; the two-sector case is defensible as a set but not as a
> point; from three sectors upward the count is not recoverable. Two-sector GOE and GUE
> are indistinguishable, so a class test on a contaminated spectrum is uninformative. A
> companion dynamical analysis shows that the double-bracket flow preserves sector
> populations only for a commuting state.

Measured lengths: `196` words, `1239` characters — against arXiv's `1920`-character limit
and its ~200-word recommendation. The manuscript's own abstract is `291` words and is
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
other document here. The posted version must not carry them.

- [ ] remove the GPL licence header (it belongs to the **code**, and the code is not part
      of the upload);
- [ ] remove §"A note on this draft", or move it to supplementary material;
- [ ] decide on §4 (the multi-copy identity). My view, unchanged: move it to an appendix.
      As a section it reads as a claim about the cited paper; the honest content is that
      three generators one can build here disagree with the quoted form and the fourth
      was never read;
- [ ] check the figures in greyscale (§3 of the checklist) — Figs. 2 and 4 distinguish
      classes by colour *and* marker style, so they should survive, but this has not been
      looked at;
- [ ] set the author block for real.

## 5. The PDF, and how it is produced

arXiv accepts PDF, or LaTeX source it compiles itself. **This machine has neither `pandoc`
nor a LaTeX distribution**, so the PDF is produced by a different route:

```bash
python scripts/build_manuscript_pdf.py \
    --author "Milan Nikolic" \
    --affiliation "Independent Researcher" \
    --email "m_nikolic@yahoo.com"
```

The pipeline is Markdown → HTML (a converter that understands exactly the subset the
manuscript uses) → headless Chrome → PDF. The figures are embedded as base64, so the PDF
is self-contained. Output: `output/desymmetrisation_paper.pdf`.

What was verified mechanically on the current build:

| check | result |
|:---|:---|
| page count | `11` |
| page size | A4 (`594.96 × 841.92` pt) |
| embedded images | `4`, one per figure |
| fonts embedded | Georgia (text), Georgia Italic/Bold, Consolas (code), Cambria Math (the `σ`, `⟨r⟩`, `≥` glyphs) |
| text layer | `/ToUnicode` maps present, so the PDF is searchable and copyable |
| licence header, draft banner, "A note on this draft" | absent |

What is **not** in it, and the author should decide on:

- **No page numbers.** Chrome's print-to-PDF does not support CSS margin boxes, and adding
  the browser's own header would print the `file:///` path. If the venue needs numbered
  pages, the PDF has to be re-made with a LaTeX or Word toolchain.
- No line numbers and no journal style class: it is a plain A4 single-column preprint.

Re-running the command regenerates the PDF from the current Markdown; `--keep-draft-note`
keeps the corrections section (useful for a review copy, not for a submission).

`[CHECK]` — the manuscript uses Unicode (`⟨r⟩`, `σ`, `→`) inside tables. Chrome falls back
to Cambria Math for those glyphs, which renders correctly but is a visible font change
inside running text. A LaTeX build with `unicode-math` would unify it, if that matters to
the venue.

## 6. Pre-flight

- [ ] repository URL resolved and public (the comments field and the data statement cite it)
- [x] PDF generated from the current Markdown, figures embedded (mechanically checked: 11
      pages, 4 images, A4, text layer present) — but **open it once** and check the page
      breaks by eye, which is the one thing a mechanical check cannot do
- [ ] abstract pasted as plain text (196 words), not the long one
- [ ] categories set; MSC added only if the `math-ph` cross-list is kept
- [ ] licence selected, and the code's GPL-3.0 licence stated in the paper's data section
- [ ] endorsement arranged if this is a first submission `[CHECK]`
- [ ] the paper's §"A note on this draft" and GPL header absent from the PDF

## 7. After it is live

Add the arXiv identifier to [`README.md`](../README.md), to
[`submission_checklist.md`](submission_checklist.md) and to the bottom of
[`state_of_the_project.md`](state_of_the_project.md). Until that identifier exists, all
three documents say "not submitted", and they should keep saying it.
