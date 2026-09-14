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
