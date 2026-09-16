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

# Future Work

This document is the forward-looking engineering and research backlog for the
Riemann Framework. It separates work that improves software reliability from
work that could produce new mathematical or scientific results.

## Guiding Principle

Every future experiment should state:

- the hypothesis being tested;
- the baseline or control model;
- the parameters and random-seed policy;
- the success and falsification criteria; and
- the limits of what the result can establish.

A passing test confirms an implementation property. It does not prove the
Riemann Hypothesis, the Dimension-Shift Hypothesis, or DSIN security.

## Priority 1: Correct the Model Contract

### 1.1 Enforce involution symmetry

The dimension-shift Hamiltonian should make its symmetry contract explicit.
When the model claims `[H, sigma] = 0`, construct matching sector blocks and
measure the commutator norm in tests.

**Acceptance criteria:**

- a symmetric Hamiltonian mode satisfies `||[H, sigma]|| = 0` up to numerical
  precision;
- a symmetry-breaking mode reports a nonzero commutator;
- the documentation distinguishes the spectral-statistics model from the
  commuting DSIN channel model.

### 1.2 Separate model construction from experiments

Keep matrix builders and mathematical definitions independent from parameter
sweeps, plotting, and report generation.

**Acceptance criteria:**

- model functions are deterministic under a supplied seed;
- experiments can consume a pre-built matrix;
- plotting scripts do not contain hidden model definitions.

## Priority 2: Strengthen the Evidence

### 2.1 Add matched reference ensembles

For every dimension-shift spectrum, compare same-size GOE, GUE, and Poisson
controls. Report mean `r`, KS distances, sample size, and seed.

### 2.2 Repeat across seeds

A single favorable seed is not robust evidence. Run each parameter point over a
fixed seed set and report mean, standard deviation, and confidence intervals.

**Acceptance criteria:**

- the falsification report includes seed count;
- verdicts distinguish a single-point match from stable behavior;
- results are reproducible from a saved configuration.

### 2.3 Improve the falsification verdict

Replace the current “any GUE point means supported” interpretation with
explicit categories such as:

- `single_point_match`;
- `robust_support`;
- `not_supported`;
- `inconclusive`.

Require a minimum number of parameter points and seeds for `robust_support`.

### 2.4 Extend spectral-density testing

The M3 diagnostic currently compares finite normalized cumulative counts. Extend
it to multiple matrix dimensions and height ranges, and report finite-size
scaling against the Riemann-von Mangoldt reference.

A successful local-spacing match is not a density match. Both must be measured
separately.

## Priority 3: Improve Software Quality

### 3.1 Centralize validation

Create shared validators for dimensions, coupling, matrix shapes, probabilities,
seeds, and finite numeric inputs. Use them across the dimension-shift and DSIN
modules.

### 3.2 Use typed result objects

Replace loosely structured dictionaries in experiment reports with dataclasses
or typed dictionaries. Document units and meanings for every field.

### 3.3 Screen candidate formulas before building numerics on them

Every candidate operation on the complex slice should be pushed through the
affine-reduction gate before any numerical work is invested in it. The gate is
`python/riemann_framework/affine_reduction.py`; an expression that is affine in
`(s, conjugate(s))` is a known similarity of the plane and is not a new
algebraic object.

**Status:** implemented, with the dimension-shift prototype recorded as
failing the gate (`docs/dimension_shift_involution.md`, section 2.1). The gate
covers closed-form expressions in `s` and `s_conj` only; it says nothing about
operator-level or arithmetic-level structure, which is where the programme's
remaining content actually lives.

### 3.3 Add package entry points

Define command-line entry points in `python/pyproject.toml` for:

- falsification reports;
- dimension-shift plots;
- DSIN simulations; and
- standard zeta plots.

This should remove the need for manual `sys.path` changes in scripts while
preserving direct module execution.

### 3.4 Maintain focused tests

Keep tests deterministic and behavior-focused. Prefer repeated-seed statistical
assertions over brittle single-seed thresholds. Add regression tests whenever
a simulation bug is corrected.

## Priority 4: Formalization

The Lean formalization should grow from small independent facts:

