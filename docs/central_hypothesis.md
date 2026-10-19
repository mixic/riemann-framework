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

> **Status: ABANDONED** (M5: 300 seeds per parameter point, `d = 100, 200`, four
> couplings, both matrix classes). The Dimension-Shift Hypothesis was tested against
> its own falsification criteria in §4 and did not survive: the `σ`-sector
> universality class is **inherited** from the input blocks rather than produced by
> the construction. This document is kept as the record of the hypothesis *as it was
> stated*, because a falsified proposal has to be readable in the form that was
> falsified. The verdict, the measurements and the lessons are in §10; the full
> artifact is [`m5_verdict.md`](m5_verdict.md).
>
> Nothing below is evidence for the Riemann hypothesis, and nothing below is now an
> open research question except where §10.9 says otherwise.

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
| S2: Model statistics | Mean ratio of `H(lambda)` | Comparable to the zero baseline without fitting | **Not met, and now understood (§10.4).** The full spectrum is a superposition of two sectors and lands at `0.37…0.43`; a sector matches the zeros only when its input blocks already did |
| S3: Spectral density | Normalized cumulative-count RMSE | Diagnostic implemented; asymptotic match remains open |
| S4: Involution symmetry | `||[H, sigma]||_F` | **Exact** for the chaos model since the correction: `H = [[A, C], [C†, A]]` gives `‖[H,σ]‖_F/‖H‖_F = 0.0` by construction, not to a tolerance. Also exact for the DSIN channel model |
| S5: Fixed locus | Dimension of the finite `+1` eigenspace | Equal to one sector dimension | Verified numerically and by tests |
| S6: Lean formalization | Independently proven algebraic lemmas | Increasing checked theorem set | First lemma added in `lean/RiemannFramework/DimensionShift.lean` |
| S7: SUSY/index structure | Witten index under explicit assumptions | A proved index theorem | Only a finite numerical diagnostic |

A criterion is verified only when the code, assumptions, parameters, and
passing test or theorem are recorded. Numerical agreement does not establish
a mathematical correspondence.

### 3.1 An exact arithmetic anchor now exists

The primon gas (Julia 1990, Spector 1990; refined into the Bost-Connes system,
1995) supplies what this project previously lacked: an operator whose trace
*provably is* the Euler product. On `l^2(N)` with `H|n> = log(n)|n>`,

```text
Tr[e^{-sH}] = sum_n n^{-s} = zeta(s)      exactly, for Re(s) > 1.
```

This is implemented in `python/riemann_framework/primon_gas.py`, and the
truncated trace is checked against `mpmath`'s `zeta` as `N` grows rather than
asserted. It matters because it converts an open-ended question -- "does the
model engage the arithmetic?" -- into a concrete test: does a proposed symmetry
commute with the one operator whose trace is the Euler product?

It does **not** supply the zeros. The eigenvalues of `H` are `log(n)`, not the
imaginary parts of the non-trivial zeros. This anchors M6 (arithmetic
embedding), not M7 (spectral correspondence).

### 3.2 Recorded negative result: the natural lift fails

The most natural attempt to give the dimension-shift involution arithmetic
content is to lift it onto `l^2(N)` as the permutation swapping the exponents
of two primes in each integer's factorisation. That lift **cannot** commute
with `H`, and the reason is structural rather than numerical: `H` is diagonal
with eigenvalues `log(n)`, which are strictly distinct, so any operator
commuting with it must itself be diagonal in the `|n>` basis -- while this
permutation is not. See `python/riemann_framework/operator_symmetry.py` and
`python/tests/test_primon_gas.py`.

This rules out basis permutations on `l^2(N)` as the route to a symmetry of the
primon gas. It does not rule out the programme: the Bost-Connes system's Galois
action, for instance, acts on a different, non-diagonal representation.

Two caveats are recorded with the numbers rather than buried:

- On a finite truncation the swap is only a partial permutation, because
  partners such as `3^3 = 27` for `8 = 2^3` fall outside it. For the `(2, 3)`
  swap every truncation with `n_max >= 8` is already affected, so the finite
  commutator norm describes a boundary-corrected map, not the intended one.
- The matrix-level obstruction is a finite-dimensional linear-algebra fact. The
  infinite-dimensional statement needs the unbounded-operator care that this
  finite test does not exercise.

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

> **Superseded.** This snapshot is a single seed from the pre-correction model,
> whose `σ`-involution was not enforced (`‖[H,σ]‖/‖H‖ = 1.35…1.46`). The corrected
> model at that coupling and 300 seeds gives a full-spectrum mean near `0.42`, and
> the sectors inherit their class from the input blocks. See §10. This number is
> kept as part of the record, not as evidence.

