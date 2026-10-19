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

This module provides the split and the warning. It is a tool, not a result about the
zeta function, and it exists because the same mistake was made in this repository:
the dimension-shift model's class was tested on the full spectrum of a `σ`-symmetric
Hamiltonian, which is why a GOE model appeared to reach GUE statistics.

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

## The two limits

**It detects but does not count.** The map from `⟨r⟩` to the number of sectors is
many-to-one, and the single-spectrum scatter (`≈0.03`) is comparable to the gaps
between successive sector counts (`0.426 → 0.404 → 0.396`). `estimate_sector_count`
inverts the table and is included to *demonstrate* the failure: for a true `N = 4` it
returns values spread over `2 … 4`, and below the three-sector level it saturates at
the largest tabulated count instead of reporting "cannot tell". The reviewer's
attempt returned `12` for a true `4`; the magnitude is a property of the estimator,
the instability is a property of the data.

**At two sectors the class information is erased.** GOE gives `0.426` and GUE `0.421`
— a difference smaller than either standard deviation. A class test run on a
two-sector full spectrum is not noisy, it is uninformative. The rule this module
enforces:

> **Desymmetrise before testing the class.**

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

Five further entry points serve a caller that has only a spectrum — the screening case,
where the candidate operator is known and its symmetries are not:

| entry point | input | what it can say |
|:---|:---|:---|
| `contamination_warning(H, U)` | a *candidate* involution | verifies it, splits, compares — the reliable half, and it raises if `[H,U] ≠ 0` |
| `detect_hidden_symmetry(eigenvalues)` | the spectrum | a severity (`none`/`mild`/`severe`) with the integrability caveat inside its own text |
| `estimate_sectors_from_mean(mean_r)` | a mean `r` | `1`, `2`, or `None` — deliberately never a count above two |
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
| `python/riemann_framework/desymmetrisation.py` | the split, the warning, the calibration table, the failed estimator |
| `python/tests/test_desymmetrisation.py` | 28 tests, including the table, both limits, and the refusal to split a non-commuting matrix |
| `scripts/run_desymmetrisation_demo.py` | the figure and the table |

## Status

An instrument: the phenomenon is standard, and what is new here is a measured
calibration, a warning that plugs into the screening step, and a recorded failure to
count. No statement about the Riemann hypothesis is made or implied.
