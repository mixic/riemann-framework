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

# State of the Project: A Closing Summary

**The Riemann hypothesis is open.** Nothing in this repository proves or disproves it,
and nothing here is evidence for or against it.

## Preamble

This document closes the research program recorded in this repository. It is written to
be read first, by anyone who wants to understand what the repository contains, what it
proved, what it falsified, what it corrected, and what remains open — without reading
every file.

It is not a eulogy. It is an inventory.

## 1. What this repository is

The Riemann Framework is an experimental workbench for approaches to the Riemann
hypothesis. It combines numerical experiments in Python with a Lean 4 formalization,
covering zeta zeros, the explicit formula, prime counting, dimension-shift models, graded
algebras, and exotic number systems.

It is not a proof, and nothing here claims to be one. Passing tests are research
evidence, not a completed proof.

What it is: a record of a research program that was pursued, tested, and closed when the
evidence required it.

## 2. What was attempted

Eleven tracks. Each asked one structural question and produced a document, a test suite,
and a measured result.

| # | track | the question it asked |
|:---|:---|:---|
| 1 | numerical core | can the zeros be verified, and the explicit formula evaluated, to working precision? |
| 2 | Dimension-Shift Hypothesis | is the critical line the fixed locus of a discrete involution whose spectrum is the zeros? |
| 3 | graded algebra / shift-zeta | does lifting the Euler product into a ℤ₂-graded algebra force the zeros into the fixed locus? |
| 4 | primon gas | can the Euler product be realized exactly as the trace of a diagonal Hamiltonian? |
| 5 | Cayley–Dickson | does dimension-lifting produce genuine Euler-product content? |
| 6 | Hilbert–Pólya prototype | can an operator be built whose spectrum is the zeros, defined without reference to them? |
| 7 | hidden symmetries | do unresolved symmetries bias spacing statistics, and can that be detected? |
| 8 | finite-field curves | where is the Riemann hypothesis a theorem, and is that proof a finite computation? |
| 9 | de Bruijn–Newman | can the hypothesis be restated as a threshold, and is the threshold verifiable? |
| 10 | Davenport–Heilbronn filter | can a candidate proof be screened against a function whose RH-analogue is false? |
| 11 | DSIN communication | can the involution structure underlie a secure communication protocol? |

The results are not uniform: some are positive, some negative, one is closed as a design
defect.

## 3. What was proved

These are machine-verified results. This is the only category in which the word "proved"
is used without qualification.

### 3.1 In Lean 4

Four of the nine modules are `sorry`-free and `axiom`-free — `DimensionShift`,
`InvolutionEigenspace`, `ZetaBridge`, `DynamicalDesymmetrisation`. The others contain
`sorry` **by design**: they state the Riemann hypothesis, and one of those `sorry`s *is*
the open problem. A test fails if any of them stops containing it.

| theorem | file | statement |
|:---|:---|:---|
| `sigma_involutive` | `ZetaBridge.lean` | `σ ∘ σ = id` for `σ(s) = 1 − conj s` |
| `sigma_fixed_iff_re_eq_half` | `ZetaBridge.lean` | `σ(s) = s ⟺ Re(s) = 1/2` |
| `riemannZeta_zero_conj` | `ZetaBridge.lean` | `ζ(s) = 0 → ζ(conj s) = 0` |
| `riemannZeta_zero_iff_sigma` | `ZetaBridge.lean` | the zero set is `σ`-invariant |
| `riemannHypothesis_iff_no_two_cycle` | `ZetaBridge.lean` | fixedness ⟺ no `σ`-twin zeros ⟺ RH |
| `commute_doubleBracketIncrement` | `DynamicalDesymmetrisation.lean` | the double-bracket increment preserves the involution |
| `commute_euler_step` | `DynamicalDesymmetrisation.lean` | one Euler step preserves the involution |
| eigenspace decomposition `(1 ± T)/2` | `InvolutionEigenspace.lean` | an involution splits the module into its `±1` eigenspaces |

