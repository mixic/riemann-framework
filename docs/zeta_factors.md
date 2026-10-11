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

# The Zeta-Containment Screen

## Abstract

The companion to [`docs/dh_filter.md`](dh_filter.md), asking a different
question. `dh_filter` asks whether a candidate's *inputs* survive the change from
`ζ` to a function whose RH-analogue is false. This screen asks whether a proposed
framework's zeta function has **`ζ` as a factor** — because if it does, proving
the framework's RH-analogue implies RH but proves strictly more, so the target is
strictly bigger than the problem it was meant to simplify.

It grew out of three proposals in a row that all landed in the same family: "work
over ℝ instead of ℂ", "use the Gaussian integers", "use Dirichlet L-functions".
The first was killed by the affine gate. The second and third are killed here, and
they are killed by the *same* fact.

## 1. The verdicts

| verdict | meaning |
|:---|:---|
| `is_the_base_case` | `Z = ζ`. The control: `ζ` is trivially a factor of itself, so this needs its own verdict rather than being called "harder than itself". |
| `strictly_harder` | `Z = ζ · W`. A proof of RH-for-`Z` **implies** RH — so this is a *valid* target, but a dominated one. Any such proof contains a proof of RH as a special case. |
| `separate_target` | No declared factor carries `ζ`. A proof of RH-for-`Z` does **not** imply RH, so the framework delivers nothing without a separate **transfer step** — and that step is the whole content of the proposal. |
| `no_euler_product` | No Euler product, so there are no local factors to divide and containment is not well-posed. The Davenport–Heilbronn / Epstein family. |

Neither `strictly_harder` nor `separate_target` is an endorsement. The first is
dominated; the second is incomplete. What the screen does is force the transfer
step into the open, which is the step ideas in this family almost always leave
implicit.

## 2. The two things it actually verifies

The screen would be bookkeeping if it merely read a declaration. So a declared
product is checked against the framework's **own Dirichlet series** over the
first 2000 coefficients:

```
ζ_ℚ(i)        = ζ(s) · L(s, χ₋₄)      checked against  r2(n)/4
ζ_ℚ(√−3)      = ζ(s) · L(s, χ₋₃)      checked against  r3(n)/6
```

where `r2(n)` counts `a² + b² = n` and `r3(n)` counts `x² + xy + y² = n`. Both
identities are classical; both are verified here rather than quoted, and both
hold for **every `n ≤ 2000`**.

That matters because the arithmetic is not obvious. The right-hand side is the
Dirichlet convolution of `ζ`'s coefficients — all ones — with the character, and
the identity is exactly the splitting law restated:

| rational prime | Gaussian | Eisenstein | effect on the local factor |
|:---|:---|:---|:---|
| splits (`p ≡ 1`) | `p ≡ 1 (4)` | `p ≡ 1 (3)` | `(1−p^{−s})^{−2}` |
| inert (`p ≡ 2`) | `p ≡ 3 (4)` | `p ≡ 2 (3)` | `(1−p^{−2s})^{−1}` |
| ramifies (`p = 0`) | `p = 2` | `p = 3` | `(1−p^{−s})^{−1}` |

