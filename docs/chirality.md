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

# Chirality and topology: mirror-closure is not achirality

## Abstract

The Dimension-Shift Hypothesis rests on a puzzle: a set can contain both a piece
and its mirror image, be closed under mirroring, and still be **chiral**, because
no piece is its own mirror. Under `sigma s = 1 - conj s` the mirror of a zero is
another zero at the same height (`sigma_partner_same_height` in
`ZetaBridge.lean`), so `sigma`-invariance of the zero set is a *theorem* and RH is
the strictly stronger statement that every zero is its own mirror.

This page verifies the four standard instances of the pattern, and one
counter-example, with numbers. **It produces no evidence about the Riemann
hypothesis**; every claim is a finite verification of a known theorem or a
measured structural failure. Run it with:

    python -m pytest tests/test_chirality.py -q

## The dictionary

| puzzle concept | mathematical structure | repository correspondence |
|:---|:---|:---|
| mirror | `sigma(s) = 1 - conj(s)` | `sigma` in `InvolutionEigenspace.lean` / `ZetaBridge.lean` |
| self-mirror piece | zero with `sigma rho = rho` | zero on the critical line |
| `L`/`J` pair | zero with `sigma rho != rho` | "`sigma`-twin" off the line |
| mirror-closed collection | zero set is `sigma`-invariant | `riemannZeta_zero_quadruple` (a theorem) |
| chiral puzzle piece | off-line zero | would form a 4-orbit `{rho, 1-rho, conj rho, 1-conj rho}` |

The key insight, as stated: **mirror-closure is necessary but not sufficient for
achirality.** The Riemann hypothesis is the statement that no piece is chiral.

## 1. Gaussian primes: splitting is the existence of a mirror pair

In `Z[i]` a rational prime behaves in exactly three ways, and they are the three
ways a piece can behave under a mirror:

| `p` | class | mirror structure |
|:---|:---|:---|
| `2` | ramified | `2 = -i(1+i)^2`: self-mirror up to a unit |
| `p = 1 mod 4` | split | `p = (a+bi)(a-bi)`: a genuine mirror pair |
| `p = 3 mod 4` | inert | stays prime: no mirror image inside `Z[i]` |

Measured by integer search below 400: **37 split, 40 inert, 1 ramified**. Two
checks make this more than a count: every split prime has a representation
`a^2 + b^2 = p` (found by search, so the mirrored pair exists), and **no** inert
prime has one. The search is what fails for the inert primes, not an assertion.

## 2. Lens spaces: the same condition in topology

`L(p, q)` is *achiral* (admits an orientation-reversing self-homeomorphism) iff
there is a `q` with `q^2 = -1 (mod p)`, i.e. iff `-1` is a quadratic residue mod
`p`, i.e. iff `p = 2` or `p = 1 mod 4`. That is the Gaussian splitting condition
again, in a different category.

Measured for every prime below 200: **22 achiral, 24 chiral**, and the split /
inert classification agrees with the existence of the involutive element in
**all** cases. Topological chirality and arithmetic splitting are the same
statement here, which is why the `sigma` analogy is more than decorative.

## 3. `chi_-4` is odd, and the archimedean factor knows it

`chi_-4` is the non-principal character mod 4: `1, 0, -1, 0, ...` with
`chi(-1) = -1`. Oddness is visible in the functional equation, because the
archimedean factor is `Gamma((s+a)/2)` with `a = 1` for an odd character and
`a = 0` for an even one.

Measured, by fitting both:

| archimedean factor | `|Lambda(s) - Lambda(1-s)|` |
|:---|---:|
| `Gamma((s+1)/2)`, `a = 1` | `2.1e-16` |
| `Gamma(s/2)`, `a = 0` | `9.1e-01` |

A ratio of `4.3e15`. Two independent normalisation checks confirm the function
being tested: `beta(1) = pi/4` and `beta(0) = 1/2`.

## 4. Cayley–Dickson conjugation is an anti-automorphism

`conj(xy) = conj(y) conj(x)` in dimensions 2, 4, 8 and 16 — the structure that
survives the loss of commutativity (dimension 4) and associativity (dimension 8),
measured at `0.0` error in every dimension (`cayley_dickson.py`).

The control matters: commutativity itself **fails** from dimension 4 on, so the
anti-automorphism test is not the trivial statement that multiplication is
commutative. In dimension 16 the algebra has zero divisors and the
anti-automorphism still holds exactly.

## 5. Davenport–Heilbronn: the functional equation without an Euler product

`dh_filter.py` provides the Davenport–Heilbronn function, which satisfies the same
type of functional equation as `zeta` but has no Euler product. Measured:

| claim | measured |
|:---|:---|
| functional equation holds | residual `2.3e-17` |
| Euler product fails | `b(2)b(3) - b(6) = 1.0807`, and `b(2)b(3) = -kappa^2` to `1e-12` |
| zeros located (bounded scan) | 7 zeros, all on `Re = 1/2` except the trivial one at `s = -1` |

**The honest limitation.** The literature holds that the Davenport–Heilbronn
function has zeros off the critical line; this module's bounded search up to
`t = 40` locates **none**, and the report says so rather than importing the claim.
What is demonstrated is the structural point: a functional equation of Riemann
type does not imply an Euler product, and the Euler product is what the usual
argument for the critical line uses. The counter-example is a warning about what
the functional equation cannot give, not a located off-line zero.

## 6. What this does and does not show

**Does:** each of the five claims above, with the numbers quoted, reproducible from
the tests.

**Does not:** produce any new evidence about the Riemann hypothesis. There is no
new evidence about the Riemann hypothesis here. This is a re-description of the
wall that `ZetaBridge.lean` already proves: mirror-closure of the zero set is a
theorem, and achirality — no zero with a distinct `sigma`-partner — is the
hypothesis.

## Files

| File | Contents |
|:---|:---|
| `riemann_framework/chirality.py` | the five checks and the `ChiralityReport` |
| `tests/test_chirality.py` | 22 tests, including the parity and non-vacuity controls |
| `docs/pt_symmetric_hilbert_polya.md` | the physics dictionary the `sigma`-pair maps onto |
| `lean/RiemannFramework/ZetaBridge.lean` | `sigma`, the same-height lemma, the two-cycle equivalence |