`ZetaBridge.lean` contains 31 declarations, all `sorry`-free. The double-bracket lemmas
depend only on `propext`; the other standard axioms (`Classical.choice`, `Quot.sound`)
appear only where they must.

### 3.2 In exact arithmetic

| result | count | failures |
|:---|---:|---:|
| elliptic curves over `F₅ … F₁₉` satisfying RH | 942 | 0 |
| smooth genus-2 curves over `F₃` satisfying RH | 324 | 0 |
| smooth genus-2 curves over `F₅` satisfying RH | 10 000 | 0 |
| the millionth-prime certificate (`p₁₀₀₀₀₀₀ = 15485863`) | 1 | 0 |

`11 266` curves, no failures. These are the only places in the repository where a
computation *is* a proof, and the reason is the same in each case: the claim is finite and
carries a certificate. A finite claim with a certificate is a theorem; a universal claim
verified on a range is not. That distinction is the subject of
[`verification.md`](verification.md).

## 4. What was falsified

These are the negative results. They are reported with the same care as the positive ones.

### 4.1 The Dimension-Shift Hypothesis — abandoned

The DSH conjectured a family of self-adjoint Hamiltonians on a ℤ₂-graded Hilbert space,
with a discrete involution `σ`, whose spectrum converges to the zeros and whose fixed
locus is the critical line.

**Verdict:** criterion (2) holds. The sector class is **inherited from the input blocks**,
not produced by the `σ` structure.

| input blocks | sector means | full spectrum |
|:---|:---|---:|
| GOE | `0.5279 … 0.5327` | `0.4199 … 0.4248` |
| GUE | `0.5964 … 0.6017` | `0.4199 … 0.4248` |

The full spectrum is the same in both cases. The `σ` structure does not see the input
class; it passes it through. With `[H, σ] = 0` enforced exactly, a GOE model produces GOE
sectors and a GUE model produces GUE sectors — so the construction cannot be the
Hilbert–Pólya operator, because the class is an assumption, not a consequence.

Evidence: [`m5_verdict.md`](m5_verdict.md), 300 seeds per point, `d = 100, 200`.

### 4.2 The shift-zeta — negative

The shift-zeta lifted the Euler product into a ℤ₂-graded algebra and asked whether the
zeros are forced into the fixed locus.

**Verdict:** no. Measured over 600 primes: at `τ = 1` (the degenerate control) the trace
equals the classical Euler-product term for term; at `τ ≠ 1` it departs from `ζ` by
`11–44%` at `s = 2` and is `3.5×–7.5×` larger at the classical zero heights, with no
corresponding dip. The structural reason is compact: every local factor is a polynomial in
one element `γ_τ`, so the product never leaves the two-dimensional subalgebra `ℂ[γ_τ]`.

Evidence: [`shift_zeta_result.md`](shift_zeta_result.md).

### 4.3 The DSIN communication design — closed

The DSIN protocol encoded a bit in the sector parity of a ℤ₂-graded Hilbert space.

**Verdict:** the design is closed — not unproven, closed. A single published observable
carries the bit, so the adversary's measurement is always the right one; no function of
that observable's statistic bounds her information.

Evidence: [`dimension_shift_quantum_communication.md`](dimension_shift_quantum_communication.md) §4.1, a proof.

What survives is an exact commutation result — a `σ`-commuting channel preserves
`Fix(σ)` — which was never a security statement.

### 4.4 The Davenport–Heilbronn filter — its own flagship

The filter screens a candidate's declared inputs against a function whose RH-analogue is
false. The dead list has one entry, and it is this repository's own flagship proposal:
`dimension_shift_w`.

**Verdict:** the DSH declares only inputs that Davenport–Heilbronn also has, so the
argument would have proved a false statement.

Evidence: [`dh_filter.md`](dh_filter.md), and the standalone write-up in
[`dh_filter_methods_note.md`](dh_filter_methods_note.md).

### 4.5 The multi-copy circuit identity — unverified, not refuted

The literature's description of the multi-copy imaginary-time circuits quotes

