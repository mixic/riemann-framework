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
The checkable certificates behind two recent proportion theorems for zeta zeros.

Two papers, both of which prove that *a proportion* of the non-trivial zeros are
simple and on the critical line, and neither of which proves the Riemann
hypothesis:

- Alpoge and Furman (arXiv:2608.13637), with the mathematical argument written by
  Claude: at least `2/3` simple and on the line, at least `5/6` distinct.
- Lamzouri (arXiv:2609.02882): a new proof of the same constants, `0.6725` and
  `0.83625` with the Montgomery-Taylor window.

What this module does and does not do
-------------------------------------
Both proofs reduce, at their load-bearing point, to a **finite elementary
statement** -- a linear-algebra inequality or a multiset inequality -- together
with analytic input that no simulation can reach. This module checks the finite
part and *only* the finite part:

    rank_trace_holds          Lemma 3.2 of Alpoge-Furman: (L), eq (1.1)
    proposition_2_1_holds     Proposition 2.1 of Lamzouri
    montgomery_taylor_constants   the constant chain, eq (1.2)

Passing these checks is evidence that the linear algebra and the arithmetic of
the constants are right. It is **not** evidence for either theorem, and it is
nowhere near evidence for RH. A Monte Carlo search cannot prove an inequality; it
can only fail to find a counterexample, and the sampling need not reach the
extremal regime. The analytic inputs -- Weil's explicit formula, the
unconditional prime-side second moment of Aryan and of Baluyot-Goldston-
Suriajaya-Turnage-Butterbaugh, Montgomery-Vaughan, Chebyshev-Mertens, Stirling --
are outside this module entirely.

Why "is there an RH proof here" has a definite answer
-----------------------------------------------------
Alpoge-Furman's section 1.4 is titled "What the results are not". It records that
the theorems are lower bounds only, that the remaining third of the zeros is *not*
shown to be off the line, and -- decisively -- that the inputs "hold for
Davenport-Heilbronn and Epstein zeta functions, for which the analogue of RH is
false". An argument that goes through unchanged where the hypothesis fails cannot
establish the hypothesis. That is not a caveat attached to the result; it is a
proof that this method cannot reach RH, and the same paper notes the certificate is
sharp within its class. Lamzouri records the matching ceiling on his route: the
pair-correlation method would need a kernel `K` with `Re K(z) >= 0` for all complex
`z`, and no such nonconstant entire kernel exists.

So this module is deliberately named for *certificates*. It has no function that
returns anything like "the Riemann hypothesis is true", and the repository's
standing position -- enforced by `tests/test_formal_proof.py`, which fails if a
module recorded as carrying an open RH target stops reporting `sorry` -- is that
RH remains open.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ============================================================
# The constant chain
# ============================================================

def montgomery_taylor_constants() -> dict:
    """The constants of Theorem A, and the arithmetic joining them.

    Alpoge-Furman's eq (1.2) is the single chain

        N_0^s/N >= 2 - R(psi),      N_d/N >= (3 - R(psi))/2,

    with `R(psi_0) = 4/3` for the indicator window and `R(psi_MT) = c_MT^{-1}` for
    the Montgomery-Taylor window. Checked here because the chain is pure
    arithmetic and a slip in it would be invisible in the prose.
    """
    c_mt_inverse = 0.5 + (1.0 / np.sqrt(2.0)) / np.tan(1.0 / np.sqrt(2.0))
    return {
        "R_indicator": 4.0 / 3.0,
        "c_MT_inverse": c_mt_inverse,
        "simple_indicator": 2.0 - 4.0 / 3.0,
        "distinct_indicator": (3.0 - 4.0 / 3.0) / 2.0,
        "simple_montgomery_taylor": 2.0 - c_mt_inverse,
        "distinct_montgomery_taylor": (3.0 - c_mt_inverse) / 2.0,
    }


def constant_chain_matches_paper() -> dict:
    """Does the arithmetic reproduce the published figures?

    `2 - 4/3 = 2/3` and `(3 - 4/3)/2 = 5/6` are the headline constants; the
    Montgomery-Taylor pair must come out at `0.6725...` and `0.83625...`.
    """
    c = montgomery_taylor_constants()
    return {
        "indicator_is_two_thirds": abs(c["simple_indicator"] - 2.0 / 3.0) < 1e-15,
        "indicator_is_five_sixths": abs(c["distinct_indicator"] - 5.0 / 6.0) < 1e-15,
        "MT_simple_exceeds_0_6725": c["simple_montgomery_taylor"] > 0.6725,
        "MT_distinct_exceeds_0_8362": c["distinct_montgomery_taylor"] > 0.8362,
        "simple_matches_lamzouri_C0": abs(c["simple_montgomery_taylor"] - 0.6725007037) < 1e-9,
        "distinct_matches_lamzouri_C1": abs(c["distinct_montgomery_taylor"] - 0.8362503518) < 1e-9,
    }


