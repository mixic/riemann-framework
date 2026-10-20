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

# Desymmetrise before testing the class

## Abstract

A level-spacing statistic measured on a Hamiltonian that commutes with an involution
is measured on a **superposition**. If `H` commutes with `U`, its eigenvalues are the
union of the sector eigenvalues, and a union of independent spectra has less level
repulsion than any of its parts. The mean adjacent-gap ratio `⟨r⟩` therefore falls —
all the way to the Poisson value as the number of unresolved sectors grows.

This module provides the split, the warning, and a posterior over the number of
unresolved sectors. It is a tool, not a result about the zeta function, and it exists
because the same mistake was made in this repository: the dimension-shift model's class
was tested on the full spectrum of a `σ`-symmetric Hamiltonian, which is why a GOE model
appeared to reach GUE statistics.

    python scripts/run_desymmetrisation_demo.py   # output/desymmetrisation.png

## The table

Measured at 300 seeds per point, `d = 60` per sector, quoting the reviewer's numbers
alongside the ones this repository reproduces:

| unresolved independent sectors | GOE blocks | GUE blocks |
|:---|---:|---:|
| 1 | `0.531` (reviewer `0.52`) | `0.600` (reviewer `0.59`) |
| 2 | `0.426` (reviewer `0.43`) | `0.421` (reviewer `0.42`) |
| 3 | `0.404` | `0.399` |
| 4 | `0.396` | `0.393` |
| 6 | `0.391` | `0.389` |
| Poisson | `0.386` | `0.386` |

The one-sector GOE value is `0.531` at `d = 60` and `0.519` at `d = 100`; the
reviewer's `0.52` is the larger-`d` value. The finite-size dependence is why the
one-sector floor below is set at `0.48` rather than at the reference value.

![Mean r against the number of unresolved sectors, for GOE and GUE blocks](output/desymmetrisation.png)

## The two limits of the mean

**The mean detects but does not count.** The map from `⟨r⟩` to the number of sectors is
many-to-one, and the single-spectrum scatter (`≈0.03`) is comparable to the gaps
between successive sector counts (`0.426 → 0.404 → 0.396`). `estimate_sector_count`
inverts the table and is included to *demonstrate* the failure: for a true `N = 4` it
returns values spread over `2 … 4`, and below the three-sector level it saturates at
the largest tabulated count instead of reporting "cannot tell". The reviewer's
attempt returned `12` for a true `4`; the magnitude is a property of the estimator,
the instability is a property of the data. The next section recovers what a mean cannot
by using the whole sequence; the limit itself does not move.

**At two sectors the class information is erased.** GOE gives `0.426` and GUE `0.421`
— a difference smaller than either standard deviation. A class test run on a
two-sector full spectrum is not noisy, it is uninformative. The rule this module
enforces:

> **Desymmetrise before testing the class.**

## The count, with an error bar

The mean cannot be inverted, but the `≈240` gap ratios of a spectrum carry more than
their average. `sector_count_posterior` fits the sequence directly:

- the data are the `r`-ratios, not their mean;
- each hypothesis — `1 … 6` unresolved sectors, with GOE and GUE marginalised at equal
  weight, plus a Poisson hypothesis standing for "integrable, or more sectors than are
  distinguishable from it" — contributes a **first-order Markov model** of the binned
  sequence, fitted on 200 simulated spectra of the same size;
- the likelihood is a product *along the chain*, because consecutive `r`-ratios share a
  spacing. Treating them as independent counted the same information twice and was
  measurably overconfident: coverage `0.70` at a nominal `0.90` (measured, `d = 60`);
- the answer is a posterior over `{1, …, 6, ≥6/poisson}` and the shortest contiguous
  interval carrying 95% of its mass.

| true count | posterior on the truth | interval covers | interval is a point |
|:---|---:|---:|---:|
| 1 | `0.98` | `1.00` | `0.95` |
| 2 | `0.65` | `0.93` | `0.28` |
| 3 | `0.24` | `0.87` | `0.00` |
| 4 | `0.17` | `0.98` | `0.00` |
| 6 | `0.20` | `0.97` | `0.00` |
| Poisson | `0.20` | `0.78` | `0.00` |

Measured over 60 simulated spectra per row (`SectorCountModel.coverage`), 240 levels,
with the seeds pinned in the demo script.

The rows are three different claims, and the difference matters:

- **one sector is measured.** `0.98` on the truth, interval `1..1` in 95% of draws, and
  the posterior on `1` stays below `0.02` for every other truth — including a Poisson
  spectrum. This is a measurement, not a warning;
- **two sectors is a set.** `0.65` on the truth, with the interval typically `2..5`.
  The point estimate is right about two thirds of the time and the interval almost
  never collapses to `2..2`. "Two" is defensible; "exactly two" is not;
- **three or more is not counted.** The interval's lower bound rises with the truth
  (`P(lower ≥ 3)` is `0.65`, `0.80`, `0.83`, `0.88` at `3, 4, 5, 6` sectors) and the
  open label carries `0.63` at six. The estimator returns `≥3`, which is the original
  negative result — now with an interval instead of a shrug.

The weakest row is the Poisson one, and it deserves saying plainly: an integrable
spectrum is read as a `4–6`-sector superposition in about a fifth of the draws, because
that is what it resembles. The open label exists so the estimator is *allowed* to say
"not a finite superposition", not because it can tell the two apart.

Two limits on the calibration itself. The model is a plug-in fit from 200 spectra, so
its own uncertainty is not integrated out — one reason the measured coverage is printed
next to the nominal level (`0.87` at three sectors, `1.00` at one) rather than assumed.
And the model is tied to the spectrum size it was fitted for; `SectorCountModel.fit`
takes `total_levels` so that a mismatched model is a caller's decision, not a default.

