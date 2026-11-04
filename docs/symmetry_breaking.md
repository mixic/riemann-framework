# Symmetry breaking: the diagnostic's degradation curve

The static diagnostic assumes `[H, σ] = 0` exactly. A real device has finite
manufacturing tolerances, stray fields and measurement resolution, so the
symmetry is only approximate. This note measures what happens to the diagnostic
when it is.

## 1. The perturbation and the dimensionless parameter

```
H(g) = H0 + g · Δ · V
```

- `H0` is block diagonal in two equal GOE sectors of 120 levels each (240 total).
- `V` is a full GOE matrix of the same dimension.
- `Δ` is the mean level spacing of `H0` over the central 80 % of its spectrum.
- `g = ε/Δ` is the ratio of the mixing matrix element to the level spacing.

`g` is the parameter that transfers between matrix sizes. A raw `ε` does not:
`Δ` shrinks with the dimension, so the same `ε` breaks a large matrix much more
than a small one. Everything below is stated in `g`.

## 2. Measured curve

The posterior is the one fitted on **exact** sectors (240 levels, 200 training
spectra per hypothesis); it is not retrained on broken spectra. Each draw uses
one `H0` and one `V`; all `g` points share that pair. 60 draws per point,
`scripts/run_symmetry_breaking.py`.

| g | mean r | flag rate | MAP accuracy | 95 % coverage |
|---:|---:|---:|---:|---:|
| 0.00 | 0.427 | 1.00 | 0.62 | 0.88 |
| 0.05 | 0.433 | 1.00 | 0.63 | 0.90 |
| 0.10 | 0.446 | 1.00 | 0.73 | 0.98 |
| 0.20 | 0.474 | 0.97 | 0.87 | 0.97 |
| **0.30** | **0.494** | **0.70** | **0.53** | **0.70** |
| 0.40 | 0.507 | 0.45 | 0.40 | 0.50 |
| 0.50 | 0.516 | 0.32 | 0.18 | 0.37 |
| 0.75 | 0.526 | 0.15 | 0.05 | 0.15 |
| 1.00 | 0.529 | 0.10 | 0.05 | 0.08 |
| 2.00 | 0.532 | 0.17 | 0.08 | 0.12 |
| 5.00 | 0.527 | 0.18 | 0.07 | 0.07 |
| 10.00 | 0.529 | 0.07 | 0.00 | 0.07 |

**Critical value:** `g_c = 0.3`, the first grid point at which the MAP accuracy
falls below `0.5` or the 95 % coverage falls below `0.8`. Both thresholds are
arguments to `degradation_curve`, not hidden constants:

```python
from riemann_framework.symmetry_breaking import degradation_curve
curve = degradation_curve(g_values=(0.0, 0.3, 0.5), draws=20)
print(curve.critical_g, curve.accuracy_threshold, curve.coverage_threshold)
```

At `g = 0.3` the mixing matrix element is about a third of the mean level
spacing; the sectors are no longer isolated, and the posterior's interval
under-covers. By `g = 0.5` the spectrum is read as a single sector, which is
correct: the sectors are mixed.

## 3. What is surprising, and what is not

The curve is **not monotone**. Between `g = 0` and `g = 0.2` the posterior's MAP
accuracy rises from `0.62` to `0.87` and coverage from `0.88` to `0.97`, before
collapsing at `0.3`. That is a measured property of this classifier, not a
story about perturbation "helping":

- the model is trained on exact finite-size sectors, and a small perturbation
  moves a spectrum away from a finite-size corner of that training distribution;
- the effect disappears as soon as `g` reaches a sizeable fraction of `Δ`;
- the flag (a single mean) is more robust than the count (the sequence): it stays
  at `1.00` through `g = 0.1`, whereas the MAP accuracy has already improved and
  then collapsed.

The correct statement is the boundary, not the plateau: the posterior is usable
while `g ≲ 0.2`, loses coverage at `g ≈ 0.3`, and by `g ≈ 0.5` the symmetry is
gone in the data. A user who quotes a raw tolerance should convert it to `g`
first.

## 4. Why this belongs in the paper

Section 5.2 of the manuscript measures robustness to the posterior's own
simulator (unequal sectors, mixed class, awkward density). Symmetry breaking is a
different axis: the data themselves no longer satisfy the hypothesis. This note
supplies the missing axis and a measured `g_c`. It also makes the appendix D
claims (calibration, device monitoring) honest: they hold only while the
symmetry is intact to a fraction of a level spacing.

## 5. Limitations

- Two equal GOE sectors; unequal sectors and GUE blocks are not swept here.
- The perturbation is a full GOE matrix; structured perturbations (a single
  matrix element, a local field) can break the symmetry more efficiently.
- The model is trained on 240-level spectra; the curve is tied to that size.
- `g_c` depends on the stipulated thresholds (`0.5` accuracy, `0.8` coverage).
  Other thresholds give other numbers; the **curve** is the result.

## 6. Reproduction

```bash
python scripts/run_symmetry_breaking.py --draws 60 --seed 0
python -m pytest python/tests/test_symmetry_breaking.py -q
```

The script writes `output/symmetry_breaking.csv` with the table above.
