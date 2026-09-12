"""Temporary diagnostic: find the best sigma for regularization."""

import numpy as np
from riemann_framework.explicit_formula import prime_count, li_approx
from riemann_framework.zeta import set_precision

set_precision(25)

x_values = np.arange(10, 200)
pi_values = np.array([prime_count(x) for x in x_values])

for sigma in [0.1, 0.3, 0.5, 1.0, 2.0]:
    errors = []
    for nz in [0, 10, 50]:
        approx = np.array([li_approx(x, nz, sigma=sigma) for x in x_values])
        errors.append(np.max(np.abs(approx - pi_values)))
    print(f"sigma={sigma}: {errors}")