```
Tr₂(u ρ₁ ⊗ ρ₂ u†) = ρ₁ − ε[[ρ₁, H], ρ₁] + O(ε^{3/2}).
```

The three natural generators that can be built here all produce a first-order term
`i√ε [H, ρ₁]` that the identity does not have, and a second-order term that is not
`±[[ρ,H],ρ]`.

**Verdict: unverified.** This is *not* a negative result about the source: the circuit's
generator was not read, and the identity evidently depends on it. The repository records
a discrepancy and declines to build on either side of it.

## 5. What was corrected

The repository found and fixed several errors — some in its code, some in its claims.
Each has a regression test, and each is on record rather than quietly repaired.

| error | what it was | how it was caught | where it is pinned |
|:---|:---|:---|:---|
| a verdict from one seed | "DSH is SUPPORTED" from one seed per point | 14% of *pure GOE* draws enter the acceptance window by chance; 300 seeds give `0.523 ± 0.069` | `test_falsification.py` |
| a symmetry never enforced | `‖[H,σ]‖/‖H‖ = 1.35 … 1.46` | the commutator was measured instead of assumed; `[H,σ] = 0` is now exact | `test_dimension_shift_chaos.py` |
| a symmetry-breaking attack that broke nothing | the attack left the bit-1 states undisturbed | the vector was `σ`-odd, i.e. inside the bit-1 eigenspace | `test_symmetry_breaking_attack_disturbs_both_encodings` |
| a BB84 "detection" that was a sifting artefact | a basis mismatch was being counted as detection | sifting is not eavesdropping | `test_bb84.py` |
| an Eisenstein enumeration bound | short by a factor of `√2` | verified against the exact count `r₃(n)/6` | `test_zeta_factors.py` |
| a de Bruijn–Newman draft from memory | three errors | `H_0` checked against `(1/8)ξ(1/2 + iz/2)` to `1e-14` | `test_de_bruijn_newman.py` |
| an unreachable Stage-D flag | the "prime-dependent mismatch" could never fire | the `log p` factor cancelled in the prototype | `test_idea_pipeline.py` |
| mpmath stub gaps | `workdps`, `floor`, an `int` defaulting to `...` | AST checks now enforce coverage of every `mp.` name | `test_mpmath_stub.py` |
| a label swap that acquitted a hypothesis | the first M5 run reported *SURVIVES* | points are keyed by class name; the tests assert it | `test_m5_analysis.py` |
| tests that ran themselves | `test_criterion_1/2` were production functions | pytest collected the imported names and ran the grid twice | `test_m5_analysis.py` |
| a figure referenced but never committed | the README embedded an ignored `output/` file | CI failed while the local suite passed | `test_documentation_sync.py` |
| prose that drifted | a README row still said "single seed" after the fix | mechanical guards catch counts, paths, figures, links — not sentences | (manual; recorded in [`lessons_learned.md`](lessons_learned.md)) |

The last row is the honest one: the guards cannot catch a sentence, and the sentences are
where the overstatement lives.

## 6. What survives

Not everything failed. These are the artifacts that outlive the DSH.

### 6.1 The Davenport–Heilbronn filter

A screening tool for any proposed proof of RH. The logic is exact: *an argument that goes
through unchanged where the hypothesis fails cannot establish the hypothesis.* The
inventory has nine rows, each with a source; three are verified by computation, three are
left unsourced rather than guessed, and a candidate declaring an unsourced input receives
no verdict. It is written up as a standalone methods note, independent of the DSH.

This is the strongest contribution in the repository, because it is a verdict procedure
rather than a claim: it decides something about an argument without knowing whether the
argument works.

### 6.2 The desymmetrisation diagnostic

A working instrument for detecting hidden symmetries in quantum spectra. It verifies the
symmetries, splits the spectrum into joint sectors, flags contamination, and estimates the
sector count as a posterior with **measured** coverage — from the sequence of gap ratios,
not their mean.

