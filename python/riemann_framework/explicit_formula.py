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

    Uses the first `num_zeros` non-trivial zeros, sorted by
    descending imaginary part for better convergence.
    """
    x = mp.mpf(x)
    result = mp.li(x)

    # Compute the zeros first, then sort by descending imaginary part
    zeros = [mp.zetazero(n) for n in range(1, num_zeros + 1)]
    zeros.sort(key=lambda z: -float(mp.im(z)))

    for rho in zeros:
        term = mp.li(mp.power(x, rho))
        result -= 2 * term.real  # conjugate pair

    return float(result)

def li_approx_regularized(x, num_zeros: int, sigma: float = 1.0) -> float:
    """
    Regularized approximation using a Gaussian test function.

    The Gaussian factor exp(-(γ·σ)²) ensures absolute convergence.
    """
    x = mp.mpf(x)
    result = mp.li(x)

    for n in range(1, num_zeros + 1):
        rho = mp.zetazero(n)
        gamma = float(mp.im(rho))
        weight = mp.e ** (-(gamma * sigma) ** 2)
        term = mp.li(mp.power(x, rho))
        result -= 2 * weight * term.real

    return float(result)