## 6. Roadmap

> **Closed.** The milestones below were the DSH's own; the programme was abandoned
> by criterion (2) of §4 before they were reached. What remains independent of the
> DSH — the Lean formalization, the BB84 implementation layer, the size-aware
> `std` criterion — is tracked in the README roadmap. See §10.9.

| Milestone | Success criterion | Status |
|:---|:---|:---|
| M1: Numerical baseline | Reproduce a stable documented zero-statistics baseline | Superseded |
| M2: Model statistics | Match the baseline without fitting to zero data | **Failed** (§10.4) |
| M3: Control ensembles | Compare same-size GOE, GUE, and Poisson controls | Planned |
| M4: Density test | Match the Riemann-von Mangoldt growth | Not started |
| M5: Lean algebra | Prove involution and commuting-sector lemmas | First lemma added |
| M6: Arithmetic embedding | Derive prime weights and the Euler product | Not started |
| M7: Spectral correspondence | Prove a precise zero-to-spectrum map | Not started |
| M8: SUSY correspondence | Define operators, domains, and an index theorem | Not started |
| M9: RH forcing theorem | Exclude all off-line zeros independently | Open problem, and unreachable from this programme |

### Immediate next steps (superseded by §10)

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

## 10. What the DSH Taught Us

The Dimension-Shift Hypothesis was the repository's flagship proposal. It was
tested, and it was abandoned. This section records what the process taught — not
as a eulogy, but as a set of constraints that apply to the next proposal.

### 10.1 The verdict

**The DSH is abandoned.** The reason is criterion (2) of the roadmap: *the sector
class is inherited, not produced.*

| input blocks | sector means (300 seeds) | full-spectrum means |
|:---|:---|:---|
| GOE | `0.5279 … 0.5327` | `0.4225 … 0.4248` |
| GUE | `0.5964 … 0.6017` | `0.4199 … 0.4238` |

Two things in that table need stating precisely, because a looser reading makes the
result look stronger than it is:

1. The full spectrum is **not identical** across the two classes — it is
   `0.4225…0.4248` against `0.4199…0.4238`, overlapping and differing by less than
   `0.005`. What is true is that it is *insensitive*: two independent sectors of
   either class superpose to the same intermediate `r`-ratio near `0.42`.
2. The `σ` structure therefore **does** see the input class — it passes it through
   unchanged, which is exactly why the sectors separate (`0.53` against `0.60`) and
   why the whole-spectrum summary hides it. The insensitivity is in the summary
   statistic, not in the construction.

### 10.2 Lesson 1: single-seed results are noise

The original grid ran one seed per point and declared "DSH is SUPPORTED" if any of
90 points landed in `[0.58, 0.62]`. At `2d = 20` the per-seed standard deviation is
`0.075`, and **14% of pure GOE draws enter that window** (`23%` with
`unfold=False`). The reported best point (`0.6117`) has a 300-seed mean of
`0.523 ± 0.069`: a `+1.3σ` fluctuation. At `d = 200` the same point gives `0.5315`.

**Constraint for the next proposal:** at least 300 seeds, a standard deviation, and
a pre-registered window. "Supported" without a std is not a verdict.

### 10.3 Lesson 2: the full spectrum is the wrong question

A `σ`-symmetric Hamiltonian is a superposition of its two sectors, and the full
spectrum lands at `0.37…0.43` for *either* input class. A whole-spectrum test asks
about the superposition, not about the object the hypothesis is stated on.

**Constraint:** test the sectors separately; report the full spectrum as a baseline.

### 10.4 Lesson 3: the sector class is inherited, not produced

`sectors are spec(A ± C)`. With `A`, `C` drawn from GUE the sectors are GUE; with
real symmetric blocks they are GOE; `‖[H,σ]‖ = 0` holds in both cases. The class is
an **assumption about the input**, not a consequence of the `σ` structure.

**Constraint:** a proposal must *produce* the class it claims. A construction that
merely passes an ensemble through has not explained the zeros' statistics; it has
restated them as an input.

### 10.5 Lesson 4: a `std < 0.02` clause is unreachable at these sizes

The specification required per-seed `std < 0.02` for `supported_multi_seed`.
Measured: `0.084` at `2d = 20`, `0.034` at `2d = 100`, `0.026` at `2d = 200`,
shrinking like `1/√(2d)`.

