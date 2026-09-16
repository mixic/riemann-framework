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

/-
  SanityChecks.lean

  Small examples that verify the definitions behave as expected.
-/

import Mathlib.Analysis.Complex.Basic
import RiemannFramework.ZetaConjecture

open Complex

namespace RiemannFramework

/--
  Sanity check: σ(0) = 1, not a fixed point.
-/
example : sigma 0 = 1 := by
  unfold sigma
  simp

/--
  Sanity check: σ(1/2) = 1/2, so 1/2 is a fixed point.
-/
example : sigma (1/2 : ℂ) = 1/2 := by
  apply fixed_point_of_re_eq_half
  simp

/--
  Sanity check: σ(1/2 + 14.134725 * I) is a fixed point.
-/
example : sigma (1/2 + 14.134725 * I) = 1/2 + 14.134725 * I := by
  apply fixed_point_of_re_eq_half
  simp

/--
  Sanity check: 0.3 is not a fixed point.
-/
example : sigma (0.3 : ℂ) ≠ 0.3 := by
  intro h
  have h_re := re_of_fixed_point_eq_half h
  norm_num at h_re

end RiemannFramework
