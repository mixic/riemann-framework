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

# Screening Riemann-hypothesis arguments against Davenport–Heilbronn

### A methods note

**Status.** Manuscript prepared for submission. It has been implemented,
machine-checked and reproduced inside this repository; it has not been submitted to a
journal or a preprint server, and no claim of peer review is made. §9 lists what remains
before submission.

## Abstract

We describe a screening procedure for proposed arguments for the Riemann hypothesis.
The procedure is a contrapositive: the Davenport–Heilbronn function satisfies a
functional equation and has a zero-symmetry of exactly the kind used by many RH
arguments, but its RH-analogue is false. Hence any argument that goes through unchanged
for Davenport–Heilbronn cannot establish the hypothesis, and every argument for RH must
use at least one input that fails there. The procedure makes that observation mechanical:
a candidate declares the mathematical inputs it uses, each input is looked up in a fixed
inventory that records whether it transfers to Davenport–Heilbronn and where that fact
was read, and the candidate returns `dead`, `eligible`, or `needs_sourcing`. The
inventory is the deliverable, and it is deliberately conservative: three of its nine rows
are established by computation rather than citation, three are marked unsourced rather
than guessed, and a candidate declaring an unsourced input receives no verdict. We report
the calibration, a worked example in which the screen rules out an entire class of
candidate, and the limitations — chief among them that the screen classifies declared
inputs and is not a checker. Nothing here advances the Riemann hypothesis, and the note
claims no theorem beyond the contrapositive itself.

## 1. The problem

Referees and reviewers of RH proposals face a recurring situation: an argument whose
individual ingredients are all true, quoted correctly, and jointly insufficient, because
the same argument runs without change for a function whose RH-analogue is false. The
defect is not a mistake to be located in a calculation; it is a missing ingredient, and
it is invisible to checking the calculation line by line.

