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

end RiemannFramework.DependencyTrace
