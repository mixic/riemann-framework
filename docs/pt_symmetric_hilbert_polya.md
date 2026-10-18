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

# The PT-symmetric Hilbert–Pólya dictionary

## Abstract

This page states the correspondence between the involution `sigma` in
`lean/RiemannFramework/ZetaBridge.lean` and the energy levels of a non-Hermitian
(`PT`-symmetric) Hamiltonian, and it states the limits of that correspondence
first, because the correspondence is where statements about the Riemann
hypothesis tend to be smuggled in.

**No new evidence about the Riemann hypothesis is produced by this dictionary.**
The Lean file already proves that `sigma`-invariance of the zero set is a theorem
and that the hypothesis is the statement that no zero has a *distinct*
`sigma`-partner. Translating that into "energy levels" changes the vocabulary, not
the mathematical content.

## 1. The correspondence

Centre the spectral parameter at `1/2`: write a zero as `rho = 1/2 + E`. Then
`sigma rho = 1 - conj rho` acts on the centred parameter as

```
E  |->  -conj(E)
```

and the dictionary is:

| in `ZetaBridge.lean` | statement | as an energy level |
|:---|:---|:---|
| `sigma rho = rho` | the zero lies on `Re = 1/2` | `E` is purely imaginary, `E = -conj E` |
| `sigma rho != rho` | the zero has a distinct mirror partner | `E != -conj E`: two distinct levels `E` and `-conj E` |
| `riemannZeta_zero_quadruple` | `{rho, 1-rho, conj rho, 1-conj rho}` are all zeros | the orbit `{E, -E, conj E, -conj E}` |
| `riemannHypothesis_iff_no_two_cycle` | no nontrivial zero has `sigma rho != rho` | no level fails `E = -conj E` |

`sigma_partner_same_height` is the load-bearing lemma and worth quoting:
`(sigma s).im = s.im` and `(sigma s).re + s.re = 1`. The `sigma`-partner of a zero
sits at the **same height**, with the real part reflected about `1/2`.

## 2. Two corrections to the popular form of this table

The table above is the version this module can defend. Two statements that appear
in circulating versions of it are wrong, and the second is wrong in a way that
would overstate the result:

**"A two-cycle gives `E` and `conj E` as levels."** The `sigma`-partner is
`-conj E`, not `conj E`. Both are levels, but they arrive from different
symmetries: `conj E` is a level because complex conjugation is a symmetry of the
zero set (`riemannZeta_zero_conj`), and `-conj E` is a level because `sigma` is
(`riemannZeta_zero_sigma`). The orbit is the quadruple `{E, -E, conj E, -conj E}`;
the *two-cycle* is the pair `{E, -conj E}`.

**"RH says no level has a complex-conjugate partner."** It does not: every
non-real level has one, by the conjugation theorem, and the zeros of `zeta` are
expected to come in conjugate pairs whether or not RH holds. What the hypothesis
denies is a **reflection** partner at the same height: a level `E` with
`E != -conj E`. Read as "no conjugate partner" the statement would be about
real energy levels, which is a different (and false) claim.

## 3. Why `PT` symmetry enters, and what it does not give

For a non-Hermitian Hamiltonian, a real spectrum is a *condition*, not a
consequence of the construction. `hilbert_polya.py` §2.3 makes that concrete with a
two-by-two `PT`-symmetric model whose spectrum is real below
`theta_c = arcsin(s/r)` (`pi/6` at `s/r = 1/2`) and a complex-conjugate pair above
it, with `|Im lambda|` matching the closed form. Nothing there is Riemann-specific;
the point is structural. A `PT`-symmetric candidate for the zeros therefore owes a
proof that it sits in the unbroken phase, and that proof is where the work would
be.

The proposal this dictionary is usually attached to is Bender, Brody and Müller,
*Hamiltonian for the zeros of the Riemann zeta function*, PRL 118, 130201 (2017),
[arXiv:1608.03679](https://ar5iv.labs.arxiv.org/html/1608.03679). It is a
proposal: the reality of its spectrum rests on boundary conditions that later
work disputes — see [arXiv:1704.02644](https://ar5iv.labs.arxiv.org/html/1704.02644)
and the reply at [arXiv:1705.06767](https://ar5iv.labs.arxiv.org/html/1705.06767).
Its spectrum is also claimed, not proved, to be the zeros; by the spectral theorem
every self-adjoint operator with that spectrum is unitarily equivalent to
`diag(gamma)`, so the identification is the entire content (see
`docs/operator_candidates.md` §4).

## 4. What the corrected chaos model adds to this dictionary

The one thing this repository can contribute here is a measured statement about
what `sigma`-symmetry does to a spectrum. `dimension_shift_chaos.py` now enforces
`[H, sigma] = 0` exactly, with the consequence spelled out in its docstring:

```
[H, sigma] = 0   <=>   H = [[A, C], [C^dagger, A]]   <=>   spec(H) = spec(A + C) + spec(A - C)
```

So the `sigma`-sectors are the spectra of `A + C` and `A - C`, and the full
spectrum is their superposition. Measured at 300 seeds per point
(`output/falsification_summary.txt`):

| quantity | value |
|:---|:---|
| full spectrum, GUE blocks | `0.369 .. 0.429` |
| full spectrum, GOE blocks | `0.402 .. 0.428` |
| single sector, GUE blocks | `0.594 .. 0.609` |
| single sector, GOE blocks | `0.525 .. 0.540` |
| `||[H, sigma]||_F / ||H||_F` | `0.0` (was `1.346 .. 1.462`) |

Two readings follow, and neither is evidence for the hypothesis:

1. A `sigma`-symmetric spectrum is **never** GUE-like as a whole. Any test that
   averages over the full spectrum is asking about a superposition, not about the
   zeros.
2. The sector is GUE-like **if and only if the input blocks are**. The class is
   imported by the construction, so the construction cannot be evidence that the
   zeros have that class.

## 5. Status

The dictionary is a translation, not an argument. The Riemann hypothesis is open.
The verifiable content of the translation is that `sigma`-invariance of the zero
set is a theorem (`stripSigmaInvariant`) and that the hypothesis is exactly the
absence of a distinct `sigma`-partner (`riemannHypothesis_iff_no_two_cycle`) —
both machine-checked in `ZetaBridge.lean`, neither of them news.

## Files

| File | Contents |
|:---|:---|
| `lean/RiemannFramework/ZetaBridge.lean` | `sigma`, the same-height lemma, the quadruple, the two-cycle equivalence |
| `lean/RiemannFramework/InvolutionEigenspace.lean` | the `+1`/`-1` eigenspace lemmas |
| `python/riemann_framework/dimension_shift_chaos.py` | the `sigma`-enforced model and its sectors |
| `python/riemann_framework/chirality.py` | the arithmetic instances of "mirror-closure without achirality" |
