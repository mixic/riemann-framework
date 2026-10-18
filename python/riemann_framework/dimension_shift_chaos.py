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
"""Dimension-Shift Hamiltonian with the involution *enforced*, not hoped for.

This module replaces the version that shipped until now. That version had three
defects, all of which are verified in `tests/test_dimension_shift_chaos.py`:

1. **It was not sigma-symmetric.** It drew two independent blocks `H_b`, `H_f` and
   a non-symmetric coupling `V`, so `sigma` (the sector swap) never commuted with
   `H`: measured `||[H, sigma]||_F / ||H||_F = 1.346 .. 1.462` across the tested
   parameters. Requirement 1 of the Dimension-Shift Hypothesis is
   `[H(lambda), sigma] = 0`, and the model violated it at every point.
2. **It was GOE, not GUE.** Both blocks were real symmetric, so the model sat in
   the time-reversal-symmetric class, whose mean `r`-ratio is `0.53` -- not the
   `0.60` of the zeros. The module's own docstring said the *goal* was to
   "iterate on the model until the spectrum matches GUE statistics", which is a
   description of p-hacking, not of a test.
3. **It was never desymmetrised.** Statistics were taken on the full
   `2d`-dimensional spectrum, which is a superposition of two sectors.

What sigma-symmetry actually forces
-----------------------------------
Write `H = [[A, C], [C^dagger, B]]` on `H_b (+) H_f` and let `sigma` swap the
sectors. Then `sigma H sigma = [[B, C^dagger], [C, A]]`, so

    [H, sigma] = 0   <=>   A = B   and   C = C^dagger.

That is the whole content, and it has a consequence the old model could not show:
in the basis `Q = (1/sqrt2)[[I, I], [I, -I]]` the Hamiltonian is block diagonal,

    Q^dagger H Q = diag(A + C, A - C),

so the sigma-sectors are exactly the `+1` and `-1` eigenspaces of `sigma`, with
spectra `spec(A + C)` and `spec(A - C)`. Both are verified numerically here to
`1e-14` rather than assumed.

Two honest consequences, both measured in `falsification_test.py`
----------------------------------------------------------------
**The class is inherited, not derived.** If `A` and `C` are GUE then `A +- C` is
GUE and the sector statistics are `0.595`; if `A` and `C` are real symmetric
(GOE) then the sector statistics are `0.528`. Choosing GUE blocks *assumes* the
time-reversal breaking that the hypothesis is supposed to supply. The model
therefore cannot be evidence for GUE statistics: it can only demonstrate that the
construction is *capable* of carrying them.

**The full spectrum is never GUE.** A superposition of two independent sectors
has intermediate statistics -- measured `0.430` (GUE blocks) and `0.417` (GOE
blocks), against `0.599` for GUE and `0.386` for Poisson. Any test that averages
over the whole `2d`-dimensional spectrum is asking the wrong question, which is
one reason the old "GUE at `d=10`" reading was an artefact.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

import numpy as np

from .quantum_chaos import riemann_zero_heights
from .statistics import (
    classify_statistics,
    ks_test_against,
    mean_r_ratio,
)

MATRIX_CLASSES = ("goe", "gue")

#: The measured violation of requirement 1 in the pre-correction model.
SIGMA_VIOLATION_RANGE = (1.346, 1.462)

#: Required for a model to count as sigma-symmetric at all.
SIGMA_TOLERANCE = 1e-10


# ============================================================
# The involution and its sectors
# ============================================================

def sector_swap(dim_per_sector: int) -> np.ndarray:
    """`sigma`: the involution swapping the bosonic and fermionic sectors.

    `sigma |b, k> = |f, k>` and back, so `sigma^2 = I` and `sigma = sigma^dagger`.
    """
    d = _validate_dimension(dim_per_sector)
    sigma = np.zeros((2 * d, 2 * d), dtype=complex)
    sigma[:d, d:] = np.eye(d)
    sigma[d:, :d] = np.eye(d)
    return sigma


def _validate_dimension(dim_per_sector: int) -> int:
    if not isinstance(dim_per_sector, (int, np.integer)):
        raise TypeError("dim_per_sector must be an integer")
    if dim_per_sector < 2:
        raise ValueError("dim_per_sector must be at least 2")
    return int(dim_per_sector)


def _hermitian_block(d: int, rng: np.random.Generator, matrix_class: str) -> np.ndarray:
    """A random Hermitian `d x d` block in the requested symmetry class.

    `"gue"`: complex Hermitian (no time-reversal symmetry).
    `"goe"`: real symmetric (time-reversal symmetric) -- the old behaviour.
    """
    if matrix_class == "gue":
        raw = (rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))) / np.sqrt(2.0)
        return (raw + raw.conj().T) / 2.0
    if matrix_class == "goe":
        raw = rng.standard_normal((d, d))
        return (raw + raw.T) / 2.0
    raise ValueError(f"matrix_class must be one of {MATRIX_CLASSES}, got {matrix_class!r}")


def sigma_sector_basis(dim_per_sector: int) -> np.ndarray:
    """`Q = (1/sqrt2)[[I, I], [I, -I]]`: columns are the `sigma` eigenbasis.

    Orthonormal, so `Q^dagger H Q` is a similarity transform and the spectra are
    preserved. Column `k` is the `+1` sector, column `d + k` the `-1` sector.
    """
    d = _validate_dimension(dim_per_sector)
    basis = np.zeros((2 * d, 2 * d), dtype=complex)
    eye = np.eye(d) / np.sqrt(2.0)
    basis[:d, :d] = eye
    basis[d:, :d] = eye
    basis[:d, d:] = eye
    basis[d:, d:] = -eye
    return basis


# ============================================================
# The Hamiltonian
# ============================================================

def build_dimension_shift_hamiltonian(
    dim_per_sector: int = 20,
    coupling: float = 1.0,
    matrix_class: str = "gue",
    seed: int | None = None,
    sigma_breaking: float = 0.0,
) -> np.ndarray:
    """The sigma-symmetric dimension-shift Hamiltonian on `H_b (+) H_f`.

        H = [[ A ,            C            ],
             [ C^dagger ,      A + D        ]]

    with `A` and `C` random Hermitian blocks of the requested class and
    `C` scaled by `coupling`. With `sigma_breaking = 0` the matrix `D` is zero and
    `[H, sigma] = 0` **exactly** -- not approximately, because `A` appears in both
    diagonal blocks. `sigma_breaking > 0` adds a random diagonal to the fermionic
    sector only, which is a *deliberate violation* of the hypothesis used as a
    control; it must never be part of a verdict grid.

    Parameters
    ----------
    dim_per_sector:
        Size `d` of each sector; the full space has dimension `2d`.
    coupling:
        Strength of the inter-sector block `C`.
    matrix_class:
        `"gue"` (complex Hermitian) or `"goe"` (real symmetric).
    seed:
        Forwarded to `numpy.random.default_rng`.
    sigma_breaking:
        Control parameter; breaks `[H, sigma] = 0` when positive.
    """
    d = _validate_dimension(dim_per_sector)
    if coupling < 0.0:
        raise ValueError("coupling must be non-negative")
    if sigma_breaking < 0.0:
        raise ValueError("sigma_breaking must be non-negative")
    rng = np.random.default_rng(seed)

    block = _hermitian_block(d, rng, matrix_class)
    inter = coupling * _hermitian_block(d, rng, matrix_class)

    hamiltonian = np.zeros((2 * d, 2 * d), dtype=complex)
    hamiltonian[:d, :d] = block
    hamiltonian[d:, d:] = block
    hamiltonian[:d, d:] = inter
    hamiltonian[d:, :d] = inter.conj().T

    if sigma_breaking > 0.0:
        hamiltonian[d:, d:] += np.diag(sigma_breaking * rng.standard_normal(d))

    return hamiltonian


def sigma_commutator_ratio(hamiltonian: np.ndarray) -> float:
    """`||[H, sigma]||_F / ||H||_F`: zero for a sigma-symmetric model.

    The relative norm is reported because the absolute commutator grows with the
    matrix size and would make small and large models incomparable.
    """
    matrix = np.asarray(hamiltonian)
    d = matrix.shape[0] // 2
    if matrix.shape != (2 * d, 2 * d):
        raise ValueError("hamiltonian must be of the form (2d, 2d)")
    sigma = sector_swap(d)
    commutator = matrix @ sigma - sigma @ matrix
    denominator = float(np.linalg.norm(matrix, "fro"))
    if denominator == 0.0:
        raise ValueError("hamiltonian must be non-zero")
    return float(np.linalg.norm(commutator, "fro") / denominator)


def is_sigma_symmetric(hamiltonian: np.ndarray, tolerance: float = SIGMA_TOLERANCE) -> bool:
    """Does the model satisfy requirement 1 of the DSH?"""
    return sigma_commutator_ratio(hamiltonian) < tolerance


def desymmetrise(hamiltonian: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split `H` into its `sigma = +1` and `sigma = -1` blocks.

    The split is done numerically, not by reading off `A +- C`: the matrix is
    transformed into the eigenbasis of `sigma` and the off-diagonal blocks are
    checked to vanish. If they do not, `H` is not sigma-symmetric and the split is
    meaningless, so this raises instead of silently returning two blocks.
    """
    matrix = np.asarray(hamiltonian, dtype=complex)
    d = matrix.shape[0] // 2
    if matrix.shape != (2 * d, 2 * d):
        raise ValueError("hamiltonian must be of the form (2d, 2d)")
    basis = sigma_sector_basis(d)
    transformed = basis.conj().T @ matrix @ basis
    off_block = np.linalg.norm(transformed[:d, d:]) + np.linalg.norm(transformed[d:, :d])
    scale = float(np.linalg.norm(matrix, "fro"))
    if scale == 0.0 or off_block / scale > SIGMA_TOLERANCE:
        raise ValueError(
            "hamiltonian is not sigma-symmetric: the sectors are not invariant, "
            f"off-block mass / ||H|| = {off_block / max(scale, 1e-300):.3e}"
        )
    return transformed[:d, :d], transformed[d:, d:]


