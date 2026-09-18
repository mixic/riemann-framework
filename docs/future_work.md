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

**Status.** Items 1, 2 and 4 are done.

Items 1 and 2 are in `lean/RiemannFramework/DimensionShift.lean`
(`sectorSwap_squared`, `sectorSwap_injective`, `sectorSwap_not_fixed`), which
needs no Mathlib import. The swap is named `sectorSwap` rather than `sigma`
because `RiemannFramework.sigma` is the critical-line reflection in
`ZetaBridge.lean`; both are in the same namespace, and two `sigma`s there made
any file importing both fail to compile.

Item 4 is in `lean/RiemannFramework/InvolutionEigenspace.lean`
(`maps_eigenspace_one`, `maps_eigenspace_neg_one`, via `maps_ker_sub_one` and
`maps_ker_add_one`). It is worth recording that this was mis-scoped in an earlier
revision of this document, which grouped item 4 with the rank-nullity work below.
It does not need rank-nullity, or finite dimension, or any characteristic
assumption: a commuting operator preserves an eigenspace because the map is well
defined on it, in about five lines. It was the cheapest item on the list, not one
of the hard ones.

The general involution layer in `InvolutionEigenspace.lean`:

- done: for an endomorphism `T` with `T * T = 1` over any field, the `+1` and
  `-1` eigenspaces are the kernels of `T - 1` and `T + 1`
  (`eigenspace_one_eq_ker_sub_one`, `eigenspace_neg_one_eq_ker_add_one`); `T - 1`
  and `T + 1` annihilate each other (`sub_one_comp_add_one`,
  `add_one_comp_sub_one`); and a commuting operator preserves both eigenspaces
  (item 4, `maps_eigenspace_one`, `maps_eigenspace_neg_one`);
- open: the matching range descriptions, and the equal-dimension and
  complementary results (item 3). *These* are the ones that reduce to a
  rank-nullity computation over `Nat` (`finrank` coercions plus `Nat` truncated
  subtraction), and that has not yet been closed.

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
| `DimensionShift.lean` | `sectorSwap_squared`, `sectorSwap_injective`, `sectorSwap_not_fixed` | — |
| `InvolutionEigenspace.lean` | the four kernel/eigenspace and mutual-annihilation lemmas listed above, plus `maps_eigenspace_one` / `maps_eigenspace_neg_one` (item 4) | — (range descriptions and item 3 in the list above) |
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

**Verdict: the design is closed.** DSIN as specified — a single published
observable carrying the bit — cannot provide security, and this is now proved
rather than suspected. Section 4.1 of
`dimension_shift_quantum_communication.md` shows that no function of its
statistic bounds the adversary's information, with an explicit attack that
recovers every bit (`1.0000`) while producing `BER = 0.0000`, detection `0.0000`,
and a deviation bit-identical to a noiseless channel. Section 4.3 shows the
entropic route is unavailable to a single-observable design. And §4.4.1 shows
that the obvious repairs *relocate* the obstruction rather than remove it: the
adversary's payload measurement is a logical operator, and no stabilizer can see
one. The one repair that would work — two mutually unbiased observables — is
high-dimensional QKD, an occupied class with a working composable-secure
realisation, so it is not a DSIN result.

This closes the *design*, not the repository. The track's one exact positive
result is untouched: a `sigma`-commuting channel preserves `Fix(sigma)`, with
`||[H, sigma]||_F = 0.00e+00` at machine precision up to `d = 12`. It was true
before this track existed and remains a small true theorem. What the track got
wrong was reading it as a security statement — it says nothing about what an
adversary can do *inside* the fixed locus, and that is exactly where the attack
lives.

The requirements below are kept as the record of what was asked for before the
simulation existed; the status block records what happened to each. Section 4.4
of the protocol document is an inventory of what a successor would have to
satisfy. It is not a plan, and it should not be read as the design surviving
under another name.

Should DSIN ever be revived, it would not be as this design. The original
requirements were:

- define a complete noise and adversary model;
- distinguish symmetry covariance from topological protection;
- measure information leakage as well as bit error rate;
- compare with established BB84 security definitions; and
- avoid claims of security until a composable proof exists.

