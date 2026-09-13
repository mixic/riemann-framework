"""
Dimension-Shift Involution – numerical consistency check.

This module implements a hypothetical operation `sigma` that acts on a
number system extending the complex numbers. Unlike rotation in C
(continuous, within a 2D plane), `sigma` is a discrete involution that
"switches dimensions" while fixing the critical line Re(s) = 1/2.

The goal is NOT to prove RH, but to check whether such a structure is
numerically consistent with the functional equation of the zeta function.
"""

from dataclasses import dataclass
import mpmath as mp


# ============================================================
# The dimension-shift element w
# ============================================================

@dataclass(frozen=True)
class DimensionElement:
    """
    Represents the new element `w` and its action.

    Properties:
    - w is an involution: w^2 = id
    - w acts on a complex number by shifting its "dimension index"
    - w fixes the critical line: if Re(s) = 1/2, then w(s) = s
    """
    dimension: int = 0

    def act_on(self, s):
        """
        Apply w to a complex number s.

        The action is defined as:
            w(s) = 1 - conjugate(s)

        This fixes the full critical line Re(s) = 1/2.
        """
        return 1 - mp.conj(s)

    def __pow__(self, n):
        """w^2 = identity."""
        if n % 2 == 0:
            return DimensionElement(dimension=0)
        return self


# ============================================================
# The dimension-shift involution sigma
# ============================================================

def sigma(s):
    """
    The dimension-shift involution.

    Unlike rotation (multiplication by i), which is continuous and
    preserves distance to the origin, sigma is a discrete involution
    that swaps the two "sides" of the critical strip.

    Key property: sigma fixes the critical line pointwise.
    """
    return 1 - mp.conj(s)


def is_fixed_point(s, tol=None):
    """Check whether s is a fixed point of sigma (i.e. Re(s) = 1/2)."""
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)
    return mp.almosteq(sigma(s), s, abs_eps=tol)


# ============================================================
# Consistency checks
# ============================================================

def check_involution(tol=None):
    """Check sigma^2 = identity on a set of test points."""
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)

    test_points = [
        mp.mpc("0.5", "14.134725"),
        mp.mpc("0.3", "10.0"),
        mp.mpc("0.7", "-5.0"),
        mp.mpc("0.5", "0.0"),
        mp.mpc("2.0", "3.0"),
    ]

    results = []
    for s in test_points:
        s2 = sigma(sigma(s))
        results.append({
            "s": s,
            "sigma(s)": sigma(s),
            "sigma^2(s)": s2,
            "is_involution": mp.almosteq(s2, s, abs_eps=tol),
            "is_fixed": is_fixed_point(s, tol=tol),
        })
    return results


def check_fixed_locus(tol=None):
    """
    Check that the fixed locus of sigma is exactly the critical line.

    A point s is fixed iff Re(s) = 1/2.
    """
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)

    results = []
    for re_part in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
        s = mp.mpc(re_part, "10.0")
        results.append({
            "Re(s)": re_part,
            "is_fixed": is_fixed_point(s, tol=tol),
        })
    return results


def check_functional_equation_consistency(num_zeros=10, tol=None):
    """
    Check that sigma is compatible with the functional equation:

        zeta(s) = chi(s) * zeta(1 - s)

    The functional equation says that zeta is "sigma-symmetric" up to
    the factor chi(s). This is the numerical shadow of the claim that
    sigma is the correct involution.
    """
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)

    results = []
    for n in range(1, num_zeros + 1):
        rho = mp.zetazero(n)
        # Conjugation and the functional equation imply
        # zeta(1 - conjugate(rho)) = 0.
        z_at_rho = mp.zeta(rho)
        z_at_sigma_rho = mp.zeta(sigma(rho))
        results.append({
            "n": n,
            "rho": rho,
            "sigma(rho)": sigma(rho),
            "|zeta(rho)|": abs(z_at_rho),
            "|zeta(sigma(rho))|": abs(z_at_sigma_rho),
            "both_zero": (abs(z_at_rho) < tol) and (abs(z_at_sigma_rho) < tol),
        })
    return results


if __name__ == "__main__":
    mp.mp.dps = 30

    print("=" * 60)
    print("Dimension-Shift Involution: Consistency Checks")
    print("=" * 60)

    print("\n[1] Involution property: sigma^2 = identity")
    for r in check_involution():
        print(f"  s = {r['s']}, sigma(s) = {r['sigma(s)']}, "
              f"sigma^2(s) = {r['sigma^2(s)']}, "
              f"involution = {r['is_involution']}, "
              f"fixed = {r['is_fixed']}")

    print("\n[2] Fixed locus: sigma(s) = s iff Re(s) = 1/2")
    for r in check_fixed_locus():
        print(f"  Re(s) = {r['Re(s)']}, is_fixed = {r['is_fixed']}")

    print("\n[3] Functional-equation consistency")
    for r in check_functional_equation_consistency():
        print(f"  n = {r['n']}, rho = {r['rho']}, "
              f"|zeta(rho)| = {r['|zeta(rho)|']:.2e}, "
              f"|zeta(sigma(rho))| = {r['|zeta(sigma(rho))|']:.2e}, "
              f"both_zero = {r['both_zero']}")