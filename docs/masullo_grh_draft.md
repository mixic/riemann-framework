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

# The Masullo draft, recorded and not adjudicated

A 940-page typescript titled *The Music of the Primes* was released on 20 November 2026 and
is described around its release as a purely human-written proof of the Generalized Riemann
Hypothesis. This note records what the document contains, what it says about itself, and what
this repository can and cannot do with it. It does not evaluate the mathematics, and it changes
no claim of this repository: the standing position in
[`claimed_proof_triage.md`](claimed_proof_triage.md) §5 still holds.

## 1. The document, as a file

| field | value |
|:---|:---|
| title | *The Music of the Primes* |
| author | Alessandro Maria Masullo |
| extent | 940 pages: 14 chapters, appendices A–E, bibliography at p. 933 |
| file date | 2026-11-20 19:13 (the PDF's own creation date), pdfTeX-1.40.25 |
| archived as | `references/masullo_music_of_the_primes_2026-11-20.pdf`, sha256 `e039d3f6…97bf5` |

It appeared the same evening as Alpöge's Lean release, which had gone up that afternoon; the
[Alpöge–Nielsen record](alpoge_nielsen_dispute.md) covers that one. The scale is different in
kind: this is a conventional mathematical typescript, not a formalization, so nothing about it
is machine-checkable — the only thing a computer can verify is what the pages say.

The phrase *purely human-written proof of GRH* is the release description, not a sentence in
the document. What the document itself claims is weaker, and it is worth keeping the two apart.

## 2. What it says about itself

The acknowledgements (p. 5) are unusually explicit, and they describe a draft:

> The math is complete, and only filling in some writing remains on several parts across this
> long paper. The plan was to take a year of doing just this, with Brian Conrad helping me
> completing the task of polishing and improving the exposition.

> The introduction itself is unfinished and will be soon replaced by a proper one …

> Brian Conrad and I are aware of several glitches here and there that I was in the process of
> addressing on the way to completing the typewriting. The ideas are however all here, and many
> of the chapters are already fairly stable.

The same page records why it was released in this state — *"In light of the current climate I am
being advised to release the current version as it is"* — and traces the work to twelve years
beginning "as a Graduate Student at Stanford under Brian Conrad", with a planned year of
polishing cut short.

This is the author's own description of the artifact. It is a draft with a finished core and an
unfinished frame, released early, by his account, because of the timing of the field.

## 3. Where the theorem would be, and what is printed there

The zeros are dealt with in Chapter 13, "Zeros of Hecke L-functions", which occupies pp. 521–522.
Its §13.3 is titled *Main Theorems on the location of the zeros*. Three things are on those
pages:

1. **Theorem 13.3.1.1 (Trace Formula)** is stated in full, for a test function `φ ∈ D(C_F)`
   subject to condition (13.3.1.2): the holomorphic derivatives of the S-local Mellin transform
   vanish at the central zeros, for orders `0 ≤ k ≤ [F : Q] − 1`.
2. The text then reads *"Upon combining Theorem 13.3.1.1 and Theorem ??, we obtain the
   following:"* — an unresolved cross-reference.
3. **Theorem 13.3.1.2 (Divisor of `L(s, χ)`)** is printed with its number and title and **no
   statement at all**. The footnotes attached to that page are the to-do list:
   *"Correct statement."*, *"Insert statement."*, and *"State and prove the Main Theorems, also
   explaining how to deduce them by approximation φ → e^{−s|log t|} as Re(s) > 1."*

So the page that would state and prove the theorem is a placeholder, and the step that would
replace the restricted test functions by the ones the deduction needs is itself on the list.

What the content is *meant* to be appears one chapter later. §14.1.2, p. 528, writes:

> Theorem 13.3.1.2 … asserts that if ρ ∈ ℂ is a non-trivial zero of `L(s, χ)`, then
> ρ ∈ 1/2 + iℝ, and if, in addition, ρ ∉ ℝ, i.e. ρ ≠ 1/2, then N(ρ) ≤ [F : ℚ].

That is the GRH-type statement. The paragraph carries a footnote of its own — *"Correct this
subsection."* — so the author flags it as provisional, and the one place the conclusion is
written down is flagged by its own author.

The consistency check that follows is conditional on the conclusion: Proposition 14.1.2.3
(p. 531), *"Multiplicity Bound, on Global Langlands, GRH and GSH"*, **assumes** Conjecture
14.1.2.1 (GRH and GSH) and Conjecture 14.1.2.2 (Global Langlands) and concludes `ρ ∈ 1/2 + iℝ`.
Its purpose, stated there, is to show the multiplicity bound is compatible with expectations
from the literature. A statement that assumes GRH cannot be cited as evidence for it, and the
author does not present it that way.

## 4. The assumption the trace formula carries

Two passages state, in plain terms, a restriction on what the trace formula covers. From §1.4.6,
p. 30:

> Indeed, the trace formula can only be proved for test functions φ on C_F … such that
> φ(C_F^1) = 0. … The condition φ(C_F^1) = 0 cannot be removed before GRH is proved.

and §1.7.2, p. 35:

> This assumption cannot be removed. It stays there until after GRH is deduced from the Trace
> Formula. It is forced on us by two divergence phenomena that can only be resolved by assuming
> that (1.7.2.1) holds.

The shape of the intended argument is therefore: prove the formula on a restricted class, deduce
zero information from it, then remove the restriction *a posteriori* using what was deduced. That
is a strategy, stated as one. The deduction in the middle is exactly what Chapter 13's placeholder
is for, and the *a posteriori* step is not carried out anywhere in these 940 pages.

Two further inputs are recorded on the way, and they are worth separating because only one of
them is conditional for the case of most interest:

- non-vanishing of the finite Hecke L-function on `1 + iℝ` "is used" (§1.4.7, p. 30) — an
  ingredient, named as such;
- Theorem 1.7.1.1(2), p. 34, selects the topologies used in the trace calculation "assuming
  Schanuel's Conjecture" for characters that are not of finite order. Part (3) of the same
  theorem says the assertion holds unconditionally when `χ` has finite order — which covers
  Dirichlet characters — so the conditional input is not on the critical path for that case.

None of this says the argument fails. It says what the document states it needs, which is the
only thing this note is about.

## 5. What was checked here, and what was not

Checked, and repeatable with the archived file:

- the hash, the byte count and the page count;
- that Theorem 13.3.1.2 is a placeholder, by reading p. 522;
- the two "cannot be removed" sentences, at pp. 30 and 35;
- the attribution of the GRH statement to 13.3.1.2, at p. 528, and the "Correct this subsection"
  footnote under it;
- that Proposition 14.1.2.3 assumes Conjectures 14.1.2.1–2, at p. 531;
- the Davenport–Heilbronn screen of §6, which is mechanical and reproducible:
  `trace_formula_screen.screen()` returns `eligible`.

Not checked, and not checkable here:

- any of the analysis. The trace formula itself, the orbital Schauder bases, the Hardy–Sobolev
  topologies and the S-local computation are 900 pages of a subject this repository does not
  implement.
- whether the two "divergence phenomena" are as described, or whether the restricted test
  functions suffice to reach the zeros.
- the document's internal consistency beyond the passages cited. Two sections describe the
  provenance of Theorem 13.3.1.2 differently — §1.4.6 says "Weil's Positivity Criterion is not
  used", while §14.1.2 calls it "a consequence of the Trace Formula combined with the Positivity
  Criterion" — but the second of those carries the author's "Correct this subsection", so the
  discrepancy is recorded rather than resolved.

**A critique that is not recorded here.** A PhilArchive critique of the draft is reported to this
repository as alleging that a uniform-boundedness step fails and that certain integrals diverge.
It was not retrieved — PhilArchive answers automated fetches with a Cloudflare challenge, the same
wall that stood in front of Nielsen's paper until a copy was obtained by other means — so it is
not archived, not cited, and not counted as evidence. If a copy arrives it belongs in
[`references/`](../references/README.md) beside the others, with its hash.

## 6. What the Davenport–Heilbronn filter says, and what it does not

One thing about the draft **is** decidable with machinery this repository already has: whether the
argument, as its own pages describe it, uses any fact that also holds for the Davenport–Heilbronn
function, whose RH-analogue is false. An argument that transfers there cannot establish RH. That is
the whole content of [`dh_filter.py`](../python/riemann_framework/dh_filter.py), and
[`trace_formula_screen.py`](../python/riemann_framework/trace_formula_screen.py) declares the
draft's inputs for it, each with the section that shows it is used.

| declared input | where the draft uses it | holds for DH? |
|:---|:---|:---|
| `euler_product` | §1.4.7, §14.1.2 (partial Euler products) | **no** — DH has none |
| `explicit_formula_prime_side` | §3.4, Appendix B.4 (Weil's explicit formulas) | **no** — no prime support without an Euler product |
| `functional_equation` | Appendix B.4 | yes |

**Verdict: `eligible`.** Two of the three inputs fail for Davenport–Heilbronn, so the filter's
contrapositive does not apply: this is not an argument that would prove RH for a function where RH
is false. The draft's analytic input is only the functional equation, which alone would be dead;
its arithmetic input — the Euler product and the prime side of the explicit formula — is what keeps
it alive.

Three inputs a reader might expect are **not** declared, and the reasons matter:

- `li_positivity`. §1.4.6 says the argument does not use Weil's positivity criterion. Declaring it
  would have misstated the paper — and, less obviously, it would not have made the verdict
  stronger: Li's criterion fails for DH, so that screen also reads `eligible`, from an
  RH-equivalent input. **The filter sees transfer, not circularity.** A pass here is therefore not
  a certificate of non-circularity, and that is the sharpest limit of this section.
- `gue_pair_correlation`. The argument is about where the zeros are, not about their statistics.
- `hadamard_product`. The draft states a divisor (Theorem 13.3.1.1), not an order-1 factorisation;
  declaring it would attribute to the author a hypothesis he does not make.

**What the verdict means and does not mean.** `eligible` is permission, not promise. It says this
draft is not of the class the repository can *reject*; it says nothing about whether the draft is
correct, nothing about the trace formula, and nothing about the placeholder at Chapter 13. The
filter cannot see the two obstacles recorded above — the missing statement and the unremovable
test-function restriction — because they are not inputs, they are gaps. `test_trace_formula_screen.py`
pins the verdict, pins that the filter still fires on a purely analytic input set, and pins that an
invented input cannot be talked into a pass.

**Calibration, so the verdict is not read as encouragement.** Run over the repository's own nine
idea records, the dead list has exactly one entry (`dimension_shift_w`), three are eligible and five
are unscreened. Eligibility is therefore not scarce — anything that uses the prime side of the
explicit formula qualifies, which is most arithmetic arguments — while the dead list is short and
decisive. The filter's value is in what it *rejects*; a draft that is not on the dead list has
cleared a low bar, not a high one.

**The declaration checked against the draft's own text.** The filter reads declarations, so an
input the argument uses but the declaration never mentions would be invisible to it. That gap is
now scanned rather than assumed: `python scripts/audit/scan_declared_inputs.py` extracts the text
of the archived PDF and matches the inventory's vocabulary against it. The result:

| class | hypothesis | mentions |
|:---|:---|---:|
| declared | `euler_product` | 60 |
| declared | `explicit_formula_prime_side` | 71 |
| declared | `functional_equation` | 78 |
| excluded, with a reason | `li_positivity` (the positivity criterion) | 5 |
| excluded, with a reason | `gue_pair_correlation` (pair correlation) | 1 |

215 mentions, none **unreconciled**: every hypothesis the draft names is either declared or
excluded in writing. Four inventory rows are never named — `hadamard_product`,
`real_coefficients`, `zero_symmetry` and `riemann_von_mangoldt_count` — and the draft's three
references to Hadamard are to Hadamard's Lemma and to Hadamard–de la Vallée Poussin, not to the
factorisation row. The check is lexicographic and the limits are stated in the module: a mention is
not a use, and a paraphrase that avoids the inventory's vocabulary is not seen. It converts a
silent omission into a reconciliation that has to be written down.

## 7. What this repository can and cannot do with it

- **The vetting pipeline cannot take it.** Every gate needs a map or an operator; a proof-shaped
  claim has no input, and the verdict such a claim receives is noise wearing the clothes of a
  result. This is argued at length in [`claimed_proof_triage.md`](claimed_proof_triage.md) §2 and
  is the reason that article exists. The `ideas/masullo_music_of_the_primes.json` record carries
  the same warning in its `notes`, because the runner will print a stage-B failure for it.
- **Numerics cannot touch it.** There is no spectrum in it, and no numerical sample settles a
  universal statement — the distinction this repository draws between the finite-field case,
  where a computation *is* a proof, and the universal one, where it is never a proof.
- **Lean cannot touch it either, for a different reason than Alpöge's archive.** There is no
  formalization of this argument to compile. For the Alpöge release a kernel replay, an axiom
  audit and a dependency walk exist and are being run by other people; here the only instrument
  is reading, and the one filter that does apply is the arithmetic one above.

**What would change this record**, in order of how much it would settle:

1. Chapter 13 written: the theorem stated, the approximation step `φ → e^{−s|log t|}` carried
   out, and the proof given.
2. The `φ(C_F^1) = 0` restriction removed, or the deduction of GRH made without needing it.
3. Expert review of the 900 pages between §2 and §13, which is where an error would live.
4. A formalization, which would make the argument machine-checkable in the way the Alpöge archive
   is — and which does not exist as of this writing.
5. A revised PDF. The archive's hash is how a reader would notice; a replacement file must be
   indexed as a new version rather than over the old one.

## 8. The standing position

The Riemann hypothesis is open. That sentence is unchanged by this note and by the document it
records, and [`claimed_proof_triage.md`](claimed_proof_triage.md) §5 continues to say so. This
repository now carries two records of 2026 claims — Alpöge's, with Nielsen's objection, and
Masullo's — both dated, both sourced to a stored file, neither adjudicated.

Nothing here says the draft is wrong. It says what its own pages contain on 2026-11-22: a stated
trace formula, an assumption its author says cannot yet be removed, a placeholder where the
consequence for the zeros would go, and an acknowledgements page that calls the whole thing a
draft with writing still to do. Those are checkable facts about a file. Whether the mathematics
is correct is a different question, and not one this repository is equipped to answer.

## Sources

- Masullo, A. M. *The Music of the Primes*, 940 pp., released 2026-11-20. Archived as
  `references/masullo_music_of_the_primes_2026-11-20.pdf`; page references above are to that file.
- Alpöge, L. *Remark*, 2026-11-20. See [`alpoge_nielsen_dispute.md`](alpoge_nielsen_dispute.md).
- Nielsen, J. L. *The Invalidity of Alpöge's Proposed Proof of the Riemann Hypothesis*,
  PhilArchive NIEIOT-2, 2026-11-20. The method-and-scope limits quoted in the reference index
  are from that paper.
