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

## 3. Examples of Formal Verification

| Project | Claim | Status |
|:---|:---|:---|
| Zeta23 (Anthropic) | >2/3 of zeros on the critical line | Serious partial result, Lean-verified |
| Lean-Verified 67.251% | 67.25126275289546 % of zeros on the critical line | Serious partial result, Lean-verified |
| apollonian-wave | Full RH proof | Highly speculative, not accepted |
| ARK Riemann Hypothesis | Full RH proof | Highly speculative, not accepted |
| Bost-Connes Modular Generator | RH as type inhabitation problem | Conditional proof, unconstructed object |

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