# Riemann Framework

Riemann Framework is an experimental research project for exploring and
verifying approaches to the Riemann Hypothesis (RH). It combines numerical
experiments in Python with formal definitions and proof checking in Lean 4,
including computations involving zeta zeros, the explicit formula, and prime
counting. The project does **not** claim to prove the Riemann Hypothesis;
computational results and passing formal checks are research evidence, not a
completed mathematical proof.

## Disclaimer

This project is **not a proof** of the Riemann Hypothesis. It is a tool to:
- test the RH **numerically** for known zeros,
- verify **formal proof attempts** in Lean 4,
- visualize and analyze the **explicit formula**.

A passing test is **evidence**, not a mathematical proof.

## Goal

The Riemann Hypothesis states that all non-trivial zeros of the
Riemann zeta function lie on the critical line `Re(s) = 1/2`.

This framework combines:
- **Python** (mpmath, numpy, matplotlib) for numerical verification and visualization,
- **Lean 4 + Mathlib** for formal verification of proof attempts,
- **pytest** as the test infrastructure (unit-test metaphor for the RH).

## Generated Results

### Non-trivial zeros in the complex plane

![First 100 non-trivial zeros of the Riemann zeta function](output/riemann_zeros_complex.png)

### Explicit formula approximation

![Riemann explicit formula approximation](output/riemann_explicit_formula.png)

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
│   └── RiemannFramework/
│       ├── RiemannHypothesis.lean    # RH as a theorem with `sorry`
│       ├── Basic.lean                # Definitions (IsNontrivialZero, etc.)
│       └── SanityChecks.lean         # Tests of the definitions
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
│   │   ├── lean_runner.py        # Compiles Lean files via subprocess
│   │   └── plots.py              # Plot generation
│   │
│   └── tests/                    # pytest tests
│       ├── test_numeric_zeros.py     # Numerical assert
│       ├── test_formal_proof.py      # Formal assert (Lean)
│       └── test_explicit_formula.py  # Test of the explicit formula
│
├── scripts/                      # Helper scripts
│   ├── setup_lean.sh             # Set up Lean + Mathlib
│   └── generate_plots.py         # Generate all plots at once
│
├── docs/                         # Documentation
│   ├── research_notes.md         # What has been tried so far
│   ├── number_systems.md         # Your idea with new number systems
│   ├── spherical_number_systems.md # Hypothetical higher-dimensional model
│   ├── dimension_shift_involution.md # Discrete involution proposal
│   ├── dimension_shift_quantum_chaos.md # Quantum-chaos extension
│   ├── dimension_shift_computational_approach.md # Computational methodology
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