A physical implementation would require controllable sector preparation,
sector-projector measurement, calibrated noise, and an independently verified
attack model.

**Status against those five points.** The track now has one exact positive result
and a definite negative answer on the security question. The negatives, all found
while documenting the simulation:

- *Symmetry covariance is not protection* (bullet 2). The detector asks whether
  the received state is *an* eigenstate of `sigma`, not whether it is the *right*
  one — which the receiver cannot know. The unitary `diag(I, -I)`, i.e. a `pi`
  phase on the fermionic sector, maps the `+1` eigenspace onto the `-1`
  eigenspace, so `|<sigma>|` stays at 1 while every bit inverts: measured BER
  `1.0000` with detection `0.0000`. Any redesign must test eigenvalue
  *consistency*, which needs a shared key or BB84-style basis sampling. Pinned by
  `test_phase_flip_at_pi_inverts_every_bit_and_is_invisible`.
- *There is no error-rate-to-information relation, and none can be built on this
  observable* (bullet 3). The graded statistic a security argument would use now
  exists (`SimulationResult.mean_sigma_deviation`), so the earlier explanation —
  "detection is binary" — was the wrong diagnosis. The right one is that the
  statistic is **non-monotone in damage**, and the sharpest witness is not the
  phase flip but a *measurement in the encoding basis*: an adversary who measures
  `sigma` itself recovers every bit with `BER = 0.0000` and detection `0.0000`,
  leaving a deviation bit-identical to the no-eavesdropper run. Two strategies
  with equal deviation and different leakage mean no function of that deviation
  can bound leakage. Stated as a proposition with proof in
  `dimension_shift_quantum_communication.md` §4.1; pinned by
  `test_sigma_basis_intercept_is_transparent_and_recovers_every_bit` and
  `test_sigma_deviation_does_not_bound_leakage`.
- *The entropic route is closed too.* An uncertainty relation needs two mutually
  unbiased observables; a single-observable design has `c = 1` and therefore no
  `log2(1/c)` term to bound anything with. The natural second observable in the
  DSIN sector — the sector basis, with `c = 1/2` — does yield a non-degenerate
  relation, but it makes each 2-dimensional sector block *be* BB84, so it proves
  BB84's theorem rather than a new one. See §4.3.
- Bullet 4 is now partially addressed by the §4.2 comparison table, whose added
  rows record the two structural deficits: no conjugate observable, and no cost
  to the adversary for measuring in the right basis.

Bullet 1 stays open — the four attacks implemented in `dsin.py` are not a
complete adversary model — and bullet 5 remains open in full. The one positive
result in this track remains the exact commutator: `[H, sigma] = 0` at machine
precision for every dimension tested (`0.00e+00` up to `d = 12`).

**What a successor would need.** Failing the design is not the same as closing the
track, and §4.4 of `dimension_shift_quantum_communication.md` records the
difference — as *requirements rather than results*, with no security claim:

- Moving the payload into the interior of `Fix(sigma)` repairs the specific attack
  above but relocates the obstruction: the adversary measures the observable that
  determines the payload instead, and no stabilizer can see it, because that
  measurement is a *logical operator*. Verified, and pinned by
  `test_payload_in_the_interior_of_fix_sigma_relocates_the_obstruction`.
- Any successor has to meet four requirements (R1–R4 in §4.4.2). R1–R3 are BB84's
  content under other words; only R4 is something this construction already
  supplies.
- Two directions are at least well-posed. (b) Draw the involution itself per round
  from a family with mutually unbiased fixed loci — verified non-vacuous at
  `d = 2`, with the family *size* left as the open question, since that size is
  the randomness budget. (c) Make the sector frame itself the secret, which is the
  standard frame-alignment problem and the only version in which the symmetry
  rather than the randomness is the secret.
- §4.4.5 poses the experiment that would settle (b): compare a high-dimensional
  QKD key rate with and without the `sigma` syndrome as a herald. If the herald
  buys nothing, direction (b) is HD-QKD and the sector structure is decoration.

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
