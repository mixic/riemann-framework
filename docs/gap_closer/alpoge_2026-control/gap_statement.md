# Gap statement: alpoge_2026

No verdict here means that the Riemann hypothesis is true. The strongest positive verdict is validated (term), which concerns a term and the definitions it invokes, not the mathematics those definitions are meant to carry.

**Target.** `geometry_is_vacuous` in `RiemannFramework.Dispute`.
**Verdict.** `undetermined`.

## 1. Computations

- **C1**, `#deps (Expr.getUsedConstants)`: `checked_ok`. closure of 4 names.
- **C2**, `#depsm (structural recursion)`: `checked_ok`. closure of 4 names. Substitution: laud graph is not available; #depsm is the repository's second traversal over the same environment.
- **C3**, `closure comparison`: `checked_ok`. the two closures agree.
- **C4**, `vacuous-analogue mutation`: `not_run`. the declared mutants for this theorem are content flips, not vacuous analogues; the flip is recorded as engine calibration (flip-vacuous-geometry-for-theorem-that-states-it: killed).

## 2. Closure

- C1 names: 4
- C2 names: 4

## 3. Flagged declarations

- `vacuousGeometry`: in closure True, critical. the definition is literally the trivially true shape, so the theorem's content is carried by a vacuous definition; classified by inspection, not by mutation (the declared rewrite ran and was killed, which calibrates the engine but is not a vacuous analogue)

## 4. What would move the verdict

- discharge the vacuity witness vacuousGeometry: replace it with a definition whose content the proof uses, or record it as load-bearing and reopen the objection
- run C4 (declare a vacuous-analogue mutant for each flagged declaration and re-run)

## 5. What this does not say

- It does not say the Riemann hypothesis is true, proved or refuted.
- It does not say the archive's definitions carry the mathematics their names suggest.
- It does not adjudicate the authors.