**Not verified, and said so.** The general theorem `ζ_K = Π L(s,χ)` was not read
from a source during this work, so it is not cited as if it had been; what is
claimed is the two instances, which are computed. `epstein_rectangular` is the
opposite case — its lack of an Euler product is **cited** (Potter–Titchmarsh
1935; [McPhedran, arXiv:1601.01724](https://arxiv.org/abs/1601.01724)), not
checked, and the module reports it as `UNVERIFIED` rather than as passing. The
`unverified_factorizations` list exists so a containment verdict resting on a
citation cannot masquerade as one resting on a computation.

## 3. What the screen says about the Gaussian integers

```
!! strictly harder   dedekind_gaussian (zeta * dirichlet_L_chi4)
!! strictly harder   dedekind_eisenstein (zeta * dirichlet_L_chi3)
-- separate target   dirichlet_L_chi4_alone
?? no Euler product  davenport_heilbronn
?? no Euler product  epstein_rectangular
```

The interesting pair is the first and third rows. `ζ_ℚ(i)` **contains** `ζ`, so
the Gaussian-integer route is strictly harder than RH. But `L(s,χ₋₄)` = `β(s)`
**alone** does not contain `ζ`, so proving RH for `β` also delivers nothing — it
is a separate target needing a transfer step. The Gaussian integers give you one
or the other depending on which object you pick, and neither is a shortcut.

And note the trap recorded in `epstein_rectangular`'s row: the **square** lattice
is the Gaussian row above, because `r2` is multiplicative. Move to a
**rectangular** lattice and the sum stops factoring and acquires zeros off the
critical line. "Use the Gaussian integers" sits on the boundary between "a
product containing `ζ`" and "a known counterexample".

## 4. Two bugs the checks caught, which are the reason to have them

**The Eisenstein enumeration bound.** `x² + xy + y² ≥ (x²+y²)/2` because of the
cross term, so `|x|` can reach `√(2n)` — not `√n`. Enumerating `x, y` only to
`√(n_max)` misses genuine representations, and the identity then fails. It failed
at exactly `n = 3781`, and the module's first draft had this bug. There is now a
regression test that reaches past `DEFAULT_N_MAX` specifically to cover it.

**The Davenport–Heilbronn witness is not every pair.** `b` is periodic mod 5 with
values `(1, κ, −κ, −1, 0)`, so `b(2)·b(3) = −κ² ≈ −0.0807 ≠ 1 = b(6)` — the
witness `dh_filter` uses. But `b(2)·b(4) = −κ = b(8)` **holds**, by accident of
the period: `2·4 = 8` lands on residue 3, exactly where `2·4` lands. A first
draft of the test asserted that every pair in `2..5` refutes multiplicativity,
and `(2,4)` refuted the test. The witness is now named explicitly, and the
accident is pinned alongside it.

Both are the same species as the rest of this repository's recorded mistakes: a
statement that looked fine as a sentence and was wrong as a computation.

## 5. How this relates to `dh_filter`

They are complementary and neither subsumes the other.

| | question | output |
|:---|:---|:---|
| `dh_filter` | does the argument use an input Davenport–Heilbronn lacks? | `dead` / `eligible` / `needs_sourcing` |
| `zeta_factors` | is the framework's zeta a superset of `ζ`? | `strictly_harder` / `separate_target` / `no_euler_product` |

A framework can pass one and fail the other. `dedekind_gaussian` is `eligible`
for `dh_filter` — it uses the Euler product, which DH lacks — and
`strictly_harder` here. Both are true, and together they say: the arithmetic
content is real, and the target is nonetheless bigger than RH.

## 6. What this screen cannot do

It classifies **declared** frameworks, exactly as `dh_filter` classifies declared
inputs. A framework whose zeta function is not written as a product of the named
factors is not screened by it, and no numerical test here could decide
containment for a general object — deciding whether the zeros of `ζ` sit inside
another function's zero set is not a finite computation.

It also does not find routes. Nothing in this module is evidence for or against
the Riemann hypothesis, and the screen has no verdict meaning "promising".

## 7. Files

| file | role |
|:---|:---|
| `python/riemann_framework/zeta_factors.py` | the factors, the convolution, the verification, and the screen |
| `python/tests/test_zeta_factors.py` | 37 tests: the two identities, the bound regression, verification-that-can-fail, the verdicts |
| `scripts/run_zeta_factors.py` | prints the factors, what was verified, and the summary |

## References

- Potter, H. S. A. and Titchmarsh, E. C. (1935). *The zeros of Epstein's zeta-functions*. Proc. London Math. Soc.
- McPhedran, R. C. (2016). *Zeros of Lattice Sums: 1. Zeros off the Critical Line*. arXiv:1601.01724.
- LeClair, A. and Mussardo, G. (2024). *Riemann zeros as quantized energies of scattering with impurities*. JHEP 04 (2024) 062; arXiv:2307.01254v2.
- Alpöge, L. and Furman, R. (2026). *More than two thirds of the zeros of the Riemann zeta function are simple and on the critical line*. arXiv:2608.13637, §1.4.

## Disclaimer

Nothing here proves or disproves the Riemann hypothesis. A `strictly_harder`
verdict says a framework is a dominated target; a `separate_target` verdict says
it is an incomplete one. Neither says anything about whether the framework's own
conjecture is true.