# ============================================================
# Lamzouri's kernel and Proposition 2.1
# ============================================================

def cos_square_kernel(zeta: complex | np.ndarray, lam: float = 1.0) -> np.ndarray:
    """`K(xi) = eta^2_hat(xi)` for `eta(u) = lam^{-1/2} |cos(pi u / (2 lam))|` on `(-lam, lam)`.

    This `eta` is real, even, supported in `(-lam, lam)`, and normalised so that
    `int eta^2 = 1`, which is exactly the admissibility Proposition 2.1 demands.
    The kernel is the entire function

        K(xi) = sinc(2 lam xi) + (sinc(1 - 2 lam xi) + sinc(1 + 2 lam xi)) / 2,

    with `sinc(x) = sin(pi x)/(pi x)`, and `K(0) = 1`.
    """
    if not lam > 0.0:
        raise ValueError(f"lam must be > 0, got {lam}")
    scaled = lam * np.asarray(zeta, dtype=complex)
    return np.sinc(2.0 * scaled) + (
        np.sinc(1.0 - 2.0 * scaled) + np.sinc(1.0 + 2.0 * scaled)
    ) / 2.0


def proposition_2_1_holds(
    multiset: np.ndarray, lam: float = 1.0
) -> dict:
    """Check both inequalities of Lamzouri's Proposition 2.1 on one multiset.

    For a finite multiset `Z` of complex numbers invariant under conjugation
    (with matching multiplicities), let `N` be its size counted with multiplicity,
    `s` the number of simple real elements, and `d` the number of distinct
    elements. The proposition asserts

        s >= 2N - sum_{z,w in Z} K(z - w)^2          (2.4)
        d >= 3N/2 - (1/2) sum_{z,w in Z} K(z - w)^2  (2.5)

    with the interior sum over the *distinct* multiset, multiplicities included.
    Both sides are computed here so the margin is visible rather than assumed.
    """
    values = np.asarray(multiset, dtype=complex)
    if values.ndim != 1:
        raise ValueError("multiset must be one dimensional")
    if values.size == 0:
        raise ValueError("multiset must be non-empty")
    if not np.allclose(np.sort_complex(values), np.sort_complex(values.conj())):
        raise ValueError(
            "multiset must be invariant under complex conjugation, with matching "
            "multiplicities; Proposition 2.1 assumes it"
        )

    n = int(values.size)
    distinct = np.unique(values)
    simple_real = sum(
        1 for z in distinct if z.imag == 0.0 and int(np.count_nonzero(values == z)) == 1
    )
    matrix = cos_square_kernel(values[:, None] - values[None, :], lam) ** 2
    quadratic = float(np.real(matrix.sum()))

    rhs_24 = 2.0 * n - quadratic
    rhs_25 = 1.5 * n - 0.5 * quadratic
    return {
        "size": n,
        "distinct": int(distinct.size),
        "simple_real": int(simple_real),
        "quadratic_form": quadratic,
        "margin_2_4": simple_real - rhs_24,
        "margin_2_5": float(distinct.size) - rhs_25,
        "holds_2_4": simple_real >= rhs_24 - 1e-9,
        "holds_2_5": float(distinct.size) >= rhs_25 - 1e-9,
    }


def random_conjugation_invariant_multiset(
    rng: np.random.Generator, max_points: int = 4
) -> np.ndarray:
    """A random multiset closed under `z -> conj(z)`, built to include the hard cases.

    Real points (simple and repeated) exercise (2.4); conjugation quadruples
    exercise the off-axis terms, where `K` is evaluated at complex arguments and
    where a wrong kernel would show up.
    """
    values: list[complex] = []
    for _ in range(int(rng.integers(0, max_points + 1))):
        z = float(rng.normal(0.0, 1.5))
        values += [z] * int(rng.integers(1, 4))
    for _ in range(int(rng.integers(0, max_points + 1))):
        x, y = float(rng.normal(0.0, 1.5)), float(rng.normal(0.05, 1.5))
        values += [complex(x, y), complex(x, -y)] * int(rng.integers(1, 3))
    if not values:
        values = [0.0]
    return np.array(values)


