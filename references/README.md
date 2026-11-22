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

# Reference archive

Four third-party documents about claims on the Riemann hypothesis, stored byte for byte as
they were obtained, indexed here with a hash, a size and a page count. Nothing in this
folder is written by this repository except this file.

**Why store them at all.** Two of the three documents are the kind that disappear or
change:

- `alpo.ge/remark.pdf` is a personal statement on a personal site;
- PhilArchive answers automated retrieval with a Cloudflare challenge, so a reader who
  follows a citation months from now may not be able to check it at all;
- the third is a 940-page draft whose author states he is still filling in sections, so the
  version that gets cited later will not be the version quoted here;
- the fourth is a live verification page that its author says will be updated as the
  remaining checks finish, so the page a reader opens later is not the page quoted here.

A citation that cannot be opened is not a reference. Storing the bytes and recording the
hash is what makes the quotations in `docs/` checkable years later, and what makes a
silent replacement of a file visible: if the PDF changes, the hash here stops matching.

**How to verify one.**

```powershell
Get-FileHash references\alpoge_remark_2026-11-20.pdf -Algorithm SHA256
```

Hashes are lowercase hex SHA-256. Byte counts are the exact file lengths. Page counts come
from the PDF's own page tree (`pdfinfo`, MiKTeX's poppler build), not from counting text.
The one HTML record has no page count: it is a single page, and its hash is of the bytes
the server returned.

**What is not here.** The 61.5 GB Lean export behind the Alpöge archive, the mirror used by
Nielsen, and any critique that could not be retrieved. A reader who needs those can find them
from the URLs recorded below; this archive stores only what was in hand.

**These are documents, not evidence.** No file here is endorsed by this repository, none is
used as an input to any computation, and none changes a claim in it. What each document says,
and where it has been checked, is recorded in `docs/` and cited per record.

---

## Archived documents

### `alpoge_remark_2026-11-20.pdf`

