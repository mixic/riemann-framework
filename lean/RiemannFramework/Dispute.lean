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

import Mathlib.NumberTheory.LSeries.RiemannZeta

/-!
# The Alpöge–Nielsen dispute, recorded and not adjudicated

This file records two positions about a claimed proof of the Riemann hypothesis, and it is
explicit about what it can and cannot carry.

## What can be stated

**Alpöge's position is a mathematical proposition.** He claims the statement is proved, and
the statement is Mathlib's own `RiemannHypothesis`. It is recorded below with `sorry`, like
the target file `RiemannHypothesis.lean`, and it is *not* a result of this repository.

## What cannot be stated

**Nielsen's position is not a mathematical proposition.** She does not claim the statement is
false; she claims that the published formalisation *establishes nothing*, because the
geometry predicate it uses is defined to be constantly `True`, so its obligations are
discharged without witnesses. That is a claim about source code. It cannot be stated as a
theorem about `RiemannHypothesis`, and encoding it as `¬ RiemannHypothesis` would misstate
her. Lean's type theory cannot state it either: proof irrelevance identifies all proofs of a
proposition, so "this proof is vacuous, that one is not" is not expressible.

What *is* expressible, and is the mathematical core of the objection, is the behaviour of a
certificate predicate under a closure. Two facts are **proved** below, with no `sorry`:

* a certificate predicate that is constantly `True` discharges its closure at every index,
  having checked nothing (`closed_of_vacuous`);
* a certificate predicate that is constantly `False` discharges nothing
  (`closed_false_impossible`).

Together they say that the closure carries exactly the content of its predicate and no more.
The archive's geometry closure has this shape; whether the archive's final theorem is reached
through the vacuous instance is the open dependency question, and it is `sorry` below.

## Status

Both `sorry`s are deliberate and the file is registered in `OPEN_RH_FILES`
(`python/tests/test_formal_proof.py`), so the test suite fails if either is removed: a file
that asserts RH and its objection cannot be allowed to report itself complete.

It is deliberately **not** imported by the aggregate module `RiemannFramework.lean`, which
imports only the sorry-free files; the two positions are recorded here, not compiled into the
library's claims.
-/

namespace RiemannFramework

/-! ## The disputed statement -/

/-- The statement under dispute: Mathlib's own definition, the one the comparator checked
against Alpöge's theorem. -/
def RiemannHypothesisStatement : Prop := RiemannHypothesis

/-! ## The structural core of the objection, proved -/

/-- The geometry predicate as the disputed archive defines it: constantly `True` on its
three arguments, so every obligation is discharged by `trivial`. -/
def vacuousGeometry (_D _J _X : Nat) : Prop := True

/-- A closure that carries a certificate along steps: the shape of the archive's `GeoCl`. -/
inductive Closed (P : Nat → Prop) : Nat → Prop
  /-- The certificate at an index. -/
  | base (n : Nat) : P n → Closed P n
  /-- The certificate carried to the next index. -/
  | step {n : Nat} : Closed P n → Closed P (n + 1)

/-- A constantly-true certificate discharges its closure at every index, having checked
nothing. This is the checkable content of Nielsen's objection, and it is not in dispute. -/
theorem closed_of_vacuous (n : Nat) : Closed (fun _ : Nat => True) n := by
  induction n with
  | zero => exact Closed.base 0 trivial
  | succ k ih => exact Closed.step ih

/-- A constantly-false certificate discharges nothing, so the closure is not automatic: it
carries exactly the content of its predicate. -/
theorem closed_false_impossible (n : Nat) : ¬ Closed (fun _ : Nat => False) n := by
  intro h
  induction h with
  | base _ hm => exact hm
  | step _ ih => exact ih

/-- The archive's geometry obligations, as quoted, are satisfied by every input. -/
theorem geometry_is_vacuous : ∀ D J X : Nat, vacuousGeometry D J X := fun _ _ _ => trivial

/-! ## The two positions, recorded -/

/-- **Alpöge's position** (2026-11-20): the statement is proved, by the released archive.

`sorry`: this is an assertion about a proof that lives outside this repository. It is not a
result of this repository, and the file is registered so that it can never report otherwise. -/
theorem alpoge_position : RiemannHypothesisStatement := by sorry

/-- A model of the one fact Nielsen's objection turns on: whether the archive reaches its
conclusion through the constantly-true geometry predicate. -/
structure Archive where
  /-- Does the archive's closing chain pass through the vacuous geometry predicate? -/
  routesThroughVacuous : Bool

/-- An archive *grounds* a statement only if it does not route through vacuous obligations.
The definition is deliberately the simplest one that makes the dispute stateable. -/
def Grounds (a : Archive) (P : Prop) : Prop := a.routesThroughVacuous = false ∧ P

/-- **The proved half of Nielsen's argument**: an archive that routes through vacuous
obligations grounds nothing. This is a theorem, not an opinion. -/
theorem vacuous_route_grounds_nothing (a : Archive) (h : a.routesThroughVacuous = true)
    (P : Prop) : ¬ Grounds a P := by
  intro hg
  have hf : a.routesThroughVacuous = false := hg.1
  rw [h] at hf
  exact Bool.noConfusion hf

/-- **Nielsen's position** (2026-11-21): the published archive routes its conclusion through
the vacuous geometry predicate, so it grounds nothing.

`sorry`: the first conjunct is a fact about 61 GB of published source, and the dependency
trace that would settle it has not been done, here or publicly. This repository asserts
nothing either way. The second conjunct is the proved lemma above, once the premise holds;
what is unverified, and what the `sorry` stands for, is the premise. -/
theorem nielsen_position (published : Archive) :
    published.routesThroughVacuous = true ∧
      ¬ Grounds published RiemannHypothesisStatement := by sorry

end RiemannFramework
