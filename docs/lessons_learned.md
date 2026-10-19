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

# Lessons Learned

This document records negative knowledge and limitations from the Riemann
Framework experiments. It is part of the research record, not a list of
failures to hide.

## Consolidated negative results (§1–§9)

Every track in this repository ends in a negative result. This part consolidates
them in one place, each with the claim that failed, the measurement that failed it,
the structural reason where one is known, and what would be needed to fix it. The
narrative sections that follow are the original record and are kept unchanged.

### §1 The falsification grid: "DSH is SUPPORTED" was a single-seed artefact

- **Claim that failed.** The dimension-shift Hamiltonian reaches GUE statistics, so
  the Dimension-Shift Hypothesis is supported.
- **Measurement.** The reported maximum was `⟨r⟩ = 0.6117` at `d = 10`,
  `coupling = 0.5`, `symmetry_breaking = 2.0`, from one seed. Over 300 seeds that
  point gives `0.5226 ± 0.0694`, and at `d = 200` it gives `0.5315 ± 0.0034`. The
  model's `σ`-violation was never enforced: `‖[H,σ]‖/‖H‖ = 1.346 … 1.462`. 14% of
  *pure GOE* draws land in the `[0.58, 0.62]` window (23% with `unfold=False`), so a
  90-point grid hits it by chance about a dozen times.
- **Structural reason.** The old model drew two independent real blocks, so (i) it
  violated requirement 1 of the hypothesis, and (ii) it was GOE, not GUE. Once
  `[H,σ] = 0` is enforced the spectrum is `spec(A+C) ⊕ spec(A−C)`, a superposition:
  the full spectrum lands at `[0.3689, 0.4287]`, and a single sector reaches
  `[0.5927, 0.6092]` only because GUE blocks were put in. The class is inherited.
- **Fix applied.** 300 seeds per point, mean ± std and sem, sector split, five-label
  verdict; `mixed` for the complex-Hermitian class, `goe_only` for the real one.
- **Still open.** The `std < 0.02` clause is unreachable at these sizes (`0.084` at
  `2d = 20` down to `0.026` at `2d = 200`); a size-aware criterion is needed.

### §2 Shift-zeta: the graded lift does not reproduce the zeros

- **Claim that failed.** A graded (shifted) extension of `ζ` on `A = A₀ + ωA₁`
  reproduces the classical zeros and their functional equation.
- **Measurement.** Of the seven criteria, `G5` (functional equation) **fails** for
  `τ ≠ 1` and `G6` (zeros in `Fix(σ)`) fails numerically; `G7` passes only at
  `τ = 1` (relative error `5.1e-4` at `s = 2`, `5.9e-12` at larger `s`). The graded
  trace is strictly larger than the classical one away from `τ = 1`.
- **Structural reason.** The graded trace agrees with `ζ` at `τ = 1` and nowhere
  else: the lift is not a deformation that preserves the Euler product, so the
  completion symmetry that forces the classical zeros into `Fix(σ)` has nothing to
  act on.
- **Fix needed.** A different lift — one whose `τ`-dependence sits in the Euler
  product rather than outside it. None is known here.

### §3 DSIN: the design is closed, not merely unproven

- **Claim that failed.** A published `σ`-eigenvalue observable can support a
  security bound for a communication channel.
- **Measurement.** The `σ`-basis intercept-resend attack yields **detection
  0.0000, BER 0.0000, one full bit**, and the fermionic phase flip at `φ = π` is
  detected at `2.22e-16` while inverting every bit (`BER = 1.0000`).
- **Structural reason.** One published observable means the adversary measures
  exactly what Alice encoded; §4.1 of `docs/dimension_shift_quantum_communication.md`
  proves that no function of that statistic bounds her information. The surviving
  result, that a `σ`-commuting channel preserves `Fix(σ)`, is an exact commutation
  theorem and never was a security statement.
- **Fix needed.** None inside this design. A successor needs a second, incompatible
  basis — which is BB84, and BB84 already exists.

### §4 Hilbert–Pólya prototype: four independent gaps

- **Claim that failed.** An operator whose eigenvalues are the zeros would prove RH.
- **Measurement.** (i) no eigenvalue: truncated norm `13.816` at width `10⁶`, no
  limit at either end; (ii) the hard box is a picket fence, `r = 1.000` against
  `0.610`, and overcounts by `2.10×` at `T = 50`; (iii) a real spectrum is free:
  `diag` of any real list is self-adjoint, and the `PT` model breaks at
  `θ_c = arcsin(s/r) = π/6`; (iv) `Z(β)` is *identical* for zeros on and off the
  line (`8.837461e-04`, difference `0`).
