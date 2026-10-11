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
Two-dimensional lattice reduction, and the good-basis/bad-basis asymmetry.

This is the one part of the lattice-cryptography story that is honestly
simulable here, and the module is deliberately limited to dimension 2. The
security of ML-KEM rests on SVP and CVP being hard in dimensions 500-1000; that
hardness is a research-level conjecture, it is not something a script can
demonstrate, and claiming otherwise would be the worst kind of simulation --
one whose picture implies a conclusion its method cannot reach.

What dimension 2 *can* show, exactly and completely, is the structural claim the
account is built on:

    the same lattice has both a "good" basis of short, nearly orthogonal
    vectors and a "bad" basis of long, nearly parallel ones, and the two are
    related by an integer change of coordinates with determinant +/-1.

That is checked here rather than illustrated. `same_lattice` verifies by exact
integer arithmetic that two bases generate the same point set, and
`shortest_vector` computes the true shortest vector via Gauss reduction, so the
"bad" basis can be shown to be bad by comparison with a known answer rather than
by a picture looking messy.

The honest limit, stated where it matters: Gauss reduction solves SVP and CVP in
dimension 2 in polynomial time. That is precisely why dimension 2 is not
cryptography. Nothing here says anything about the difficulty of lattice problems
in high dimension.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

#: An integer vector in the plane, as a tuple.
Vec2 = tuple[int, int]


# ============================================================
# Basic geometry
# ============================================================

def dot(u: Vec2, v: Vec2) -> int:
    return u[0] * v[0] + u[1] * v[1]


def norm_sq(v: Vec2) -> int:
    return dot(v, v)


def det(u: Vec2, v: Vec2) -> int:
    """The signed area of the parallelogram on `u` and `v`.

    The absolute value is the covolume of the lattice: it is invariant under
    change of basis, which is what makes it the right fingerprint for "same
    lattice".
    """
    return u[0] * v[1] - u[1] * v[0]


# ============================================================
# Gauss (Lagrange) reduction
# ============================================================

def gauss_reduce(b1: Vec2, b2: Vec2) -> tuple[Vec2, Vec2]:
    """Lagrange-Gauss reduction: the shortest basis of the same 2D lattice.

    Repeatedly swap so that `|b1| <= |b2|`, then subtract the nearest multiple of
    `b1` from `b2`. Terminates with `|dot(b1, b2)| <= |b1|^2 / 2`, which is the
    2D optimality condition: `b1` is then a shortest nonzero lattice vector.

    This is SVP solved exactly, in polynomial time, in dimension 2.
    """
    if det(b1, b2) == 0:
        raise ValueError("the two vectors are linearly dependent, so not a basis")
    a, b = b1, b2
    while True:
        if norm_sq(b) < norm_sq(a):
            a, b = b, a
        mu = round(dot(a, b) / norm_sq(a))
        if mu == 0:
            return a, b
        b = (b[0] - mu * a[0], b[1] - mu * a[1])


def shortest_vector(basis: tuple[Vec2, Vec2]) -> Vec2:
    """A shortest nonzero vector of the lattice spanned by `basis`."""
    a, _ = gauss_reduce(*basis)
    return a


@dataclass(frozen=True)
class BasisQuality:
    """How usable a basis is, in the terms the account describes."""

    norm_ratio: float
    angle_degrees: float
    orthogonality_defect: float

    def summary(self) -> str:
        return (
            f"|b2|/|b1| = {self.norm_ratio:.3f}, angle = {self.angle_degrees:.2f} deg, "
            f"orthogonality defect = {self.orthogonality_defect:.3f}"
        )


def basis_quality(b1: Vec2, b2: Vec2) -> BasisQuality:
    """Measure a basis by vector ratio, angle, and orthogonality defect.

    The orthogonality defect is `(|b1| |b2|) / |det|`, which is 1 for a
    rectangular basis and grows without bound as the vectors become parallel. It
    is the quantity the account is describing informally when it distinguishes
    "fast rechtwinklig" from "fast parallel".
    """
    if det(b1, b2) == 0:
        raise ValueError("the two vectors are linearly dependent")
    n1 = norm_sq(b1) ** 0.5
    n2 = norm_sq(b2) ** 0.5
    cos_theta = dot(b1, b2) / (n1 * n2)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    angle = math.degrees(math.acos(cos_theta))
    ratio = max(n1, n2) / min(n1, n2)
    return BasisQuality(
        norm_ratio=ratio,
        angle_degrees=angle,
        orthogonality_defect=(n1 * n2) / abs(det(b1, b2)),
    )


# ============================================================
# Same lattice, different basis
# ============================================================

def is_unimodular(matrix: tuple[tuple[int, int], tuple[int, int]]) -> bool:
    """True when `matrix` is an integer matrix with determinant `+/-1`."""
    (a, b), (c, d) = matrix
    return abs(a * d - b * c) == 1


