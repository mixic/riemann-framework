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

# Quantum-Chaos Claims: What Was Already Here, What Is New, and What Is Wrong

## Abstract

A second long account was submitted — Hilbert–Pólya, the Montgomery–Dyson
meeting, the Gutzwiller trace formula, imaginary time, the Riemann gas, lab
analogues, and AI. The instruction was to take only what is new and ignore what
is already covered.

**Most of it is already covered.** This repository has the primon gas implemented
and tested (`primon_gas.py`, 32 tests), GUE statistics (`quantum_chaos.py`), and
Berry–Keating, Connes and the trace-formula programmes documented in
`docs/dimension_shift_quantum_chaos.md` and `docs/research_notes.md`. Reproducing
any of that would have been duplication.

Four things were genuinely absent — zero hits anywhere in the tree:

| absent | now |
|:---|:---|
| Wick rotation / imaginary time | `imaginary_time.py`, 15 tests |
| Hagedorn temperature (the account says Bose–Einstein) | corrected and measured |
| the Gutzwiller trace formula by name | `prime_orbits.py`, 16 tests |
| prime-orbit counting | `prime_orbits.py` |

    python scripts/run_quantum_chaos_claims_demo.py   # output/quantum_chaos_claims.png

## 1. Already covered, and deliberately not repeated

| claim in the account | where it already lives |
|:---|:---|
| Montgomery–Dyson, GUE **spacing** statistics | `quantum_chaos.py`, `statistics.py`, `docs/central_hypothesis.md` |
| Hilbert–Pólya: a self-adjoint operator with the zeros as spectrum | `docs/central_hypothesis.md` §3, `docs/dimension_shift_quantum_chaos.md` |
| Riemann gas: `Z(β) = Σ n^{−β} = ζ(β)`, one bosonic mode per prime | `primon_gas.py`, `tests/test_primon_gas.py` |
| Julia 1990 / Spector 1990 / Bost–Connes 1995 | `primon_gas.py`, `docs/graded_prime_monoid.md` |
| Berry–Keating `H = xp`, Connes' adele class space | `docs/research_notes.md`, `docs/dimension_shift_quantum_chaos.md` |
| an operator trace reproducing the Euler product, but with spectrum `log n` | `primon_gas.py`, README |
| Shor, RSA, post-quantum migration | `docs/number_theory_claims.md` |
| Lean/Coq formalisation | `lean/`, `docs/future_work.md` Priority 4 |

**Correction to that table.** The first row originally said "pair correlation",
which is wrong. What `statistics.py` implements is the **nearest-neighbour gap
distribution** -- `level_spacings`, the Wigner surmise `gue_spacing_pdf`, the
ratio statistic `mean_r_ratio`, and KS tests against GUE/GOE/Poisson. Those are
*one-point* statistics. **Montgomery's pair correlation function
`R₂(x) = 1 − (sin πx / πx)²` is not implemented anywhere in this repository** --
it is cited in eight documents and two idea records and computed in none. The two
are not the same quantity, and matching the Wigner surmise does not establish the
pair correlation: the surmise is the exact `2×2` GUE gap distribution and only an
approximation to the large-`N` one, whereas Montgomery's theorem is a statement
about the two-point function. `proportion_certificates.cos_square_kernel` also
uses `sinc`, but that is Lamzouri's kernel from the proportion proof, a different
object.

## 2. New: imaginary time

The account's table maps real time to imaginary time, and that mapping is the
*bridge* between the two halves this repository already has — the statistical
(primon gas) and the spectral (zeros as levels). Neither half states the point
that makes the bridge load-bearing:

> **The real-time trace diverges. It is the imaginary-time trace that converges.**

On the primon gas `H|n⟩ = log(n)|n⟩`:

```
real time:       Tr[e^{-iHt}] = Σ_n n^{-it}      |n^{-it}| = 1, so partial sums ~ N
imaginary time:  Tr[e^{-τH}] = Σ_n n^{-τ}        converges for τ > 1, equals ζ(τ)
```

