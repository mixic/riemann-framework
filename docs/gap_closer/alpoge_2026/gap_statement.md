# Gap statement: alpoge_2026

No verdict here means that the Riemann hypothesis is true. The strongest positive verdict is validated (term), which concerns a term and the definitions it invokes, not the mathematics those definitions are meant to carry.

**Target.** `Main.riemannHypothesis` in `Main`.
**Verdict.** `undetermined`.

## 1. Computations

- **C1**, `#deps (Expr.getUsedConstants)`: `not_run`. C:\alpoge-archive\src\TraceProbe.lean:1:0: error: object file 'C:\alpoge-archive\.lake\build\lib\lean\Formalism\LocalToGlobal\SiegelLatticeTheory\CasimirReductionTheory\OneParameterDerivatives\TauReduction\BlockGramReduction\LatticeFinitelyGeneratedOfCommensurable.olean' of modul.
- **C2**, `#depsm (structural recursion)`: `not_run`. C:\alpoge-archive\src\TraceProbe.lean:1:0: error: object file 'C:\alpoge-archive\.lake\build\lib\lean\Formalism\LocalToGlobal\SiegelLatticeTheory\CasimirReductionTheory\OneParameterDerivatives\TauReduction\BlockGramReduction\LatticeFinitelyGeneratedOfCommensurable.olean' of modul. Substitution: laud graph is not available; #depsm is the substitute.
- **C3**, `closure comparison`: `not_run`. no closure to compare.
- **C4**, `vacuous-analogue mutation`: `not_run`. no vacuous analogue has been declared from the archive's own sources yet.

## 2. Closure

- C1 names: not computed
- C2 names: not computed

## 3. Flagged declarations

- none

## 4. What would move the verdict

- run C1 (build the archive on a filesystem without the Windows 260-character path limit, then re-run)
- run C2 (build the archive on a filesystem without the Windows 260-character path limit, then re-run)
- run C3 (run C1 and C2)
- run C4 (for every flagged declaration in the closure, replace its body with a vacuous analogue in a copy of the archive, recompile the target, and record the outcome)

## 5. What this does not say

- It does not say the Riemann hypothesis is true, proved or refuted.
- It does not say the archive's definitions carry the mathematics their names suggest.
- It does not adjudicate the authors.
