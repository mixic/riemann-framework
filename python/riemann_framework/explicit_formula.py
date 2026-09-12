"""Riemann explicit formula for π(x)."""

import numpy as np
import mpmath as mp


def prime_count(x: int) -> int:
    """Exact π(x) using the sieve of Eratosthenes."""
    if x < 2:
        return 0
    sieve = np.ones(int(x) + 1, dtype=bool)
    sieve[0:2] = False
    for i in range(2, int(np.sqrt(x)) + 1):
        if sieve[i]:
            sieve[i * i::i] = False
    return int(np.sum(sieve))


def li_approx(x, num_zeros: int) -> float:
    """
    Approximation of π(x) via Li(x) − Σ_ρ Li(x^ρ).

    Uses the first `num_zeros` non-trivial zeros.
    """
    x = mp.mpf(x)
    result = mp.li(x)

    for n in range(1, num_zeros + 1):
        rho = mp.zetazero(n)
        term = mp.li(mp.power(x, rho))
        result -= 2 * term.real  # conjugate pair

    return float(result)