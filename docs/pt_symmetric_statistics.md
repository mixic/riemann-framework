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

# PT symmetry: what the sector diagnostic does, measured

The rest of this framework uses **linear** involutions on **Hermitian** operators. A PT
symmetry is neither: it is anti-linear, so `[H, PT] = 0` is a statement about a map with
no matrix, and the operator is not Hermitian, so its eigenvalues are complex. The
dictionary between the critical-line reflection and a PT-symmetric level pairing is in
[`pt_symmetric_hilbert_polya.md`](pt_symmetric_hilbert_polya.md), and it is a statement
about vocabulary rather than about evidence.

This note asks a narrower and answerable question: if a spectrum carries a PT symmetry,
what do the sector tools measure? The answer is measured in
[`pt_symmetric_statistics.py`](../python/riemann_framework/pt_symmetric_statistics.py) and
produced by
[`scripts/generate_pt_symmetric_report.py`](../scripts/generate_pt_symmetric_report.py).

## 1. Why the machinery does not apply, in two sentences

A sector decomposition needs a linear involution: an operator with a matrix, whose `+1`
and `-1` eigenspaces are subspaces and therefore have dimensions. An anti-linear symmetry
has eigen*values* but not eigenspaces in that sense, and `sector_blocks` cannot be called
on it at all. The second obstruction is the spectrum: a broken PT operator has conjugate
pairs, and a gap ratio needs an ordered real spectrum.

Both are visible as code behaviour rather than as prose. `analyse_hamiltonian` raises
`the Hamiltonian is not symmetric` on the ensemble below, before it can compute anything
misleading.

## 2. The dimer, which is exact

`H = [[level + i gamma, g], [g, level - i gamma]]` has eigenvalues
`level +/- sqrt(g^2 - gamma^2)`, so they are real below `gamma / g = 1` and a conjugate
pair above it:

| `gamma / g` | eigenvalues | phase |
|---:|:---|:---|
| 0.00 | `-1.0000, +1.0000` | unbroken |
| 0.50 | `-0.8660, +0.8660` | unbroken |
| 0.75 | `-0.6614, +0.6614` | unbroken |
| 1.00 | `0, 0` | exceptional point |
| 1.25 | `-0.7500i, +0.7500i` | broken |
| 1.50 | `-1.1180i, +1.1180i` | broken |
| 2.00 | `-1.7321i, +1.7321i` | broken |

The closed form and the matrix agree to machine precision, and the collision at
`gamma = g` is exact. This is the only place in the note where a statement is
mathematical rather than statistical, and it is the reason the crossover is not an
artefact of sampling.

## 3. The random ensemble, which is generically broken

Every real matrix commutes with complex conjugation, so `H = S + w A`, with `S` Gaussian
symmetric and `A` Gaussian antisymmetric, is a PT-symmetric ensemble with `PT = conj`.
`w = 0` is the Hermitian control. Dimension 120, forty spectra per point:

| `w` | unbroken | real-part `<r>` | `mean |Im E| / spacing` | pairing defect |
|---:|---:|---:|---:|---:|
| 0.00 | 1.00 | **0.5343** | 0.000 | 0 |
| 0.05 | 0.00 | 0.5389 | 0.018 | 0 |
| 0.10 | 0.00 | 0.5322 | 0.116 | 0 |
| 0.20 | 0.00 | 0.4847 | 0.551 | 0 |
| 0.30 | 0.00 | 0.4272 | 1.271 | 0 |
| 0.50 | 0.00 | 0.4013 | 3.476 | 0 |
| 1.00 | 0.00 | 0.3925 | 13.539 | 0 |

Three readings, in order of how much they can be trusted.

**The unbroken phase does not survive a generic perturbation.** At dimension 120 not one
of the forty spectra with `w = 0.05` has a real spectrum. The control at `w = 0` is
unbroken in all forty and its mean ratio is `0.5343`, within `0.003` of the GOE value, so
the code and the sample are sound; the brokenness is the physics of a random real matrix,
not a bug. An unbroken PT phase needs structure, as in the dimer, and it is wrong to
assume it.

**The pairing is exact when the spectrum is not.** The pairing defect, the largest
distance from an eigenvalue's conjugate to its nearest partner, is `0` at every `w`,
including the ones where every eigenphase is complex. This is the invariant a PT symmetry
actually supplies, and it is precisely what the sector machinery cannot represent: it is
a pairing of levels, not a decomposition into subspaces.

**The ratio of the real parts is a measurement of the projection.** It runs from the GOE
value `0.534` to `0.393` as `w` grows. A user who applied the sector-count posterior to
the real parts of a fully broken spectrum would be told "Poisson, or six or more sectors,
or integrable": the artefact of a projection reported as a property of the spectrum. The
one number that would have warned them is `mean |Im E| / spacing = 13.5` at `w = 1`, which
says the real parts are not where the levels are.

## 4. What this does not say

* **One ensemble, one dimension, one symmetric/antisymmetric decomposition.** The dimer
  is exact but has two levels; the ensemble is a single family at dimension 120. The
  unbroken fraction at `w = 0.05` is size-dependent, which the test file records: at
  dimension 40 the same point keeps half its spectra unbroken. The doc reports the size it
  used rather than a size-free claim.
* **A structured PT model could behave differently.** Altland-Zirnbauer classes with a
  PT symmetry have their own universality, and this module does not attempt them.
* **None of this is evidence for the Riemann hypothesis.** The dictionary note says why:
  translating `sigma`-invariance into a level pairing changes the vocabulary, not the
  content. No zero of `zeta` is used here.

Reproduce with:

```bash
python scripts/generate_pt_symmetric_report.py
```

which prints the two tables and rewrites `output/pt_symmetric.png` and
`output/pt_symmetric.csv`.
