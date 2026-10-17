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
"""The Hilbert-Polya prototype: build the operator, then measure the four gaps.

The conjecture is that the nontrivial zeros of `zeta` are the eigenvalues of a
self-adjoint operator, so that "the eigenvalues are real" forces
`Re(s) = 1/2`. This module builds the most concrete version of that idea -- the
Berry-Keating dilation operator -- actually computes with it, and reports what it
does and does not deliver. **Nothing here proves or disproves the Riemann
hypothesis**, and the module is written so that claim cannot be misread.

What is built
-------------
`H = -i (x d/dx + 1/2)` on `L^2(0, inf)`, which is the symmetric quantization of
the classical `xp`. It is the honest starting point because it is the one case
where the critical line appears *algebraically*: `H x^a = -i(a + 1/2) x^a`, so
`H psi = E psi` with `psi = x^{-1/2 + iE}`. The exponent is exactly
`s - 1` with `s = 1/2 + iE`: **the operator's spectral parameter is the
ordinate, and the real part `1/2` is not a parameter at all but a fixed point of
the construction.** That much is real and is verified here.

The four gaps, all of them measured rather than asserted
--------------------------------------------------------
1. **No eigenvalues.** `|psi|^2 = x^{-1}` has `int_a^b |psi|^2 dx = log(b/a)`,
   which diverges at `b -> inf` *and* at `a -> 0`. No formal eigenfunction is in
   `L^2`, so `H` has empty point spectrum: its spectrum is all of the real line.
   A real line contains every real number, so it cannot select the zeros. The
   critical line is where the norm *stops being integrable* -- it is a boundary,
   not a discrete level.

2. **The box destroys the structure it was supposed to reveal.** Cutting off the
   infinity is not a technicality. With `y = log x` and a periodic box of length
   `L`, `H` becomes `-i d/dy` on a circle, whose eigenvalues are `2 pi n / L`:
   a **picket fence**, perfectly evenly spaced, with `r`-ratio exactly `1.000`.
   The first `100` zeros have `r`-ratio `0.610` and spacings ranging over
   `0.716 ... 6.887`. The box also gets the *density* wrong: a linear ladder has
   `N(T) = T L / 2 pi` while the zeros grow like `(T/2 pi) log(T/2 pi e)`, so a
   box fitted to hold `100` zeros by `gamma_100 = 236.52` predicts `21` levels
   below `T = 50` where there are `10` -- overcounting by `2.10x` -- and the
   overcount decays only as the fit height is approached: `1.45x` at `100`,
   `1.06x` at `200`. Even after rescaling the ladder onto the zeros' endpoints it
   misses by `14.40` on average, `6.4` mean spacings of `2.246`.
   The literature does not use a hard box for exactly this reason; it uses an
   action-dependent boundary condition whose form is the conjecture.

3. **A real spectrum is free, so self-adjointness carries no arithmetic.** Any
   prescribed list of real numbers is the spectrum of a self-adjoint operator --
   `diag(values)` is one. So "there exists a self-adjoint operator with real
   spectrum" is a tautology, and a finite numerical match of eigenvalues to
   zeros is a tautology performed with `n` numbers. What would have to be shown
   is that an operator *defined without reference to the zeros* has spectrum
   **provably** equal to them, infinitely many of them. No such construction
   exists. For the non-Hermitian route actually proposed in the literature
   (PT-symmetric Hamiltonians) the gap is even more visible: there reality is a
   *condition*, not a gift. The model below has an exact breaking threshold
   `theta_c = arcsin(s/r)` -- `30` degrees at `s/r = 1/2` -- below which the
   spectrum is real and above which it is a complex-conjugate pair. Reality has
   to be proved, and proving it for the Riemann operator is open.

4. **Imaginary time is blind to `Re(s)`.** This is the sharpest of the four. A
   thermal functional of a spectrum depends on the energies only:
   `Z(beta) = sum_n exp(-beta E_n)` uses `E_n`. If the zeros are the energies,
   then `E_n = Im(s_n)` and *the real parts never enter*. Moving a zero from
   `1/2 + i gamma` to `0.6 + i gamma` leaves every `Z(beta)` unchanged -- which
   the measurement below confirms is not approximately but identically true,
   because the ordinates are literally the same array. **Wick rotation erases
   exactly the information the Riemann hypothesis is about.** It is a
   consequence of spectral theory, not a route into it. What is genuinely
   checkable in this territory is the statement that makes it "temperature": the
   KMS periodicity of imaginary time, `G(tau) = G(beta - tau)`, verified here to
   `1e-16`, and the Hawking relation `beta = 8 pi G M / c^3`.

What would count as progress
----------------------------
An operator defined in arithmetic terms -- not by its spectrum -- together with a
proof that its spectrum is the zeros. Failing that, a construction that survives
all four of the tests above. The point of the prototype is that the four tests are
computable, so a candidate can be screened instead of admired.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .prime_orbits import zeta_zero_ordinates
from .statistics import mean_r_ratio


#: Stated wherever the continuum result is reported, because "the spectrum is the
#: whole real line" is easy to mistake for a success.
CONTINUUM_NOTE = (
    "The unregularized dilation operator has NO eigenvalues: its formal "
    "eigenfunctions are not normalizable at either end, so its spectrum is all "
    "of R. That is consistent with the zeros being real and equally consistent "
    "with every other real number being a zero. The continuum cannot select the "
    "zeros; it only contains them."
)

#: The measured failure of the "quantum box" regularization.
BOX_NOTE = (
    "A hard box in log x quantizes H to an evenly spaced picket fence "
    "(2 pi n / L). The zeros are not a picket fence: r-ratio 0.610 against "
    "1.000, spacings 0.716..6.887, and a logarithmic counting function against a "
    "linear one. A box fitted to hold 100 zeros by T = 236.5 predicts 21 levels "
    "below T = 50 where there are 10, i.e. 2.10x too many, and is still 1.06x "
    "too many at T = 200. The box is the naive regularization; the literature's "
    "action-dependent boundary condition is the conjecture, not a detail."
)

#: Why a spectral match does not prove the hypothesis.
NON_SEQUITUR_NOTE = (
    "Self-adjointness gives reality; it does not give the zeros. Any prescribed "
    "real list is the spectrum of a self-adjoint operator (diag of the list), so "
    "a finite eigenvalue match is a tautology with n numbers in it. The content "
    "of Hilbert-Polya is the identification spectrum = zeros for ALL zeros, "
    "which no finite computation can establish and no known operator achieves."
)

#: Why the Wick rotation cannot settle Re(s).
BLINDNESS_NOTE = (
    "Imaginary-time ('thermal') functionals of the spectrum depend on the "
    "energies alone. With E_n = Im(s_n), the real parts Re(s) do not appear "
    "anywhere, so moving zeros off the critical line changes nothing: Z(beta) is "
    "identical because the ordinates are literally the same. Wick rotation is a "
    "consequence of spectral theory, not a tool for proving reality."
)

#: The PT-symmetry route, and where it stops.
PT_NOTE = (
    "For a non-Hermitian (PT-symmetric) candidate, a real spectrum is a "
    "condition that must be established, not a consequence of the construction. "
    "The two-by-two model here has an exact threshold theta_c = arcsin(s/r), "
    "real below it and a conjugate pair above. Establishing that the Riemann "
    "operator is in the unbroken phase is open."
)

#: The only genuine thermodynamics in this file.
KMS_NOTE = (
    "What IS a theorem here is the temperature statement: the Euclidean "
    "correlator of a thermal state is symmetric about beta/2, G(tau) = "
    "G(beta - tau), i.e. imaginary time is a circle of circumference beta with "
    "Matsubara frequencies 2 pi n / beta. Verified to machine precision below. "
    "It says imaginary time behaves like inverse temperature; it says nothing "
    "about the critical line."
)

#: SI constants for the black-hole temperature, used only to check a formula.
GRAVITATIONAL_CONSTANT = 6.67430e-11
SPEED_OF_LIGHT = 2.99792458e8
REDUCED_PLANCK = 1.054571817e-34
BOLTZMANN = 1.380649e-23
SOLAR_MASS = 1.98892e30


# ============================================================
# 1. The dilation operator H = -i (x d/dx + 1/2)
# ============================================================

def eigenfunction_exponent(energy: float) -> complex:
    """The exponent `a` in `psi = x^a` for which `H psi = E psi`.

    `H x^a = -i (a + 1/2) x^a`, so `-i(a + 1/2) = E` gives `a = -1/2 + iE`.
    That value of `a` is `s - 1` at `s = 1/2 + iE`: the real part is pinned to
    `-1/2` by the construction, which is the algebraic shadow of the critical
    line.
    """
    return complex(-0.5, float(energy))


def algebraic_residual(energy: float) -> complex:
    """`H x^a / x^a - E` for `a = eigenfunction_exponent(E)`, in exact arithmetic.

    Returns zero (to rounding) because the eigenvalue relation is an identity:
    this checks the *algebra* of the claim, not a discretization of it. The
    finite-difference version below is a separate, lossier object.
    """
    a = eigenfunction_exponent(energy)
    return complex(0.0, -1.0) * (a + 0.5) - energy


def central_difference_residual(energy: float, spacing: float) -> float:
    """`|H_d psi / psi - E|` for the central-difference `H_d` on a uniform grid.

    The point of having this next to `algebraic_residual` is that the two
    disagree, and the disagreement is *predictable*: a central difference applied
    to `exp(a y)` returns `exp(a y) sinh(a h)/h`, so the residual is

        |a|^3 h^2 / 6,      a = -1/2 + iE,

    by `predicted_discretisation_error`. Measured against that formula it is an
    artefact-free diagnostic; read on its own, `1.2e-4` at `E = gamma_1` looks
    like a failure of the eigenfunction when it is only the grid.
    """
    a = eigenfunction_exponent(energy)
    a_eff = a * np.sinh(a * spacing) / (a * spacing)
    return float(abs(complex(0.0, -1.0) * (a_eff + 0.5) - energy))


def predicted_discretisation_error(energy: float, spacing: float) -> float:
    """`|a|^3 h^2 / 6`, the leading error of the central difference above."""
    a = eigenfunction_exponent(energy)
    return float(abs(a) ** 3 * spacing**2 / 6.0)


@dataclass(frozen=True)
class NormRow:
    """`int_a^b |psi|^2 dx` for the formal eigenfunction, at one width."""

    width: float
    norm_squared: float

    @property
    def log_width(self) -> float:
        return float(np.log(self.width))


def truncated_norm_squared(a: float, b: float) -> float:
    """`int_a^b |x^{-1/2+iE}|^2 dx = log(b/a)`, independent of `E`.

    The independence is not an accident of the formula: `|x^{-1/2+iE}|^2 = x^{-1}`
    for every real `E`, so this is the same log divergence for every energy.
    """
    if not (0.0 < a < b):
        raise ValueError("need 0 < a < b")
    return float(np.log(b / a))


def norm_growth_table(widths: list[float], lower: float = 1.0) -> list[NormRow]:
    """The truncated norm against the width, growing without bound.

    Grows at both ends: `lower -> 0` diverges too, which is the half of the
    statement that is usually omitted.
    """
    if lower <= 0:
        raise ValueError("lower must be positive")
    return [
        NormRow(width=w, norm_squared=truncated_norm_squared(lower, lower + w))
        for w in widths
    ]


# ============================================================
# 2. Regularizing with a box: the picket fence
# ============================================================

def box_spectrum(length: float, samples: int) -> np.ndarray:
    """Eigenvalues of `-i d/dy` on a circle of circumference `length`.

    `2 pi m / length` for the `samples` discrete wavenumbers, ascending. The
    spectrum is symmetric about zero, which is already a mismatch with the zeros
    (all positive); the prototype uses the positive half, where the spacing is
    `2 pi / length`.
    """
    if length <= 0:
        raise ValueError("length must be positive")
    if samples < 4 or samples % 2:
        raise ValueError("samples must be even and at least 4")
    return np.sort(2.0 * np.pi * np.fft.fftfreq(samples, d=length / samples))


def box_positive_levels(length: float, count: int) -> np.ndarray:
    """The first `count` positive rungs of the ladder: `2 pi n / length`."""
    if count < 1:
        raise ValueError("count must be at least 1")
    return 2.0 * np.pi * np.arange(1, count + 1) / length


def box_count(height: float, length: float) -> int:
    """`floor(height * length / 2 pi)`: the ladder's counting function, linear."""
    if height <= 0:
        raise ValueError("height must be positive")
    return int(np.floor(height * length / (2.0 * np.pi)))


