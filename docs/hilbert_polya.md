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

# The Hilbert–Pólya prototype

## Abstract

Hilbert and Pólya suggested that the nontrivial zeros of `ζ` are the eigenvalues
of a self-adjoint operator, so that the reality of eigenvalues forces
`Re(s) = 1/2`. Berry and Keating gave the most concrete candidate, the
dilation operator `H = xp`. This module builds that operator, computes with it,
and measures where the argument stops working.

**It does not prove the Riemann hypothesis. It does not get nearer to proving
it.** What it does is turn "the zeros are the eigenvalues of a self-adjoint
operator" into four statements that can each be checked, and each of which
currently fails.

One genuinely positive result comes out of it, and it is worth stating plainly:
the operator's formal eigenfunctions are `x^{-1/2 + iE}`, whose exponent is
`s - 1` at `s = 1/2 + iE`. **The critical line is not a parameter of this
construction; it is its fixed point.** That is the algebraic reason the operator
is the right starting point, and it is verified here rather than asserted.

    python scripts/run_hilbert_polya_demo.py   # output/hilbert_polya.png

## What was already here, and what is new

No part of the source material was re-implemented. The repository already had:

| Piece | Where | Status |
|:---|:---|:---|
| the primon gas, `Tr[e^{-sH}] = ζ(s)` exactly | `primon_gas.py` | exact anchor |
| real-time versus imaginary-time traces, the `β = 1` Hagedorn maximum | `imaginary_time.py` | measured |
| GUE spacing statistics of the zeros | `quantum_chaos.py` | measured |
| the Gutzwiller dictionary, periods `log p`, `h = 1` forced | `prime_orbits.py` | exact at first order |
| Berry–Keating `H = xp`, Connes, the trace-formula programmes | `docs/research_notes.md`, `docs/dimension_shift_quantum_chaos.md` | documented, **not** implemented as an operator |

What was absent, and is what this module adds: **an actual operator whose
spectrum can be computed and compared with the zeros**, the boundary condition
that a regularization requires, the logical status of "the spectrum is real", and
the thermodynamic question of what imaginary time can and cannot see.

## 1. The operator, and why the critical line appears

`H = -i(x d/dx + 1/2)` on `L²(0, ∞)` is the symmetric quantization of `xp`
(`xp` alone is not symmetric on `dx`; the `1/2` is the Jacobian). For
`ψ = x^a`,

```
H x^a = -i(a + 1/2) x^a        so        H ψ = E ψ  ⟺  a = -1/2 + iE.
```

With `s = 1/2 + iE`, `a = s - 1`: the eigenvalue relation forces the real part to
`-1/2` for every `E`. The real part is not varied anywhere in the construction.

`eigenfunction_exponent` and `algebraic_residual` verify this. The residual is
computed in exact complex arithmetic, and it is `0` to rounding; shifting the
real part by `δ` produces a residual of exactly `|δ|`, so the check can fail.

## 2. The four gaps, measured

### 2.1 There are no eigenvalues

`|x^{-1/2 + iE}|² = x^{-1}` for every real `E`, so

```
∫_a^b |ψ|² dx = log(b/a)
```

with no limit as `b → ∞` **and none as `a → 0`**. At width `10⁶` the truncated
norm is `13.816` and still growing. No formal eigenfunction is square-integrable,
so `H` has empty point spectrum and its spectrum is all of `ℝ`.

That is consistent with the zeros being real. It is equally consistent with every
other real number being an eigenvalue, which is the point: **the continuum cannot
select the zeros, it can only contain them.**

### 2.2 The box destroys the structure it was meant to reveal

Cutting off the infinity is not bookkeeping. Put `y = log x` and impose
periodicity of length `L`: `H` becomes `-i d/dy` on a circle, with eigenvalues
`2πn/L` — a **picket fence**.

Against the first 100 zeros (`γ₁ = 14.1347`, `γ₁₀₀ = 236.524`):

| | hard box | zeros |
|:---|:---|:---|
| `r`-ratio | `1.000` (exactly) | `0.610` |
| nearest-neighbour spacings | all `2.3652` | `0.716 … 6.887`, mean `2.246` |

A box fitted to hold 100 rungs by `T = 236.52` (`L = 2.6565`) gets the *density*
wrong too, and worst where the fit is not anchored:

| `T` | box levels | actual zeros | ratio |
|:---|---:|---:|---:|
| 50 | 21 | 10 | **2.10×** |
| 100 | 42 | 29 | 1.45× |
| 150 | 63 | 52 | 1.21× |
| 200 | 84 | 79 | 1.06× |

