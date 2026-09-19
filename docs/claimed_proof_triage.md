# Triaging a Claimed Proof

## Abstract

This article records what this repository can and cannot do with a claimed proof
of the Riemann hypothesis, prompted by two recent papers that are **not** RH
proofs and that say so themselves:

- Alpöge and Furman, *More than two thirds of the zeros of the Riemann zeta
  function are simple and on the critical line* (arXiv:2608.13637), with the
  mathematical argument written by Claude.
- Lamzouri, *A new proof that more than 2/3 of the zeros are simple and on the
  critical line* (arXiv:2609.02882).

Both prove that a **proportion** of the non-trivial zeros are simple and on the
line — 2/3 (0.6725 with the Montgomery–Taylor window) and 5/6 (0.83625) distinct.
Neither proves RH, and one of them contains a proof that its method cannot.

The repository checks the elementary, load-bearing components of both — a
rank–trace inequality, a multiset inequality, and the arithmetic of the constants
— and **names** the parts that no computation can reach. The alternative, feeding
a proof-shaped claim into the vetting pipeline, produces a verdict that looks like
a result and means nothing.

## 1. What is checkable, and what is not

Both proofs are, at the point where they do work, a finite elementary statement
combined with analytic input:

| component | paper | checkable here? |
|:---|:---|:---|
| Lemma 3.2, `rank P1 >= 2 tr P1 + 4 tr Q' - 4b - \|\|P1 + Q'\|\|²_HS` | Alpöge–Furman, item (L) | **yes**, exactly, and by Monte Carlo |
| The constant chain `2 - R(ψ)`, `(3 - R(ψ))/2` | both | **yes**, exactly — pure arithmetic |
| Proposition 2.1 (both inequalities) | Lamzouri | **yes**, exactly, and by Monte Carlo |
| Kernel admissibility: `η` real, even, `supp η ⊂ (−λ,λ)`, `η²̂(0) = 1` | Lamzouri | **yes** — the choice used here is verified |
| Weil's explicit formula; the unconditional prime-side second moment (Aryan; Baluyot–Goldston–Suriajaya–Turnage-Butterbaugh); Montgomery–Vaughan; Chebyshev–Mertens; Stirling | both | **no** — analytic number theory, outside any simulation |

`python/riemann_framework/proportion_certificates.py` implements the first four.

**What passing means.** Evidence that the linear algebra and the arithmetic of the
constants are right. Nothing more. A Monte Carlo search cannot prove an
inequality; it can only fail to find a counterexample, and the sampling need not
reach the extremal regime. The tests therefore weight the explicit tight cases
above the searches: at `Z = {x}` a single simple real point, both inequalities of
Proposition 2.1 are *equalities*, and at `P1 = [[1]]`, `Q = 0`, `b = 0` so is
Lemma 3.2. A tight case pins the normalisation in a way a random search does not.

Measured, for the record: Lemma 3.2 held in 20 000 random admissible cases (margin
at worst 0.096); Proposition 2.1 held in 3 000 random conjugation-invariant
multisets (both inequalities, tightest margin 0.0 — the tight case again); the
constants come out at `0.6725007037` and `0.8362503518`, matching both papers.

## 2. Why the vetting pipeline cannot take these

The pipeline's gates each require an input these papers do not supply:

| Stage | Requires | These papers offer |
|:---|:---|:---|
| B — affine gate | a closed-form expression in `s` and `s̄` | nothing of the kind |
| C — statistics | an eigenvalue spectrum | the zeros *are* the spectrum, but the claim is not a spacing claim |
| D — arithmetic probe | an expression to test against `p^{−s}` | nothing applicable |
| D2 — operator screen | a matrix spec (a prime-exponent permutation) | no such operator |

Supply a placeholder expression and you get a verdict: `passed=True,
stage_reached="D+"` for anything non-affine, or a stage-B failure for a constant.
Neither is about the paper. `Verdict.passed` is documented as *"not falsified by any
gate it was subjected to"* — deliberately not a correctness claim — so for a
proof-shaped claim that verdict is noise wearing the clothes of a result.

The two records in `ideas/` carry this in their `notes` precisely because of that
hazard: `scripts/run_idea_pipeline.py` will report a stage-B failure for each, and
that verdict means **"this claim is outside the pipeline's input domain"**, not
"this paper is wrong". A pipeline that returns a misleading answer for a whole
class of input is worse than one that refuses, and the cheapest fix available is to
say so where the answer is printed.

