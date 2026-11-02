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
"""Measure the three things the diagnostic's limits depend on, and print them.

Usage, from the repository root:

    python scripts/robustness_diagnostics.py

Three tables, each a measured answer to a measured objection:

1. **The flag's size dependence.** The contamination floor is a fixed `0.48`, which is
   `R_GOE - 1.3 * std` at 60 levels per sector. Because the scatter of a mean over `n`
   ratios falls as `1 / sqrt(n)`, the fixed floor over-flags at small sizes and
   under-flags at large ones. The table shows the one-sector moments and the false
   positive rate at the fixed floor and at a size-dependent floor that keeps the same
   z-score, together with the rate at which a two-sector superposition is missed.

2. **Robustness of the posterior to the simulator's assumptions.** The posterior is
   trained on equal, independent, class-balanced sectors. The table runs the same
   posterior over equal sectors, unequal sectors, a mixed-class pair, and a spectrum
   with a compressed sector (an awkward density), and records how far the coverage and
   the mass on the truth move.

3. **What long-range statistics add.** The adjacent-gap ratio is short range, and it is
   the reason Poisson and a three-or-more-sector superposition look the same. The number
   variance and the Dyson-Mehta statistic are long range, and they separate the two, so
   "not recoverable" is a property of the ratio, not of the spectrum.

No Riemann-hypothesis claim is made here.
"""

from __future__ import annotations

import os
import runpy
import sys
from collections.abc import Callable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

if __name__ == "__main__" and Path.cwd() != PROJECT_ROOT and not os.environ.get(
    "_ROBUSTNESS_DIAGNOSTICS_BOOTSTRAPPED"
):
    os.environ["_ROBUSTNESS_DIAGNOSTICS_BOOTSTRAPPED"] = "1"
    os.chdir(PROJECT_ROOT)
    runpy.run_path(str(Path(__file__).resolve()), run_name="__main__")
    sys.exit(0)

import numpy as np  # noqa: E402

from riemann_framework.desymmetrisation import (  # noqa: E402
    SINGLE_SECTOR_FLOOR,
    HigherOrderCountModel,
    default_higher_order_model,
    false_positive_rate_at_size,
    one_sector_r_moments,
    robustness_table,
    size_dependent_floor,
    superposition_spectrum,
)
from riemann_framework.statistics import (  # noqa: E402
    dyson_mehta_statistic,
    mean_r_ratio,
    number_variance,
)

#: Levels per sector in the size table, and seeds per point.
SIZES = (15, 30, 60, 120, 240, 480)
SEEDS = 400

#: Long-range statistics: window length and spectra per point.
WINDOW = 20.0
LONG_RANGE_SEEDS = 200


def _long_range_spectra() -> list[tuple[str, Callable[[int], np.ndarray]]]:
    return [
        ("1 sector", lambda s: superposition_spectrum(1, 240, "goe", s)),
        ("2 sectors", lambda s: superposition_spectrum(2, 120, "goe", s)),
        ("3 sectors", lambda s: superposition_spectrum(3, 80, "goe", s)),
        ("6 sectors", lambda s: superposition_spectrum(6, 40, "goe", s)),
        ("poisson", lambda s: np.cumsum(np.random.default_rng(s).exponential(1.0, 240))),
    ]


def main() -> None:
    print("== 1. the flag's size dependence (GOE, one sector) ==")
    print(f"{'n levels':>8} {'mean r':>8} {'std':>8} {'floor(z=1.3)':>13} "
          f"{'FP at 0.48':>11} {'FP scaled':>10} {'missed 2-sector':>16}")
    for n in SIZES:
        mean, std = one_sector_r_moments(n, seeds=SEEDS)
        floor = size_dependent_floor(n)
        fp_fixed = false_positive_rate_at_size(n, seeds=SEEDS, floor=SINGLE_SECTOR_FLOOR)
        fp_scaled = false_positive_rate_at_size(n, seeds=SEEDS)
        missed = sum(
            1
            for seed in range(SEEDS)
            if mean_r_ratio(superposition_spectrum(2, n, "goe", seed), unfold=False)
            >= SINGLE_SECTOR_FLOOR
        ) / SEEDS
        print(f"{n:8d} {mean:8.4f} {std:8.4f} {floor:13.4f} {fp_fixed:11.3f} "
              f"{fp_scaled:10.3f} {missed:16.3f}")
    print("the fixed floor over-flags at small n and under-flags at large n; the scaled")
    print("floor keeps the same z-score, so its false-positive rate is flat.")

    print()
    print("== 2. robustness of the posterior to the simulator's assumptions ==")
    for row in robustness_table(draws=400, seed=0):
        print("  " + row.summary())

    print()
    print(f"== 3. long-range statistics, window L = {WINDOW:.0f}, "
          f"{LONG_RANGE_SEEDS} spectra per point ==")
    print(f"{'spectrum':>10} {'mean r':>8} {'Sigma^2(L)':>11} {'Delta_3(L)':>11}")
    for label, builder in _long_range_spectra():
        mean_r = sigma2 = delta3 = 0.0
        for seed in range(LONG_RANGE_SEEDS):
            spectrum = builder(seed)
            mean_r += mean_r_ratio(spectrum, unfold=False)
            sigma2 += number_variance(spectrum, WINDOW, unfold=True)
            delta3 += dyson_mehta_statistic(spectrum, WINDOW, unfold=True)
        print(f"{label:>10} {mean_r / LONG_RANGE_SEEDS:8.3f} "
              f"{sigma2 / LONG_RANGE_SEEDS:11.3f} {delta3 / LONG_RANGE_SEEDS:11.3f}")
    print("the r-ratio reads Poisson and a 3-or-more-sector union as the same number;")
    print("the long-range statistics read them as different, so 'not recoverable' is a")
    print("property of the adjacent-gap ratio, not of the spectrum.")

    print()
    print("== 4. what the higher-order ratios add (one spectrum, balanced accuracy) ==")
    order_one = HigherOrderCountModel.fit(orders=(1,), seeds=200)
    family = default_higher_order_model()
    print(f"{'pair':>8} {'k = 1 only':>12} {'k = 1..6':>10}")
    for first, second in ((2, 3), (3, 6), (4, 6)):
        one = order_one.balanced_accuracy(first, second, draws=200)
        many = family.balanced_accuracy(first, second, draws=200)
        print(f"{first} vs {second:<3} {one:12.3f} {many:10.3f}")
    print("the adjacent-gap ratio is the k = 1 member of the family; the counts it cannot")
    print("separate are separable once the higher orders are read.")

    print()
    print("== coverage of the higher-order posterior, 120 draws per row ==")
    for row in family.coverage(draws=120):
        print("  " + row.summary())

    print()
    print("No Riemann-hypothesis claim is made here.")


if __name__ == "__main__":
    main()