1. sector swap squares to identity;
2. sector swap is injective and has no fixed sector labels;
3. finite `+1` and `-1` eigenspaces have equal dimension;
4. a commuting operator preserves involution eigenspaces;
5. finite matrix symmetry assumptions imply real eigenvalues;
6. a finite zero-mode count has the stated index under explicit assumptions.

None of these lemmas proves RH. Their purpose is to make the algebraic core
precise before attempting analytic or spectral claims.

**Status.** Items 1 and 2 are done in `lean/RiemannFramework/DimensionShift.lean`
(`sigma_squared`, `sigma_injective`, `sigma_not_fixed`), which needs no Mathlib
import. The general involution layer is in progress in
`lean/RiemannFramework/InvolutionEigenspace.lean`:

- done: for an endomorphism `T` with `T * T = 1` over any field, the `+1` and
  `-1` eigenspaces are the kernels of `T - 1` and `T + 1`
  (`eigenspace_one_eq_ker_sub_one`, `eigenspace_neg_one_eq_ker_add_one`), and
  `T - 1` and `T + 1` annihilate each other (`sub_one_comp_add_one`,
  `add_one_comp_sub_one`);
- open: the matching range descriptions, the equal-dimension and
  complementary results, and item 4 above. These reduce to a rank-nullity
  computation over `Nat` (`finrank` coercions plus `Nat` truncated
  subtraction) that has not yet been closed.

### 4.1 Proven vs. open, by file

This is the honest ledger of the Lean development. "Proven" means the
declaration compiles with no `sorry` and no `axiom`. The test suite enforces both
directions of the ledger (`python/tests/test_formal_proof.py`):

- `test_sorry_free_file_is_complete` fails if a module recorded here as proven
  starts containing a `sorry` or an `axiom`;
- `test_rh_statement_stays_open` fails if a module recorded here as carrying an
  open target stops reporting `sorry`, that is, if a claim of having proved RH
  appears without independent verification.

| File | Proven | Open (`sorry`) |
|:---|:---|:---|
| `DimensionShift.lean` | `sigma_squared`, `sigma_injective`, `sigma_not_fixed` | — |
| `InvolutionEigenspace.lean` | the four kernel/eigenspace and mutual-annihilation lemmas listed above | — (refinements in item 4 above) |
| `SanityChecks.lean` | all worked examples for `σ` | — |
| `ZetaBridge.lean` | all 31 declarations: `sigma`, `sigma_re`, `sigma_im`, `sigma_involutive`, `fixed_point_of_re_eq_half`, `re_of_fixed_point_eq_half`, `sigma_fixed_iff_re_eq_half`, `riemannZeta_zero_conj`, `riemannZeta_zero_one_sub`, `cos_pi_mul_div_two_ne_zero`, `riemannZeta_one_sub_prefactor_ne_zero`, `riemannZeta_zero_iff_one_sub`, `riemannZeta_zero_sigma` (`σ`-invariance), `riemannZeta_zero_iff_conj`, `riemannZeta_zero_iff_sigma`, `riemannZeta_zero_quadruple`, `rh_iff_zeros_fixed_by_sigma`, `fixed_on_zeros_iff_no_distinct_reflection`, `riemannHypothesis_iff_no_two_cycle`, and the Section 5 verdict | — |
| `ZetaConjecture.lean` | `RiemannHypothesisStatement`, `rh_of_zeros_fixed_by_sigma`, `prove_rh_via_sigma` | `zeros_are_fixed_by_sigma` |
| `NewIdeaTest.lean` | `RHIdea`, `RHIdea.riemannHypothesisStatement`, `testMyIdea.is_involution`, `testMyIdea.eval_re` | `testMyIdea.fixed_on_zeros` |
| `RiemannHypothesis.lean` | the definitions `IsNontrivialZero`, `IsOnCriticalLine` | `riemann_hypothesis` |
| `RiemannHypothesis_optimized.lean` | the Clay equivalences (`iff_real_part`, `iff_mathlib`, `of_mathlib`, `mathlib`) and every supporting lemma | `clay_prize_riemann_hypothesis` |