The box's counting function is linear, `N(T) = TL/2π`; the zeros grow like
`(T/2π)log(T/2πe)`. And the rungs are *equally spaced while the zeros are not*,
which no amount of fitting repairs: rescaling the ladder onto the zeros'
endpoints still misses by `14.40` on average, `6.4` mean spacings.

The literature does not use a hard box for exactly this reason. It uses an
action-dependent boundary condition — and specifying that boundary condition *is*
the conjecture, not a technical preliminary.

**Numerical aside, kept because it bit this module first.** The naive
central-difference discretization of `-i d/dy` has eigenvalues `sin(kh)/h`, not
`k`: at `L = 20`, `N = 64` the deviation reaches `6.85`, twice the spacing, and a
first pass "discovered" a non-uniform spectrum that was entirely grid dispersion.
The spectral discretization reproduces the ladder to `1e-14`, and both are kept so
the comparison is in the tests.

### 2.3 A real spectrum is free, so self-adjointness carries no arithmetic

Any prescribed list of reals is the spectrum of a self-adjoint operator: `diag` of
the list. Two consequences, and they are the crux of the whole programme:

1. "There exists a self-adjoint operator with a real spectrum" is a tautology.
2. A finite numerical match of eigenvalues to zeros is a tautology performed with
   `n` numbers. It is compatible with the `(n+1)`-th eigenvalue being anything.

What Hilbert–Pólya requires is an operator **defined without reference to the
zeros** whose spectrum is **provably** theirs, all of them. No such construction
exists. `eigenfunction_exponent` takes an energy and knows nothing about `ζ`;
a test asserts that, so the operator cannot quietly become a fit.

For the non-Hermitian route the gap is starker: there reality is a *condition*.
The two-by-two `PT`-symmetric model `M = [[re^{iθ}, s], [s, re^{-iθ}]]` has
eigenvalues `r cos θ ± √(s² − r² sin²θ)`, real below `θ_c = arcsin(s/r)` and a
conjugate pair above. At `s/r = 1/2`, `θ_c = π/6 = 0.5236` exactly — thirty
degrees — and at `θ = 0.55` the pair has `|Im λ| = 0.1523`, matching the closed
form. Breaking is a property of the parameter, not a numerical accident, and
establishing that the Riemann operator sits in the unbroken phase is open.

### 2.4 Imaginary time is blind to `Re(s)`

This is the sharpest result here, and it constrains the whole "Wick rotation"
framing.

A thermal functional of a spectrum consumes the energies: `Z(β) = Σ e^{-βE_n}`.
If the zeros are the energies, then `E_n = Im(s_n)` and **the real parts do not
enter anywhere**. Moving a zero from `1/2 + iγ` to `0.6 + iγ` changes `Z(β)` by
*exactly zero*, not approximately: the ordinates are the same numbers.

Measured at `β = 0.5` over the first 100 zeros: `Z = 8.837461×10⁻⁴` on the line,
`8.837461×10⁻⁴` with every zero shifted by `+0.1` — difference `0`.

So Wick rotation is a *consequence* of spectral theory, not a route into it. It
shows that a self-adjoint `H` implies decay and reality; it cannot show that the
zeros are real, because it never reads them. Any argument of the form "the
imaginary-time picture reveals the truth about the critical line" is reading a
quantity that is invariant under moving the zeros off the line.

## 3. What survives: the temperature statement

Imaginary time really is inverse temperature, and that part is a theorem, so it is
verified here rather than merely cited:

- **KMS symmetry.** `G(τ) = G(β − τ)` for the Euclidean correlator of a thermal
  state. Measured asymmetry `< 1.2×10⁻¹⁶` — a symbolic identity, not an
  approximate agreement.
- **The Matsubara circle.** Imaginary time has circumference `β`, and
  `G(τ) = cosh(ω(τ − β/2)) / (2ω sinh(βω/2))`. At `τ = 0` this is
  `coth(βω/2)/(2ω) = 0.446333`, confirmed independently by the explicit
  Boltzmann sum (`x_squared_thermal`), so the closed form was not fitted to
  itself.
- **Imaginary-time evolution isolates one level.** `e^{-Eτ}` weights give the
  ground state `99.8961%` of the weight at `τ = 1` and `99.9999%` at `τ = 2`, and
  the gap `γ₂ − γ₁ = 6.887315` is recovered exactly from `−(1/τ)log(w₁/w₀)`.
  That is QITE working — on a spectrum it is *given*.
- **Hawking.** `β = 8πGM/c³`, equal to `4πr_s/c`, and `T = ħ/(k_Bβ)`. For one
  solar mass, `T = 6.1687×10⁻⁸ K`, the textbook value, with
  `T·β·k_B/ħ = 1`.

