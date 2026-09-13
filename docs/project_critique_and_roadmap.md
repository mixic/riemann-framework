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

# Critics on the Current Work: From Notebook to Research Programme

## Purpose of This Critique

The repository has grown from a small scaffold into a public research
notebook. It now contains numerical experiments, dimension-shift models,
DSIN communication simulations, plots, and a substantial collection of
speculative research notes.

That growth is a strength, but it also creates a risk: readers may not know
which results are established, which are computational observations, and which
are hypotheses. This article records a critical assessment and proposes a
roadmap for making the project a more focused research programme.

The assessment is intentionally conservative. Passing tests demonstrate that
code runs and that specified properties hold for the tested cases. They do not
establish RH, construct a Hilbert-Polya operator, or provide cryptographic
security.

## 1. What the Project Is Now

| Layer | Current contents | Maturity |
|:---|:---|:---|
| Core numerics | `zeta.py`, `zeros.py`, `explicit_formula.py`, `plots.py` | Working and tested |
| Quantum chaos | `statistics.py`, `quantum_chaos.py` | Working and exploratory |
| Dimension shift | `dimension_shift.py`, `dimension_shift_chaos.py` | Working and exploratory |
| DSIN simulation | `dsin.py`, `test_dsin.py`, `run_dsin_analysis.py` | Toy simulation, not a security proof |
| Documentation | Research notes and dimension-shift articles | Rich, partly speculative |
| Lean formalization | Reserved project area | No Lean source currently tracked |

The project is therefore best described as a **multi-track research
exploration**. It should not describe these tracks as equally mature or as
parts of one completed theory.

## 2. What Is Strong

### 2.1 The project is explicit about its limits

The repository repeatedly states that it is not a proof of RH. Separating
numerical evidence, formal verification, and mathematical proof is good
research practice and should remain central to the README.

### 2.2 The numerical core is real

The zeta, zero, explicit-formula, and plotting modules perform actual
computations. Their tests exercise known values and numerical behavior. The
explicit formula is also documented as conditionally convergent, which avoids
a common overclaim about naive zero summation.

### 2.3 The dimension-shift track is a coherent hypothesis

The dimension-shift work combines:

- a discrete involution `sigma`;
- a `Z_2`-graded or two-sector model;
- finite Hamiltonian experiments;
- GUE, GOE, and Poisson reference statistics; and
- a proposed connection to spectral and SUSY-QM ideas.

This is a coherent research direction because it can produce measurements and
failure conditions. It is not yet a theory of the Riemann zeros: GUE-like
statistics are necessary evidence for some spectral models, not sufficient
identification with zeta.

### 2.4 The history is becoming reproducible

The scripts, tests, generated plots, and documentation record a meaningful
trajectory: numerical core, refactoring, dimension-shift experiments, and DSIN
simulation. Reproducible commands and fixed seeds make that trajectory more
useful to future readers.

## 3. What Needs Attention

### 3.1 State one central hypothesis

The repository currently explores RH, quantum chaos, dimension shift, and DSIN.
A central hypothesis would give these experiments a testable focus. A possible
formulation is:

> **Central Dimension-Shift Hypothesis (DSH):** There exists a naturally
> defined family of self-adjoint Hamiltonians `H(lambda)` on a `Z_2`-graded
> Hilbert space, together with an involution `sigma`, such that:
>
> 1. `[H(lambda), sigma] = 0` for the intended parameter range;
> 2. the spectral density of `H(lambda)` matches the Riemann-von Mangoldt
>    asymptotic;
> 3. a precisely defined subsequence of the spectrum corresponds to the
>    non-trivial zeta zeros; and
> 4. the fixed-locus or positivity structure forces the corresponding zeros to
>    satisfy `Re(s) = 1/2`.

This hypothesis is deliberately stronger than “the model has GUE statistics.”
It can be weakened into staged sub-hypotheses, but every stage should state
what observation would count against it.

### 3.2 Record negative results

A research log should report failures as carefully as successes. Examples
already suggested by the current experiments include:

- zero coupling produces a non-GUE baseline rather than the target statistics;
- changing symmetry breaking does not automatically produce a universal GUE
  regime;
- random-matrix agreement can vary with dimension, seed, unfolding, and
  normalization;
- naive explicit-formula summation is not a monotone approximation because
  the zero sum is conditionally convergent;
- the finite DSIN model is not a cryptographic security proof.

A result that a model fails to reproduce the target behavior is valuable when
the parameter range, seed, metric, and interpretation are recorded.

### 3.3 Separate DSIN from the RH proof strategy

DSIN and the RH dimension-shift work share vocabulary: involutions, sectors,
fixed subspaces, and possible index structures. That analogy is useful, but
DSIN is a downstream application hypothesis, not evidence for RH.

The repository should keep the relationship explicit:

- the RH track asks whether a spectral or algebraic structure explains zeta
  zeros;
