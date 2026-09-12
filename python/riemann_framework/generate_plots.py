"""Generate all plots for the Riemann Framework."""

from pathlib import Path
import sys

# Add package path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from riemann_framework.plots import (
    plot_explicit_formula,
    plot_zeros_complex,
    plot_error_amplitude,
)


if __name__ == "__main__":
    plot_explicit_formula()
    plot_zeros_complex()
    plot_error_amplitude()
    print("\n🎉 All plots created!")