def spectral_box_matrix(length: float, samples: int) -> np.ndarray:
    """The same operator as an explicit Hermitian matrix, via a spectral derivative.

    Built so that the discretization does not shadow the algebra:
    `i * A` is Hermitian with eigenvalues exactly `2 pi m / length`.
    """
    if samples < 4 or samples % 2:
        raise ValueError("samples must be even and at least 4")
    wavenumbers = 2.0 * np.pi * np.fft.fftfreq(samples, d=length / samples)
    forward = np.fft.fft(np.eye(samples))
    inverse = np.fft.ifft(np.eye(samples))
    return inverse @ np.diag(wavenumbers) @ forward


def box_matrix_max_error(length: float, samples: int) -> float:
    """`max |eigvalsh(spectral box) - box_spectrum|`: the discretization check.

    The counterpart of `finite_difference_box_spectrum`: this one asks whether the
    *matrix* reproduces the analytic ladder, and answers `1e-14`. Having both is
    the difference between "the spectrum is uniform" and "my grid says so".
    """
    matrix = spectral_box_matrix(length, samples)
    analytic = box_spectrum(length, samples)
    return float(np.abs(np.linalg.eigvalsh(matrix) - analytic).max())


def finite_difference_box_spectrum(length: float, samples: int) -> np.ndarray:
    """The naive central-difference box, kept because it is a trap worth showing.

    Eigenvalues are `sin(k h)/h`, not `k`, so the ladder bends at the edge of the
    band: at `L = 20`, `N = 64` the deviation from `2 pi m / L` reaches `6.85`,
    twice the spacing. A first pass at this module used this matrix and
    "discovered" a non-uniform spectrum. Comparing against
    `box_spectrum` catches it; comparing against nothing does not.
    """
    if samples < 4 or samples % 2:
        raise ValueError("samples must be even and at least 4")
    h = length / samples
    matrix = np.zeros((samples, samples))
    for index in range(samples):
        matrix[index, (index + 1) % samples] = 1.0
        matrix[index, (index - 1) % samples] = -1.0
    return np.sort(np.linalg.eigvalsh(-1j * matrix / (2.0 * h)))