- **Structural reason.** Scale invariance gives a continuous spectrum; a box gives
  an arithmetic ladder; self-adjointness is a hypothesis about `H`, not about `ζ`;
  and thermal functionals read only `Im(s)`.
- **Fix needed.** An operator defined without `ζ`, with a proved identification of
  its spectrum with the zeros. That is the open problem.

### §5 Operator candidates: statistics cannot certify

- **Claim that failed.** Matching GUE spacing statistics identifies a candidate with
  the zeros.
- **Measurement.** A prime-length star graph — Gutzwiller dictionary exact, closed
  orbits `= log n`, self-adjoint by construction — scores `r = 0.641` and a KS
  distance `0.0438` to the Wigner surmise, against the zeros' own `0.610` and
  `0.0579`: it fits the universal statistics **better** than the zeros do, while its
  counting function is linear. The unitary twin `U diag(γ) U†` passes everything to
  `2e-13`.
- **Structural reason.** Universal statistics are universal, and by the spectral
  theorem every self-adjoint operator with spectrum `{γ_n}` is unitarily equivalent
  to `diag(γ_n)`, so the existence of such an operator is empty.
- **Fix needed.** Screen the *definition*, not the spectrum: independence from `ζ`
  plus a proved identification.

### §6 Primon gas symmetry: a basis permutation cannot commute

- **Claim that failed.** Swapping the exponents of two primes is a symmetry of the
  primon Hamiltonian and can lift to the chaos model.
- **Measurement.** `‖[W, H]‖_F` stays bounded away from zero as `n_max` grows to
  `4000` (and grows with it); at `n_max = 2000` about 800 basis vectors genuinely
  move while about 400 are pinned by the truncation boundary.
- **Structural reason.** `H` is diagonal with the strictly increasing, hence simple,
  spectrum `log n`. A matrix commuting with a diagonal matrix of simple spectrum is
  diagonal in that basis, so any map moving weight between `|n⟩` and `|m⟩` provably
  fails. The nonzero norm is an illustration, not the argument.
- **Fix needed.** A symmetry acting on a non-diagonal representation — the
  Bost–Connes Galois action, for instance.

### §7 de Bruijn–Newman: `Λ ≤ 0` is not numerically verifiable

- **Claim that failed.** A numerical study of `H_t = e^{−tD²}H₀` can support
  `Λ ≤ 0`.
- **Measurement.** The zero-count scan is flat at `[9, 9, 9, 9, 9, 9, 9]` across the
  whole tested range, and it would be flat under either hypothesis: if `Λ < 0` the
  first exit sits at Lehmer-pair heights, far above the range. Known bounds are
  `Λ ≥ 0` (Rodgers–Tao) and `Λ ≤ 0.2` (Polymath15).
- **Structural reason.** `Λ ≤ 0` is *equivalent* to RH, so no computation can
  establish it; the low-zero scan is insensitive by construction, not reassuring.
- **Fix needed.** None. The equivalence is exact and the insensitivity is documented
  in `INSENSITIVITY_NOTE`.

### §8 DH filter: the flagship proposal is on the dead list

- **Claim that failed.** The repository's flagship idea is a live candidate.
- **Measurement.** It screens `dead`: every input it declares also transfers to
  Davenport–Heilbronn, for which the analogue of RH is **false**. DH itself has the
  functional equation (residual `2.3e-17`) but no Euler product — `b(2)b(3) = −κ²`
  rather than `b(6)`.
- **Structural reason.** The screening principle is that an input which survives
  transfer to a known-false analogue cannot be evidence for the target. Validity
  under DH is a property of the *argument*, not of the phenomenon.
- **Fix needed.** Declare inputs that do not transfer. The filter names them.

### §9 What this project learned about falsification

1. **A maximum over a grid is a search, not a test.** Any verdict built from the
   best of `N` noisy points needs a multiple-comparison correction; without one it
   reports the noise.
2. **A statistic needs a seed floor and a pre-registered window.** "Supported" is not
   a word that can be attached to a number without a standard deviation.
3. **A model correction invalidates the old verdict.** The `σ`-violation existed for
   many commits, and every number computed under it had to be recomputed, not
   reinterpreted.
4. **A negative result must be recomputed, not just requalified.** Four of the nine
   sections above were found by re-running a test that had passed.
