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
cannot resolve the count, because the per-spectrum scatter exceeds the gaps between
counts; the sequence of gap ratios carries more. A
first-order Markov model fitted on simulated superpositions yields a posterior over
`{1, …, 6, ≥6/poisson}`. At a nominal 95% interval, measured coverage is `0.99`, `0.92`,
`0.91`, `0.96`, `0.98` at `1, 2, 3, 4, 6` sectors and `0.78` for a Poisson spectrum, over
400 spectra per row. The single-sector case is decisive (`p = 0.97`, interval `1..1`); the
two-sector case yields a lower bound (`2`) but not a count, and from three sectors upward
the count is not recoverable from adjacent-gap ratios alone, because `3` through `6` are
indistinguishable to them. Two-sector GOE
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

Quantum chaos is diagnosed by level-spacing statistics [4]. The mean adjacent-gap ratio
`⟨r⟩` [6, 5] takes three reference values:

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
product of a larger project, and the failure that produced it is the failure it detects.

The project began with a candidate operator for the Riemann hypothesis. The map
`σ(s) = 1 − conj(s)` reflects the complex plane about the critical line; its fixed locus
is exactly `Re(s) = 1/2`; and a Hamiltonian built around this involution was proposed as a
route to the zeros. That proposal, the dimension-shift hypothesis, was tested against
criteria it had set for itself and was abandoned. The decisive run found that the sector
class of a `σ`-symmetric Hamiltonian is inherited from the input blocks, not produced by
the `σ` structure: GOE sectors at `0.528 … 0.533`, GUE sectors at `0.596 … 0.602`, but a
full spectrum at `0.420 … 0.425` for either input. The verdict is recorded with the
abandoned hypothesis and is final.

Two errors made during that work are the subject of this paper. The first was statistical: a
single seed of a 90-point grid reported "supported", and 300 seeds with error bars
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
the previous section the two-sector class gap is `0.0010`, which is `1.4` standard errors;
in the nested series of Fig. 2 at 3200 spectra it is `0.0004`, which is `0.5` standard
errors. Neither is a measurement of a class difference: both are consistent with zero, and
both are one thirtieth of the scatter that one spectrum carries. **More spectra sharpen the
mean and leave the single measurement untouched.** That is why the diagnostic resolves the
symmetry structurally, by splitting the spectrum into sectors, instead of averaging harder
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
6. reports the limits: the mean cannot resolve the count, the count is not recoverable
   from adjacent-gap ratios above two sectors, the flag's rate depends on the spectrum
   size, the posterior degrades on sectors that are not equal and independent, two-sector
   GOE and GUE are indistinguishable in the mean as well as in one spectrum, and more
   spectra do not change that.

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

The structural reason the split matters is worth stating explicitly. An involution is an
operator `σ` with

```
σ² = 1.
```

If the Hamiltonian commutes with it, `[H, σ] = 0`, the Hilbert space decomposes into the
two eigenspaces of `σ`, with eigenvalues `+1` and `-1`. In the eigenbasis of `σ`, the
Hamiltonian is block diagonal:

```
\[
H = \begin{pmatrix} H_{+} & 0 \\ 0 & H_{-} \end{pmatrix}
\]
```

The full spectrum of `H` is the union of the spectra of `H₊` and `H₋`. A spacing statistic
measured on the full spectrum is therefore measured on a superposition, not on either
sector. That is the silent failure mode: a value of `⟨r⟩ = 0.42` looks like a legitimate
measurement, and it is exactly what a two-sector superposition produces.

In the application that motivated this paper, `σ` is the map

```
σ(s) = 1 − conj(s),
```

whose fixed locus is the critical line `Re(s) = 1/2`. That involution came from an
abandoned route to the Riemann hypothesis (§1.2); it is used here as a diagnostic tool,
not as a proof route.

