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

# The Davenport–Heilbronn Filter

## Abstract

A screening filter for candidate Riemann-hypothesis arguments, keyed on the
Davenport–Heilbronn function. It asks, of each mathematical input a candidate
uses, whether that input survives the change from `ζ` to a function whose
RH-analogue is **false**, and returns one of `dead`, `eligible`, or
`needs_sourcing`.

It is not an idea. It is an elimination procedure, and the interesting output is
the **dead list**: arguments ruled out because every input they declare also
holds where the hypothesis fails, so the same argument would have proved a false
statement. Run against this repository's own records it returns one entry, and it
is the repository's flagship proposal.

The filter is only as strong as its inventory, so the inventory is the
deliverable. Every row records the source it was read from, three rows are
verified by computation rather than citation, and three are marked `unsourced`
rather than guessed at — including one where the expected answer is probably
knowable and simply was not established here.

## 1. The contrapositive, and where it comes from

Alpöge and Furman's §1.4, "What the results are not", records that their inputs

> hold for Davenport–Heilbronn and Epstein zeta functions, for which the analogue
> of RH is false.

Read forwards, that is a ceiling on one method. Read backwards, it is a filter,
and a sharp one:

> An argument that goes through unchanged where the hypothesis fails cannot
> establish the hypothesis. **Therefore any proof of RH must use at least one
> input that fails for Davenport–Heilbronn.**

`docs/claimed_proof_triage.md` §3 already records the forwards reading. This
document, and `python/riemann_framework/dh_filter.py`, are the backwards one made
mechanical.

## 2. What Davenport–Heilbronn is, and exactly what was read

The sourcing rule for this work was that the definition had to be *read*, not
recalled, and the record below says what was actually read and what was not.

| Fact relied on | Where it was read |
|:---|:---|
| DH is a linear combination of two Dirichlet L-series, satisfies a functional equation, has infinitely many zeros on the critical line **and zeros off it** | França–LeClair, arXiv:1407.4358v2, §XIX and abstract |
| The DH *completion* satisfies the duality equation `χ(s) = χ(1−s)` | LeClair–Mussardo, arXiv:2307.01254v2 / JHEP 04 (2024) 062, abstract and §VII |
| DH "does not have an Euler product representation" | LeClair–Mussardo, same |
| There are "infinitely many pairs of solutions away from this axis and symmetrically placed with respect to it" | LeClair–Mussardo, same |
| Non-principal Dirichlet L-functions "are entire functions in the complex plane due to the absence of the pole at s = 1" | LeClair–Mussardo, §I |
| DH is the standard counterexample on which sequential RH criteria "selectively react to zeros off the critical line" | Voros, arXiv:1703.02844v3 / Exp. Math. 29(4), abstract |
| Zeros off the critical line have been computed for this function | Balanzario–Sánchez-Ortiz, Math. Comp. 76 (2007), abstract |

**Not read, and flagged as such.** Ivić's survey (`arXiv:math/0311162v1`) lists
the Davenport–Heilbronn zeta-function among the classical reasons to doubt RH;
the fetch truncated before that section, so **no inventory row is sourced from
Ivić's detailed treatment**. Voros's §4.4, "The Davenport–Heilbronn
counterexamples", was likewise not read, which is why the `li_positivity` row
carries a caveat. The *order* of the DH function (as opposed to its entirety) was
not stated in any source read, which is what leaves the `hadamard_product` row
unsourced.

**The explicit formula was derived here, not quoted.** No source read gave the
constant `κ` or the coefficients `b(n)`. Both are derived in the module from the
structural definition — a real combination of `L(s,χ)` and `L(s,χ̄)` with `χ` the
odd character mod 5 — and then *validated by the functional equation the object
must satisfy*, which is a stronger check than a quotation would have been:

```
κ                = 0.2840790438404122960282918
|τ(χ)/(i√5)|     = 1
worst |Λ(s) − Λ(1−s)| / max(...)   =  6.3e-30   at 30 digits
```

A residual at `1e-30` is the functional equation holding to working precision. It
validates the character, the conductor, the odd-character gamma factor
`(s+1)/2`, and `κ` simultaneously: any one of them wrong and the residual is
`O(1)`. It is also what caught an inverted sign convention for `κ` while the
module was being written, where the residual was `0.7`.

## 3. The inventory

Nine rows. `==` transfers to DH, so the input **cannot** carry a proof of RH;
`!!` fails for DH, so using it is what makes an argument eligible; `??` is
unsourced, and the filter declines to guess.