5. **An asymptotic obstruction is not a screen at accessible sizes.** The zero
   density is asymptotically `T log T`, yet a power law `T^1.436` reproduces the
   count to `1.33` levels in `100`, so the obstruction is a requirement on future
   constructions, not a test of present ones.
6. **Prose drifts last and worst.** Every mechanical guard in this repository
   (`test_documentation_sync.py`) checks counts, paths, figures and links; none can
   catch a sentence that stopped being true, and the sentences are where the
   overstatement lives.

## 1. Numerical Evidence Is Not a Proof

Known zeta zeros can be computed and checked to high precision, but finite
verification cannot establish that every non-trivial zero lies on the
critical line. Passing numerical tests are evidence about the tested range.

Likewise, a model with GUE-like spacing statistics has matched a universal
statistical feature. It has not reproduced the Euler product, the individual
zeros, or the Riemann-von Mangoldt density.

## 2. Explicit-Formula Summation Is Delicate

The naive sum over zeta zeros is conditionally convergent. Adding more zeros
in their numerical order does not guarantee a monotone improvement. The
current implementation uses Gaussian regularization for visualization and
records this limitation rather than treating the output as an exact prime
counting formula.

A future comparison should state the test function, truncation, ordering,
precision, and error metric.

## 3. GUE Statistics Alone Are Too Weak

The dimension-shift chaos experiments can produce mean adjacent-gap ratios that
are classified as GUE-like by a simple reference heuristic. This does not
identify the model with the Riemann spectrum. Random matrices are designed to
produce universal local statistics without carrying the arithmetic structure
of the primes.

The missing tests are spectral density, prime weighting, out-of-sample
prediction, and an exact or mathematically controlled zero-to-spectrum map.

## 4. Coupling Results Depend on Experimental Choices

The observed mean `r` value changes with matrix dimension, random seed,
coupling, symmetry-breaking strength, unfolding method, and normalization.
A single favorable parameter value is therefore not a robust result.

Every reported sweep should include:

- matrix dimension;
- coupling values;
- symmetry-breaking values;
- random seed policy;
- unfolding method;
- sample size; and
- the reference ensemble values.

## 5. Symmetry Does Not Automatically Force Fixed Points

The functional equation maps zeros to symmetry partners. It does not by itself
prove that every zero is fixed by the symmetry. The fixed-locus idea requires
an additional positivity, self-adjointness, trace-formula, or equivalent
forcing theorem.

This distinction is essential for both the dimension-shift RH proposal and
interpretations of the DSIN sector swap.

## 6. The Finite Sector Model Is a Toy Model

The finite matrix

```text
sigma = [[0, I], [I, 0]]
```

is a useful test object. Its square is the identity, it is Hermitian, and its
`+1` and `-1` eigenspaces have equal dimension. These facts do not establish
the existence of a canonical infinite-dimensional number system or physical
Hamiltonian.

The current finite Witten-index helper counts numerical zero modes of matrices.
It is not by itself a supersymmetric index theorem and does not prove
topological protection.

## 7. The First DSIN Simulation Was Incomplete

The initial DSIN simulation accepted a coupling parameter without applying the
Hamiltonian evolution, used a deterministic projection in its intercept-resend
model, and relied on a brittle single-seed detection threshold. These issues
were corrected by:

- applying finite Hamiltonian evolution;
- sampling sigma measurements with the Born rule;
- sampling intercept-resend outcomes according to measurement probabilities;
- validating dimensions, channel settings, and noise parameters; and
- replacing the single-run threshold with an aggregate multi-seed test.

The corrected simulation is still a toy channel. It does not provide a
composable security proof or BB84-equivalent guarantees.

## 8. Lean Formalization Is Still Open

The repository now has a first standalone Lean lemma for the involution
identity, but this is only a small algebraic result. It does not formalize the
zeta function, the Hamiltonian, the Euler product, or RH.

The next useful formal steps are finite matrix identities, eigenspace
properties, and commutation lemmas with explicit assumptions.

## 9. What Has Not Yet Worked

The following major goals remain unresolved:

- no operator has been constructed with a proved exact zeta spectrum;
- no spectral-density match has been established;
- no Euler-product derivation emerges from the sector model;
- no proof forces all zeros into the fixed locus;
- no physical DSIN implementation has been demonstrated; and
- no cryptographic security theorem has been proved for DSIN.

Recording these open failures prevents the project from confusing a working
prototype with a completed theory.

## 10. A Lift Confined to the Fixed Locus Cannot Test the Fixed Locus

The shift-zeta programme asked whether lifting the Euler product to a graded
algebra `A = A0 + omega*A1` forces the zeros into `Fix(sigma) = A0`. The
construction built for that purpose cannot answer the question, and the reason
is structural rather than numerical.

