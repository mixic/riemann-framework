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

/-- The sector-swapping involution on the finite model's labels.

Named `sectorSwap` rather than `sigma` on purpose: `RiemannFramework.sigma` is
already the critical-line reflection `s ↦ 1 - conj s` in `ZetaBridge.lean`, and
both declarations live in the `RiemannFramework` namespace. Two `sigma`s there
would make any file importing both fail to compile with "environment already
contains 'RiemannFramework.sigma'". The finite model is the proxy; the plane
reflection is the object the framework's own results are about, so the latter
keeps the name. -/
def sectorSwap : Sector → Sector
  | .boson => .fermion
  | .fermion => .boson

/-- Applying the sector swap twice returns to the original sector. -/
theorem sectorSwap_squared (sector : Sector) : sectorSwap (sectorSwap sector) = sector := by
  cases sector <;> rfl

/-- The sector swap is injective. -/
theorem sectorSwap_injective : Function.Injective sectorSwap := by
  intro left right equality
  simpa [sectorSwap_squared left, sectorSwap_squared right] using congrArg sectorSwap equality

/-- The sector swap has no fixed label: it is a free involution, unlike the plane
reflection, whose fixed locus is the critical line. -/
theorem sectorSwap_not_fixed (sector : Sector) : sectorSwap sector ≠ sector := by
  cases sector <;> decide

end RiemannFramework
