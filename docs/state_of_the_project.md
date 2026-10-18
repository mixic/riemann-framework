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

# State of the Project

This is the closing summary: what the repository contains, what it established,
what it falsified, what it corrected, and what remains open. It is written to be read
without the rest of the repository.

**The Riemann hypothesis is open.** Nothing here proves or disproves it, and no
result below is evidence for or against it except where a result is explicitly about
the hypothesis — which, in this repository, means the finite-field theorem, where RH
is a theorem and the computation is a proof.

## 1. What this is

A research workbench for the Riemann hypothesis: a numerical core, a set of
falsifiable claims about it, and — the part that turned out to matter most — a
machinery for killing those claims with numbers. Nine tracks, each with a document,
tests, and a recorded verdict.

It is **not** a proof attempt in the sense of a manuscript. It is a place where
proposals are stated precisely enough to be refuted, and where refutations are
recorded rather than quietly dropped. The flagship proposal was refuted.

## 2. Status at a glance

| track | status | evidence |
|:---|:---|:---|
| Numerical core (`zeta.py`, `zeros.py`, `explicit_formula.py`) | **working** | every other track depends on it |
| RH over finite fields (`finite_field_curves.py`) | **proved per curve** | 942 elliptic over `F₅…F₁₉`, 324 smooth genus-2 over `F₃`, 10 000 over `F₅`, **zero failures**; exact integer arithmetic |
| Prime certificates (`prime_certificate.py`) | **proved** | `p₁₀₀₀₀₀₀ = 15485863`, none of the first million missing |
| Lean 4 (`lean/`) | **8 modules compile** | 3 `sorry`- and `axiom`-free (`DimensionShift`, `InvolutionEigenspace`, `ZetaBridge`); RH statements carry `sorry` by design |
| Davenport–Heilbronn filter (`dh_filter.py`) | **working screen** | the repository's flagship proposal screens **dead**: every input it declares transfers to a function whose RH analogue is false |
| Zeta-containment screen (`zeta_factors.py`) | **working** | two number-field factorizations; the bound regression |
| Physics dictionary (`imaginary_time.py`, `prime_orbits.py`, `quantum_chaos.py`) | **measured, bounded** | `Tr[e^{−sH}] = ζ(s)` exactly for the primon gas; orbit dictionary exact at first order; the error term relocates RH |
| Hilbert–Pólya prototype (`hilbert_polya.py`) | **four gaps measured** | no eigenvalue; the box is a picket fence; a real spectrum is free; imaginary time is blind to `Re(s)` |
| Operator candidates (`operator_candidates.py`) | **screen built, negative result** | a prime-length graph fits GUE better than the zeros do; every operator with these eigenvalues is `diag(γ)` up to unitary |
| **Dimension-Shift Hypothesis** | **ABANDONED** | criterion (2): the sector class is inherited, not produced ([`central_hypothesis.md`](central_hypothesis.md) §10, [`m5_verdict.md`](m5_verdict.md)) |
| DSIN communication model | **closed** | a single published observable cannot support a security bound (§4.1 of [`dimension_shift_quantum_communication.md`](dimension_shift_quantum_communication.md)) |
| BB84 implementation layer | **started, one gap closed** | PNS recovers up to 99% of the sifted key; decoy bound valid ~2% below; finite-key floor `5.6e5` pulses; **detector blinding modelled** (QBER `0.0000` under attack, caught by a power monitor) |
| de Bruijn–Newman (`de_bruijn_newman.py`) | **restated, not tested** | `Λ ≤ 0` *is* RH; the low-zero scan is flat at `[9,9,9,9,9,9,9]` and insensitive by construction |

Test suite: **the whole tree is covered**, and every number quoted above is pinned by
a test that can fail. `python -m pytest tests/ -q` runs the suite; the Lean
assertions may skip on machines without a toolchain.

## 3. What was proved

Only two tracks produce proof in the strict sense, and both are finite:

1. **RH over finite fields, per curve.** `Z(C,T) = P(T)/((1−T)(1−qT))` with `P` an
   integer polynomial, so `|αᵢ| = q^{1/2}` is decidable by exact integer arithmetic —
   genus 1 reduces to `a² ≤ 4q`, genus 2 to a test on `S(w)`. No irrational is ever
   evaluated. This does **not** transfer to `ℚ`: the proof runs through Frobenius on
   étale cohomology, and no analogue of that action is known over `ℚ`.
2. **Prime certificates.** Sieve invariants plus deterministic primality prove that
   `15485863` is the millionth prime and that none is missing.

The Lean development proves the algebraic lemmas — `σ` is an involution, its fixed
locus is `Re(s) = 1/2`, the zeros form a `σ`-invariant quadruple, and the hypothesis
is equivalent to the absence of a distinct `σ`-partner. None of that is a step
towards proving RH; it is a precise statement of where the wall is.

## 4. What was falsified or closed

