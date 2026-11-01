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

# Desymmetrization of Quantum Spectra: A Bayesian Sector-Count Diagnostic with Measured Coverage

### Methods manuscript: draft for submission

**Status.** Draft complete and reproducible in this repository; not submitted anywhere,
no venue assigned, no peer review. The licence header above is kept for repository
consistency and should be stripped for submission. Corrections made to the previous
draft are listed in ["A note on this draft"](#a-note-on-this-draft), the numbers in the
tables are the measured ones, and where the draft had a figure or a deviation wrong, this
version says what the measurement is.

## Abstract

Spacing statistics are the standard diagnostic for quantum chaos, but they are measured
on a superposition whenever the Hamiltonian commutes with an involution. A spectrum that
appears Poisson-like may instead be a union of unresolved sectors, and the standard mean
gap ratio `⟨r⟩` cannot distinguish the two. We present a diagnostic that verifies the
symmetries, splits the spectrum into joint sectors, flags a contaminated full spectrum, and
estimates the unresolved-sector count as a posterior with measured coverage. The mean
cannot be inverted; the sequence of gap ratios can. A
first-order Markov model fitted on simulated superpositions yields a posterior over
`{1, …, 6, ≥6/poisson}`. At a nominal 95% interval, measured coverage is `0.99`, `0.92`,
`0.91`, `0.96`, `0.98` at `1, 2, 3, 4, 6` sectors and `0.78` for a Poisson spectrum, over
400 spectra per row. The single-sector case is decisive (`p = 0.97`, interval `1..1`); the
two-sector case yields a lower bound (`2`) but not a count, and from three sectors upward
the count is not recoverable, because `3` through `6` are indistinguishable. Two-sector GOE
and GUE are indistinguishable in the full spectrum, and that limit is measured rather than
assumed: the best single-spectrum class accuracy is `0.79` at one sector and `0.53`, which
is chance, at two, while averaging thousands of spectra sharpens the mean to `0.0006` and
leaves the single measurement untouched. The false-positive rate is stated (`37` of `400`
pure single-sector GOE spectra are flagged, `0` of `400` GUE), and the limits are reported
rather than hidden. The companion dynamical analysis shows that the double-bracket flow
preserves sector populations only for a state that commutes with the involution, so the
flow cannot repair a contaminated spectrum.

## 1. Introduction

### 1.1 Problem statement

Quantum chaos is diagnosed by level-spacing statistics. The mean adjacent-gap ratio
`⟨r⟩` takes three reference values:

| class | `⟨r⟩` | meaning |
|:---|---:|:---|
| Poisson | `0.386` | integrable |
| GOE | `0.531` | chaotic, time-reversal symmetric |
| GUE | `0.600` | chaotic, time-reversal broken |

When a Hamiltonian commutes with an involution `σ`, its spectrum is the union of the
spectra of the `σ = ±1` sectors. If the sectors are not resolved, `⟨r⟩` of the full
spectrum is not the class of the Hamiltonian. It is the class of a superposition.

The failure is silent. There is no error message. The number `0.42` looks like a
legitimate measurement. It is wrong, and it is wrong in a specific way: it is exactly
what a two-sector superposition produces.

### 1.2 Origin of the diagnostic

This diagnostic was not designed in the abstract and justified afterwards. It is the
residue of a larger project, and the failure that produced it is the failure it detects.

The project began with a candidate operator for the Riemann hypothesis. The map
`σ(s) = 1 − conj(s)` reflects the complex plane about the critical line; its fixed locus
is exactly `Re(s) = 1/2`; and a Hamiltonian built around this involution was proposed as a
route to the zeros. That proposal, the dimension-shift hypothesis, was tested against
criteria it had set for itself and was abandoned. The decisive run found that the sector
class of a `σ`-symmetric Hamiltonian is inherited from the input blocks, not produced by
the `σ` structure: GOE sectors at `0.528 … 0.533`, GUE sectors at `0.596 … 0.602`, but a
full spectrum at `0.420 … 0.425` for either input. The verdict is recorded in the
repository, in the document that proposed the hypothesis, and it is final.

Two mistakes made on the way are the subject of this paper. The first was statistical: a
single seed of a 90-point grid once reported "supported", and 300 seeds with error bars
showed that the value was noise (`0.523 ± 0.069`). The second was structural, and it is
the one that matters here: the model's universality class was tested on the full spectrum
of a `σ`-symmetric Hamiltonian, and a GOE model appeared to reach GUE statistics. The
apparent GUE class was not a property of the model. A Hamiltonian that commutes with an
involution has a spectrum that is the union of its sector spectra, and that union has a
mean gap ratio of about `0.42` for either input class. The class was being read from a
superposition.

Neither error was a bug in one codebase. Both are ways of reading a property from a
sample that does not carry it. This paper makes the structural one visible, measures when
the information is and is not recoverable, and states the limits.

### 1.3 Measured dependence on the number of unresolved sectors

At 4000 seeds per point, `60` levels per sector, the full-spectrum `⟨r⟩` depends on the
number of unresolved sectors (Fig. 1):

| unresolved sectors | GOE blocks | GUE blocks |
|:---|---:|---:|
| 1 | `0.530` | `0.599` |
| 2 | `0.423` | `0.422` |
| 3 | `0.404` | `0.400` |
| 4 | `0.396` | `0.393` |
| 6 | `0.391` | `0.389` |

Each entry is the mean over `4000` simulated spectra and carries a standard error of at
most `0.0007`, which is three decimal places of real information. The per-spectrum
scatter at the same points is `0.017` to `0.039` (Appendix A), that is twenty-five to sixty
times the standard error of the mean. The whole argument of Section 1.4 rests on that
ratio.

Two facts follow:

- **At three or more sectors, `⟨r⟩` is inside the Poisson window** `[0.36, 0.41]`. A
  researcher who measures `0.39` and concludes "integrable" is wrong, and the standard
  test gives no indication.
- **At two sectors the class is erased.** `0.4232` against `0.4222` is a gap of `0.0010`,
  which is `1.4` standard errors of the two means, and one thirtieth of the per-spectrum
  scatter of `0.031`. A class test on a two-sector full spectrum is uninformative, not
  merely noisy: averaging more spectra cannot rescue it, and Section 1.4 measures why.

![Fig. 1. Full-spectrum mean adjacent-gap ratio against the number of unresolved independent sectors, at 4000 seeds per point and 60 levels per sector. GOE input blocks (circles) and GUE input blocks (squares). Reference values are marked: Poisson 0.386, GOE 0.531, GUE 0.600. The shaded band is the Poisson window [0.36, 0.41]; from three sectors upward the full spectrum lies inside it.](output/desymmetrisation.png)

### 1.4 Statistical resolution of the diagnostic

The table above is an average over thousands of spectra, and a measurement is one
spectrum. The two are different questions, and the diagnostic is only useful for the
second, so the resolution of the statistic is measured rather than assumed (Fig. 2).

**What more spectra buy.** Fig. 2(a) repeats the two-sector measurement on nested samples
of `25` to `3200` spectra per class:

| spectra per class | GOE `⟨r⟩` | GOE 95% error | GUE `⟨r⟩` | GUE 95% error |
|:---|---:|---:|---:|---:|
| 25 | `0.4332` | `0.0119` | `0.4145` | `0.0144` |
| 100 | `0.4284` | `0.0061` | `0.4139` | `0.0067` |
| 400 | `0.4253` | `0.0030` | `0.4208` | `0.0032` |
| 1600 | `0.4241` | `0.0015` | `0.4227` | `0.0016` |
| 3200 | `0.4231` | `0.0011` | `0.4227` | `0.0011` |

Three things are visible in it. The mean **converges**: the GUE value moves from
`0.4145` at 25 spectra to `0.4227` at 3200, so 25 spectra are off by `0.008` and 100
spectra still carry a 95% error of `0.007`. The 95% error **shrinks as the sample grows**:
128 times the
spectra (25 to 3200) reduces the GUE error by a factor of `12.6` and the GOE error by
`11.0`, either side of the `11.3` expected from the inverse square root of the sample size.
The per-spectrum scatter **does not move**: `0.0305` to `0.0330` for GUE at every sample
size, because it is a property of one spectrum and not of the sample.

**What that means for one spectrum.** Fig. 2(b) superimposes the two per-spectrum
distributions at two sectors, `4000` spectra per class, and measures the best a single
threshold on `⟨r⟩` can do. The answer is `0.526` balanced accuracy against the chance
value `0.500`: the two-sector classes are interchangeable one spectrum at a time. The same
measurement at one sector, where the classes are `0.530` and `0.599`, gives `0.790`.

The two results are consistent and they are not in tension. In the 4000-spectrum table of
Section 1.3 the two-sector class gap is `0.0010`, `1.4` standard errors; in the nested
series of Fig. 2 at 3200 spectra it is `0.0004`, `0.5` standard errors. Neither is a
measurement of a class difference: both are consistent with zero, and both are one
thirtieth of the scatter that one spectrum carries. **More spectra sharpen the mean and
leave the single measurement untouched.** That is why the diagnostic resolves the symmetry
structurally, by splitting the spectrum into sectors, instead of averaging harder
statistically: the averaging route is bounded by the overlap of the distributions, not by
the number of spectra, and this paper measures the bound.

![Fig. 2. Resolution of the mean gap ratio at two sectors. (a) Mean r on nested samples of 25 to 3200 spectra per class, with the 95% error of the mean as error bars and the per-spectrum scatter as a shaded band; the mean converges and its error falls with the sample size, while the band does not move. (b) The two per-spectrum distributions at 4000 spectra per class, superimposed, with the best single-threshold balanced accuracy annotated (0.526 at two sectors, chance 0.500; 0.790 at one sector, for comparison).](output/desymmetrisation_seeds.png)

### 1.5 Contribution and scope

We provide a diagnostic that:

1. verifies that the proposed involutions commute with `H` and with each other, and
   refuses the split when they do not;
2. splits the spectrum into joint sectors, and reports the sector means against the
   full-spectrum mean;
3. warns when a full spectrum is contaminated by an unresolved symmetry, with a measured
   false-positive rate of `37` of `400` for GOE and `0` of `400` for GUE single-sector
   spectra at `d = 60` (Appendix C);
4. estimates the number of unresolved sectors as a posterior whose interval coverage is
   measured at `400` spectra per row: `0.99`, `0.92`, `0.91`, `0.96`, `0.98` at
   `1, 2, 3, 4, 6` sectors and `0.78` for a Poisson spectrum (Appendix B);
5. measures the resolution of the statistic it uses: the best single-spectrum class
   accuracy is `0.790` at one sector and `0.526`, that is chance, at two (Section 1.4);
6. reports the limits: the mean cannot be inverted, the count is not recoverable above
   two sectors, two-sector GOE and GUE are indistinguishable in the mean as well as in one
   spectrum, and more spectra do not change that.

The phenomenon is standard quantum-chaos practice (Giraud et al. [1]). What is local is
the table measured at 4000 spectra per point to a standard error of `0.0007`, the entry
points, the posterior's measured coverage, the measured resolution of the single-spectrum
statistic, and the recorded limits.

## 2. Static desymmetrization diagnostic

### 2.1 Verification of the involutions and joint-sector decomposition

Given a Hamiltonian `H` and a set of involutions `{U₁, …, Uₖ}`:

* **Step 1: verify.** Check `[H, Uᵢ] = 0` for every `i`, and `[Uᵢ, Uⱼ] = 0` for every
  pair. If a commutator is nonzero the split is invalid, and the diagnostic refuses to
  proceed rather than returning a plausible-looking decomposition.
* **Step 2: diagonalize the involution group.** The involutions generate `(ℤ₂)ᵏ`;
  diagonalize each `Uᵢ` and group the simultaneous eigenspaces.
* **Step 3: split.** Project `H` onto each joint eigenspace and diagonalize the block.
* **Step 4: validate.** For the `σ` case the sectors are `spec(A + C)` and `spec(A − C)`;
  that identity is checked against the blocks, not assumed. For a `ℤ₂ × ℤ₂` the four
  sectors are checked against a direct sum built from four known blocks.

The refusal in Step 1 is not a formality. A split routine that skips it returns arrays
that are not sector spectra, and the error is invisible downstream: the reviewer-supplied
fixture for this family of utilities measures `‖[H, U]‖/‖H‖ = 1.14 … 1.18` and its split
discards exactly the mass that makes the blocks non-sectors.

### 2.2 Contamination detection from a single spectrum

Two entry points cover a caller that has only a spectrum:

* `contamination_warning(H, U)`: when a candidate involution is known. It verifies the
  commutation, splits, and compares the full spectrum with the resolved sectors. This is
  the reliable half: the comparison is within one Hamiltonian and needs no calibration.
* `detect_hidden_symmetry(eigenvalues)`: when no involution is known. It computes the
  full-spectrum `⟨r⟩` and flags a value below the single-sector floor.

The flag is not a classifier (Fig. 3). `37` of `400` pure single-sector GOE spectra at
`d = 60` also fall below the floor, a rate of `9.2%` with a 95% binomial interval of
`6.6%` to `12.6%`, and `0` of `400` GUE spectra do (Appendix C). The rate is that high
because the one-sector GOE value is `0.530` with a per-spectrum scatter of `0.039`, and
the floor is `0.48`: a third of a distribution width below the mean is a tenth of the
distribution. A low `⟨r⟩` is also what an integrable system produces. Spacing statistics
cannot separate the two, and the warning says so in its own text.

![Fig. 3. Distribution of the full-spectrum mean gap ratio for four sector counts and both block classes, one dot per simulated spectrum (4000 per point), with the per-point mean marked. The Poisson window is shaded, the flag threshold (0.48) and the severe-contamination boundary (0.46) are drawn. At two sectors the GOE and GUE clouds coincide, so a class test on the full spectrum is uninformative rather than noisy.](output/desymmetrisation_warning.png)

### 2.3 Bayesian estimation of the sector count

The mean `⟨r⟩` cannot be inverted. The sequence of `≈240` gap ratios can be.

The reason is information. The mean collapses about 240 ratios into a single number, and
the collapse is many-to-one: a three-sector and a six-sector superposition both land near
`0.39`, so no function of the mean can tell them apart. The sequence keeps the ratios
themselves, and the way one ratio follows the next carries the sector count that the mean
discards.

**Model.** A first-order Markov model of the sequence,

```
r_{n+1} | r_n ~ f(r_{n+1} | r_n; k),
```

where `k` is the number of unresolved sectors, restricted to `k = 1, …, 6`, plus a
Poisson hypothesis standing for "integrable, or more sectors than are distinguishable
from it". Concretely, the ratios are placed on a fixed grid of bins, and for each
hypothesis the conditional frequency `f(r_{n+1} | r_n; k)` is estimated by counting
transitions between bins across 200 simulated superpositions per hypothesis. The block
class is marginalised at equal weight, so the posterior answers only the question asked:
how many sectors, not what class.

**Why first order?** Modelling the ratios as independent is measurably overconfident:
coverage `0.70` at a nominal `0.90`, because consecutive ratios share a spacing and the
independent product counts the same information twice. The first-order chain is the
smallest model that keeps the dependence, and the coverage of the resulting interval is
measured rather than assumed.

**Output.** A posterior over `{1, 2, 3, 4, 5, 6, ≥6/poisson}` and the shortest contiguous
interval carrying 95% of its mass. The open label exists so that the estimator is
*allowed* to say "not a finite superposition"; it does not claim to distinguish seven
sectors from an integrable spectrum.

### 2.4 Measured coverage of the credible interval

At a nominal 95% interval, over 400 spectra per row (Fig. 4):

| true sectors | coverage | posterior on the truth | modal interval | `P(lower ≥ 3)` |
|:---|---:|---:|:---|---:|
| 1 | `0.99` | `0.97` | `1..1` (376 of 400) | `0.00` |
| 2 | `0.92` | `0.66` | `2..2` (146 of 400) | `0.08` |
| 3 | `0.91` | `0.24` | `3..≥6` (138 of 400) | `0.60` |
| 4 | `0.96` | `0.19` | `3..≥6` (166 of 400) | `0.80` |
| 5 | `0.99` | `0.22` | `3..≥6` (166 of 400) | `0.85` |
| 6 | `0.98` | `0.22` | `3..≥6` (174 of 400) | `0.90` |
| Poisson | `0.78` | `0.24` | `3..≥6` (150 of 400) | `0.94` |

Reading the table:

* **One sector is decisive.** `p = 0.97` on the truth, interval `1..1` in 376 of 400
  draws, and the posterior on `1` is below `0.001` for every other truth, Poisson
  included.
* **Two sectors is bounded below, not counted.** The lower end of the interval is `2` in
  92% of draws, but the upper end ranges from `2` (146 of 400 draws) to the open label
  and beyond, so "at least two" is defensible and "exactly two" is not. The posterior on
  the truth is `0.66`.
* **Three or more is not counted.** The posterior reports `≥3`, and `3` through `6` are
  indistinguishable. The probability that the lower end is at least `3` rises with the
  truth (`0.60, 0.80, 0.85, 0.90` at `3, 4, 5, 6`), which is a weaker and more useful
  statement than a point estimate.
* **Poisson is the hard row.** The lower end is at least `3` in 94% of draws, so an
  integrable spectrum is described as a superposition of three or more sectors, because
  that is what it looks like. Its coverage, `0.78`, is the honest number for the row: in
  the other `0.22` of draws the interval excludes the open label, and that residual is
  the false-positive rate of the posterior.

![Fig. 4. Measured coverage of the sector-count posterior at a nominal 95% interval, 400 spectra per row, against the nominal level (dashed). The open-ended label is the hard row: an integrable spectrum is covered by its own label in only 0.78 of draws, so in 0.22 of draws the posterior reports a finite count, and that residual is also its false-positive rate.](output/desymmetrisation_coverage.png)

## 3. Symmetry dynamics under the double-bracket flow

### 3.1 Definition of the flow

The multi-copy imaginary-time circuits are built on the double-bracket flow

```
dρ/dβ = [[ρ, H], ρ] = 2ρHρ − Hρ² − ρ²H.
```

This flow has a property the static analysis does not: it preserves the sector structure
when the state commutes with the involution.

### 3.2 Isospectrality and preservation of the sector populations

Measured over `β = 15` with RK4 at 3000 steps:

| quantity | drift |
|:---|---:|
| spectrum of `ρ` | `3e-12` |
| trace | `1.3e-15` |
| non-Hermiticity | `2.8e-17` |
| sector populations, when `[ρ, σ] = 0` | `< 1e-8` |

The populations panel of Fig. 5(a) uses a state with equal mass in the two sectors that
is *not* an eigenstate of `H` (`‖[ρ, H]‖ = 1.46`): the flow does real work on it and the
populations still do not move.

### 3.3 Sector selection from a non-invariant state

When the state does not commute with `σ`, the flow drives it into a single sector:

| quantity | before | after |
|:---|---:|---:|
| coherence `‖[ρ, σ]‖` | `1.41` | `3e-3` |
| populations | `(0.50, 0.50)` | `(1.00, 0.00)` |

The flow selects a sector rather than preserving one. This is a measured behaviour of
the flow, not a claim in the sources, and it is the opposite direction from the
invariance row: from an asymmetric start the flow does not break the symmetry, it
*creates* it.

![Fig. 5. Sector populations under the double-bracket flow for (a) a state that commutes with the involution and (b) one that does not. Panel (a): populations (0.50, 0.50) are preserved to rounding error while the state itself evolves (the initial state is not an eigenstate of H). Panel (b): the coherence falls from 1.41 to 3e-3 and the population is driven to (1.00, 0.00). The flow is isospectral in the state and never acts on the Hamiltonian.](output/desymmetrisation_flow.png)

### 3.4 The flow cannot repair a contaminated spectrum

In neither case does the flow touch the Hamiltonian. `H` is an input, the state is the
variable, and the flow is isospectral in the state. The class is a property of `H`, and
`H` never evolves. The flow cannot repair a contaminated spectrum, and no amount of
imaginary-time evolution changes the number `⟨r⟩` of a fixed Hamiltonian.

That is a precise statement of what the flow can and cannot do. It is the kind of limit
that makes a tool trustworthy.

### 3.5 Machine-checked invariance of the commutant

The invariance step is machine-verified in
`lean/RiemannFramework/DynamicalDesymmetrisation.lean`:

* `commute_doubleBracketIncrement`: if `ρ` and `H` commute with an involution, then so
  does the double-bracket increment;
* `commute_euler_step`: the same holds for one Euler step.

Both are `sorry`-free and depend only on `propext`, checked by `#print axioms`.

## 4. Non-reproduction of a quoted multi-copy identity

The literature's description of the multi-copy imaginary-time circuits quotes an identity
for the first-order term:

```
Tr₂(u ρ₁ ⊗ ρ₂ u†) = ρ₁ − ε[[ρ₁, H], ρ₁] + O(ε^{3/2}).
```

We tested it against the three natural generators (`exp(i√ε(H₁ − H₂))`, the same with a
swap inserted, and the Trotter split of the two phases) by fitting
`ρ(ε) = ρ + √ε A + ε B + …` from three scales. In every case:

* the first-order term is **not** zero: it is `A = i[H, ρ₁]`, which the identity does
  not have;
* the second-order term is **not** `±[[ρ₁, H], ρ₁]`.

The identity is therefore recorded as **unverified from the description available**, not
as confirmed and not as refuted: the generator that makes the first-order term vanish is
a property of the circuit, and the circuit was not read. Recording the discrepancy is the
correct response; assuming the identity and building on it would not be.

## 5. Limitations and scope

| limit | measured | consequence |
|:---|:---|:---|
| the mean cannot be inverted | the table is many-to-one and the scatter exceeds the gaps between counts | the posterior must use the sequence, not the mean |
| two-sector GOE/GUE indistinguishable | `0.4232` vs `0.4222`, `1.4` standard errors of the two means | a class test on a contaminated spectrum is uninformative |
| more spectra do not fix the two-sector class test | best single-spectrum balanced accuracy `0.526` at 4000 spectra per class | the diagnostic must split the spectrum, not average it |
| the count is not recoverable above two | `3…6` indistinguishable | report `≥3`, not a number |
| false positive at the floor | `37` of `400` GOE, `0` of `400` GUE | the flag is a hint, not a decision |
| Poisson read as a finite superposition | coverage `0.78`, so a finite count in `0.22` of draws | an integrable spectrum looks contaminated about a fifth of the time |
| the flow cannot repair contamination | `H` is an input | the class is a property of `H`; `H` does not evolve |
| the model is a plug-in fit | 200 spectra per hypothesis | the coverage is measured rather than asserted, and under-covers at two and three sectors (`0.92`, `0.91`) |

## 6. Comparison with explicit desymmetrization

The standard alternative is explicit desymmetrization: find the symmetry,
block-diagonalize, analyse the blocks.

| method | cost | when it applies |
|:---|:---|:---|
| explicit | one block-diagonalization | the symmetry is known |
| implicit (this diagnostic) | one eigenvalue spectrum | the symmetry may be unknown |

The implicit test is cheaper but coarser. It flags contamination when the symmetry is
unknown; it does not replace explicit desymmetrization when the symmetry is known. When
the symmetry is known, the explicit route also gives the class of each sector, which the
implicit route cannot recover at two sectors.

The rule is the title of the document: **desymmetrize before testing the class.**

## 7. Reproducibility

### 7.1 Software and commands

Every number, table and figure in this paper is produced by the *Riemann Framework*
repository, released under the GNU General Public License v3.0 and available at

    https://github.com/mixic/riemann-framework

The repository is a Python package (`python/riemann_framework`) with a command-line
script layer (`scripts/`) and a test suite (`python/tests/`). Three modules carry the
results of this paper:

| module | what it provides |
|:---|:---|
| `python/riemann_framework/statistics.py` | the gap ratio `r_ratio` and its mean, computed without unfolding |
| `python/riemann_framework/desymmetrisation.py` | the split (`desymmetrise`, `sector_blocks`), the two warnings, the calibration table and the sector-count posterior (`sector_count_posterior`) |
| `python/riemann_framework/dynamical_desymmetrisation.py` | the double-bracket flow, its invariants, and the multi-copy circuit check of Section 4 |

Four commands regenerate the paper's content. They are run from the repository root and
write into `output/`:

| command | what it produces |
|:---|:---|
| `python scripts/run_desymmetrisation_demo.py` | Fig. 1 and the 4000-seed calibration table, printed |
| `python scripts/generate_desymmetrisation_figures.py` | Figs. 2 to 4 and the coverage table, printed |
| `python scripts/run_dynamical_desymmetrisation_demo.py` | the flow trajectory and the circuit-expansion table (a working demo, not a manuscript figure) |
| `python scripts/build_manuscript_pdf.py` | this paper as a PDF |

The figures are not drawn from stored numbers. Every point is computed when the script
runs, so the scripts and the tests, rather than the image files, are the record of the
measurement; a figure that could not be regenerated would be an assertion, not evidence.

The test suite is run from the `python/` directory, and each file pins one part of the
paper:

```bash
cd python
python -m pytest tests/test_desymmetrisation.py -v            # split, table, posterior
python -m pytest tests/test_dynamical_desymmetrisation.py -v  # the flow
python -m pytest tests/test_desymmetrisation_figures.py -v    # the figures
python -m pytest tests/ -q                                    # the whole repository
```

The PDF itself is built by `scripts/build_manuscript_pdf.py` and checked by
`scripts/verify_pdf.py`, which reads the built file back and asserts its page count, its
figure placement, its text layer and the absence of build artefacts. `scripts/build_and_verify.py`
runs the two in sequence and stops at the first failure.

### 7.2 Computational environment

Measured on the machine that produced the tables:

| component | version |
|:---|:---|
| Python | `3.14.7` |
| NumPy | `2.5.3` |
| matplotlib | `3.11.2` (figures only) |
| pytest | `9.1.1` |
| mpmath | `1.3.0` (not used by these modules; used elsewhere in the repository) |

SciPy is installed in the development environment but is **not** used by the
desymmetrisation or dynamical modules; no result here depends on it.

### 7.3 Data and figure files

The measured table, the coverage table and the false-positive rate are produced by
`scripts/generate_desymmetrisation_figures.py` and pinned by
`tests/test_desymmetrisation_figures.py`. The resolution figure is produced by
`scripts/generate_seed_study_figure.py` and pinned by the same test file. Every number in
the figures is computed at draw time; none is typed into the plotting code.

| figure | file | contents |
|:---|:---|:---|
| Fig. 1 | `output/desymmetrisation.png` | `⟨r⟩` against unresolved sectors, 4000 seeds per point |
| Fig. 2 | `output/desymmetrisation_seeds.png` | nested samples, and the two-sector overlap |
| Fig. 3 | `output/desymmetrisation_warning.png` | one dot per spectrum, four sector counts, both classes, Poisson window, both thresholds |
| Fig. 4 | `output/desymmetrisation_coverage.png` | measured coverage against the nominal 95% level |
| Fig. 5 | `output/desymmetrisation_flow.png` | sector populations under the flow, commuting and cross-sector starts |

These five files, the scripts that produce them and the tests that pin them are all
versioned in the repository named in Section 7.1, at
`https://github.com/mixic/riemann-framework`, together with the Lean development
referred to in Section 3.5. No external data set is used: the spectra are generated from
the seed sequence fixed in the scripts, so a fresh checkout reproduces the tables and
the figures without further input.

## 8. Relation to prior work

| reference | contribution | what this adds |
|:---|:---|:---|
| Giraud et al. [1] | the phenomenon: superpositions bias spacing statistics | the measured table, the entry points, the posterior, the coverage |
| Rosenzweig–Porter [3] | block superpositions in random-matrix theory | the diagnostic form, not the theory |
| Mehta [2] | the reference distributions | the calibration values |
| Atas et al. [5] | the `r`-ratio as a statistic | the inversion attempt and its measured failure |

The phenomenon is not new. The instrument is.

## 9. Conclusion

A spacing statistic measured on a Hamiltonian that commutes with an involution is
measured on a superposition. The standard `⟨r⟩` cannot distinguish a Poisson spectrum
from a union of unresolved sectors, and the failure is silent.

We provide a diagnostic that verifies the symmetries, splits the spectrum, flags
contamination, and estimates the sector count as a posterior with a measured coverage.
The single-sector case is decisive; the two-sector case is bounded below but not counted;
from three sectors upward the count is not recoverable. Two-sector GOE and GUE are
indistinguishable, in one spectrum and in the mean of thousands. The false-positive rate
is stated. The limits are reported rather than hidden.

The measurement that decides how the tool may be used is the resolution, not the
precision: 4000 spectra per point determine the mean to `0.0007`, and the best
single-spectrum class test at two sectors is still `0.526`, which is chance. Averaging
buys a better-known ensemble; it does not buy a classifiable spectrum. The instrument
therefore resolves the symmetry, and the number it reports is a flag rather than a
classifier.

The companion dynamical analysis shows that the double-bracket flow preserves sector
populations when the state commutes with the involution, but selects a sector when it
does not, so the flow cannot repair a contaminated spectrum, because the class is a
property of the Hamiltonian and the Hamiltonian does not evolve.

The rule is simple: desymmetrize before testing the class.

The diagnostic began as a mistake made on a candidate operator; it ends as a tool that
makes that mistake visible, measurable, and stated.

## 10. Technical applications and outlook

The diagnostic is a software method, and a method is not a device. This section states,
as an outlook, how the three measured things in this paper (the split, the posterior, and
the flow) assemble into a physical instrument. It is a technical description, not a
patent claim: no application is filed or pending, nothing here asserts patentability, and
what an office would grant is a matter for a patent attorney and depends on the
jurisdiction.

### 10.1 A symmetry-aware spectrum analyzer

| component | technical function | what it uses here |
|:---|:---|:---|
| signal acquisition | measure the energy spectrum of a sample, for instance a quantum dot array, a microwave cavity, or a material | the input spectrum |
| symmetry verification | test whether the spectrum commutes with a candidate involution, such as a spatial symmetry of the sample | `desymmetrise(H, involutions)` |
| sector splitting | project into joint eigenspaces once the symmetry is verified | the `spec(A ± C)` identity and the `Z₂ × Z₂` split |
| posterior engine | estimate the number of unresolved sectors from the gap-ratio sequence | `sector_count_posterior` |
| output | emit a contamination flag, or a posterior over the sector count | the `severe` / `mild` / `none` warning |

The problem the instrument solves is the failure mode of this whole manuscript. An
analyzer that reports one number, `⟨r⟩`, can label a chaotic system integrable when a
symmetry is unresolved. The instrument replaces the number with a verdict and a posterior
whose coverage is measured rather than assumed.

### 10.2 A quantum-processor calibration system

A processor, for instance a superconducting qubit array, can sit in a symmetry-protected
regime whose spectrum looks integrable, and control pulses calibrated against that
spectrum are wrong. The device reads the spectrum, applies the diagnostic, and, on a
contaminated result, drives a symmetry-breaking perturbation to resolve the sectors
before re-measuring. The technical effect is control fidelity; the algorithm is the means.

### 10.3 A double-bracket flow controller

The flow `dρ/dβ = [[ρ, H], ρ]` preserves or selects a sector, as measured in §3. A
controller that implements the flow and monitors the coherence `‖[ρ, σ]‖` can stop the
evolution when the wrong sector is being selected, instead of discovering it after the
prepared state is wrong.

### 10.4 Application domains

Three settings give the instrument its technical effect.

* **Quantum simulation and many-body systems.** A simulator that is meant to be chaotic
  but sits in a symmetry-protected sector can be misread as integrable; the flag and the
  posterior catch the misreading before it is published.
* **Microwave billiards and cavity measurements.** A cavity whose resonance spectrum is
  contaminated by a geometric symmetry (a mirror plane, a rotation) has a `⟨r⟩` that sits
  in the Poisson window; the diagnostic says "resolve the symmetry" instead of
  "integrable".
* **Quantum dots and materials spectroscopy.** A measured single-particle spectrum of a
  dot array or a material sample is a superposition whenever the sample carries a spatial
  symmetry; the posterior bounds how many sectors are unresolved.

In each case the output is not a new theory. It is a control on an old one: a number that
would otherwise have been trusted is replaced by a number together with its provenance (a
resolved sector or an unresolved superposition) and its uncertainty.

### 10.5 Scope of the claims

* the algorithm itself (a Bayesian posterior over sector counts);
* a numerical simulation with no physical input or output;
* the mathematics of Sections 2 through 4.

A granted patent claims a physical embodiment and a technical effect, not these. The
path from this outlook to a filed application runs through a patent attorney; the cost is
on the order of several tens of thousands of dollars across the major jurisdictions, and
the first step is a consultation rather than a filing. This manuscript makes no patent
claim and no assertion about what any office would grant.

## Appendix A: The full measured table

At 4000 seeds per point, `60` levels per sector, with the per-spectrum standard deviation
of the mean `⟨r⟩`:

| sectors | GOE `⟨r⟩` | GOE std | GUE `⟨r⟩` | GUE std |
|:---|---:|---:|---:|---:|
| 1 | `0.5297` | `0.0393` | `0.5993` | `0.0374` |
| 2 | `0.4232` | `0.0312` | `0.4222` | `0.0329` |
| 3 | `0.4035` | `0.0250` | `0.3997` | `0.0246` |
| 4 | `0.3964` | `0.0213` | `0.3932` | `0.0209` |
| 6 | `0.3909` | `0.0174` | `0.3890` | `0.0172` |

The standard error of each mean is the standard deviation divided by the square root of
`4000`, that is by `63.2`, so no entry is uncertain by more than `0.0007`.

The two-sector gap between classes (`0.0010`) is `1.4` standard errors of the two means
and one thirtieth of either standard deviation, which is the quantitative form of "the
class is erased". Adding spectra does not change it: Section 1.4 measures the same gap on
a nested series from 25 to 3200 spectra, and it stays consistent with zero at every
sample size.

## Appendix B: The coverage table

At a nominal 95% interval, 400 spectra per row:

| true sectors | coverage | posterior on the truth |
|:---|---:|---:|
| 1 | `0.99` | `0.97` |
| 2 | `0.92` | `0.66` |
| 3 | `0.91` | `0.24` |
| 4 | `0.96` | `0.19` |
| 5 | `0.99` | `0.22` |
| 6 | `0.98` | `0.22` |
| Poisson | `0.78` | `0.24` |

The Poisson row is the false-positive rate of the posterior: in `0.22` of draws the
interval excludes the open label and reports a finite count, which is the failure mode the
table exists to expose.

## Appendix C: The false-positive rate

| test | result |
|:---|:---|
| pure single-sector GOE spectra below the floor, `d = 60` | `37` of `400` |
| pure single-sector GUE spectra below the floor, `d = 60` | `0` of `400` |
| false-positive rate, GOE | `9.2%`, 95% interval `6.6%` to `12.6%` |
| false-positive rate, GUE | `0%`, 95% upper bound `0.75%` |

The floor is `0.48`, not the reference value `0.531`, because the measured one-sector GOE
value at `d = 60` is `0.5297` with a per-spectrum scatter of `0.0393`: the floor sits `1.3`
standard deviations below that mean, which is precisely why `9.2%` of pure GOE spectra are
flagged. A floor raised to the reference value would exchange those false positives for
missed contamination, and the trade is the user's, so the rate is stated rather than
tuned. The GUE side is quiet because its one-sector value is `0.5993`, nearly two
standard deviations above the floor.

## A note on this draft

The previous draft of this manuscript was assembled from the implementation and contained
several defects that this version corrects. They are listed because a manuscript whose
numbers cannot be traced is not reproducible, and because the corrections are part of the
record rather than an embarrassment to be quietly removed.

| defect in the draft | correction here |
|:---|:---|
| Appendix A quoted standard deviations `≈0.005, 0.008, 0.008, 0.007` | the measured values are `0.0393, 0.0312, 0.0250, 0.0213, 0.0174` (GOE) and `0.0374, 0.0329, 0.0246, 0.0209, 0.0172` (GUE): the draft understated the scatter by four to eight times, which matters because the two-sector gap is compared against it |
| Fig. 1 was named `output/desymmetrisation_table.png` | the file is `output/desymmetrisation.png` |
| Fig. 4 was to be drawn from a hardcoded list of coverage values | it is computed by `SectorCountModel.coverage(draws=400)` at draw time |
| Fig. 5 was to be drawn from a fitted exponential curve matching two endpoints | it is the integrated flow, RK4 at 3000 steps |
| the environment was given as Python `3.12`, NumPy `≥1.26`, SciPy `≥1.11` | measured: Python `3.14.7`, NumPy `2.5.3`, matplotlib `3.11.2`; SciPy is not used by these modules |
| the commands were `cd python` then `python scripts/…` | the scripts live at the repository root, so the figures are generated from the root and the tests are run from `python/` |
| the coverage table omitted the five-sector row | it is included (`0.99`), because the figure shows it and a table that hides a row the figure displays is worse than a longer table |
| `p(true)` for `3, 4, 6` was left blank | the measured values are `0.24, 0.19, 0.22`, all low, which is the point of those rows |

## References

1. Giraud, O. et al. *Probing symmetries of quantum many-body systems through gap ratio
   statistics.* Phys. Rev. X **12**, 011006 (2022); arXiv:2008.11173.
2. Mehta, M. L. *Random Matrices.* 3rd ed., Elsevier (2004).
3. Rosenzweig, N. and Porter, C. E. *"Repulsion of energy levels" in complex atomic
   spectra.* Phys. Rev. **120**, 1698 (1960).
4. Bohigas, O., Giannoni, M.-J. and Schmit, C. *Characterization of chaotic quantum
   spectra and universality of level fluctuation laws.* Phys. Rev. Lett. **52**, 1 (1984).
5. Atas, Y. Y., Bogomolny, E., Giraud, O. and Roux, G. *Distribution of the ratio of
   consecutive level spacings in random matrix ensembles.* Phys. Rev. Lett. **110**,
   084101 (2013).
6. Oganesyan, V. and Huse, D. A. *Localization of interacting fermions at high
   temperature.* Phys. Rev. B **75**, 155111 (2007).
7. Davenport, H. and Heilbronn, H. *On the zeros of certain Dirichlet series I, II.*
   J. London Math. Soc. **11**, 181–185, 307–312 (1936).

## Disclaimer

This manuscript describes a diagnostic instrument, not a result about the Riemann
hypothesis. The phenomenon it addresses, that unresolved symmetries bias spacing
statistics toward Poisson, is standard quantum-chaos practice. What is local is the
measured table, the entry points, the posterior's measured coverage, and the recorded
limits.

The diagnostic detects contamination. It does not count sectors reliably above two, and
it does not distinguish GOE from GUE at two sectors. Those limits are stated, not hidden.

The rule is: desymmetrize before testing the class.