def fit_box_length(heights: np.ndarray | list[float]) -> float:
    """The box that contains exactly `len(heights)` rungs by the last height.

    `N = gamma_N * L / 2 pi`, so `L = 2 pi N / gamma_N`. This is the *most
    generous* fit available: it matches the count at the top by construction, and
    the comparison below is what that fit does everywhere else.
    """
    values = np.sort(np.asarray(heights, dtype=float))
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("need at least two heights")
    if values[-1] <= 0:
        raise ValueError("heights must be positive")
    return float(2.0 * np.pi * len(values) / values[-1])


@dataclass(frozen=True)
class BoxCountRow:
    """Ladder count against zero count at one height."""

    height: float
    box_count: int
    zero_count: int

    @property
    def ratio(self) -> float:
        return self.box_count / self.zero_count if self.zero_count else float("nan")


@dataclass(frozen=True)
class BoxVerdict:
    """What a hard box does to the zero spectrum, measured."""

    length: float
    ladder_spacing: float
    box_r_ratio: float
    zero_r_ratio: float
    mean_miss: float
    max_miss: float
    mean_zero_spacing: float
    rows: list[BoxCountRow]

    @property
    def miss_in_mean_spacings(self) -> float:
        return self.mean_miss / self.mean_zero_spacing

    def summary(self) -> str:
        return (
            f"box L = {self.length:.4f} -> rungs every {self.ladder_spacing:.4f}, "
            f"r-ratio {self.box_r_ratio:.3f} (exactly 1 = picket fence) against "
            f"{self.zero_r_ratio:.3f} for the zeros; endpoint-rescaled ladder "
            f"misses by {self.mean_miss:.2f} on average = "
            f"{self.miss_in_mean_spacings:.1f} mean spacings"
        )