Measured: `|Σ_{n≤N} n^{−it}|/N` is constant at `0.0766` across a 128-fold range of
`N` — linear divergence. The thermal error `|Σ_{n≤N} n^{−β} − ζ(β)|` at `β = 2`
falls `2.0e−3 → 1.6e−5` over the same range, halving each doubling.

Two consequences the account does not draw:

- **The critical strip is exactly the continuation problem.** The thermal trace
  exists for `Re s > 1` and nowhere else, so the entire region RH is about — the
  critical strip — is reached by analytic continuation, not by summation.
- **The mechanism of that continuation is Jacobi's theta identity**,
  `θ(x) = x^{−1/2} θ(1/x)`, checked here to `1e−16`. It is `s ↦ 1 − s` seen in
  imaginary time, and unlike the Dirichlet series it converges for every `x > 0`
  because the exponent is quadratic in `n`.

## 3. Correction: Hagedorn, not Bose–Einstein

The account says cooling the gas to `β = 1` "corresponds to a phase transition
(related to Bose–Einstein condensation)". That is the wrong phase transition.

`E_n = log n` means the number of states below energy `E` is `⌊e^E⌋`, so the
density of states grows **exponentially**. An exponentially growing state count
produces a **Hagedorn temperature** — a *maximum* temperature, at `β = 1`, above
which the partition function diverges because the state count outruns the
Boltzmann factor. Bose–Einstein condensation is the opposite phenomenon: a
*minimum* temperature at which a finite supply of low-lying states is exhausted.

The distinction is measurable, and measured: the ratio
`#{E_n ≤ E} / #{E_n ≤ E−1}` settles at `e = 2.71828` and stays there
(`2.700` – `2.741` over `E = 4..40`) instead of decaying towards 1. A condensate
would show it falling to 1.

## 4. New: the prime-orbit dictionary, and where it stops

### The part that is exact

For a hyperbolic (Anosov) flow with topological entropy `h`, the number of
primitive periodic orbits of period at most `T` obeys `π(T) ~ e^{hT}/(hT)`. If the
orbits have periods `log p`, the count is `π(e^T)`, and the prime number theorem
gives `π(e^T) ~ e^T/T`. **The two are the same statement with `h = 1`** — the
entropy is not a free parameter, it is forced by the periods being logarithms of
primes.

Measured, and it holds:

| `T` | `e^T` | primes | `e^T/T` | ratio |
|:---|:---|:---|:---|:---|
| 6 | 403 | 79 | 67 | 1.175 |
| 9 | 8,103 | 1,019 | 900 | 1.132 |
| 12 | 162,754 | 14,912 | 13,563 | 1.100 |
| 15 | 3,269,017 | 234,855 | 217,934 | 1.078 |

So the dictionary is not an analogy at the level of counting. It is an identity.

### The part that does not, and this is the measured finding

The interesting object is the error term, and there the correspondence stops
helping:

```
ψ(X) = X − Σ_ρ X^ρ/ρ − log 2π − ½ log(1 − X^{−2})
```

The deviation of the orbit count from its smooth part is a sum over the **zeros**,
not over the orbits. A trace formula can reproduce the primes; it does not
constrain where the zeros are.

I first wrote this as a claim that "adding more zeros improves the
reconstruction". **Measurement says otherwise**, and the module now reports the
measurement:

| `X` | error over `K ≤ 89` zeros | zeros actually needed, `N(X)` | fraction used |
|:---|:---|:---|:---|
| 1,000 | `0.74` – `2.74` | 648 | 1.4e−1 |
| 10,000 | `1.26` – `14.58` | 10,142 | 8.8e−3 |
| 100,000 | `0.56` – `34.28` | 138,068 | 6.5e−4 |
| 1,000,000 | `48.6` – `339.5` | 1,747,145 | 5.1e−5 |

The errors **oscillate with no downward trend**, because the zero sum converges
only conditionally and a truncation carries an oscillating tail of size about
`X^{1/2}/γ_K`. And resolving `ψ(X)` needs on the order of
`(X/2π) log(X/2πe)` zeros — `3.9 × 10^{12}` of them at `X = 10^{12}`.