| | input | status | source | verified here |
|:---|:---|:---|:---|:---|
| `==` | `functional_equation` | transfers | LeClair–Mussardo | **yes** |
| `==` | `real_coefficients` | transfers | derived | **yes** |
| `==` | `zero_symmetry` | transfers | França–LeClair | |
| `??` | `hadamard_product` | unsourced | — | |
| `!!` | `euler_product` | **fails** | LeClair–Mussardo | **yes** |
| `!!` | `explicit_formula_prime_side` | **fails** | LeClair–Mussardo | |
| `!!` | `li_positivity` | **fails** | Voros | |
| `??` | `riemann_von_mangoldt_count` | unsourced | — | |
| `??` | `gue_pair_correlation` | unsourced | — | |

Three rows are **verified by computation** rather than cited. The functional
equation is checked as above. Real coefficients are checked to `1e-25`. And the
absence of an Euler product is checked decisively and cheaply:

```
b(2)·b(3) = −κ² = −0.0807009031...      b(6) = 1
```

The coefficients are not multiplicative. One failure settles it; there is nothing
asymptotic to check. The multiplicativity predicate has a **positive control**
(`c(n) = 1`, the coefficients of `ζ` itself, returns `True`), so the check is
known to fire for the stated reason rather than always returning `False`.

### Why three rows are left unsourced

`hadamard_product`: LeClair–Mussardo state the *entirety* of the L-functions, so
half this row is sourced. The *order* — which is what a Hadamard product needs —
was not. Filling it in from the textbook expectation is exactly the move this
vocabulary exists to prevent.

`riemann_von_mangoldt_count`: the analogue should follow from the functional
equation and the argument principle, both of which DH has, but no source read
states it for DH.

`gue_pair_correlation`: not established from any source. There is a *reason to
expect this row to be delicate* rather than a copy — DH is a linear combination
of two L-functions, so its zero process would plausibly be a superposition rather
than a single GUE — but that expectation came from a third-party code comment
encountered while searching, **not** from a source. It is recorded in the module
as an unverified lead.

## 4. The verdicts

| verdict | condition |
|:---|:---|
| `dead` | every declared input transfers to DH |
| `eligible` | at least one declared input fails for DH |
| `needs_sourcing` | no failing input, and at least one input unknown or unsourced; **or** nothing declared |

Precedence is deliberate and pinned by tests. A **failing** input outranks an
unsourced one: with one input that DH lacks already in evidence, the unsourced
rows could not make the candidate *more* dead. An **empty declaration** is
`needs_sourcing`, not `dead` — a candidate that declares nothing has not been
screened, and calling that "dead" would be a verdict from no evidence.

`eligible` is weak on purpose. "The coefficients are multiplicative" fails for DH
and is still worthless, because it is true of `ζ` and proves nothing. Failing the
transfer test is **necessary** for an RH proof and nowhere near sufficient.

The filter classifies **declared** inputs. An argument that uses an input it does
not declare, or depends silently on an undeclared one, is not classified. It is a
screen on paper, not a checker.

## 5. Screening this repository's own records

`python scripts/run_dh_filter.py`

```
DEAD        dimension_shift_w
eligible    dimension_shift_w_lifted_to_primon_gas (via euler_product)
eligible    weil_positivity_finite_compression (via explicit_formula_prime_side)
unscreened  de_bruijn_newman_first_exit (missing: hadamard_product)
unscreened  nonlinear_probe_example (missing: declaration)
unscreened  nyman_beurling_density (missing: declaration)
unscreened  proportion_lamzouri_new_proof (missing: declaration)
unscreened  proportion_two_thirds_alpoge_furman (missing: declaration)
```

**The dead entry is the flagship proposal.** `dimension_shift_w` proposes a
discrete involution of the plane fixing `Re s = 1/2`. Every input it declares —
the functional equation and the zero symmetry — holds for Davenport–Heilbronn,
whose zeros are *not* all on that line. So the same construction would fix the
critical line of a function that violates the hypothesis. The record's own
falsification criterion already said it carried no arithmetic content if it
treated every prime identically; the filter says something stronger, from a
different direction: it cannot work even in principle.

**The primon-gas lift survives, and for a checkable reason.**
`dimension_shift_w_lifted_to_primon_gas` is built on the operator whose trace
*is* the Euler product — precisely the input DH lacks. The filter says the
arithmetic content has somewhere to live. It says nothing about whether the
operator commutes; that is the record's own criterion and it is separately known
to fail.

**The Weil compression survives too.** That record's own text says its trace and
Hilbert–Schmidt norm are "evaluated on the prime side". DH has no prime side.

### Why four records are undelivered rather than guessed

