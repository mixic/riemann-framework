"""Phase 2.2: the norm-preimage identification of Masullo's divisorial strata.

The claim under test, quoted from the draft (Section 1.3.2, pp. 25-26):

    "the stratum GL1(A_F)^{P_k} is the pre-image under the norm map
     GL1(A_F) -> GL1(A_Q) of the kth divisorial stratum on GL1(A_Q)",

with, explicitly,

    GL1(A_F)^{P_k} = {g : g_v in O_{F_v}^x for all v in S_p, p in T_k},
    T_k = the first k rational primes,

and the Q-side stratum defined the same way on GL_1(A_Q).

Test.  Let F be a quadratic field and p a rational prime with p = p1 p2 split.
Put g_{p1} = p, g_{p2} = 1/p, and g_w = 1 at every other place.  Then

    N(g)_p = g_{p1} * g_{p2} = 1,

so N(g) is the identity idele of A_Q^x, which is a unit at every place and so
lies in *every* Q-stratum T_k.  But g is a non-unit at both places above p,
so g does not lie in the F-stratum P_k as soon as p is among the first k
primes.  Therefore

    N^{-1}(T_k)  strictly contains  GL1(A_F)^{P_k},

so the identification as stated is false, by an exact integer computation with
no numerical error.  The ramified case is checked as the control: there the
local norms multiply, N_{F_v/Q_p}(g) = g^2, so a unit norm forces a unit, and
no such cancellation exists.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from sympy import legendre_symbol, primerange

OUT = Path(r"C:\Users\Milan\Projects\riemann-audit\out")

# The first rational primes, for the T_k strata.
PRIMES = list(primerange(2, 60))


def splitting_behaviour(d: int, p: int) -> str:
    """split / ramified / inert for the quadratic field Q(sqrt d) at p."""
    disc = d if d % 4 == 1 else 4 * d
    if p == 2:
        # Q(sqrt d) with d squarefree: 2 is ramified iff disc is even and the
        # field discriminant is even; treat via the discriminant's 2-adic part.
        return "ramified" if disc % 4 == 0 else "split"
    if disc % p == 0:
        return "ramified"
    ls = legendre_symbol(d % p, p)
    return "split" if ls == 1 else "inert"


def local_abs(g: Fraction, v_p: Fraction, p: int) -> Fraction:
    """Normalised absolute value at p: |g|_p = p^{-v_p(g)}, v_p for rational g."""
    # Fraction g possibly with p-power denominator-numerator.
    if g == 0:
        return Fraction(0)
    num, den = abs(g.numerator), g.denominator
    e = 0
    while num % p == 0:
        num //= p
        e += 1
    while den % p == 0:
        den //= p
        e -= 1
    return Fraction(p) ** (-e)


def stratum_test(g: dict[int, Fraction], p: int, k: int, split: bool) -> bool:
    """Is the idele in the F-stratum P_k?  Units above the first k primes.

    `g` maps a prime p to the *product* of the components at the places above p
    only in the split case do we need the components separately; we pass the
    two components as g[p] = (g_{p1}, g_{p2}) or a single Fraction when inert or
    ramified.
    """
    first_k = set(PRIMES[:k])
    for q, comp in g.items():
        if q in first_k:
            vals = comp if isinstance(comp, tuple) else (comp,)
            for c in vals:
                if local_abs(c, None, q) != 1:
                    return False
    return True


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []

    # --- the main counterexample: split primes in Q(sqrt 5), and controls -----
    for d in (5, 2, -3):
        for p in (5, 11, 19, 29, 3, 7):
            kind = splitting_behaviour(d, p)
            if kind == "split":
                # N(g)_p = g_{p1} * g_{p2} = 1 with both components non-units
                comps = (Fraction(p), Fraction(1, p))
                norm_at_p = comps[0] * comps[1]
                norm_is_unit = local_abs(norm_at_p, None, p) == 1
                # smallest k such that p is among the first k primes
                k_p = PRIMES.index(p) + 1
                in_preimage = norm_is_unit  # norm = 1 is a unit everywhere
                in_stratum = all(local_abs(c, None, p) == 1 for c in comps)
                rows.append(
                    {
                        "field": f"Q(sqrt({d}))",
                        "p": p,
                        "behaviour": kind,
                        "components": [str(comps[0]), str(comps[1])],
                        "N_g_at_p": str(norm_at_p),
                        "norm_is_unit": norm_is_unit,
                        "local_abs": [str(local_abs(c, None, p)) for c in comps],
                        "in_norm_preimage_T_k": in_preimage,
                        "in_F_stratum_P_k": in_stratum,
                        "k_for_which_p_in_T_k": k_p,
                        "violates_identification": in_preimage and not in_stratum,
                    }
                )
            elif kind == "ramified":
                # control: N_{F_v/Q_p}(g) = g^2, so unit norm forces unit g
                comps = (Fraction(p),)  # a single place above p
                norm_at_p = comps[0] ** 2
                norm_is_unit = local_abs(norm_at_p, None, p) == 1
                in_stratum = local_abs(comps[0], None, p) == 1
                rows.append(
                    {
                        "field": f"Q(sqrt({d}))",
                        "p": p,
                        "behaviour": kind,
                        "components": [str(comps[0])],
                        "N_g_at_p": str(norm_at_p),
                        "norm_is_unit": norm_is_unit,
                        "local_abs": [str(local_abs(comps[0], None, p))],
                        "in_norm_preimage_T_k": norm_is_unit,
                        "in_F_stratum_P_k": in_stratum,
                        "k_for_which_p_in_T_k": PRIMES.index(p) + 1,
                        "violates_identification": False,
                        "note": "ramified: cancellation impossible, unit norm forces unit",
                    }
                )

    splits = [r for r in rows if r["behaviour"] == "split"]
    violations = [r for r in splits if r["violates_identification"]]

    # The k=3 instance spelled out, since T_3 = {2,3,5}: Q(sqrt 5), p = 5 is
    # ramified, so use the first split prime after it to keep the argument exact.
    showcase = next((r for r in splits if r["field"] == "Q(sqrt(5))"), None)

    result = {
        "claim": (
            "GL1(A_F)^{P_k} equals the norm pre-image of the k-th divisorial stratum on GL1(A_Q)"
        ),
        "rows": rows,
        "split_cases": len(splits),
        "violations": len(violations),
        "showcase": showcase,
        "verdict": (
            "REFUTED as an identity: for a split prime the two local components cancel under the "
            "norm, so the norm pre-image of T_k contains ideles that are non-units above a prime of "
            "T_k and therefore lie in no P_k. The inclusion P_k subset N^{-1}(T_k) holds; the "
            "reverse inclusion fails."
        ),
        "ramified_control": [r for r in rows if r["behaviour"] == "ramified"][:3],
    }
    (OUT / "masullo_idele_strata.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"{'field':<12}{'p':>4} {'behaviour':<10} {'N(g)_p':>10} {'norm unit':>10} "
          f"{'in preimage':>12} {'in stratum':>11} {'violates':>9}")
    for r in rows:
        print(
            f"{r['field']:<12}{r['p']:>4} {r['behaviour']:<10} {r['N_g_at_p']:>10} "
            f"{str(r['norm_is_unit']):>10} {str(r['in_norm_preimage_T_k']):>12} "
            f"{str(r['in_F_stratum_P_k']):>11} {str(r['violates_identification']):>9}"
        )
    print(f"\nsplit cases: {len(splits)}; violations of the identity: {len(violations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
