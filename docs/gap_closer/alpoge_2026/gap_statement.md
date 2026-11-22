# Gap statement: alpoge_2026

No verdict here means that the Riemann hypothesis is true. The strongest positive verdict is validated (term), which concerns a term and the definitions it invokes, not the mathematics those definitions are meant to carry.

**Target.** `riemannHypothesis` in the archive, whose module is not yet identified.
**Verdict.** `undetermined`.

## 1. Computations

- **C1**, `#deps (Expr.getUsedConstants)`: `not_run`. archive precondition failed (archive directory: missing, lakefile: missing, lean-toolchain: missing).
- **C2**, `#depsm (structural recursion)`: `not_run`. archive precondition failed (archive directory: missing, lakefile: missing, lean-toolchain: missing). Substitution: laud graph is not available; #depsm is the substitute.
- **C3**, `closure comparison`: `not_run`. no closure to compare.
- **C4**, `vacuous-analogue mutation`: `not_run`. no flagged declaration was reachable.

## 2. Closure

- C1 names: not computed
- C2 names: not computed

## 3. Flagged declarations

- none

## 4. What would move the verdict

- run C1 (clone https://github.com/Deicyde/riemann-hypothesis into external/alpoge-lean (931 MB; needs core.longpaths), build it with its own lakefile under Lean v4.33.1 and Mathlib 0df444a3, then re-run this script with --archive external/alpoge-lean)
- run C2 (clone https://github.com/Deicyde/riemann-hypothesis into external/alpoge-lean (931 MB; needs core.longpaths), build it with its own lakefile under Lean v4.33.1 and Mathlib 0df444a3, then re-run this script with --archive external/alpoge-lean)
- run C3 (run C1 and C2)
- run C4 (run C1--C3, then declare a vacuous analogue from the archive's own source)

## 5. What this does not say

- It does not say the Riemann hypothesis is true, proved or refuted.
- It does not say the archive's definitions carry the mathematics their names suggest.
- It does not adjudicate the authors.