Four records are left undeclared, and the reason is the same in each case: naming
their inputs would have been recall rather than reading.

- `nonlinear_probe_example` — a toy, by its own description.
- `nyman_beurling_density` — the criterion's route to `μ` is where an Euler
  product would enter, but I did not read the derivation, so I did not declare it.
- the two proportion records — see the tension in §6.

## 6. An open tension the filter surfaced

My inventory marks `explicit_formula_prime_side` as **failing** for DH: no Euler
product means no local factor to expand and no `−f'/f` expansion supported on
prime powers. But Alpöge–Furman §1.4 says their *inputs* hold for DH.

If both were true in the same sense, the paper would be contradicting itself, and
it is not. The likely resolution is that §1.4's input list is not the prime side —
the prime side belongs to the pair-correlation route — and that the two things
called "inputs" are different lists.

That is a guess, and I declined to let it produce a verdict. Declaring
`explicit_formula_prime_side` on the proportion records would return `eligible`,
which directly contradicts the papers' own sharpness statements; printing that
would be the failure mode `docs/claimed_proof_triage.md` §2 warns about, where a
misleading answer for a whole class of input is worse than a refusal. So the two
records are left unscreened and the question is recorded: **read §1.4's input
list, then either reconcile the row or add one.**

## 7. Two mpmath traps found while building this

Both produced *false* results before being caught, and both are recorded in the
tests rather than only here.

**Precision is ambient, and unary negation rounds to it.** `mpmath` evaluates at
the ambient precision, and `-x` is *not* exact: negating a 30-digit value at the
default 15 digits silently replaces a 102-bit value with a 53-bit one. The first
version of the coefficient test formed `-κ` at ambient precision and failed by
`2.5e-17` while `coeffs[3] + κ` was *exactly zero* — subtracting the two
originals was exact, negating one was not. `mp.mpf(x)` rounds the same way, so
wrapping a value in the constructor to "fix" it makes both sides collapse to
`float64` and the check pass for the wrong reason.

**Two test modules leak the global precision.**
`tests/test_graded_algebra.py:56` and `tests/test_graded_algebra_even_odd.py:54`
assign `mp.mp.dps = 30` at *module import time*, changing the ambient precision
for every test that runs afterwards. A test of this module that assumed the
default 15 digits therefore passed on its own and failed in the full suite. This
module's own functions are unaffected — they work inside `workdps` blocks — and
`test_ambient_mpmath_precision_is_not_what_this_module_assumes` pins that, but the
leak itself is **not fixed here** and is recorded as a defect: any test asserting
high-precision behaviour at ambient precision is currently order-dependent.

## 8. Files

| file | role |
|:---|:---|
| `python/riemann_framework/dh_filter.py` | the inventory, the verdict logic, and the DH calibration |
| `python/tests/test_dh_filter.py` | 41 tests: calibration, inventory integrity, verdict precedence, the real records |
| `scripts/run_dh_filter.py` | prints the calibration, the inventory, and the three lists |
| `ideas/*.json` | four records carry a `dh_inputs` declaration; four do not, deliberately |

## References

- Alpöge, L. and Furman, R. (2026). *More than two thirds of the zeros of the Riemann zeta function are simple and on the critical line*. arXiv:2608.13637, §1.4.
- Balanzario, E. P. and Sánchez-Ortiz, J. (2007). *Zeros of the Davenport–Heilbronn counterexample*. Mathematics of Computation 76, 2025–2029.
- Davenport, H. and Heilbronn, H. (1936). *On the zeros of certain Dirichlet series I, II*. J. London Math. Soc. 11, 181–185, 307–312.
- França, G. and LeClair, A. (2024). *A theory for the zeros of Riemann ζ and other L-functions*. arXiv:1407.4358v2, §XIX.
- Ivić, A. (2003). *On some reasons for doubting the Riemann hypothesis*. arXiv:math/0311162v1.
- LeClair, A. and Mussardo, G. (2024). *Riemann zeros as quantized energies of scattering with impurities*. JHEP 04 (2024) 062; arXiv:2307.01254v2.
- Voros, A. (2020). *Discretized Keiper/Li approach to the Riemann Hypothesis*. Experimental Mathematics 29(4), 452–469; arXiv:1703.02844v3.

## Disclaimer

Nothing here proves or disproves the Riemann hypothesis, and nothing here
evaluates any candidate argument as correct. A `dead` verdict says an argument
would also have established a statement that is false. An `eligible` verdict says
only that this filter found somewhere for the arithmetic content to live, which
is permission and not promise. `needs_sourcing` is the absence of a verdict, not
a bad one.
