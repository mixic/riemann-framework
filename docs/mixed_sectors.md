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

# When the sectors are not the same size

The posterior in [`desymmetrisation.md`](desymmetrisation.md) is fitted on equal blocks:
`m` sectors of `total_levels // m` levels each. That is a modelling choice, not a property
of a hidden symmetry. A sector can dominate, as it does in an asymmetric double well or
under a parity class that carries most of the spectral weight, and the question this note
answers by measurement is what that does to the count.

The property under test is falsifiable in one line: *if the count is read off the spacing
statistics, an unequal partition must not look like a different count.* It does, and the
size of the error depends on how unequal the partition is.

## 1. The construction

A spectrum is `m` independent GOE or GUE blocks, each block drawn at the same class, and the
largest block is `r` times the smallest. The total number of levels is held at 240, so the
occupation of the largest block is fixed by the pair:

```
f = r / (r + m - 1)
```

At `r = 1` the blocks are equal and the construction reduces to the manuscript's. At
`m = 2, r = 4` the blocks are `(192, 48)` and the dominant sector carries four fifths of
the levels. The union is unfolded only implicitly: the features are the mean spacing ratio
at orders one to six, computed on the raw eigenvalues as in
[`desymmetrisation.py`](../python/riemann_framework/desymmetrisation.py).

The pairs measured are `m` in `{1, 2, 3, 4, 6}` and `r` in `{1, 2, 4}`, thirteen labels in
all, with forty training spectra per label and class and two hundred test spectra per
label. The code is [`mixed_sector_count.py`](../python/riemann_framework/mixed_sector_count.py);
the numbers below are produced by
[`scripts/generate_mixed_sector_report.py`](../scripts/generate_mixed_sector_report.py).

## 2. The model, and one thing that had to be fixed

The joint posterior is Gaussian naive Bayes over the thirteen labels, on the same six
features the higher-order count model uses. Two design decisions matter and both were
forced by a measurement, not chosen:

* **The prior is uniform over counts, not over labels.** The grid is ragged, one label at
  `m = 1` and three at every larger count. A flat prior over labels would hand the counts
  with more ratios a larger total mass for no reason, and the count marginals would not be
  comparable.
* **Each label carries one Gaussian per random-matrix class.** The first version carried
  one Gaussian per label, fitted on spectra alternating GOE and GUE. It read a one-sector
  GOE spectrum as a two-sector GUE one, because the two classes differ in mean ratio by
  about `0.07` while one and six unresolved sectors differ by `0.17`. The class is now an
  explicit mixture and is summed out. The one-sector accuracy went from `0.78` to `0.905`
  when that changed, which is the measurement that justifies the extra parameters.

## 3. Does the count survive a dominant sector?

Per-class accuracy of the count's most probable value, against the equal-block model
applied unchanged to the same spectra. The last two columns are the equal-block model's own
answer, and the mean is its mean count, with the open-ended label read as 7.

| sectors | ratio | joint count | ratio given count | joint pair | 90% interval | equal-block count | equal-block mean |
|:---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | **0.905** | 1.000 | 0.905 | 0.965 | 1.000 | 1.00 |
| 2 | 1 | 0.605 | 0.785 | 0.500 | 0.915 | 0.760 | 2.22 |
| 2 | 2 | 0.605 | 0.550 | 0.330 | 0.955 | 0.780 | 2.01 |
| 2 | 4 | 0.600 | 0.740 | 0.405 | 0.910 | 0.515 | 1.51 |
| 3 | 1 | 0.590 | 0.595 | 0.315 | 0.930 | 0.505 | 3.08 |
| 3 | 2 | 0.570 | 0.490 | 0.325 | 0.895 | 0.470 | 3.04 |
| 3 | 4 | 0.405 | 0.840 | 0.325 | 0.900 | 0.290 | 2.31 |
| 4 | 1 | 0.555 | 0.625 | 0.455 | 0.900 | 0.460 | 4.33 |
| 4 | 2 | 0.375 | 0.565 | 0.150 | 0.910 | 0.450 | 4.19 |
| 4 | 4 | 0.380 | 0.855 | 0.350 | 0.915 | 0.225 | 2.98 |
| 6 | 1 | **0.875** | 0.580 | 0.505 | 0.960 | 0.560 | 5.68 |
| 6 | 2 | **0.890** | 0.500 | 0.490 | 0.975 | 0.690 | 5.83 |
| 6 | 4 | **0.735** | 0.715 | 0.470 | 0.825 | 0.300 | 4.80 |