Every local factor is a polynomial in the single element
`gamma_tau = ((1+tau)/2)I + ((1-tau)/2)omega`, so the whole Euler product lies
in the two-dimensional algebra `C[gamma_tau]`. There is no interaction *between*
primes: the product is a product of functions of one generator. At `tau = 1` the
generator is the identity, so the product is scalar and sits in `Fix(sigma)` by
construction.

An object placed inside the fixed locus by definition cannot serve as evidence
about whether zeros are forced there. The general lesson: **check that a
proposed test can fail before running it.** If the construction satisfies the
conclusion identically, the test is vacuous.

Numerically the framework behaves as follows (600 primes; details in
`docs/shift_zeta_result.md`):

- the algebra is well-defined and `sigma` is an algebra homomorphism;
- the graded trace is `sigma`-invariant and the supertrace is
  `sigma`-anti-invariant -- two different functionals, easily confused;
- at `tau = 1` the graded trace equals the classical Euler product term by term
  (relative error `5.1e-4` at `s = 2`, which is pure truncation);
- for `tau != 1` it departs from `zeta` by 11% to 44% at `s = 2` and fails the
  completion symmetry with residuals `1e-2` to `1e-1`.

## 11. A Control Is What Makes a Zero Comparison Decisive -- or Not

An earlier version of the shift-zeta analysis concluded that the zero
comparison was undecidable, because a sign-change scan on the critical line
reported 28 crossings against 4 classical zeros. That conclusion was too
pessimistic, and the reason is instructive.

The scan was the wrong diagnostic. The right one uses a control: at `tau = 1`
the graded trace *is* the classical partial Euler product term by term, so
whatever a diagnostic reports there is pure truncation artefact. Comparing
`|Z_A(rho, tau)| / |Z_A(rho, 1)|` at the classical zero heights cancels the
truncation and isolates the grading:

| `tau` | ratios at the first six zeros |
|---:|---|
| 0 | 7.54, 5.72, 4.35, 6.88, 6.14, 3.45 |
| 0.5 | 2.25, 2.07, 1.97, 2.35, 2.19, 1.75 |
| 2 | 0.551, 0.565, 0.551, 0.533, 0.543, 0.557 |

The ratio is tightly clustered across six independent heights and is not 1. At
`tau = 1` the trace dips sharply exactly at the classical zeros; at `tau = 0`
it shows no such dips and is 3.5 to 7.5 times larger there. The zero sets do not
coincide.

Two further lessons:

- **A withdrawn statistic.** Flagging "deepest local minima" and counting
  matches to classical zeros scored 7 of 8 *at the `tau = 1` control*, where the
  trace is the classical product. It was measuring the oscillation of a
  truncated product, not the location of zeros. It was removed, not reported.
- **Failures of a diagnostic are not findings about the object.** "I cannot
  resolve the zeros" and "the zeros differ" are different claims. Both mistakes
  were made here before the control settled it.

### The asymmetry that remains

The comparison settles one direction and not the other, and it is worth being
explicit rather than letting the figure imply more than it supports.

Settled: the graded trace does **not** reproduce the classical zeros. The
`tau = 1` control dips sharply at every marked zero and the `tau = 0` trace does
not, while the ratio is 3.5 to 7.5 there and tightly clustered across six
independent heights.

Not settled: *where* the graded zeros are. Locating them by the deepest minima
of the raw product fails. At `tau = 0.5` the minima reproduce the `tau = 1`
positions to within 0.05 against classical-zero deviations of 0.02 to 0.10,
which means they are tracking truncation rather than the function. A localisation
claim needs an analytic continuation of `Z_A` into the critical strip, and none
has been built.

General form: **a comparison can falsify a match without being able to certify a
mismatch in position.** Say which direction the evidence runs.

## 12. `numpy.bool` Is Not `bool` to a Type Checker

A type checker rejects

```python
def is_x(self) -> bool:
    return np.isclose(self.a, 0.0)
```

with

```text
Type "numpy.bool[builtins.bool]" is not assignable to return type "bool"
```

`np.isclose`, `np.allclose` and `np.array_equal` are declared as returning
`np.bool[builtins.bool]` in the numpy 2.x stubs. `np.bool_` subclasses `bool`,
so this works at runtime and every test passes, but the declared annotation is
a lie to the checker.

Wrap it: `return bool(np.isclose(...))`. Same for `np.isscalar`, and for
`np.all`/`np.any` applied to an array.