The refusal in Step 1 is not a formality. A split routine that skips it returns arrays
that are not sector spectra, and the error is invisible downstream: on a fixture whose
`‖[H, U]‖/‖H‖` is `1.14 … 1.18`, the unchecked split discards exactly the mass that makes
the blocks non-sectors.

### 2.2 Contamination detection from a single spectrum

Two entry points cover a caller that has only a spectrum:

* `contamination_warning(H, U)`: when a candidate involution is known. It verifies the
  commutation, splits, and compares the full spectrum with the resolved sectors. This is
  the reliable half: the comparison is within one Hamiltonian and needs no calibration.
* `detect_hidden_symmetry(eigenvalues)`: when no involution is known. It computes the
  full-spectrum `⟨r⟩` and flags a value below the single-sector floor, where the floor
  scales with the number of levels in the spectrum (§5.1). A bare spectrum is screened
  under the null hypothesis that it is a single sector, so the size that enters the
  floor is its total length.

The flag is not a classifier (Fig. 3). `37` of `400` pure single-sector GOE spectra at
`d = 60` also fall below the floor, a rate of `9.2%` with a 95% binomial interval of
`6.6%` to `12.6%`, and `0` of `400` GUE spectra do (Appendix C). The rate is that high
because the one-sector GOE value is `0.530` with a per-spectrum scatter of `0.039`, and
the floor at 60 levels is `0.48`: a third of a distribution width below the mean is a
tenth of the distribution. A low `⟨r⟩` is also what an integrable system produces. Spacing
statistics cannot separate the two, and the warning says so in its own text.

![Fig. 3. Distribution of the full-spectrum mean gap ratio for four sector counts and both block classes, one dot per simulated spectrum (4000 per point), with the per-point mean marked. The Poisson window is shaded, the flag threshold at 60 levels (0.48) and the severe-contamination boundary (0.46) are drawn. At two sectors the GOE and GUE clouds coincide, so a class test on the full spectrum is uninformative rather than noisy.](output/desymmetrisation_warning.png)

### 2.3 Bayesian estimation of the sector count

The mean `⟨r⟩` cannot resolve the sector count. The mean is monotone in the count at the
ensemble level, but the per-spectrum scatter exceeds the gaps between successive counts,
so a single spectrum's mean does not carry its count. The sequence of `≈240` gap ratios
carries more.

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
how many sectors, not what class. The posterior is a plug-in estimate with a uniform
prior over the seven hypotheses: the transition frequencies are fitted once and then used
as if they were exact, not marginalised over, which is why its interval coverage is
measured rather than assumed (§2.4).

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

### 2.5 The count from higher-order spacing ratios

The adjacent-gap ratio is the first member of a family. With spacings `s_i = E_{i+1} − E_i`,
the `k`-th order spacing ratio is

```
r_i^(k) = (E_{i+2k} − E_{i+k}) / (E_{i+k} − E_i),
```

folded to `(0, 1]` with min/max so that `k = 1` reproduces `⟨r⟩`. Tekur, Bhosale and
Santhanam [10] showed that the `k`-th order distribution of a composite spectrum is the
nearest-neighbour distribution with a modified Dyson index, which is why the family can
carry a count that `k = 1` cannot.

**Model.** The mean ratio at each order `k = 1, …, 6` is one feature. For each hypothesis
(1 to 6 sectors, plus Poisson) the feature vector is fitted on 200 simulated spectra with
the class alternated, and the posterior is Gaussian naive Bayes over the six per-order
means, with one mean and one standard deviation per hypothesis and order and a uniform
prior over the seven hypotheses. It is a plug-in classifier like the one in Section 2.3,
and its coverage is measured the same way, at 120 spectra per row:

| true sectors | coverage | posterior on the truth |
|:---|---:|---:|
| 1 | `1.00` | `0.99` |
| 2 | `0.90` | `0.76` |
| 3 | `0.78` | `0.47` |
| 4 | `0.82` | `0.40` |
| 5 | `0.87` | `0.31` |
| 6 | `0.88` | `0.48` |
| Poisson | `0.96` | `0.90` |