**Constraint:** a criterion must be reachable at the sizes the study can run, or it
is a hidden prohibition rather than a test. The clause was implemented as written,
reported as unreachable, and the standard error (`0.004` at 300 seeds) reported
beside it.

### 10.6 Lesson 5: criterion (1) was class-conditional

Criterion (1) holds for GOE blocks (`goe=True`) and fails for GUE blocks
(`gue=False`): 24 of 48 sector means in each window. It is therefore not independent
evidence — it is a description of one input class. The abandonment rests on
criterion (2), which is class-independent.

**Constraint:** evaluate a criterion across the whole admissible family, and report
the result per class. A criterion that holds only where its conclusion was assumed
is circular.

### 10.7 Lesson 6: document the defects with the verdict

Two **defects in the analysis** were found while producing the verdict, and both are
recorded in [`m5_verdict.md`](m5_verdict.md) next to the result:

1. A **label swap** in criterion (2): `MATRIX_CLASSES` is `("goe", "gue")` and the
   first draft named the GOE point "gue", so the first full run reported the class
   as *not* inherited — **DSH SURVIVES**, the opposite of the data, and in the
   direction that acquits the hypothesis.
2. **`test_`-prefixed production functions** (`test_criterion_1/2`) were collected by
   pytest as tests, so the test file ran the full default grid twice — about twelve
   minutes of hidden computation, and `--collect-only` reported 18 items where 16
   exist.

These are distinct from the *findings about the criteria* in §10.5 and §10.6.

**Constraint:** a verdict without its defects is an overstatement. A bug that runs
towards the hoped-for answer is the one most likely to be believed.

### 10.8 What was positive

| component | status |
|:---|:---|
| The involution `σ(s) = 1 − conj(s)`, fixed locus = critical line | **Proved in Lean**, `sorry`-free (`ZetaBridge.lean`) |
| `σ² = id` | **Proved in Lean** (`sigma_involutive`, componentwise) |
| The multi-seed falsification test | 300 seeds, error bars, per-sector split, five-label verdict |
| Sector extraction | Verified numerically against `spec(A ± C)` |
| Commutation enforcement | `‖[H,σ]‖/‖H‖ = 0.0` exactly, by construction |
| The negative result | Precise, structural, and generalisable |

The **method** survived even though the **hypothesis** did not.

### 10.9 What comes next

The DSH is abandoned; the remaining milestones are independent of it.

| milestone | status | independence |
|:---|:---|:---|
| M1 multi-seed verdict | done (`mixed`, 300 seeds) | independent |
| M2 consolidated negative results | done (`lessons_learned.md` §1–§9) | independent |
| M3 BB84 detector blinding | see the roadmap | independent — a communication-model result |
| M4 Lean `σ² = id` | done (`sigma_involutive`) | independent — a formal result |
| M5 DSH sector question | **done — abandoned** | — |

Neither the BB84 implementation layer nor the Lean formalization depends on whether
the DSH is true.

### 10.10 The final lesson

The repository's own standard, from the README:

> *"Several tracks here do fail, on purpose and on record: a negative result
> obtained by a stated method is worth more than an unfalsifiable claim of
> progress."*

The DSH is now one of those tracks. It was proposed, tested by its own stated
criteria, and abandoned. The abandonment is documented with numbers, in the document
that proposed it.

**That is the contribution.** Not the Riemann hypothesis — the science.

### 10.11 What the `σ` structure still is: a detector

The hypothesis is abandoned, and the structure that produced it is not useless. A
`σ`-symmetric Hamiltonian has sector spectra `spec(A ± C)`, and a class test run on
its full spectrum is run on a superposition: `⟨r⟩` falls from `0.53`/`0.60` at one
sector to `0.43` at two and `0.39–0.40` from three upward. That is what made a GOE
model look like GUE (§10.4), and it is the reason the M5 criteria were rewritten to
test sectors.

The same fact is a usable warning: [`desymmetrisation.md`](desymmetrisation.md)
implements it — split-and-compare when the involution is known, a spectrum-only flag
when it is not — with a 300-seed calibration table, and with its own failure on
record: it detects contamination but cannot count the sectors, and at two sectors it
cannot tell GOE from GUE. The phenomenon is standard
([Giraud et al., Phys. Rev. X **12**, 011006 (2022)](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.12.011006));
what is local is the measured table, the entry points, and the documented limit.

Read this the honest way. It is a sensor for a specific mistake, not evidence for the
hypothesis: `⟨r⟩` low means *find the symmetry*, never *the class has changed*.

