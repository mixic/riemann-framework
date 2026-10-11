# How an RH Proof Is Checked

This document describes the process by which a claimed proof of the
Riemann Hypothesis is verified.

## 1. Formal Criteria (Clay Mathematics Institute)

The Clay Mathematics Institute (CMI), which offers a $1 million prize
for a proof of RH, has strict rules:

| Criterion | Description |
|:---|:---|
| **Publication** | The proof must appear in a "Qualifying Outlet" – a peer-reviewed mathematical journal |
| **Two-year waiting period** | At least two years must pass after publication |
| **General acceptance** | The proof must be accepted by the global mathematical community |
| **No direct submission** | Direct submission to CMI is not possible |

Only when all three criteria are met can the CMI's Scientific Advisory
Board (SAB) convene a special committee to examine the proof.

## 2. Technical Verification

### 2.1 Traditional Peer Review

Other experts in analytic number theory read the proof and check every
statement, equation, and logical step for correctness and gaps.

**Strengths:** Catches conceptual errors, verifies mathematical meaning.
**Weaknesses:** Slow, subjective, can miss subtle errors.

### 2.2 Formal Verification with Proof Assistants

The proof is translated into a formal language like **Lean 4** and
checked by a computer for logical correctness. Every step must be
formally proven.

**Strengths:** Eliminates logical errors, fully rigorous.
**Weaknesses:** Cannot guarantee the formal translation is correct,
cannot verify mathematical meaning.

**Key checks:**

| Check | Tool | What it detects |
|:---|:---|:---|
| Compilation | `lake build` | Syntax and type errors |
| `sorry` detection | `grep "sorry"` or Lean output | Incomplete proofs |
| Axiom analysis | `#print axioms` | Hidden assumptions / circular reasoning |
| Dependency check | `#print axioms riemann_hypothesis` | Which axioms the main theorem depends on |

**Warning:** A Lean proof that compiles without `sorry` and without
arbitrary axioms is **necessary** but **not sufficient** for acceptance.
It must also be understood and accepted by mathematicians.

### 2.3 What Computation Can and Cannot Decide

Sections 2.1 and 2.2 are about checking a proof once one exists. This subsection
is about what a computation establishes on its own, because "numerical evidence"
is not one thing and the differences are decisive.

**Direction of the implication.** A finite computation refutes or supports
according to which way the implication runs, and the two are not symmetric. RH
implies that Weil's Hermitian form is positive semidefinite, and a principal
submatrix of a PSD matrix is PSD, so *every* finite compression of that form is
PSD — meaning one negative eigenvalue of a correctly constructed compression
**refutes RH**. Likewise RH is equivalent to `Lambda = 0` for the de Bruijn–Newman
constant, so one non-real zero of `H_t` with `0 < t < 0.2` **refutes RH**. Both are
finite, checkable, and sensitive to a single off-line pair. Their converses are
worth nothing: a positive compression proves nothing, because a compression is
positive whenever its subspace happens to miss the negative directions, and a
finite test family cannot exhaust the space. See
[`../ideas/weil_positivity_finite_compression.json`](../ideas/weil_positivity_finite_compression.json)
and [`../ideas/de_bruijn_newman_first_exit.json`](../ideas/de_bruijn_newman_first_exit.json).

**Method-level insensitivity, which is stronger than finiteness.** The usual reason
given for why ten trillion verified zeros settle nothing is that RH speaks about
all zeros. There is a sharper reason and it concerns *methods* rather than
finiteness: Alpöge and Furman record that their inputs are insensitive to `o(N)`
off-line zeros and hold for Davenport–Heilbronn and Epstein zeta functions, for
which the analogue of RH is false. No pair-correlation, mollifier, density or
random-matrix argument can therefore reach RH at any `N`, however good its
constants become. The proportion results in section 3 are serious mathematics and
they are provably not a route to RH.

**Finite claims, where computation is the gold standard.** The operative
distinction is not "evidence versus proof" but whether the claim is finite. For
finitely many instances, exact verified computation *is* proof:
`prime_certificate.py` certifies that the first million primes are exactly the sieve
output and that none is missing — deterministic Miller–Rabin over a proven base set
(bases 2..37 are sufficient below 3.317e24, and these values are under 1.6e7), two
independently implemented sieves that must agree, a direct check of the sieve
invariant, and the published landmark `p_1000000 = 15485863`. That is a proof of a
finite claim rather than evidence for it, and it carries a digest so a later run
elsewhere can be compared. The RH work in this repository is not of that kind and
cannot be.

## 3. Examples of Formal Verification

| Project | Claim | Status |
|:---|:---|:---|
| Zeta23 (Anthropic) | >2/3 of zeros on the critical line | Serious partial result, Lean-verified |
| Lean-Verified 67.251% | 67.25126275289546 % of zeros on the critical line | Serious partial result, Lean-verified |
| apollonian-wave | Full RH proof | Highly speculative, not accepted |
| ARK Riemann Hypothesis | Full RH proof | Highly speculative, not accepted |
| Bost-Connes Modular Generator | RH as type inhabitation problem | Conditional proof, unconstructed object |

**A discrepancy in this table.** The first two rows appear to record the same result
with different constants. `2/3` improved by the Montgomery–Taylor window is
`2 - c_MT^{-1}` with `c_MT^{-1} = 1/2 + (1/sqrt2)cot(1/sqrt2)`, which is
`0.6725007...`, i.e. `67.25007037%`. The second row gives
`67.25126275289546%`, which does not match, and its fourteen figures look
transcribed from a numeric literal rather than derived.
`proportion_certificates.montgomery_taylor_constants()` reproduces `0.6725007037`
exactly, is tested, and agrees with both papers read for
[`claimed_proof_triage.md`](claimed_proof_triage.md). Whichever row is wrong, they
cannot both be right. Flagged rather than edited, because the source of the second
figure is not recorded here.

## 4. What a Proof Would Achieve

| Aspect | Consequence |
|:---|:---|
| **Binary truth** | RH is either proven or not – no middle ground |
| **Prime distribution** | Gives the smallest possible error term in the prime number theorem |
| **Other problems** | Does not automatically solve unrelated problems |
| **New mathematics** | Likely requires fundamentally new ideas |

## 5. The Role of AI

AI can assist in verification in several ways:

| Task | Tool | Status |
|:---|:---|:---|
| Numerical verification of zeros | `mpmath`, `pytest` | Fully automated |
| Lean compilation | `lake build` | Fully automated |
| `sorry` detection | Output parsing | Fully automated |
| Axiom analysis | `#print axioms` | Fully automated |
| Circular reasoning detection | Heuristics | Partially automated |
| Mathematical validity of new theories | Human review | Not automatable |
| Proof search | TreeThink + LLM | Heuristic, no guarantee |

## 6. References

- Clay Mathematics Institute. *Millennium Problems: Riemann Hypothesis*.
- Lean Prover Community. *Mathlib4 Documentation*.
- Anthropic. *Zeta23: Formal verification of a partial result on RH* (2026).
- Devlin, K. *What Is Experimental Mathematics?* — on numerical evidence,
  confidence, and why neither amounts to proof. Section 2.3 refines rather than
  restates its thesis: the decisive axis is the direction of the implication and
  the finiteness of the claim, not the quantity of evidence.