With `k = 1` alone the model is the adjacent-gap limit and reproduces the negative result
of Section 2.4: single-spectrum balanced accuracy is `0.66` for two versus three sectors,
`0.63` for three versus six and `0.55` for four versus six. With orders one to six the same
model reaches `0.81`, `0.94` and `0.82`. The count that the adjacent-gap ratio cannot carry
above two sectors is carried by the family, and the Poisson row improves from `0.78` to
`0.96`: an integrable spectrum is now identified as such in `0.90` of draws, against
`0.24` for the adjacent-gap model.

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

The flow selects a sector rather than preserving one. The direction is expected rather
than surprising, and this section records the measurement, not a discovery: the commutant
of an involution is closed under products and commutators, so a commuting state cannot
leave it, and a state with both parity components flows to the ground state, which has
definite parity. What is measured here is the selection itself. From an asymmetric start
the flow does not break the symmetry; it settles into a definite sector.

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

A description of the multi-copy imaginary-time circuits quotes an identity for the
first-order term. The description has no citable source, and no published derivation of
the identity was found for this paper, so it is reproduced here as quoted and tested as
quoted:

```
Tr₂(u ρ₁ ⊗ ρ₂ u†) = ρ₁ − ε[[ρ₁, H], ρ₁] + O(ε^{3/2}).
```

The identity is tested against the three natural generators (`exp(i√ε(H₁ − H₂))`, the same with a
swap inserted, and the Trotter split of the two phases) by fitting
`ρ(ε) = ρ + √ε A + ε B + …` from three scales. In every case:

* the first-order term is **not** zero: it is `A = i[H, ρ₁]`, which the identity does
  not have;
* the second-order term is **not** `±[[ρ₁, H], ρ₁]`.

The identity is therefore recorded as **unverified**, not as confirmed and not as
refuted: the generator that makes the first-order term vanish is
a property of the circuit, and the circuit was not read. Recording the discrepancy is the
correct response; assuming the identity and building on it would not be.

## 5. Limitations and scope

| limit | measured | consequence |
|:---|:---|:---|
| the mean cannot resolve the count | the mean is monotone but the scatter exceeds the gaps between counts | the posterior must use the sequence, not the mean |
| two-sector GOE/GUE indistinguishable | `0.4232` vs `0.4222`, `1.4` standard errors of the two means | a class test on a contaminated spectrum is uninformative |
| more spectra do not fix the two-sector class test | best single-spectrum balanced accuracy `0.526` at 4000 spectra per class | the diagnostic must split the spectrum, not average it |
| the count is not recoverable from adjacent-gap ratios above two | `3…6` indistinguishable to `⟨r⟩` and to the ratio sequence | report `≥3`, not a number; long-range statistics do better (§5.3) |
| false positive at the floor | `37` of `400` GOE, `0` of `400` GUE, at `d = 60` | the flag is a hint, not a decision, and its rate depends on the spectrum size (§5.1) |
| Poisson read as a finite superposition | coverage `0.78`, so a finite count in `0.22` of draws | an integrable spectrum looks contaminated about a fifth of the time |
| the flow cannot repair contamination | `H` is an input | the class is a property of `H`; `H` does not evolve |
| the model is a plug-in fit | 200 spectra per hypothesis | the coverage is measured rather than asserted, and under-covers at two and three sectors (`0.92`, `0.91`) |

### 5.1 The flag's rate is a function of the spectrum size

The contamination floor is the fixed `0.48`, which is the one-sector GOE mean minus `1.3`
per-spectrum standard deviations at `d = 60`. The scatter of a mean over `n` ratios falls
as `1/√n`, so the same absolute floor over-flags at small sizes and under-flags at large
ones (measured, 400 spectra per point, GOE):