| true sectors | coverage | posterior on the truth | modal interval |
|:---|---:|---:|:---|
| 1 | `0.99` | `0.97` | `1..1` |
| 2 | `0.92` | `0.66` | `2..2` |
| 3 | `0.91` | `0.24` | `3..≥6` |
| 4 | `0.96` | `0.19` | `3..≥6` |
| 5 | `0.99` | `0.22` | `3..≥6` |
| 6 | `0.98` | `0.22` | `3..≥6` |
| Poisson | `0.78` | `0.24` | `3..≥6` |

The limits are stated: two-sector GOE and GUE are indistinguishable (`0.4232` vs `0.4222`,
`1.4` standard errors of the two means, against a per-spectrum scatter of `0.031`); the
count is not recoverable above two; the false-positive rate is `37` of `400` pure
single-sector GOE spectra. The resolution of the statistic is measured too: the best
single-spectrum class accuracy is `0.790` at one sector and `0.526`, which is chance, at
two, so more spectra sharpen the mean and not the measurement. The dynamical companion (the
double-bracket flow) preserves sector populations for a commuting state and selects a
sector for one that does not, but never touches the Hamiltonian — so it cannot repair a
contaminated spectrum.

Documents: [`desymmetrisation.md`](desymmetrisation.md) and the manuscript
[`desymmetrisation_paper.md`](desymmetrisation_paper.md).

### 6.3 The finite-field certificates

`11 266` curves certified, `0` failures. What this does **not** do: per-curve certificates
do not prove Weil's theorem, and the theorem does not transfer to `ℚ`. The proof runs
through Frobenius on étale cohomology, and no analogue of that action is known over `ℚ`.

### 6.4 The Lean formalization

The fixed locus of `σ` is exactly the critical line; the zero set is `σ`-invariant; and
the implication "invariance ⟹ fixedness" is **itself equivalent to RH**. That last one is
the most valuable statement in the formalization, because it is machine-checked evidence
that the structural route restates the problem rather than solving it.

It is small. It is real.

### 6.5 The documented record of failure

Nineteen sections in [`lessons_learned.md`](lessons_learned.md), each with a measurement.
The DSH is abandoned in [`central_hypothesis.md`](central_hypothesis.md) §10 — in the
document that proposed it. The decisive test is in [`m5_verdict.md`](m5_verdict.md).

The record of a falsified hypothesis is a contribution: it saves the next researcher from
spending months on the same dead end, and it is the only part of a failed program that
transfers.

## 7. What remains open

### 7.1 The Riemann hypothesis

Open. Nothing in this repository changes that. The DSH failed, the shift-zeta failed, the
DSIN design is closed, `σ` is a known affine map, the Hilbert–Pólya prototype has four
measured gaps, and the finite-field success does not transfer to `ℚ`.

The hypothesis is exactly as open as it was when the repository began.

### 7.2 Within the repository

| item | status | why it remains open |
|:---|:---|:---|
| a Lean proof of RH | open | the problem is open; no formalization can close it |
| `zeros_are_fixed_by_sigma` | open, and equivalent to RH | the repository proves the equivalence, not the fact |
| BB84 timing / Trojan-horse channels | open | needs hardware physics, not accounting |
| the DH inventory's unsourced rows | open | no source read supplies them; guessing is what the vocabulary exists to prevent |
| the multi-copy circuit identity | unverified | the generator was not read; three natural candidates disagree |
| the operator screen's symmetry check | unimplemented | the screen still reports raw statistics; wiring the contamination flag into it is not done |
| the `std < 0.02` clause | unreachable as written | it must be redefined at the tested sizes (`0.084`, `0.034`, `0.026` at `2d = 20, 100, 200`) |

### 7.3 The DSH

Closed. The verdict is final. The correct action is to stop.

## 8. What the repository teaches

### 8.1 About the hypothesis

RH is not a problem that will be solved by manipulation within `ℂ`. It needs a structural
explanation of why the critical line exists, and the structural route has been worked for
167 years. The repository's own Lean file proves the precise form of that obstacle:
"invariance implies fixedness" is equivalent to RH, so the functional equation supplies
the symmetry but not the absence of two-cycles.

### 8.2 About method

