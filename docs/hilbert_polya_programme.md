# A programme for a Hilbert–Pólya operator: gates, kill criteria, and the first attack

**Status.** The Riemann hypothesis is open. This document is a research programme, not a claim, and
nothing in it asserts that RH is true or that any operator has been found. Its purpose is to make
the search falsifiable in the way this repository requires: each candidate must pass explicit
gates, each failure has a named kill criterion, and the first attack is chosen because its
obstruction is a single, named, provable statement rather than an aspiration.

**What would count as success.** A Hilbert space, a dense domain, a self-adjoint operator `H`, and
a proof of two things: that its spectrum is discrete with eigenvalues `γ_n`, and that a trace
identity holds,
`tr f(H) = Σ_ρ f(ρ)`, whose right-hand side is the arithmetic side of the explicit formula. A
self-adjoint operator has real spectrum, so the first condition gives the real part `1/2` for every
zero in the spectrum; the second gives that the zeros are exactly what the spectrum contains. The
two together are a proof of RH. The route is stronger than RH: RH does not produce such an
operator, so a success settles more than the hypothesis itself.

**Why numerics cannot decide it.** A match of the first `N` eigenvalues to the first `N` zeros is
evidence about `N` numbers. It is not evidence that the spectra agree beyond them, and it is not a
proof that the operator is self-adjoint or that its trace formula holds. Every gate below therefore
requires a statement that quantifies over the whole spectrum.

## 1. The circularity trap, stated first

Two standard routes pass through a positivity statement that is itself equivalent to RH:

- **Weil's criterion.** RH holds if and only if the explicit-formula functional `W(f)` is
  non-negative for every `f` in a declared class. An operator whose quadratic form is `W` is a
  candidate, but proving its positivity *is* proving RH. Assuming positivity because RH is expected
  is circular (kill criterion K6).
- **de Branges spaces.** The route reduces RH to the positivity of a reproducing-kernel metric. The
  reduction is real; the proof of positivity is the open problem.

The programme therefore never scores a candidate as progress when its missing step is "positivity".
The missing step is the work, and the programme must name the class of test functions for which it
is claimed and the argument that proves it without using RH.

## 2. Gates

| gate | requirement | why it is necessary |
|:---|:---|:---|
| G0 specification | a concrete Hilbert space, domain, and operator, with the claimed spectral identity stated | an operator defined only up to a fit cannot be checked |
| G1 self-adjointness | a proof that the operator is self-adjoint on its domain, or that its spectrum is real for a stated reason | otherwise real eigenvalues are an accident, not a theorem |
| G2 spectral identity | a proof that the spectrum equals `{γ_n}` (or a stated subset), not equality of finitely many eigenvalues | finite agreement is not an identity |
| G3 arithmetic input | the construction uses the Euler product or the prime side, in a form that fails for a function with off-line zeros | a construction that only uses the functional equation cannot distinguish RH from a counterexample class |
| G4 formalisation | the theorem chain stated in Lean with the obligation theorems proved | the repository's standard for a mechanical record; optional for a first publication, mandatory before a formal claim |

A candidate is **open** while a gate is unproved, **failed** when a gate is false, and **complete**
when all five are proved. Completion is a submission for independent checking; it is not a
protocol verdict, because the six-term vocabulary has no term meaning "true".

## 3. Kill criteria, with the repository's precedents

| kill | meaning | precedent in this repository |
|:---|:---|:---|
| K1 fitted | parameters are chosen by matching the zeros | the picket-fence box: `r = 1.000` against the zeros' `0.610`, rungs equally spaced while zero spacings run `0.716…6.887`, and a box fitted to 100 zeros predicts `21` levels where there are `10` (`docs/hilbert_polya.md`) |
| K2 statistics only | only spacing statistics match, not the spectrum | the prime-length graph and the "twin" candidate: GUE-like spacings without the zeros (`docs/operator_candidates.md`) |
| K3 non-self-adjoint | the operator is not self-adjoint, or reality of the spectrum is assumed | the PT-symmetric family: real spectrum only below the threshold, and thermal data cannot see the difference (`docs/pt_symmetric_hilbert_polya.md`) |
| K4 transfer | the construction's inputs also hold for a function with off-line zeros, so it cannot establish RH | the Davenport–Heilbronn control of the screening protocol: a construction that uses only the functional equation is positive for DH too |
| K5 finite check | the "proof" is a numerical match to finitely many zeros | every numerical experiment in this repository is reported as evidence about an instance |
| K6 circularity | positivity is assumed, or the operator is built from the zeros themselves | Weil and de Branges routes, as stated in §1 |