| levels per sector | one-sector std | flag rate at fixed `0.48` | two-sector superpositions missed | flag rate at a scaled floor |
|:---|---:|---:|---:|---:|
| 15 | `0.087` | `0.29` | `0.19` | `0.12` |
| 60 | `0.039` | `0.11` | `0.04` | `0.11` |
| 240 | `0.020` | `0.013` | `0.00` | `0.12` |
| 480 | `0.014` | `0.003` | `0.00` | `0.12` |

The fifth column keeps the same `1.3` z-score at every size (`R_GOE − 1.3·σ(n)` with
`σ(n) = 0.0393·√(60/n)`), and its rate is flat at about `0.12`. That is the floor the
detector uses, so its threshold moves with the spectrum and the flag rate does not; the
fixed `0.48` remains the reference value at 60 levels, where the two coincide.

The scaled floor is not free, and the trade runs in both directions. At small sizes it
sits below `0.48`, so it flags fewer pure spectra but misses contamination: at 15 levels
per sector it misses `0.46` of two-sector superpositions against `0.19` for the fixed
floor, and at 30 levels `0.21` against `0.12`. At long sizes it sits above `0.48`, so it
flags more pure spectra, about `0.12` at 240 and 480 levels against `0.013` and `0.003`,
while missing no two-sector superposition under either floor. The two floors are mirror
images: the fixed one is talkative at short sizes and quiet at long ones, the scaled one
the reverse. The scaled floor is chosen for a rate that does not depend on the size, and
both directions of the trade are stated here rather than only the one that flatters it. A
caller should therefore report the z-score together with the
missed rate at the size in hand. The calibration is in levels per sector, which is the size
of one block; a caller who knows only the total length of a spectrum should pass that
length, because that is what the null hypothesis, a single sector, assumes.

Appendix C's `9.2%` and the `0.11` in this table measure the same quantity at different
sample sizes: their difference is sampling noise, with a standard error of about `0.015`,
not a measurement that moved.

### 5.2 Robustness of the posterior to its own simulator

The posterior is trained on equal-sized, independent, class-balanced sectors at 240
levels. Real symmetries give unequal sectors, mixed classes and awkward densities, so the
same posterior is run over the symmetric baseline and three departures (400 spectra each;
the baseline uses GOE draws, so its mass on the truth differs from the class-marginalised
coverage of Section 2.4):

| scenario | truth | posterior on the truth | coverage |
|:---|---:|---:|---:|
| equal sectors | 3 | `0.30` | `0.90` |
| unequal sectors (120/80/40) | 3 | `0.26` | `0.90` |
| mixed class (GOE + GUE) | 2 | `0.69` | `0.95` |
| awkward density (one sector compressed) | 3 | `0.26` | `0.92` |

The departures degrade the three-sector rows modestly and never improve on the baseline;
the two-sector mixed-class row stays the strong case. The coverage numbers in Sections
2.4 and 1.5 are therefore a property of the symmetric simulator, not a promise about a
real spectrum, and Appendix D's device descriptions are stated as an outlook for exactly
that reason.

### 5.3 The limit is the ratio, not the spectrum

"Not recoverable above two" is a property of the adjacent-gap ratio, not of the spectrum.
The ratio is a short-range statistic, and a three-or-more-sector superposition and a
Poisson spectrum have the same adjacent gaps. Long-range statistics do not (measured,
window length 20, 200 spectra per point):

| spectrum | `⟨r⟩` | number variance `Σ²(20)` | Dyson–Mehta `Δ₃(20)` |
|:---|---:|---:|---:|
| 1 sector | `0.530` | `0.98` | `0.22` |
| 2 sectors | `0.423` | `1.65` | `0.39` |
| 3 sectors | `0.403` | `2.24` | `0.51` |
| 6 sectors | `0.392` | `3.76` | `0.74` |
| Poisson | `0.386` | `12.41` | `1.23` |