Three statements survive the table.

**The equal-block model's error is a bias, and it points one way.** At ratio four it reads
two sectors as `1.51`, three as `2.31`, four as `2.98` and six as `4.80`: a dominant sector
costs it about a full sector at every count. That is worse than noise, because noise would
average out. The joint model's mean count is not reported here because its count is a MAP
label rather than an average, but its accuracy at the same ratio is `0.60`, `0.41`, `0.38`
and `0.74`, against `0.52`, `0.29`, `0.23` and `0.30`.

**The joint model pays for that with the decisive cases.** It is behind the equal-block
model at one sector (`0.905` against `1.000`) and at two sectors with a ratio of one or two
(`0.605` against `0.760` and `0.780`). Widening the hypothesis space is not free: three
ratio labels per count split the posterior mass, and a spectrum that is genuinely equal
partitioned now competes with its imbalanced look-alikes.

**Six sectors is the easy case, not the hard one.** At `m = 6` the joint model names the
count `0.875`, `0.890` and `0.735` across the ratios, because a six-block union is close to
Poisson whatever the block sizes and the features are correspondingly flat. This is the
same reason the manuscript's open-ended label exists: at six sectors the spectrum has
nearly stopped carrying where it came from.

## 4. Is the size ratio recoverable?

No, except at the extremes, and the middle ratio is the worst case in every row:

* `r = 4` is named correctly `0.74`, `0.84`, `0.86`, `0.72` of the time for `m = 2` to 6
  once the count is known. A four-to-one partition is visible in the higher-order ratios.
* `r = 1` is named `0.79` at two sectors but falls to `0.58` and `0.63` at six and four.
* `r = 2` is never above `0.57` and is `0.50` at six sectors: indistinguishable from a
  coin flip. A moderate imbalance is absorbed by both of its neighbours, so the posterior
  splits between `r = 1` and `r = 4` and the MAP label is a toss-up.

The pair as a pair is never identified: the joint-correct column peaks at `0.505`. The
honest summary is that the posterior can say "one sector" or "not one sector", can count
six, and cannot place a spectrum in the two-dimensional grid. Reporting the pair would be
over-claiming; reporting the count marginal, with the ratio marginal beside it, is what the
measurement supports.

## 5. Is the interval calibrated?

Nominal 90 per cent, measured on the same 2600 test spectra: `0.825` to `0.975`, with a
median of `0.915` over the thirteen labels. Only the six-sector, ratio-four cell is
under-nominal at `0.825`; the rest are at or above `0.895`. This is a frequentist coverage
of a Bayesian interval for the count with the pair summed out, which is the comparable
quantity, and it is the only one of the four numbers in the table that is not a MAP
accuracy.

## 6. What this does not say

* **There is no Poisson label.** The thirteen hypotheses are all superpositions of chaotic
  sectors, so this posterior cannot answer "integrable, or a superposition?", which is the
  question the manuscript's label set answers with its open-ended sixth label. Adding one
  is the natural next step and is not done here.
* **The spectra are synthetic and the class is balanced by construction.** Real spectra
  come with one class, and a model that has marginalised the other has paid for a
  robustness it does not need.
* **Two hundred spectra per label is a measurement, not a law.** The standard error of an
  accuracy at that size is `0.03`, so differences below `0.06` in the table should not be
  read as an ordering.
* **Nothing here touches the Riemann hypothesis.** The zeros are not used, and no claim
  about them is made.

Reproduce with:

```bash
python scripts/generate_mixed_sector_report.py
```

which prints the table above and rewrites `output/mixed_sector_count.png` and
`output/mixed_sector_count.csv`.