## Precedent, and what is new here

The phenomenon is not new, and the document says so before claiming anything. That a
discrete symmetry splits a spectrum into independent blocks, and that an unresolved
block structure pushes the gap-ratio statistics toward the Poisson value, is
established. Giraud and co-workers derive gap-ratio distributions for spectra built
from several independent blocks and use them to *infer* the block structure
(*Probing symmetries of quantum many-body systems through gap ratio statistics*,
[Phys. Rev. X **12**, 011006 (2022)](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.12.011006),
[arXiv:2008.11173](https://arxiv.org/abs/2008.11173)). Their analytical formulas are
the general version of the measured table above, and they are also the reason the
table cannot be inverted for the block count in general.

What is local is the calibration for *this* `σ` structure, the warning functions, and
the recorded failure of the count. In the vocabulary of an instrument: the physics is
known, the sensor is what this module adds.

## What the utility does

`desymmetrise(H, involutions)` verifies, splits and reports:

1. every object is an involution (`U² = I`, Hermitian);
2. every involution commutes with `H` (`‖[H,U]‖/‖H‖ ≤ 1e-8`, reported);
3. the involutions commute with each other — otherwise there are no joint sectors;
4. the joint eigenspaces span the whole space;
5. every block is Hermitian.

For one `Z₂` the sectors of a `σ`-symmetric model are `spec(A + C)` and
`spec(A − C)`; that identity is checked against the blocks, not assumed. For a
`Z₂ × Z₂` — two commuting involutions — there are four sectors, checked against a
direct sum built with four known blocks.

`contamination_warnings` then compares the full-spectrum statistic with the resolved
sectors and emits up to three flags, in decreasing order of reliability:

| flag | meaning | reliability |
|:---|:---|:---|
| full mean below **every** sector by `> 0.05` | the full spectrum is a superposition | high — a comparison within one Hamiltonian, no calibration needed |
| full mean in the two-sector band `[0.40, 0.49]` | the class is unreadable there | medium — an absolute band, and one spectrum scatters by `≈0.03` |
| full mean `≤ 0.40` | consistent with `≥ 3` sectors **or** integrability | a flag only — spacing statistics cannot separate the two |

Six further entry points serve a caller that has only a spectrum — the screening case,
where the candidate operator is known and its symmetries are not:

| entry point | input | what it can say |
|:---|:---|:---|
| `contamination_warning(H, U)` | a *candidate* involution | verifies it, splits, compares — the reliable half, and it raises if `[H,U] ≠ 0` |
| `detect_hidden_symmetry(eigenvalues)` | the spectrum | a severity (`none`/`mild`/`severe`) with the integrability caveat inside its own text |
| `sector_count_posterior(eigenvalues)` | the spectrum | a posterior over `{1,…,6, ≥6/poisson}` and a 95% interval — `1` is a measurement, `2` a set, `≥3` the honest ceiling |
| `estimate_sectors_from_mean(mean_r)` | a mean `r` | `1`, `2`, or `None` — the mean-inverting estimator, kept to demonstrate the failure |
| `classify_mean(mean_r)` | a mean `r` | `goe`/`gue`/`poisson`/`intermediate`, in the windows `m5_analysis.py` uses |
| `sector_spectra(H, U)` | a candidate involution | the sector spectra, or a `ValueError` naming the failed commutation |

`sector_spectra` is the reviewer's interface with the check it lacked: their version
diagonalises the involution and keeps the diagonal blocks, which on a matrix with
`‖[H,U]‖/‖H‖ ≈ 1.2` returns arrays that are not sector spectra. The measured refusal is
in the tests.

## The honest boundary

A low `⟨r⟩` is produced by an unresolved symmetry *and* by a genuinely integrable
system, and no spacing statistic distinguishes them. The warning says so in its own
text. The fix it recommends — find the involutions, verify they commute, split, test
each sector — is the only one that works, and it requires knowing the symmetries.

Because the absolute-band flags overlap at finite size (a single GOE sector can draw
`0.49`; a two-sector GUE superposition can draw `0.46`), the utility is a **flag to
investigate**, not a classifier. Measured at `d = 60`, seeds `0 … 39`: `4` of `40` pure
single-sector GOE spectra fall below the `0.48` floor and are flagged, and `0` of `40`
GUE spectra are. A `severe` flag therefore means *do not call this Poisson yet* — not
*this is a superposition*. The reliable half is the comparison against resolved
sectors, which is exactly what the tool exists to make easy.

## Where this applies in the repository

The `σ`-sectors of the dimension-shift model are the case that produced the
misreading: `m5_analysis.py` and `dimension_shift_chaos.py` now desymmetrise before
classifying. `operator_candidates.py` screens candidates on statistics, so any
candidate with an unresolved symmetry would be biased low in the same direction —
see the note in [`operator_candidates.md`](operator_candidates.md).

Standard practice in quantum chaos; the contribution here is a measured case and a
tool that makes the mistake hard.

## Files

| File | Contents |
|:---|:---|
| `python/riemann_framework/desymmetrisation.py` | the split, the warning, the calibration table, the posterior over sector counts, and the failed mean-inverting estimator kept as the demonstration |
| `python/tests/test_desymmetrisation.py` | 37 tests: the table, both limits of the mean, the refusal to split a non-commuting matrix, and the posterior's measured accuracy and coverage |
| `scripts/run_desymmetrisation_demo.py` | the figure, the table, and the coverage rows |

## Status

A tool, and a measurement with a stated resolution: the phenomenon is standard; what is
local is a measured calibration, a warning that plugs into the screening step, a
posterior that counts one sector and bounds two, and a recorded refusal to count above
that. No statement about the Riemann hypothesis is made or implied.
