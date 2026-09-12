# Research Notes on the Riemann Hypothesis

This document summarizes what has been attempted so far in the pursuit
of a proof of the Riemann Hypothesis (RH), and what remains open.

## 1. Analytic Number Theory

The classical approach: study the zeta function directly and try to
prove that all non-trivial zeros lie on the critical line `Re(s) = 1/2`.

| Result | Author(s) | Year | Statement |
|:---|:---|:---|:---|
| Infinitely many zeros on the critical line | Hardy | 1914 | At least infinitely many zeros satisfy `Re(ρ) = 1/2` |
| Positive proportion on the critical line | Levinson | 1974 | At least 1/3 of zeros on the critical line |
| Improved proportion | Conrey | 1989 | At least 40 % of zeros on the critical line |
| Improved proportion | Pratt, Robles, Zaharescu, Zeindler | 2020 | At least 41.6 % of zeros on the critical line |
| Improved proportion (AI-assisted) | Anthropic + human mathematicians | 2026 | At least 67.2 % of zeros on the critical line |

**Key insight:** These results prove that a large fraction of zeros lie
on the critical line, but they do **not** prove that *all* zeros do.

## 2. Spectral Theory (Hilbert–Pólya Conjecture)

The idea: find a self-adjoint (Hermitian) operator whose eigenvalues are
the imaginary parts of the non-trivial zeros. Since eigenvalues of a
self-adjoint operator are always real, this would immediately prove RH.

| Result | Author(s) | Year | Statement |
|:---|:---|:---|:---|
| Pair correlation of zeros = GUE statistics | Montgomery | 1972 | The gaps between zeros follow the Gaussian Unitary Ensemble |
| Numerical confirmation | Odlyzko | 1987 | Verified GUE statistics to extraordinary precision |
| Hamiltonian candidate `H = xp` | Berry & Keating | 1999 | Formal resemblance, but not self-adjoint on a standard Hilbert space |
| Non-commutative geometry | Connes | 1999 | Zeta zeros as spectrum of an operator on the adele class space |
| Adele class space as a hyperring | Connes & Consani | 2011 | The adele class space has a natural algebraic structure |

**Key insight:** The statistical distribution of zeros matches quantum
chaotic systems, suggesting a deep connection to physics. But no explicit
self-adjoint operator has been constructed whose spectrum is exactly the
zeros.

## 3. Function Field Case

Over function fields (finite extensions of `F_p(t)`), the Riemann
Hypothesis has been **proven**.

| Result | Author(s) | Year | Statement |
|:---|:---|:---|:---|
| RH for function fields | Weil | 1940s | Proven using algebraic geometry |
| Castelnuovo positivity | Castelnuovo | 1890s | The key positivity criterion |

**Key insight:** In the function field case, the analogue of RH follows
from a **positivity condition** (Castelnuovo's inequality). In the number
field case, no such positivity criterion has been found.

## 4. p-adic Riemann Hypothesis

Over the p-adic numbers, an analogue of RH has been **proven**.

| Result | Author(s) | Year | Statement |
|:---|:---|:---|:---|
| p-adic RH | Dwork | 1960 | Proven using p-adic analysis |

**Key insight:** The p-adic world has a different metric, in which the
primes are structurally embedded. This suggests that a **global**
non-archimedean structure might be the key to the classical RH.

## 5. Failed Proof Attempts

Many mathematicians (and amateurs) have claimed to prove RH. The most
prominent failed attempts:

| Attempt | Author | Year | Outcome |
|:---|:---|:---|:---|
| Proof via the fine structure constant | Atiyah | 2018 | Rejected by the mathematical community |
| Various preprints on arXiv, Zenodo, etc. | Anonymous | ongoing | Usually contain hidden circular reasoning |

**Key insight:** RH is notoriously difficult to prove. Most failed attempts
contain subtle errors, often circular reasoning or unproven assumptions.

## 6. Open Questions

1. Why is RH provable in the function field case but not in the number
   field case?
2. What is the role of Castelnuovo positivity?
3. Is there a global positivity criterion for the number field case?
4. Can a new number system (like the p-adic numbers) embed the primes
   structurally and force the critical line?
5. Does the Euler product structure uniquely determine the location of
   the zeros?

## 7. AI-Assisted Progress (2026)

| Result | Institution | Year | Statement |
|:---|:---|:---|:---|
| Lower bound raised to 67.2 % | Anthropic | 2026 | AI-assisted proof of a stronger partial result |
| Formal verification in Lean 4 | Anthropic + collaborators | 2026 | The partial result was formalized in Lean 4 |

**Key insight:** AI can produce meaningful partial results, but a full
proof of RH remains open.

## 8. Conditional Convergence of the Explicit Formula

The Riemann explicit formula
    π(x) = Li(x) − Σ_ρ Li(x^ρ) + (smaller terms)
is **only conditionally convergent**. The sum over the zeros does not
converge absolutely, and naive summation in ascending order of Im(ρ)
can cause the approximation error to grow rather than shrink.

For numerical work, two approaches are common:
1. **Gaussian regularization**: multiply each term by exp(-(γ·σ)²).
   This ensures convergence but damps the contributions of higher zeros,
   which are needed for accuracy at larger x.
2. **Test functions with compact support**: used in the theoretical
   literature (e.g., Weil's explicit formula) to control convergence.

This framework uses approach 1 for visualization purposes. The
numerical tests do **not** assert monotonic convergence, because
that would be mathematically incorrect.

## 9. References

- Riemann, B. (1859). *Über die Anzahl der Primzahlen unter einer gegebenen Größe*.
- Montgomery, H. L. (1973). *The pair correlation of zeros of the zeta function*.
- Connes, A. (1999). *Trace formula in noncommutative geometry and the zeros of the Riemann zeta function*.
- Clay Mathematics Institute. *Millennium Problems: Riemann Hypothesis*.