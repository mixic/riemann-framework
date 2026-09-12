"""Wrapper around mpmath for the Riemann zeta function."""

import mpmath as mp

# Default precision (adjustable)
DEFAULT_DPS = 50


def set_precision(dps: int = DEFAULT_DPS) -> None:
    """Set the computation precision (number of decimal places)."""
    mp.mp.dps = dps


def zeta(s):
    """Compute ζ(s) using the current precision."""
    return mp.zeta(s)


def zeta_zero(n: int):
    """
    Return the n-th non-trivial zero of the zeta function.

    The return value is a complex mpmath object.
    """
    return mp.zetazero(n)


def is_zero(s, tol=None):
    """
    Check whether ζ(s) ≈ 0 (within tolerance).

    If `tol` is None, 10^(-dps/2) is used.
    """
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)
    return abs(mp.zeta(s)) < tol