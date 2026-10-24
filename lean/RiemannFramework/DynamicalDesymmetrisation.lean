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

import Mathlib.Algebra.Group.Commute.Basic
import Mathlib.RingTheory.NonUnitalSubsemiring.Basic

/-!
# The double-bracket flow preserves a symmetry

The dynamical desymmetriser in `dynamical_desymmetrisation.py` integrates

    d rho / d beta = [[rho, H], rho] = 2 rho H rho - H rho^2 - rho^2 H,

and the invariance it tests is that a state commuting with an involution `sigma` keeps
commuting with it, provided `H` does too. This file proves the algebraic step that the
test measures: the increment commutes with `sigma`, so one Euler step stays inside the
commutant, and by induction so does the trajectory.

The proof is about an associative ring, not about matrices, because the argument never
uses anything else: `Commute` is closed under products, sums and differences, and the
increment is built from `rho` and `H` with those operations only.

A warning about what this does *not* prove. It says the symmetry is preserved, which is
a statement about a trajectory. It says nothing about the flow desymmetrising a
Hamiltonian -- `H` is a constant of the flow, and the flow is isospectral in `rho` --
and nothing about the Riemann hypothesis.
-/

namespace RiemannFramework

variable {R : Type*}

/-- One Euler increment of the double-bracket flow, `[[rho, H], rho]`, written out so
that no intermediate commutator is formed twice. -/
def doubleBracketIncrement [Ring R] (rho H : R) : R :=
  2 * rho * H * rho - H * rho * rho - rho * rho * H

/-- **The increment commutes with a symmetry that commutes with `rho` and `H`.**

This is the algebraic content of "the flow preserves the sectors": since the increment
lies in the commutant, one Euler step stays there. -/
theorem commute_doubleBracketIncrement [Ring R] {rho H sigma : R}
    (hH : Commute H sigma) (hrho : Commute rho sigma) :
    Commute (doubleBracketIncrement rho H) sigma := by
  unfold doubleBracketIncrement
  have h2 : Commute (2 : R) sigma := by
    have hsum : Commute ((1 : R) + 1) sigma :=
      (Commute.one_left sigma).add_left (Commute.one_left sigma)
    simpa [one_add_one_eq_two] using hsum
  have first : Commute (2 * rho * H * rho) sigma :=
    ((h2.mul_left hrho).mul_left hH).mul_left hrho
  have second : Commute (H * rho * rho) sigma := (hH.mul_left hrho).mul_left hrho
  have third : Commute (rho * rho * H) sigma := (hrho.mul_left hrho).mul_left hH
  exact (first.sub_left second).sub_left third

/-- **One Euler step of the flow stays in the commutant.**

The time step `k` must itself commute with `sigma`; every realistic step (a rational or
real scalar) does. Iterating the step, or taking a limit, therefore keeps the state
inside the commutant for the whole trajectory. -/
theorem commute_euler_step [Ring R] {rho H sigma k : R}
    (hH : Commute H sigma) (hrho : Commute rho sigma) (hk : Commute k sigma) :
    Commute (rho + k * doubleBracketIncrement rho H) sigma :=
  hrho.add_left (hk.mul_left (commute_doubleBracketIncrement hH hrho))

end RiemannFramework