def coordinates_in_basis(basis: tuple[Vec2, Vec2], v: Vec2) -> tuple[int, int] | None:
    """Write `v = p b1 + q b2` exactly, or return `None` if impossible.

    Cramer's rule over the integers: `p = det(v, b2)/det(b1, b2)` and
    `q = det(b1, v)/det(b1, b2)`. The division has to be exact, which is the
    whole content -- a real-valued solve would return coordinates for any point
    in the plane, including points not on the lattice.
    """
    b1, b2 = basis
    d = det(b1, b2)
    if d == 0:
        raise ValueError("not a basis")
    p_num = det(v, b2)
    q_num = det(b1, v)
    if p_num % d != 0 or q_num % d != 0:
        return None
    return (p_num // d, q_num // d)


def same_lattice(first: tuple[Vec2, Vec2], second: tuple[Vec2, Vec2]) -> bool:
    """True when two bases span exactly the same point set.

    Checked by exact arithmetic, not by sampling: each vector of `second` is
    expressed in `first`, which must succeed with integer coefficients, and the
    resulting change-of-basis matrix must be unimodular. Both conditions are
    necessary and together sufficient.
    """
    rows: list[tuple[int, int]] = []
    for v in second:
        coords = coordinates_in_basis(first, v)
        if coords is None:
            return False
        rows.append(coords)
    (a, b), (c, d) = rows
    return is_unimodular(((a, b), (c, d)))


def apply_unimodular(
    basis: tuple[Vec2, Vec2], matrix: tuple[tuple[int, int], tuple[int, int]]
) -> tuple[Vec2, Vec2]:
    """Rewrite a basis by an integer change of coordinates.

    The lattice is unchanged when the matrix is unimodular; `same_lattice` is
    what confirms that, rather than the construction being trusted.
    """
    (a, b), (c, d) = matrix
    b1, b2 = basis
    new1 = (a * b1[0] + b * b2[0], a * b1[1] + b * b2[1])
    new2 = (c * b1[0] + d * b2[0], c * b1[1] + d * b2[1])
    return new1, new2


def skew_matrix(stretch: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """A unimodular matrix whose off-diagonal entry is `stretch`.

    `[[1, k], [k, k^2 + 1]]` has determinant `1` for every `k`, so it is a change
    of basis and not a change of lattice. It is also the cheapest way to make a
    basis look terrible: the two new vectors are `b1 + k b2` and `k b1 + (k^2+1) b2`.
    """
    if stretch < 1:
        raise ValueError("stretch must be at least 1")
    k = stretch
    return ((1, k), (k, k * k + 1))


def good_and_bad_basis(
    stretch: int = 20, base: tuple[Vec2, Vec2] = ((1, 0), (0, 1))
) -> tuple[tuple[Vec2, Vec2], tuple[Vec2, Vec2]]:
    """Return `(good, bad)` bases of one lattice.

    The same lattice, deliberately: `same_lattice(good, bad)` holds, so any
    difficulty the bad basis presents is a property of the *description* and not
    of the point set. That distinction is the entire content of the claim.
    """
    good = gauss_reduce(*base)
    bad = apply_unimodular(base, skew_matrix(stretch))
    return good, bad


# ============================================================
# The closest vector problem, in dimension 2
# ============================================================

def babai_nearest_plane(basis: tuple[Vec2, Vec2], target: tuple[float, float]) -> Vec2:
    """The closest lattice point, via a reduced basis.

    Correct in dimension 2: after Gauss reduction, checking the integer points
    around the real-valued solution is enough, and the nine neighbours of the
    rounded coefficients are enumerated to be safe. In higher dimensions this
    becomes an approximation with a provable but large factor -- which is where
    the hardness begins, and why this function's correctness here is a statement
    about dimension 2 only.
    """
    a, b = gauss_reduce(*basis)
    d = det(a, b)
    t = (float(target[0]), float(target[1]))
    # Real-valued coordinates of the target in the reduced basis, written out
    # rather than routed through `det`, which is typed over integer vectors.
    p = (t[0] * b[1] - t[1] * b[0]) / d
    q = (a[0] * t[1] - a[1] * t[0]) / d
    best: Vec2 | None = None
    best_dist = float("inf")
    for dp in (-1, 0, 1):
        for dq in (-1, 0, 1):
            pi = int(round(p)) + dp
            qi = int(round(q)) + dq
            v = (pi * a[0] + qi * b[0], pi * a[1] + qi * b[1])
            dist = (v[0] - t[0]) ** 2 + (v[1] - t[1]) ** 2
            if dist < best_dist:
                best_dist = dist
                best = v
    assert best is not None
    return best


def closest_vector_bruteforce(
    basis: tuple[Vec2, Vec2], target: tuple[float, float], coefficient_bound: int
) -> Vec2:
    """The closest lattice point, by exhaustive search over coefficients.

    Exact for the given bound, and used in the tests as the reference that
    `babai_nearest_plane` is checked against. If the bound were too small it would
    silently be wrong, which is why the tests also check that the returned point
    is beaten by nothing on the boundary of the search box.
    """
    a, b = basis
    best: Vec2 | None = None
    best_dist = float("inf")
    for p in range(-coefficient_bound, coefficient_bound + 1):
        for q in range(-coefficient_bound, coefficient_bound + 1):
            v = (p * a[0] + q * b[0], p * a[1] + q * b[1])
            dist = (v[0] - target[0]) ** 2 + (v[1] - target[1]) ** 2
            if dist < best_dist:
                best_dist = dist
                best = v
    assert best is not None
    return best


def lattice_points(
    basis: tuple[Vec2, Vec2], coefficient_bound: int
) -> list[Vec2]:
    """Lattice points with coefficients in `[-bound, bound]`, for plotting."""
    a, b = basis
    return [
        (p * a[0] + q * b[0], p * a[1] + q * b[1])
        for p in range(-coefficient_bound, coefficient_bound + 1)
        for q in range(-coefficient_bound, coefficient_bound + 1)
    ]


def random_unimodular(seed: int, magnitude: int = 5) -> tuple[tuple[int, int], tuple[int, int]]:
    """A random unimodular matrix, for tests that must not use one fixed shape."""
    rng = random.Random(seed)
    while True:
        a = rng.randint(-magnitude, magnitude)
        b = rng.randint(-magnitude, magnitude)
        c = rng.randint(-magnitude, magnitude)
        d = rng.randint(-magnitude, magnitude)
        if abs(a * d - b * c) == 1:
            return ((a, b), (c, d))
