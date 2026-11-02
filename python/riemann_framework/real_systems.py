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
"""Real systems with real involutions: does the diagnostic carry over?

Every other measurement in this framework is made on Gaussian blocks. The evidence for the
sector-count diagnostic would be thin if it only held there. Three systems that a physicist
would actually write down are built here, each with an **exact** involution, and the
statistic is measured on the full spectrum and on the sectors:

* the **transverse-field Ising chain** ``-J sum sz_i sz_{i+1} - h sum sx_i``, whose spin
  flip ``prod sx_i`` commutes with it exactly, at the free-fermion point and away from it;
* the **Heisenberg chain** ``sum S_i . S_{i+1}`` with a next-nearest-neighbour coupling and
  weak bond disorder, in the zero-magnetisation sector, whose spin flip commutes with it
  exactly and which is the standard chaotic many-body model;
* the **kicked top**, a Floquet operator ``exp(-i p Jz^2 / 2j) exp(-i q Jy)`` whose
  ``exp(-i pi Jy)`` commutes with it exactly, where the spectrum is a set of phases on a
  circle rather than energies on a line.

The measurement is the same one the manuscript makes on synthetic spectra: is the full
spectrum's mean ratio below each sector's? On the chaotic systems it is, and splitting
restores a value near the Gaussian reference. On the integrable Ising chain it is not a
random-matrix spectrum at all, and the module says so rather than reporting a count.

Two conventions are pinned here because real spectra force the question:

* ratios are formed from the **raw** spectrum (no polynomial unfolding): the ratio is
  invariant under a locally smooth density by construction, which is why it transfers to a
  many-body spectrum at all;
* **degenerate spacings are dropped** before the ratios are formed. ``statistics.r_ratio``
  does not drop them, and a spectrum with ``n`` exact degeneracies produces ``2n`` ratios
  equal to zero, which drags the mean down by a factor of two or more: the free Ising chain
  at ten spins measures ``0.042`` unfiltered and ``0.344`` filtered, and only the second
  number is comparable to anything.

Nothing here uses the Riemann zeros, and no claim about them is made.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .desymmetrisation import sector_blocks

#: Mean gap ratio of a Poisson spectrum, of a GOE block and of a GUE block, as used
#: throughout the manuscript.
POISSON_MEAN_RATIO = 0.386
GOE_MEAN_RATIO = 0.531
GUE_MEAN_RATIO = 0.600

#: A spacing below this is treated as a degeneracy and dropped.
DEGENERACY_TOLERANCE = 1e-12


# ============================================================
# The statistics, with the real-spectrum conventions
# ============================================================

def ratios_from_spacings(spacings: np.ndarray, circular: bool = False) -> np.ndarray:
    """``min/max`` of consecutive spacings, optionally closing a circle.

    On a circle every spacing has two neighbours, including the wrap-around, so ``n``
    phases give ``n`` ratios rather than ``n - 1``. That matters for a Floquet spectrum:
    the same sector measured as a line and as a circle differs by one ratio, and the
    circle is the geometric object the phases live on.
    """
    values = np.asarray(spacings, dtype=float)
    if values.size < 2:
        return np.array([])
    if circular:
        following = np.roll(values, -1)
        return np.minimum(values, following) / np.maximum(values, following)
    return np.minimum(values[:-1], values[1:]) / np.maximum(values[:-1], values[1:])


def mean_ratio(values, circular: bool = False) -> float:
    """The mean adjacent-gap ratio of a spectrum, with degeneracies dropped.

    ``circular=True`` treats the values as phases in ``[0, 2 pi)`` and closes the circle.
    A degenerate spacing is dropped whole: leaving it in forms ratios of ``0 / x``, which
    are zero for a reason that has nothing to do with level repulsion.
    """
    levels = np.sort(np.asarray(values, dtype=float))
    if levels.size < 3:
        return float("nan")
    if circular:
        spacings = np.diff(np.concatenate([levels, [levels[0] + 2.0 * np.pi]]))
    else:
        spacings = np.diff(levels)
    spacings = spacings[spacings > DEGENERACY_TOLERANCE]
    ratios = ratios_from_spacings(spacings, circular=circular)
    return float(np.mean(ratios)) if ratios.size else float("nan")


# ============================================================
# Systems
# ============================================================

def _kron_product(operators: list[np.ndarray]) -> np.ndarray:
    """Kronecker product of a list, left to right."""
    out = np.array([[1.0]])
    for operator in operators:
        out = np.kron(out, operator)
    return out


def _local_site(n_sites: int, site: int, operator: np.ndarray) -> np.ndarray:
    """One single-site operator embedded in the ``2 ** n_sites`` space."""
    operators = [np.eye(2)] * n_sites
    operators[site] = operator
    return _kron_product(operators)


#: Pauli matrices, in the ``sz`` basis.
_SX = np.array([[0.0, 1.0], [1.0, 0.0]])
_SZ = np.array([[1.0, 0.0], [0.0, -1.0]])


def tfim_chain(
    n_sites: int,
    field: float = 1.0,
    coupling: float = 1.0,
    next_neighbour: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """The transverse-field Ising chain and its spin-flip parity, periodic in the sites.

    ``H = -coupling sum sz_i sz_{i+1} - next_neighbour sum sz_i sz_{i+2} - field sum sx_i``
    and ``P = prod sx_i``. ``[H, P] = 0`` exactly, because every term carries an even
    number of ``sx``. At ``next_neighbour = 0`` the chain is free (Jordan-Wigner) and
    integrable; away from zero it is not, though at ten spins the measured statistics say
    more about the free-fermion structure than about integrability (see the note).
    """
    if n_sites < 2:
        raise ValueError("need at least two sites")
    dimension = 2**n_sites
    hamiltonian = np.zeros((dimension, dimension))
    for site in range(n_sites):
        for offset, strength in ((1, coupling), (2, next_neighbour)):
            if strength == 0.0:
                continue
            other = (site + offset) % n_sites
            if other == site:
                continue
            operators = [np.eye(2)] * n_sites
            operators[site] = _SZ
            operators[other] = _SZ
            hamiltonian -= strength * _kron_product(operators)
    for site in range(n_sites):
        hamiltonian -= field * _local_site(n_sites, site, _SX)

    parity = np.eye(dimension)
    for site in range(n_sites):
        parity = parity @ _local_site(n_sites, site, _SX)
    return hamiltonian, parity


def fixed_magnetisation_basis(n_sites: int) -> tuple[list[int], dict[int, int]]:
    """Basis states with exactly half the spins up, and their positions."""
    if n_sites % 2:
        raise ValueError("an even number of sites is needed for zero magnetisation")
    states = [state for state in range(2**n_sites) if bin(state).count("1") == n_sites // 2]
    return states, {state: index for index, state in enumerate(states)}


def heisenberg_chain(
    n_sites: int = 10,
    coupling: float = 1.0,
    next_neighbour: float = 0.0,
    disorder: float = 0.0,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """The Heisenberg chain in the zero-magnetisation sector, and its spin flip.

    ``H = sum_b J_b (Sx Sx + Sy Sy + Sz Sz)`` over nearest and, if asked, next-nearest
    bonds, periodic in the sites. Each bond strength is ``J (1 + disorder * u)`` with ``u``
    uniform in ``[-1, 1]``: the disorder is what breaks translation and reflection, the two
    symmetries this sector would otherwise still carry, so that the spin flip is the only
    involution left and the full spectrum really is the union of exactly two sectors.
    With ``disorder = 0`` and ``next_neighbour = 0`` the chain is the Bethe-ansatz
    integrable point.

    The spin flip is ``state -> complement(state)``, a permutation matrix commuting with
    the Hamiltonian because the bond list is invariant under the complement.
    """
    states, index = fixed_magnetisation_basis(n_sites)
    dimension = len(states)
    rng = np.random.default_rng(seed)
    bonds = [
        (site, (site + 1) % n_sites,
         coupling * (1.0 + disorder * (rng.random() - 0.5) * 2.0))
        for site in range(n_sites)
    ]
    if next_neighbour:
        bonds += [
            (site, (site + 2) % n_sites,
             next_neighbour * (1.0 + disorder * (rng.random() - 0.5) * 2.0))
            for site in range(n_sites)
        ]

    hamiltonian = np.zeros((dimension, dimension))
    for site, other, strength in bonds:
        if site == other:
            continue
        for column, state in enumerate(states):
            bit_a = (state >> site) & 1
            bit_b = (state >> other) & 1
            hamiltonian[index[state], column] += strength * (
                0.25 if bit_a == bit_b else -0.25
            )
            if bit_a != bit_b:
                flipped = state ^ (1 << site) ^ (1 << other)
                hamiltonian[index[flipped], column] += 0.5 * strength

    mask = 2**n_sites - 1
    parity = np.zeros((dimension, dimension))
    for column, state in enumerate(states):
        parity[index[state ^ mask], column] = 1.0
    return hamiltonian, parity


def _unitary(matrix: np.ndarray) -> np.ndarray:
    """``exp(-i * matrix)`` for a Hermitian ``matrix``."""
    values, vectors = np.linalg.eigh((matrix + matrix.conj().T) / 2.0)
    return (vectors * np.exp(-1j * values)) @ vectors.conj().T


def kicked_top(
    spin: int = 60,
    kick: float = 4.0,
    precession: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """The kicked top as a Floquet operator, and its parity ``exp(-i pi Jy)``.

    ``U = exp(-i kick Jz^2 / 2j) exp(-i precession Jy)`` in the ``|j, m>`` basis of
    dimension ``2j + 1``. Both factors commute with the rotation by pi about ``y``, which
    is therefore an exact involution of the Floquet operator: ``Jz^2`` is invariant under
    it and ``exp(-i precession Jy)`` commutes with it because both are functions of
    ``Jy``. Its two eigenspaces are the Floquet analogue of the parity sectors.

    The eigenphases live on a circle, so :func:`mean_ratio` is called with
    ``circular=True``.
    """
    dimension = 2 * spin + 1
    m_values = np.arange(spin, -spin - 1, -1, dtype=float)
    jz = np.diag(m_values)
    raising = np.zeros((dimension, dimension))
    for row in range(dimension - 1):
        raising[row, row + 1] = np.sqrt(
            spin * (spin + 1) - m_values[row + 1] * (m_values[row + 1] + 1)
        )
    jy = (raising - raising.T) / 2j
    unitary = _unitary(kick * jz @ jz / (2.0 * spin)) @ _unitary(precession * jy)
    parity = _unitary(np.pi * jy)
    return unitary, parity


# ============================================================
# The measurement
# ============================================================

@dataclass(frozen=True)
class SystemSpectra:
    """A full spectrum, its sectors, and the commutator that justifies the split."""

    name: str
    full: np.ndarray
    sectors: list[np.ndarray]
    circular: bool
    commutator: float

    @property
    def full_mean(self) -> float:
        return mean_ratio(self.full, circular=self.circular)

    @property
    def sector_means(self) -> list[float]:
        return [mean_ratio(sector, circular=self.circular) for sector in self.sectors]

    @property
    def split_raises_the_statistic(self) -> bool:
        """Is the full spectrum's mean below *every* sector's?"""
        means = self.sector_means
        return bool(means) and all(
            self.full_mean < value for value in means
        )

    def summary(self) -> str:
        sectors = ", ".join(f"{value:.3f}" for value in self.sector_means)
        return (
            f"{self.name:>34}: full {self.full_mean:.3f} ({self.full.size} levels), "
            f"sectors {sectors}, [H,P] {self.commutator:.1e}"
        )


def _check_involution(involution: np.ndarray, tolerance: float = 1e-8) -> None:
    square = involution @ involution
    if np.abs(square - np.eye(involution.shape[0])).max() > tolerance:
        raise ValueError("the involution does not square to the identity")


def analyse_hamiltonian(
    name: str,
    matrix: np.ndarray,
    involution: np.ndarray,
    tolerance: float = 1e-8,
) -> SystemSpectra:
    """Split a Hermitian matrix by an involution and measure both views.

    The commutator is checked rather than assumed: a split by an operator that does not
    commute with the Hamiltonian mixes sectors and produces a meaningless comparison. The
    check is a real one, and a test drives it into failing.
    """
    matrix = np.asarray(matrix, dtype=float)
    involution = np.asarray(involution, dtype=float)
    if matrix.shape != involution.shape or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("the involution must have the Hamiltonian's shape")
    if np.abs(matrix - matrix.T).max() > tolerance:
        raise ValueError("the Hamiltonian is not symmetric")
    commutator = float(np.abs(matrix @ involution - involution @ matrix).max())
    if commutator > tolerance:
        raise ValueError(
            f"the involution does not commute with the Hamiltonian "
            f"(max |[H, P]| = {commutator:.3e})"
        )
    _check_involution(involution, tolerance)
    blocks = sector_blocks(matrix.astype(complex), [involution.astype(complex)])
    return SystemSpectra(
        name=name,
        full=np.linalg.eigvalsh(matrix),
        sectors=[np.linalg.eigvalsh(block.real) for _, block in sorted(blocks.items())],
        circular=False,
        commutator=commutator,
    )


def analyse_floquet(
    name: str,
    unitary: np.ndarray,
    involution: np.ndarray,
    tolerance: float = 1e-8,
) -> SystemSpectra:
    """The Floquet analogue: split the unitary by its parity and take eigenphases.

    ``sector_blocks`` cannot be reused here, because the blocks of a Floquet operator are
    unitary rather than Hermitian; the split is done with the involution's eigenvectors and
    the spectrum is the set of phases of each block's eigenvalues, sorted into ``[0, 2pi)``.
    """
    unitary = np.asarray(unitary, dtype=complex)
    involution = np.asarray(involution, dtype=complex)
    if unitary.shape != involution.shape:
        raise ValueError("the involution must have the unitary's shape")
    if np.abs(unitary.conj().T @ unitary - np.eye(unitary.shape[0])).max() > tolerance:
        raise ValueError("the Floquet operator is not unitary")
    commutator = float(np.abs(unitary @ involution - involution @ unitary).max())
    if commutator > tolerance:
        raise ValueError(
            f"the involution does not commute with the Floquet operator "
            f"(max |[U, P]| = {commutator:.3e})"
        )
    _check_involution(involution, tolerance)
    values, vectors = np.linalg.eigh((involution + involution.conj().T) / 2.0)
    sectors = []
    for sign in (1.0, -1.0):
        basis = vectors[:, np.where(values > 0.5 if sign > 0 else values < -0.5)[0]]
        block = basis.conj().T @ unitary @ basis
        phases = np.angle(np.linalg.eigvals(block))
        sectors.append(np.sort((phases + 2.0 * np.pi) % (2.0 * np.pi)))
    phases = np.angle(np.linalg.eigvals(unitary))
    return SystemSpectra(
        name=name,
        full=np.sort((phases + 2.0 * np.pi) % (2.0 * np.pi)),
        sectors=sectors,
        circular=True,
        commutator=commutator,
    )


# ============================================================
# The systems the report measures
# ============================================================

def tfim_system(
    n_sites: int = 10,
    field: float = 1.0,
    next_neighbour: float = 0.0,
    label: str | None = None,
) -> SystemSpectra:
    """The Ising chain at the free-fermion point, or away from it."""
    hamiltonian, parity = tfim_chain(
        n_sites, field=field, next_neighbour=next_neighbour
    )
    name = label or (
        "TFIM (free fermions)" if next_neighbour == 0.0 else "TFIM (interacting)"
    )
    return analyse_hamiltonian(name, hamiltonian, parity)


def heisenberg_system(
    n_sites: int = 10,
    next_neighbour: float = 0.0,
    disorder: float = 0.0,
    seed: int = 0,
    label: str | None = None,
) -> SystemSpectra:
    """The magnetisation sector of the Heisenberg chain."""
    hamiltonian, parity = heisenberg_chain(
        n_sites, next_neighbour=next_neighbour, disorder=disorder, seed=seed
    )
    name = label or (
        "Heisenberg (integrable)" if next_neighbour == 0.0 and disorder == 0.0
        else "Heisenberg (chaotic)"
    )
    return analyse_hamiltonian(name, hamiltonian, parity)


def kicked_top_system(
    spin: int = 60, kick: float = 4.0, precession: float = 2.0
) -> SystemSpectra:
    """The kicked top's Floquet spectrum, split by its parity."""
    unitary, parity = kicked_top(spin=spin, kick=kick, precession=precession)
    return analyse_floquet(f"kicked top (j = {spin})", unitary, parity)


#: The reference values a random-matrix spectrum should sit near.
REFERENCE_VALUES: dict[str, float] = {
    "Poisson": POISSON_MEAN_RATIO,
    "GOE": GOE_MEAN_RATIO,
    "GUE": GUE_MEAN_RATIO,
}

#: What the systems in the report are, so the script and the tests agree.
DEFAULT_SYSTEMS: tuple[str, ...] = (
    "tfim_free",
    "tfim_interacting",
    "heisenberg_chaotic",
    "kicked_top",
)


def default_systems() -> dict[str, SystemSpectra]:
    """The four spectra the report and the note use, built on demand."""
    return {
        "tfim_free": tfim_system(10, field=1.0, next_neighbour=0.0),
        "tfim_interacting": tfim_system(10, field=1.0, next_neighbour=0.3),
        "heisenberg_chaotic": heisenberg_system(10, next_neighbour=0.5, disorder=0.3),
        "kicked_top": kicked_top_system(60, kick=4.0, precession=2.0),
    }
