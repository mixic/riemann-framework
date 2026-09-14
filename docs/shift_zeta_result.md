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

# Shift-Zeta Result

**Outcome: null result (the mission's outcome 3).** The graded algebra
framework is well-defined and computable, but it does **not** yield a
shift-zeta whose zeros can be shown to coincide with — or to differ from — the
classical Riemann zeros. The obstruction is structural and is identified below.

This document contains no proof of the Riemann Hypothesis and no claim of one.
The Riemann Hypothesis remains open.

## What was built

- `python/riemann_framework/graded_algebra.py` — the graded algebra
  `A = A₀ + ωA₁` with `ω² = 1`, the involution `σ(x) = ωxω`, three trace
  functionals, and the local factors
  `1/(1 - p^{-s}γ_τ)` with
  `γ_τ = ((1+τ)/2)I + ((1-τ)/2)ω`.
- `python/riemann_framework/shift_zeta.py` — the Euler product in `A`, the
  functional-equation test, and the zero comparison.
- `python/tests/test_graded_algebra.py` — 197 tests, all passing.
- `scripts/run_shift_zeta_analysis.py` — reproduces every number below and
  writes `output/shift_zeta_summary.txt`, `shift_zeta_traces.png`,
  `shift_zeta_convergence.png`.

## Criterion verdicts

| ID | Criterion | Verdict | Evidence |
|:---|:---|:---|:---|
| G1 | Graded algebra well-defined | **PASS** | `ω² = 1`; associativity, distributivity, units, inverses verified; zero divisors rejected |
| G2 | `σ` is an algebra homomorphism | **PASS** | `σ(xy) = σ(x)σ(y)` for all sampled `x, y` |
| G3 | Trace invariant under `σ` | **PASS** | `tr(σ(x)) = tr(x)`, exact |
| G4 | Shift-zeta computable | **PASS** | finite complex values for all tested `s`, `τ` |
| G5 | Functional equation holds | **FAIL** for `τ ≠ 1` | see below |
| G6 | Zeros in `Fix(σ)` | **UNDECIDABLE** | see below |
| G7 | Euler product converges | **PASS** at `τ = 1` | relative error `5.1e-4` at `s=2`, `5.9e-12` at `s=5`, 600 primes |
| F4 | Involution not a homomorphism | not triggered | G2 passes |
| F5 | Supertrace not invariant | **triggered as expected** | the supertrace is *anti*-invariant: it flips sign |

### A note on G3 versus F5

These are not in conflict. For `x = a + bω` the regular representation is
`diag(a+b, a−b)`, and `σ` **swaps those two eigenvalues**. The `σ`-invariant
functional is therefore their average, which is `a`; that is `trace`, and it
satisfies G3. The half-difference is `b`; that is `supertrace`, it changes sign
under `σ`, and it vanishes exactly on `Fix(σ) = A₀`. The two functionals are
different objects and only `trace` is invariant.

## The graded trace agrees with `ζ` only at `τ = 1`

Graded trace of `Z_A(s)` against `mpmath`'s `ζ(s)`, 600 primes:

| `τ` | `s=2` | `s=3` | `s=4` | `s=5` | `s=6` | max rel. err |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1.64489 | 1.20206 | 1.08232 | 1.03693 | 1.01734 | 2.4e-05 |
| 0 | 1.32245 | 1.10103 | 1.04116 | 1.01846 | 1.00867 | 1.96e-01 |
| 0.5 | 1.45586 | 1.14790 | 1.06105 | 1.02755 | 1.01297 | 1.15e-01 |
| 0.25 | 1.38370 | 1.12364 | 1.05094 | 1.02297 | 1.01081 | 1.59e-01 |
| 2 | 2.37212 | 1.33970 | 1.12958 | 1.05664 | 1.02630 | 4.42e-01 |

(`ζ(2) = 1.64493`, `ζ(3) = 1.20206`, `ζ(4) = 1.08232`, `ζ(5) = 1.03693`,
`ζ(6) = 1.01734`.)

At `τ = 1` the weight `γ₁ = I`, every local factor is scalar, and the graded
trace equals the classical Euler product term by term — the `2.4e-05` is pure
Euler truncation at 600 primes, and it shrinks as more primes are used.

For `τ ≠ 1` the trace leaves the classical values by 11% to 44% at `s = 2`. This
is the mechanism behind the null result: the graded trace is a genuinely
different function, but it is *only computable where the Euler product
converges*, namely `Re(s) > 1`, and that region contains no zeros.

## The functional equation fails away from `τ = 1`

Residual `|ξ_τ(s) − ξ_τ(1−s)| / |ξ_τ(s)|`, with the classical completion
`π^{−s/2}Γ(s/2)`:

| `s` | classical control | `τ = 1` | `τ = 0.5` | `τ = 0` |
|---:|---:|---:|---:|---:|
| 2.5 | 0.000e+00 | 1.98e-06 | 7.60e-02 | 1.46e-01 |
| 3.5 | 1.77e-31 | 1.00e-09 | 3.04e-02 | 5.96e-02 |
| 4.5 | 4.07e-31 | 5.91e-13 | 1.35e-02 | 2.66e-02 |

The classical control sits at numerical precision, and `τ = 1` reproduces it —
so the methodology is sound. For `τ ≠ 1` the residual is `1e-2` to `1e-1`,
three to ten orders of magnitude above the truncation floor. **The graded
shift-zeta does not satisfy the completion symmetry.** No falsification
criterion is triggered (F2 requires failure for *all* `s > 1`, and `τ = 1`
succeeds), but the graded family fails.

## The zeros comparison is undecidable at accessible truncation

Criterion G6 asks whether the shift-zeta zeros coincide with the classical
zeros. Two diagnostics were tried; both are limited by the same problem.

**Ratio test.** Compare `R(s) = Z_A(s,τ) / ∏_p^{N}(1−p^{−s})^{−1}` — the graded
trace against the *same truncated* classical product, so Euler truncation
cancels. If the zero sets agreed, `|R|` would be comparable at the classical
zeros and at generic points on the critical line:

| `τ` | mean `\|R\|` at classical zeros | at control points | spread |
|---:|---:|---:|---:|
| 0 | 6.13 | 2.84 | 1.73 |
| 0.5 | 2.17 | 1.45 | 1.20 |
| 0.9 | 1.14 | 1.05 | 1.03 |
| 2 | 0.55 | 0.78 | 1.06 |

The ratio does not separate the two sets at any tested `τ`. This is not
evidence that the zeros agree; it is a failure of the diagnostic to resolve the
question.

**Sign-change scan** on the critical line is worse. At `τ = 1` — where the
graded trace *equals* the classical partial product by construction, so
whatever the scan finds is a pure truncation artefact — it reports **28 sign
changes against 4 classical zeros** in `t ∈ [0.5, 30]`, with 24 spurious.

That control is decisive: the truncated Euler product at a few hundred primes
oscillates near the critical line and does not locate zeros. **G6 is therefore
undecidable with this construction, and this is a limitation of the
methodology, not a finding about the zeros.**

## Why the framework cannot answer the central question

The construction is confined by its own definition.

Every local factor is a polynomial in the single element `γ_τ`, so the whole
product lies in the two-dimensional algebra `C[γ_τ]`. There is no interaction
*between* primes: the product is a product of functions of one generator. And
at `τ = 1` the generator is the identity, so the graded trace *is* the classical
Euler product and `Z_A(s) ∈ Fix(σ)` trivially.

The central question — *does the Euler product, lifted to the graded algebra,
force the zeros into `Fix(σ)`?* — is not answered here because the lift never
leaves `Fix(σ)`: it is built there. A construction that places its object inside
the fixed locus by definition cannot test whether zeros are forced there. That
is the structural obstruction, and it is the substantive finding of this
exercise.

A variant worth trying would need at least one local factor that is **not** a
function of `γ_τ` alone — for instance a genuinely non-commutative extension
whose local factors at different primes fail to commute. In the commutative
setting used here that cannot happen.

## What this does and does not establish

**Does not establish:** anything about the Riemann Hypothesis; whether the
zeros of the graded shift-zeta lie on the critical line; whether a graded
extension of `ζ` is impossible in general.

**Does establish, with numbers:** the graded algebra is well-defined and `σ` is
an algebra homomorphism (G1, G2); the graded trace is `σ`-invariant and the
supertrace is anti-invariant (G3, F5); the graded trace reproduces the classical
Euler product exactly at `τ = 1` and deviates by up to 44% for `τ ≠ 1`; the
family fails the functional equation for `τ ≠ 1`; and the zero comparison is
undecidable at accessible truncation, with the `τ = 1` control showing why.

## Reproducing

```powershell
python scripts/run_shift_zeta_analysis.py
python -m pytest python/tests/test_graded_algebra.py -q
```