The core algebraic result is fully proven: the fixed locus of `σ` is exactly the
critical line (`sigma_fixed_iff_re_eq_half`). There is exactly one open statement
in the formalization, written in four syntactic forms across the four files
above: *every nontrivial zero of `ζ` is fixed by `σ`*.

**Where the gap actually is.** It is *not* in the analytic bridge to Mathlib's
functional equation. That bridge is complete and `sorry`-free. Composing
`Λ(1 - s) = Λ(s)` with `ζ(conj s) = conj (ζ s)` proves `ζ s = 0 → ζ (σ s) = 0`,
so the zero set of `ζ` is `σ`-invariant.

Because `σ` is an involution, `σ`-invariance partitions the zeros into orbits of
size 1 or 2; and since `σ` preserves the imaginary part while reflecting the real
part about `1/2`, a size-2 orbit is a *pair of distinct zeros at the same height
whose real parts sum to 1*. The functional equation therefore reformulates the
open obligation exactly as

> there are no `σ`-twin nontrivial zeros

(`riemannHypothesis_iff_no_two_cycle`). The functional equation supplies the
symmetry; it cannot supply the absence of 2-cycles. Indeed
`strip_invariance_imp_fixedness_iff_riemannHypothesisOnStrip` proves that, since
invariance is a theorem, the implication "invariance implies fixedness" is
*itself* equivalent to RH.

**The `cos (π s / 2)` prefactor: closed, and never needed.** An earlier draft
inside `ZetaBridge.lean` took `fixed_on_zeros` to require the functional-equation
prefactor `2 · (2π)^{-s} · Γ(s) · cos(π s / 2)` to be non-zero, and recorded
"`Gamma_conj_ne_zero`" and "`cos` non-zero" as open. Two separate things are true
about that.

*It was never needed.* Mathlib's `riemannZeta_one_sub` states

    ζ(1 - s) = 2 * (2 * π) ^ (-s) * Gamma s * cos (π * s / 2) * ζ(s),

so `ζ s = 0` yields `ζ (1 - s) = 0` outright: the left-hand side is
*proportional* to `ζ s`. Nonvanishing of the prefactor is needed only for the
converse. `riemannZeta_zero_sigma` therefore carries only the side conditions
`0 < re s < 1` — which make `riemannZeta_one_sub` applicable and are stable under
`conj`.

*It is also now closed*, because closing it buys a genuine strengthening — the
zero symmetry as an **equivalence** rather than a one-way implication:

- `cos_pi_mul_div_two_ne_zero`: on the strip, `cos (π s / 2) ≠ 0`. Mathlib's
  `Complex.cos_eq_zero_iff` gives `cos θ = 0 ↔ θ = (2k+1)π/2`, so
  `cos (π s / 2) = 0` forces `s = 2k + 1`; its real part `2k + 1` then cannot lie
  in `(0, 1)`, since `0 < 2k + 1 < 1` would put the integer `k` strictly between
  `-1/2` and `0`.
- `riemannZeta_one_sub_prefactor_ne_zero`: the full prefactor is non-zero on the
  strip, from the above together with `Complex.Gamma_ne_zero_of_re_pos` (`Γ` has
  no zeros) and `cpow_ne_zero_iff`.
- `riemannZeta_zero_iff_one_sub` and `riemannZeta_zero_iff_sigma`: the functional
  equation's zero symmetry and the `σ`-invariance, each as an `↔`, by dividing by
  the prefactor.
- `riemannZeta_zero_iff_conj`: conjugation symmetry as an `↔`.

So the ledger has 31 declarations in `ZetaBridge.lean`, none with a `sorry`.
This does **not** change the verdict below: an equivalence of zero sets is still
weaker than the fixedness the wall demands, and the gap remains the 2-cycles.

Four things had to be fixed before the original draft compiled: `open scoped
ComplexConjugate` (`conj` is scoped notation; `open Complex` alone does not bring
it in), `open scoped Real` (without it `π` is read as an auto-implicit *variable*
rather than `Real.pi`, and then `π` and Mathlib's `↑Real.pi` silently become
different terms), the `Mathlib.NumberTheory.Harmonic.ZetaAsymp` import
(`riemannZeta_conj` does not live in the `RiemannZeta` module), and a definition
of `sigma` itself, which now lives in `ZetaBridge.lean` and is imported by
`ZetaConjecture.lean` — defining it in the latter would make the import circular.

