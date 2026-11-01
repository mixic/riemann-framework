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
"""
Statistical tools for quantum chaos analysis.

Provides level-spacing statistics, the r-ratio, and comparison
against GUE (chaotic) and Poisson (integrable) distributions.
"""

import numpy as np
from scipy import stats


# ============================================================
# Reference mean gap ratios
# ============================================================

# Analytic/standard random-matrix values for the mean adjacent-gap ratio
# (Atas et al., PRL 2013). Hard-coded constants, not fitted.
REFERENCE_R = {
    "poisson": 0.386,
    "goe": 0.530,
    "gue": 0.599,
}


# ============================================================
# Level spacing statistics
# ============================================================

def unfold_spectrum(eigenvalues):
    """
    Unfold a spectrum to mean spacing 1.

    Unfolding removes the smooth part of the density of states so
    that the fluctuations can be compared to universal statistics.

    Uses a simple polynomial fit to the cumulative level count.
    """
    eigenvalues = np.sort(np.asarray(eigenvalues, dtype=float))
    n = len(eigenvalues)

    # Cumulative count (staircase)
    cumulative = np.arange(1, n + 1)

    # Fit a smooth polynomial to the staircase
    degree = min(5, max(2, n // 10))
    coeffs = np.polyfit(eigenvalues, cumulative, degree)
    smooth = np.polyval(coeffs, eigenvalues)

    # Unfolded spectrum
    unfolded = smooth
    return unfolded


def level_spacings(eigenvalues, unfold=True):
    """
    Compute the spacings between consecutive levels.

    If `unfold=True`, the spectrum is first unfolded to mean spacing 1.
    """
    if unfold:
        levels = unfold_spectrum(eigenvalues)
    else:
        levels = np.sort(np.asarray(eigenvalues, dtype=float))

    spacings = np.diff(levels)
    # Normalize to mean spacing 1
    if len(spacings) > 0 and np.mean(spacings) > 0:
        spacings = spacings / np.mean(spacings)
    return spacings


def r_ratio(eigenvalues, unfold=True):
    """
    Compute the r-ratio: r_n = min(s_n, s_{n+1}) / max(s_n, s_{n+1}).

    The mean r-ratio is a robust indicator:
      - Poisson (integrable):  <r> ≈ 0.386
      - GUE (chaotic):         <r> ≈ 0.599
      - GOE (chaotic, T-sym):  <r> ≈ 0.530
    """
    spacings = level_spacings(eigenvalues, unfold=unfold)
    if len(spacings) < 2:
        return np.array([])

    s_n = spacings[:-1]
    s_next = spacings[1:]
    r = np.minimum(s_n, s_next) / np.maximum(s_n, s_next)
    return r


def mean_r_ratio(eigenvalues, unfold=True):
    """Return the mean r-ratio (a single scalar)."""
    r = r_ratio(eigenvalues, unfold=unfold)
    return float(np.mean(r)) if len(r) > 0 else float("nan")


# ============================================================
# Long-range (spectral rigidity) statistics
# ============================================================

def _unfolded_levels(eigenvalues, unfold):
    """Levels with mean spacing 1, for the rigidity statistics.

    `unfold_spectrum` already returns mean-spacing-1 positions (the fitted
    staircase). The extra rescale is a no-op there but does the right thing for a
    raw spectrum when `unfold=False`.
    """
    levels = np.sort(np.asarray(eigenvalues, dtype=float))
    if unfold:
        levels = unfold_spectrum(levels)
    count = levels.size
    if count < 3 or levels[-1] <= levels[0]:
        return np.array([])
    return (levels - levels[0]) * (count - 1) / (levels[-1] - levels[0])


def number_variance(eigenvalues, window_length, unfold=True):
    """The number variance Sigma^2(L) over windows of length L.

    On an unfolded spectrum the number of levels in a window of length L has
    expectation L. Its variance is the standard long-range rigidity statistic:

    * a Poisson process has Sigma^2(L) = L exactly;
    * the rigid ensembles have Sigma^2(L) ~ ln L, far below L.

    A superposition of several independent rigid sectors keeps the short-range
    Poisson look of the adjacent-gap ratio but stays rigid at long range, which
    is why this statistic separates the two where the r-ratio cannot.
    """
    levels = _unfolded_levels(eigenvalues, unfold)
    if levels.size == 0:
        return float("nan")
    length = float(window_length)
    span = float(levels[-1] - levels[0])
    if length <= 0.0 or length >= span:
        return float("nan")
    starts = np.arange(levels[0], levels[-1] - length, 0.5)
    if starts.size == 0:
        return float("nan")
    counts = np.array(
        [np.count_nonzero((levels >= start) & (levels < start + length)) for start in starts]
    )
    return float(np.var(counts, ddof=1))


def dyson_mehta_statistic(eigenvalues, window_length, unfold=True):
    """The Dyson-Mehta rigidity statistic Delta_3(L) over windows of length L.

    In each window the unfolded staircase is fitted by a straight line and the
    mean squared deviation is averaged over all window positions. A Poisson
    process gives Delta_3(L) = L/15; the rigid ensembles give Delta_3 ~ ln L.
    """
    levels = _unfolded_levels(eigenvalues, unfold)
    if levels.size == 0:
        return float("nan")
    length = float(window_length)
    span = float(levels[-1] - levels[0])
    if length <= 0.0 or length >= span:
        return float("nan")
    starts = np.arange(levels[0], levels[-1] - length, 0.5)
    if starts.size == 0:
        return float("nan")
    total = 0.0
    windows = 0
    for start in starts:
        window = levels[(levels >= start) & (levels < start + length)] - start
        if window.size < 2:
            continue
        staircase = np.arange(1, window.size + 1, dtype=float)
        slope, intercept = np.polyfit(window, staircase, 1)
        total += float(np.mean((staircase - (slope * window + intercept)) ** 2))
        windows += 1
    if windows == 0:
        return float("nan")
    return total / windows


# ============================================================
# Reference distributions
# ============================================================

def poisson_spacing_pdf(s):
    """Poisson level-spacing distribution: P(s) = exp(-s)."""
    return np.exp(-s)


def gue_spacing_pdf(s):
    """
    GUE level-spacing distribution (Wigner surmise):
        P(s) = (32/π²) · s² · exp(-4s²/π)
    """
    return (32.0 / np.pi**2) * s**2 * np.exp(-4.0 * s**2 / np.pi)


def goe_spacing_pdf(s):
    """
    GOE level-spacing distribution (Wigner surmise):
        P(s) = (π/2) · s · exp(-π s²/4)
    """
    return (np.pi / 2.0) * s * np.exp(-np.pi * s**2 / 4.0)


# ============================================================
# Goodness-of-fit tests
# ============================================================

def ks_test_against(eigenvalues, reference="gue", unfold=True):
    """
    Kolmogorov-Smirnov test against a reference distribution.

    Returns a dict with the KS statistic and p-value.
    """
    spacings = level_spacings(eigenvalues, unfold=unfold)
    if len(spacings) < 5:
        return {"ks_stat": float("nan"), "p_value": float("nan")}

    if reference == "gue":
        return _ks_against_cdf(spacings, _gue_cdf)
    elif reference == "poisson":
        return _ks_against_cdf(spacings, lambda s: 1 - np.exp(-s))
    elif reference == "goe":
        return _ks_against_cdf(spacings, _goe_cdf)
    else:
        raise ValueError(f"Unknown reference: {reference}")


def _ks_against_cdf(spacings, cdf_func):
    """Internal KS test against an explicit CDF."""
    sorted_s = np.sort(spacings)
    n = len(sorted_s)
    empirical = np.arange(1, n + 1) / n
    theoretical = cdf_func(sorted_s)
    ks_stat = np.max(np.abs(empirical - theoretical))
    # Approximate p-value
    p_value = 2 * np.exp(-2 * n * ks_stat**2)
    return {"ks_stat": float(ks_stat), "p_value": float(p_value)}


def _gue_cdf(s):
    """CDF of the GUE Wigner surmise."""
    # Integral of (32/π²) s² exp(-4s²/π) from 0 to s
    from scipy.special import erf
    a = 2.0 / np.sqrt(np.pi)
    return erf(a * s) - (2 * a * s / np.sqrt(np.pi)) * np.exp(-a**2 * s**2)


def _goe_cdf(s):
    """CDF of the GOE Wigner surmise."""
    return 1 - np.exp(-np.pi * s**2 / 4.0)


def classify_statistics(eigenvalues, unfold=True):
    """
    Classify a spectrum as GUE, GOE, or Poisson.

    Returns the mean r-ratio and the best-fitting reference.
    """
    r = mean_r_ratio(eigenvalues, unfold=unfold)
    best = min(REFERENCE_R, key=lambda k: abs(REFERENCE_R[k] - r))
    return {
        "mean_r": r,
        "best_fit": best,
        "reference_values": dict(REFERENCE_R),
    }