`Σ²(20)` reads a Poisson spectrum as `12.4` and a six-sector union as `3.8`, where the
ratio reads both as `0.39`. Long-range statistics therefore separate Poisson from a union
of sectors almost perfectly, which is the comparison the ratio fails and the one a
complete instrument should add. The posterior is the instrument when the symmetry is
unknown and only the gap ratios are available; the number variance and the Dyson–Mehta
statistic are the instruments when a bare spectrum must be read as Poisson or as a union
of rigid sectors. A complete diagnostic reports both, because the two statistics fail in
different places. The posterior in this paper uses the ratio sequence alone, so its "not
counted above two" is a statement about that statistic and nothing stronger.

The number variance is also sensitive to the unfolding. With the polynomial unfolding used
here the Poisson value is `12.2` at a window of 20, against `17.8` with no polynomial
unfolding and `20` for a pure Poisson process, so the absolute values and the factor of
three depend on the unfolding while the ordering does not. Table 5.3 compares means; one
spectrum at a time, with the balanced accuracy of Section 1.4, the two statistics separate
three sectors from six at `0.90` (`Σ²`) and `0.93` (`Δ₃`), and six sectors from Poisson at
`0.98` and `0.96`.

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

The phenomenon this paper addresses is not new. The superposed spectra of independent
symmetry sectors were studied by Rosenzweig and Porter [3] and entered quantum chaos
through the Bohigas–Giannoni–Schmit conjecture [4]; the gap-ratio statistic used
throughout is from Atas et al. [5] and Oganesyan and Huse [6]. The specific observation
that a superposed spectrum biases the gap-ratio distribution away from the single-sector
class is due to Giraud et al. [1]. This paper takes that phenomenon as given and measures
its consequences.

Two recent works address the same structural fact, that discrete symmetries split the
Hilbert space into invariant sectors, and that a composite spectrum does not preserve the
spectral correlations of its blocks, and cross the boundary this paper measures, using
higher-order statistics rather than the adjacent-gap ratio.

The higher-order family itself is older, and the two papers below build on it. Tekur and
Santhanam [9] showed that a spectrum composed of `k` independent level sequences of equal
level density has a `k`-th order spacing-ratio distribution equal to its nearest-neighbour
counterpart with a modified Dyson index, which is how the symmetry structure of a measured
spectrum can be read without desymmetrization. Tekur, Bhosale and Santhanam [10] derived
the modified index for the Gaussian and circular ensembles, and Bhosale [11] carried the
construction to superposed spectra. The statistics the two papers below use, and those
measured in Section 2.5, are theirs.

Vyas, Tekur and Santhanam (arXiv:2610.03108) use higher-order spacing ratios (HOSR) and a
Best Subset Technique (BST). For order `k` they define

```
r_i^(k) = (E_{i+2k} − E_{i+k}) / (E_{i+k} − E_i),
```

and fit the empirical `k`-th order spacing-ratio distribution to the Wigner surmise with
an effective Dyson index `β′`, minimising the Kullback–Leibler divergence

```
D_KL(k, f) = Σ_r  P_emp^(k)(r; f) · log[ P_emp^(k)(r; f) / P(r; β′) ]
```

over a fraction `f` of the spectrum that selects the maximally overlapping part of the
blocks. Their central self-consistency relation is

```
P_k(r, β = 1, m) = P(r, β′ = k = m)       (GOE)
P_k(r, β = 2, m) = P(r, β′ = k+1 = m+1)   (GUE)
```

so that for `k = m` in the GOE case (or `k+1 = m+1` in the GUE case) the number of
sectors `m` becomes directly readable. The `k`-th order ratio sees the sector count where
the adjacent-gap ratio does not.

Rout and Bhosale (arXiv:2510.00503) study higher-order spacings in superposed spectra of
random matrices of the same class, with equal-sized subsectra, and test the result on the
quantum kicked top. Their setting is therefore the symmetric case that the best-subset
technique generalises: the unequal-dimension problem is treated by Vyas et al. through the
optimal fraction `f*`, not by Rout and Bhosale.

