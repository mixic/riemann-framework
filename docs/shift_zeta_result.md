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

**Outcome: negative result (the mission's outcome 2), with a null component.**
The graded algebra framework is well-defined and computable. It does **not**
reproduce the classical zeros: for `τ ≠ 1` the graded trace does not satisfy the
functional equation, is not a scalar multiple of `ζ`, and is *larger* at the
classical zeros than at neighbouring heights, so its own zeros lie elsewhere.
The reason is structural and is identified below.

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
  writes `output/shift_zeta_summary.txt` and four figures:
  `shift_zeta_traces.png`, `shift_zeta_convergence.png`,
  `shift_zeta_critical_line.png`, `shift_zeta_comparison.png`.

## Criterion verdicts

| ID | Criterion | Verdict | Evidence |
|:---|:---|:---|:---|
| G1 | Graded algebra well-defined | **PASS** | `ω² = 1`; associativity, distributivity, units, inverses verified; zero divisors rejected |
| G2 | `σ` is an algebra homomorphism | **PASS** | `σ(xy) = σ(x)σ(y)` for all sampled `x, y` |
| G3 | Trace invariant under `σ` | **PASS** | `tr(σ(x)) = tr(x)`, exact |
| G4 | Shift-zeta computable | **PASS** | finite complex values for all tested `s`, `τ` |
| G5 | Functional equation holds | **FAIL** for `τ ≠ 1` | see below |
| G6 | Zeros in `Fix(σ)` | **FAIL** (numerically) | the graded zero set does not coincide with the classical one; see below |
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

## The zeros do not coincide with the classical zeros

Criterion G6 asks whether the shift-zeta zeros coincide with the classical
zeros. The decisive evidence is a controlled comparison, and the control is what
makes it decisive.

**The control.** At `τ = 1` the graded trace *is* the classical partial Euler
product, term by term. So whatever a zero-locating diagnostic reports at
`τ = 1` is a pure truncation artefact. In
`output/shift_zeta_comparison.png`, the right-hand panel shows the `τ = 1`
trace dipping sharply and exactly at every marked classical zero, while the
left-hand `τ = 0` panel shows no corresponding dips at all. The method
*can* resolve zeros — at `τ = 1` it does.

**The measured ratio.** `|Z_A(ρ, τ)| / |Z_A(ρ, 1)|` at the first six classical
zero heights. Both numerator and denominator are truncated over the same primes,
so the truncation factor cancels and the ratio isolates the grading:

| `τ` | ratios at the first six zeros |
|---:|---|
| 0 | 7.54, 5.72, 4.35, 6.88, 6.14, 3.45 |
| 0.5 | 2.25, 2.07, 1.97, 2.35, 2.19, 1.75 |
| 2 | 0.551, 0.565, 0.551, 0.533, 0.543, 0.557 |

Two features make this informative despite the oscillation of the underlying
product: the ratio is tightly clustered across six independent heights (a noisy
quantity would not be), and it is **not** equal to 1. If the graded trace
vanished at the classical zeros the ratio would sit far below 1; at `τ = 0` it
is 3.5 to 7.5.

**Conclusion.** For `τ ≠ 1` the graded trace is strictly larger at the classical
zero heights than its own typical size, and it shows none of the dip structure
that the `τ = 1` control shows there. Its minima therefore lie elsewhere: the
zero sets do not coincide. This satisfies falsification criterion **F1**, which
reproduces the mission's scenario 2 — *the framework does not reproduce RH*.

**What this does and does not establish.** It establishes numerically that the
graded trace is not merely a scalar multiple of `ζ` for `τ ≠ 1`, and that the
natural graded shift-zeta built here fails to reproduce the classical zeros. It
does not establish any theorem about the critical line, and it does not rule out
other gradings, other local factors, or other traces.

**A withdrawn statistic, recorded.** An earlier version of this analysis flagged
the "deepest local minima" of the graded trace and counted how many fell within
0.5 of a classical zero. It scored 7 of 8 at `τ = 1` — the control, where the
trace is the classical product — so it was measuring the oscillation of a
truncated product rather than the location of zeros. It was removed rather than
reported.

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

**Does not establish:** anything about the Riemann Hypothesis; where the
graded zeros actually are, or whether they lie on the critical line; whether a
graded extension of `ζ` is impossible in general. What fails is one particular
family of local factors and one particular trace.

**Does establish, with numbers:** the graded algebra is well-defined and `σ` is
an algebra homomorphism (G1, G2); the graded trace is `σ`-invariant and the
supertrace is anti-invariant (G3, F5); the graded trace reproduces the classical
Euler product exactly at `τ = 1` and deviates by up to 44% for `τ ≠ 1`; the
family fails the functional equation for `τ ≠ 1`; and the graded trace does not
share the classical zeros, being 3.5 to 7.5 times larger at those heights for
`τ = 0` while the `τ = 1` control dips sharply there (F1).

## Reproducing

```powershell
python scripts/run_shift_zeta_analysis.py
python -m pytest python/tests/test_graded_algebra.py -q
```

Both commands run from the repository root; the script inserts the `python`
directory on `sys.path` itself, so there is no need to `cd python` first. The
analysis writes four figures plus `output/shift_zeta_summary.txt`:

| File | What it shows |
|:---|:---|
| `shift_zeta_traces.png` | graded trace vs classical `ζ`, by `τ` |
| `shift_zeta_convergence.png` | Euler truncation error vs number of primes |
| `shift_zeta_critical_line.png` | exact `\|ζ(1/2+it)\|` against the raw graded product |
| `shift_zeta_comparison.png` | graded trace on the critical line with the classical zeros marked, and the `τ = 1` control |