def box_versus_zeros(
    count: int = 100,
    heights: tuple[float, ...] = (50.0, 100.0, 150.0, 200.0),
) -> BoxVerdict:
    """Compare the best-fitting hard box to the real zeros.

    Three independent mismatches are returned: the `r`-ratio (uniformity), the
    counting function at intermediate heights (density), and the residual after
    the most generous affine rescaling (positions).
    """
    zeros = np.array(zeta_zero_ordinates(count))
    length = fit_box_length(zeros)
    ladder = box_positive_levels(length, count)

    rows = [
        BoxCountRow(
            height=h,
            box_count=box_count(h, length),
            zero_count=int(np.searchsorted(zeros, h, side="right")),
        )
        for h in heights
    ]

    rescaled = np.interp(ladder, [ladder[0], ladder[-1]], [zeros[0], zeros[-1]])
    miss = np.abs(rescaled - zeros)

    return BoxVerdict(
        length=length,
        ladder_spacing=float(2.0 * np.pi / length),
        box_r_ratio=float(mean_r_ratio(ladder, unfold=False)),
        zero_r_ratio=float(mean_r_ratio(zeros, unfold=False)),
        mean_miss=float(np.mean(miss)),
        max_miss=float(np.max(miss)),
        mean_zero_spacing=float(np.mean(np.diff(zeros))),
        rows=rows,
    )