**A robustness gap this exposed.** The records use a constant certificate as their
`expression`, which the evaluator accepts and Stage B then rejects as an affine
constant — the documented behaviour. The first drafts used `cot(1/sqrt(2))`, which
is *not* in the expression evaluator's allowlist, and the result was not a verdict:
`check_affine_reduction` raises `ExpressionError` at evaluation time and
`run_idea_pipeline.py` does not catch it, so the runner **crashed** with a
traceback. Stage A catches forbidden tokens and syntax errors but not an expression
that compiles and then fails to evaluate, because the guard wraps parsing and the
failure happens later, inside the affine gate. Recorded rather than fixed silently;
the fix is to wrap the Stage B call the way Stage A is already wrapped.

## 3. The papers' own ceilings, which are results in their own right

Alpöge–Furman §1.4 is titled *"What the results are not"*. It records that the
theorems are lower bounds only, that the remaining third of the zeros is *not*
shown to be off the line, and — decisively —

> the inputs ... hold for Davenport–Heilbronn and Epstein zeta functions, for
> which the analogue of RH is false.

An argument that goes through unchanged where the hypothesis fails cannot
establish the hypothesis. That is not a caveat attached to the result; it is a
**proof that this method cannot reach RH**, and the same paper records that the
certificate is sharp within its class. Lamzouri records the matching ceiling on the
other route: the pair-correlation method would need `Re K(z) ≥ 0` for all complex
`z`, and *"no such nonconstant entire kernel exists"*.

This belongs with the repository's other limits-of-the-method findings — the
affine-reduction gate, the shift-zeta result, the DSIN closure. It is the same
species: a precise statement of where a line of attack stops, obtained by
argument rather than by running out of ideas.

## 4. What would actually check a proof

Not this pipeline, and not numerics. Two things:

**Lean.** `python/tests/test_formal_proof.py` compiles Lean modules and enforces
both directions: a module recorded as sorry-free that gains a `sorry` or an
`axiom` fails, and a module recorded as carrying an open RH target that stops
reporting `sorry` fails. Both papers claim Lean 4 formalisations (Alpöge–Furman
Appendix A; Lamzouri Appendix A, by AxiomProver). Compiling those and counting
`sorry`s is a real mechanical check — of a *formalisation of a proportion theorem*,
not of RH.

**Reading it.** The residual limit is unchanged: a formalisation can compile and be
a faithful proof of a mis-stated theorem, and neither paper's analytic input is
mechanically checkable here.

## 5. The standing position

RH is open. This article adds no evidence either way, and the machinery it
describes cannot produce any. `tests/test_formal_proof.py` enforces the negative
half mechanically, and `tests/test_proportion_certificates.py` guards the module's
public surface against acquiring a name that implies a proof verdict. Neither
paper claims RH, and the second contains a proof that its method cannot reach it.

## 6. Files

| file | role |
|:---|:---|
| `python/riemann_framework/proportion_certificates.py` | the constants, the kernel, Lemma 3.2, Proposition 2.1 |
| `python/tests/test_proportion_certificates.py` | 20 tests, weighted toward the tight cases |
| `ideas/proportion_two_thirds_alpoge_furman.json` | claim, falsification criterion, and the ineligibility note |
| `ideas/proportion_lamzouri_new_proof.json` | the same for Lamzouri |

## References

- Alpöge, L. and Furman, R. (2026). *More than two thirds of the zeros of the Riemann zeta function are simple and on the critical line*. arXiv:2608.13637.
- Lamzouri, Y. (2026). *A new proof that more than 2/3 of the zeros of the Riemann zeta function are simple and on the critical line*. arXiv:2609.02882.
- Montgomery, H. L. (1973). *The pair correlation of zeros of the zeta function*.
- Baluyot, S., Goldston, D. A., Suriajaya, A. I. and Turnage-Butterbaugh, C. (2024). *An unconditional Montgomery theorem for pair correlation of zeros of the Riemann zeta function*.
- Weil, A. (1952). *Sur les "formules explicites" de la théorie des nombres premiers*.

## Disclaimer

Nothing here proves or disproves the Riemann hypothesis, and nothing here evaluates
either paper as a proof. It checks their elementary components, records the parts
that cannot be checked by computation, and documents the limits of the repository's
own vetting pipeline rather than stretching it to return a verdict it cannot
support.
