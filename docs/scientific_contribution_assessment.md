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

# Scientific Contribution Assessment

## Short Answer

The project is methodologically serious but scientifically speculative. It
now has the infrastructure of a research programme and a preliminary
computational result, but it does not yet provide a theorem, an exact spectral
correspondence, or a proof of the Riemann Hypothesis.

The distinction matters. A working experiment is not automatically a
scientific contribution, and GUE-like statistics are not automatically
evidence that a model encodes the Riemann zeros.

## 1. What Counts as a Contribution?

| Type | Example | Current status |
|:---|:---|:---|
| New theorem | A proved mathematical lemma | One small Lean involution lemma; no RH theorem |
| New numerical result | A reproducible measurement or counterexample | Preliminary falsification-grid result recorded |
| New framework | A definition enabling new questions | Dimension-shift and DSIN models |
| New conjecture | A motivated, testable claim | Dimension-Shift Hypothesis (DSH) |
| New method | A technique that transfers to other problems | Not established yet |

A conjecture is a weak contribution if it remains only a proposal. It becomes
more useful when it is precisely stated, tested against baselines, exposed to
falsification, and connected to a theorem or reproducible numerical result.

## 2. Component Assessment

| Component | Scientific role | Honest assessment |
|:---|:---|:---|
| `zeta.py`, `zeros.py` | Standard numerical zeta computations | Useful infrastructure, not novel by themselves |
| `explicit_formula.py` | Regularized explicit-formula experiments | Established method applied to this project |
| Quantum-chaos statistics | GUE, GOE, and Poisson comparisons | Standard tools used for a new model |
| `dimension_shift.py` | Finite involution and sector model | Novel framing, elementary finite algebra |
| `dimension_shift_chaos.py` | Coupled Hamiltonian family | Exploratory model without theoretical derivation |
| `falsification_test.py` | Parameter grid and verdict system | Good reproducible methodology |
| `spectral_density.py` | Finite cumulative-count diagnostic | Useful M3 diagnostic; not an asymptotic proof |
| `DimensionShift.lean` | Formal sector-swap lemma | First small formal result; not RH formalization |
| `dsin.py` | Toy communication-channel simulation | Speculative application; no security theorem |
| Documentation | Research record and hypotheses | Rich, with claims explicitly marked as speculative |

## 3. What Is Genuinely Promising?

### 3.1 The dimension-shift framing

The use of a discrete sector involution as a lift of the functional-equation
symmetry is a distinctive framing. The finite matrix

```text
sigma = [[0, I], [I, 0]]
```

has transparent algebraic properties: it is Hermitian, squares to identity,
and has symmetric and antisymmetric eigenspaces.

This is a useful research object. It is not yet a canonical infinite-dimensional
number system or an operator whose spectrum is known to be the zeta zeros.

### 3.2 Falsification as a method

The grid experiment classifies parameter points using mean adjacent-gap ratios
and reports GUE-like, GOE-like, Poisson-like, or intermediate behavior. This is
stronger than presenting only favorable plots because it exposes parameter
regions that do not support the target behavior.

The method becomes scientifically stronger when it includes repeated seeds,
finite-size scaling, control ensembles, density diagnostics, and fixed output
artifacts.

### 3.3 Honest presentation

The repository distinguishes evidence from proof, states that RH is open, and
marks DSIN and dimension-shift claims as speculative. This is an important
scientific strength and should be preserved.

## 4. Preliminary Numerical Result

The default falsification grid used:

- dimensions `[10, 20, 30]`;
- couplings `[0.0, 0.25, 0.5, 1.0, 2.0, 5.0]`;
- symmetry-breaking values `[0.0, 0.5, 1.0, 2.0, 5.0]`; and
- seed `42`.

The 90 runs produced:

| Classification | Count |
|:---|---:|
| GUE-like | 10 |
| GOE-like | 16 |
| Poisson-like | 4 |
| Intermediate | 60 |

The minimum mean ratio was `0.304776`. The maximum was `0.611747`, at
`dim_per_sector = 10`, `coupling = 0.5`, and `symmetry_breaking = 2.0`.
The grid summary was `supported` because at least one point entered the
heuristic GUE interval `[0.58, 0.62]`.

This is preliminary evidence, not confirmation of DSH. Most parameter points
were intermediate, and the best point occurred at the smallest tested
 dimension. One seed and a finite grid are insufficient for a robust claim.

The M3 spectral-density diagnostic also shows why local statistics are not
enough. For a separate seeded model comparison with `dim_per_sector = 20` and
30 reference zeros, the normalized cumulative-count RMSE values were:

```text
model versus reference: 0.222305
model versus Riemann-von Mangoldt curve: 0.217680
reference zeros versus Riemann-von Mangoldt curve: 0.014622
```

The model therefore does not yet reproduce the reference density in that
finite test. The diagnostic uses an explicit height normalization and should
not be interpreted as an asymptotic theorem.

## 5. What Is Missing?

### 5.1 Theoretical grounding

The model has a mechanism, but not yet a derivation of why it should produce
the specific zeta spectrum. A complete theory must address:

- the prime Euler product and `log(p)` weights;
- the Riemann-von Mangoldt spectral density;
- the exact zero-to-spectrum correspondence;
- self-adjointness and operator domains; and
- a theorem forcing off-line zeros to be absent.

### 5.2 Formal development

The first Lean lemma proves that a two-sector swap squares to identity. This
moves the repository beyond an entirely empty formal scaffold, but it is only
an elementary algebraic fact. The zeta function, Hamiltonian family, and RH
remain unformalized.

### 5.3 Repeated and controlled experiments

The current numerical result should be extended with:

- repeated seeds and confidence intervals;
- same-size GOE, GUE, and Poisson controls;
- finite-size scaling;
- spectral-density measurements over increasing ranges; and
- parameter choices fixed independently of the target zeros.

## 6. Honest Verdict

| Question | Answer |
|:---|:---|
| Is the project serious? | Yes; the methodology is explicit and testable |
| Is it novel? | Partially; the dimension-shift framing is distinctive |
| Is it speculative? | Yes; the arithmetic theory and RH mechanism are missing |
| Does it have a result? | Yes, a preliminary finite-grid numerical result |
| Does it prove RH? | No |
| Does it prove DSIN security? | No |
| Is it publishable as a proof? | No |
| Could it become a research note? | Possibly, with stronger controls and analysis |

The most accurate current description is:

> A serious, methodologically explicit, speculative research exploration with
> a working numerical core, a preliminary falsification result, and one small
> formal lemma, but without a proven arithmetic spectral correspondence.

## 7. Next Contributions to Target

1. Repeat the falsification grid across seeds and dimensions.
2. Add matched random-matrix control ensembles.
3. Improve the M3 density test toward a genuine scaling study.
4. Formalize finite matrix identities and commuting-sector lemmas in Lean.
5. Derive or justify the prime contribution to the Hamiltonian.
6. Record null results and parameter sensitivity in the research log.
7. Keep DSIN separated as a speculative downstream application.

## Disclaimer

This assessment does not claim that the Riemann Hypothesis has been proved,
that the Dimension-Shift Hypothesis is correct, or that the DSIN model is a
secure cryptographic protocol. It records the current scientific status of the
repository as a research notebook.
