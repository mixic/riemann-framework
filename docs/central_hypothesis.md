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

# Central Hypothesis: The Dimension-Shift Program for the Riemann Hypothesis

## Preamble

This document states the central falsifiable hypothesis of the Riemann
Framework. The repository contains several tracks, but the dimension-shift
programme supplies the main research question. Numerical experiments,
formal definitions, and documentation are infrastructure or evidence for this
question.

This is not a proof of the Riemann Hypothesis. It is a research programme with
explicit success criteria, falsification criteria, and milestones.

## 1. The Central Hypothesis

> **Dimension-Shift Hypothesis (DSH):** There exists a naturally defined
> family of self-adjoint Hamiltonians `H(lambda)` on a `Z_2`-graded Hilbert
> space `H = H_b direct_sum H_f`, together with a discrete involution `sigma`,
> such that:
>
> 1. `[H(lambda), sigma] = 0` in the intended parameter regime;
> 2. the spectral density of `H(lambda)` matches the Riemann-von Mangoldt
>    asymptotic;
> 3. a precisely defined spectral subsequence corresponds to the non-trivial
>    zeta zeros;
> 4. the fixed-locus or positivity structure forces the corresponding zeros to
>    satisfy `Re(s) = 1/2`; and
> 5. the local statistics are compatible with the observed GUE-like behavior.

This formulation is intentionally stronger than “the model has GUE
statistics.” Random matrices can reproduce universal local statistics without
encoding the Euler product or the individual zeta zeros.

## 2. Why This Hypothesis

The Hilbert-Polya idea seeks a self-adjoint operator whose spectral values are
related to the zero ordinates. Such an operator would provide real spectral
parameters, but a complete construction must not assume the representation
`rho = 1/2 + i gamma` before proving the critical-line condition.

The dimension-shift proposal replaces continuous rotation within one complex
plane with a discrete sector involution. On the complex slice, the prototype
uses conjugate reflection:

```text
sigma(s) = 1 - conjugate(s),
sigma(sigma(s)) = s,
sigma(s) = s  <=>  Re(s) = 1/2.
```

The fixed-locus identity is easy to verify. The difficult part is proving that
all relevant zeta zeros are forced into that locus and that the prime Euler
product is represented by the same structure.

## 3. Success Criteria

| Criterion | Metric | Threshold | Current status |
|:---|:---|:---|:---|
| S1: Zero baseline | Mean adjacent-gap ratio of tested zeros | Documented GUE-like range | Working numerical check |
| S2: Model statistics | Mean ratio of `H(lambda)` | Comparable to the zero baseline without fitting | Exploratory |
| S3: Spectral density | Normalized cumulative-count RMSE | Diagnostic implemented; asymptotic match remains open |
| S4: Involution symmetry | `||[H, sigma]||_F` | Zero or controlled numerical error | Verified for the DSIN channel model; not for every chaos model |
| S5: Fixed locus | Dimension of the finite `+1` eigenspace | Equal to one sector dimension | Verified numerically and by tests |
| S6: Lean formalization | Independently proven algebraic lemmas | Increasing checked theorem set | First lemma added in `lean/RiemannFramework/DimensionShift.lean` |
| S7: SUSY/index structure | Witten index under explicit assumptions | A proved index theorem | Only a finite numerical diagnostic |

A criterion is verified only when the code, assumptions, parameters, and
passing test or theorem are recorded. Numerical agreement does not establish
a mathematical correspondence.

## 4. Falsification Criteria

The programme should be abandoned or fundamentally revised if robust evidence
shows that:

- no natural parameter regime produces statistics comparable to the zero
  baseline;
- the spectrum has incompatible density for every proposed scaling;
- the involution is not a symmetry of the intended Hamiltonian;
- the finite or infinite fixed-locus construction does not correspond to the
  critical-line condition;
- the model has no canonical relation to prime weights and the Euler product;
- the apparent zero agreement disappears under increased dimension, precision,
  or out-of-sample tests; or
