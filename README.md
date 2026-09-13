# Riemann Framework

Riemann Framework is an experimental research project for exploring and
verifying approaches to the Riemann Hypothesis (RH). It combines numerical
experiments in Python with a planned Lean 4 formalization, including
computations involving zeta zeros, the explicit formula, prime counting, and
dimension-shift models. The project does **not** claim to prove the Riemann
Hypothesis; computational results and passing tests are research evidence,
not a completed mathematical proof.

## Disclaimer

This project is **not a proof** of the Riemann Hypothesis. It is a tool to:
- test the RH **numerically** for known zeros,
- verify **formal proof attempts** in Lean 4,
- visualize and analyze the **explicit formula**.

A passing test is **evidence**, not a mathematical proof.

## Status

| Component | Status |
|:---|:---|
| Numerical zero verification | Working |
| Explicit-formula calculations and plots | Working |
| Dimension-shift experiments | Working and exploratory |
| DSIN communication simulation | Working as a toy simulation; no security proof |
| Lean formalization of RH | Scaffold planned; no Lean source currently tracked |
| Formal proof of RH | Open problem |

## Goal

The Riemann Hypothesis states that all non-trivial zeros of the
Riemann zeta function lie on the critical line `Re(s) = 1/2`.

This framework combines:
- **Python** (mpmath, numpy, matplotlib) for numerical verification and visualization,
- **Lean 4 + Mathlib** as a planned formalization target,
- **pytest** as the test infrastructure (unit-test metaphor for the RH).

## Generated Results

Plots are generated locally and are not required source files. From the
repository root, run:

```powershell
python python/riemann_framework/test_plot.py
python scripts/run_dimension_shift_chaos.py
```

The scripts write PNG files to `output/`, including zero plots,
explicit-formula plots, spectrum comparisons, coupling sweeps, and
symmetry-breaking sweeps. The current plot snapshots are included below.

### Non-trivial zeros in the complex plane

![First 100 non-trivial zeros of the Riemann zeta function](output/riemann_zeros_complex.png)

### Explicit formula approximation

![Riemann explicit formula approximation](output/riemann_explicit_formula.png)

### Dimension-shift spectrum comparison

![Dimension-shift spectrum compared with Riemann zeros](output/dimension_shift_spectrum.png)

### Dimension-shift coupling sweep

![Dimension-shift coupling sweep](output/dimension_shift_coupling_sweep.png)

### Dimension-shift symmetry-breaking sweep

![Dimension-shift symmetry-breaking sweep](output/dimension_shift_symmetry_sweep.png)

## Project Structure


```
riemann-framework/
│
├── README.md                     # Main documentation
├── LICENSE                       # GPL-3.0
├── .gitignore                    # Exclude Python, Lean, VS Code artifacts
├── lakefile.toml                 # Lean 4 project definition
├── lean-toolchain                # Lean version pin (e.g. leanprover/lean4:v4.x.x)
│
├── lean/                         # Formal verification
│   └── RiemannFramework/             # Reserved for future Lean formalization
│
├── python/                       # Numerical tests and control logic
│   ├── pyproject.toml            # Project definition (uv/pip)
│   ├── requirements.txt          # numpy, matplotlib, mpmath, pytest
│   │
│   ├── riemann_framework/        # Python package
│   │   ├── __init__.py
│   │   ├── zeta.py               # mpmath wrapper for ζ(s)
│   │   ├── zeros.py              # Computation / verification of zeros
│   │   ├── explicit_formula.py   # Riemann explicit formula
│   │   ├── dimension_shift.py    # Dimension-shift operator model
│   │   ├── dimension_shift_chaos.py # Hamiltonian chaos experiments
│   │   ├── quantum_chaos.py       # Zero-spacing statistics
│   │   ├── dsin.py                # DSIN communication simulation
│   │   ├── statistics.py          # Spectral statistics utilities
│   │   ├── lean_runner.py        # Compiles Lean files via subprocess
│   │   └── plots.py              # Plot generation
│   │
│   └── tests/                    # pytest tests
│       ├── test_numeric_zeros.py     # Numerical assert
│       ├── test_formal_proof.py      # Formal assert (Lean)
│       ├── test_explicit_formula.py  # Test of the explicit formula
│       ├── test_dimension_shift.py   # Dimension-shift tests
│       ├── test_dimension_shift_chaos.py # Chaos pipeline tests
│       ├── test_quantum_chaos.py     # Zero statistics tests
│       └── test_dsin.py              # DSIN simulation tests
│
├── scripts/                      # Helper scripts
│   ├── setup_lean.sh             # Set up Lean + Mathlib
│   ├── generate_plots.py          # Generate standard plots
│   ├── run_dimension_shift_chaos.py # Generate chaos plots
│   └── run_dsin_analysis.py       # Run DSIN simulations
│
├── docs/                         # Documentation
│   ├── research_notes.md         # What has been tried so far
│   ├── number_systems.md         # Your idea with new number systems
│   ├── spherical_number_systems.md # Hypothetical higher-dimensional model
│   ├── dimension_shift_involution.md # Discrete involution proposal
│   ├── dimension_shift_quantum_chaos.md # Quantum-chaos extension
│   ├── dimension_shift_computational_approach.md # Computational methodology
│   ├── dimension_shift_quantum_communication.md # DSIN communication proposal
│   └── verification.md           # How an RH proof is checked
│
├── output/                       # Generated plots (gitignored)
│   └── .gitkeep
│
└── .github/
    └── workflows/
        └── ci.yml                # GitHub Actions: run tests automatically
```

## License

This project is licensed under the **GNU General Public License v3.0**.

See [`LICENSE`](LICENSE) for the full text.

**Note:** The Lean library **Mathlib** is licensed under the
Apache License 2.0 and is compatible with GPL v3. See
[Mathlib LICENSE](https://github.com/leanprover-community/mathlib4/blob/master/LICENSE).

## Third-Party Software

This project uses third-party dependencies with their own licenses,
including mpmath, NumPy, Matplotlib, pytest, Lean, and Mathlib. Their
respective licenses remain applicable to those components.