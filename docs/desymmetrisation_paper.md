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

### Methods manuscript — draft for submission

**Status.** Draft complete and reproducible in this repository; not submitted anywhere,
no venue assigned, no peer review. The licence header above is kept for repository
consistency and should be stripped for submission. Corrections made to the previous
draft are listed in ["A note on this draft"](#a-note-on-this-draft) — the numbers in the
tables are the measured ones, and where the draft had a figure or a deviation wrong, this
version says what the measurement is.

## Abstract

Spacing statistics are the standard diagnostic for quantum chaos, but they are measured
on a superposition whenever the Hamiltonian commutes with an involution. A spectrum that
appears Poisson-like may instead be a union of unresolved sectors, and the standard mean
gap ratio `⟨r⟩` cannot distinguish the two. We present a diagnostic that (i) verifies the
symmetries, (ii) splits the spectrum into joint sectors, (iii) flags a contaminated full
spectrum, and (iv) estimates the number of unresolved sectors as a posterior with a
measured coverage. The mean cannot be inverted; the sequence of gap ratios can. A
first-order Markov model fitted on simulated superpositions yields a posterior over
`{1, …, 6, ≥6/poisson}`. At a nominal 95% interval, measured coverage is `1.00`, `0.93`,
`0.87`, `0.98`, `0.97` at `1, 2, 3, 4, 6` sectors and `0.78` for a Poisson spectrum. The
single-sector case is decisive (`p = 0.98`, interval `1..1`, correct 95% of the time).
The two-sector case is defensible as a set (`2..5`) but not as a point. From three
sectors upward the count is not recoverable: the posterior reports `≥3`, and `3` through
`6` are indistinguishable. Two-sector GOE and GUE are indistinguishable in the full
spectrum, so a class test on a contaminated spectrum is uninformative rather than noisy.
The diagnostic is calibrated on a measured table, its false-positive rate is stated (`4`
of `40` pure single-sector GOE spectra fall below the flag), and its limits are reported
rather than hidden. The companion dynamical analysis shows that the double-bracket flow
preserves sector populations when the state commutes with the involution, but selects a
sector when it does not — so the flow cannot repair a contaminated spectrum, because the
class is a property of the Hamiltonian and the Hamiltonian does not evolve.

## 1. Introduction

### 1.1 The problem

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

### 1.2 The measured table

At 300 seeds per point, `60` levels per sector, the full-spectrum `⟨r⟩` depends on the
number of unresolved sectors:

| unresolved sectors | GOE blocks | GUE blocks |
|:---|---:|---:|
| 1 | `0.531` | `0.600` |
| 2 | `0.426` | `0.421` |
| 3 | `0.404` | `0.399` |
| 6 | `0.391` | `0.389` |

Two facts follow, and the measured per-spectrum scatter (Appendix A) is what makes them
true rather than suggestive:

- **At three or more sectors, `⟨r⟩` is inside the Poisson window** `[0.36, 0.41]`. A
  researcher who measures `0.39` and concludes "integrable" is wrong, and the standard
  test gives no indication.
- **At two sectors the class is erased.** `0.426` against `0.421` is a gap of `0.005`,
  against a per-spectrum scatter of `≈0.03` for each class. A class test on a two-sector
  full spectrum is uninformative, not merely noisy.

### 1.3 The contribution

We provide a diagnostic that:

1. verifies that the proposed involutions commute with `H` and with each other;
2. splits the spectrum into joint sectors;
3. warns when a full spectrum is contaminated by an unresolved symmetry;
4. estimates the number of unresolved sectors as a posterior with a measured coverage;
5. reports the limits: the mean cannot be inverted, the count is not recoverable above
   two sectors, and two-sector GOE and GUE are indistinguishable.

The phenomenon is standard quantum-chaos practice (Giraud et al. [1]). What is local is
the measured table, the entry points, the posterior's measured resolution, and the
recorded limits.

## 2. The diagnostic

### 2.1 Static desymmetrization

Given a Hamiltonian `H` and a set of involutions `{U₁, …, Uₖ}`:

* **Step 1 — verify.** Check `[H, Uᵢ] = 0` for every `i`, and `[Uᵢ, Uⱼ] = 0` for every
  pair. If a commutator is nonzero the split is invalid, and the diagnostic refuses to
  proceed rather than returning a plausible-looking decomposition.
* **Step 2 — diagonalize the involution group.** The involutions generate `(ℤ₂)ᵏ`;
  diagonalize each `Uᵢ` and group the simultaneous eigenspaces.
* **Step 3 — split.** Project `H` onto each joint eigenspace and diagonalize the block.
* **Step 4 — validate.** For the `σ` case the sectors are `spec(A + C)` and `spec(A − C)`;
  that identity is checked against the blocks, not assumed. For a `ℤ₂ × ℤ₂` the four
  sectors are checked against a direct sum built from four known blocks.

The refusal in Step 1 is not a formality. A split routine that skips it returns arrays
that are not sector spectra, and the error is invisible downstream: the reviewer-supplied
fixture for this family of utilities measures `‖[H, U]‖/‖H‖ = 1.14 … 1.18` and its split
discards exactly the mass that makes the blocks non-sectors.

### 2.2 The contamination warning

Two entry points cover a caller that has only a spectrum:

* `contamination_warning(H, U)` — when a candidate involution is known. It verifies the
  commutation, splits, and compares the full spectrum with the resolved sectors. This is
  the reliable half: the comparison is within one Hamiltonian and needs no calibration.
* `detect_hidden_symmetry(eigenvalues)` — when no involution is known. It computes the
  full-spectrum `⟨r⟩` and flags a value below the single-sector floor.

The flag is not a classifier. `4` of `40` pure single-sector GOE spectra also fall below
the floor (Appendix C). A low `⟨r⟩` is also what an integrable system produces. Spacing
statistics cannot separate the two, and the warning says so in its own text.

### 2.3 The posterior

The mean `⟨r⟩` cannot be inverted. The sequence of `≈240` gap ratios can be.

**Model.** A first-order Markov model of the sequence,

```
r_{n+1} | r_n ~ f(r_{n+1} | r_n; k),
```

where `k` is the number of unresolved sectors, restricted to `k = 1, …, 6`, plus a
Poisson hypothesis standing for "integrable, or more sectors than are distinguishable
from it". The conditional density is estimated on binned ratios from 200 simulated
superpositions per hypothesis, with GOE and GUE marginalised at equal weight.

**Why first order?** Modelling the ratios as independent is measurably overconfident:
coverage `0.70` at a nominal `0.90`, because consecutive ratios share a spacing and the
independent product counts the same information twice. The dependence is in the model,
and the coverage is measured rather than assumed.

**Output.** A posterior over `{1, 2, 3, 4, 5, 6, ≥6/poisson}` and the shortest contiguous
interval carrying 95% of its mass. The open label exists so that the estimator is
*allowed* to say "not a finite superposition"; it does not claim to distinguish seven
sectors from an integrable spectrum.

### 2.4 The measured coverage

At a nominal 95% interval, over 60 spectra per row:

| true sectors | coverage | posterior on the truth | typical interval |
|:---|---:|---:|:---|
| 1 | `1.00` | `0.98` | `1..1` |
| 2 | `0.93` | `0.65` | `2..5` |
| 3 | `0.87` | `0.24` | `3..6` |
| 4 | `0.98` | `0.17` | `3..6` |
| 5 | `1.00` | `0.21` | `3..6` |
| 6 | `0.97` | `0.20` | `3..6` |
| Poisson | `0.78` | `0.20` | `4..6` |

Reading the table:

* **One sector is decisive.** `p = 0.98` on the truth, interval `1..1` in 95% of draws,
  and the posterior on `1` stays below `0.02` for every other truth, Poisson included.
* **Two sectors is a set.** `p = 0.65`, interval `2..5`. "Two" is defensible; "exactly
  two" is not.
* **Three or more is not counted.** The posterior reports `≥3`, and `3` through `6` are
  indistinguishable. The interval's lower bound rises with the truth
  (`P(lower ≥ 3) = 0.65, 0.80, 0.83, 0.88` at `3, 4, 5, 6` sectors), which is a weaker
  and more useful statement than a point estimate.
* **Poisson is the hard row.** An integrable spectrum is read as a `4–6`-sector
  superposition about a fifth of the time, because that is what it looks like. Coverage
  `0.78` is the honest number for that row.

## 3. The dynamical counterpart

### 3.1 The double-bracket flow

The multi-copy imaginary-time circuits are built on the double-bracket flow

```
dρ/dβ = [[ρ, H], ρ] = 2ρHρ − Hρ² − ρ²H.
```

This flow has a property the static analysis does not: it preserves the sector structure
when the state commutes with the involution.

### 3.2 What the flow preserves

Measured over `β = 15` with RK4 at 3000 steps:

| quantity | drift |
|:---|---:|
| spectrum of `ρ` | `3e-12` |
| trace | `1.3e-15` |
| non-Hermiticity | `2.8e-17` |
| sector populations, when `[ρ, σ] = 0` | `< 1e-8` |

The populations panel of Fig. 4(a) uses a state with equal mass in the two sectors that
is *not* an eigenstate of `H` (`‖[ρ, H]‖ = 1.46`): the flow does real work on it and the
populations still do not move.

### 3.3 What the flow does not preserve

When the state does not commute with `σ`, the flow drives it into a single sector:

| quantity | before | after |
|:---|---:|---:|
| coherence `‖[ρ, σ]‖` | `1.41` | `3e-3` |
| populations | `(0.50, 0.50)` | `(1.00, 0.00)` |

The flow selects a sector rather than preserving one. This is a measured behaviour of
the flow, not a claim in the sources, and it is the opposite direction from the
invariance row: from an asymmetric start the flow does not break the symmetry, it
*creates* it.

### 3.4 The limit

In neither case does the flow touch the Hamiltonian. `H` is an input, the state is the
variable, and the flow is isospectral in the state. The class is a property of `H`, and
`H` never evolves. The flow cannot repair a contaminated spectrum, and no amount of
imaginary-time evolution changes the number `⟨r⟩` of a fixed Hamiltonian.

That is a precise statement of what the flow can and cannot do. It is the kind of limit
that makes a tool trustworthy.

### 3.5 The Lean theorem

The invariance step is machine-verified in
`lean/RiemannFramework/DynamicalDesymmetrisation.lean`:

* `commute_doubleBracketIncrement`: if `ρ` and `H` commute with an involution, then so
  does the double-bracket increment;
* `commute_euler_step`: the same holds for one Euler step.

Both are `sorry`-free and depend only on `propext`, checked by `#print axioms`.

## 4. The negative result on the multi-copy identity

The literature's description of the multi-copy imaginary-time circuits quotes an identity
for the first-order term:

```
Tr₂(u ρ₁ ⊗ ρ₂ u†) = ρ₁ − ε[[ρ₁, H], ρ₁] + O(ε^{3/2}).
```

We tested it against the three natural generators (`exp(i√ε(H₁ − H₂))`, the same with a
swap inserted, and the Trotter split of the two phases) by fitting
`ρ(ε) = ρ + √ε A + ε B + …` from three scales. In every case:

* the first-order term is **not** zero — it is `A = i[H, ρ₁]`, which the identity does
  not have;
* the second-order term is **not** `±[[ρ₁, H], ρ₁]`.

The identity is therefore recorded as **unverified from the description available**, not
as confirmed and not as refuted: the generator that makes the first-order term vanish is
a property of the circuit, and the circuit was not read. Recording the discrepancy is the
correct response; assuming the identity and building on it would not be.

## 5. Limitations

| limit | measured | consequence |
|:---|:---|:---|
| the mean cannot be inverted | the table is many-to-one and the scatter exceeds the gaps between counts | the posterior must use the sequence, not the mean |
| two-sector GOE/GUE indistinguishable | `0.426` vs `0.421` | a class test on a contaminated spectrum is uninformative |
| the count is not recoverable above two | `3…6` indistinguishable | report `≥3`, not a number |
| false positive at the floor | `4` of `40` | the flag is a hint, not a decision |
| Poisson read as `4–6` sectors | coverage `0.78` | an integrable spectrum looks contaminated about a fifth of the time |
| the flow cannot repair contamination | `H` is an input | the class is a property of `H`; `H` does not evolve |
| the model is a plug-in fit | 200 spectra per hypothesis | the coverage is measured rather than asserted, and slightly under-covers at three sectors (`0.87`) |

## 6. Comparison to the standard alternative

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

### 7.1 Commands

From the repository root:

```bash
python scripts/generate_desymmetrisation_figures.py   # the four figures and the tables
python scripts/run_desymmetrisation_demo.py           # the working demo and its figure
cd python && python -m pytest tests/test_desymmetrisation.py -v
cd python && python -m pytest tests/test_dynamical_desymmetrisation.py -v
cd python && python -m pytest tests/test_desymmetrisation_figures.py -v
```

### 7.2 Environment

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

### 7.3 Data and figures

The measured table, the coverage table and the false-positive rate are produced by
`scripts/generate_desymmetrisation_figures.py` and pinned by
`tests/test_desymmetrisation_figures.py`. Every number in the figures is computed at
draw time; none is typed into the plotting code.

| figure | file | contents |
|:---|:---|:---|
| Fig. 1 | `output/desymmetrisation.png` | `⟨r⟩` against unresolved sectors, 300 seeds per point |
| Fig. 2 | `output/desymmetrisation_warning.png` | one dot per spectrum, four sector counts, both classes, with the Poisson window and the contamination floor |
| Fig. 3 | `output/desymmetrisation_coverage.png` | measured coverage against the nominal 95% level |
| Fig. 4 | `output/desymmetrisation_flow.png` | sector populations under the flow, commuting and cross-sector starts |

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
The single-sector case is decisive; the two-sector case is defensible as a set but not as
a point; from three sectors upward the count is not recoverable. Two-sector GOE and GUE
are indistinguishable. The false-positive rate is stated. The limits are reported rather
than hidden.

The companion dynamical analysis shows that the double-bracket flow preserves sector
populations when the state commutes with the involution, but selects a sector when it
does not — so the flow cannot repair a contaminated spectrum, because the class is a
property of the Hamiltonian and the Hamiltonian does not evolve.

The rule is simple: desymmetrize before testing the class.

## Appendix A: The full measured table

At 300 seeds per point, `60` levels per sector, with the per-spectrum standard deviation
of the mean `⟨r⟩`:

| sectors | GOE `⟨r⟩` | GOE std | GUE `⟨r⟩` | GUE std |
|:---|---:|---:|---:|---:|
| 1 | `0.5309` | `0.0407` | `0.5999` | `0.0342` |
| 2 | `0.4260` | `0.0317` | `0.4209` | `0.0327` |
| 3 | `0.4036` | `0.0255` | `0.3989` | `0.0247` |
| 4 | `0.3960` | `0.0209` | `0.3933` | `0.0212` |
| 6 | `0.3907` | `0.0168` | `0.3889` | `0.0171` |

The two-sector gap between classes (`0.0051`) is smaller than either standard deviation
by a factor of six, which is the quantitative form of "the class is erased".

## Appendix B: The coverage table

At a nominal 95% interval, 60 spectra per row:

| true sectors | coverage | posterior on the truth |
|:---|---:|---:|
| 1 | `1.00` | `0.98` |
| 2 | `0.93` | `0.65` |
| 3 | `0.87` | `0.24` |
| 4 | `0.98` | `0.17` |
| 5 | `1.00` | `0.21` |
| 6 | `0.97` | `0.20` |
| Poisson | `0.78` | `0.20` |

The Poisson row is the false-positive rate of the posterior: it reports a finite count
with probability `0.80`.

## Appendix C: The false-positive rate

| test | result |
|:---|:---|
| pure single-sector GOE spectra below the floor, `d = 60` | `4` of `40` |
| pure single-sector GUE spectra below the floor, `d = 60` | `0` of `40` |
| false-positive rate, GOE | `10%` |

The floor is `0.48`, not the reference value `0.531`: the finite-size dependence of the
one-sector value (`0.531` at `d = 60`, `0.519` at `d = 100`) is why the floor is set
below the reference.

## A note on this draft

The previous draft of this manuscript was assembled from the implementation and contained
several defects that this version corrects. They are listed because a manuscript whose
numbers cannot be traced is not reproducible, and because the corrections are part of the
record rather than an embarrassment to be quietly removed.

| defect in the draft | correction here |
|:---|:---|
| Appendix A quoted standard deviations `≈0.005, 0.008, 0.008, 0.007` | the measured values are `0.041, 0.032, 0.026, 0.021, 0.017` (GOE) and `0.034, 0.033, 0.025, 0.021, 0.017` (GUE): the draft understated the scatter by four to eight times, which matters because the two-sector gap is compared against it |
| Fig. 1 was named `output/desymmetrisation_table.png` | the file is `output/desymmetrisation.png` |
| Fig. 3 was to be drawn from a hardcoded list of coverage values | it is computed by `SectorCountModel.coverage(draws=60)` at draw time |
| Fig. 4 was to be drawn from a fitted exponential curve matching two endpoints | it is the integrated flow, RK4 at 3000 steps |
| the environment was given as Python `3.12`, NumPy `≥1.26`, SciPy `≥1.11` | measured: Python `3.14.7`, NumPy `2.5.3`, matplotlib `3.11.2`; SciPy is not used by these modules |
| the commands were `cd python` then `python scripts/…` | the scripts live at the repository root, so the figures are generated from the root and the tests are run from `python/` |
| the coverage table omitted the five-sector row | it is included (`1.00`), because the figure shows it and a table that hides a row the figure displays is worse than a longer table |
| `p(true)` for `3, 4, 6` was left as `—` | the measured values are `0.24, 0.17, 0.20` — all low, which is the point of those rows |

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
hypothesis. The phenomenon it addresses — that unresolved symmetries bias spacing
statistics toward Poisson — is standard quantum-chaos practice. What is local is the
measured table, the entry points, the posterior's measured coverage, and the recorded
limits.

The diagnostic detects contamination. It does not count sectors reliably above two, and
it does not distinguish GOE from GUE at two sectors. Those limits are stated, not hidden.

The rule is: desymmetrize before testing the class.
