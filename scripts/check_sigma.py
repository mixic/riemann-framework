
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

"""Temporary diagnostic: find the best sigma for regularization."""

from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

from riemann_framework.explicit_formula import prime_count, li_approx
from riemann_framework.zeta import set_precision

set_precision(25)

x_values = np.arange(10, 200)
pi_values = np.array([prime_count(int(x)) for x in x_values])

for sigma in [0.1, 0.3, 0.5, 1.0, 2.0]:
    errors = []
    for nz in [0, 10, 50]:
        approx = np.array([li_approx(x, nz, sigma=sigma) for x in x_values])
        errors.append(np.max(np.abs(approx - pi_values)))
    print(f"sigma={sigma}: {errors}")