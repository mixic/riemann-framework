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

# State of the Project — closing summary

**The Riemann hypothesis is open.** Nothing in this repository proves or disproves it,
and nothing here is evidence for or against it. What the repository contains is a
numerical core, a set of claims stated precisely enough to be refuted, the refutations,
and two instruments that survived the refutations.

This document is the one-page version. It is written to be read without the rest of the
repository; every claim in it is reproducible from the code, and every number is pinned
by a test that can fail.

## 1. The bottom line

| category | contents |
|:---|:---|
| **Proved** (strict sense, finite) | RH over finite fields, per curve: 942 elliptic over `F₅…F₁₉`, 324 genus-2 over `F₃`, 10 000 over `F₅`, zero failures; `15485863` is the millionth prime; `σ² = id` and the fixed locus of `σ` in Lean; the double-bracket invariance lemmas in Lean |
| **Measured** (finite evidence, explicitly not proof) | the zero statistics and explicit formula; the imaginary-time dictionary; the desymmetrisation calibration and its posterior; the DH filter's inventory |
| **Falsified or closed** | the Dimension-Shift Hypothesis (abandoned); the single-observable DSIN channel; the graded shift-zeta lift; the hard-box regularisation; "GUE statistics certify a candidate" |
| **Open** | RH itself; the Lean `zeros_are_fixed_by_sigma` obligation (which *is* RH); the two unsourced rows of the DH inventory; whether the multi-copy circuit identity is right |

## 2. What was attempted

| track | what it tried | verdict |
|:---|:---|:---|
| Numerical core | verify zeros, explicit formula, zero statistics | working |
| Finite-field RH | prove RH per curve by exact arithmetic | proved, per curve |
| Prime certificates | certify the millionth prime | proved |
| Dimension-Shift Hypothesis | a discrete involution whose fixed locus is the critical line, lifted to an operator | **abandoned** — the sector class is inherited, not produced |
| Quantum chaos | the zeros' spacing statistics, and what they can certify | measured; the certification claim died |
| Hilbert–Pólya | build a candidate operator and measure its gaps | four gaps measured, no eigenvalue |
| Operator candidates | screen candidates on statistics | negative: a prime-length graph fits GUE better than the zeros do |
| DSIN | a communication model on a single published observable | closed: one observable cannot bound an adversary |
| BB84 layer | detector blinding, power monitor, defences | modelled; one gap closed, one left open |
| Davenport–Heilbronn filter | screen arguments by what they would also prove for a false statement | **working instrument** |
| Desymmetrisation | the silent failure mode of spacing statistics | **working instrument with measured limits** |

## 3. What worked

The two instruments are the part that survived, and both survived because they are
honest about what they cannot do.

**The Davenport–Heilbronn filter.** A candidate argument declares the inputs it uses;
each is looked up in an inventory of nine that records whether it transfers to a function
whose RH-analogue is false. The verdicts are `dead`, `eligible`, `needs_sourcing`. Run
against this repository's own records, it returns one `dead` entry, and that entry is the
repository's flagship proposal. Its written-up form is
[`dh_filter_methods_note.md`](dh_filter_methods_note.md).

**The desymmetrisation diagnostic.** A spectrum of a Hamiltonian commuting with an
involution is a union of sectors, and `⟨r⟩` measured on the full spectrum is a property
of the superposition:

| unresolved sectors | GOE | GUE |
|:---|---:|---:|
| 1 | `0.531` | `0.600` |
| 2 | `0.426` | `0.421` |
| 3 | `0.404` | `0.399` |
| 6 | `0.391` | `0.389` |

The diagnostic verifies the symmetries, splits, flags contamination, and — from the
sequence of gap ratios rather than their mean — estimates the sector count as a posterior
with **measured** coverage (`1.00, 0.93, 0.87, 0.98, 1.00, 0.97, 0.78` for
`1, 2, 3, 4, 5, 6, ≥6/poisson`). It counts one sector decisively (`p = 0.98`, interval
`1..1`), bounds two (`2..5`), and refuses above two. Its false-positive rate is `4 of 40`.
Its manuscript is [`desymmetrisation_paper.md`](desymmetrisation_paper.md).

**The Lean development.** Nine modules compile; four are `sorry`- and `axiom`-free
(`DimensionShift`, `InvolutionEigenspace`, `ZetaBridge`, `DynamicalDesymmetrisation`).
The RH statements carry `sorry` by design: one of them *is* the open problem, and the
suite fails if that ever stops being true.

## 4. What failed, and why that was the useful outcome

| claim | how it died |
|:---|:---|
| The Dimension-Shift Hypothesis | tested by its own criteria: the sector class is inherited from the input blocks, not produced by the `σ` structure (M5) |
| "DSH is SUPPORTED" | one seed of a 90-point grid; 300 seeds give `0.523 ± 0.069`, and 14% of pure GOE draws enter the window |
| A `σ`-symmetric model reaching GUE | the model's commutator was `1.35…1.46` (not a symmetry at all); with `[H,σ] = 0` enforced, the sectors are GOE when the blocks were |
| A single published observable in DSIN | no function of it bounds an adversary's information |
| The graded shift-zeta lift | the functional equation fails for `τ ≠ 1` |
| A hard-box regularisation of `xp` | an evenly spaced ladder, `r = 1.000` against `0.610`, and `2.10×` overcounting at `T = 50` |
| "GUE statistics certify a candidate" | a prime-length graph scores `r = 0.641`, KS `0.0438` to Wigner — better than the zeros' own `0.610` / `0.0579` — with a linear counting function |
| A multi-copy circuit identity | every natural generator produces a first-order term the identity does not have; recorded unverified |