A standard remedy is the sanity check: apply the argument to a known counterexample.
That remedy is informal and sporadic. Nobody is obliged to perform it, the choice of
counterexample is arbitrary, and the conclusion ("this also seems to work for
Davenport–Heilbronn") is a remark rather than a status. This note proposes a small piece
of machinery in that gap: make the check explicit, attach it to the inputs of the
argument rather than to the argument as a whole, and give it three outcomes with stated
semantics.

The observation it rests on is old and is stated in the literature. Alpöge and Furman
record in §1.4 of their paper on simple zeros that a certain list of inputs "hold for
Davenport–Heilbronn and Epstein zeta functions, for which the analogue of RH is false"
[1]. Read forwards, that is a ceiling on one method. Read backwards, it is a screen:

> An argument that goes through unchanged where the hypothesis fails cannot establish
> the hypothesis.

What is new here is not the observation but the operational form: an inventory of inputs
with recorded provenance, a verdict vocabulary with pinned precedence, computational
verification of the rows that can be verified, and a refusal rule for the rows that
cannot.

## 2. The screen

### 2.1 Inputs and the transfer relation

A candidate argument is represented by an *input set*: a finite list of named
mathematical facts the argument uses, drawn from a fixed vocabulary. The vocabulary need
not be exhaustive for the screen to be useful, and it is not: nine names are used here,
because nine is what the worked examples required.

For each name and each counterexample function `f`, the inventory records a status in
`{transfers, fails, unsourced}`:

- `transfers` — the fact holds for `f` as it holds for `ζ`;
- `fails` — the fact is false for `f`;
- `unsourced` — a source was sought and the status was not established from it.

The screen is only as strong as this table, and the table is therefore the object that
must be published alongside the method: every row records the source it was read from,
and the three rows that were verified by computation say so.

### 2.2 Verdicts and precedence

| verdict | condition |
|:---|:---|
| `dead` | every declared input transfers to Davenport–Heilbronn |
| `eligible` | at least one declared input fails for Davenport–Heilbronn |
| `needs_sourcing` | no failing input, and at least one declared input is unknown or unsourced; or nothing is declared |

Precedence is deliberate. A failing input outranks an unsourced one: with one input that
Davenport–Heilbronn lacks already in evidence, the unsourced rows cannot make the
candidate more dead. An empty declaration is `needs_sourcing`, not `dead`: a candidate
that declares nothing has not been screened, and calling that "dead" would be a verdict
from no evidence.

`eligible` is weak on purpose. That the coefficients are multiplicative fails for
Davenport–Heilbronn and is still worthless as a proof strategy, because it is true of
`ζ` and proves nothing. Failing the transfer test is *necessary* for an RH proof and
nowhere near sufficient.

### 2.3 What the screen does not do

The screen classifies **declared** inputs. An argument that uses an input it does not
declare, or uses a declared input in a way that silently depends on an undeclared one, is
not classified. It is a screen on paper, not a checker, and its output is a filter on a
finite list of facts rather than a judgement about a proof.

## 3. The inventory

### 3.1 The nine inputs

`==` transfers, so the input cannot carry a proof of RH; `!!` fails for
Davenport–Heilbronn, so using it is what makes an argument eligible; `??` is unsourced,
and the screen declines to guess.

| | input | status | source | verified here |
|:---|:---|:---|:---|:---|
| `==` | functional equation | transfers | [4] | yes |
| `==` | real coefficients | transfers | derived | yes |
| `==` | zero symmetry (`ρ`, `1−ρ`, `conj ρ`, `1−conj ρ`) | transfers | [3] | |
| `??` | Hadamard product / order-1 factorization | unsourced | — | |
| `!!` | Euler product | **fails** | [4] | yes |
| `!!` | explicit formula with prime-power support | **fails** | [4] | |
| `!!` | Li/Keiper positivity | **fails** | [6] | |
| `??` | Riemann–von Mangoldt count | unsourced | — | |
| `??` | GUE pair correlation | unsourced | — | |

Three rows are left unsourced rather than filled in from the textbook expectation,
because filling them in would be exactly the move the vocabulary exists to prevent. The
Hadamard row is instructive: the *entirety* of Davenport–Heilbronn's L-functions is
sourced, the *order* — which is what a Hadamard product needs — was not. A screen that
guessed there would be a screen that launders recall into evidence.

### 3.2 Three rows established by computation

The explicit formula itself was derived, not quoted: no source read gave the constant
`κ` or the coefficients `b(n)`, so both are derived from the structural definition — a
real combination of `L(s, χ)` and `L(s, χ̄)` with `χ` the odd character mod 5 — and then
validated against the functional equation the object must satisfy. That validation
checks the character, the conductor, the odd-character gamma factor, and `κ`
simultaneously; get any one wrong and the residual is `O(1)` rather than `O(10⁻³⁰)`.

| check | measured | what it validates |
|:---|:---|:---|
| `κ` | `0.2840790438404122960282918` | the constant the functional equation selects |
| `\|τ(χ)/(i√5)\|` | `1.000` | the character and conductor |
| worst `\|Λ(s) − Λ(1−s)\|` at 30 digits | `6.3e-30` | the whole completion at once |
| `b(2)·b(3)` | `−κ² = −0.0807` | not multiplicative |
| `b(6)` | `1` | the same, from the other side |
| real coefficients | `< 1e-25` imaginary part | conjugation symmetry transfers |
The non-multiplicativity check settles the Euler-product row decisively and cheaply: one
failure is enough, and there is nothing asymptotic to check. It carries a positive
control — the coefficients `c(n) = 1` of `ζ` itself return `True` from the same
predicate — so the check is known to fire for the stated reason rather than always
returning `False`.

The residual is also what caught an inverted sign convention for `κ` while the
implementation was being written, where the residual was `0.7`. A validation that can
only pass is not a validation.

## 4. A worked example

Consider an argument built on a discrete involution of the plane whose fixed locus is
`Re s = 1/2`, offered as a reason why every zero must lie there. It declares two inputs:
the functional equation and the zero symmetry.

Both transfer. Davenport–Heilbronn has both, and has zeros off the line. So the same
involution fixes the critical line of a function that violates the hypothesis, and the
argument is `dead` — not by a calculation, and not by a numerical counterexample, but
because the two facts it uses are true of a function whose RH-analogue is false.

The screen does not say the involution is meaningless. It says that no argument using
only those two inputs can work, whatever the involution is. That is a stronger and more
useful statement than a failure to commute with an arithmetic structure, and it arrives
before any code is written.

The same screen returns `eligible` for a variant of that construction which is built on
the operator whose trace *is* the Euler product — precisely the input
Davenport–Heilbronn lacks — and `eligible` for a Weil-type compression whose trace and
Hilbert–Schmidt norm are evaluated on the prime side. In both cases the filter's
statement is narrow: there is somewhere for the arithmetic content to live. It says
nothing about whether the construction works.

## 5. An unresolved tension

The inventory marks the prime-side explicit formula as failing for Davenport–Heilbronn:
no Euler product means no local factor to expand and no `−f′/f` expansion supported on
prime powers. Alpöge–Furman §1.4 states that their inputs hold for Davenport–Heilbronn.

If both were true in the same sense, the paper would be contradicting itself, and it is
not. The likely resolution is that §1.4's input list is not the prime side — the prime
side belongs to the pair-correlation route — and that the two things called "inputs" are
different lists. That is a guess, and it is recorded as a guess rather than allowed to
produce a verdict: applying the prime-side row to such records would return `eligible`,
which directly contradicts the papers' own sharpness statements, and printing that would
be worse than refusing to print anything.

**This is the open item of the note.** A reader who resolves it should either reconcile
the row or add one; either way the inventory changes and the calibration must be re-run.

## 6. Implementation notes and traps

Two traps produced *false* results while the reference implementation was being written,
and both are recorded because a reader implementing the checks will meet them.

**Precision is ambient, and unary negation rounds to it.** A multiprecision library
evaluates at the ambient precision, and `-x` is not exact: negating a 30-digit value at
the default 15 digits silently replaces a 102-bit value with a 53-bit one. The first
version of the coefficient test formed `-κ` at ambient precision and failed by `2.5e-17`
while `c[3] + κ` was *exactly* zero — subtracting the two originals was exact, negating
one was not. Wrapping a value in the constructor to "fix" this makes both sides collapse
to `float64` and the check pass for the wrong reason.

**Ambient precision leaks between callers.** A module that assigns the ambient precision
at import time changes it for every caller afterwards. A check that assumed the default
digits then passes in isolation and fails in a larger suite. Every computational row
here runs inside a scoped-precision block, and a test pins that the ambient precision is
not what these functions assume.

## 7. Limitations and honest scope

1. **The inventory is the method.** A screen is exactly as strong as its table, and the
   table is nine rows with three unsourced entries. Extending it is the work.
2. **Declared inputs only.** Undeclared and silently assumed inputs escape, as §2.3 says.
3. **`eligible` is permission, not promise.** The screen has nowhere near the resolution
   to say an argument works.
4. **The contrapositive is elementary.** The methodological claim — that an inventory
   with provenance and a refusal rule is better than an informal sanity check — is the
   content, and it is a claim about practice, not a theorem.
5. **No claim about RH.** A `dead` verdict says an argument would also have established
   a false statement. It does not say RH is false, unprovable, or anything else.
6. **One counterexample family.** Davenport–Heilbronn is used because it is the standard
   one and because its functional equation and zero symmetry are *exactly* the ones an
   argument for `ζ` would use. Epstein zeta functions offer a second family; the
   vocabulary does not address them yet.

## 8. Reproducibility

The reference implementation is a single module with no dependencies beyond a
multiple-precision library. It exposes the inventory, the verdict logic, the calibration
constants of §3.2, and the three computed checks; a driver prints the calibration, the
inventory and the three lists.

The claims of §3.2 are reproduced by calling the calibration entry point at 30 digits;
the claims of §4 are reproduced by screening the recorded candidates. Every number quoted
here is pinned by an independent test that can fail: the constant `κ` to `1e-15`, the
functional-equation residual below `1e-20` across points that are mostly *off* the
critical line (sampling only on the line would test strictly less than it appears to),
the coefficient reality below `1e-25`, the non-multiplicativity witness, and the verdict
of every worked example.

## 9. What remains before submission

- Choose a venue. The natural homes are a number-theory journal willing to publish
  methodology, or an *Experimental Mathematics*-style venue; a preprint server is the
  minimum, and the note should be posted there before any journal submission.
- Strip the repository's license header (kept here for repository consistency) and set
  author metadata.
- Package the reference implementation and the full inventory — including the sources
  each row was read from — as supplementary material. Without the inventory the note is
  a suggestion, not a method.
- Resolve or explicitly retire the tension in §5.
- Decide whether the paper should also report the *negative* result: the screen was run
  against the author's own records and returned one `dead` entry, which is the flagship
  proposal of the repository in which the method was built. Reporting that is honest and
  costs nothing; omitting it would be a methods note whose method was never used on the
  author.

## References

1. Alpöge, L. and Furman, R. (2026). *More than two thirds of the zeros of the Riemann
   zeta function are simple and on the critical line*. arXiv:2608.13637, §1.4.
2. Davenport, H. and Heilbronn, H. (1936). *On the zeros of certain Dirichlet series I,
   II*. Journal of the London Mathematical Society 11, 181–185, 307–312.
3. França, G. and LeClair, A. (2024). *A theory for the zeros of Riemann ζ and other
   L-functions*. arXiv:1407.4358v2, §XIX.
4. LeClair, A. and Mussardo, G. (2024). *Riemann zeros as quantized energies of
   scattering with impurities*. JHEP 04 (2024) 062; arXiv:2307.01254v2.
5. Balanzario, E. P. and Sánchez-Ortiz, J. (2007). *Zeros of the Davenport–Heilbronn
   counterexample*. Mathematics of Computation 76, 2025–2029.
6. Voros, A. (2020). *Discretized Keiper/Li approach to the Riemann Hypothesis*.
   Experimental Mathematics 29(4), 452–469; arXiv:1703.02844v3.