| lesson | where it appears |
|:---|:---|
| single-seed results are noise | [`lessons_learned.md`](lessons_learned.md) §1 |
| the full spectrum is the wrong question | §3 |
| the class is inherited, not produced | §4 |
| a clause unreachable at the tested sizes is a prohibition | §5 |
| document the defects alongside the verdict | §6 |
| a negative result is a contribution | §10, §15–§19 |
| an instrument is not a measurement | §18 |
| a dynamical analogue is not the same tool | §19 |

### 8.3 About instruments

The DSH failed as a proof strategy and succeeded as a diagnostic. The transition from
failed hypothesis to working tool is the ordinary trajectory of scientific work, and it is
the part that other people can use.

An instrument that prevents a specific error is a contribution. It is not a proof of the
grand conjecture. It is what makes the next attempt harder to fool.

## 9. The final inventory

| category | count | files |
|:---|---:|:---|
| tracks attempted | 11 | — |
| tracks closed as negative | 3 | DSH, shift-zeta, DSIN |
| tracks with surviving instruments | 2 | the DH filter, the desymmetrisation diagnostic |
| tracks with finite proofs | 2 | finite-field curves, prime certificates |
| `sorry`-free Lean modules | 4 of 9 | `DimensionShift`, `InvolutionEigenspace`, `ZetaBridge`, `DynamicalDesymmetrisation` |
| tests passing | 1231 | `python/tests/` |
| documents | 38 | `docs/` |
| negative results on record | 19 sections | [`lessons_learned.md`](lessons_learned.md) |
| corrections with regression tests | 12 | §5 above |
| manuscripts | 2 | [`desymmetrisation_paper.md`](desymmetrisation_paper.md), [`dh_filter_methods_note.md`](dh_filter_methods_note.md) |

### 9.1 Document index

| document | what it is |
|:---|:---|
| [`lessons_learned.md`](lessons_learned.md) | the negative results and the methodological lessons, §1–§19 |
| [`central_hypothesis.md`](central_hypothesis.md) | the DSH as proposed, and its abandonment in the same document (§10) |
| [`m5_verdict.md`](m5_verdict.md) | the decisive test, with the defects and the numbers |
| [`desymmetrisation.md`](desymmetrisation.md), [`desymmetrisation_paper.md`](desymmetrisation_paper.md) | the diagnostic, and its manuscript |
| [`build_workflow.md`](build_workflow.md) | how the manuscript becomes a verified PDF, and the two failures that shaped the checks |
| [`submission_checklist.md`](submission_checklist.md), [`cover_letter.md`](cover_letter.md) | submission materials, unsent |
| [`dh_filter.md`](dh_filter.md), [`dh_filter_methods_note.md`](dh_filter_methods_note.md) | the screening filter, and its methods note |
| [`hilbert_polya.md`](hilbert_polya.md), [`operator_candidates.md`](operator_candidates.md), [`pt_symmetric_hilbert_polya.md`](pt_symmetric_hilbert_polya.md) | the operator attempts and their measured gaps |
| [`verification.md`](verification.md) | what "verified" means here: finite evidence versus universal claim |
| [`future_work.md`](future_work.md) | milestones and what is left in each |
| [`chirality.md`](chirality.md), [`zeta_factors.md`](zeta_factors.md), [`graded_prime_monoid.md`](graded_prime_monoid.md) | the algebraic and arithmetic tracks |
| [`number_systems.md`](number_systems.md), [`spherical_number_systems.md`](spherical_number_systems.md) | the dimension-lift proposals and their status |
| [`bb84_implementation.md`](bb84_implementation.md), [`dimension_shift_quantum_communication.md`](dimension_shift_quantum_communication.md) | the communication tracks |
| [`claimed_proof_triage.md`](claimed_proof_triage.md), [`openai_math_quasi_riemann.md`](openai_math_quasi_riemann.md) | the triage of outside claims |
| [`scientific_contribution_assessment.md`](scientific_contribution_assessment.md), [`project_critique_and_roadmap.md`](project_critique_and_roadmap.md) | what this is worth, and what it should do next |
| [`state_of_the_project.md`](state_of_the_project.md) | this document |