- the DSIN track asks whether a sector symmetry can support a detectable
  communication label;
- neither result automatically proves the other.

The current DSIN implementation is a toy simulation with Hamiltonian
evolution, noise, attacks, and statistical tests. It has no composable
 security theorem and should not be presented as equivalent to BB84.

### 3.4 Formalize small mathematical facts

The Lean area is currently reserved for future work; no Lean source is tracked
at this stage. A useful formalization plan would begin with small independent
lemmas rather than a direct RH theorem:

- an explicitly defined sector-swap matrix squares to identity;
- the matrix is Hermitian and unitary;
- the dimensions of its `+1` and `-1` eigenspaces are equal;
- a commuting Hamiltonian preserves the eigenspaces;
- a finite zero-mode count has the stated index under explicit assumptions.

These lemmas would not prove RH, but they would turn part of the current
scaffold into checked mathematics.

### 3.5 Establish baselines

A model result is difficult to interpret without controls. Every dimension-shift
experiment should compare at least:

- the dimension-shift Hamiltonian;
- a same-size GOE random matrix;
- a same-size GUE or complex Hermitian random matrix;
- a Poisson spectrum;
- the selected Riemann zero ordinates.

The comparison should report sample size, unfolding method, mean adjacent-gap
ratio, reference values, KS distances, random seed, and parameter values.

A statement such as “mean `r = 0.5757` is GUE-like under the current heuristic”
is more accurate than “the model reproduces the Riemann spectrum.”

### 3.6 Explain the target, not only the mechanism

The involution and fixed-locus mechanism explains how a preferred subspace
might arise. It does not explain why that subspace should encode the specific
Riemann zeros.

A convincing spectral theory must also address:

- the Euler product and the prime weights `log(p)`;
- the Riemann-von Mangoldt spectral density;
- the functional equation and conjugation symmetries;
- the exact zero-to-spectrum correspondence; and
- the theorem that excludes off-line zeros.

Universal GUE statistics are a universality-class observation. The arithmetic
identity of the spectrum is the harder target.

## 4. Milestones

| Milestone | Success criterion | Status |
|:---|:---|:---|
| M1: Numerical baseline | Riemann zeros produce a stable GUE-like statistic under documented settings | In progress |
| M2: Model statistics | The dimension-shift model reaches a comparable range without fitting to zero data | In progress |
| M3: Control comparison | Same-size GOE, GUE, and Poisson controls are reported | Planned |
| M4: Density test | A model spectrum reproduces the Riemann-von Mangoldt growth | Not started |
| M5: Arithmetic embedding | Prime weights and the Euler product arise naturally | Not started |
| M6: Lean algebra | Involution, eigenspace, and commutation lemmas are proven | Not started |
| M7: SUSY correspondence | A rigorous operator construction and index statement are established | Not started |
| M8: RH forcing theorem | Off-line zeros are excluded by an independent theorem | Open problem |
| M9: DSIN security | A physical and composable security proof exists for an explicit channel model | Not started |

## 5. Lessons Learned So Far

The current work already supports several useful lessons:

1. Numerical evidence must be tied to a metric, sample size, precision, and
   baseline.
2. A passing computation is not the same as convergence, and convergence is
   not the same as proof.
3. A symmetry can organize a problem without forcing every object into its
   fixed locus.
4. A finite matrix with a sector swap is a useful test object, but not yet a
   canonical infinite-dimensional operator.
5. A Witten-index helper that counts finite zero modes is not automatically a
   supersymmetric index theorem.
6. A DSIN simulation can study disturbance and decoding, but cryptographic
   security requires an explicit attack model and a proof relating information
   leakage to observed errors.

## 6. Roadmap

The next practical sequence is:

1. Freeze documented baseline experiments and publish their seeds and
   parameters.
2. Add same-dimension GOE, GUE, and Poisson controls.
3. Measure spectral density separately from local spacing statistics.
4. Define the arithmetic input that should produce prime weights.
5. Formalize the finite involution and commuting-Hamiltonian lemmas in Lean.
6. Keep DSIN experiments in a clearly marked speculative application track.
7. Record null results in a dedicated research log rather than deleting them.

## 7. Honest Verdict

The repository is a genuine research exploration with a working numerical
core, reproducible toy experiments, and unusually detailed documentation. It
is not yet a proof project in the mathematical sense, because the central
spectral object, arithmetic correspondence, density theorem, and RH-forcing
argument are missing.

The most important transition now is from “many interesting experiments” to a
single falsifiable programme. The central question is:

> Can a naturally defined dimension-shift operator reproduce the arithmetic
> spectrum of the zeta function, not merely its universal local statistics?

Until that question is answered, the correct status is exploratory, useful,
and unproven.

## Disclaimer

This critique and roadmap are part of the research notebook. They do not claim
that the Riemann Hypothesis has been proved, that the dimension-shift model is
correct, or that DSIN provides practical cryptographic security.
