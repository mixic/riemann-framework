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
"""Finite spectral-density diagnostics for the dimension-shift programme."""

import numpy as np


_TWO_PI_E = 2.0 * np.pi * np.e


def riemann_von_mangoldt_count(height):
    """Return the leading Riemann-von Mangoldt approximation for ``N(T)``.

    The approximation is meaningful at sufficiently large height. It is used
    here as a finite-range diagnostic, not as an exact zero-counting formula.
    """
    height = np.asarray(height, dtype=float)
    if np.any(~np.isfinite(height)) or np.any(height <= 0):
        raise ValueError("height must contain finite positive values")

    with np.errstate(divide="ignore", invalid="ignore"):
        count = height / (2.0 * np.pi) * np.log(height / _TWO_PI_E) + 7.0 / 8.0
    return np.maximum(count, 0.0)


def _positive_levels(levels):
    levels = np.asarray(levels, dtype=float)
    if levels.ndim != 1 or len(levels) < 2:
        raise ValueError("levels must be a one-dimensional array with at least 2 values")
    if np.any(~np.isfinite(levels)):
        raise ValueError("levels must contain only finite values")

    positive = np.sort(levels[levels > 0])
    if len(positive) < 2:
        raise ValueError("levels must contain at least 2 positive values")
    return positive


def compare_spectral_density(model_levels, reference_heights, grid_size=25):
    """Compare finite model density with zeros and the RvM approximation.

    Model eigenvalues have arbitrary units, so positive model levels are
    linearly scaled to the maximum reference height before cumulative counts
    are compared. Returned RMSE values describe finite-sample shape agreement;
    they do not establish asymptotic spectral convergence.
    """
    if not isinstance(grid_size, (int, np.integer)) or grid_size < 5:
        raise ValueError("grid_size must be an integer of at least 5")

    model = _positive_levels(model_levels)
    reference = _positive_levels(reference_heights)
    scale = reference[-1] / model[-1]
    scaled_model = model * scale

    lower = max(reference[0], _TWO_PI_E)
    grid = np.linspace(lower, reference[-1], int(grid_size))
    model_fraction = np.searchsorted(scaled_model, grid, side="right") / len(model)
    reference_fraction = np.searchsorted(reference, grid, side="right") / len(reference)

    rvm = riemann_von_mangoldt_count(grid)
    rvm_fraction = rvm / rvm[-1]

    return {
        "grid": grid,
        "scale": float(scale),
        "model_fraction": model_fraction,
        "reference_fraction": reference_fraction,
        "rvm_fraction": rvm_fraction,
        "model_vs_reference_rmse": float(
            np.sqrt(np.mean((model_fraction - reference_fraction) ** 2))
        ),
        "model_vs_rvm_rmse": float(
            np.sqrt(np.mean((model_fraction - rvm_fraction) ** 2))
        ),
        "reference_vs_rvm_rmse": float(
            np.sqrt(np.mean((reference_fraction - rvm_fraction) ** 2))
        ),
    }
