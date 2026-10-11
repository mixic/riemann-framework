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

# A Fact-Check of a Popular Account, and What of It Can Be Simulated

## Abstract

A long German-language account of Dirichlet characters, Miller–Rabin, Shor's
algorithm, lattice cryptography and ML-KEM was submitted for investigation, with
a request for a simulation and unit tests. This document records the
investigation: what the account gets right, what it gets wrong, and — the
governing constraint — **which claims are simulable in this repository and which
are not**.

The rule applied throughout is the one this repository already uses: a simulation
must not appear to establish something its method cannot reach. Shor's algorithm
requires a quantum computer. The security of ML-KEM is a research-level
conjecture about lattice problems in dimension 500–1000. Neither is simulable
here, and a figure that looked like a demonstration of either would be the worst
kind of output — a picture implying a conclusion that no computation in it
supports.

So the account was split. Five claims are checkable and are now checked, with
tests and a figure. The rest are recorded as verdicts on the text, with sources
where the source was read.

    python scripts/run_number_theory_claims_demo.py   # output/number_theory_claims.png

## 1. The claim that is wrong, and interestingly so

> "Die Primzahlen sind absolut symmetrisch und gerecht auf beide Restklassen
> verteilt."

This is false, and it is the one error in the account that is wrong in an
instructive direction rather than a careless one.

