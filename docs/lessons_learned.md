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

# Lessons Learned

This document records negative knowledge and limitations from the Riemann
Framework experiments. It is part of the research record, not a list of
failures to hide.

## 1. Numerical Evidence Is Not a Proof

Known zeta zeros can be computed and checked to high precision, but finite
verification cannot establish that every non-trivial zero lies on the
critical line. Passing numerical tests are evidence about the tested range.

Likewise, a model with GUE-like spacing statistics has matched a universal
statistical feature. It has not reproduced the Euler product, the individual
zeros, or the Riemann-von Mangoldt density.

## 2. Explicit-Formula Summation Is Delicate

The naive sum over zeta zeros is conditionally convergent. Adding more zeros
in their numerical order does not guarantee a monotone improvement. The
current implementation uses Gaussian regularization for visualization and
records this limitation rather than treating the output as an exact prime
counting formula.

A future comparison should state the test function, truncation, ordering,
precision, and error metric.

## 3. GUE Statistics Alone Are Too Weak

The dimension-shift chaos experiments can produce mean adjacent-gap ratios that
are classified as GUE-like by a simple reference heuristic. This does not
identify the model with the Riemann spectrum. Random matrices are designed to
produce universal local statistics without carrying the arithmetic structure
of the primes.

The missing tests are spectral density, prime weighting, out-of-sample
prediction, and an exact or mathematically controlled zero-to-spectrum map.

## 4. Coupling Results Depend on Experimental Choices

The observed mean `r` value changes with matrix dimension, random seed,
coupling, symmetry-breaking strength, unfolding method, and normalization.
A single favorable parameter value is therefore not a robust result.

Every reported sweep should include:

- matrix dimension;
- coupling values;
- symmetry-breaking values;
- random seed policy;
- unfolding method;
- sample size; and
- the reference ensemble values.

## 5. Symmetry Does Not Automatically Force Fixed Points

The functional equation maps zeros to symmetry partners. It does not by itself
prove that every zero is fixed by the symmetry. The fixed-locus idea requires
an additional positivity, self-adjointness, trace-formula, or equivalent
forcing theorem.

This distinction is essential for both the dimension-shift RH proposal and
interpretations of the DSIN sector swap.

## 6. The Finite Sector Model Is a Toy Model

The finite matrix

```text
sigma = [[0, I], [I, 0]]
```

is a useful test object. Its square is the identity, it is Hermitian, and its
`+1` and `-1` eigenspaces have equal dimension. These facts do not establish
the existence of a canonical infinite-dimensional number system or physical
Hamiltonian.

The current finite Witten-index helper counts numerical zero modes of matrices.
It is not by itself a supersymmetric index theorem and does not prove
topological protection.

## 7. The First DSIN Simulation Was Incomplete

The initial DSIN simulation accepted a coupling parameter without applying the
Hamiltonian evolution, used a deterministic projection in its intercept-resend
model, and relied on a brittle single-seed detection threshold. These issues
were corrected by:

- applying finite Hamiltonian evolution;
- sampling sigma measurements with the Born rule;
- sampling intercept-resend outcomes according to measurement probabilities;
- validating dimensions, channel settings, and noise parameters; and
- replacing the single-run threshold with an aggregate multi-seed test.

The corrected simulation is still a toy channel. It does not provide a
composable security proof or BB84-equivalent guarantees.

## 8. Lean Formalization Is Still Open

The repository now has a first standalone Lean lemma for the involution
identity, but this is only a small algebraic result. It does not formalize the
zeta function, the Hamiltonian, the Euler product, or RH.

The next useful formal steps are finite matrix identities, eigenspace
properties, and commutation lemmas with explicit assumptions.

## 9. What Has Not Yet Worked

The following major goals remain unresolved:

- no operator has been constructed with a proved exact zeta spectrum;
- no spectral-density match has been established;
- no Euler-product derivation emerges from the sector model;
- no proof forces all zeros into the fixed locus;
- no physical DSIN implementation has been demonstrated; and
- no cryptographic security theorem has been proved for DSIN.

Recording these open failures prevents the project from confusing a working
prototype with a completed theory.