## 10. Four sentences

From the README:

> *"Several tracks here do fail, on purpose and on record: a negative result obtained by a
> stated method is worth more than an unfalsifiable claim of progress."*

From [`lessons_learned.md`](lessons_learned.md) §1:

> *"The corrected verdict is mixed, and 'mixed' is not a success."*

From [`m5_verdict.md`](m5_verdict.md):

> *"The class is inherited from the input blocks, not produced by the construction."*

From [`desymmetrisation.md`](desymmetrisation.md):

> *"Desymmetrise before testing the class."*

Those four describe the project exactly. It is not the RH. It is science.

## 11. A note to the next reader

If you came looking for a path to the Riemann hypothesis: this is not it. The DSH is
abandoned, the shift-zeta is negative, `σ` is a known affine map, and the Hilbert–Pólya
prototype has four measured gaps.

If you came looking for an honest research record — what was attempted, measured,
corrected, and what survives — read §2 to §7, then the documents in §9.1.

If you came looking for a diagnostic for hidden symmetries in spectra, use
`python/riemann_framework/desymmetrisation.py`. It is calibrated, its limits are stated,
and its false-positive rate is measured.

If you came looking for a screen for a proposed proof of RH, use
`python/riemann_framework/dh_filter.py`. It is independent of everything else here, and it
is the artifact most likely to be useful to someone else.

The DSH failed. The instrument survived. That is the correct outcome.

## 12. Closing statement

This repository records a research program that was pursued, tested, and closed when the
evidence required it.

It did not prove the Riemann hypothesis. It did not find a new number system that solves
the problem. It did not produce a Hilbert–Pólya operator.

It did produce:

- a falsification filter that killed its own flagship idea;
- a diagnostic instrument with measured coverage and stated limits;
- a formal verification of the involution's structure, and of the fact that the
  structural equivalence *is* the hypothesis;
- a finite-field proof for 11 266 curves;
- a documented record of nineteen negative results;
- two manuscripts on working methods.

That is what research looks like when the central hypothesis fails.

### 12.1 The artifacts, and the pipeline that makes them

The two manuscripts are not the only artifacts. Each one is the output of a script, and
each script is checked by something that has failed before:

| artifact | produced by | checked by |
|:---|:---|:---|
| `output/desymmetrisation_paper.pdf` | `scripts/build_manuscript_pdf.py` (Markdown → LaTeX → `pdflatex`) | `scripts/verify_pdf.py`, 27 checks |
| the five figures in `output/` | `scripts/generate_desymmetrisation_figures.py` and `scripts/generate_seed_study_figure.py` | `tests/test_desymmetrisation_figures.py` |
| the manuscript's figure references | the Markdown | `tests/test_manuscript_figures.py` |
| this document's counts | the tree | `tests/test_documentation_sync.py` |

The whole workflow — including the two failures that produced its checks (browser
furniture on every page; a figure whose natural width exceeded the page) — is written up
in [`build_workflow.md`](build_workflow.md). One command runs it:

```bash
python scripts/build_and_verify.py
```

That is the last thing worth saying about the repository as an *instrument*: the claims
are only as good as their reproduction, and the reproduction is a script with a failing
case behind every check in it.

The Riemann hypothesis remains open. The next attempt will be more careful because of what
is recorded here.

---

**Status:** closed as a research program; retained as an instrument.

**Last verified:** `python -m pytest tests/ -q` → `1231 passed`; `lake build` → 10 modules
compile, the 4 `sorry`-free modules remain `sorry`-free;
`python scripts/build_and_verify.py` → 25 PDF checks pass;
`python scripts/generate_desymmetrisation_figures.py` reproduces the manuscript's figures.

**Manuscripts:** [`desymmetrisation_paper.md`](desymmetrisation_paper.md) (draft, not
submitted), [`dh_filter_methods_note.md`](dh_filter_methods_note.md) (draft, not
submitted).