None of this says anything about the critical line. It says imaginary time
behaves like temperature, which is why the metaphor is so attractive and so
misleading here.

## 4. Corrections to the source material

The framing that prompted this prototype contains four claims that the numbers do
not support. They are worth recording because each is plausible in isolation.

**"If a quantum system exists whose energy states match the zeros, RH would be
automatically proven."** Only with "all of them" attached to *match*, and that is
the entire open problem. Self-adjointness gives reality; it gives nothing about
which real numbers appear. See §2.3 — `diag` of any list is a counterexample to
the naive reading.

**"The continuous spectrum snaps into discrete energy spikes, and those spikes
map directly to the Riemann zeros."** A hard box snaps it into spikes that are
*equally spaced* — `r = 1.000` against `0.610`, and a linear counting function
against a logarithmic one. See §2.2. The literature's regularization is an
action-dependent boundary condition, not a box, precisely because the box fails.

**"In the hypothetical Riemann system, shifting into imaginary time reveals the
prime number counting function."** The primes do appear — in the explicit formula
`ψ(X) = X − Σ_ρ X^ρ/ρ − log 2π − ½log(1 − X⁻²)`, which is implemented in
`prime_orbits.py` and needs `N(X) ≈ 138,068` zeros at `X = 10⁵`. That identity is
not a Wick rotation of the zeros' operator, and no thermal trace of that operator
can see `Re(s)` at all (§2.4).

**Attribution.** The 2017 construction discussed is Bender, Brody and **Müller**,
*Hamiltonian for the zeros of the Riemann zeta function*, PRL 118, 130201
([arXiv:1608.03679](https://ar5iv.labs.arxiv.org/html/1608.03679)); the source
material's "Hugh Jones" could not be confirmed. The pair-correlation story is
also usually told the other way round from the source: Montgomery computed the
form `1 − (sin πx/πx)²` and Dyson recognised it as GUE at tea in 1972. And the
2017 proposal is a proposal: its claimed spectrum rests on boundary conditions
that later work has disputed — see
[arXiv:1704.02644](https://ar5iv.labs.arxiv.org/html/1704.02644) and the reply at
[arXiv:1705.06767](https://ar5iv.labs.arxiv.org/html/1705.06767).

The Hartle–Hawking no-boundary proposal is a genuine use of periodic imaginary
time. It has no bearing on the zeta function, and nothing here uses it.

## 5. What would count as progress

A candidate must now pass four screens, all of them computable:

1. Is the operator defined **without** reference to the zeros?
2. Does its regularization leave the spectrum non-uniform, with spacings that
   vary at the GUE rate rather than in a ladder?
3. Is the reality of the spectrum **proved**, not observed — and if the operator
   is non-Hermitian, is it in the unbroken phase, with the threshold identified?
4. Is the identification `spectrum = zeros` a theorem for infinitely many levels,
   rather than a match of the first `n`?

No known construction clears all four. The prototype's value is that a new
candidate can be screened against them in seconds instead of being admired.

## Reproduce

```bash
python scripts/run_hilbert_polya_demo.py      # output/hilbert_polya.png
cd python && python -m pytest tests/test_hilbert_polya.py -q
```

`h = 1` in the operator (energies are ordinates directly); SI constants are used
only for the Hawking check. The linear-algebra panels are `numpy`; the zeros come
from `prime_orbits.zeta_zero_ordinates`, cached.

**Typing note, because it cost seven errors.** On arrays write `np.real(a)` and
`np.imag(a)`, never the property forms `a.real` / `a.imag`. Under numpy 2.5's
stubs the properties fail with `No overloads for "__get__" match the provided
arguments`, while the function forms are clean — and so are scalar attributes
such as `z.imag` on a `np.complex128` element, which is why the same expression
is an error on the array and fine on `a[0]`. The committed `pyrightconfig.json`
cannot resolve `numpy`, so `npx pyright` in this repository reports 100+ import
errors and *none* of these attribute errors; they appear only in an editor with an
interpreter configured. To reproduce that view, point a throwaway config at
site-packages (`{"extraPaths": ["./python", "<site-packages>"], "stubPath":
"./typings"}`). With `numpy` resolved the whole tree is clean: 0 errors.

## Files

| File | Contents |
|:---|:---|
| `riemann_framework/hilbert_polya.py` | the operator, the box, the `PT` model, the thermal functionals |
| `tests/test_hilbert_polya.py` | 40 tests, including the four gaps and the numerical-analysis traps |
| `scripts/run_hilbert_polya_demo.py` | the six-panel figure |

## Status

The Riemann hypothesis is **open**. This prototype is a screening device and a
record of four measured obstructions. It is not a proof, not a partial proof, and
not evidence for the hypothesis in either direction.