## 10. A Lift Confined to the Fixed Locus Cannot Test the Fixed Locus

The shift-zeta programme asked whether lifting the Euler product to a graded
algebra `A = A0 + omega*A1` forces the zeros into `Fix(sigma) = A0`. The
construction built for that purpose cannot answer the question, and the reason
is structural rather than numerical.

Every local factor is a polynomial in the single element
`gamma_tau = ((1+tau)/2)I + ((1-tau)/2)omega`, so the whole Euler product lies
in the two-dimensional algebra `C[gamma_tau]`. There is no interaction *between*
primes: the product is a product of functions of one generator. At `tau = 1` the
generator is the identity, so the product is scalar and sits in `Fix(sigma)` by
construction.

An object placed inside the fixed locus by definition cannot serve as evidence
about whether zeros are forced there. The general lesson: **check that a
proposed test can fail before running it.** If the construction satisfies the
conclusion identically, the test is vacuous.

Numerically the framework behaves as follows (600 primes; details in
`docs/shift_zeta_result.md`):

- the algebra is well-defined and `sigma` is an algebra homomorphism;
- the graded trace is `sigma`-invariant and the supertrace is
  `sigma`-anti-invariant -- two different functionals, easily confused;
- at `tau = 1` the graded trace equals the classical Euler product term by term
  (relative error `5.1e-4` at `s = 2`, which is pure truncation);
- for `tau != 1` it departs from `zeta` by 11% to 44% at `s = 2` and fails the
  completion symmetry with residuals `1e-2` to `1e-1`.

## 11. A Control Is What Makes a Zero Comparison Decisive -- or Not

An earlier version of the shift-zeta analysis concluded that the zero
comparison was undecidable, because a sign-change scan on the critical line
reported 28 crossings against 4 classical zeros. That conclusion was too
pessimistic, and the reason is instructive.

The scan was the wrong diagnostic. The right one uses a control: at `tau = 1`
the graded trace *is* the classical partial Euler product term by term, so
whatever a diagnostic reports there is pure truncation artefact. Comparing
`|Z_A(rho, tau)| / |Z_A(rho, 1)|` at the classical zero heights cancels the
truncation and isolates the grading:

| `tau` | ratios at the first six zeros |
|---:|---|
| 0 | 7.54, 5.72, 4.35, 6.88, 6.14, 3.45 |
| 0.5 | 2.25, 2.07, 1.97, 2.35, 2.19, 1.75 |
| 2 | 0.551, 0.565, 0.551, 0.533, 0.543, 0.557 |

The ratio is tightly clustered across six independent heights and is not 1. At
`tau = 1` the trace dips sharply exactly at the classical zeros; at `tau = 0`
it shows no such dips and is 3.5 to 7.5 times larger there. The zero sets do not
coincide.

Two further lessons:

- **A withdrawn statistic.** Flagging "deepest local minima" and counting
  matches to classical zeros scored 7 of 8 *at the `tau = 1` control*, where the
  trace is the classical product. It was measuring the oscillation of a
  truncated product, not the location of zeros. It was removed, not reported.
- **Failures of a diagnostic are not findings about the object.** "I cannot
  resolve the zeros" and "the zeros differ" are different claims. Both mistakes
  were made here before the control settled it.

### The asymmetry that remains

The comparison settles one direction and not the other, and it is worth being
explicit rather than letting the figure imply more than it supports.

Settled: the graded trace does **not** reproduce the classical zeros. The
`tau = 1` control dips sharply at every marked zero and the `tau = 0` trace does
not, while the ratio is 3.5 to 7.5 there and tightly clustered across six
independent heights.

Not settled: *where* the graded zeros are. Locating them by the deepest minima
of the raw product fails. At `tau = 0.5` the minima reproduce the `tau = 1`
positions to within 0.05 against classical-zero deviations of 0.02 to 0.10,
which means they are tracking truncation rather than the function. A localisation
claim needs an analytic continuation of `Z_A` into the critical strip, and none
has been built.

General form: **a comparison can falsify a match without being able to certify a
mismatch in position.** Say which direction the evidence runs.

## 12. `numpy.bool` Is Not `bool` to a Type Checker

A type checker rejects