Worth recording because it is invisible in testing: the runtime behaviour is
correct, so only a static check catches it. Note also that a test asserting
`is True` or using `assert` will not distinguish the two, since `np.bool_` is
truthy in the same way.

## 13. Falsification Grid Result

The default falsification grid was run with:

- dimensions `[10, 20, 30]`;
- couplings `[0.0, 0.25, 0.5, 1.0, 2.0, 5.0]`;
- symmetry-breaking values `[0.0, 0.5, 1.0, 2.0, 5.0]`; and
- seed `42`.

This produced 90 parameter points:

| Result | Count |
|:---|---:|
| GUE-like | 10 |
| GOE-like | 16 |
| Poisson-like | 4 |
| Intermediate | 60 |

The minimum mean ratio was `0.304776`. The maximum was `0.611747`, reached at
`dim_per_sector = 10`, `coupling = 0.5`, and
`symmetry_breaking = 2.0`. The current heuristic therefore returned
`supported` because at least one point entered the GUE window `[0.58, 0.62]`.

This is a mixed result, not a confirmation of DSH. Most tested points were
intermediate, and the favorable point occurred at the smallest tested
dimension. The grid also uses one random seed per parameter point, so the
result needs repeated-seed and larger-dimension validation before it can be
interpreted as robust evidence.

The result demonstrates why a single maximum mean `r` is insufficient. Future
falsification summaries should report stability across seeds, finite-size
scaling, control ensembles, KS distances, and spectral density.

The reproducible runner `scripts/run_falsification.py` now writes the complete
console table, `output/falsification_heatmap.png`,
`output/falsification_histogram.png`, and
`output/falsification_summary.txt`. These artifacts make the result reviewable
without treating a generated plot as a proof.

## 14. A Probe Whose Prime-Dependence Cancels Is Not a Probe

The external `rh_idea_framework` prototype's "Stage D" arithmetic probe was
meant to test whether a candidate map `w` interacts with the Euler product, by
comparing `w(p^{-s})` against `p^{-w(s)}` for each prime `p`. The code actually
computed

```text
lhs = w(-s) * log(p)
rhs = -w(s) * log(p)
```

and took the *relative* error `|lhs - rhs| / max(|lhs|, |rhs|)`. Both `lhs` and
`rhs` carry the same factor `log(p)`, so the factor cancels out of the relative
error exactly:

```text
|w(-s) + w(s)| / max(|w(-s)|, |w(s)|)
```

