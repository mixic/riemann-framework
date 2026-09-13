"""
Quantitative falsification test for the Dimension-Shift Hypothesis (DSH).

This module runs the dimension-shift Hamiltonian across a grid of
parameters (coupling, symmetry_breaking, dim_per_sector) and reports
the mean r-ratio for each combination.

The goal is to answer one question with numbers:

    Does the dimension-shift model reach GUE statistics (mean r ~ 0.599)?

If yes: DSH is supported (evidence, not proof).
If no:  DSH is falsified at the tested parameters.

Reference values:
    Poisson (integrable):          0.386
    GOE (chaotic, T-symmetric):    0.530
    GUE (chaotic, T-broken):       0.599
    Riemann zeros (target):        0.592 (for the first 100 zeros)
"""

import numpy as np
from dataclasses import dataclass, asdict

from .statistics import mean_r_ratio, ks_test_against, classify_statistics
from .dimension_shift_chaos import build_dimension_shift_hamiltonian


# ============================================================
# Reference values
# ============================================================

R_POISSON = 0.386
R_GOE = 0.530
R_GUE = 0.599
R_RIEMANN = 0.592  # for the first 100 zeros

GUE_WINDOW = (0.58, 0.62)   # accepted range for "GUE-like"
GOE_WINDOW = (0.51, 0.55)   # accepted range for "GOE-like"
POISSON_WINDOW = (0.36, 0.41)  # accepted range for "Poisson-like"


# ============================================================
# Single run
# ============================================================

@dataclass
class FalsificationResult:
    """Result of a single parameter point."""
    dim_per_sector: int
    coupling: float
    symmetry_breaking: float
    mean_r: float
    best_fit: str
    ks_gue: float
    ks_poisson: float
    verdict: str  # "gue", "goe", "poisson", "intermediate"


def classify_verdict(mean_r: float) -> str:
    """Classify the mean r-ratio into a regime."""
    if GUE_WINDOW[0] <= mean_r <= GUE_WINDOW[1]:
        return "gue"
    if GOE_WINDOW[0] <= mean_r <= GOE_WINDOW[1]:
        return "goe"
    if POISSON_WINDOW[0] <= mean_r <= POISSON_WINDOW[1]:
        return "poisson"
    return "intermediate"


def run_single(
    dim_per_sector: int,
    coupling: float,
    symmetry_breaking: float,
    seed: int = 42,
) -> FalsificationResult:
    """Run one parameter point and return the result."""
    H = build_dimension_shift_hamiltonian(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        symmetry_breaking=symmetry_breaking,
        seed=seed,
    )
    eigenvalues = np.linalg.eigvalsh(H)

    mean_r = mean_r_ratio(eigenvalues, unfold=True)
    classification = classify_statistics(eigenvalues, unfold=True)
    ks_gue = ks_test_against(eigenvalues, reference="gue", unfold=True)
    ks_poisson = ks_test_against(eigenvalues, reference="poisson", unfold=True)

    return FalsificationResult(
        dim_per_sector=dim_per_sector,
        coupling=coupling,
        symmetry_breaking=symmetry_breaking,
        mean_r=mean_r,
        best_fit=classification["best_fit"],
        ks_gue=ks_gue["ks_stat"],
        ks_poisson=ks_poisson["ks_stat"],
        verdict=classify_verdict(mean_r),
    )


# ============================================================
# Grid sweep
# ============================================================

def run_grid(
    dim_per_sector_values=None,
    coupling_values=None,
    symmetry_breaking_values=None,
    seed: int = 42,
) -> list:
    """
    Run the falsification test across a full grid of parameters.

    Returns a list of FalsificationResult objects.
    """
    if dim_per_sector_values is None:
        dim_per_sector_values = [10, 20, 30]
    if coupling_values is None:
        coupling_values = [0.0, 0.25, 0.5, 1.0, 2.0, 5.0]
    if symmetry_breaking_values is None:
        symmetry_breaking_values = [0.0, 0.5, 1.0, 2.0, 5.0]

    results = []
    total = (len(dim_per_sector_values)
             * len(coupling_values)
             * len(symmetry_breaking_values))
    count = 0

    for d in dim_per_sector_values:
        for c in coupling_values:
            for sb in symmetry_breaking_values:
                count += 1
                print(f"  [{count}/{total}] d={d}, coupling={c}, "
                      f"symmetry_breaking={sb}")
                r = run_single(d, c, sb, seed=seed)
                results.append(r)
    return results


def summarize_grid(results: list) -> dict:
    """
    Summarize the grid results into a single falsification verdict.

    Returns:
        {
            "n_runs": int,
            "max_mean_r": float,
            "max_mean_r_params": dict,
            "min_mean_r": float,
            "n_gue": int,
            "n_goe": int,
            "n_poisson": int,
            "n_intermediate": int,
            "verdict": str,
            "explanation": str,
        }
    """
    mean_rs = [r.mean_r for r in results]
    max_idx = int(np.argmax(mean_rs))
    min_idx = int(np.argmin(mean_rs))

    n_gue = sum(1 for r in results if r.verdict == "gue")
    n_goe = sum(1 for r in results if r.verdict == "goe")
    n_poisson = sum(1 for r in results if r.verdict == "poisson")
    n_intermediate = sum(1 for r in results if r.verdict == "intermediate")

    # Determine the overall verdict
    if n_gue > 0:
        verdict = "supported"
        explanation = (
            f"DSH is SUPPORTED: {n_gue} of {len(results)} parameter "
            f"points reached GUE statistics (mean r in "
            f"[{GUE_WINDOW[0]}, {GUE_WINDOW[1]}]). "
            f"Maximum mean r = {mean_rs[max_idx]:.4f} at "
            f"d={results[max_idx].dim_per_sector}, "
            f"coupling={results[max_idx].coupling}, "
            f"sb={results[max_idx].symmetry_breaking}."
        )
    elif n_goe > 0 and n_intermediate == 0:
        verdict = "goe_only"
        explanation = (
            f"DSH is NOT SUPPORTED for GUE: the model reaches GOE "
            f"statistics (mean r in [{GOE_WINDOW[0]}, {GOE_WINDOW[1]}]) "
            f"but never GUE. Maximum mean r = {mean_rs[max_idx]:.4f}. "
            f"This suggests the model is time-reversal symmetric, not "
            f"time-reversal broken."
        )
    elif n_poisson > 0 and n_gue == 0 and n_goe == 0:
        verdict = "poisson_only"
        explanation = (
            f"DSH is FALSIFIED for GUE: the model is integrable "
            f"(Poisson statistics) across all tested parameters. "
            f"Maximum mean r = {mean_rs[max_idx]:.4f}, which is well "
            f"below the GUE value {R_GUE}."
        )
    else:
        verdict = "inconclusive"
        explanation = (
            f"DSH is INCONCLUSIVE: the model shows intermediate "
            f"statistics (mean r in [0.41, 0.51] or [0.55, 0.58]) "
            f"that do not clearly match any reference. "
            f"Maximum mean r = {mean_rs[max_idx]:.4f}. "
            f"Further exploration is needed."
        )

    return {
        "n_runs": len(results),
        "max_mean_r": float(mean_rs[max_idx]),
        "max_mean_r_params": asdict(results[max_idx]),
        "min_mean_r": float(mean_rs[min_idx]),
        "min_mean_r_params": asdict(results[min_idx]),
        "n_gue": n_gue,
        "n_goe": n_goe,
        "n_poisson": n_poisson,
        "n_intermediate": n_intermediate,
        "verdict": verdict,
        "explanation": explanation,
    }