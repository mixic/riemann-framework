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
"""Dynamical desymmetrisation: the double-bracket flow, and what it cannot do.

The static utility in `desymmetrisation.py` splits a Hamiltonian into the sectors of a
commuting involution. This module is the dynamical analogue, and its first finding is
that the analogy is **about the state, not the spectrum**.

The flow is the double-bracket (Brockett) gradient flow

    d rho / d beta = [[rho, H], rho] = 2 rho H rho - H rho^2 - rho^2 H,

which is isospectral: `[[rho, H], rho]` is a commutator with `rho`, so the step is
tangent to the similarity orbit and every eigenvalue of `rho` is conserved. The flow
minimises `tr(H rho)` along that orbit, hence its limit set is contained in the states
that commute with `H`. Three consequences, all measured by the tests:

1. **The invariance direction is what the papers describe.** If `[rho, sigma] = 0` and
   `[H, sigma] = 0`, then `[rho(beta), sigma] = 0` for every `beta`: the increment
   commutes with `sigma` whenever `rho` and `H` do, so the sector populations
   `tr(P_+ rho)` and `tr(P_- rho)` are constants of the motion.

2. **The flow cannot desymmetrise a Hamiltonian.** It never acts on `H`. `H` is an
   input, `rho` is the variable, and the flow is isospectral in `rho`; no spacing
   statistic of `H` -- and none of `rho`'s spectrum -- changes by construction. A
   contaminated `H` stays contaminated, and the class test of
   `desymmetrisation.py` is not repaired by evolving anything.

3. **It does something the papers do not claim, and it is not desymmetrisation either:
   from a cross-sector state it *selects* a sector.** If `[rho_0, sigma] != 0` the
   populations move, and because the limit commutes with `H` and `sigma` commutes with
   `H` (so the eigenbasis can be chosen inside sectors), the limit is block-diagonal:
   the coherence `||[rho, sigma]||` decays to zero. Measured: `1.41 -> 3e-3` over
   `beta = 15`, with the population moving from `(0.50, 0.50)` to `(1.00, 0.00)`.
   That is a state collapsing into one sector, not a spectrum being split.

The multi-copy circuit identity quoted from the literature is checked numerically in
`two_copy_expansion`, and the check is a **negative** result: the natural two-copy
circuits `exp(i sqrt(eps) (H_1 - H_2))` (with or without a swap, and the Trotter split
of the two phases) do not reproduce

    Tr_2[u rho_1 (x) rho_2 u^dag] = rho_1 - eps [[rho_1, H], rho_1] + O(eps^{3/2}).

They produce a first-order term `i sqrt(eps) [H, rho_1]` -- which the quoted identity
does not have -- and a second-order term that is not (plus or minus) the double bracket.
The claim is therefore recorded as unverified from the description available here: the
identity depends on the circuit's generator, which was not read. What *is* verified is
the flow itself and its invariants.

Nothing here concerns the Riemann hypothesis. It exists because the repository's
desymmetrisation tool has a static and a dynamical reading, and only one of them is a
statement about spectra.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ============================================================
# The flow
# ============================================================


def _square(matrix, name: str) -> np.ndarray:
    array = np.asarray(matrix, dtype=complex)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError(f"{name} must be a square matrix")
    return array


def commutator_norm(first, second) -> float:
    """Frobenius norm of `[A, B]`. Zero is a symmetry, not a small number."""
    left = _square(first, "first operator")
    right = _square(second, "second operator")
    if left.shape != right.shape:
        raise ValueError("operators must have the same shape")
    return float(np.linalg.norm(left @ right - right @ left))


def double_bracket(rho, hamiltonian) -> np.ndarray:
    """The right-hand side of `d rho / d beta = [[rho, H], rho]`.

    Written out as `2 rho H rho - H rho^2 - rho^2 H` so that no intermediate `[.,.]`
    is formed twice. The increment is a commutator with `rho`, which is why the flow is
    isospectral.
    """
    state = _square(rho, "density matrix")
    hermitian = _square(hamiltonian, "hamiltonian")
    if state.shape != hermitian.shape:
        raise ValueError("the density matrix and the hamiltonian must have the same shape")
    return 2.0 * (state @ hermitian @ state) - (hermitian @ state @ state) - (
        state @ state @ hermitian
    )


def sector_projectors(involutions) -> list[np.ndarray]:
    """Joint sector projectors of a set of commuting involutions, as a list."""
    operators = [_square(operator, "involution") for operator in involutions]
    dimension = operators[0].shape[0]
    identity = np.eye(dimension, dtype=complex)
    projectors: list[np.ndarray] = []
    for signs in _sector_signs(len(operators)):
        projector = identity.copy()
        for sign, operator in zip(signs, operators):
            projector = projector @ (identity + sign * operator) / 2.0
        projectors.append(projector)
    return projectors


def _sector_signs(count: int) -> list[tuple[int, ...]]:
    signs: list[tuple[int, ...]] = [()]
    for _ in range(count):
        signs = [signs_so_far + (sign,) for signs_so_far in signs for sign in (1, -1)]
    return signs


def sector_populations(rho, involutions) -> np.ndarray:
    """`tr(P rho)` for every joint sector `P`: the state's mass in each sector.

    These are the quantities the flow conserves when the state and the Hamiltonian
    commute with the involutions. A contaminated spectrum and a state are different
    objects: this measures the state.
    """
    state = _square(rho, "density matrix")
    projectors = sector_projectors(involutions)
    return np.array(
        [float(np.real(np.trace(projector @ state))) for projector in projectors]
    )


@dataclass(frozen=True)
class FlowReport:
    """The trajectory of the double-bracket flow, and the invariants along it."""

    betas: np.ndarray
    states: np.ndarray
    sector_populations: np.ndarray
    coherences: np.ndarray
    spectrum_drift: float
    trace_drift: float
    hermiticity_drift: float
    commutant_preserved: bool
    sector_selected: bool
    explanation: str
    invariant: str = "the flow never acts on H: no spectral statistic of H can change"

    @property
    def final(self) -> np.ndarray:
        return self.states[-1]

    def summary(self) -> str:
        return (
            f"beta {self.betas[0]:.2f} -> {self.betas[-1]:.2f}, "
            f"spectrum drift {self.spectrum_drift:.1e}, "
            f"coherence {self.coherences[0]:.3f} -> {self.coherences[-1]:.3f}, "
            f"populations {self.sector_populations[0].round(3).tolist()} -> "
            f"{self.sector_populations[-1].round(3).tolist()}: {self.explanation} "
            f"({self.invariant})"
        )


def flow(
    rho0,
    hamiltonian,
    involutions=(),
    beta: float = 4.0,
    steps: int = 800,
    direction: int = 1,
    decohere: bool = True,
) -> FlowReport:
    """Integrate the double-bracket flow with RK4 and record its invariants.

    `direction = +1` is the descent direction of `tr(H rho)`: the energy expectation
    decreases along the run, which is the "imaginary-time-like" direction the flow is
    used for. `direction = -1` ascends; it is available so that the sign convention can
    be tested rather than assumed.

    `decohere` symmetrises the state after each step, which removes the O(dt^5) drift in
    Hermiticity that RK4 would otherwise leave; the effect on the flow is a change of
    order `dt^4`, far below the tolerances the tests use.
    """
    if direction not in (1, -1):
        raise ValueError("direction must be +1 or -1")
    if steps < 2:
        raise ValueError("need at least two steps")
    if beta <= 0.0:
        raise ValueError("beta must be positive")
    state = _square(rho0, "initial state")
    hermitian = _square(hamiltonian, "hamiltonian")
    if state.shape != hermitian.shape:
        raise ValueError("the initial state and the hamiltonian must have the same shape")
    if np.abs(state - state.conj().T).max() > 1e-8:
        raise ValueError("the initial state must be Hermitian")
    if np.abs(hermitian - hermitian.conj().T).max() > 1e-8:
        raise ValueError("the hamiltonian must be Hermitian")
    if np.real(np.trace(state)) <= 0.0:
        raise ValueError("the initial state must have positive trace")

    operators = [_square(operator, "involution") for operator in involutions]
    for operator in operators:
        if np.abs(operator @ operator - np.eye(operator.shape[0])).max() > 1e-8:
            raise ValueError("every involution must be an involution (U^2 = I)")
        if commutator_norm(hermitian, operator) > 1e-8 * np.linalg.norm(hermitian):
            raise ValueError("every involution must commute with the hamiltonian")

    dt = beta / steps
    sign = float(direction)
    current = state.copy()
    baseline_spectrum = np.sort(np.linalg.eigvalsh(current))
    baseline_populations = (
        sector_populations(current, operators) if operators else np.array([])
    )
    baseline_coherence = max(
        (commutator_norm(current, operator) for operator in operators), default=0.0
    )

    states = [current.copy()]
    betas = [0.0]
    populations = [baseline_populations.copy()]
    coherences = [baseline_coherence]

    for index in range(steps):
        k1 = sign * double_bracket(current, hermitian)
        k2 = sign * double_bracket(current + 0.5 * dt * k1, hermitian)
        k3 = sign * double_bracket(current + 0.5 * dt * k2, hermitian)
        k4 = sign * double_bracket(current + dt * k3, hermitian)
        current = current + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if decohere:
            current = (current + current.conj().T) / 2.0
        states.append(current.copy())
        betas.append((index + 1) * dt)
        if operators:
            populations.append(sector_populations(current, operators))
            coherences.append(
                max(commutator_norm(current, operator) for operator in operators)
            )

    stack = np.stack(states)
    spectrum_drift = max(
        float(np.abs(np.sort(np.linalg.eigvalsh(state_)) - baseline_spectrum).max())
        for state_ in stack
    )
    trace_drift = max(
        float(abs(np.real(np.trace(state_)) - np.real(np.trace(state)))) for state_ in stack
    )
    hermiticity_drift = max(
        float(np.abs(state_ - state_.conj().T).max()) for state_ in stack
    )

    population_array = (
        np.stack(populations) if operators else np.zeros((len(states), 0))
    )
    coherence_array = np.array(coherences) if operators else np.zeros(len(states))

    commutant_preserved = True
    sector_selected = False
    explanation = "no involution was supplied, so there is no sector structure to report"
    if operators:
        final_pops = population_array[-1]
        commutant_preserved = bool(
            np.abs(final_pops - baseline_populations).max() < 1e-6
            and coherence_array[-1] <= baseline_coherence + 1e-9
        )
        sector_selected = bool(
            coherence_array[-1] < 0.05 * max(baseline_coherence, 1e-12)
            and final_pops.max() > 0.9
        )
        if baseline_coherence < 1e-9:
            explanation = (
                "the state commutes with the involution and the flow preserves the "
                "commutant: sector populations are constants of the motion"
            )
        elif sector_selected:
            explanation = (
                "the state did not commute with the involution; the flow drove the "
                "coherence to zero and the population into one sector -- a state "
                "selecting a sector, not a spectrum being split"
            )
        else:
            explanation = (
                "the state did not commute with the involution and the flow did not "
                "select a sector within this beta"
            )

    return FlowReport(
        betas=np.array(betas),
        states=stack,
        sector_populations=population_array,
        coherences=coherence_array,
        spectrum_drift=spectrum_drift,
        trace_drift=trace_drift,
        hermiticity_drift=hermiticity_drift,
        commutant_preserved=commutant_preserved,
        sector_selected=sector_selected,
        explanation=explanation,
    )


def dynamical_desymmetrise(
    hamiltonian,
    involution,
    rho0,
    beta: float = 4.0,
    steps: int = 800,
) -> FlowReport:
    """The dynamical counterpart of `desymmetrisation.desymmetrise`, for a state.

    The signature follows the static utility (`H`, the involution, and the object that
    is evolved), and the name is deliberately *not* a promise: the flow cannot split a
    Hamiltonian. What the returned report measures is the state's sector structure along
    the trajectory -- whether it is a constant of the motion, or whether the flow
    selects a sector.
    """
    return flow(
        rho0,
        hamiltonian,
        involutions=[involution],
        beta=beta,
        steps=steps,
    )


# ============================================================
# The multi-copy circuit, checked rather than quoted
# ============================================================


def _unitary_from_hermitian(generator: np.ndarray, angle: float) -> np.ndarray:
    """`exp(i angle S)` for Hermitian `S`, by eigendecomposition (no scipy)."""
    values, vectors = np.linalg.eigh(generator)
    phases = np.exp(1j * angle * values)
    return (vectors * phases) @ vectors.conj().T


def _partial_trace_second_copy(state: np.ndarray, dimension: int) -> np.ndarray:
    """Trace out the second copy of a `dimension^2 x dimension^2` operator."""
    tensor = state.reshape(dimension, dimension, dimension, dimension)
    return np.einsum("iaja->ij", tensor)


def _swap_operator(dimension: int) -> np.ndarray:
    swap = np.zeros((dimension * dimension, dimension * dimension), dtype=complex)
    for i in range(dimension):
        for j in range(dimension):
            swap[i * dimension + j, j * dimension + i] = 1.0
    return swap


def two_copy_step(rho, hamiltonian, epsilon: float, generator: str = "difference") -> np.ndarray:
    """One two-copy circuit step, reduced over the second copy.

    `generator` selects the candidate circuit:

    * `"difference"` -- `exp(i sqrt(eps) (H_1 - H_2))`;
    * `"swap"` -- the same with a swap inserted: `exp(i sqrt(eps) S P)`;
    * `"split"` -- the Trotter split `exp(i sqrt(eps) H_1) exp(-i sqrt(eps) H_2)`.

    All three start from `rho (x) rho` and trace out the second copy. The reduction is
    what the quoted identity computes; the three differ in their generators.
    """
    state = _square(rho, "density matrix")
    hermitian = _square(hamiltonian, "hamiltonian")
    if state.shape != hermitian.shape:
        raise ValueError("the density matrix and the hamiltonian must have the same shape")
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")
    dimension = state.shape[0]
    identity = np.eye(dimension, dtype=complex)
    product = np.kron(state, state)
    angle = float(np.sqrt(epsilon))

    if generator == "difference":
        first = np.asarray(np.kron(hermitian, identity), dtype=complex)
        second = np.asarray(np.kron(identity, hermitian), dtype=complex)
        unitary = _unitary_from_hermitian(first - second, angle)
    elif generator == "swap":
        first = np.asarray(np.kron(hermitian, identity), dtype=complex)
        second = np.asarray(np.kron(identity, hermitian), dtype=complex)
        unitary = _unitary_from_hermitian((first - second) @ _swap_operator(dimension), angle)
    elif generator == "split":
        first = np.asarray(np.kron(hermitian, identity), dtype=complex)
        second = np.asarray(np.kron(identity, hermitian), dtype=complex)
        unitary = _unitary_from_hermitian(first, angle) @ _unitary_from_hermitian(
            -second, angle
        )
    else:
        raise ValueError(f"unknown generator {generator!r}")

    evolved = unitary @ product @ unitary.conj().T
    return _partial_trace_second_copy(evolved, dimension)


@dataclass(frozen=True)
class CircuitExpansion:
    """`rho(eps) = rho + sqrt(eps) A + eps B + ...`, fitted numerically."""

    first_order: np.ndarray
    second_order: np.ndarray
    target: np.ndarray
    generator: str

    @property
    def first_order_is_zero(self) -> bool:
        return bool(np.linalg.norm(self.first_order) < 1e-8)

    @property
    def second_order_matches_target(self) -> bool:
        return bool(
            min(
                np.linalg.norm(self.second_order - self.target),
                np.linalg.norm(self.second_order + self.target),
            )
            < 1e-3 * max(np.linalg.norm(self.target), 1e-12)
        )

    def summary(self) -> str:
        return (
            f"{self.generator}: ||A|| = {np.linalg.norm(self.first_order):.3e}, "
            f"||B|| = {np.linalg.norm(self.second_order):.3e}, "
            f"first order zero: {self.first_order_is_zero}, "
            f"second order is +/-[[rho,H],rho]: {self.second_order_matches_target}"
        )


def two_copy_expansion(
    rho,
    hamiltonian,
    generator: str = "difference",
    scales=(1e-3, 1e-4, 1e-5),
) -> CircuitExpansion:
    """Fit the first two terms of the circuit's `sqrt(eps)` expansion.

    The quoted identity claims `A = 0` and `B = -[[rho, H], rho]`. The fit measures what
    the circuit actually does: it solves for `A` and `B` from three scales, using the
    difference from the zeroth-order term, so a non-zero `A` is not silently absorbed.
    """
    if len(scales) != 3:
        raise ValueError("need exactly three epsilon scales")
    state = _square(rho, "density matrix")
    hermitian = _square(hamiltonian, "hamiltonian")
    evaluations = [two_copy_step(state, hermitian, epsilon, generator) for epsilon in scales]
    roots = np.sqrt(np.array(scales))
    matrix = np.array(
        [
            [roots[0] - roots[2], scales[0] - scales[2]],
            [roots[1] - roots[2], scales[1] - scales[2]],
        ]
    )
    rhs = np.stack(
        [
            (evaluations[0] - evaluations[2]).ravel(),
            (evaluations[1] - evaluations[2]).ravel(),
        ],
        axis=0,
    )
    solved = np.linalg.solve(matrix, rhs)
    dimension = state.shape[0]
    target = -double_bracket(state, hermitian)
    return CircuitExpansion(
        first_order=solved[0].reshape(dimension, dimension),
        second_order=solved[1].reshape(dimension, dimension),
        target=target,
        generator=generator,
    )