Dirichlet gives **equal density in the limit**: each class among the units gets
the same share. What the account then does is treat that as *even distribution*,
and that is a different statement. The approach to the limit is biased, and the
bias has a name — **Chebyshev's bias**, proved to be a genuine limiting
phenomenon by [Rubinstein and Sarnak](https://zbmath.org/pdf/0823.11050.pdf).

Measured here:

| quantity | mod 4, classes 1 and 3 | mod 3, classes 1 and 2 |
|:---|:---|:---|
| counts below `10^6` | 39175 vs **39322** | 39231 vs **39266** |
| `sum 1/p` below `10^6` | 1.026174 vs **1.361154** | 0.956082 vs **1.597913** |
| logarithmic density of the lead, at `3×10^6` | **0.928** | **1.000** |
| first crossing | `x = 26861` | none below `10^6` |

The two density measures tell opposite-sounding stories and both are true. Under
natural density the classes agree to under half a percent — the account's
"symmetrisch" reading. Under *logarithmic* density, weighting each prime by
`1/p`, class `3 mod 4` leads with density 0.93 and class `1 mod 4` essentially
never leads. That is what "biased" means here, and it is not a small effect: the
reciprocal-sum gap is 0.335 out of a total mass of about 2.89, more than a tenth
of everything.

**The limiting Rubinstein–Sarnak value is about 0.9959 and is NOT claimed here.**
The measurement at `3×10^6` is 0.928 and climbing slowly. Convergence is far too
slow to reach the limit at any range this repository can compute, and the figure
plots the trend rather than the limit.

## 2. A constant this repository got wrong

The module first recorded the mod-4 crossing as `x = 2946`, written from memory.
That is wrong. Measurement gives **26861**, agreed by two independent primality
routes — the sieve in `prime_certificate` and its deterministic Miller–Rabin —
and at `x = 2946` the gap is `+7` *in favour of* `3 mod 4`, so it is not a
crossing of any kind. A regression test pins `Δ(2946) = 7`, so the wrong value
cannot quietly return.

Recorded because the wrong number was exactly the kind that would have looked
authoritative in a document.

## 3. Claim-by-claim verdicts

### Dirichlet characters and primes

| claim | verdict | basis |
|:---|:---|:---|
| `χ mod 3` is `1, -1, 0` periodically | **correct** | it is `chi_minus_3`, the character of the Eisenstein integers, already in `zeta_factors` |
| the Dirichlet sum equals the Euler product | **correct** | verified here: relative difference `2.3e-8` at `s=2`, `9.5e-13` at `s=3`, computed by two independent routes |
| `χ(3) = 0`, so the prime 3 drops out of the product entirely | **correct** | the local factor is exactly `1`; the "filtering" description is accurate |
| the `±1` pattern creates interference "like light waves" | **metaphor** | the cancellation is in the *sum*, not the product; harmless as an image, not a mechanism |
| if one class had more primes "the balance would collapse" and zeros would leave the critical line | **inverted** | the dependence runs the other way: zeros off the line *cause* the bias, and GRH bounds it. Also asserts a false equivalence between even counts and RH |
| the primes are "absolutely symmetric and fairly distributed" | **wrong** | Chebyshev's bias; section 1 |

### Miller–Rabin and GRH

| claim | verdict | basis |
|:---|:---|:---|
| "composite" is 100% certain | **correct** | a witness is a proof of compositeness |
| a single round errs with probability at most 1/4 | **correct** | Rabin; measured here, and the bound is *attained*, at `n = 9` where exactly `2` of `8` bases are liars |
| more random bases → error falls fast | **correct** | `4^-k`, with the standard caveat that the bases be independent and the composite not chosen after seeing them |
| under GRH, testing bases up to `2 (ln n)^2` suffices | **correct, misattributed** | Bach (1985) gives the explicit bound; Miller (1976) proved the polynomial-time determinism it makes explicit |
| for a 500-digit `n` that is "only a few thousand trials" | **wrong by ~1000×** | it is **2,650,950**; even at 100 digits it is 106,038 |
| with GRH the test becomes "perfect, infallible" | **overstated** | infallible *if GRH is true*, which is unproven; and unnecessary in practice, since bases `2..37` are proven sufficient below `3.317e24` unconditionally, which `prime_certificate` already uses |
| "the complex zeros guarantee that no malicious number constructs can trick our encryption" | **wrong direction** | nothing is guaranteed, because GRH is unproven. The implication runs conjecture → algorithm, not zeros → safety. And primality testing is not what protects RSA |

### Shor, surface codes, quantum hardware

| claim | verdict | basis |
|:---|:---|:---|
| Shor (1994) reduces factoring to period finding via the QFT | **correct** | standard |
| "a few thousand stable logical qubits" break RSA/DH/ECC | **directionally right, physical cost understated** | thousands of *logical* qubits is the right order; the physical requirement is in the millions |
| surface-code threshold around 0.7–1% | **correct** | standard circuit-level estimates |
| Google's Willow showed a logical error rate "exactly halved" from `3×3` to `7×7` | **imprecise** | the paper reports distances `d = 5` and `d = 7`, with suppression `Λ = 2.14 ± 0.02` — slightly better than halving, and not the stated sizes ([arXiv:2408.13687](https://arxiv.org/abs/2408.13687), Nature 638 (2025) 920–926) |
| "1,000 to 1,700 physical qubits per logical qubit" | **rule of thumb, not a constant** | depends strongly on code distance and decoder |
| "experts estimate a few years to a decade" | **opinion** | unfalsifiable here; recorded as a forecast, not a fact |

### Lattices and ML-KEM

| claim | verdict | basis |
|:---|:---|:---|
| SVP and CVP as stated | **correct** | standard definitions |
| the same lattice has a good basis and a bad basis, related by an integer change of coordinates | **correct** | verified here *exactly*, in dimension 2 |
| "Shor has no lever because there is no periodic wave" | **conclusion defensible, reasoning unsound** | no efficient quantum algorithm for SVP is known, but "no periodic wave" is not why; quantum sieving does give speedups |
| NIST standardised ML-KEM and ML-DSA | **correct** | FIPS 203 and FIPS 204 |
| post-quantum crypto is "no longer based on primes but on lattices" | **overstated** | not all of it is lattice-based: SLH-DSA (FIPS 205) is hash-based |
| ML-KEM-512/768/1024 correspond to AES-128/192/256 | **correct** | NIST's own categorisation |
| ML-KEM-768 public key about 1.2 kB | **correct** | 1184 bytes |

## 4. What was simulated, and what was not

### Simulated, with tests and a figure

| panel | what it shows | module |
|:---|:---|:---|
| prime race mod 4 | the crossing at 26861, and that 2946 is not one | `prime_races.py` |
| logarithmic density | Chebyshev's bias, and its slow convergence | `prime_races.py` |
| Miller–Rabin liar fraction | the `1/4` bound, attained at `n = 9` | `miller_rabin.py` |
| good vs bad basis | one 2D lattice, two bases, verified identical | `lattice_reduction.py` |

The lattice panel is deliberately dimension 2 and says so in its title. In
dimension 2, Gauss reduction solves SVP exactly in polynomial time, so nothing
about hardness is being shown — the panel shows the *structural* asymmetry, which
is real, and not the *computational* one, which is not observable here.

### Not simulated, and why

| topic | why not |
|:---|:---|
| Shor's algorithm | requires a quantum computer. Classically simulating period finding for small `N` would be a demo of classical arithmetic wearing a quantum label |
| surface codes and thresholds | a faithful simulation is a substantial project in its own right; a toy repetition code would have a threshold too, but quoting its number as "the surface-code threshold" would be a substitution of one object for another |
| quantum hardware state of the art | a literature claim, checkable only by reading. Done above, for the one numeric claim that was specific enough to check |
| ML-KEM security, and lattice hardness in high dimension | a research-level conjecture. No computation of any size available here bears on it |

## 5. What this has to do with the rest of the repository

Little, and that is worth stating rather than manufacturing a connection. The
number-theoretic half touches two things already here: the characters are the
same `χ₋₃` and `χ₋₄` that `zeta_factors.py` uses for the Gaussian and Eisenstein
Dedekind zetas, and the deterministic primality testing is the same
`is_prime_deterministic` that certifies the millionth prime.

The connection to the Riemann hypothesis is the one the account gestures at and
gets backwards: zeros off the critical line control the bias in the prime race,
so GRH bounds it. That makes the race a *consequence* of the zeros, not a
mechanism for proving anything about them — and `L(s,χ)` having no off-line
zeros is a conjecture, not a guarantee.

Nothing in this document is evidence for or against RH, and nothing in it is a
statement about the security of any deployed system.

## 6. Files

| file | role |
|:---|:---|
| `python/riemann_framework/prime_races.py` | residue-class counts, the race, logarithmic density, the Euler product check |
| `python/riemann_framework/miller_rabin.py` | the strong test, the liar bound, Carmichael numbers, the GRH base count |
| `python/riemann_framework/lattice_reduction.py` | 2D Gauss reduction, SVP/CVP, good vs bad basis |
| `python/tests/test_prime_races.py` | 18 tests, including the `2946` regression |
| `python/tests/test_miller_rabin.py` | 14 tests, including the Carmichael list and the base-count correction |
| `python/tests/test_lattice_reduction.py` | 17 tests, including Babai against exhaustive search |
| `scripts/run_number_theory_claims_demo.py` | the four-panel figure |

## References

- Rubinstein, M. and Sarnak, P. (1994). *Chebyshev's bias*. Experimental Mathematics 3(3), 173–197.
- Bach, E. (1985). *Analytic Methods in the Analysis and Design of Number-Theoretic Algorithms*. MIT Press.
- Miller, G. L. (1976). *Riemann's hypothesis and tests for primality*. J. Computer and System Sciences 13, 300–317.
- Sorenson, J. and Webster, J. (2015). *Strong pseudoprimes to twelve prime bases*.
- Acharya, R. et al. (2024). *Quantum error correction below the surface code threshold*. arXiv:2408.13687; Nature 638 (2025) 920–926.
- Shor, P. W. (1994). *Algorithms for quantum computation: discrete logarithms and factoring*. FOCS.
- NIST FIPS 203 (2024). *Module-Lattice-Based Key-Encapsulation Mechanism Standard*.

## Disclaimer

Nothing here proves or disproves the Riemann hypothesis. The verdicts on the
submitted account are about that text, not about the underlying mathematics,
which in the correct places is standard and well established.
