-- Riemann Framework
-- Copyright (C) 2026 MILAN NIKOLIC
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.

import Lean

/-!
# Transitive dependency closure of a proved theorem

This file exists for one question, and it is the question an objection of the
Alpoge–Nielsen kind turns on: **does the compiled term of the final theorem reach the
definitions whose obligations were discharged vacuously?**

A kernel check answers something else. `#print axioms` reports which *axioms* a term
uses, and a proof whose geometry predicate is `fun _ _ _ => True` uses none beyond the
standard three: the vacuous definitions are definitions, not axioms, so they are
invisible to the axiom audit. That is why `docs/alpoge_nielsen_dispute.md` §3 lists
"reading the dependency graph" as the check that decides the dispute, and why the paper
names it as the decisive computation for the 2026 Alpoge claim.

## What `#deps` computes

Given a constant, `#deps` walks `Environment.find?` over the constant's *type* and
*value*, collecting every constant it can reach, transitively. The closure includes what
the statement mentions and what the proof term uses; a name that never appears there
cannot have contributed to the theorem.

## Two extractors, on purpose

A closure is a claim about a term, and a claim about a term that rests on one traversal of
one API is a claim with an unexamined premise: if `Expr.getUsedConstants` skipped a
constructor, the closure would be short and nothing would say so. So the closure is
computed twice, by two independent traversals of the same environment:

* `#deps` walks expressions with `Expr.getUsedConstants`, Lean's own collector;
* `#depsm` walks them with `usedConstantsManual`, the structural recursion written out
  here, case by case.

The two must agree exactly. `#depscmp` prints the difference when they do not, and the
agent records `only_in_deps` / `only_in_depsm` in the cross-validation payload rather than
picking one. **What the pair does not close:** both read the same environment, so a defect
in Lean's environment — or in Mathlib's definitions, which is the assumption the MIT
verification page states for its own checks — is invisible to both. The pair rules out a
defect in *this* module's traversal, not a defect in the data. It is not a second
implementation of Lean, and this file does not claim to be one.

## What it does not compute

* It is **syntactic over the environment**, not a semantic analysis: it says a name is
  reachable, not that the name's content is load-bearing. A definition reached only
  through an unused hypothesis is still reached.
* It says nothing about whether a reached definition is *true*, only that the term
  mentions it.
* Reachability of a vacuous definition is therefore evidence that the objection's route
  exists, not proof that the conclusion depends on it semantically. The distinction is
  recorded, not glossed: see `docs/claim_verification_agent.md`.
* It uses only `Lean` core (`Environment`, `ConstantInfo`, `Expr.getUsedConstants`), so
  it needs no Mathlib and builds against any Lean 4 toolchain whose core API is stable.
  It was compiled here against Lean v4.34.0-rc2; the pinned archive of the 2026 claim is
  v4.33.1, and that gap is stated in the paper rather than assumed away.

## Usage

```lean
import RiemannFramework.DependencyTrace
#deps RiemannFramework.geometry_is_vacuous
```

prints

```
DEPS_BEGIN
RiemannFramework.geometry_is_vacuous
RiemannFramework.vacuousGeometry
...
DEPS_END
```

`python scripts/audit_claim.py` parses exactly that block. Nothing here is part of the
library's claims, so the aggregate module does not import it.
-/

namespace RiemannFramework.DependencyTrace

open Lean

