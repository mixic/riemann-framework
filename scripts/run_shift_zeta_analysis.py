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

Usage:
    python scripts/run_shift_zeta_analysis.py

Writes:
    output/shift_zeta_traces.png        graded trace vs classical zeta, by tau
    output/shift_zeta_convergence.png   Euler truncation error vs number of primes
    output/shift_zeta_summary.txt       every number quoted in the report

This is a diagnostic run, not a proof of anything. It reports a negative/null
outcome; see docs/shift_zeta_result.md.
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
    classical_partial_euler,
    compare_zeros,
    first_primes,
    functional_equation_residual,
    graded_to_classical_ratio,
    shift_zeta,
    shift_zeta_element,
    shift_zeta_supertrace,
)

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

mp.mp.dps = 30

TAUS = [1, 0, mp.mpf("0.5"), mp.mpf("0.25"), 2]
S_VALUES = [2, 3, 4, 5, 6]


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

    g2 = all(
        (x * y).sigma() == x.sigma() * y.sigma() for x in samples for y in samples
    )
    lines.append(f"G2 sigma is an algebra homomorphism            : {'PASS' if g2 else 'FAIL'}")

    tol = mp.mpf(10) ** -25
    g3 = all(abs(x.sigma().trace() - x.trace()) < tol for x in samples)
    lines.append(f"G3 trace invariant under sigma                 : {'PASS' if g3 else 'FAIL'}")

    f5 = all(
        abs(x.sigma().supertrace() + x.supertrace()) < tol for x in samples
    )
    lines.append(
        f"F5 supertrace anti-invariant (flips sign)      : {'PASS (expected)' if f5 else 'FAIL'}"
    )

    g4 = True
    for s in (2, 3):
        for tau in TAUS:
            value = shift_zeta(s, tau, first_primes(20))
            g4 = g4 and bool(mp.isfinite(value.real))
    lines.append(f"G4 shift-zeta returns finite values            : {'PASS' if g4 else 'FAIL'}")

    f4 = not g2
    lines.append(f"F4 involution NOT a homomorphism               : {'TRIGGERED' if f4 else 'not triggered'}")

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

    zeta_values = [float(mp.zeta(s)) for s in S_VALUES]
    axis.plot(S_VALUES, zeta_values, "k--", marker="o", label="classical zeta(s)")

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
    lines.append(f"{'tau':>6} | " + " | ".join(f"s={s}" for s in S_VALUES) + " | max rel err")
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
                f"1/(1-x)={mp.nstr(1 / (1 - x), 12)}  supertrace={mp.nstr(factor.supertrace(), 4)}"
            )

    lines.extend(["", "Functional equation residuals", "=" * 60])
    for entry in functional_equation_residual(n_primes=200):
        parts = "  ".join(
            f"{k}={entry[k]:.3e}" for k in sorted(entry) if k.startswith("tau_")
        )
        lines.append(f"  s={entry['s']}: classical={entry['classical_residual']:.3e}  {parts}")
    lines.append(
        "  The classical control is at numerical precision. At tau=1 the graded"
    )
    lines.append(
        "  residual is also tiny; for tau != 1 it is 1e-1 to 1e-2, so the graded"
    )
    lines.append("  function does not satisfy the completion symmetry.")

    lines.extend(["", "Zeros: ratio test at the classical zeros", "=" * 60])
    for tau in (0, mp.mpf("0.5"), mp.mpf("0.9"), 2):
        comparison = compare_zeros(tau, n_zeros=5, n_primes=300)
        lines.append(
            f"  tau={float(tau):g}: mean|R| at zeros={comparison.mean_ratio_at_zeros:.4e} "
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
    lines.append("  Conclusion for G6: UNDECIDABLE at accessible truncation.")

    lines.extend(["", "Ratio at s in the convergent region", "=" * 60])
    primes = first_primes(300)
    for tau in (0, mp.mpf("0.5"), 2):
        row = [
            abs(graded_to_classical_ratio(s, tau, primes)) for s in (2, 3, 5)
        ]
        lines.append(
            f"  tau={float(tau):g}: " + "  ".join(f"s={s}: {float(v):.6f}" for s, v in zip((2, 3, 5), row))
        )

    lines.extend(["", "Construction is confined to the fixed locus", "=" * 60])
    for tau in TAUS:
        gamma = grading_shift(tau)
        lines.append(
            f"  tau={float(tau):g}: gamma_tau = ({mp.nstr(gamma.a, 6)}, {mp.nstr(gamma.b, 6)}), "
            f"even={gamma.is_even()}"
        )
    element = shift_zeta_element(2, 1, first_primes(20))
    lines.append(
        f"  product at tau=1: (a,b)=({mp.nstr(element.a, 8)}, {mp.nstr(element.b, 8)}), "
        f"in Fix(sigma)={element.is_fixed()}"
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print("Shift-zeta analysis (diagnostic; outcome is negative/null)")
    print("=" * 60)

    _plot_traces()
    _plot_convergence()
    _write_summary(OUTPUT_DIR / "shift_zeta_summary.txt")

    for line in _gates():
        print(line)
    print()
    print("Wrote shift_zeta_traces.png, shift_zeta_convergence.png, shift_zeta_summary.txt")
    print("See docs/shift_zeta_result.md for the interpretation.")


if __name__ == "__main__":
    main()
