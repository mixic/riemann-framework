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

# Screening operator candidates

## Abstract

`docs/hilbert_polya.md` built one operator and measured four gaps. This page asks
the question that follows: **can a candidate be screened at all?** It constructs
three new candidates, applies the same five criteria to each, and reports a
result that is uncomfortable for the whole programme.

**The Riemann hypothesis is not proved, and nothing here gets closer to proving
it.** What this page does establish is that the numerical tests the programme
usually relies on — spacing statistics above all — do not distinguish a real
candidate from an empty one.

    python scripts/run_operator_candidates_demo.py   # output/operator_candidates.png

## The candidates

| candidate | definition | self-adjoint | spectrum computable |
|:---|:---|:---|:---|
| prime-length quantum graph | **new here**: star graph, edge lengths `(1/2) log p_j` | yes, by construction | yes, one secular equation |
| fixed box | `-i d/dy` on a circle of circumference `L` | yes | yes, `2 pi n / L` |
| primon gas | energies `log n`, one mode per prime | yes | yes, `N(T) = e^T` |
| unitary twin | `U diag(gamma) U^dagger` — *not a candidate* | yes | tautologically |

## 1. The prime-length quantum graph

The Gutzwiller dictionary says: energy levels ↔ zero ordinates, closed orbits ↔
primes, orbit period ↔ `log p`. The hard box of `hilbert_polya.py` fails it
because a circle has one orbit length, repeated. A graph can realize the
dictionary literally.

Take a **star**: one central vertex, `m` edges ending in Dirichlet walls, edge
lengths `ell_j = (1/2) log p_j`. The wavefunction on edge `j` is
`A_j sin(k(ell_j - x))`, Kirchhoff (flux conservation) at the centre gives
`sum_j A_j = 0`-type matching, and eliminating the amplitudes leaves

```
sum_j cot(k ell_j) = 0.
```

That is the entire spectral problem, and it is self-adjoint by construction —
no boundary condition has to be guessed, which is exactly what went wrong in
BBM (`docs/hilbert_polya.md` §4).

**The dictionary holds exactly, and it is verified rather than asserted.**
`closed_orbit_lengths` writes a closed path as a sequence of round trips, computes
its length as `sum_j 2 n_j ell_j` from the geometry, and compares it with `log n`
for `n = prod p_j^{n_j}`: all 23 such paths with `n <= 30` match to `1e-12`. The
half-lengths are chosen precisely so that the round trip is `log p_j`; the other
option (`log p_j`) is kept in the code and is exactly twice as large, so the
favourable choice is not being smuggled in.

The spectrum: between consecutive poles of the secular function (the union of
`n pi / ell_j`) the function is strictly decreasing from `+inf` to `-inf`, so
bisection finds exactly one level per interval and cannot miss one. In `k <= 120`
there are **150 levels**, and `N(k)/k = 1.250` against the Weyl prediction
`L/pi = 1.233`. **The counting function is linear**, so the density is wrong in
the way `hilbert_polya.py` §2.2 describes — but the spacings are *not* uniform:
below `k = 14` the gaps range `0.269 … 1.480` against the lattice constant
`0.811`. It is a jittered lattice, not a picket fence.

## 2. Finding: the dictionary is satisfiable without `ζ`

`prime_orbits.py` recorded that the orbit dictionary **relocates** RH rather than
approaching it. This is the concrete demonstration: an operator whose closed
orbits are exactly the primes, whose spectrum is `N(k) ~ (L/pi) k`, and which has
nothing to do with the zeta zeros.

The counting functions make the distance explicit. Below `k = gamma_1 = 14.13`
the graph has **20 levels**; the zeros have **1**.

## 3. Finding: the spacing statistics are not a certificate

This is the sharpest result on this page, and it is the reason the page exists.

| object | mean `r`-ratio | KS distance to the Wigner surmise |
|:---|---:|---:|
| GUE reference (`statistics.REFERENCE_R`) | `0.599` | — |
| **prime-length graph** | **`0.641`** | **`0.0438`** |
| zeta zeros (first 100) | `0.610` | `0.0579` |
| Poisson | `0.386` | large |

The graph scores **higher** on the `r`-ratio than the zeros do and is **closer**
to the Wigner surmise than the zeros are, while its counting function is wrong by
a factor of twenty at the first zero. An object that provably is not the zeros
fits the universal statistics better than the object it is supposed to explain.

