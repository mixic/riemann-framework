"""Generate all plots for the Riemann Framework."""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import mpmath as mp

from .explicit_formula import prime_count, li_approx
from .zeta import set_precision, zeta_zero

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

set_precision(25)


def plot_explicit_formula():
    """Plot 1: Explicit formula."""
    X_MAX = 200
    x_values = np.arange(2, X_MAX + 1)
    pi_values = np.array([prime_count(x) for x in x_values])

    zero_counts = [0, 5, 20, 50, 100]
    approx_curves = {}
    for nz in zero_counts:
        print(f"Computing {nz} zeros...")
        approx_curves[nz] = np.array([li_approx(x, nz) for x in x_values])

    fig, axes = plt.subplots(2, 1, figsize=(12, 9))

    ax = axes[0]
    ax.step(x_values, pi_values, where="post", color="black",
            linewidth=2, label="π(x) – true prime counting function")
    for nz in zero_counts:
        style = "--" if nz == 0 else "-"
        label = "Li(x) – no zeros" if nz == 0 else f"Li(x) − Σ ({nz} zeros)"
        ax.plot(x_values, approx_curves[nz], style, linewidth=1.3, label=label)
    ax.set_xlabel("x")
    ax.set_ylabel("π(x)")
    ax.set_title("Riemann explicit formula: primes from zeta zeros")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    for nz in zero_counts:
        error = approx_curves[nz] - pi_values
        style = "--" if nz == 0 else "-"
        label = "Error without zeros" if nz == 0 else f"Error with {nz} zeros"
        ax.plot(x_values, error, style, linewidth=1.3, label=label)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("x")
    ax.set_ylabel("Approximation − π(x)")
    ax.set_title("Approximation error")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "riemann_explicit_formula.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"✅ Saved: {out}")


def plot_zeros_complex():
    """Plot 2: Zeros in the complex plane."""
    fig, ax = plt.subplots(figsize=(10, 8))

    N_ZEROS = 100
    zeros = [zeta_zero(n) for n in range(1, N_ZEROS + 1)]
    re_parts = [float(z.real) for z in zeros]
    im_parts = [float(z.imag) for z in zeros]

    ax.axvline(0.5, color="red", linewidth=2, linestyle="--",
               label="Critical line Re(s) = 1/2")
    ax.scatter(re_parts, im_parts, color="blue", s=30, zorder=5,
               label=f"{N_ZEROS} non-trivial zeros")

    ax.set_xlabel("Re(s)")
    ax.set_ylabel("Im(s)")
    ax.set_title("The first 100 non-trivial zeros of the zeta function")
    ax.set_xlim(-0.2, 1.2)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "riemann_zeros_complex.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"✅ Saved: {out}")


def plot_error_amplitude():
    """Plot 3: Error amplitude vs. number of zeros."""
    X_MAX = 200
    x_values = np.arange(2, X_MAX + 1)
    pi_values = np.array([prime_count(x) for x in x_values])

    nz_range = [0, 1, 2, 5, 10, 20, 50, 100, 200]
    max_errors = []
    for nz in nz_range:
        print(f"Error analysis for {nz} zeros...")
        approx = np.array([li_approx(x, nz) for x in x_values])
        max_errors.append(np.max(np.abs(approx - pi_values)))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(nz_range, max_errors, "o-", color="darkred", linewidth=2, markersize=8)
    ax.set_xlabel("Number of zeros included")
    ax.set_ylabel("Maximum error |Approximation − π(x)|")
    ax.set_title("Error shrinks with the number of zeros")
    ax.set_xscale("symlog")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.3, which="both")

    plt.tight_layout()
    out = OUTPUT_DIR / "riemann_error_amplitude.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"✅ Saved: {out}")


if __name__ == "__main__":
    plot_explicit_formula()
    plot_zeros_complex()
    plot_error_amplitude()
    print("\n🎉 All plots created!")