/-- One step of the walk: pop a name, record it, and push everything it mentions. -/
partial def visit (env : Environment) (stack : List Name) (acc visited : NameSet) :
    NameSet × NameSet :=
  match stack with
  | [] => (acc, visited)
  | n :: rest =>
    if visited.contains n then
      visit env rest acc visited
    else
      let visited := visited.insert n
      match env.find? n with
      | none => visit env rest acc visited
      | some info =>
        let acc := acc.insert n
        -- `Expr.getUsedConstants` returns an `Array Name` in this toolchain; the
        -- previous `NameSet` spelling is what the same call returned in 4.26.
        let mentioned : Array Name :=
          info.type.getUsedConstants ++
            (match info.value? with
             | some value => value.getUsedConstants
             | none => #[])
        visit env (mentioned.toList ++ rest) acc visited

/-- Every constant reachable from `root` through types and values, including `root`. -/
def closure (env : Environment) (root : Name) : NameSet :=
  (visit env [root] NameSet.empty NameSet.empty).1

/-- `#deps name` prints the transitive closure of `name` between two markers. -/
elab "#deps " n:ident : command => do
  let env ← Lean.getEnv
  let deps := closure env n.getId
  let names := deps.toList.map (fun name => toString name)
  logInfo m!"DEPS_BEGIN {n.getId}"
  logInfo m!"DEPS_COUNT {names.length}"
  for name in names do
    logInfo m!"{name}"
  logInfo m!"DEPS_END"

/-! ## The second extractor

`usedConstantsManual` is the same relation as `Expr.getUsedConstants`, written out. It is
deliberately a *different* implementation and not a wrapper: a wrapper would agree by
construction and would measure nothing. If the two disagree, one of them is wrong about
this expression, and the disagreement is the finding.
-/

/-- Every constant mentioned by an expression, collected by an explicit structural walk. -/
partial def usedConstantsManual (e : Expr) (acc : NameSet) : NameSet :=
  match e with
  | .const n _ => acc.insert n
  | .app f a => usedConstantsManual a (usedConstantsManual f acc)
  | .lam _ t b _ => usedConstantsManual b (usedConstantsManual t acc)
  | .forallE _ t b _ => usedConstantsManual b (usedConstantsManual t acc)
  | .letE _ t v b _ =>
    usedConstantsManual b (usedConstantsManual v (usedConstantsManual t acc))
  | .mdata _ b => usedConstantsManual b acc
  | .proj _ _ b => usedConstantsManual b acc
  | .sort _ | .bvar _ | .fvar _ | .mvar _ | .lit _ => acc

/-- The same walk as `visit`, over the manual collector. -/
partial def visitManual (env : Environment) (stack : List Name) (acc visited : NameSet) :
    NameSet × NameSet :=
  match stack with
  | [] => (acc, visited)
  | n :: rest =>
    if visited.contains n then
      visitManual env rest acc visited
    else
      let visited := visited.insert n
      match env.find? n with
      | none => visitManual env rest acc visited
      | some info =>
        let acc := acc.insert n
        let mentioned : NameSet :=
          usedConstantsManual info.type
            (match info.value? with
             | some value => usedConstantsManual value NameSet.empty
             | none => NameSet.empty)
        visitManual env ((mentioned.toList) ++ rest) acc visited

/-- Every constant reachable from `root`, by the manual traversal. -/
def closureManual (env : Environment) (root : Name) : NameSet :=
  (visitManual env [root] NameSet.empty NameSet.empty).1

/-- `#depsm name` prints the manual traversal's closure in the `#deps` format. -/
elab "#depsm " n:ident : command => do
  let env ← Lean.getEnv
  let deps := closureManual env n.getId
  let names := deps.toList.map (fun name => toString name)
  logInfo m!"DEPS_BEGIN {n.getId}"
  logInfo m!"DEPS_COUNT {names.length}"
  for name in names do
    logInfo m!"{name}"
  logInfo m!"DEPS_END"

/-- `#depscmp name` prints the disagreement between the two extractors, and nothing else.

The agent runs the two extractors separately, so that one failure cannot take the other
down with it; this command exists so that a person can see the difference directly. -/
elab "#depscmp " n:ident : command => do
  let env ← Lean.getEnv
  let a := closure env n.getId
  let b := closureManual env n.getId
  logInfo m!"CMP_COUNT {a.toList.length} {b.toList.length}"
  for name in a.toList do
    unless b.contains name do
      logInfo m!"CMP_ONLY_DEPS {name}"
  for name in b.toList do
    unless a.contains name do
      logInfo m!"CMP_ONLY_DEPSM {name}"
  logInfo m!"CMP_END"

end RiemannFramework.DependencyTrace