K4 is the discriminator that makes this programme different from a spectral-fitting exercise: a
candidate must be tested on a companion function whose analogue of RH is false. If the construction
does not notice the difference, it cannot prove RH.

## 4. Candidate classes, and what each is missing

| class | G0 | G1 | G2 | G3 | status | next computation |
|:---|:---|:---|:---|:---|:---|:---|
| Berry–Keating `H = xp` | defined | open: domain and regularisation | fail: continuous spectrum, no exact zeros | open | open | a self-adjoint regularisation with a discrete spectrum and a proved trace identity |
| Picket-fence box | defined | pass | fail: uniform rungs (`r = 1.000`) | none | **rejected** (K1) | none |
| Prime-length quantum graph | defined | pass | fail: spacings only | partial | **rejected** (K2) | none |
| PT-symmetric family | defined | open: threshold | fail for the constructed examples | none | **rejected** for the tested family (K3) | a family with a proved real spectrum and a zero identification |
| Solvable (supersymmetric) potential | defined | pass | fail: spectra are not the zeros | none | **rejected** (G2) | none |
| Connes / explicit-formula trace | open: operator not constructed | open | open | open: positivity is RH-equivalent | open | write the operator and its quadratic form; name the test class |
| de Branges canonical system | open | open | open | open: positivity is RH-equivalent | open | state the positivity claim for a declared class; prove it without RH |
| Random-matrix / GUE statistics | defined as an ensemble | not applicable | fail | none | **rejected** (K2) | none |

The table is the programme's first result, and it is a negative one: none of the recorded classes
has a live route to G2 and G3. That is the honest starting position, not a reason to stop.

## 5. The first attack: the Weil functional, with the DH control

The explicit formula already has the shape of a trace formula. The programme's first attack is to
treat it as one and to attack its positivity directly, with the DH control built in.

1. **Fix the test class.** Choose a class of functions for which `W(f)` is defined and computable:
   compactly supported, even, with the prime side truncated at a declared bound, and the zero side
   evaluated from a certified list to a declared height. The class and the truncations are declared
   before any search, so a later choice cannot be a fit (K1).
2. **Write the quadratic form.** `W(f) = Σ_p Σ_k (log p) p^{-k/2} (f(k log p) + f(-k log p)) − …`,
   with the archimedean term and the zero side as in the explicit formula. The exact convention is
   fixed in the document that reports the result.
3. **Search for a negative.** For the declared class and truncations, compute `W(f)`. A negative
   value is a refutation of RH by Weil's criterion, not a failed candidate: it is the one outcome of
   this programme that would settle the hypothesis in the negative, and it is checked twice, with a
   tighter truncation, before it is reported.
4. **Build the operator.** If no negative appears, define the Hilbert space on which `W` is the
   quadratic form of a self-adjoint operator. This is the constructive step the literature has not
   completed; the programme treats the quadratic form as the object and the operator as the target.
5. **Apply the DH control.** The same computation on the Davenport–Heilbronn coefficients, whose
   analogue of RH is false. The construction must be positive for the zeros and fail for DH at the
   same class and truncation; if it is positive for both, it is not discriminating (K4) and cannot
   prove RH, whatever its values at the zeros.
6. **Formalise the theorem chain** (G4) once steps 1–5 are written, so the arithmetic and the
   spectral identity are machine-checked rather than quoted.

**Milestone M1.** A written operator/quadratic form, the declared test class and truncations, and
the DH control, with the numerical tables that go with them. M1 is falsified by a single negative
`W(f)` in the declared class (which would refute RH) or by a DH value that is positive at the same
truncation (which would refute the construction's discriminating power).

**Milestone M2.** Positivity of `W` proved for a restricted class (for example, functions whose
Fourier support is bounded away from the pole and the trivial zeros), with the restriction stated.
**M3.** The full declared class. **M4.** Formalisation.

## 6. Stop conditions and review

The programme stops with a negative result if the declared class produces a negative `W` that
survives independent recomputation; it stops with a methodological result if every candidate class
is killed by K1–K6 and the literature adds none; and it stops with a proof candidate at M3, to be
submitted for independent review. None of these is a protocol verdict on RH, and the paper's
standing sentence applies throughout: the Riemann hypothesis remains open until a proof or a
counterexample is accepted.

## 7. Relationship to the evaluation paper

The paper's six-term vocabulary is for claims, not for programmes; this programme generates claims,
and the protocol screens them. The DH screen is the K4 control in miniature. The Lean interface in
`RiemannFramework/NewIdeaTest.lean` states the wall the programme would have to climb: every
non-trivial zero must be a fixed point of the involution. The repository's negative results are the
programme's evidence base, not its conclusion.
