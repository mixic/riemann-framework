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

# The Riemann Hypothesis for Curves over Finite Fields

## Abstract

This is the one case in the whole project where the Riemann hypothesis is a
**theorem**, and — more usefully — the one case where a computation is a
**proof**.

For a smooth projective curve `C` over `F_q` with `N_m = #C(F_{q^m})`,

```
Z(C, T) = exp( Σ_{m≥1} N_m T^m / m ) = P(T) / ((1 − T)(1 − qT)),
P(T) = Π_{i=1}^{2g} (1 − α_i T)  ∈ Z[T],
```

and the Riemann hypothesis for `C` is

```
|α_i| = q^{1/2}   for every i.
```

`P(T)` is computed exactly by counting points, and its coefficients are
**integers**. So for a *specific* curve the hypothesis is a finite statement,
decidable by exact integer arithmetic, and the answer is a proof for that curve —
not evidence, not a search, not a statistical agreement.

    python scripts/run_finite_field_curves_demo.py   # output/finite_field_curves.png

**What is proved here, and what is not.** Every certificate below is exact and is
a proof for its curve. None of them proves Weil's theorem, which is universal over
all curves and all `q`. And the theorem does not transfer to the number-field
case: the function-field proof runs through the Frobenius action on étale
cohomology, and no analogue of that action is known over `Q`. The one case where
RH is a theorem is the case whose proof has no known counterpart for `ζ`.

## 1. Why a computation can be a proof here

This is the `prime_certificate.py` situation again, and the same doctrine from
`docs/verification.md`: **finite claims are where computation is the gold
standard.** The operative question is never evidence-versus-proof; it is whether
the claim is finite.

For **genus 1** the reduction is immediate. `P(T) = 1 − a T + qT²` with
`a = q + 1 − N_1`, and `|α| = |β| = √q` holds exactly when

```
a² <= 4q,
```

an inequality between integers. That is Hasse's theorem (1934), and the check is a
single exact comparison.

For **genus 2** it takes one step more. The functional equation makes `P`
palindromic, so `P(T)/T^g` is a polynomial in `w = T + q/T`:

```
S(w) = w² − a₁ w + (a₂ − 2q)   ∈ Z[w],
```

and RH is exactly "both roots of `S` are real and lie in `[−2√q, 2√q]`". Writing
the roots as `(a₁ ± √d)/2` with `d = a₁² − 4(a₂ − 2q)`, that condition is

```
d >= 0   and   16q − a₁² − d >= 0   and   4 a₁² d <= (16q − a₁² − d)²,
```

again entirely in integers. **No irrational quantity is ever evaluated.**

## 2. What was measured

| what | how many | violations |
|:---|:---|:---|
| elliptic curves over `F_p`, `p = 5, 7, 11, 13, 17, 19` | 942 | **0** |
| smooth genus-2 curves over `F_3` | 324 | **0** |
| smooth genus-2 curves over `F_5` | 10 000 | **0** |

All 11 266 certificates are exact. The counts also check the *structure*, not just
the bound: `N_m = q^m + 1 − Σ α_i^m` reproduces brute-force counts at `m = 1, 2, 3`
for `y² = x³ + 1` over `F_13` — `12, 192, 2268` — which says the point counts
really are governed by the `2g` numbers `α_i`.

**The Hasse bound is attained, from both signs.** For `y² = x³ + 1` over `F_5` the
deviation `N_m − q^m − 1` is `+10` at `m = 2` against a bound of exactly `10`, and
`−50` at `m = 4` against `50`. A bound never attained is not known to be sharp, so
both are pinned — and checking magnitudes alone would have hidden that they come
from opposite directions.

## 3. A false alarm, and what it was

Sweeping **all** 729 coefficient tuples `y² = f(x)` over `F_3` reported **30
uncertified curves**. Since RH for curves is a theorem, 30 failures would be a
counterexample to a theorem — so the first assumption had to be that the
hypotheses were not being met, not that the theorem was wrong.

They were not. All 30 have either `deg f = 4` (genus 1 with *two* points at
infinity, so the `+1` in the point count is wrong) or a repeated root (a singular
curve, and Weil's theorem is about *smooth projective* curves). Among the 324
genuine smooth genus-2 curves over `F_3`, the count is **zero**.

`is_smooth_genus2` is what separates them, and no certificate is issued without
it. This is worth recording as a general lesson: a screen that reports violations
of a theorem is reporting a bug in the screen's hypotheses first and a
mathematical discovery a very distant second.

## 4. A bug that was caught immediately

The irreducibility test that finds the modulus for `GF(p^n)` was inverted during a
"tidying" pass: `all(not any(remainder))` asks for every remainder to be *zero*,
i.e. for the candidate to be divisible by every divisor of degree `≤ n/2`, which
rejects every irreducible polynomial. `GF(3²)` failing to construct is what
exposed it.

The tests now verify irreducibility **independently**, by the field axiom
`a^(q−1) = 1` for every `a ≠ 0` — which fails in a ring with zero divisors, and
would have caught the inversion at once.

## 5. The graphical representation

Four panels, in `output/finite_field_curves.png`:

1. **The finite-field sphere.** `P¹(F_9)` — the 9 field elements plus the point at
   infinity — drawn on a circle, with chords joining each `x` to its Frobenius
   image `x³` and colours marking the `F_3`-conjugacy classes. Three elements are
   fixed (they are `F_3` itself) and the other six form three orbits of size two.
2. **The rational points of `y² = x³ + 1` over `F_5`**, with the `x ↦ −x` pairing
   drawn: 5 affine points, plus the point at infinity, gives `N_1 = 6` and
   `a_p = 0`.
3. **Hasse's bound, measured.** Every trace `a_p` for every curve over
   `p = 5, 7, 11, 13`, with the `±2√p` envelope. All inside.
4. **The zeros of `Z(C,T)`.** The `α_i/√q`, which lie on the unit circle — that
   *is* the statement `|α_i| = √q`. Two for the elliptic curve over `F_5`, four
   for a genus-2 curve over `F_3`.

## 6. Files

| file | role |
|:---|:---|
| `python/riemann_framework/finite_field_curves.py` | `GF(p^n)`, point counting, and the exact certificates |
| `python/tests/test_finite_field_curves.py` | 30 tests, including the field axioms and the smoothness hypotheses |
| `scripts/run_finite_field_curves_demo.py` | the four-panel figure |

## References

- Weil, A. (1949). *Numbers of solutions of equations in finite fields*. Bull. AMS 55, 497–508.
- Hasse, H. (1934). *Abstrakte Begründung der komplexen Multiplikation und Riemannsche Vermutung in Funktionenkörpern*.
- Deligne, P. (1974). *La conjecture de Weil I*. Publ. Math. IHÉS 43, 273–307.
- Artin, E. (1924). *Quadratische Körper im Gebiete der höheren Kongruenzen*.
- `Weil conjectures`, Wikipedia — the statement of rationality, the functional equation and `|α_ij| = q^{i/2}` used above.

## Disclaimer

Nothing here proves or disproves the Riemann hypothesis **over `Q`**. The
certificates are exact proofs for individual curves; the universal theorem is
proved elsewhere by Weil and Deligne, and is not verified by any computation here.
The absence of a Frobenius action over `Q` is the reason the function-field
success does not transfer, and it is stated with every certificate.
