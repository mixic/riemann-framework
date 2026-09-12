"""Numerical assert: RH for the first N zeros."""

import pytest

from riemann_framework.zeros import verify_first_n_zeros
from riemann_framework.zeta import set_precision

NUM_ZEROS = 100  # adjustable
DPS = 50


@pytest.fixture(autouse=True)
def setup_precision():
    set_precision(DPS)


def test_realpart_is_half():
    """For every tested zero: Re(ρ) = 1/2."""
    results = verify_first_n_zeros(NUM_ZEROS)
    for r in results:
        assert r["on_critical_line"], (
            f"ERROR: Zero #{r['n']} has real part {r['re']}, "
            f"expected 0.5"
        )


def test_zeta_value_is_zero():
    """For every tested zero: ζ(ρ) ≈ 0."""
    results = verify_first_n_zeros(NUM_ZEROS)
    for r in results:
        assert r["is_zero"], (
            f"ERROR: ζ({r['zero']}) is not zero"
        )