Consequences, stated plainly:

- `statistics.py`'s `mean_r_ratio` / `ks_test_against` cannot certify a candidate.
  They can eliminate one with no level repulsion at all, and that is the limit.
- The Dimension-Shift Hypothesis criterion **S2** ("model statistics comparable to
  the zero baseline") is nearly vacuous. `docs/central_hypothesis.md` already says
  the formulation must be "stronger than 'the model has GUE statistics'"; that
  warning is now demonstrated rather than asserted.
- Why it happens: universal statistics are universal. Any sufficiently
  incommensurate superposition of oscillatory modes gives level repulsion, and
  `sum_j cot(k ell_j) = 0` is such a superposition. Matching GUE is cheap;
  matching *which* numbers appear is not.

## 4. Finding: every operator with the zeros as spectrum is the same operator

By the spectral theorem, a self-adjoint operator with simple spectrum
`{gamma_n}` is unitarily equivalent to `diag(gamma_n)`. The *twin* is
`U diag(gamma) U^dagger` for a random unitary `U` — deliberately **not**
diagonal, so that it is a genuine operator rather than a list:

| screen | twin |
|:---|:---|
| Hermiticity | `1.8e-14` |
| `max |E_n - gamma_n|` | `2.0e-13` |
| `|Tr - sum gamma_n|` | `1.8e-12` |
| `r`-ratio | `0.610` (the zeros' value) |
| KS to Wigner | `0.0579` (the zeros' value) |

Every numerical test passes and nothing is proved, because the twin's definition
*is* the zeros. The logical consequence is worth stating precisely, because it
governs how any proposal in this area should be read:

> The content of a Hilbert–Pólya construction is not the existence of an operator
> whose spectrum is the zeros — those are `diag(gamma)` and its unit conjugates,
> and they prove nothing. The content is that the operator is defined **without
> reference to `zeta`** and that its spectrum is **proved** to be the zeros, for
> infinitely many levels, by an argument that does not assume they are real.

So a construction whose spectrum is *defined* by an integral or transform
involving `zeta` is in the twin's class until an independent identification
argument is supplied. That is a statement about logical form, not about any
particular paper.

## 5. Finding: the density requirement is real but is not a screen

`dN/dT = (1/2 pi) log(T/2 pi) + O(1)` is unbounded. No Weyl power law
`N = C T^alpha` has an unbounded logarithmic density: `alpha = 1` is constant,
`alpha > 1` is a power, and `log T` is neither. So asymptotically the density
**does** reject every fixed finite-dimensional regularization — the box and the
graph both fail for this reason.

But asymptotics are invisible where the numbers are. Measured over the first 100
zeros:

| `T` | exact `N(T)` | best power law `0.03952 T^1.436` | Riemann–von Mangoldt |
|---:|---:|---:|---:|
| 20 | 1 | 2.92 | 1.38 |
| 50 | 10 | 10.88 | 9.42 |
| 100 | 29 | 29.43 | 29.00 |
| 150 | 52 | 52.69 | 52.75 |
| 200 | 79 | 79.64 | 79.19 |

The power law reproduces the counting function to **1.33 levels out of 100**, and
the local exponent `log N / log T` drifts `0.589 -> 0.731 -> 0.825` instead of
being constant — visible, but only just. **A density-based rejection at
`T <= 236` is not evidence of anything.** The `dN/dT` measurement does rise
monotonically (`0.278 -> 0.380 -> 0.460 -> 0.543` per unit height), which is what
a logarithm looks like, but a fitted power law has a rising density too.

The honest summary: the density requirement is a constraint on any *future*
construction, not a test of a present one. This is the same limitation that
`docs/hilbert_polya.md` §2.2 found for the box, sharpened.

## 6. The screening table

| candidate | independent definition | density class | statistics | reality is a theorem | identification proved |
|:---|:---|:---|:---|:---|:---|
| fixed box | yes | no (linear) | no (`r = 1.000`) | yes | no |
| prime-length graph | yes | no (linear) | **yes** | yes | no |
| primon gas | yes | no (`e^T`) | n/a | yes | no |
| unitary twin | **no** | yes | yes | yes | **yes** |

No candidate satisfies both criteria that would make it a candidate
(`survivors` returns the empty list). The pattern is the finding:

- the box fails on statistics and density, and is an honest attempt;
- the graph is *better* than the box on statistics and no better on anything
  that matters;
- the twin is perfect on every numerical criterion and worthless;
- the one criterion that separates them — whether the definition mentions
  `zeta` — is read off the source and cannot be measured.

## 7. On the cited preprint

[arXiv:2503.09644](https://arxiv.org/abs/2503.09644) (Tamburini, *A Majorana
Relativistic Quantum Spectral Approach to the Riemann Hypothesis in
(1+1)-Dimensional Rindler Spacetimes*) proposes a Hamiltonian `H_M` whose spectrum
is claimed to be in bijection with the zero ordinates, argues essential
self-adjointness by deficiency indices and Krein extension theory, and concludes
RH. Its abstract states that the spectrum is defined by "a Mellin–Barnes integral
that explicitly contains" `zeta`.

I have not verified the 73-page argument, so this is not a verdict on it. Two
questions decide its status, and both are questions of logical form:

1. **Is `H_M` defined without `zeta`?** If the spectrum is fixed by an integral
   containing `zeta`, then §4 applies: the self-adjointness of an operator whose
   spectrum is defined through `zeta` establishes something about that operator,
   and the identification with the zeros has to come from somewhere independent.
   If instead `H_M` is a geometric operator on Rindler space and the integral is
   only how the correspondence is *displayed*, the construction is a genuine
   candidate and the work is in the identification step.
2. **What is its counting function?** A differential operator on a fixed
   background has a Weyl law, `N(E) ~ C E^alpha`. If the claimed spectrum is
   exactly the zeros, its counting function must be `(T/2 pi) log T`. Those
   cannot both hold asymptotically (§5), so one of the two -- the Weyl law of the
   geometric model, or the identification -- must fail at large energy. This is
   checkable from the paper's own formulae and is the single most informative
   thing to test.

Neither question can be settled numerically, which is the point of §3 and §4.

## 8. What a new idea must satisfy

The four screens of `hilbert_polya.py` become five here, and the first one is not
numerical:

1. **Independence.** Is the operator defined without `zeta` or the zeros? Audit
   the source; a construction that mentions them is `diag(gamma)` in disguise
   (§4).
2. **Density class.** Does the counting function have an unbounded logarithmic
   density rather than a Weyl power law? Note that at accessible heights this
   cannot be observed (§5), so the answer must come from analysis, not fitting.
3. **Non-uniform, GUE-like spacings.** Necessary, nowhere near sufficient — the
   prime graph passes and is not the zeros (§3).
4. **Reality is proved, not observed.** Self-adjoint by construction, or the
   unbroken `PT` phase established with its threshold (`hilbert_polya.py` §2.3).
5. **Identification.** Is `spectrum = zeros` a theorem for infinitely many levels,
   established without assuming the zeros are real? This is the open problem and
   the only criterion that matters.

No known construction clears 1 and 5 together.

## Reproduce

```bash
python scripts/run_operator_candidates_demo.py      # output/operator_candidates.png
cd python && python -m pytest tests/test_operator_candidates.py -q
```

## Files

| File | Contents |
|:---|:---|
| `riemann_framework/operator_candidates.py` | the prime-length graph, the twin, the density analysis, the screening table |
| `tests/test_operator_candidates.py` | 33 tests, including the statistics trap and the twin |
| `scripts/run_operator_candidates_demo.py` | the six-panel figure |

## Status

The Riemann hypothesis is **open**. This page is a negative result about
screening: the numerical criteria the programme relies on can be satisfied by
operators that are not candidates at all, and the one criterion that decides
cannot be measured. It is offered as a checklist, not as a construction.

## Desymmetrise before screening

A screening test built on spacing statistics is biased low whenever the candidate
commutes with a symmetry, because the full spectrum is then a superposition of
sectors and `⟨r⟩` falls toward Poisson without any integrability being involved.
Measured: one sector gives `0.53` (GOE) / `0.60` (GUE), two sectors both give about
`0.42`, and three or more give `0.39`, which is the Poisson value. A candidate that
looked "Poisson-like" may simply have an unresolved symmetry.

The prime-length graph in this module has no such symmetry (its spectrum is the
secant equation's roots, not a union), so its measured `0.641` is not contaminated.
But any candidate built as a direct sum, a graded space, or a `Z₂`-symmetric pair
must be split first: see [`desymmetrisation.md`](desymmetrisation.md) and
`desymmetrisation.desymmetrise`. Counts are not recoverable from the statistic —
only the split is.