The relation between those methods and this paper is precise and complementary, not
competitive. The adjacent-gap ratio is the `k = 1` case of the higher-order family. This
paper measures where the `k = 1` statistic stops carrying the sector count: at three or
more sectors the `⟨r⟩` values (`0.404`, `0.396`, `0.391`) lie closer together than the
per-spectrum scatter (`0.017` to `0.039`) that one spectrum carries, so no ensemble
average can separate them.

The crossing is measured here rather than quoted. Section 2.5 extends the posterior to
orders one to six, and on one spectrum the difference is direct: the mean ratio alone
separates two from three sectors at `0.66` balanced accuracy, three from six at `0.63` and
four from six at `0.55`, while orders one to six separate them at `0.81`, `0.94` and `0.82`
(200 spectra per class). The count that the adjacent-gap ratio cannot carry above two
sectors is carried by the family, and the statement "not recoverable" belongs to `k = 1`,
not to the spectrum.

The involution `σ` plays a different role in the two settings. In this paper `σ` is a
concrete, verifiable operator: `[H, σ] = 0` and `[Uᵢ, Uⱼ] = 0` are checked before the
split, and the involution is the key that guarantees the block structure. In Vyas et al.
the symmetry is more general and less explicit: the sectors may arise from several
discrete symmetries (parity, reflection, and others), their dimensions may be unequal, and
the BST recovers the count `m` without knowing the symmetry operators. The involution used
here is the simplest case of the general problem those papers solve: `m = 2`, equal
dimensions, one explicit `ℤ₂` symmetry.

The contribution of this paper is therefore a measurement of that case, not a method that
generalises it. It reports the interval coverage of a Bayesian posterior over the ratio
sequence (`0.99` to `0.78`, at 400 spectra per row), the separation of precision from
resolution (4000 spectra determine the mean to `0.0007`, while the best single-spectrum
class accuracy at two sectors is `0.526`, which is chance), and the explicit statement
that the ratio stops carrying the count above two sectors, where the Dyson–Mehta number
variance continues to separate Poisson from a six-sector union by a factor of three.

| **reference** | **contribution** | **what this adds** |
| :--- | :--- | :--- |
| Giraud et al. [1] | the phenomenon: superpositions bias the ratio | the measured table, the entry points, the posterior, the coverage |
| Rosenzweig–Porter [3] | block superpositions in RMT | the diagnostic form, not the theory |
| Mehta [2] | the reference distributions | the calibration values |
| Atas et al. [5] | the `r`-ratio as a statistic | the inversion attempt and its measured failure |
| Vyas, Tekur, Santhanam [7] | sector count from higher-order ratios, unequal sectors | the measured coverage and the stated ratio-limit |
| Rout, Bhosale [8] | higher-order spacings, quantum kicked top | the Bayesian posterior and the resolution measurement |

The phenomenon is not new. The boundary is what this paper measures.

## 9. Conclusion

A spacing statistic measured on a Hamiltonian that commutes with an involution is
measured on a superposition. The standard `⟨r⟩` cannot distinguish a Poisson spectrum
from a union of unresolved sectors, and the failure is silent.

We provide a diagnostic that verifies the symmetries, splits the spectrum, flags
contamination, and estimates the sector count as a posterior with a measured coverage.
The single-sector case is decisive; the two-sector case is bounded below but not counted;
from three sectors upward the count is not recoverable from adjacent-gap ratios alone,
and long-range statistics do what the ratios cannot. Two-sector GOE and GUE are
indistinguishable, in one spectrum and in the mean of thousands. The false-positive rate
is stated, as a function of the spectrum size. The limits are reported rather than hidden.

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

The diagnostic began as an error made on a candidate operator; it ends as a tool that
makes that mistake visible, measurable, and stated.

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

