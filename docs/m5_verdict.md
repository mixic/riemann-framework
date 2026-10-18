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

# M5 Verdict: the decisive test for the Dimension-Shift Hypothesis

**Seeds per point:** 300
**Dimensions tested:** 100, 200 (per sector, so matrices of order 200 and 400)
**Couplings tested:** 0.5, 1.0, 2.0, 5.0
**Matrix classes tested:** GOE (real symmetric) and GUE (complex Hermitian)
**Wall-clock:** 374 s
**Artifact:** `output/m5_verdict.txt`; figures `output/m5_criterion1.png`, `output/m5_criterion2.png`

## Verdict

> **ABANDONED** — on criterion (2), the sector class is inherited.

The Dimension-Shift Hypothesis is abandoned in its current form. This is a
**result**, not a failure: it says that this construction cannot carry the zeros'
class, and it says why in terms that generalise to any lift built the same way.

## Criterion (1): structural GOE

- **Holds (all admissible classes):** **no**
- **Holds per class:** `goe = True`, `gue = False`
- **Sectors tested:** 48 (24 parameter points × 2 sectors)
- **Sectors in the GOE window `[0.51, 0.55]`:** 24
- **Sectors in the GUE window `[0.58, 0.62]`:** 24
- **Max sector mean:** `0.6017` at `d = 200`, `coupling = 0.5`, `matrix_class = gue`, sector `+1`
- **Full spectrum never in the GUE window:** `True` (measured range `0.4199 … 0.4248`)

Measured sector means:

| input blocks | sector means | class |
|:---|:---|:---|
| GOE | `0.5279 … 0.5327` | GOE |
| GUE | `0.5964 … 0.6017` | GUE |

**Why criterion (1) cannot be reported as a single verdict.** The first draft of
this analysis evaluated it with GOE blocks only, calling that "the strictest test".
It is the reverse: with GOE blocks the sectors are GOE *because GOE was put in*, so
the criterion "holds" by construction and would abandon the DSH on the strength of
an input choice. Evaluated across the admissible family it holds for one class and
fails for the other — which makes it a restatement of criterion (2), not independent
evidence. The measured `||[H, σ]||_F / ||H||_F` is `0.0` at every point, so the
sectors are genuine.

## Criterion (2): inherited class

- **Holds:** **yes**
- **GUE blocks → GUE sectors:** 2/2
- **GOE blocks → GUE sectors:** 0/2

The sector of a `σ`-symmetric model is `spec(A ± C)`. With `A`, `C` drawn from a
GUE ensemble the sectors are GUE; with `A`, `C` real symmetric they are GOE. Nothing
in the `σ` structure selects the class: **the class is an assumption about the input
blocks, not a consequence of the construction.** Any GUE result obtained this way is
therefore not evidence that the construction explains the zeros' statistics.

## Two defects found while running M5

Recorded because both produced wrong answers, and one of them produced a *favourable*
wrong answer.

**1. A label swap inverted criterion (2).** `MATRIX_CLASSES` is `("goe", "gue")`, and
the first draft assigned `gue_point = points[0]` / `goe_point = points[1]`. The first
full run therefore reported

> GUE blocks → 0 GUE sectors; GOE blocks → 2 GUE sectors — **DSH SURVIVES**

which is the opposite of the measurement and would have acquitted the hypothesis.
The points are now keyed by class name, and the tests assert
`points[i].matrix_class` so the positional assumption cannot come back. This is the
strongest argument in the repository for re-running a test that "passed".

**2. `test_`-prefixed production functions were collected by pytest.** The criteria
were named `test_criterion_1` / `test_criterion_2`. pytest collects any module-level
name beginning with `test_`, including imported ones, so `tests/test_m5_analysis.py`
silently ran the full default grid twice: about twelve minutes of hidden computation,
and `--collect-only` reported 18 items instead of 16. They are now
`evaluate_criterion_1` / `evaluate_criterion_2`, and
`test_no_imported_symbol_is_collected_as_a_test` guards the import.

## What this means

The Dimension-Shift Hypothesis is abandoned **in its current form**, for a reason
that is structural rather than numerical: a `σ`-symmetric Hamiltonian built from
random blocks inherits the universality class of those blocks. To carry the zeros'
class the construction would have to *derive* time-reversal breaking from its own
structure — a specific, non-random, arithmetic origin for `C` — rather than accept it
as an ensemble choice.

What is *not* claimed:

- This is not a proof of the Riemann Hypothesis.
- This is not a proof that no dimension-shift idea can work; one construction is
  abandoned, and the reason above says precisely which assumption has to change.
- No new evidence for or against RH is produced here.

## Reproduce

```bash
python scripts/run_m5_analysis.py      # ~6 minutes, writes output/m5_verdict.txt
cd python && python -m pytest tests/test_m5_analysis.py -q    # ~38 s
```

The suite runs the criteria on a reduced grid (`d = 100`, one or two couplings) with
the full 300 seeds, so the numbers asserted there are real multi-seed numbers.

## Files

| File | Contents |
|:---|:---|
| `python/riemann_framework/m5_analysis.py` | both criteria, sector extraction, the verdict |
| `python/tests/test_m5_analysis.py` | 17 tests, including the two regression guards |
| `scripts/run_m5_analysis.py` | the run, the artifact and the two figures |