One trap when editing this file: unrestricted `simp` **diverges** on any goal
containing `conj`, because in this Mathlib `starRingEnd_apply` and `star_def`
rewrite into each other; use `simp only` with an explicit lemma list, or plain
`rw`. A related trap: `rw` matches syntactically, so a lemma stated with `star`
will not fire on a goal containing `conj` (= `starRingEnd ℂ`) even though they are
definitionally equal — `riemannZeta_zero_iff_conj` needs an explicit
`starRingEnd_apply` step for exactly this reason.

**Next step.** Not a trigonometric lemma — that is done. The only remaining step
is the negative half of `riemannHypothesis_iff_no_two_cycle`: show that no
2-cycle exists. That is RH, and no side-condition work inside the functional
equation can supply it.

## Priority 5: Arithmetic Grounding

The dimension-shift model currently has no derived prime structure. Future work
must address:

- how prime elements or periodic orbits are represented;
- how `log(p)` weights arise;
- how the Euler product is recovered;
- how the Riemann-von Mangoldt density emerges; and
- how an exact zero-to-spectrum correspondence would be stated.

A model that reproduces only GUE statistics remains a universality-class model,
not an arithmetic model of zeta.

### 5.1 The primon gas supplies an exact anchor

`python/riemann_framework/primon_gas.py` implements the one operator in this
project whose trace provably is the Euler product: on `l^2(N)` with
`H|n> = log(n)|n>`, `Tr[e^{-sH}] = zeta(s)` for `Re(s) > 1`. This closes the
first two bullets above in the only sense currently available:

- `log(p)` weights arise as the oscillator energies, one bosonic mode per prime;
- the Euler product is recovered exactly, from unique factorisation, not fitted.

**Status:** implemented and tested. What remains open is everything from the
third bullet onward: the eigenvalues are `log(n)`, not the zero ordinates, so
the Riemann-von Mangoldt density and the zero-to-spectrum correspondence are
untouched. This anchors M6, not M7.

### 5.2 Use the anchor as a target, not just a demonstration

Any proposed symmetry should now be tested against `H` rather than only against
GUE statistics. `python/riemann_framework/operator_symmetry.py` does this and
records a negative result: the natural lift of the dimension-shift involution
onto `l^2(N)` -- permuting prime exponents -- provably cannot commute with `H`,
because `H` has simple spectrum and the permutation is not diagonal. See
`docs/central_hypothesis.md` section 3.2 for the caveats that travel with it.

**Next:** a candidate that acts on a non-diagonal representation, in the spirit
of the Bost-Connes Galois action, rather than a basis permutation.

## Priority 6: DSIN Research Track

DSIN should remain explicitly downstream and speculative. Future work should:

- define a complete noise and adversary model;
- distinguish symmetry covariance from topological protection;
- measure information leakage as well as bit error rate;
- compare with established BB84 security definitions; and
- avoid claims of security until a composable proof exists.

A physical implementation would require controllable sector preparation,
sector-projector measurement, calibrated noise, and an independently verified
attack model.

## Suggested Release Milestones

| Release | Goal | Exit criterion |
|:---|:---|:---|
| R1 | Reproducible numerical baseline | Controls, seeds, and artifacts are recorded |
| R2 | Correct symmetry contract | Commutator tests pass for symmetric and broken modes |
| R3 | Robust falsification | Multi-seed verdicts and finite-size scaling are reported |
| R4 | Density study | M3 results cover multiple dimensions and height ranges |
| R5 | Lean algebra core | Initial sector and eigenspace lemmas compile and are tested |
| R6 | Arithmetic model | Prime weights and Euler-product relation are explicitly defined |
| R7 | Research decision | Evidence supports continued pursuit or a documented abandonment |

## Open Decision

The project should not optimize parameters indefinitely to enter the GUE window.
After controls, repeated seeds, density tests, and formal algebra are complete,
the evidence should determine whether the Dimension-Shift Hypothesis deserves
further development or should be recorded as a negative result.