# ============================================================
# 3. Reality is a condition, not a gift
# ============================================================

def prescribed_spectrum_operator(values: np.ndarray | list[float]) -> np.ndarray:
    """A self-adjoint operator whose spectrum is exactly `values`.

    Diagonal. This is the whole refutation of "a real spectrum would prove RH":
    an operator with any prescribed real spectrum exists by writing it down, so
    the existence of such an operator is empty. The hypothesis needs the
    spectrum of an *arithmetically defined* operator to be the zeros.
    """
    flat = np.asarray(values, dtype=float).ravel()
    if flat.size == 0:
        raise ValueError("need at least one value")
    return np.diag(flat)


def hermiticity_error(matrix: np.ndarray) -> float:
    """`max |M - M^dagger|`, zero for a self-adjoint operator."""
    matrix = np.asarray(matrix)
    return float(np.abs(matrix - matrix.conj().T).max())


def pt_matrix(radius: float, coupling: float, theta: float) -> np.ndarray:
    """A `PT`-symmetric two-by-two matrix with an exactly solvable threshold.

    `M = [[r e^{i theta}, s], [s, r e^{-i theta}]]` is invariant under
    `P = sigma_x` composed with complex conjugation. Its eigenvalues are
    `r cos theta +- sqrt(s^2 - r^2 sin^2 theta)`: real for
    `r |sin theta| <= s` and a conjugate pair beyond it.
    """
    if radius <= 0:
        raise ValueError("radius must be positive")
    if coupling < 0:
        raise ValueError("coupling must be non-negative")
    return np.array(
        [
            [radius * np.exp(1j * theta), coupling],
            [coupling, radius * np.exp(-1j * theta)],
        ]
    )