So the dictionary *relocates* RH into the trace formula rather than approaching
it, and the relocation is not a technicality: its error term is not computable at
any `X` where the first-order match is even visible.

Two bugs were found while measuring this, both recorded in the tests: the
`log 2π` and `½ log(1 − X^{−2})` terms were missing from `psi_from_zeros`
(a systematic offset of `−1.84`, which is exactly what makes a convergence
measurement look like noise), and the zero ordinates were recomputed on every
call — 90 seconds per evaluation, now 5.9 s for the whole table.

## 5. Claims in the account that are wrong

| claim | verdict |
|:---|:---|
| "Primzahl-Strukturen sind extrem stabil gegen äussere Störungen (Dekohärenz)" | **wrong.** Prime structure has nothing to do with decoherence resistance; there is no mechanism connecting them |
| microcavities shaped so the reflected light paths equal `log p`, letting one "photograph the zeros as dark lines" | **not what the experiments do.** Microwave-cavity work (Sridhar and others) reproduces *spectral statistics* — GUE-like spacing — not the zeta zeros themselves. Berry–Keating is a formal analogy, not a laboratory protocol |
| photonic crystals whose "optical energy states rise exactly with `log 2, log 3, log 5`" | **no such result is known to me**, and the account gives no reference |
| AI systems "verify the conjecture numerically for billions of zeros" | **wrong.** Numerical verification is deterministic computation — Odlyzko–Schönhage, then Gourdon–Demichel to `10^{13}` zeros — with no AI involved |
| AI "translates the physicists' bridges such as the Gutzwiller trace formula into strict mathematics to construct a complete formal proof of RH" | **not a thing that exists.** The formalisation track works on elementary lemmas; there is no route from the trace-formula analogy to a formal RH proof |
| "chaotic quantum cryptography": intercepting the key disturbs the chaotic system and produces visible turbulence | **this repository has already refuted this class of argument.** `docs/dimension_shift_quantum_communication.md` §4.1 proves that no function of a disturbance statistic bounds an adversary's information, with an explicit attack recovering every bit at `BER = 0.0000` and detection `0.0000` |
| Shor's algorithm "uses the principles of quantum chaos" | **loose.** Shor uses the quantum Fourier transform for period finding; quantum chaos is not a mechanism it employs |
| AI helping to formulate new conjectures about L-functions | **plausible in kind, not verified here.** AI-assisted conjecture generation is real; I have not checked this specific claim and it is recorded as unverified rather than endorsed |

## 6. Files

| file | role |
|:---|:---|
| `python/riemann_framework/imaginary_time.py` | Wick rotation, the two traces, Hagedorn, Jacobi theta |
| `python/riemann_framework/prime_orbits.py` | orbit counting, the `h = 1` correspondence, and the measured error-term limit |
| `python/tests/test_imaginary_time.py` | 14 tests |
| `python/tests/test_prime_orbits.py` | 17 tests |
| `scripts/run_quantum_chaos_claims_demo.py` | the four-panel figure |

## References

- Julia, B. (1990). *Statistical mechanics of the arithmetic gas*.
- Spector, D. (1990). *Supersymmetry and the Möbius inversion function*.
- Bost, J.-B. and Connes, A. (1995). *Hecke algebras, type III factors and phase transitions with spontaneous symmetry breaking in number theory*.
- Berry, M. V. and Keating, J. P. (1999). *The Riemann zeros and eigenvalue asymptotics*. SIAM Review.
- Gutzwiller, M. C. (1971). *Periodic orbits and classical quantization conditions*.
- Hagedorn, R. (1965). *Statistical thermodynamics of strong interactions at high energies*.
- Rodgers, B. and Tao, T. (2018). arXiv:1801.05914 — for the imaginary-time normalisation used in `de_bruijn_newman.py`.

## Disclaimer

Nothing here proves or disproves the Riemann hypothesis. The first-order orbit
correspondence is exact and is a statement about counting; the error term is where
RH lives, and Section 4 measures why the dictionary does not reach it. The
laboratory and AI claims in Section 5 are assessed against the literature, not
against any computation in this repository.