Each death is documented with its measurement. The general lessons are in
[`lessons_learned.md`](lessons_learned.md) §1–§19, and the M5 verdict is in
[`m5_verdict.md`](m5_verdict.md).

## 5. What was corrected

The recurring failure of this repository was not a wrong theorem. It was a claim that
stopped being true quietly. The corrections are part of the record:

- A verdict from one seed, replaced by 300 seeds with error bars.
- A symmetry that was never enforced (`‖[H,σ]‖ = 1.35…1.46`), now `0.0` exactly.
- A window calibrated on one draw, now calibrated on sampled references.
- A label swap that acquitted the hypothesis in the M5 run.
- Production functions named `test_*`, which pytest collected and ran twice.
- A figure referenced from the README, on disk, and never committed — the CI failure that
  produced the guard requiring every embedded figure to be git-tracked.
- Prose that drifted: a README row still saying "single seed" after the fix. Mechanical
  guards check counts, paths, figures and links; none can catch a sentence, and the
  sentences are where the overstatement lives.

## 6. What remains

| open item | why it is open |
|:---|:---|
| RH | it is the open problem; nothing here touches it |
| the Lean obligation `zeros_are_fixed_by_sigma` | it is equivalent to RH; the repository proves the equivalence, not the fact |
| the DH inventory's two unsourced rows | no source was read that supplies them, and guessing is what the vocabulary exists to prevent |
| the multi-copy circuit identity | the generator was not read; three natural candidates disagree with the quoted form |
| the two-sector class test | GOE and GUE are indistinguishable there; no statistic in this repository resolves it |
| the operator screen's symmetry check | the screen still reports raw statistics; wiring the contamination flag into it is unimplemented |

## 7. How to verify

```bash
python -m pytest tests/ -q                     # from python/ ; 1107 tests
python scripts/generate_desymmetrisation_figures.py
python scripts/run_dh_filter.py
lake build                                     # from the repository root
```

`tests/test_documentation_sync.py` compares the README against live artefacts: per-file
test counts, every module, test file and document, every embedded figure (against the
filesystem *and* git's index), and every internal link.

## 8. Document index

| document | what it is |
|:---|:---|
| [`lessons_learned.md`](lessons_learned.md) | the negative results and the methodological lessons, §1–§19 |
| [`central_hypothesis.md`](central_hypothesis.md) | the DSH as proposed, and its abandonment in the same document (§10) |
| [`m5_verdict.md`](m5_verdict.md) | the decisive test, with the defects and the numbers |
| [`desymmetrisation.md`](desymmetrisation.md) | the static and dynamical diagnostics, the tables, the limits |
| [`desymmetrisation_paper.md`](desymmetrisation_paper.md) | the manuscript for the diagnostic |
| [`submission_checklist.md`](submission_checklist.md), [`cover_letter.md`](cover_letter.md) | submission materials, unsent |
| [`dh_filter.md`](dh_filter.md) | the DH filter, its inventory and the dead list |
| [`dh_filter_methods_note.md`](dh_filter_methods_note.md) | the filter as a standalone methods note |
| [`hilbert_polya.md`](hilbert_polya.md), [`operator_candidates.md`](operator_candidates.md), [`pt_symmetric_hilbert_polya.md`](pt_symmetric_hilbert_polya.md) | the operator attempts and their measured gaps |
| [`verification.md`](verification.md) | what "verified" means here: finite evidence versus universal claim |
| [`future_work.md`](future_work.md) | milestones, and what is left in each |
| [`chirality.md`](chirality.md), [`zeta_factors.md`](zeta_factors.md), [`graded_prime_monoid.md`](graded_prime_monoid.md) | the algebraic and arithmetic tracks |
| [`number_systems.md`](number_systems.md), [`spherical_number_systems.md`](spherical_number_systems.md) | the dimension-lift proposals and their status |
| [`bb84_implementation.md`](bb84_implementation.md), [`dimension_shift_quantum_communication.md`](dimension_shift_quantum_communication.md) | the communication tracks |
| [`claimed_proof_triage.md`](claimed_proof_triage.md), [`openai_math_quasi_riemann.md`](openai_math_quasi_riemann.md) | the triage of outside claims |
| [`scientific_contribution_assessment.md`](scientific_contribution_assessment.md), [`project_critique_and_roadmap.md`](project_critique_and_roadmap.md) | what this is worth, and what it should do next |

## 9. Closing

The flagship hypothesis is dead. It was proposed in a document that now carries its
verdict, tested by criteria it stated itself, and abandoned with the numbers attached.

What survived is not a theorem about the zeros. It is a screening filter for arguments
about them, a diagnostic for a silent failure mode in quantum spectra, and a set of
machine-checked lemmas that are exactly as strong as their statements.

A repository that refutes its own flagship and keeps the tools is in the correct state.
The alternative — a hypothesis defended by adjusting the criteria — is the failure this
repository was built to avoid.