- title: *Remark* (untitled in the PDF; the file is `remark.pdf`)
- author: Levent Alpöge
- issued: 2026-11-20 13:52 (the PDF's own creation date; pdfTeX-1.40.29)
- pages: 4
- bytes: 245114
- sha256: `3fc97784b71ddd44ff8aa0a177e99622a1c61b13cfa843a0989ee4a7a0cfeb8d`
- source: `https://alpo.ge/remark.pdf`; the archive itself is at `https://alpo.ge/lean.tar.gz.part01` … `.part14`
- obtained: 2026-11-22, as `alpoege_remark.pdf`
- cited by: [docs/alpoge_nielsen_dispute.md](../docs/alpoge_nielsen_dispute.md)

**What it is.** A statement of belief and a story: that the author, "working with Claude,
discovered a proof of the Riemann Hypothesis", that the method "easily extends much further,
resolving the so-called Generalized Riemann Hypothesis", and that they "also formalized the
arguments without assumptions". It is the only prose that accompanied the release. It contains
a dated timeline of the argument (20 entries, 10/6/26 to 11/16/26) and says why no paper was
written: *"It being obviously inappropriate to attempt to post some massive unreadable
travesty of 'slop', I decided to only present Lean."*

**What it is not.** It is not a proof, not an abstract of a proof, and not a summary of an
argument. It states no theorem, defines no object, and gives no estimate. Every mathematical
claim about the 2026 Alpöge release in this repository is drawn from the archive itself, from
the Lean and Mathlib communities' statement, or from Nielsen's analysis — never from this file.

### `nielsen_invalidity_2026-11-20.pdf`

- title: *The Invalidity of Alpöge's Proposed Proof of the Riemann Hypothesis*
- subtitle: *Vacuously true geometric and lattice witnesses in the Lean formalization*
- author: J. L. Nielsen, Center for Topological Physics, Lawrence, Kansas
- issued: 2026-11-20 (title page); the PDF was generated 2026-11-21 16:50 (xdvipdfmx)
- pages: 13
- bytes: 98048
- sha256: `2f8bd3c47c211457e1d6cfe7bddf20761b96166a4f3ea594d63de711e304507c`
- source: `https://philarchive.org/rec/NIEIOT-2` (PhilArchive NIEIOT-2)
- obtained: 2026-11-22, as `Invalidy_Aloeges_Proof.pdf`
- cited by: [docs/alpoge_nielsen_dispute.md](../docs/alpoge_nielsen_dispute.md)

**What it is.** A source-level reading of the Alpöge Lean archive, at the mirror
`github.com/Deicyde/riemann-hypothesis`, commit `712a6aef`. It argues that the hypothesis
bundle on which the final theorem depends is inhabited through witnesses whose obligations are
vacuously true — a geometry predicate defined as `True`, a degenerate model, a zero map from
lattices to sections, an identification that holds by `rfl` — and that the lemmas written to
extract content from those witnesses are never called. Its §9 lists four checks that would
settle the matter, one of which is a compiled dependency trace.

**What it is not.** It is not a refutation of the Riemann hypothesis, and not a claim that the
Lean term fails to typecheck: §9 and Appendix A say so explicitly. It has not been
peer-reviewed, it was written without a build of the archive, and its author reports reading
about 70 of 175,187 files. Those limits are hers, stated in her §10, and this repository quotes
them rather than removing them.

### `masullo_music_of_the_primes_2026-11-20.pdf`

- title: *The Music of the Primes*
- author: Alessandro Maria Masullo
- issued: 2026-11-20 19:13 (the PDF's own creation date; pdfTeX-1.40.25)
- pages: 940
- bytes: 6756996
- sha256: `e039d3f6cf0a4b14f03c7edb85097752dd65c0a2fe543c76fe992be234f97bf5`
- source: not recorded with the copy; see the note on the source path below
- obtained: 2026-11-22, as `the-music-of-the-primes.pdf`
- cited by: [docs/masullo_grh_draft.md](../docs/masullo_grh_draft.md)

**What it is.** A 940-page typescript in 14 chapters and 5 appendices, presented in its
acknowledgements as twelve years of work begun as a graduate student at Stanford under Brian
Conrad, on a trace formula for the idelic class group of a number field and its consequences
for zeros of Hecke L-functions. Around the release it is described as a purely human-written
proof of GRH. The document's Chapter 13 is where that would be established, and as printed it
states the trace formula and leaves the consequence for the zeros as a placeholder; see
[`docs/masullo_grh_draft.md`](../docs/masullo_grh_draft.md) for the pages and the quotations.

**What it is not.** As of this hash it is not a document that states the theorem it is reported
to prove. It is also not evidence of anything: nothing in this repository has checked its
argument, and no simulation here can.

**Note on the source path.** The copy carries no URL. The release was reported to this
repository as announced through Ravi Vakil's Math 216 course blog, which was not fetched; only
the file itself, its dates and its contents are facts of record here. If a stable location
becomes known, add it to this line without changing the hash.

### `sutherland_grh_checks_2026-11-22.html`

- title: *Verification files for the Lean proof of the Riemann Hypothesis*
- author: Andrew Sutherland (MIT), "checks run with Claude Code"
- issued: page last updated 2026-11-22 04:35 UTC; the snapshot archived here is of that state
- bytes: 27222
- sha256: `01a43fc8defab818d878bfa8fd900d7563073db3dbc6f150ad73baec0fe388a7`
- source: `https://math.mit.edu/~drew/grh/`
- obtained: 2026-11-22, as the server returned it
- cited by: [docs/claim_verification_agent.md](../docs/claim_verification_agent.md)

**What it is.** The verification report for the 2026 Alpöge archive, and the most complete
kernel-level record of it that exists. At this hash it states: all 175,187 modules compile
(Lean v4.33.1, Mathlib v4.33.1) with zero errors; `#print axioms` for the five headline
theorems returns `propext`, `Classical.choice`, `Quot.sound` and nothing else; 15 axioms
exist in the environment and all are in `Init`; 8,322 Mathlib and 378 dependency `.olean`
files are byte-identical to the official cache; an independent sandboxed `lake build`
(no network, read-only source, separate machine) exits 0 and its `lean4export` output is
byte-identical to the published 61,570,595,788-byte export; `leanchecker` replays 175,187 of
175,187 modules with zero rejections; nanoda, con-leche (`master`, and `--compare` against
the challenge) and con-ron (`--compare`) all accept, with con-leche reporting 1,468,418
declarations accepted in `--verified` mode and all five challenge theorems "justified by the
solution"; lean4lean accepts 175,187 of 175,187 compiled modules (five after raising a step
limit). The arithmetic consequences — Robin's and Lagarias's inequalities — are also
recorded, combined with an independent formalisation of Robin's criteria
(`kimihiro64/Robin1984`, commit `acab1a3`), and the page reports that the elaborated
Lagarias statement names 27 constants directly and depends on 1,801 Mathlib and core
declarations (2,050 for Robin's), counting definitions with their bodies and theorems by
their statements.

**What it establishes.** That a term of the five stated types exists, depends only on the
three standard axioms, and is accepted by three independently written kernels and by a
byte-identical export rebuilt from a sandboxed build. That is a much stronger kernel result
than any replay in this repository.

**What it does not establish, in its own words.** The page's closing caveat: "A passing
check shows that the formal statements, as written in Lean against Mathlib's definitions,
follow from the three standard axioms according to the kernels used. It relies on those
kernels and on Mathlib's definitions being what they are intended to be." Its scope note is
equally explicit: "GRH" there means Dirichlet L-functions, all moduli and all characters,
and "Dedekind zeta functions, Hecke L-functions and automorphic L-functions in general are
not among the statements that were checked." The page is a record of kernels accepting
terms. It says nothing about whether a theorem's proof routes through definitions that
carry no mathematics — the question Nielsen's objection poses — and nothing in it is
evidence about the Riemann hypothesis beyond what the stated statements say.

This repository treats the page as an institutional fact (`recorded`, not `checked_ok`) and
does not promote it: a replay of someone else's kernel run is not a check this repository
ran. `docs/claim_verification_agent.md` records what the page does and does not settle, and
the evaluation paper cites it for exactly that distinction.

---

## How these are cited

| document | uses |
|:---|:---|
| [`docs/alpoge_nielsen_dispute.md`](../docs/alpoge_nielsen_dispute.md) | Alpöge's remark and Nielsen's analysis, side by side, not adjudicated |
| [`docs/masullo_grh_draft.md`](../docs/masullo_grh_draft.md) | the 940-page draft, and what its own pages do and do not contain |
| [`docs/claimed_proof_triage.md`](../docs/claimed_proof_triage.md) | the standing position that RH is open, and why a proof-shaped claim has no input to this repository's pipeline |