def sector_spectra(hamiltonian: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Eigenvalues of the `+1` and `-1` sectors, ascending."""
    plus, minus = desymmetrise(hamiltonian)
    return np.linalg.eigvalsh(plus), np.linalg.eigvalsh(minus)


# ============================================================
# Analysis pipeline
# ============================================================

def analyze_dimension_shift(
    dim_per_sector: int = 20,
    coupling: float = 1.0,
    matrix_class: str = "gue",
    seed: int | None = 42,
    unfold: bool = False,
    sigma_breaking: float = 0.0,
) -> dict:
    """Full spectrum and both sigma-sectors of one parameter point.

    The full-spectrum statistics are reported next to the sector statistics
    because they answer different questions and only the second one is the DSH's:
    the full spectrum is a superposition of two sectors and lands near `0.42`,
    while a sector carries the class of its blocks.

    `unfold=False` by default: polynomial unfolding of a `2d`-point spectrum adds
    variance without removing structure at these sizes, and the pre-correction
    code's choice of unfolding was never justified.
    """
    hamiltonian = build_dimension_shift_hamiltonian(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        matrix_class=matrix_class,
        seed=seed,
        sigma_breaking=sigma_breaking,
    )
    full = np.linalg.eigvalsh(hamiltonian)

    result: dict = {
        "dim_per_sector": dim_per_sector,
        "coupling": coupling,
        "matrix_class": matrix_class,
        "seed": seed,
        "sigma_breaking": sigma_breaking,
        "sigma_commutator_ratio": sigma_commutator_ratio(hamiltonian),
        "sigma_symmetric": is_sigma_symmetric(hamiltonian),
        "eigenvalues": full,
        "mean_r_full": float(mean_r_ratio(full, unfold=unfold)),
    }

    if result["sigma_symmetric"]:
        plus, minus = sector_spectra(hamiltonian)
        result["sector_plus"] = plus
        result["sector_minus"] = minus
        result["mean_r_plus"] = float(mean_r_ratio(plus, unfold=unfold))
        result["mean_r_minus"] = float(mean_r_ratio(minus, unfold=unfold))
    else:
        # A sigma-breaking control has no sectors; saying so is the point.
        result["sector_plus"] = None
        result["sector_minus"] = None
        result["mean_r_plus"] = float("nan")
        result["mean_r_minus"] = float("nan")

    result["classification_full"] = classify_statistics(full, unfold=unfold)
    result["ks_gue_full"] = ks_test_against(full, reference="gue", unfold=unfold)["ks_stat"]
    result["ks_poisson_full"] = ks_test_against(full, reference="poisson", unfold=unfold)["ks_stat"]
    return result


def sweep_coupling(
    dim_per_sector: int = 20,
    coupling_values: list[float] | None = None,
    matrix_class: str = "gue",
    seed: int | None = 42,
) -> list[dict]:
    """Vary the inter-sector coupling with sigma enforced throughout."""
    if coupling_values is None:
        coupling_values = [0.0, 0.25, 0.5, 1.0, 2.0]
    return [
        analyze_dimension_shift(
            dim_per_sector=dim_per_sector,
            coupling=coupling,
            matrix_class=matrix_class,
            seed=seed,
        )
        for coupling in coupling_values
    ]


def sweep_matrix_class(
    dim_per_sector: int = 20,
    coupling: float = 1.0,
    seed: int | None = 42,
) -> list[dict]:
    """The same construction in both symmetry classes -- the class is an assumption."""
    return [
        analyze_dimension_shift(
            dim_per_sector=dim_per_sector,
            coupling=coupling,
            matrix_class=matrix_class,
            seed=seed,
        )
        for matrix_class in MATRIX_CLASSES
    ]


def sigma_control(
    dim_per_sector: int = 20,
    coupling: float = 1.0,
    matrix_class: str = "gue",
    seed: int | None = 42,
    breaking_values: list[float] | None = None,
) -> list[dict]:
    """Negative control: what happens when requirement 1 is deliberately violated.

    Reported separately from every verdict, because a broken model is not a test
    of the hypothesis.
    """
    if breaking_values is None:
        breaking_values = [0.0, 0.1, 0.5, 1.0]
    return [
        analyze_dimension_shift(
            dim_per_sector=dim_per_sector,
            coupling=coupling,
            matrix_class=matrix_class,
            seed=seed,
            sigma_breaking=value,
        )
        for value in breaking_values
    ]


def compare_to_riemann(
    dim_per_sector: int = 20,
    coupling: float = 1.0,
    matrix_class: str = "gue",
    seed: int | None = 42,
    n_riemann: int = 100,
) -> dict:
    """The model's statistics against the zeros', with the reference values."""
    analysis = analyze_dimension_shift(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        matrix_class=matrix_class,
        seed=seed,
    )
    gammas = riemann_zero_heights(n_riemann)

    return {
        "model": {
            "matrix_class": matrix_class,
            "mean_r_full": analysis["mean_r_full"],
            "mean_r_plus": analysis["mean_r_plus"],
            "mean_r_minus": analysis["mean_r_minus"],
            "sigma_commutator_ratio": analysis["sigma_commutator_ratio"],
        },
        "riemann": {
            "mean_r": float(mean_r_ratio(gammas)),
            "n_zeros": n_riemann,
        },
        "reference_values": {"poisson": 0.386, "goe": 0.530, "gue": 0.599},
    }