def is_pt_symmetric(matrix: np.ndarray, tolerance: float = 1e-12) -> bool:
    """`P M P = conj(M)` with `P = sigma_x`: the unbroken-`PT` setting."""
    matrix = np.asarray(matrix)
    if matrix.shape != (2, 2):
        raise ValueError("only the two-by-two model is checked here")
    exchange = np.array([[0.0, 1.0], [1.0, 0.0]])
    return bool(
        np.abs(exchange @ matrix.conj() @ exchange - matrix).max() < tolerance
    )


def pt_threshold(radius: float, coupling: float) -> float:
    """`arcsin(s/r)`: the `theta` at which the real spectrum breaks.

    `pi/6` at `s/r = 1/2`. Half-width of the unbroken phase, exactly.
    """
    if radius <= 0:
        raise ValueError("radius must be positive")
    ratio = coupling / radius
    if ratio >= 1.0:
        return float(np.pi / 2.0)
    return float(np.arcsin(ratio))


def pt_eigenvalues(radius: float, coupling: float, theta: float) -> np.ndarray:
    """Eigenvalues of `pt_matrix`, ascending by real part.

    Returned as complex so the transition is visible without a branch test.
    """
    return np.sort_complex(np.linalg.eigvals(pt_matrix(radius, coupling, theta)))


def pt_max_imaginary_part(radius: float, coupling: float, theta: float) -> float:
    """`sqrt(r^2 sin^2 theta - s^2)` when broken, else `0`."""
    discriminant = coupling**2 - radius**2 * np.sin(theta) ** 2
    return float(np.sqrt(-discriminant)) if discriminant < 0 else 0.0


@dataclass(frozen=True)
class PtRow:
    """The `PT` model at one `theta`."""

    theta: float
    unbroken: bool
    max_imaginary_part: float


def pt_scan(radius: float, coupling: float, thetas: list[float]) -> list[PtRow]:
    """Sweep `theta` through the threshold, for the figure and for the tests."""
    rows: list[PtRow] = []
    for theta in thetas:
        eigenvalues = pt_eigenvalues(radius, coupling, theta)
        rows.append(
            PtRow(
                theta=float(theta),
                unbroken=bool(np.all(np.abs(eigenvalues.imag) < 1e-12)),
                max_imaginary_part=float(np.abs(eigenvalues.imag).max()),
            )
        )
    return rows


# ============================================================
# 4. Imaginary time: what it does, and what it cannot see
# ============================================================

def real_time_weight(energy: float, time: float) -> complex:
    """`exp(-i E t)`: unit modulus for every `t`. No decay, ever."""
    return complex(np.exp(-1j * energy * time))


def imaginary_time_weight(energy: float, tau: float) -> float:
    """`exp(-E tau)`: exponential decay, faster for higher energy."""
    if tau < 0:
        raise ValueError("tau must be non-negative")
    return float(np.exp(-energy * tau))


@dataclass(frozen=True)
class DecayRow:
    """Mode weights under `exp(-H tau)`, normalised to the ground state."""

    tau: float
    weights: list[float]

    @property
    def ground_fraction(self) -> float:
        return self.weights[0] / float(np.sum(self.weights))


def decay_table(energies: np.ndarray | list[float], taus: list[float]) -> list[DecayRow]:
    """`exp(-E_n tau)` relative to the lowest level, for each `tau`.

    The lowest level dominates as `tau` grows: that is the QITE mechanism, and it
    is a property of *any* spectrum with a gap. It isolates one eigenvalue; it
    does not produce the spectrum.
    """
    values = np.sort(np.asarray(energies, dtype=float))
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("need at least two energies")
    rows: list[DecayRow] = []
    for tau in taus:
        raw = np.exp(-values * tau)
        rows.append(DecayRow(tau=tau, weights=list(raw / raw[0])))
    return rows


