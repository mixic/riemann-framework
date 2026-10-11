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
"""Tests for the two-dimensional lattice module.

Everything here is dimension 2, where Gauss reduction solves SVP exactly and
Babai's nearest plane is exact. The tests say so rather than implying anything
about high dimension -- the hardness that lattice cryptography rests on is not
observable here, and a test suite that seemed to observe it would be wrong.
"""

import pytest

from riemann_framework.lattice_reduction import (
    apply_unimodular,
    babai_nearest_plane,
    basis_quality,
    closest_vector_bruteforce,
    coordinates_in_basis,
    det,
    dot,
    gauss_reduce,
    good_and_bad_basis,
    is_unimodular,
    lattice_points,
    norm_sq,
    random_unimodular,
    same_lattice,
    shortest_vector,
    skew_matrix,
)


# ============================================================
# Geometry
# ============================================================

def test_dot_and_determinant():
    assert dot((1, 0), (0, 1)) == 0
    assert norm_sq((3, 4)) == 25
    assert det((1, 0), (0, 1)) == 1
    assert det((2, 0), (0, 3)) == 6


def test_gauss_reduce_returns_a_canonical_basis_for_z2():
    a, b = gauss_reduce((1, 0), (0, 1))
    assert {a, b} == {(1, 0), (0, 1)}


def test_gauss_reduce_satisfies_the_optimality_condition():
    """`|dot(b1, b2)| <= |b1|^2 / 2`, the 2D definition of reduced."""
    for basis in (
        ((4, 1), (1, 3)),
        ((100, 1), (1, 0)),
        ((7, 5), (3, 2)),
        ((12, 0), (5, 5)),
    ):
        a, b = gauss_reduce(*basis)
        assert norm_sq(a) <= norm_sq(b)
        assert abs(dot(a, b)) * 2 <= norm_sq(a)


def test_gauss_reduce_preserves_the_lattice():
    for basis in (((4, 1), (1, 3)), ((100, 1), (1, 0)), ((7, 5), (3, 2))):
        reduced = gauss_reduce(*basis)
        assert same_lattice(basis, reduced)
        assert abs(det(*basis)) == abs(det(*reduced))


def test_gauss_reduce_rejects_dependent_vectors():
    with pytest.raises(ValueError):
        gauss_reduce((2, 4), (1, 2))


def test_shortest_vector_is_actually_shortest():
    """Compare against an exhaustive search, so 'shortest' is not self-certified."""
    basis = ((9, 4), (4, 2))
    claimed = shortest_vector(basis)
    n = norm_sq(claimed)
    assert n > 0
    found = min(
        (norm_sq(v) for v in lattice_points(basis, 6) if v != (0, 0)),
        default=None,
    )
    assert found is not None
    assert n == found


# ============================================================
# Same lattice, different basis
# ============================================================

def test_skew_matrix_is_unimodular_for_every_stretch():
    for k in (1, 2, 5, 20, 1000):
        assert is_unimodular(skew_matrix(k))


def test_good_and_bad_basis_span_the_same_lattice():
    """The structural claim, checked exactly rather than by a picture.

    The two bases look nothing alike -- one is orthogonal, the other's vectors are
    almost parallel -- and they generate exactly the same point set.
    """
    good, bad = good_and_bad_basis(20)
    assert same_lattice(good, bad)
    assert abs(det(*good)) == abs(det(*bad))


def test_the_bad_basis_is_actually_bad():
    """Measured, not asserted from the name."""
    good, bad = good_and_bad_basis(20)
    good_quality = basis_quality(*good)
    bad_quality = basis_quality(*bad)
    assert good_quality.orthogonality_defect == pytest.approx(1.0)
    assert bad_quality.orthogonality_defect > 1000
    assert bad_quality.angle_degrees < 1.0
    assert good_quality.angle_degrees == pytest.approx(90.0)


def test_same_lattice_detects_a_genuinely_different_lattice():
    """The check can fail, which is what makes the pass meaningful."""
    assert not same_lattice(((1, 0), (0, 1)), ((2, 0), (0, 1)))
    assert not same_lattice(((1, 0), (0, 1)), ((1, 0), (0, 2)))


def test_coordinates_in_basis_rejects_off_lattice_points():
    """A real-valued solve would return coordinates for any point in the plane."""
    assert coordinates_in_basis(((2, 0), (0, 2)), (4, 6)) == (2, 3)
    assert coordinates_in_basis(((2, 0), (0, 2)), (3, 1)) is None


def test_apply_unimodular_preserves_the_lattice_for_random_matrices():
    rng_basis = ((3, 1), (1, 2))
    for seed in range(25):
        matrix = random_unimodular(seed, magnitude=4)
        assert is_unimodular(matrix)
        moved = apply_unimodular(rng_basis, matrix)
        assert same_lattice(rng_basis, moved)


def test_lattice_points_counts_the_expected_number():
    points = lattice_points(((1, 0), (0, 1)), 2)
    assert len(points) == 25
    assert (0, 0) in points


# ============================================================
# Closest vector, in dimension 2
# ============================================================

def test_babai_agrees_with_exhaustive_search_on_a_good_basis():
    basis = ((1, 0), (0, 1))
    for target in ((6.3, 4.1), (-3.7, 9.2), (0.4, -2.6), (0.5, 0.5)):
        assert babai_nearest_plane(basis, target) == closest_vector_bruteforce(
            basis, target, 12
        )


def test_babai_on_the_bad_basis_matches_search_on_the_good_one():
    """The same lattice described two ways gives the same nearest point.

    This is the honest version of the "good basis vs bad basis" story in
    dimension 2. The bad description does not make the problem hard *here*,
    because Gauss reduction recovers a good basis from it in polynomial time.
    What it makes is the *naive* search expensive; the answer is unchanged.
    """
    good, bad = good_and_bad_basis(20)
    for target in ((6.3, 4.1), (-3.7, 9.2), (0.4, -2.6)):
        from_bad = babai_nearest_plane(bad, target)
        from_good = closest_vector_bruteforce(good, target, 12)
        assert from_bad == from_good


def test_babai_returns_a_lattice_point():
    good, bad = good_and_bad_basis(15)
    for target in ((6.3, 4.1), (-9.9, 0.1)):
        point = babai_nearest_plane(bad, target)
        assert coordinates_in_basis(bad, point) is not None


def test_quality_rejects_dependent_vectors():
    with pytest.raises(ValueError):
        basis_quality((1, 1), (2, 2))
