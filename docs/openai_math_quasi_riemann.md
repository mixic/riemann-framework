# OpenAI Math: quasi-Riemann results (family 003)

This project tracks the Riemann-related material in
[`openai/math`](https://github.com/openai/math), family 003, at upstream revision
[`fd4aeeb`](https://github.com/openai/math/commit/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb).
The upstream repository describes these as research results at different
stages of verification; this page records their claims and formalization scope,
not an endorsement or an independent proof.

## Manuscripts

Family 003 lists three manuscripts:

1. [The Quasi-Riemann Hypothesis: A Zero-Free Half-Plane Re(s) > 7/8](https://github.com/openai/math/blob/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb/preprints/The-Quasi-Riemann-Hypothesis-September-30-2026/paper.pdf)
   claims zero-freeness for the Riemann zeta function and Dirichlet
   L-functions to the right of 7/8, and for finite-order Hecke L-functions
   over Q(sqrt(-3)).
2. [Uniform exclusion of Landau-Siegel zeros](https://github.com/openai/math/blob/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb/preprints/Uniform-exclusion-of-Landau-Siegel-zeros-October-1-2026/paper.pdf)
   claims a uniform logarithmic gap from 1 for real zeros of primitive,
   nonprincipal real Dirichlet L-functions.
3. [The Quasi-Riemann Hypothesis (alternate 11/12 proof)](https://github.com/openai/math/blob/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb/preprints/The-Quasi-Riemann-Hypothesis-October-5-2026/paper2.pdf)
   claims a zero-free half-plane to the right of 11/12.

The upstream [family scope note](https://github.com/openai/math/blob/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb/lean/docs/003.md)
describes Lean coverage for the 7/8 result and the uniform real-zero gap. It
does not list a separate formalization of the alternate 11/12 proof.

## Lean artifacts and verification limits

The upstream [comparator challenge](https://github.com/openai/math/blob/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb/lean/ComparatorChallenges/QuasiRiemannHypothesis.lean)
contains the zeta nonvanishing theorem statement with `sorry`; it is a target,
not a proof. The configured solution points to
[`OAI.NumberTheory.DirichletL.Nonvanishing`](https://github.com/openai/math/blob/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb/lean/OAI/NumberTheory/DirichletL/Nonvanishing.lean),
which imports a substantial dependency tree in the upstream Lean project.
Merely compiling the comparator target would therefore not verify the claimed
result. A meaningful Lean check must build the configured solution and check
its axioms and dependencies, not only the challenge file.

This repository does not currently import or vendor that upstream proof tree.
Its Lean toolchain is pinned to 4.34.0-rc2, while upstream pins 4.34.1; keep
their builds separate unless and until the toolchain and dependency closure
have been deliberately reconciled. Numerical tests of known zeta zeros do not
verify a zero-free theorem or the manuscript arguments.

These claims are narrower than RH and do not prove RH. They are recorded as
external claims pending independent verification; they do not change this
project's RH status or its GPL-3.0 license.
