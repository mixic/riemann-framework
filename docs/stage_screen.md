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

# Screening the sector-count programme with the DH filter

The filter in [`dh_filter.md`](dh_filter.md) is a contrapositive: an argument that goes
through unchanged for Davenport–Heilbronn, where the analogue of the Riemann hypothesis is
false, cannot establish the Riemann hypothesis. It classifies the *declared inputs* of a
candidate and returns `dead`, `eligible` or `needs_sourcing`.

It was built to be pointed at other people's proposals. This note points it at the
sector-count programme itself, which is the only way to show that it works as designed
rather than as described. The code is
[`stage_screen.py`](../python/riemann_framework/stage_screen.py); the claims are declared
there and the verdicts are computed, not written down.

## 1. The five claims

Each claim in the stage is recorded with the inventory key that would have to hold for it
to say anything about the zeros, and with the scope it actually has:

| claim | what it asserts | scope | input it would need |
|:---|:---|:---|:---|
| `boundary_map` | no spacing statistic names a count above two; pairwise separation is easier | spectra | `gue_pair_correlation` |
| `mixed_sectors` | an equal-block posterior under-counts when one block dominates | spectra | `gue_pair_correlation` |
| `real_systems` | the split lowers the statistic on three real systems | spectra | `gue_pair_correlation` |
| `diagnose` | the report verifies its involutions and states its numbers | spectra | `gue_pair_correlation` |
| `pt_symmetry` | a broken PT spectrum has no real spectrum to measure | spectra | `gue_pair_correlation` |

None of the five is a claim about the zeros. That is the first honest result, and it is
recorded in the data (`about_zeros = False`) rather than only in prose: the filter's
contrapositive applies to arguments that conclude something about the zeros, and there are
none here.

## 2. The verdicts

Every claim screens as `needs_sourcing`, which is what the filter says when a declared
input has no recorded status:

```
  boundary_map: needs_sourcing inputs=gue_pair_correlation spectra only
 mixed_sectors: needs_sourcing inputs=gue_pair_correlation spectra only
  real_systems: needs_sourcing inputs=gue_pair_correlation spectra only
      diagnose: needs_sourcing inputs=gue_pair_correlation spectra only
   pt_symmetry: needs_sourcing inputs=gue_pair_correlation spectra only

{'dead': 0, 'eligible': 0, 'needs_sourcing': 5}
```

The inventory row is this one, verbatim from
[`dh_filter.py`](../python/riemann_framework/dh_filter.py): "the zeros have the same local
spacing / pair-correlation statistics as the zeta zeros (GUE); source: none recorded". It is
one of the three rows the filter marks `unsourced`, and it is the row this entire stage
inherits.

That is the useful outcome, and it is not a criticism of the statistics. The stage measures
what a spacing statistic does on spectra it generates; it never needed the zeros' statistics
to do that, and none of its numbers is evidence about the Riemann hypothesis. What the
screen adds is a mechanical statement of the condition under which that could change: if
anyone connected the sector count to the zeros, the first thing they would owe is a source
for `gue_pair_correlation`, and the inventory does not have one.

## 3. What the screen is not

* **Not evidence for RH.** A screen that returns `needs_sourcing` has not adjudicated
  anything. It has said which input is missing.
* **Not a proof that the stage is irrelevant.** An input marked unsourced may well be true
  and citable elsewhere; the inventory's rule is that a row is only written from a source
  that was read here, and no one has read one for this row.
* **Not a checker.** The filter classifies declarations. A claim that declares the wrong
  input passes or fails for the wrong reason, which is why
  `test_the_stage_declares_five_claims` and `test_every_claim_declares_the_spectral_input`
  exist: the declaration is the part a reader cannot verify from the output.

Reproduce with:

```bash
python -c "from riemann_framework.stage_screen import stage_summary; print(stage_summary())"
```