def recovered_gap(energies: np.ndarray | list[float], tau: float) -> float:
    """`-(1/tau) log(w_1/w_0)`: the gap read off from imaginary time.

    Exact when the first two levels are both present, which is why imaginary-time
    evolution is the standard way to *measure* a gap -- and why it is useless
    here: the gap is measured, not derived.
    """
    values = np.sort(np.asarray(energies, dtype=float))
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("need at least two energies")
    if tau <= 0:
        raise ValueError("tau must be positive")
    ratio = imaginary_time_weight(values[1], tau) / imaginary_time_weight(values[0], tau)
    return float(-np.log(ratio) / tau)


def partition_function(beta: float, ordinates: np.ndarray | list[float]) -> float:
    """`Z(beta) = sum_n exp(-beta E_n)` over the supplied energies.

    Converges for every `beta > 0` because the ordinates grow like
    `n log n`. The values are small at large `beta` -- the sum is dominated by
    `gamma_1 = 14.13` -- which is a statement about the density, not about the
    critical line.
    """
    if beta <= 0:
        raise ValueError("beta must be positive")
    values = np.asarray(ordinates, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("ordinates must be a non-empty one-dimensional array")
    return float(np.sum(np.exp(-beta * values)))


def partition_function_of_zeros(beta: float, zeros: np.ndarray | list[complex]) -> float:
    """`Z(beta)` from a list of complex zeros, using **only** their ordinates.

    The signature takes complex numbers precisely so that the omission is
    visible: the real part is discarded here, which is the blindness being
    demonstrated below rather than a convenience.
    """
    values = np.asarray(zeros, dtype=complex)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("zeros must be a non-empty one-dimensional array")
    return partition_function(beta, np.abs(values.imag))


def partition_function_from_zeros(beta: float, count: int = 100) -> float:
    """`Z(beta)` computed from the imaginary parts of the first `count` zeros."""
    if count < 1:
        raise ValueError("count must be at least 1")
    return partition_function_of_zeros(
        beta, [0.5 + 1j * g for g in zeta_zero_ordinates(count)]
    )


def thermal_blindness(beta: float, count: int = 100, shift: float = 0.1) -> dict[str, float]:
    """Demonstrate that `Z(beta)` cannot see `Re(s)`.

    Two *different* zero lists are constructed -- each zero at `1/2 + i gamma`,
    then each at `1/2 + shift + i gamma`, i.e. off the critical line -- and fed
    to the same thermal functional. The results are equal, and equal because the
    ordinates are what the functional consumes; `shift` cancels. This is an
    identity, not a near miss, and its being an identity is the finding: no
    imaginary-time observable can distinguish RH from its negation.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    ordinates = zeta_zero_ordinates(count)
    on_line = [0.5 + 1j * g for g in ordinates]
    off_line = [0.5 + shift + 1j * g for g in ordinates]
    left = partition_function_of_zeros(beta, on_line)
    right = partition_function_of_zeros(beta, off_line)
    return {
        "on_line": left,
        "off_line": right,
        "difference": abs(left - right),
        "real_part_shift": shift,
    }


def kms_correlator(tau: float, beta: float, omega: float) -> float:
    """Euclidean position correlator of a harmonic oscillator at inverse `beta`.

    `G(tau) = cosh(omega (tau - beta/2)) / (2 omega sinh(beta omega / 2))` on
    `0 <= tau <= beta`. Exactly symmetric about `beta/2`, which *is* the KMS
    condition: imaginary time is a circle of circumference `beta`.
    """
    if beta <= 0:
        raise ValueError("beta must be positive")
    if omega <= 0:
        raise ValueError("omega must be positive")
    if not 0.0 <= tau <= beta:
        raise ValueError("tau must lie in [0, beta]")
    return float(
        np.cosh(omega * (tau - beta / 2.0)) / (2.0 * omega * np.sinh(beta * omega / 2.0))
    )


def kms_asymmetry(beta: float, omega: float, samples: int = 401) -> float:
    """`max |G(tau) - G(beta - tau)|` over the imaginary-time circle.

    Identically zero; the measurement is that the floating-point value is at the
    level of rounding, which is how a symbolic identity behaves and how an
    approximate one does not.
    """
    if samples < 3:
        raise ValueError("samples must be at least 3")
    taus = np.linspace(0.0, beta, samples)
    return float(
        max(abs(kms_correlator(t, beta, omega) - kms_correlator(beta - t, beta, omega))
            for t in taus)
    )


def x_squared_thermal(beta: float, omega: float, terms: int = 20000) -> float:
    """`<x^2>` from the explicit Boltzmann sum, to cross-check `G(0)`.

    `sum_n (1 - e^{-beta omega}) e^{-beta omega n} (n + 1/2)/omega`, which is the
    same trace as the closed form and is the check that the closed form was not
    merely fitted to itself.
    """
    if beta <= 0 or omega <= 0:
        raise ValueError("beta and omega must be positive")
    if terms < 1:
        raise ValueError("terms must be at least 1")
    n = np.arange(terms)
    weight = np.exp(-beta * omega * n) * (1.0 - np.exp(-beta * omega))
    return float(np.sum(weight * (n + 0.5)) / omega)


def hawking_beta(mass_kg: float) -> float:
    """`beta = 8 pi G M / c^3`: the circumference of black-hole imaginary time.

    Equals `4 pi r_s / c` with `r_s = 2GM/c^2`, so the thermal circle has the
    circumference one expects from the horizon. This is the formula behind the
    "imaginary time is a donut" statement; it is a statement about gravity, not
    about the zeta function.
    """
    if mass_kg <= 0:
        raise ValueError("mass must be positive")
    return float(8.0 * np.pi * GRAVITATIONAL_CONSTANT * mass_kg / SPEED_OF_LIGHT**3)


def hawking_temperature(mass_kg: float) -> float:
    """`hbar / (k_B beta)`, i.e. `hbar c^3 / (8 pi G M k_B)`, in kelvin."""
    return float(REDUCED_PLANCK / (BOLTZMANN * hawking_beta(mass_kg)))


# ============================================================
# The prototype's own verdict
# ============================================================

@dataclass(frozen=True)
class PrototypeReport:
    """Everything the prototype establishes, in one object."""

    continuum_norm_at_1e6: float
    box: BoxVerdict
    pt_threshold: float
    pt_broken_magnitude: float
    thermal_difference: float
    kms_asymmetry: float
    hawking_temperature: float

    def verdict(self) -> str:
        return (
            "Prototype status: the operator exists and the critical line is its "
            "eigenfunction exponent; the four gaps are open. "
            f"(1) no eigenvalues: truncated norm reaches {self.continuum_norm_at_1e6:.3f} "
            "at width 1e6 and grows without bound; "
            f"(2) the box is a picket fence, r-ratio {self.box.box_r_ratio:.3f} "
            f"against {self.box.zero_r_ratio:.3f}, overcounting {self.box.rows[0].ratio:.2f}x "
            f"at T = {self.box.rows[0].height:.0f}; "
            f"(3) real spectrum is free, and the PT phase breaks at theta = "
            f"{self.pt_threshold:.4f} with |Im| = {self.pt_broken_magnitude:.4f} beyond it; "
            f"(4) imaginary time is blind to Re(s): the thermal difference is "
            f"{self.thermal_difference:.1e}. The Riemann hypothesis is NOT proved, "
            "and nothing in this prototype bears on it beyond these four screens."
        )


def prototype_report(count: int = 100) -> PrototypeReport:
    """Run the four screens and collect the numbers they produce."""
    radius, coupling = 1.0, 0.5
    return PrototypeReport(
        continuum_norm_at_1e6=truncated_norm_squared(1.0, 1.0e6),
        box=box_versus_zeros(count),
        pt_threshold=pt_threshold(radius, coupling),
        pt_broken_magnitude=pt_max_imaginary_part(radius, coupling, 0.55),
        thermal_difference=thermal_blindness(0.5, count)["difference"],
        kms_asymmetry=kms_asymmetry(2.0, 1.3),
        hawking_temperature=hawking_temperature(SOLAR_MASS),
    )
