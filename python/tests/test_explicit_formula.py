"""Test of the Riemann explicit formula."""

import numpy as np
import pytest

from riemann_framework.explicit_formula import prime_count, li_approx
from riemann_framework.zeta import set_precision


@pytest.fixture(autouse=True)
def setup_precision():
    set_precision(25)


def test_pi_small_values():
    """Known values: π(10) = 4, π(100) = 25, π(1000) = 168."""
    assert prime_count(10) == 4
    assert prime_count(100) == 25
    assert prime_count(1000) == 168


def test_approximation_improves_with_zeros():
    """The more zeros are included, the smaller the maximum error."""
    x_values = np.arange(10, 200)
    pi_values = np.array([prime_count(x) for x in x_values])

    errors = []
    for nz in [0, 10, 50]:
        approx = np.array([li_approx(x, nz) for x in x_values])
        errors.append(np.max(np.abs(approx - pi_values)))

    # Error must decrease monotonically
    assert errors[0] > errors[1] > errors[2], (
        f"Error is not monotonically decreasing: {errors}"
    )