def proposition_2_1_search(trials: int = 4000, seed: int = 0, lam: float = 1.0) -> dict:
    """Sample random multisets and report any violation of Proposition 2.1."""
    rng = np.random.default_rng(seed)
    violations_2_4 = violations_2_5 = 0
    checked = 0
    worst_margin = None
    for _ in range(trials):
        values = random_conjugation_invariant_multiset(rng)
        report = proposition_2_1_holds(values, lam)
        checked += 1
        if not report["holds_2_4"]:
            violations_2_4 += 1
        if not report["holds_2_5"]:
            violations_2_5 += 1
        if worst_margin is None or report["margin_2_4"] < worst_margin:
            worst_margin = report["margin_2_4"]
    return {
        "checked": checked,
        "violations_2_4": violations_2_4,
        "violations_2_5": violations_2_5,
        "tightest_margin_2_4": worst_margin,
    }


# ============================================================
# Alpoge-Furman's rank-trace inequality
# ============================================================

@dataclass
class RankTraceReport:
    """Margin by which Lemma 3.2 holds for one matrix pair."""

    rank: int
    trace_p1: float
    trace_q: float
    positive_index_bound: int
    hilbert_schmidt_squared: float
    right_hand_side: float

    @property
    def margin(self) -> float:
        return self.rank - self.right_hand_side

    @property
    def holds(self) -> bool:
        return self.margin >= -1e-8


def rank_trace_holds(
    p1: np.ndarray, q: np.ndarray, b: int, tol: float = 1e-8
) -> RankTraceReport:
    """Check Lemma 3.2: for `P1 >= 0` and `Q` with `n_+(Q) <= b`,

        rank P1 >= 2 tr P1 + 4 tr Q - 4b - ||P1 + Q||_HS^2.

    This is item (L) of Alpoge-Furman, eq (1.1), and it is where `RH` was removed
    from Montgomery's deduction: the positivity of Weil's form off the critical
    line is replaced by an inertia count. The paper notes it is the matrix form of
    `m^2 >= 2m - 1`, sharpening to `m^2 >= 3m - 2` once multiple zeros carry the
    flat charge 4.

    Validated as a *test*, not a proof: a Monte Carlo search can fail to find a
    counterexample without the inequality being true.
    """
    p1 = np.asarray(p1, dtype=complex)
    q = np.asarray(q, dtype=complex)
    if p1.shape != q.shape or p1.ndim != 2 or p1.shape[0] != p1.shape[1]:
        raise ValueError("p1 and q must be square matrices of the same shape")
    if not np.allclose(p1, p1.conj().T, atol=1e-10):
        raise ValueError("p1 must be Hermitian")
    if not np.allclose(q, q.conj().T, atol=1e-10):
        raise ValueError("q must be Hermitian")
    if float(np.linalg.eigvalsh(p1).min()) < -tol:
        raise ValueError("p1 must be positive semidefinite")

    eigenvalues = np.linalg.eigvalsh(q)
    positive_index = int(np.count_nonzero(eigenvalues > tol))
    if positive_index > b:
        raise ValueError(
            f"n_+(Q) = {positive_index} exceeds b = {b}; the hypothesis of "
            "Lemma 3.2 is not met and the inequality need not hold"
        )

    total = p1 + q
    return RankTraceReport(
        rank=int(np.linalg.matrix_rank(p1, tol=tol)),
        trace_p1=float(np.trace(p1).real),
        trace_q=float(np.trace(q).real),
        positive_index_bound=int(b),
        hilbert_schmidt_squared=float(np.sum(np.abs(total) ** 2)),
        right_hand_side=(
            2.0 * float(np.trace(p1).real)
            + 4.0 * float(np.trace(q).real)
            - 4.0 * float(b)
            - float(np.sum(np.abs(total) ** 2))
        ),
    )


def rank_trace_search(trials: int = 20000, seed: int = 0, max_dim: int = 8) -> dict:
    """Sample random admissible pairs and report any violation of Lemma 3.2."""
    rng = np.random.default_rng(seed)
    violations = 0
    worst = None
    for _ in range(trials):
        n = int(rng.integers(2, max_dim + 1))
        r = int(rng.integers(0, n + 1))
        a = rng.normal(size=(r, n)) + 1j * rng.normal(size=(r, n))
        p1 = a.conj().T @ a
        bmat = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
        q = (bmat + bmat.conj().T) / 2.0
        positive_index = int(np.count_nonzero(np.linalg.eigvalsh(q) > 1e-9))
        b = positive_index + int(rng.integers(0, 3))
        report = rank_trace_holds(p1, q, b)
        if not report.holds:
            violations += 1
        if worst is None or report.margin < worst:
            worst = report.margin
    return {"checked": trials, "violations": violations, "tightest_margin": worst}
