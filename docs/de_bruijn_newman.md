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

# The de Bruijn–Newman Constant

## Abstract

The request was to introduce `Λ` into the simulation and tests, and to check that
`Λ ≤ 0`. The first half is done. The second half **cannot be done**, and the
reason is not difficulty:

> **RH ⟺ Λ ≤ 0.**

`Λ ≤ 0` is not a quantity to be estimated; it is the Riemann hypothesis in a
different coordinate system. No computation establishes it, and this document and
the module are structured so that nothing in them can be mistaken for having
tried. The honest deliverable is the machinery, the validation, and a precise
statement of what it can and cannot see.

    python scripts/run_de_bruijn_newman_demo.py   # output/de_bruijn_newman.png

## 1. The definition, sourced rather than recalled

From Rodgers–Tao, [arXiv:1801.05914](https://ar5iv.labs.arxiv.org/html/1801.05914),
equations (1)–(4):

```
H_t(z) = ∫_0^∞ e^{t u²} Φ(u) cos(zu) du
Φ(u)   = Σ_{n≥1} (2π²n⁴e^{9u} − 3πn²e^{5u}) exp(−πn²e^{4u})
H_0(z) = (1/8) ξ(1/2 + iz/2)
∂_t H_t = −∂_zz H_t
```

**This module's first draft had three things wrong**, all from memory:

1. the exponents as `9u/2, 5u/2, 2u` instead of `9u, 5u, 4u`;
2. no `1/8`;
3. `ξ(1/2 + iz)` instead of `ξ(1/2 + iz/2)`.

The check that caught it was comparing `∫_0^∞ Φ(u)cos(zu)du` against
`H_0(z) = (1/8)ξ(1/2 + iz/2)` at several `z`. The recalled version was off by 0.5%
— small enough to look like a numerical artefact, and consistent enough across
`z` to look like a normalisation constant. Only a *sourced* target distinguishes
those two cases, which is why the sourcing rule exists.

The corrected definitions then check out to working precision:

| `z` | quadrature | `(1/8)ξ(1/2+iz/2)` | difference |
|:---|:---|:---|:---|
| 1 | 0.061782123488754 | 0.061782123488760 | −5.5e−15 |
| 3 | 0.058986617138142 | 0.058986617138148 | −5.6e−15 |
| 7 | 0.046687381950056 | 0.046687381950062 | −5.9e−15 |
| 14 | 0.019025565535755 | 0.019025565535761 | −6.6e−15 |
| 28 | 0.000025161805523 | 0.000025161805529 | −6.8e−15 |

Two routes with no shared code: one a quadrature over a precomputed table, the
other evaluating `ζ` and `Γ` directly.

## 2. What Λ is, and the window

| bound | value | source |
|:---|:---|:---|
| lower | `Λ ≥ 0` | Rodgers–Tao (2018) |
| upper | `Λ ≤ 0.2` | Polymath15 (2019) |
| sharper upper | `Λ ≤ 0.1875` | later certified bound, recorded but unused here |
| equivalence | `RH ⟺ Λ ≤ 0` | de Bruijn, Newman |

Together: **`RH ⟺ Λ = 0`**, and the question lives in the window `[0, 0.2]`.

Rodgers–Tao's lower bound says something worth stating plainly: **if RH is true,
it is only barely so.** `Λ = 0` means the zeros sit exactly at the edge of the
region where they are real, with no margin at all.

## 3. What is genuinely available: a refutation

The one direction that is finite and valid:

> if some `H_t` with `t > 0` has a non-real zero, then `Λ > 0` and RH is false.

Because `Λ ≤ 0.2`, all zeros of `H_t` are real for `t ≥ 0.2`, so the search window
is `t ∈ (0, 0.2]`. This is one of only **two** refutation-capable framings in this
repository's scope — the other being a negative eigenvalue of a finite compression
of Weil's form.

The converse is worth nothing. Verifying that the zeros of `H_t` are real for
`t ∈ [0, 0.2]` is exactly the published computation, and is consistent with
`Λ = 0.2`, under which RH is **false**.

## 4. Three limits, all measured

The module is written so that its limits are as visible as its successes. All
three are pinned by tests.

### 4.1 The zero scan is insensitive to what it is named for

Counting real zeros of `H_t` over the low range returns **the same count for every
`t` in `[−0.2, 0.2]`** — including negative `t`, where an exit would appear if
`Λ < 0`. The counts are `[9, 9, 9, 9, 9, 9, 9]`.

That flatness is **not** evidence for RH. If `Λ < 0`, the first exit of a zero from
the real axis happens at Lehmer-pair heights, far above any range scanned here.
The scan would return the same count whether `Λ = 0` or `Λ = 0.2`. It demonstrates
the mechanism; it cannot detect the quantity it is named for. The module reports
`INSENSITIVITY_NOTE` alongside every count, because a flat number on its own reads
as reassurance.

### 4.2 The quadrature degrades with height

The fixed Gauss–Legendre rule agrees with the exact `2γ_k` at low `k` and drifts:

| `k` | computed | exact `2γ_k` | relative error |
|:---|:---|:---|:---|
| 1 | 28.269450283 | 28.269450283 | 2.8e−12 |
| 3 | 50.021715077 | 50.021715160 | 1.7e−09 |
| 5 | 65.870097363 | 65.870123175 | 3.9e−07 |
| 7 | 81.828473961 | 81.837438024 | 1.1e−04 |
| 9 | 94.998199228 | 96.010301762 | 1.1e−02 |

Float64 cannot resolve `cos(zu)` at `z ≈ 100` on a fixed node set. The first zero,
at `2γ₁ = 28.269450283469` against a computed `28.269450283390`, validates Φ, the
`1/8`, the `iz/2` and the quadrature in one number. Beyond `k ≈ 6` the positions
should not be quoted.

### 4.3 The dynamics equation does not truncate

Rodgers–Tao's equation (5),

```
∂_t x_k(t) = 2 Σ_{j ≠ k} 1/(x_k(t) − x_j(t)),
```

sums over **all** zeros. Truncating to the computed ones gives a derivative that
disagrees with the numerically differentiated zero positions by a roughly constant
offset:

| `k` | numeric `dx_k/dt` | truncated `2Σ` |
|:---|:---|:---|
| 1 | −0.580 | −0.292 |
| 3 | −0.586 | −0.048 |
| 5 | −0.465 | +0.298 |
| 8 | −0.397 | +0.771 |

The numeric velocities are all near −0.6, which a truncated sum cannot produce;
that near-constancy is the signature of a missing tail. This is why the paper
needs spatial cutoffs and a renormalised energy, and it is why this module does
**not** integrate the flow. `DYNAMICS_NOTE` travels with the function.

## 5. The control, where an exit *is* observable

Since the scan cannot see an exit because none is in range, the machinery is run
on a family whose exit is in range and whose constant is known by hand:

```
p(z) = z² + c        exp(−t ∂²/∂z²) p = z² + c − 2t
zeros: ±√(2t − c)    real exactly when t ≥ c/2
```

So `Λ = c/2 > 0` exactly, and the crossing is at `t = c/2`. With `c = 1` the panel
shows the pair going from `±0.775i` at `t = 0.2`, colliding at `t = 0.5`, and
becoming real `±0.447` at `t = 0.6`. This is what the machinery *would* show if an
exit were in range. It is a control for the detector, not evidence about `ζ`.

## 6. Files

| file | role |
|:---|:---|
| `python/riemann_framework/de_bruijn_newman.py` | `Φ`, `H_t`, the reference route, zero location, the three limits, the control |
| `python/tests/test_de_bruijn_newman.py` | 18 tests: the identity, the zeros, and the three limits pinned |
| `scripts/run_de_bruijn_newman_demo.py` | the four-panel figure |
| `ideas/de_bruijn_newman_first_exit.json` | the pre-existing idea record for this framing |

## References

- Rodgers, B. and Tao, T. (2018). *The de Bruijn–Newman constant is non-negative*. arXiv:1801.05914. Forum of Mathematics, Pi.
- Polymath15 (2019). *Effective approximation of heat flow evolution of the Riemann ξ function, and a new upper bound for the de Bruijn–Newman constant*.
- de Bruijn, N. G. (1950). *The roots of trigonometric integrals*.
- Newman, C. M. (1976). *Fourier transforms with only real zeros*.
- Csordas, G., Smith, W. and Varga, R. S. (1994). *Lehmer pairs of zeros, the de Bruijn–Newman constant Λ, and the Riemann hypothesis*.

## Disclaimer

Nothing here proves or disproves the Riemann hypothesis. `Λ ≤ 0` is reported as an
*equivalence*, never as a computed result, and no function in this module returns
anything resembling a verdict on it. The flat zero-count scan is explicitly
labelled as insensitive rather than as supporting evidence.
