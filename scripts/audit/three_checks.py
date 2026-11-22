"""The three checks as supplied, run exactly, and what each one actually tests.

Check 1 (split-prime idele).  Exact integer arithmetic in Z[i]: 5 = (2+i)(2-i),
both factors of norm 5, neither a unit, and the valuation pair (+1, -1) summing to
zero.  Generalised to every p = 1 mod 4 that is representable as a sum of squares.

Check 2 (Archimedean integral).  The supplied script integrates
    int_0^T exp(-pi x^2) x^(sigma-1) dx
and reads the growth of Gamma_R(sigma) = pi^(-sigma/2) Gamma(sigma/2) as a failure of
uniform boundedness.  This file shows that the integral converges to Gamma_R(sigma)/2
for every sigma > 0, i.e. that the observed growth is the *pole of Gamma at 0* -- the
trivial factor of zeta at s = 1 -- and not a property of any family of test functions.
The quantity that Masullo's Section 1.4.3 actually bounds is tested in
`masullo_archimedean.py`; this file only establishes that the supplied test does not
test it.

Check 3 (zeta values).  |zeta(1/2 + i t_k)| at the first zeros, and |zeta(0.6 + i t_k)|.
Recorded with the caveat that make it non-evidence: `mpmath.zetazero` returns zeros
that lie on the critical line by construction, so the on-line column is a consistency
check of the arithmetic, not a test of the hypothesis.

No output here is evidence for or against RH.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import mpmath as mp
from sympy import factorint

OUT = Path(r"C:\Users\Milan\Projects\riemann-audit\out")
mp.mp.dps = 30


# ---------------------------------------------------------------- check 1 ----
def gaussian_norm(a: int, b: int) -> int:
    """N(a + bi) = a^2 + b^2."""
    return a * a + b * b


def gaussian_mul(x: tuple[int, int], y: tuple[int, int]) -> tuple[int, int]:
    (a, b), (c, d) = x, y
    return (a * c - b * d, a * d + b * c)


def gaussian_is_unit(z: tuple[int, int]) -> bool:
    return gaussian_norm(*z) == 1


def split_prime_certificate(p: int) -> dict:
    """Find a^2 + b^2 = p and check the two Gaussian factors.

    The larger of the two squares is taken first, so that p = 5 is certified as
    5 = (2 + i)(2 - i), the pair used in `lean/RiemannFramework/IdeleSplit.lean`.
    """
    if p % 4 != 1:
        raise ValueError(f"{p} does not split in Z[i] (p = 3 mod 4)")
    a = next(x for x in range(_isqrt(p), 0, -1) if _is_square(p - x * x))
    b = _isqrt(p - a * a)
    pi1, pi2 = (a, b), (a, -b)
    prod = gaussian_mul(pi1, pi2)
    return {
        "p": p,
        "a": a,
        "b": b,
        "pi1": f"{a} + {b}i",
        "pi2": f"{a} - {b}i",
        "product": f"{prod[0]} + {prod[1]}i",
        "product_equals_p": prod == (p, 0),
        "norm_pi1": gaussian_norm(*pi1),
        "norm_pi2": gaussian_norm(*pi2),
        "pi1_is_unit": gaussian_is_unit(pi1),
        "pi2_is_unit": gaussian_is_unit(pi2),
        "local_valuations": [1, -1],
        "norm_valuation": 1 + (-1),
        "norm_valuation_is_zero": 1 + (-1) == 0,
    }


def _is_square(n: int) -> bool:
    r = _isqrt(n)
    return r * r == n


def _isqrt(n: int) -> int:
    import math

    return math.isqrt(n)


def check_one() -> dict:
    rows = [split_prime_certificate(p) for p in (5, 13, 29, 37, 41, 53, 61, 73)]
    # The p = 5 row spelled out, since that is the case the supplied script used.
    five = rows[0]
    # Exact rational check of the two local absolute values, as fractions:
    # |pi1|_{v1} = 5^-1, |pi2^-1|_{v2} = 5^+1, product 1.
    abs_v1 = Fraction(1, 5)
    abs_v2 = Fraction(5, 1)
    return {
        "all_split": all(r["product_equals_p"] and r["norm_pi1"] == r["p"] for r in rows),
        "all_factors_non_units": all(not r["pi1_is_unit"] and not r["pi2_is_unit"] for r in rows),
        "all_norm_valuations_zero": all(r["norm_valuation_is_zero"] for r in rows),
        "rows": rows,
        "p5_local_absolute_values": {
            "v1": str(abs_v1),
            "v2": str(abs_v2),
            "product": str(abs_v1 * abs_v2),
            "neither_is_one": abs_v1 != 1 and abs_v2 != 1,
        },
        "five": five,
    }


# ---------------------------------------------------------------- check 2 ----
def gamma_R(sigma: float) -> float:
    """Gamma_R(sigma) = pi^(-sigma/2) Gamma(sigma/2), the Archimedean factor."""
    s = mp.mpf(sigma)
    return float(mp.pi ** (-s / 2) * mp.gamma(s / 2))


def mellin_truncated(sigma: float, T: float) -> float:
    """int_0^T exp(-pi x^2) x^(sigma-1) dx, the supplied script's quantity."""
    s = mp.mpf(sigma)
    return float(mp.quad(lambda x: mp.exp(-mp.pi * x**2) * x ** (s - 1), [0, T]))


