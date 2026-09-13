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

import RiemannFramework.DimensionShift

/-!
# Riemann Framework

Aggregate module for the `RiemannFramework` Lean library.
The source root of the library is the `lean/` directory
(see `srcDir` in `lakefile.toml`), so this file is
`lean/RiemannFramework.lean` and its submodules live in
`lean/RiemannFramework/`.

Add new `import` lines here as further modules are introduced,
so that a plain `lake build` elaborates the whole library.
-/
