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
Operator-level screening: does a candidate symmetry commute with the primon
Hamiltonian?

Adapted from the "Stage D2" idea in an external `rh_idea_framework` prototype.
`affine_reduction.py` screens candidate *formulas* on the complex plane. This
module screens candidate *operators* against the one operator in this
repository whose trace provably is `zeta(s)` (see `primon_gas.py`):

    [W, H] = W H - H W = 0 ?

The structural fact, which the numbers below merely confirm
----------------------------------------------------------------
`H` is diagonal on the basis `|n>` with eigenvalues `log(n)`, and `n |-> log(n)`
is injective on the positive integers, so the spectrum is **simple** (no
repeats). A matrix that commutes with a diagonal matrix of simple spectrum is
itself diagonal in that same basis.

Therefore any candidate symmetry that moves weight between distinct basis
vectors `|n>` and `|m>`, `n != m` -- for instance a permutation swapping the
exponents of two primes in each integer's factorisation -- **provably cannot
commute with `H`**. The computed commutator norm is not evidence for that
conclusion; it is an illustration of it. This is stated plainly because a
nonzero number that stays nonzero as `N` grows is easy to mistake for a
numerical artefact.

The honest limitation
---------------------
On the truncated space the map is only a partial permutation: whenever the
swapped partner of some `n <= n_max` exceeds `n_max`, that basis vector is left
fixed. That is an artefact of truncation, not of the idea, and it means the
*exact* value of the commutator norm is truncation-dependent.

This is not a rare edge case. `8 = 2^3` swaps with `3^3 = 27`, so for the
(2, 3) swap **every** truncation with `n_max >= 8` is already unsafe
(`is_truncation_safe` reports this). At `n_max = 2000` roughly 800 basis vectors
genuinely move while roughly 400 are pinned in place by the boundary. The
computed norm therefore describes a boundary-corrected map rather than the
intended infinite-dimensional one.

The diagnostic that survives is the behaviour as `N` grows: a structural
failure stays bounded away from zero, whereas an artefact decays. The values
are reported alongside `is_truncation_safe` so the caveat travels with them.

