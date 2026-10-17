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
"""Candidate operators for Hilbert-Polya, and what screening can and cannot see.

`hilbert_polya.py` built one operator and measured four gaps. This module asks the
next question: *can a candidate be screened at all?* It builds three new
candidates, runs each through the same tests, and reports a result that is
uncomfortable for the whole programme. **Nothing here proves or disproves the
Riemann hypothesis.**

The candidates
--------------
1. **Prime-length quantum graph** (new here). A star graph -- one vertex, `m`
   edges to Dirichlet dead ends -- with edge lengths `ell_j = (1/2) log p_j`. This
   is the *literal* realization of the Gutzwiller dictionary: the out-and-back
   path on edge `j` has length `log p_j`, and every closed path has length
   `sum_j n_j log p_j = log n`, which is exactly the spectrum of the primon gas.
   It is self-adjoint by construction (Kirchhoff at the vertex, Dirichlet at the
   ends), its spectrum solves one explicit secular equation
   `sum_j cot(k ell_j) = 0`, and the choice of lengths is the most favourable one
   available, so no failure below can be blamed on a handicapped construction.
2. **Fixed box** (from `hilbert_polya`) -- the naive regularization, for contrast.
3. **Primon gas** (`primon_gas.py`) -- one mode per prime, energies `log n`.
4. **The unitary twin** -- *not a candidate*: `U diag(gamma) U^dagger`. It exists
   to make a logical point, see finding C3.

Five findings, measured
-----------------------
**C1. The dictionary is satisfiable without `zeta`.** The prime-length graph
realizes the periodic-orbit dictionary exactly and its spectrum is a *jittered
picket fence*: Weyl-linear, `N(k)/k = 1.250` against `L/pi = 1.233`, spacings
`0.044 .. 0.858` in `k`. So "periodic orbits are the primes" does not imply
"the spectrum is the zeros". `prime_orbits.py` already said the dictionary
relocates RH; this shows the relocation is realizable by a concrete operator.

**C2. Spectral statistics are not a certificate, and this is the sharpest
result here.** The graph's unfolded spacings score `r = 0.641` -- versus `0.610`
for the zeros and `0.599` for GUE -- and against the Wigner surmise the graph is
*accepted more strongly than the zeros are*: KS statistic `0.0438` for the graph
against `0.0579` for the zeros. A five-edge graph with prime lengths, which
cannot be the zeros (its counting function is linear in `k`, not
`(T/2 pi) log T`), reproduces the universal statistics better than the object it
is supposed to explain. `statistics.py`, `quantum_chaos.py` and the DSH criterion
S2 all rest on this statistic; `docs/central_hypothesis.md` already warned that
the formulation must be "stronger than the model has GUE statistics". That
warning is now demonstrated rather than asserted.

**C3. Every operator with the zeros as spectrum is the same operator.** By the
spectral theorem a self-adjoint operator with simple spectrum `{gamma_n}` is
unitarily equivalent to `diag(gamma_n)`. The twin passes *every* numerical test
exactly -- `max |eig - gamma| = 2e-13`, `r = 0.610`, right density, right thermal
trace -- and proves nothing, because its definition *is* the zeros. Consequently
the only decisive criterion is the one that is not numerical: whether the
definition mentions `zeta` or the zeros. Any construction whose spectrum is
defined through `zeta` -- a Mellin-Barnes integral of it, for instance -- is in
this class until shown otherwise.

**C4. The density requirement is real but unusable as a screen.** The zeros'
density `dN/dT = (1/2 pi) log(T/2 pi) + O(1)` is unbounded, and no Weyl power law
`N = C T^alpha` has an unbounded *logarithmic* density: `alpha = 1` is constant,
`alpha > 1` is a power. So asymptotically the density does reject every fixed
finite-dimensional regularization. But the effect is invisible where the numbers
live: over the first 100 zeros a single power law `T^1.436` reproduces the
counting function to **1.33 levels out of 100**. A density-based rejection at
`T <= 236` is therefore not evidence of anything.

**C5. Only criterion 1 survives.** `screening_table()` scores all four candidates
on five criteria. The box passes independence and self-adjointness and fails the
rest; the graph passes independence, self-adjointness *and* statistics and still
fails; the twin passes everything except independence. The pass/fail pattern is
the finding: **numerical agreement is cheap, and the one criterion that decides a
candidate is not numerical at all.**
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .hilbert_polya import box_versus_zeros
from .prime_certificate import sieve_slice
from .prime_orbits import zeta_zero_ordinates
from .spectral_density import riemann_von_mangoldt_count
from .statistics import ks_test_against, level_spacings, mean_r_ratio


#: The periodic-orbit dictionary, made concrete.
DICTIONARY_NOTE = (
    "A star graph with edges of length (1/2) log p_j realizes the Gutzwiller "
    "dictionary literally: the round trip on edge j has length log p_j, and every "
    "closed path has length sum_j n_j log p_j = log n, which is the primon gas "
    "spectrum. The operator is self-adjoint by construction. Its spectrum is "
    "nevertheless a jittered lattice, N(k)/k = 1.250 against L/pi = 1.233. The "
    "dictionary does not determine the spectrum."
)

#: Why a statistical match means almost nothing.
STATISTICS_NOTE = (
    "The prime-length graph scores r = 0.641 against 0.610 for the zeros and "
    "0.599 for GUE, and its KS distance to the Wigner surmise (0.0438) is SMALLER "
    "than the zeros' own (0.0579). An object that provably is not the zeros fits "
    "the universal statistics better than the zeros do. Statistics cannot certify "
    "a candidate; at most they can eliminate one that has no repulsion at all."
)

#: The spectral theorem, as a screening criterion.
TWIN_NOTE = (
    "By the spectral theorem, any self-adjoint operator with simple spectrum "
    "{gamma_n} is unitarily equivalent to diag(gamma_n). So 'find an operator "
    "whose eigenvalues are the zeros' has trivial solutions and passes every "
    "numerical test -- the twin below passes all of them to 1e-13 and proves "
    "nothing, because its definition is the zeros. The only non-trivial question "
    "is whether the definition mentions zeta."
)

#: The density requirement and its uselessness at accessible heights.
DENSITY_NOTE = (
    "dN/dT = (1/2 pi) log(T/2 pi) is unbounded, so no Weyl power law N = C T^alpha "
    "can match it asymptotically: alpha = 1 gives a bounded density and alpha > 1 "
    "a power. But at the heights where zeros are known a single power law T^1.436 "
    "reproduces N(T) to 1.33 levels out of 100, so the asymptotic obstruction is "
    "not observable. It is a requirement on a future construction, not a test of "
    "a present one."
)

#: The conclusion of the table.
SCREENING_NOTE = (
    "Across the four candidates no numerical criterion separates the useful from "
    "the empty. The twin passes density, positions, statistics and thermality "
    "exactly; the prime graph passes statistics better than the zeros do. The "
    "deciding criterion is the independence of the definition, which is read off "
    "the source and cannot be measured."
)


# ============================================================
# 1. Counting functions and the density scale
# ============================================================

def zero_counting(height: float, count: int = 100) -> int:
    """`N(T)`, exactly, from the first `count` computed ordinates."""
    if height <= 0:
        raise ValueError("height must be positive")
    zeros = np.array(zeta_zero_ordinates(count))
    return int(np.searchsorted(zeros, height, side="right"))


@dataclass(frozen=True)
class DensityRow:
    """Zeros per unit height in one band."""

    lower: float
    upper: float
    count: int

    @property
    def per_unit_height(self) -> float:
        return self.count / (self.upper - self.lower)


def density_table(
    bands: tuple[tuple[float, float], ...] = ((14.0, 50.0), (50.0, 100.0), (100.0, 150.0), (150.0, 236.5)),
    count: int = 100,
) -> list[DensityRow]:
    """`dN/dT` measured in bands: it rises, which is what a logarithm looks like."""
    zeros = np.array(zeta_zero_ordinates(count))
    rows: list[DensityRow] = []
    for lower, upper in bands:
        if not 0.0 < lower < upper:
            raise ValueError("each band needs 0 < lower < upper")
        rows.append(
            DensityRow(
                lower=lower,
                upper=upper,
                count=int(np.sum((zeros >= lower) & (zeros < upper))),
            )
        )
    return rows


def local_exponent(height: float, count: int = 100) -> float:
    """`log N(T) / log T`: drifts toward 1, which no fixed power law does."""
    if height <= 1.0:
        raise ValueError("height must exceed 1")
    n = zero_counting(height, count)
    if n < 2:
        raise ValueError("too few zeros below this height to fit an exponent")
    return float(np.log(n) / np.log(height))


@dataclass(frozen=True)
class PowerLawFit:
    """Best single `C T^alpha` through the zero counting function."""

    coefficient: float
    exponent: float
    max_error_levels: float
    zero_count: int
    heights: list[float] = field(default_factory=list)
    predicted: list[float] = field(default_factory=list)
    actual: list[float] = field(default_factory=list)

    @property
    def max_error_at_heights(self) -> float:
        return float(
            max(
                (abs(predicted - actual) for predicted, actual in zip(self.predicted, self.actual)),
                default=0.0,
            )
        )

    def summary(self) -> str:
        return (
            f"best power law N = {self.coefficient:.5f} T^{self.exponent:.4f}: "
            f"worst residual {self.max_error_levels:.2f} levels over the first "
            f"{self.zero_count} zeros (up to {self.max_error_at_heights:.2f} at the "
            "sampled heights). A pure power law fits at accessible heights, so "
            "density cannot reject a candidate here"
        )


def power_law_fit(count: int = 100, heights: tuple[float, ...] = (20.0, 50.0, 100.0, 150.0, 200.0)) -> PowerLawFit:
    """Fit `C T^alpha` to `N(gamma_n) = n`, then evaluate it off the zeros.

    Least-squares in `alpha` with the optimal `C` per `alpha`: the point is that a
    *power law* fits, which is exactly what `DENSITY_NOTE` warns about.
    """
    if count < 10:
        raise ValueError("need at least 10 zeros to fit")
    zeros = np.array(zeta_zero_ordinates(count))
    target = np.arange(1, count + 1, dtype=float)

    best: tuple[float, float, float] | None = None
    for alpha in np.linspace(0.5, 2.5, 2001):
        coefficient = float(np.sum(target * zeros**alpha) / np.sum(zeros ** (2.0 * alpha)))
        error = float(np.abs(coefficient * zeros**alpha - target).max())
        if best is None or error < best[2]:
            best = (coefficient, float(alpha), error)
    assert best is not None
    coefficient, alpha, error = best

    return PowerLawFit(
        coefficient=coefficient,
        exponent=alpha,
        max_error_levels=error,
        zero_count=count,
        heights=list(heights),
        predicted=[float(coefficient * h**alpha) for h in heights],
        actual=[zero_counting(h, count) for h in heights],
    )


def von_mangoldt_table(heights: tuple[float, ...] = (20.0, 50.0, 100.0, 150.0, 200.0), count: int = 100) -> list[tuple[float, int, float]]:
    """`(T, N(T), Riemann-von Mangoldt)` -- the smooth density, which is not a power law."""
    return [
        (h, zero_counting(h, count), float(riemann_von_mangoldt_count(np.array([h]))[0]))
        for h in heights
    ]


# ============================================================
# 2. Candidate: the prime-length quantum graph
# ============================================================

def star_edge_lengths(edge_count: int = 5, dictionary_exact: bool = True) -> np.ndarray:
    """Edge lengths of the star graph: `(1/2) log p_j`, or `log p_j` unscaled.

    `dictionary_exact=True` makes the round trip on edge `j` exactly `log p_j`, so
    every closed path has length `log n`. The other option halves nothing and
    leaves the dictionary off by a factor two -- kept only so the difference can
    be measured and so nobody has to take the favourable choice on trust.
    """
    if edge_count < 2:
        raise ValueError("need at least two edges")
    if edge_count > 500:
        raise ValueError("too many edges for the sieve")
    primes = np.array(
        sieve_slice(max(200, edge_count * 40))[:edge_count], dtype=float
    )
    if len(primes) < edge_count:
        raise ValueError("sieve did not produce enough primes")
    logs = np.log(primes)
    return 0.5 * logs if dictionary_exact else logs


def star_secular(wavenumber: float, lengths: np.ndarray) -> float:
    """`sum_j cot(k ell_j)`: the secular function of the star graph.

    Kirchhoff (flux conservation) at the central vertex, Dirichlet at the dead
    ends. Roots of this function are the spectrum in `k`; the eigenvalues of the
    Laplacian are `k^2`, and `k` is what plays the role of the ordinate here.
    """
    return float(np.sum(1.0 / np.tan(wavenumber * np.asarray(lengths, dtype=float))))


def star_poles(lengths: np.ndarray, k_max: float) -> np.ndarray:
    """Poles `n pi / ell_j` of the secular function inside `(0, k_max]`."""
    values = np.asarray(lengths, dtype=float)
    if np.any(values <= 0):
        raise ValueError("lengths must be positive")
    poles: list[float] = []
    for ell in values:
        n = np.arange(1, int(k_max * ell / np.pi) + 2)
        poles.extend((n * np.pi / ell).tolist())
    return np.unique(np.array(poles))


def star_spectrum(lengths: np.ndarray, k_max: float, tolerance: float = 1e-13) -> np.ndarray:
    """Levels in `k` from the secular equation, by bisection between its poles.

    Between consecutive poles the secular function is strictly decreasing (each
    `cot` is), from `+inf` to `-inf`, so there is exactly one root per interval
    and bisection cannot miss one. Roots closer than `1e-6` are merged, which is
    bisection debris next to a pole rather than a level.
    """
    if k_max <= 0:
        raise ValueError("k_max must be positive")
    edges = np.concatenate(([0.0], star_poles(lengths, k_max), [k_max]))
    roots: list[float] = []
    for lower, upper in zip(edges[:-1], edges[1:]):
        lo, hi = lower + 1e-13, upper - 1e-13
        if hi <= lo:
            continue
        f_lo, f_hi = star_secular(lo, lengths), star_secular(hi, lengths)
        if not (np.isfinite(f_lo) and np.isfinite(f_hi)) or f_lo * f_hi > 0:
            continue
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            f_mid = star_secular(mid, lengths)
            if f_lo * f_mid <= 0:
                hi = mid
            else:
                lo, f_lo = mid, f_mid
            if hi - lo < tolerance:
                break
        roots.append(0.5 * (lo + hi))

    ordered = np.sort(np.array(roots))
    keep = [ordered[0]]
    for value in ordered[1:]:
        if value - keep[-1] > 1e-6:
            keep.append(value)
    return np.array(keep)


@dataclass(frozen=True)
class OrbitRow:
    """One closed path: its geometric length against the `log n` the dictionary asks for."""

    n: int
    geometric_length: float
    log_n: float

    @property
    def matches(self) -> bool:
        return abs(self.geometric_length - self.log_n) < 1e-12


def closed_orbit_lengths(edge_count: int = 5, max_integer: int = 30) -> list[OrbitRow]:
    """Closed paths of the star graph, with their lengths computed from the geometry.

    A closed path is a sequence of round trips, so its length is
    `sum_j 2 n_j ell_j`. With `ell_j = (1/2) log p_j` that *should* be `log n` for
    `n = prod p_j^{n_j}`, and the length here is computed from the `ell_j` and the
    exponents rather than written down as a logarithm -- so the agreement in
    `OrbitRow.matches` is the dictionary being verified, not restated.
    """
    lengths = star_edge_lengths(edge_count, dictionary_exact=True)
    primes = [int(round(np.exp(2.0 * ell))) for ell in lengths]

    rows: list[OrbitRow] = []
    for n in range(2, max_integer + 1):
        rest = n
        exponents: list[int] = []
        for p in primes:
            power = 0
            while rest % p == 0:
                rest //= p
                power += 1
            exponents.append(power)
        if rest != 1:
            # n needs a prime this graph does not carry, so it has no such path
            continue
        geometric = float(sum(2 * power * ell for power, ell in zip(exponents, lengths)))
        rows.append(OrbitRow(n=n, geometric_length=geometric, log_n=float(np.log(n))))
    return rows


def primon_counting(height: float) -> int:
    """`#{n : log n <= T} = floor(e^T)`: the primon gas's counting function.

    Exponential, not linear, let alone `T log T`. The three candidates bracket the
    zeros from below (box, graph: linear in `k`) and above (gas: `e^T`).
    """
    if height <= 0:
        raise ValueError("height must be positive")
    if height > 40.0:
        raise ValueError("keep e^T representable: height <= 40")
    return int(np.floor(np.exp(height)))


@dataclass(frozen=True)
class GraphReport:
    """The prime-length graph, measured against the zeros."""

    edge_lengths: np.ndarray
    total_length: float
    k_max: float
    level_count: int
    weyl_slope: float
    predicted_slope: float
    r_ratio: float
    ks_statistic: float
    ks_p_value: float
    spacing_min: float
    spacing_max: float
    zero_r_ratio: float
    zero_ks_statistic: float

    @property
    def counting_is_linear(self) -> bool:
        return abs(self.weyl_slope - self.predicted_slope) / self.predicted_slope < 0.05

    def summary(self) -> str:
        return (
            f"prime-length star graph: {self.level_count} levels below k = {self.k_max:.0f}, "
            f"N/k = {self.weyl_slope:.3f} against L/pi = {self.predicted_slope:.3f} "
            f"(linear, so the density is wrong); r = {self.r_ratio:.3f} against "
            f"{self.zero_r_ratio:.3f} for the zeros; KS to Wigner {self.ks_statistic:.4f} "
            f"against the zeros' {self.zero_ks_statistic:.4f} -- the graph fits the "
            "universal statistics BETTER than the zeros do"
        )


def graph_report(edge_count: int = 5, k_max: float = 120.0, zero_count: int = 100) -> GraphReport:
    """Build the prime-length graph and measure it two ways."""
    lengths = star_edge_lengths(edge_count, dictionary_exact=True)
    levels = star_spectrum(lengths, k_max)
    spacings = level_spacings(levels, unfold=True)
    ks = ks_test_against(levels, reference="gue", unfold=True)
    zeros = np.array(zeta_zero_ordinates(zero_count))
    zero_ks = ks_test_against(zeros, reference="gue", unfold=True)

    return GraphReport(
        edge_lengths=lengths,
        total_length=float(lengths.sum()),
        k_max=k_max,
        level_count=len(levels),
        weyl_slope=len(levels) / k_max,
        predicted_slope=float(lengths.sum() / np.pi),
        r_ratio=float(mean_r_ratio(levels, unfold=False)),
        ks_statistic=float(ks["ks_stat"]),
        ks_p_value=float(ks["p_value"]),
        spacing_min=float(spacings.min()),
        spacing_max=float(spacings.max()),
        zero_r_ratio=float(mean_r_ratio(zeros, unfold=False)),
        zero_ks_statistic=float(zero_ks["ks_stat"]),
    )


# ============================================================
# 3. The twin: everything passes, nothing is proved
# ============================================================

def unitary_twin(values: np.ndarray | list[float], seed: int = 0) -> np.ndarray:
    """`U diag(values) U^dagger` for a random unitary `U`: spectrum exactly `values`.

    A *non-diagonal* self-adjoint operator with the prescribed spectrum. Its only
    purpose is to show that the numerical agreement a candidate is judged by is
    inherited from the prescription: nothing about the matrix encodes anything
    except the list it was built from.
    """
    flat = np.asarray(values, dtype=float).ravel()
    if flat.size == 0:
        raise ValueError("need at least one value")
    rng = np.random.default_rng(seed)
    size = flat.size
    raw = rng.standard_normal((size, size)) + 1j * rng.standard_normal((size, size))
    unitary, _ = np.linalg.qr(raw)
    return unitary @ np.diag(flat) @ unitary.conj().T


@dataclass(frozen=True)
class TwinReport:
    """Every screen the twin passes, and the deviation achieved."""

    size: int
    hermiticity_error: float
    max_eigenvalue_error: float
    r_ratio: float
    ks_statistic: float
    trace_error: float

    def summary(self) -> str:
        return (
            f"unitary twin ({self.size}x{self.size}): hermiticity {self.hermiticity_error:.1e}, "
            f"max |eig - gamma| {self.max_eigenvalue_error:.1e}, trace {self.trace_error:.1e}, "
            f"r = {self.r_ratio:.3f}, KS to Wigner {self.ks_statistic:.4f}. Every numerical "
            "screen passes exactly, and the construction is a restatement."
        )


def twin_report(count: int = 100, seed: int = 7) -> TwinReport:
    """Build the twin from the zeros and run the screens on it."""
    zeros = np.array(zeta_zero_ordinates(count))
    matrix = unitary_twin(zeros, seed)
    eigenvalues = np.sort(np.linalg.eigvalsh(matrix))
    ks = ks_test_against(eigenvalues, reference="gue", unfold=True)
    return TwinReport(
        size=count,
        hermiticity_error=float(np.abs(matrix - matrix.conj().T).max()),
        max_eigenvalue_error=float(np.abs(eigenvalues - zeros).max()),
        r_ratio=float(mean_r_ratio(eigenvalues, unfold=False)),
        ks_statistic=float(ks["ks_stat"]),
        trace_error=float(abs(np.trace(matrix).real - zeros.sum())),
    )


# ============================================================
# 4. The screening table
# ============================================================

@dataclass(frozen=True)
class ScreenRow:
    """One candidate against the five criteria.

    The criteria are ordered as they must be applied, and the first one is not
    numerical: a candidate whose *definition* mentions the zeros cannot be
    screened by any number computed from those zeros.
    """

    candidate: str
    independent_definition: bool
    density_class: bool
    statistics: bool | None
    reality_is_a_theorem: bool
    identification_proved: bool
    note: str

    @property
    def passes_every_numerical_test(self) -> bool:
        return bool(
            self.density_class
            and (self.statistics is not False)
            and self.reality_is_a_theorem
            and self.identification_proved
        )

    @property
    def is_a_candidate(self) -> bool:
        return self.independent_definition and self.identification_proved


def screening_table(zero_count: int = 100) -> list[ScreenRow]:
    """Score the four candidates. The pattern is the result."""
    box = box_versus_zeros(zero_count)
    graph = graph_report(zero_count=zero_count)
    twin = twin_report(zero_count)

    return [
        ScreenRow(
            candidate="fixed box (log x, length L)",
            independent_definition=True,
            density_class=False,
            statistics=False,
            reality_is_a_theorem=True,
            identification_proved=False,
            note=f"r = {box.box_r_ratio:.3f} (picket fence); "
            f"overcounts {box.rows[0].ratio:.2f}x at T = {box.rows[0].height:.0f}",
        ),
        ScreenRow(
            candidate="prime-length quantum graph",
            independent_definition=True,
            density_class=False,
            statistics=True,
            reality_is_a_theorem=True,
            identification_proved=False,
            note=f"dictionary exact, r = {graph.r_ratio:.3f}, KS {graph.ks_statistic:.4f} "
            f"(the zeros' own is {graph.zero_ks_statistic:.4f}), but "
            f"N/k = {graph.weyl_slope:.3f} is linear",
        ),
        ScreenRow(
            candidate="primon gas (energies log n)",
            independent_definition=True,
            density_class=False,
            statistics=None,
            reality_is_a_theorem=True,
            identification_proved=False,
            note="counting is e^T, the opposite failure: far too many levels",
        ),
        ScreenRow(
            candidate="unitary twin of diag(gamma)",
            independent_definition=False,
            density_class=True,
            statistics=True,
            reality_is_a_theorem=True,
            identification_proved=True,
            note=f"everything exact (max |eig - gamma| = {twin.max_eigenvalue_error:.0e}) "
            "because the definition is the zeros",
        ),
    ]


def survivors(rows: list[ScreenRow]) -> list[ScreenRow]:
    """Candidates that pass independence *and* identification -- currently none."""
    return [row for row in rows if row.is_a_candidate]