which contains no `p` at all. The per-prime error was therefore identical for
every prime, the spread across primes was always ~0, and the probe's
"p-dependent mismatch" flag (and the pipeline's `"D+"` stage) could never fire.
The test was silently measuring "is `w` odd under negation", not "does `w`
distinguish primes".

Two lessons follow.

First, a diagnostic whose headline signal is a *spread across* a parameter must
be checked for accidental invariance in that parameter. Dimensional analysis on
the probe's own formula would have caught this in one line.

Second, a numeric gate should be unit-tested against both a map that must pass
it and a map that must fail it. In the corrected port
(`riemann_framework/idea_pipeline.py`), `probe_multiplicative_coupling("s")`
gives spread ~1e-17 (identity commutes with every Euler factor) while
`probe_multiplicative_coupling("1 - s_conj")` gives spread ~0.28 (the
reflection genuinely distinguishes primes), and both are asserted in
`tests/test_idea_pipeline.py`. The corrected comparison is `w(p^{-s})` versus
`p^{-w(s)}`, evaluated with mpmath so that large map values do not overflow
Python's complex exponentiation.

**A second instance, and a sharper version of the same lesson.** The corrected
probe still read its headline signal from a spread across primes, and a spread
can be accidentally invariant in a second way: when the mismatch *saturates* near
its maximum for every prime, the spread collapses to round-off. The registry
record `nonlinear_probe_example` (`s*s_conj - s`) produces per-prime errors of
exactly `1.0` and a spread of `2.1e-08`, so the probe described "treats every
tested prime identically" for a map that fails to commute with the Euler factor
as badly as it possibly can — the description was the opposite of the truth.

Two things were wrong, and only one of them was the description. The spread was
misleading, and Stage D was *not matching its own contract*: it was
informational, so a map with no p-dependence reached `passed=True` while its own
summary said it did not engage the Euler product — even though the arithmetic
clause of the recorded falsification criterion names exactly that observation as
falsifying. Both are fixed. The probe now reports a regime (`commutes`,
`uniform_failure`, `p_dependent`) so the two near-zero-spread situations cannot
be confused, and Stage D fails an idea whose mismatch carries no p-dependence.

The generalisation is worth more than the bug. Section 14's lesson is usually
read as "check the formula once". It is really that a spread-across-a-parameter
diagnostic needs rechecking *every time its inputs change*, because each new
invariance hides in the same place, and the first fix — which was correct, and
tested — is exactly what made the second one look trustworthy. A gate that
reports a statistic it never acts on is the other half of the same failure: the
number was right and the verdict ignored it.

## 15. The DSH Falsification Verdict Was a Single-Seed Artefact

The `falsification_summary.txt` that shipped until this correction said
**"DSH is SUPPORTED"**. It was not, and the reasons are worth recording because
each one is a pattern rather than a slip.

**The verdict took the maximum of a noisy statistic.** The grid ran one seed per
point and declared support if *any* of 90 points had a mean `r`-ratio in
`[0.58, 0.62]`. At `2d = 20` the per-seed standard deviation of that statistic is
`0.075`, and **14% of pure GOE draws** (`23%` with `unfold=False`) land in that
window. With 90 points the window is hit by chance a dozen times over. The
reported point — `d = 10, coupling = 0.5, sb = 2.0`, `0.6117` — has a 300-seed
mean of `0.523 +- 0.069`: a `+1.3 sigma` fluctuation of a model that was never in
the GUE class at all.

**The model was GOE and said GUE.** Both blocks were real symmetric, so the model
sat in the time-reversal-symmetric class (`0.53`), not the zeros' class (`0.60`).
The module's own docstring stated the goal as "iterate on the model until the
spectrum matches GUE statistics" — a description of p-hacking written where the
method should have been.

**Requirement 1 of the hypothesis was violated at every point.** `sigma` is the
sector swap; `[H, sigma] = 0` requires equal diagonal blocks and a Hermitian
coupling. The old model drew them independently, so
`||[H, sigma]||_F / ||H||_F = 1.346 .. 1.462` — larger than 1, which should have
been impossible to miss. The corrected construction measures `0.0` by making the
block appear in both sectors.

**The windows were calibrated against a single draw.** `R_GUE = 0.599` is the
asymptotic value; the code's own reference call drew *one* 100×100 matrix and got
`0.574`, and the window `[0.58, 0.62]` was then applied to data that could not
reach its own reference. Sampled properly the references are `GOE 0.528 +- 0.033`
and `GUE 0.600 +- 0.028`.

**What the correction found.** With `sigma` enforced and 300 seeds per point the
verdict is `mixed`, and "mixed" is not a success: the full spectrum of a
`sigma`-symmetric model is a superposition of two sectors and lands at
`0.369 .. 0.429`, never GUE; a single sector lands at `0.594 .. 0.609` when — and
only when — the input blocks are GUE. The class is inherited, so the model
demonstrates that the construction *can* carry GUE statistics, not that it
produces them.

**And one criterion needs fixing before it is used again.** The specification asks
for `std < 0.02` over 300 seeds. Measured per-seed `std` is `0.084` at `2d = 20`,
`0.034` at `2d = 100` and `0.026` at `2d = 200`, shrinking like `1/sqrt(2d)`;
`0.02` needs a few hundred levels. The threshold is implemented as written, it is
reported as unreachable, and the standard error of the mean (`0.004` at 300 seeds)
is reported next to it. Redefining the threshold to make a verdict reachable would
have repeated the original error in the opposite direction.

Two further traps that cost time here, recorded so they cost less next time:
`coupling = 0` makes every level exactly doubly degenerate, so the mean `r`-ratio
is `0`, and such a point carries no class information — it is now excluded from
the grid and kept as a control. And the bounded Davenport–Heilbronn zero scan in
`chirality.py` locates **no** off-line zero up to `t = 40`, which is reported as a
negative result rather than replaced by the literature's claim.

**The "support" was found by violating the hypothesis.** The sharpest measurement to
come out of the correction: violating `[H, sigma] = 0` decouples the two diagonal
blocks, and the superposition then moves *toward* the GUE window rather than away
from it. Measured at `d = 20`, `coupling = 1.0`, 60 seeds per row:

| `sigma`-violation | mean `r` (full spectrum) | draws inside `[0.58, 0.62]` |
|:---|---:|---:|
| `0.0` (intact) | `0.4125` | `0.00` |
| `2.0` | `0.5192` | `0.05` |
| `5.0` | `0.5369` | `0.17` |

The pre-correction grid's best point had `symmetry_breaking = 2.0`. So the region
that produced "DSH is SUPPORTED" is the region in which requirement 1 of the
Dimension-Shift Hypothesis fails: the model was not tested, it was broken in the
direction that makes the statistic look right. That is now a test
(`test_breaking_the_hypothesis_moves_the_statistic_toward_the_gue_window`) and a
section of `output/falsification_summary.txt` rather than a remark.

**Independent replication, and the finite-size test that settles it.** The same four
findings were re-measured by a reviewer on a separate checkout, and every number
agrees: `||[H, sigma]||/||H|| = 1.42`, `GOE 0.532 +- 0.005` at `d = 200`, the
`0.6117` point averaging `0.523 +- 0.069` over 300 seeds, and the corrected model
giving `0.43` full-spectrum with `0.527` (real symmetric) and `0.597` (complex
Hermitian) sectors.

The reviewer also ran the check that makes the refutation structural rather than
numerical: the legacy "supported" point at `d = 200` collapses to **`0.5315`**
(sem `0.0034`) -- the GOE value. Reproduced here, the drift is monotone in the
matrix size: `d = 10 -> 0.50`, `d = 50 -> 0.529`, `d = 200 -> 0.532`. A structural
result is stable under `d`; a fluctuation is not.
`test_the_legacy_best_point_regresses_to_goe_as_the_matrix_grows` pins it.

One precision point from the comparison: the reviewer's "23% of seeds land in the
GUE window" is measured with `unfold=False`, while the legacy code used
`unfold=True`, where the figure is `14%`. Both are correct and both are reported;
the fact that the number moves by 60% with a choice the old code never justified is
itself part of why the window was never a criterion.

## 16. M5: the Dimension-Shift Hypothesis Is Abandoned

The roadmap's decisive milestone ran, and the hypothesis did not survive it. Both
defects found on the way are worth recording, because one of them produced a
*favourable* wrong answer.

**The measurement.** 300 seeds per point, `d = 100, 200`, four couplings, both
matrix classes, `||[H, sigma]||_F / ||H||_F = 0` at every point:

| input blocks | sector means | full-spectrum means |
|:---|---:|---:|
| GOE | `0.5279 … 0.5327` | `0.4225 … 0.4248` |
| GUE | `0.5964 … 0.6017` | `0.4199 … 0.4238` |

Criterion (2) holds: GUE blocks give `2/2` GUE sectors and GOE blocks give `0/2`, so
the universality class is **inherited from the input blocks**, not produced by the
`sigma` structure. Criterion (1) holds for the GOE class and fails for the GUE class,
which makes it class-conditional -- a restatement of criterion (2), not independent
evidence. Verdict: **abandoned**, in `docs/m5_verdict.md`.

The structural lesson is compact: a `sigma`-symmetric Hamiltonian built from random
blocks has sectors `spec(A ± C)`, so it inherits the class of `A` and `C`. Carrying
the zeros' class would require *deriving* time-reversal breaking from the
construction -- a specific arithmetic origin for `C` -- instead of choosing it as an
ensemble.

**The defect that exonerated it.** `MATRIX_CLASSES` is `("goe", "gue")`, and the first
draft of criterion (2) assigned `gue_point = points[0]`, i.e. it named the GOE point
"gue" and inverted the verdict. The first full run therefore reported

> GUE blocks -> 0 GUE sectors; GOE blocks -> 2 GUE sectors -- **DSH SURVIVES**

the opposite of the data, and in the direction that acquits the hypothesis. Points are
now keyed by class name and the tests assert `points[i].matrix_class`. A bug that
runs *towards* the hoped-for answer is the one most likely to be believed.

**The defect that hid it in the test suite.** The criteria were originally named
`test_criterion_1` / `test_criterion_2`. pytest collects every module-level name
starting with `test_`, *including imported ones*, so `tests/test_m5_analysis.py` ran
the full default grid twice as if those were tests: about twelve minutes of hidden
computation, and `--collect-only` reported 18 items where 16 exist. Renamed to
`evaluate_criterion_1` / `evaluate_criterion_2`, with
`test_no_imported_symbol_is_collected_as_a_test` as the guard.

**What M5 does and does not settle.** It settles one construction. It does not show
that no dimension-shift idea can work; it shows which assumption has to change, and
names it: the origin of `C`. It produces no evidence for or against the Riemann
hypothesis.

## 17. What the DSH Taught Us (summary)

The full account is [`central_hypothesis.md` §10](central_hypothesis.md) — the
document that proposed the hypothesis now carries its verdict, deliberately, so that
a falsified proposal is readable in the form that was falsified. The constraints it
leaves behind, in one table:

| constraint | why |
|:---|:---|
| **≥ 300 seeds, and report the std** | the original "SUPPORTED" verdict came from one seed; 14% of pure GOE draws landed in its window |
| **test the sector, not the full spectrum** | a `σ`-symmetric spectrum is a superposition of two sectors and lands at `0.37…0.43` for *either* input class; the summary statistic hides the class that the sectors show |
| **a proposal must *produce* the class it claims** | the sectors are `spec(A ± C)`, so they inherit the class of `A` and `C`; `‖[H,σ]‖ = 0` in both cases |
| **criteria must be reachable at the tested sizes** | `std < 0.02` cannot be met at `2d ≤ 200` (measured `0.084`, `0.034`, `0.026`); it was implemented as written and reported as unreachable |
| **evaluate a criterion across the whole admissible family** | criterion (1) holds for GOE blocks and fails for GUE ones, so a single-class verdict would have been circular |
| **document defects next to the verdict** | the first M5 run said *SURVIVES* because of a label swap — the error ran in the direction that acquitted the hypothesis |

Two defects in the analysis, both recorded in [`m5_verdict.md`](m5_verdict.md): the
label swap above, and `test_`-prefixed production functions that pytest collected as
tests, which ran the full grid twice inside the suite.

What survived: the involution and `σ² = id` (proved in Lean), the multi-seed
falsification harness, the verified sector extraction, exact commutation enforcement,
the desymmetrisation detector of §18, and a negative result that is structural rather
than numerical.

## 18. An Instrument Is Not a Measurement

The `σ` structure failed as a proof strategy (§16) and works as a diagnostic. The
distinction is worth stating precisely, because it is the difference between a
contribution and a claim.

**The phenomenon is not ours.** A discrete symmetry splits a spectrum into independent
blocks, and a union of unresolved blocks has less level repulsion than any of its
parts, so `⟨r⟩` falls toward `0.386`. Giraud and co-workers derive gap-ratio
distributions for spectra built from several blocks and use them to infer the block
structure ([Phys. Rev. X **12**, 011006 (2022)](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.12.011006),
[arXiv:2008.11173](https://arxiv.org/abs/2008.11173)); the general point is standard
quantum-chaos practice. The measured table in
[`desymmetrisation.md`](desymmetrisation.md) is that result instantiated for one
`σ`, not new physics.

**What is ours is the sensor, and the record of its failure.** `desymmetrise(H, U)`
verifies the involutions, splits, and compares the full spectrum with the sectors;
`detect_hidden_symmetry` flags a bare spectrum. Both were calibrated against 300-seed
measurements (`0.531`/`0.600` at one sector, `0.426`/`0.421` at two, `0.39–0.40` from
three) and both are wrong often enough to be honest about:

| limit | measured |
|:---|:---|
| it detects, it does not count | the table is many-to-one and the scatter (`≈0.03`) exceeds the gaps between counts; a true `N = 4` was estimated as `12` (reviewer) and saturates or refuses here |
| the count is a property of the estimator | a *known* two-sector spectrum at `d = 40` maps to `None`, because its full mean `0.404` sits in the three-sector band |
| at two sectors the class is erased | GOE `0.426` vs GUE `0.421`, a difference smaller than either standard deviation |
| a pure single sector can be flagged | 4 of 40 GOE draws (10%) at `d = 60` fall below the `0.48` floor; 0 of 40 GUE draws do |

**The second lesson is about utilities, not physics.** A split function that skips its
precondition is worse than no function, because it returns plausible arrays. The
reviewer's `make_sigma_symmetric_hamiltonian` does not commute with its own `σ`
(`‖[H,σ]‖/‖H‖ = 1.14 … 1.18`); their `sector_spectra` diagonalises the involution and
keeps the diagonal blocks, silently discarding the mass that makes them non-sectors.
The version here refuses (`ValueError`, naming the commutator), and the refusal is a
test rather than a docstring promise. The same applies to the `test_`-prefix defect of
§16: a guard that is not driven into failing is a comment.

**What that buys.** A false "Poisson" reading has a specific shape — `⟨r⟩` low, no
analysis of the symmetries — and it is common in many-body simulations, cavity
measurements and operator screening, including this repository's own screening step.
The tool cannot tell symmetry from integrability and does not pretend to; it converts
"the spectrum looks Poisson" into "find the symmetry, or say you cannot distinguish
the two". That is the whole contribution, and it is the contribution an instrument
makes: the physics stays known and the error gets harder to commit silently.

