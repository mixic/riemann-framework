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

# The diagnostic on real systems

Every other measurement in this framework is made on Gaussian blocks. That is enough to
test a statistical claim and not enough to test a diagnostic: a spectrum that a physicist
would write down has degeneracies, lattice symmetries, and a level density with more
structure than a semicircle. This note measures what the diagnostic does there.

Three systems are built in [`real_systems.py`](../python/riemann_framework/real_systems.py),
each with an **exact** involution, verified by commutator rather than assumed:

| system | Hamiltonian | involution | commutator |
|:---|:---|:---|---:|
| transverse-field Ising chain | `-J sum sz_i sz_{i+1} - K sum sz_i sz_{i+2} - h sum sx_i` | `prod sx_i` | `0.0` |
| Heisenberg chain, zero magnetisation | `sum_b J_b S_i . S_j` over nearest and next-nearest bonds | `state -> complement` | `0.0` |
| kicked top | `exp(-i p Jz^2 / 2j) exp(-i q Jy)` | `exp(-i pi Jy)` | `1.1e-14` |

The Ising chain is measured at the free-fermion point `K = 0` and away from it at
`K = 0.3`. The Heisenberg chain is measured with `J2 = 0.5` and weak bond disorder
(`+/- 30 per cent`), which is what breaks translation and reflection so that the spin flip
is the only involution left and the full spectrum really is the union of exactly two
sectors. The kicked top is a Floquet operator, so its spectrum is a set of phases and the
statistic is taken on the circle.

## 1. The measurement

Full spectrum against its sectors, with the detector's verdict at each size. The floor is
`size_dependent_floor(n)`, the same function the screening test uses.

| system | levels | full | sectors | floor | full flagged | sector verdicts |
|:---|---:|---:|:---|---:|---|---|
| Ising, free fermions | 1024 | **0.370** | 0.500, 0.559 | 0.519 | yes | flag, clear |
| Ising, interacting | 1024 | **0.382** | 0.402, 0.359 | 0.519 | yes | flag, flag |
| Heisenberg, chaotic | 252 | **0.399** | 0.431, 0.494 | 0.506 | yes | flag, flag |
| kicked top, j = 60 | 121 | **0.418** | 0.520, 0.603 | 0.495 | yes | clear, clear |

Reference values: Poisson `0.386`, GOE `0.531`, GUE `0.600`.

Three results, one of them a defect that has since been fixed.

**The flag fires on every contaminated full spectrum.** Four of four, and on the kicked top
it also names the count: the full spectrum is read as two unresolved sectors, which is
exactly what it is. The within-Hamiltonian comparison, the manuscript's reliable warning,
is right in three of four cases: the full spectrum is below every sector's for the free
Ising chain (`0.370` against `0.500` and `0.559`), the Heisenberg chain (`0.399` against
`0.431` and `0.494`) and the kicked top (`0.418` against `0.520` and `0.603`).

**The interacting Ising chain is the counterexample.** At `K = 0.3` the sectors measure
`0.402` and `0.359`, and the second is *below* the full spectrum's `0.382`, so the ordering
that the synthetic model predicts does not hold. The chain is not a random-matrix system at
ten spins, and neither does it behave like one after one symmetry is removed. The honest
reading is that a real many-body spectrum can fail the diagnostic's assumption rather than
fail the diagnostic: the sector statistics are not RMT-like to begin with, so no
comparison of them can be.

**The absolute floor over-flags real sectors.** Only three of the eight sector spectra are
cleared. The Heisenberg sectors (`0.431`, `0.494`) sit below the floor of `0.496` for 126
levels and are flagged, although each is a single sector by construction; one Ising sector
at `0.500` misses the floor of `0.514` by `0.014`. The floor was calibrated on GOE blocks,
whose mean ratio is `0.531` at any size, while a real 126-level sector measures `0.43` to
`0.49`. That is the finite-size and mixed-dynamics content of a real spectrum, not an
unresolved symmetry, and the detector has no way to tell the two apart. The manuscript
already puts the within-Hamiltonian comparison first for this reason; this measurement is
the evidence for that ordering, on systems rather than on blocks.

## 2. The defect this found

The first run returned a *NaN* mean ratio for the free Ising chain, and the detector's
comparison against the floor then fell through to "contaminated" for a reason that had
nothing to do with symmetry.

The cause is exact degeneracies. The free chain has `113` zero spacings in `251` at ten
spins, and a zero spacing produces the ratio `0 / x = 0` (or `0 / 0`, which is the NaN).
Those zeros are not level repulsion, they are symmetry, and averaging them in moves the
statistic by a factor of two: the same spectrum measures `0.042` with them and `0.344`
without. The ratio sequence in
[`desymmetrisation.py`](../python/riemann_framework/desymmetrisation.py) now drops
degenerate spacings **before** forming the ratios, and `detect_hidden_symmetry` uses that
sequence instead of the raw one. Synthetic Gaussian blocks have no degeneracies, so every
number the manuscript quotes is unchanged by the fix, and
`test_the_detector_survives_a_degenerate_real_spectrum` pins it.

## 3. What this does not say

* **One spectrum per system.** The standard error of a mean ratio over 121 phases is about
  `0.02`, and the systems are not averaged over disorder realisations or over `(p, q)`
  points in the chaotic regime. A proper study would average, and this note reports single
  draws with that limitation stated rather than hidden.
* **Ten spins is small.** The Heisenberg sectors reach `0.43` and `0.49` against the GOE
  value `0.531`; whether that gap closes with size is exactly the question a larger
  calculation would answer, and it is not answered here.
* **The Ising chain has a further symmetry.** The periodic chain also carries translation,
  which this module does not resolve, so its full spectrum is a union over more than the
  two parity sectors. That is visible in the free case, where the sectors (`0.500`,
  `0.559`) are still below GOE.
* **Nothing here touches the Riemann hypothesis.** The zeros are not used and no claim
  about them is made.

Reproduce with:

```bash
python scripts/generate_real_systems_report.py
```

which prints the table above and rewrites `output/real_systems.png` and
`output/real_systems.csv`.