def mellin_truncated_exact(sigma: float, T: float) -> float:
    """The same integral, in closed form, so quadrature error is not mistaken for growth.

    Substituting u = pi x^2 gives

        int_0^T exp(-pi x^2) x^(sigma-1) dx = (1/2) pi^(-sigma/2) gamma(sigma/2, pi T^2),

    with gamma the lower incomplete gamma function.  As T -> infinity this is
    Gamma_R(sigma)/2, exactly, for every sigma > 0.
    """
    s = mp.mpf(sigma)
    lower = mp.gammainc(s / 2, 0, mp.pi * mp.mpf(T) ** 2)
    return float(mp.mpf("0.5") * mp.pi ** (-s / 2) * lower)


def check_two() -> dict:
    rows = []
    for sigma in (0.5, 0.2, 0.1, 0.01, 0.001):
        g = gamma_R(sigma)
        t100_supplied = mellin_truncated(sigma, 100.0)
        t100_exact = mellin_truncated_exact(sigma, 100.0)
        full = mellin_truncated_exact(sigma, mp.inf)
        rows.append(
            {
                "sigma": sigma,
                "Gamma_R": g,
                "mellin_T100_supplied": t100_supplied,
                "mellin_T100": t100_exact,
                "mellin_full": full,
                "half_Gamma_R": g / 2,
                "quadrature_relative_error": abs(t100_supplied - t100_exact) / t100_exact,
                "T100_over_half_GammaR": t100_exact / (g / 2) if g else None,
                "sigma_times_Gamma_R": sigma * g,
            }
        )
    return {
        "rows": rows,
        "identity_mellin_equals_half_GammaR": all(
            abs(r["mellin_full"] - r["half_Gamma_R"]) <= 1e-9 * max(1.0, abs(r["half_Gamma_R"]))
            for r in rows
        ),
        "worst_quadrature_relative_error": max(r["quadrature_relative_error"] for r in rows),
        "sigma_GammaR_limit": rows[-1]["sigma_times_Gamma_R"],
        "what_it_shows": (
            "int_0^inf exp(-pi x^2) x^(sigma-1) dx = Gamma_R(sigma)/2 for every sigma > 0; "
            "the growth as sigma -> 0+ is the pole of Gamma at 0, i.e. the trivial pole of zeta "
            "at s = 1. It is not a bound on any family of test functions, and sigma -> 0 is not "
            "the limit (epsilon -> 0, h -> 1) that Section 1.4.3 takes on a compact K. At "
            "sigma = 0.01 and 0.001 the supplied quadrature under-resolves the x^(sigma-1) "
            "endpoint and reports roughly half the true value."
        ),
    }


# ---------------------------------------------------------------- check 3 ----
def check_three() -> dict:
    rows = []
    for k in range(1, 6):
        z = mp.zetazero(k)
        t = z.imag
        rows.append(
            {
                "k": k,
                "t": float(t),
                "on_line_abs": float(abs(mp.zeta(mp.mpc(0.5, t)))),
                "off_line_06_abs": float(abs(mp.zeta(mp.mpc(0.6, t)))),
                "zetazero_real_part": float(mp.re(z)),
            }
        )
    return {
        "rows": rows,
        "all_on_line": all(abs(r["zetazero_real_part"] - 0.5) < 1e-12 for r in rows),
        "off_line_nonzero": all(r["off_line_06_abs"] > 1e-3 for r in rows),
        "circularity": (
            "mpmath.zetazero returns the k-th zero with real part 1/2 by construction, so the "
            "on-line column is a check of the evaluation, not a test of the hypothesis; and a "
            "finite list of zeros cannot decide a universal statement in any case."
        ),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"check1": check_one(), "check2": check_two(), "check3": check_three()}
    (OUT / "three_checks.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    c1 = result["check1"]
    print("CHECK 1 -- split primes in Z[i]")
    for r in c1["rows"]:
        print(
            f"  p={r['p']:>3}  ({r['pi1']})({r['pi2']}) = {r['product']}  "
            f"norms={r['norm_pi1']},{r['norm_pi2']}  units={r['pi1_is_unit']},{r['pi2_is_unit']}  "
            f"norm valuation={r['norm_valuation']}"
        )
    print("  p=5 local absolute values:", c1["p5_local_absolute_values"])
    print(f"  all products correct={c1['all_split']}, all non-units={c1['all_factors_non_units']}")

    print("\nCHECK 2 -- the supplied Archimedean test")
    print("  sigma     Gamma_R        quad[0,100]    exact[0,100]   Gamma_R/2      sigma*Gamma_R")
    for r in result["check2"]["rows"]:
        print(
            f"  {r['sigma']:<9} {r['Gamma_R']:<14.6g} {r['mellin_T100_supplied']:<14.6g} "
            f"{r['mellin_T100']:<14.6g} {r['half_Gamma_R']:<14.6g} {r['sigma_times_Gamma_R']:.6g}"
        )
    print("  worst quadrature relative error:", result["check2"]["worst_quadrature_relative_error"])
    print("  Mellin(full) == Gamma_R/2 for all sigma:", result["check2"]["identity_mellin_equals_half_GammaR"])
    print("  sigma*Gamma_R at sigma=0.001:", result["check2"]["sigma_GammaR_limit"])

    print("\nCHECK 3 -- zeta on and off the line")
    for r in result["check3"]["rows"]:
        print(
            f"  k={r['k']}  t={r['t']:.10f}  |zeta(1/2+it)|={r['on_line_abs']:.3e}  "
            f"|zeta(0.6+it)|={r['off_line_06_abs']:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