| claim | how it died |
|:---|:---|
| The Dimension-Shift Hypothesis | tested by its own criteria: the sector class is inherited from the input blocks (M5) |
| The "single-observable" DSIN channel | no function of one published observable bounds an adversary's information |
| The graded (shift-zeta) lift of `ζ` | functional equation fails for `τ ≠ 1`; the graded zeros do not coincide with the classical ones |
| A hard-box regularization of `xp` | produces an evenly spaced ladder, `r = 1.000` against `0.610`; overcounts `2.10×` at `T = 50` |
| "GUE statistics certify a candidate" | a prime-length graph scores `r = 0.641`, KS `0.0438` to Wigner, better than the zeros' own `0.610`/`0.0579`, and its counting function is linear |
| `Λ ≤ 0` by numerics | it is equivalent to RH; no computation establishes it |
| The repository's flagship proposal | the DH filter puts it on the dead list |

Each of these is documented with its measurement, and the six general lessons are in
[`central_hypothesis.md`](central_hypothesis.md) §10 and
[`lessons_learned.md`](lessons_learned.md) §17.

## 5. What was corrected

The repository's recurring failure was not a wrong theorem; it was a claim that
stopped being true quietly. The corrections are part of the record:

- **A verdict from one seed.** "DSH is SUPPORTED" came from the maximum of a 90-point
  grid at one seed. At `2d = 20` the per-seed standard deviation is `0.075` and 14% of
  *pure GOE* draws enter the acceptance window. Replaced with 300 seeds and error
  bars; the reported point (`0.6117`) has a 300-seed mean of `0.523 ± 0.069`.
- **A symmetry that was never enforced.** The model's commutator with `σ` was
  `1.35…1.46`, i.e. larger than 1. Now `H = [[A, C], [C†, A]]` gives `0.0` exactly.
- **A window calibrated on one draw.** The GUE reference was one matrix (`0.574`) and
  the window `[0.58, 0.62]` was applied to data that could not reach it. The references
  are now sampled: GOE `0.528 ± 0.033`, GUE `0.600 ± 0.028`.
- **A label swap that acquitted the hypothesis.** The first M5 run reported *SURVIVES*
  because `MATRIX_CLASSES` is `("goe", "gue")` and the draft named the GOE point
  "gue". Points are keyed by class name; the tests assert it.
- **Tests that ran themselves.** `test_criterion_1/2` were production functions;
  pytest collected the imported names and ran the full grid twice inside the suite.
  Renamed, with a collection guard.
- **Prose that drifted.** A README row still said "single seed" after the fix removed
  the single seed. Mechanical guards check counts, paths, figures and links; none can
  catch a sentence, and the sentences are where the overstatement lives.

## 6. What is open

| item | why it is still open |
|:---|:---|
| RH over `ℚ` | the hypothesis itself; every statement in `lean/` that names it carries `sorry` |
| Lean formalization of a proof | would need a proof first; the roadmap notes it is a multi-year undertaking |
| BB84 timing and Trojan-horse channels | need a time-resolved source/detector model and a back-reflection channel |
| A size-aware replacement for `std < 0.02` | the clause is unreachable at `2d ≤ 200`; it needs restating in terms of the standard error |
| Whether `Ω_{m,1}`-type weight-one inputs can be classified | the DH filter currently returns `needs_sourcing` for them |

The DSH is **not** on that list. It is closed.

## 7. What is claimed and not claimed

**Claimed:** the measurements above, reproducible by the commands in §8; the two
finite proofs; the Lean lemmas; the falsifications and their reasons.

**Not claimed:** any progress toward the Riemann hypothesis; that any track is a
candidate proof; that a numerical agreement is evidence for a structural
correspondence; that the models are faithful descriptions of deployed systems (the
BB84 layer especially — it is a model, and says so).

The operative distinction throughout is **finite versus universal**, not evidence
versus proof. Where a claim is finite, a computation with a certificate *is* a proof.
Where it quantifies over all zeros, no finite computation establishes it, and a test
not falsified at `N = 100 000` is never a proof for all `N`.

## 8. How to verify

```bash
cd python && python -m pytest tests/ -q          # the whole suite
python scripts/run_m5_analysis.py                # the decisive test (~6 min)
python scripts/run_falsification.py              # multi-seed grid, 300 seeds/point
python scripts/run_hilbert_polya_demo.py         # the four gaps
python scripts/run_finite_field_curves_demo.py   # the one place RH is a theorem
```

`tests/test_documentation_sync.py` checks the README against live artefacts —
counts, paths, figures, links — so the tables in this document cannot drift from the
code without failing a test. Prose can still drift; that limitation is itself
recorded.

## 9. The bottom line

The flagship hypothesis was falsified by its own stated criteria, in the document
that proposed it, with the numbers attached. That is the completion of a research
programme, not its failure.

The repository's standard, from the README:

> *"Several tracks here do fail, on purpose and on record: a negative result obtained
> by a stated method is worth more than an unfalsifiable claim of progress."*

The Riemann hypothesis remains open. What this project contributes is a worked
example of how to lose a hypothesis honestly — and a set of tools that make the
losing measurable.
