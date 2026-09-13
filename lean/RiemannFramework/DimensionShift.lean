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

namespace RiemannFramework

/-- A two-sector label for the finite dimension-shift model. -/
inductive Sector where
  | boson
  | fermion
  deriving DecidableEq, Repr

/-- The sector-swapping involution. -/
def sigma : Sector → Sector
  | .boson => .fermion
  | .fermion => .boson

/-- Applying the sector swap twice returns to the original sector. -/
theorem sigma_squared (sector : Sector) : sigma (sigma sector) = sector := by
  cases sector <;> rfl

theorem sigma_injective : Function.Injective sigma := by
  intro left right equality
  simpa [sigma_squared left, sigma_squared right] using congrArg sigma equality

theorem sigma_not_fixed (sector : Sector) : sigma sector ≠ sector := by
  cases sector <;> decide

end RiemannFramework
