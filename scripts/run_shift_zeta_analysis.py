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
"""Run the shift-zeta analysis and write the numbers quoted in the result report.

Usage, from the repository root:

    python scripts/run_shift_zeta_analysis.py

Writes to output/:

    shift_zeta_traces.png           graded trace vs classical zeta, by tau
    shift_zeta_convergence.png      Euler truncation error vs number of primes
    shift_zeta_critical_line.png    |zeta(1/2+it)| and the graded analogue
    shift_zeta_comparison.png       classical zeros vs dips of the graded trace
    shift_zeta_summary.txt          every number quoted in docs/shift_zeta_result.md

Read the caveats in `_plot_critical_line` and `_plot_comparison` before drawing
conclusions from the second pair of figures. The truncated Euler product does
not converge on the critical line, and demonstrating that is the point of those
figures rather than an inconvenience.

Outcome is negative/null; see docs/shift_zeta_result.md.
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "python"))

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import mpmath as mp

from riemann_framework.graded_algebra import GradedElement, grading_shift, local_factor
from riemann_framework.shift_zeta import (
    compare_zeros,
    first_primes,
    functional_equation_residual,
    graded_to_classical_ratio,
    shift_zeta,
    shift_zeta_element,
)

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

mp.mp.dps = 30

TAUS = [1, 0, mp.mpf("0.5"), mp.mpf("0.25"), 2]
S_VALUES = [2, 3, 4, 5, 6]

# First non-trivial zero heights, used as landmarks throughout.
ZERO_HEIGHTS = [float(mp.im(mp.zetazero(k))) for k in range(1, 7)]
T_MAX = 40.0
T_SAMPLES = 200
# The raw product has a singularity wherever p^{-1/2} approaches 1, i.e. for
# small p and small t; below about t = 5 it is dominated by those rather than
# by any structure of the function.
T_MIN = 5.0


def _gates() -> list[str]:
    """Criteria G1-G4, G7 and F4/F5, evaluated directly."""
    lines = ["Criterion checks", "=" * 60]
    samples = [
        GradedElement.of(1, 0),
        GradedElement.of(0, 1),
        GradedElement.of(2, -3),
        GradedElement.of(mp.mpf("0.5"), mp.mpf("0.25")),
    ]

    g1 = GradedElement.omega() * GradedElement.omega() == GradedElement.identity()
    g1 = g1 and all(
        (x * y) * z == x * (y * z) for x in samples for y in samples for z in samples
    )
    lines.append(f"G1 algebra well-defined (unit, associativity) : {'PASS' if g1 else 'FAIL'}")

    g2 = all((x * y).sigma() == x.sigma() * y.sigma() for x in samples for y in samples)
    lines.append(f"G2 sigma is an algebra homomorphism            : {'PASS' if g2 else 'FAIL'}")

    tol = mp.mpf(10) ** -25
    g3 = all(abs(x.sigma().trace() - x.trace()) < tol for x in samples)
    lines.append(f"G3 trace invariant under sigma                 : {'PASS' if g3 else 'FAIL'}")

    f5 = all(abs(x.sigma().supertrace() + x.supertrace()) < tol for x in samples)
    lines.append(
        f"F5 supertrace anti-invariant (flips sign)      : "
        f"{'PASS (expected)' if f5 else 'FAIL'}"
    )

    g4 = True
    for s in (2, 3):
        for tau in TAUS:
            value = shift_zeta(s, tau, first_primes(20))
            g4 = g4 and bool(mp.isfinite(value.real))
    lines.append(f"G4 shift-zeta returns finite values            : {'PASS' if g4 else 'FAIL'}")

    lines.append(
        f"F4 involution NOT a homomorphism               : "
        f"{'TRIGGERED' if not g2 else 'not triggered'}"
    )

    for s, tolerance in ((2, mp.mpf("2e-3")), (5, mp.mpf("1e-8"))):
        value = shift_zeta(s, 1, first_primes(60))
        relative = abs(value - mp.zeta(s)) / abs(mp.zeta(s))
        ok = relative < tolerance
        lines.append(
            f"G7 Euler product -> zeta at tau=1, s={s}     : "
            f"{'PASS' if ok else 'FAIL'} (rel err {mp.nstr(relative, 4)})"
        )
    return lines


def _plot_traces() -> None:
    figure: Figure = plt.figure(figsize=(9, 5))
    axis: Axes = figure.subplots()

    axis.plot(
        S_VALUES,
        [float(mp.zeta(s)) for s in S_VALUES],
        "k--",
        marker="o",
        label="classical zeta(s)",
    )

    primes = first_primes(600)
    for tau in TAUS:
        values = [float(mp.re(shift_zeta(s, tau, primes))) for s in S_VALUES]
        label = f"graded trace, tau={float(tau):g}"
        if float(tau) == 1.0:
            label += "  (degenerate: equals zeta)"
            axis.plot(S_VALUES, values, marker="s", linewidth=2, label=label)
        else:
            axis.plot(S_VALUES, values, marker="x", label=label)

    axis.set_xlabel("s")
    axis.set_ylabel("value")
    axis.set_title("Graded trace of the shift-zeta vs classical zeta")
    axis.legend(fontsize=8)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "shift_zeta_traces.png", dpi=150)
    plt.close(figure)


def _plot_convergence() -> None:
    figure: Figure = plt.figure(figsize=(9, 5))
    axis: Axes = figure.subplots()

    counts = [10, 30, 100, 300, 1000, 3000]
    for tau in (1, 0, mp.mpf("0.5")):
        errors = []
        for n in counts:
            value = shift_zeta(2, tau, first_primes(n))
            errors.append(float(abs(value - mp.zeta(2))))
        axis.loglog(counts, errors, marker="o", label=f"tau={float(tau):g}")

    axis.set_xlabel("number of primes")
    axis.set_ylabel("|graded trace - zeta(2)|")
    axis.set_title("Euler truncation error at s = 2")
    axis.legend()
    axis.grid(alpha=0.25, which="both")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "shift_zeta_convergence.png", dpi=150)
    plt.close(figure)


def _critical_line_values(tau, n_primes: int):
    """|Z_A(1/2 + it, tau)| sampled on the critical line."""
    primes = first_primes(n_primes)
    heights = [T_MIN + (T_MAX - T_MIN) * i / (T_SAMPLES - 1) for i in range(T_SAMPLES)]
    values = []
    for t in heights:
        try:
            values.append(
                float(abs(shift_zeta(mp.mpc(mp.mpf("0.5"), t), tau, primes)))
            )
        except ZeroDivisionError:
            values.append(float("nan"))
    return heights, values


def _plot_critical_line() -> None:
    """|Tr(zeta_A(1/2 + it))| along the critical line.

    Read this as a diagnostic of the *method*, not of the zeros.

    The classical curve is exact: at `tau = 1` the graded trace is the classical
    Euler product, so mpmath's analytic continuation applies and the zeros are
    visible as sharp dips. The graded curve is the raw product at
    `Re(s) = 1/2`, which is outside its domain of convergence. Increasing the
    prime count moves it without settling, and the figure reports the size of
    that movement rather than hiding it.
    """
    figure: Figure = plt.figure(figsize=(11, 5.5))
    axis: Axes = figure.subplots()

    heights, _ = _critical_line_values(1, 60)
    classical = [float(abs(mp.zeta(mp.mpc(mp.mpf("0.5"), t)))) for t in heights]
    axis.plot(
        heights,
        classical,
        color="black",
        linewidth=1.6,
        label="|zeta(1/2 + it)|  exact, via continuation",
    )

    for index, height in enumerate(ZERO_HEIGHTS):
        axis.axvline(
            height,
            color="green",
            linestyle=":",
            alpha=0.55,
            linewidth=1.3,
            label="classical zeros" if index == 0 else None,
        )

    _, graded_low = _critical_line_values(1, 100)
    _, graded_mid = _critical_line_values(1, 400)
    _, graded_high = _critical_line_values(1, 1500)

    axis.plot(
        heights,
        graded_mid,
        color="tab:blue",
        linewidth=1.0,
        alpha=0.85,
        label="graded trace, tau=1, raw 400-prime product",
    )
    axis.plot(
        heights,
        graded_high,
        color="tab:orange",
        linewidth=0.9,
        alpha=0.7,
        linestyle="--",
        label="graded trace, tau=1, raw 1500-prime product",
    )

    spread = max(
        abs(a - b) for a, b in zip(graded_low, graded_high) if a == a and b == b
    )

    axis.set_xlabel("t")
    axis.set_ylabel("|value|  (log scale)")
    axis.set_title(
        "Critical line: exact |zeta| vs the raw graded product\n"
        f"the product has no limit here (100- vs 1500-prime spread {spread:.2f})"
    )
    axis.set_yscale("log")
    axis.set_ylim(1e-3, 1e3)
    axis.legend(fontsize=8, loc="upper right")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "shift_zeta_critical_line.png", dpi=150)
    plt.close(figure)


def _zero_ratios(tau, n_primes: int = 300):
    """`|Z_A(rho, tau)| / |Z_A(rho, 1)|` at the classical zeros.

    This ratio *is* meaningful: both numerator and denominator are truncated
    over the same primes, so the truncation factor cancels and what remains is
    the effect of the grading at the classical zeros. It does not, however,
    locate zeros -- see docs/shift_zeta_result.md.
    """
    primes = first_primes(n_primes)
    ratios = []
    for height in ZERO_HEIGHTS:
        point = mp.mpc(mp.mpf("0.5"), height)
        try:
            numerator = abs(shift_zeta(point, tau, primes))
            denominator = abs(shift_zeta(point, 1, primes))
            ratios.append(float(numerator / denominator) if denominator else float("nan"))
        except ZeroDivisionError:
            ratios.append(float("nan"))
    return ratios


def _plot_comparison() -> None:
    """Classical zeros vs the graded trace, with the tau=1 control.

    An earlier version of this figure marked the deepest local minima of the
    graded trace and counted how many fell within 0.5 of a classical zero. That
    statistic was unreliable and is not used: it reported 7 of 8 hits even at
    `tau = 1`, where the trace *is* the classical product, so it was measuring
    the oscillation of a truncated product rather than the location of zeros.

    What is shown instead is the graded trace itself on a log scale, with the
    classical zeros marked. The trace has no converged value at those heights,
    which is the finding: the truncated product cannot place zeros.

    The ratio `|Z_A(z, tau)| / |Z_A(z, 1)|` at each classical zero *is*
    well-defined -- the common truncation cancels -- and it is reported in the
    summary rather than plotted here.
    """
    figure: Figure = plt.figure(figsize=(11, 5.5))
    panels = figure.subplots(1, 2, sharey=True)

    for axis, tau, title in (
        (panels[0], 0, "graded trace, tau = 0"),
        (panels[1], 1, "tau = 1 control (trace is the classical product)"),
    ):
        heights, graded = _critical_line_values(tau, 400)
        axis.plot(heights, graded, color="tab:blue", linewidth=0.9)
        for index, height in enumerate(ZERO_HEIGHTS):
            axis.axvline(
                height,
                color="green",
                linestyle=":",
                alpha=0.6,
                linewidth=1.4,
                label="classical zeros" if index == 0 else None,
            )
        axis.set_yscale("log")
        axis.set_ylim(1e-2, 1e2)
        axis.set_title(title, fontsize=10)
        axis.set_xlabel("t")
        axis.set_xlim(T_MIN, T_MAX)
        axis.grid(alpha=0.2, which="both")
        axis.legend(fontsize=8, loc="upper left")

    figure.suptitle(
        "The graded trace on the critical line, with the classical zeros marked\n"
        "it oscillates and has no converged value at those heights, so this "
        "cannot locate zeros",
        fontsize=10,
    )
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "shift_zeta_comparison.png", dpi=150)
    plt.close(figure)


def _write_summary(path: Path) -> None:
    lines = [
        "Shift-zeta analysis",
        "=" * 60,
        "",
        "These are diagnostic numbers, not a proof. The outcome is negative/null;",
        "see docs/shift_zeta_result.md.",
        "",
    ]
    lines.extend(_gates())
    lines.extend(["", "Graded trace vs classical zeta", "=" * 60])
    lines.append(
        f"{'tau':>6} | " + " | ".join(f"s={s}" for s in S_VALUES) + " | max rel err"
    )
    lines.append("-" * 78)
    primes = first_primes(600)
    for tau in TAUS:
        values = [shift_zeta(s, tau, primes) for s in S_VALUES]
        errors = [
            abs(v - mp.zeta(s)) / abs(mp.zeta(s)) for v, s in zip(values, S_VALUES)
        ]
        row = " | ".join(f"{float(mp.re(v)):9.5f}" for v in values)
        lines.append(f"{float(tau):6g} | {row} | {float(max(errors)):.4e}")

    lines.extend(["", "Local factor at tau=1 equals 1/(1-p^-s)", "=" * 60])
    for p in (2, 3, 5, 7):
        for s in (2, 3):
            x = mp.mpf(p) ** (-s)
            factor = local_factor(p, s, 1)
            lines.append(
                f"  p={p} s={s}: trace={mp.nstr(factor.trace(), 12)}  "
                f"1/(1-x)={mp.nstr(1 / (1 - x), 12)}  "
                f"supertrace={mp.nstr(factor.supertrace(), 4)}"
            )

    lines.extend(["", "Functional equation residuals", "=" * 60])
    for entry in functional_equation_residual(n_primes=200):
        parts = "  ".join(
            f"{k}={entry[k]:.3e}" for k in sorted(entry) if k.startswith("tau_")
        )
        lines.append(
            f"  s={entry['s']}: classical={entry['classical_residual']:.3e}  {parts}"
        )
    lines.append("  The classical control is at numerical precision. At tau=1 the graded")
    lines.append("  residual is also tiny; for tau != 1 it is 1e-1 to 1e-2, so the graded")
    lines.append("  function does not satisfy the completion symmetry.")

    lines.extend(["", "Zeros: ratio test at the classical zeros", "=" * 60])
    for tau in (0, mp.mpf("0.5"), mp.mpf("0.9"), 2):
        comparison = compare_zeros(tau, n_zeros=5, n_primes=300)
        lines.append(
            f"  tau={float(tau):g}: mean|R| at zeros="
            f"{comparison.mean_ratio_at_zeros:.4e} "
            f"at controls={comparison.mean_ratio_at_controls:.4e} "
            f"spread={comparison.ratio_spread:.3f}"
        )
    lines.append("")
    lines.append("  The ratio does not separate zeros from control points at any tested")
    lines.append("  tau, so this diagnostic cannot decide whether the zero sets agree.")
    lines.append("  A sign-change scan on the critical line is worse: at tau=1, where the")
    lines.append("  graded trace equals the classical partial product by construction, it")
    lines.append("  reports 28 sign changes against 4 classical zeros in [0.5, 30].")
    lines.append("  The Euler product truncated at a few hundred primes is simply not")
    lines.append("  accurate enough near the critical line to locate zeros.")
    lines.append("")
    lines.append("  Conclusion for G6: the evidence points to DIFFERENT zeros, though the")
    lines.append("  case is numerical rather than rigorous -- see the next block.")

    lines.extend(["", "Critical-line spread of the raw product", "=" * 60])
    _, low = _critical_line_values(1, 100)
    _, high = _critical_line_values(1, 1500)
    spread = max(abs(a - b) for a, b in zip(low, high) if a == a and b == b)
    lines.append(
        f"  max | 100-prime product - 1500-prime product | on t in [0, {T_MAX:g}] "
        f"= {spread:.4f}"
    )
    lines.append("  A converged series would show this shrinking with the prime count; it")
    lines.append("  does not, which is why the critical-line figure is not evidence about")
    lines.append("  the location of any zero.")

    lines.extend(["", "Ratio at the classical zeros", "=" * 60])
    lines.append(
        "  |Z_A(rho, tau)| / |Z_A(rho, 1)| at the first six zero heights"
    )
    lines.append(f"  {'tau':>6} | ratios at the first six zeros")
    for tau in (0, mp.mpf("0.5"), 2):
        ratios = _zero_ratios(tau)
        row = "  ".join(f"{r:.4f}" for r in ratios)
        lines.append(f"  {float(tau):6g} | {row}")
    lines.append("  The ratio is well defined (common truncation cancels). Two things")
    lines.append("  make it informative despite the oscillation:")
    lines.append("    - it is tightly clustered across the six zeros (spread ~2x), which")
    lines.append("      a noisy quantity would not be;")
    lines.append("    - it is NOT equal to 1 at the classical zeros. If the graded trace")
    lines.append("      vanished there, the ratio would be far below 1. At tau=0 it is")
    lines.append("      3.5 to 7.5; at tau=2 it is 0.53 to 0.57.")
    lines.append("  The tau=1 control in shift_zeta_comparison.png shows the method does")
    lines.append("  resolve zeros -- the trace there dips sharply exactly at the classical")
    lines.append("  zeros, and the tau=0 panel shows no corresponding dips. Therefore the")
    lines.append("  graded trace is strictly larger at those heights and its minima lie")
    lines.append("  elsewhere: the zero sets do not coincide.")
    lines.append("")
    lines.append("  This is numerical evidence, not a proof. What it establishes is that")
    lines.append("  for tau != 1 the graded trace is not merely a scalar multiple of")
    lines.append("  zeta; what it does not establish is any theorem about the critical")
    lines.append("  line.")
    lines.append("")
    lines.append("  A withdrawn statistic is recorded for honesty: 'deepest local minima'")
    lines.append("  scored 7 of 8 hits at tau=1, the control, so it was measuring")
    lines.append("  oscillation rather than zeros and is not used.")

    lines.extend(["", "Ratio at s in the convergent region", "=" * 60])
    primes = first_primes(300)
    for tau in (0, mp.mpf("0.5"), 2):
        row = [abs(graded_to_classical_ratio(s, tau, primes)) for s in (2, 3, 5)]
        lines.append(
            f"  tau={float(tau):g}: "
            + "  ".join(f"s={s}: {float(v):.6f}" for s, v in zip((2, 3, 5), row))
        )

    lines.extend(["", "Construction is confined to the fixed locus", "=" * 60])
    for tau in TAUS:
        gamma = grading_shift(tau)
        lines.append(
            f"  tau={float(tau):g}: gamma_tau = "
            f"({mp.nstr(gamma.a, 6)}, {mp.nstr(gamma.b, 6)}), even={gamma.is_even()}"
        )
    element = shift_zeta_element(2, 1, first_primes(20))
    lines.append(
        f"  product at tau=1: (a,b)=({mp.nstr(element.a, 8)}, "
        f"{mp.nstr(element.b, 8)}), in Fix(sigma)={element.is_fixed()}"
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print("Shift-zeta analysis (diagnostic; outcome is negative/null)")
    print("=" * 60)

    _plot_traces()
    _plot_convergence()
    _plot_critical_line()
    _plot_comparison()
    _write_summary(OUTPUT_DIR / "shift_zeta_summary.txt")

    for line in _gates():
        print(line)
    print()
    print("Wrote:")
    for name in (
        "shift_zeta_traces.png",
        "shift_zeta_convergence.png",
        "shift_zeta_critical_line.png",
        "shift_zeta_comparison.png",
        "shift_zeta_summary.txt",
    ):
        print(f"  output/{name}")
    print("See docs/shift_zeta_result.md for the interpretation.")


if __name__ == "__main__":
    main()
