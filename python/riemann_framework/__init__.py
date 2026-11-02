# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Riemann Framework: a workbench, not a proof.

The package is the code behind the repository's negative results and measured limits:
spacing statistics, the desymmetrisation diagnostic, the sector-count posteriors, the
boundary map, real-system validation, the one-call report, and the PT-symmetric
measurements. Nothing in it is evidence for the Riemann hypothesis, and the documents next
to each module say what each measurement does and does not support.

The version lives here and only here. ``pyproject.toml`` reads it through
``[tool.setuptools.dynamic]``, and ``tests/test_packaging.py`` checks that the two agree,
so a release cannot be half-bumped.
"""

from __future__ import annotations

#: The package version, read by the build backend and by the packaging test.
__version__ = "0.1.0"

__all__ = ["__version__"]