- the proposed correspondence requires parameters fitted directly to known
  zeros.

A single numerical mismatch is not automatically a falsification: the model,
normalization, and observable must be specified before the test is decisive.

## 5. Current Computational Evidence

The repository provides three related but distinct computational surfaces:

1. `dimension_shift.py` tests a finite sector swap, its eigenspaces, and
   finite Hamiltonian diagnostics.
2. `dimension_shift_chaos.py` builds a random coupled Hamiltonian and measures
   local spectral statistics.
3. `dsin.py` simulates an idealized communication channel with Hamiltonian
   evolution, noise, attacks, and sigma measurements.

The chaos model and the DSIN channel model should not be conflated. The former
is a spectral-statistics experiment; the latter is a toy communication model.
Neither currently constructs the arithmetic operator required by DSH.

The coupling sweep should be reported with its exact dimension, seed,
normalization, unfolding method, and tested coupling values. Its maximum is a
model diagnostic, not evidence that the spectrum converges to zeta zeros.

### Coupling-sweep snapshot

Using `dim_per_sector = 30`, `seed = 42`, zero symmetry breaking, and coupling
values `[0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]`, the maximum observed
mean ratio was:

```text
coupling = 1.00
mean r   = 0.575671
classification = GUE-like by the repository heuristic
```

This is below the reference GUE value `0.599` and is one finite seeded
experiment. It supports continued investigation, but it does not establish
the model statistics criterion or spectral convergence.

## 6. Roadmap

| Milestone | Success criterion | Status |
|:---|:---|:---|
| M1: Numerical baseline | Reproduce a stable documented zero-statistics baseline | In progress |
| M2: Model statistics | Match the baseline without fitting to zero data | In progress |
| M3: Control ensembles | Compare same-size GOE, GUE, and Poisson controls | Planned |
| M4: Density test | Match the Riemann-von Mangoldt growth | Not started |
| M5: Lean algebra | Prove involution and commuting-sector lemmas | First lemma added |
| M6: Arithmetic embedding | Derive prime weights and the Euler product | Not started |
| M7: Spectral correspondence | Prove a precise zero-to-spectrum map | Not started |
| M8: SUSY correspondence | Define operators, domains, and an index theorem | Not started |
| M9: RH forcing theorem | Exclude all off-line zeros independently | Open problem |

### Immediate next steps

1. Record the coupling sweep maximum with fixed reproducibility metadata.
2. Add same-size GOE, GUE, and Poisson controls.
3. Measure spectral density independently of local spacing statistics.
4. Prove the finite sector-swap and commuting-Hamiltonian lemmas in Lean.
5. Define the arithmetic object that should produce the prime weights.
6. Keep DSIN clearly marked as a downstream speculative application.

## 7. Relation to DSIN

The Dimension-Shift Involution Network (DSIN) shares the vocabulary of sector
swaps, eigenspaces, and discrete symmetry. It is a downstream application
track, not a proof strategy for RH.

- DSH asks whether an operator can explain the arithmetic spectrum of zeta.
- DSIN asks whether a sector observable can support a detectable communication
  label under an explicit channel and attack model.
- A result in one track does not automatically prove a result in the other.

## 8. What Success Would Mean

If DSH succeeds, it would provide a concrete spectral framework with an
arithmetic correspondence, correct density, and an independent theorem forcing
the critical-line condition. GUE agreement would then be an explained
consequence rather than the primary result.

If DSH fails, the negative result would still constrain dimension-shift,
sector-coupled, and prime-based operator models. It would not affect the truth
of RH or rule out other Hilbert-Polya, geometric, or analytic approaches.

## 9. Disclaimer

This document states a speculative and falsifiable research hypothesis. It is
not a proof of RH, not a claim that a Hilbert-Polya operator has been built,
and not a claim that the current numerical models encode the Riemann zeros.