What this does not do
---------------------
It does not show the dimension-shift programme is dead. It rules out one
natural-looking family of lifts -- basis permutations on `l^2(N)` -- and
explains why, so a future attempt can aim somewhere the obstruction does not
apply (the Bost-Connes system's Galois action, for instance, acts on a
different, non-diagonal representation).
"""

from __future__ import annotations

import numpy as np

from .primon_gas import factorize, hamiltonian_diagonal


def commutator_norm(W: np.ndarray, n_max: int) -> float:
    """Frobenius norm of `[W, H]` for the truncated primon Hamiltonian `H`.

    Only the diagonal of `H` is needed:
    `(W H - H W)_{ij} = W_{ij} (h_j - h_i)`.
    """
    if W.shape != (n_max, n_max):
        raise ValueError(f"W must be {n_max}x{n_max}, got {W.shape}")

    h = hamiltonian_diagonal(n_max)
    comm = W * (h[np.newaxis, :] - h[:, np.newaxis])
    return float(np.linalg.norm(comm, ord="fro"))


def build_prime_swap_permutation(n_max: int, p1: int, p2: int) -> np.ndarray:
    """Permutation (0-indexed) swapping the exponents of primes `p1` and `p2`.

    For `n = p1^a * p2^b * rest` this maps `n -> p1^b * p2^a * rest`,
    whenever the partner also lies in `[1, n_max]`; otherwise `n` is left
    fixed, which is a truncation artefact rather than a property of the
    intended infinite-dimensional map.
    """
    if p1 == p2:
        raise ValueError("p1 and p2 must be distinct primes.")
    if n_max < 1:
        raise ValueError(f"n_max must be >= 1, got {n_max}")

    permutation = np.arange(n_max)

    for index in range(n_max):
        n = index + 1
        factors = factorize(n)
        a = factors.get(p1, 0)
        b = factors.get(p2, 0)
        if a == 0 and b == 0:
            continue

        rest = n // (p1**a) // (p2**b)
        swapped = rest * (p1**b) * (p2**a)
        if 1 <= swapped <= n_max:
            permutation[index] = swapped - 1

    return permutation


def build_prime_swap_involution(n_max: int, p1: int, p2: int) -> np.ndarray:
    """Permutation matrix for the prime-exponent swap on `C^{n_max}`."""
    permutation = build_prime_swap_permutation(n_max, p1, p2)
    matrix = np.zeros((n_max, n_max))
    for index, target in enumerate(permutation):
        matrix[target, index] = 1.0
    return matrix


def is_truncation_safe(n_max: int, p1: int, p2: int) -> bool:
    """True when the swap never pushes a basis vector outside the truncation.

    This asks whether the *honest* partner of every `n <= n_max` also lies in
    `[1, n_max]`. It is deliberately not the same as "the permutation is an
    involution": leaving an out-of-range partner fixed still produces an
    involution, but it silently changes the operator (that basis vector should
    have moved), so the resulting commutator describes a different map from the
    intended one.
    """
    if p1 == p2:
        raise ValueError("p1 and p2 must be distinct primes.")

    for n in range(1, n_max + 1):
        factors = factorize(n)
        a = factors.get(p1, 0)
        b = factors.get(p2, 0)
        if a == 0 and b == 0:
            continue
        rest = n // (p1**a) // (p2**b)
        swapped = rest * (p1**b) * (p2**a)
        if not 1 <= swapped <= n_max:
            return False
    return True


def screen_operator(W: np.ndarray, n_max: int, tolerance: float = 1e-8) -> dict:
    """Screen a candidate operator `W` against the primon Hamiltonian.

    Returns a dict with the commutator norm, whether `W` is diagonal in the
    `|n>` basis, and a verdict whose wording never implies that commuting is
    sufficient for an idea to be correct.
    """
    norm = commutator_norm(W, n_max)
    off_diagonal_mass = float(np.linalg.norm(W - np.diag(np.diag(W)), ord="fro"))
    is_diagonal = off_diagonal_mass < tolerance
    commutes = norm < tolerance

    if commutes:
        verdict = "commutes"
        explanation = (
            f"||[W, H]||_F = {norm:.3e} (numerically zero): W commutes with the "
            "primon Hamiltonian. "
            + (
                "W is diagonal, which is the expected shape: H has simple "
                "spectrum, so its commutant is exactly the diagonal algebra."
                if is_diagonal
                else "W is not diagonal despite commuting; re-examine the "
                "truncation, since log is injective on the positive integers."
            )
            + " Commuting is necessary for a symmetry of this operator, not "
            "evidence of correctness."
        )
    else:
        verdict = "does_not_commute"
        explanation = (
            f"||[W, H]||_F = {norm:.3e} (nonzero): W does NOT commute with H. "
            "This is forced, not accidental. H is diagonal with strictly "
            "distinct eigenvalues log(1) < log(2) < ..., so any operator that "
            "moves weight between distinct basis vectors |n>, |m> (n != m) -- "
            "such as a permutation swapping prime exponents -- cannot commute "
            "with it. A matrix commuting with a diagonal matrix of simple "
            "spectrum must itself be diagonal."
        )

    return {
        "n_max": n_max,
        "commutator_norm": norm,
        "is_diagonal": is_diagonal,
        "commutes": commutes,
        "verdict": verdict,
        "explanation": explanation,
    }


def commutator_scaling(p1: int, p2: int, sizes=(200, 500, 1000, 2000, 4000)) -> dict:
    """Track the commutator norm as the truncation grows.

    This is the diagnostic that separates a structural failure from a
    truncation artefact: a genuine failure stays bounded away from zero, while
    an artefact decays. Also reports whether each size is truncation-safe.
    """
    results = []
    for n_max in sizes:
        W = build_prime_swap_involution(n_max, p1, p2)
        results.append(
            {
                "n_max": n_max,
                "commutator_norm": commutator_norm(W, n_max),
                "truncation_safe": is_truncation_safe(n_max, p1, p2),
            }
        )

    return {
        "p1": p1,
        "p2": p2,
        "results": results,
        "norms": [entry["commutator_norm"] for entry in results],
        "all_truncation_safe": all(entry["truncation_safe"] for entry in results),
        "does_not_vanish": all(norm > 1e-8 for norm in (e["commutator_norm"] for e in results)),
    }