At 60 levels the floor is `0.48`, not the reference value `0.531`, because the measured
one-sector GOE value at `d = 60` is `0.5297` with a per-spectrum scatter of `0.0393`: the
floor sits `1.3` standard deviations below that mean, which is precisely why `9.2%` of pure
GOE spectra are flagged. A floor raised to the reference value would exchange those false
positives for missed contamination, and the trade is the user's, so the rate is stated
rather than tuned. The GUE side is quiet because its one-sector value is `0.5993`, `3.2`
standard deviations above the floor. The rate is a function of the spectrum size, not a
constant of the instrument: Section 5.1 reports it across sizes, and the detector applies
the scaled floor, so `0.48` is the value that scaling takes at 60 levels rather than a
constant.

## Appendix D: Technical applications and outlook

The diagnostic is a software method, and a method is not a device. This appendix sketches,
as an outlook only, how the measured pieces assemble into a physical instrument; it makes
no patent claim.

### D.1 A symmetry-aware spectrum analyzer

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

### D.2 A quantum-processor calibration system

A processor, for instance a superconducting qubit array, can sit in a symmetry-protected
regime whose spectrum looks integrable, and control pulses calibrated against that
spectrum are wrong. The device reads the spectrum, applies the diagnostic, and, on a
contaminated result, drives a symmetry-breaking perturbation to resolve the sectors
before re-measuring. The technical effect is control fidelity; the algorithm is the means.

### D.3 A double-bracket flow controller

The flow `dρ/dβ = [[ρ, H], ρ]` preserves or selects a sector, as measured in §3. A
controller that implements the flow and monitors the coherence `‖[ρ, σ]‖` can stop the
evolution when the wrong sector is being selected, instead of discovering it after the
prepared state is wrong.

### D.4 Application domains

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

### D.5 Scope of the claims

What the manuscript does **not** claim:

* the algorithm itself (a plug-in posterior over sector counts);
* a numerical simulation with no physical input or output;
* the mathematics of Sections 2 through 4.

A granted patent claims a physical embodiment and a technical effect, not these. This
manuscript makes no patent claim and no assertion about what any office would grant; the
device descriptions above are an outlook, and the quantum-processor and dot-array cases
carry no experimental results behind them.

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
7. Vyas, N., Tekur, S. H. and Santhanam, M. S. *Determining the Number of Symmetry
   Sectors in Composite Quantum Spectra.* arXiv:2610.03108 (2026).
8. Rout, S. and Bhosale, U. T. *Higher-order spacings in the superposed spectra of random
   matrices with comparison to spacing ratios and application to complex systems.*
   arXiv:2510.00503 (2025).
9. Tekur, S. H. and Santhanam, M. S. *Symmetry deduction from spectral fluctuations in
   complex quantum systems.* Phys. Rev. Research **2**, 032063 (2020); arXiv:1808.08541.
10. Tekur, S. H., Bhosale, U. T. and Santhanam, M. S. *Higher order spacing ratios in
    random matrix theory and complex quantum systems.* Phys. Rev. B **98**, 104305 (2018);
    arXiv:1806.05958.
11. Bhosale, U. T. *Superposition and higher-order spacing ratios in random matrix theory
    with application to complex systems.* Phys. Rev. B **104**, 054204 (2021);
    arXiv:1905.02585.

## Disclaimer

This manuscript describes a diagnostic instrument, not a result about the Riemann
hypothesis. The phenomenon it addresses, that unresolved symmetries bias spacing
statistics toward Poisson, is standard quantum-chaos practice. What is local is the
measured table, the entry points, the posterior's measured coverage, and the recorded
limits.

The diagnostic detects contamination. It does not count sectors reliably above two from
adjacent-gap ratios alone, and it does not distinguish GOE from GUE at two sectors. Those
limits are stated, not hidden.

The rule is: desymmetrize before testing the class.