```python
def is_x(self) -> bool:
    return np.isclose(self.a, 0.0)
```

with

```text
Type "numpy.bool[builtins.bool]" is not assignable to return type "bool"
```

`np.isclose`, `np.allclose` and `np.array_equal` are declared as returning
`np.bool[builtins.bool]` in the numpy 2.x stubs. `np.bool_` subclasses `bool`,
so this works at runtime and every test passes, but the declared annotation is
a lie to the checker.

Wrap it: `return bool(np.isclose(...))`. Same for `np.isscalar`, and for
`np.all`/`np.any` applied to an array.

Worth recording because it is invisible in testing: the runtime behaviour is
correct, so only a static check catches it. Note also that a test asserting
`is True` or using `assert` will not distinguish the two, since `np.bool_` is
truthy in the same way.

## 13. Falsification Grid Result

The default falsification grid was run with:

- dimensions `[10, 20, 30]`;
- couplings `[0.0, 0.25, 0.5, 1.0, 2.0, 5.0]`;
- symmetry-breaking values `[0.0, 0.5, 1.0, 2.0, 5.0]`; and
- seed `42`.

This produced 90 parameter points:

| Result | Count |
|:---|---:|
| GUE-like | 10 |
| GOE-like | 16 |
| Poisson-like | 4 |
| Intermediate | 60 |

The minimum mean ratio was `0.304776`. The maximum was `0.611747`, reached at
`dim_per_sector = 10`, `coupling = 0.5`, and
`symmetry_breaking = 2.0`. The current heuristic therefore returned
`supported` because at least one point entered the GUE window `[0.58, 0.62]`.

This is a mixed result, not a confirmation of DSH. Most tested points were
intermediate, and the favorable point occurred at the smallest tested
dimension. The grid also uses one random seed per parameter point, so the
result needs repeated-seed and larger-dimension validation before it can be
interpreted as robust evidence.

The result demonstrates why a single maximum mean `r` is insufficient. Future
falsification summaries should report stability across seeds, finite-size
scaling, control ensembles, KS distances, and spectral density.

The reproducible runner `scripts/run_falsification.py` now writes the complete
console table, `output/falsification_heatmap.png`,
`output/falsification_histogram.png`, and
`output/falsification_summary.txt`. These artifacts make the result reviewable
without treating a generated plot as a proof.

## 14. A Probe Whose Prime-Dependence Cancels Is Not a Probe

The external `rh_idea_framework` prototype's "Stage D" arithmetic probe was
meant to test whether a candidate map `w` interacts with the Euler product, by
comparing `w(p^{-s})` against `p^{-w(s)}` for each prime `p`. The code actually
computed

```text
lhs = w(-s) * log(p)
rhs = -w(s) * log(p)
```

and took the *relative* error `|lhs - rhs| / max(|lhs|, |rhs|)`. Both `lhs` and
`rhs` carry the same factor `log(p)`, so the factor cancels out of the relative
error exactly:

```text
|w(-s) + w(s)| / max(|w(-s)|, |w(s)|)
```

which contains no `p` at all. The per-prime error was therefore identical for
every prime, the spread across primes was always ~0, and the probe's
"p-dependent mismatch" flag (and the pipeline's `"D+"` stage) could never fire.
The test was silently measuring "is `w` odd under negation", not "does `w`
distinguish primes".

Two lessons follow.

First, a diagnostic whose headline signal is a *spread across* a parameter must
be checked for accidental invariance in that parameter. Dimensional analysis on
the probe's own formula would have caught this in one line.

Second, a numeric gate should be unit-tested against both a map that must pass
it and a map that must fail it. In the corrected port
(`riemann_framework/idea_pipeline.py`), `probe_multiplicative_coupling("s")`
gives spread ~1e-17 (identity commutes with every Euler factor) while
`probe_multiplicative_coupling("1 - s_conj")` gives spread ~0.28 (the
reflection genuinely distinguishes primes), and both are asserted in
`tests/test_idea_pipeline.py`. The corrected comparison is `w(p^{-s})` versus
`p^{-w(s)}`, evaluated with mpmath so that large map values do not overflow
Python's complex exponentiation.
