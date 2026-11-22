# Independent verification report: the November 2026 RH/GRH claims

**Scope.** An audit of two artifacts announced on 20 November 2026: Levent Alpöge's Lean 4
formalisation of the Riemann Hypothesis and of GRH for Dirichlet L-functions, and Alessandro
Maria Masullo's 940-page typescript *The Music of the Primes*. The work is split into a formal
audit of the Lean archive (Phase 1) and numerical/symbolic tests of two disputed steps in the
typescript (Phase 2).

**What this report is not.** It does not adjudicate the Riemann Hypothesis. It reports what
specific instruments returned on specific inputs, with the trust base of each instrument named.
"VERIFIED" below always means "the named check ran on this machine and accepted", never "the
mathematical claim is true".

**Environment.** Windows 11, Intel Core Ultra 9 285K, 24 logical CPUs, 63.3 GB RAM, 746 GB free
disk, `git` 2.55, `curl` 8.x, Python 3.14.7 (`mpmath` 1.3.0, `sympy` 1.14.0, `zstandard` 0.25.0).
Lean toolchains: `leanprover/lean4:v4.34.0-rc2` (pre-existing) and `leanprover/lean4:v4.36.0`
(installed for this audit, commit `611c117b`).

---

## 1. Verdicts at a glance

| # | Sub-claim | Verdict | How it was checked |
|---|---|---|---|
| 1 | The five headline theorems depend only on standard Lean axioms | **VERIFIED** | streaming scan of the 61.5 GB published export: exactly 3 axiom declarations, `propext`, `Quot.sound`, `Classical.choice`; zero `sorryAx` |
| 2 | The archive contains no `sorry` and declares no axioms of its own | **VERIFIED** | git-wide text scan of 164,283 modules: 5 `sorry`, all in the Comparator-only `Challenge.lean`; 0 `axiom`/`constant`/`opaque` declarations |
| 3 | The theorems prove Mathlib's statements, not look-alikes | **VERIFIED** | independent statement comparison (`con-leche --compare`): all five "justified by the solution"; source-level identity of `Statements.lean` and `Challenge.lean` definitions |
| 4 | The proof is accepted by an independent checker | **VERIFIED** | `con-leche --verified` on the full export: 1,468,418 declarations accepted, exit 0, 9.5 min on 20 workers |
| 5 | Nielsen's vacuity objection decides the archive | **INCONCLUSIVE** | not tested here; it is a claim about the *meaning* of intermediate definitions, not about the term |
| 6 | Masullo §1.4.3: the Archimedean integrals have a common bound `A` independent of `z` **and of φ** | **REFUTED as stated** | the bound holds in `z` at fixed φ, but grows as `log(1/δ)` along the very family φ the draft defines; measured slope 0.9999 |
| 7 | Masullo §1.4.3, narrowed to uniformity in `z` at fixed φ | **VERIFIED** (narrower claim) | integral bounded (0.18–2.87) over the sampled `z` grid |
| 8 | Masullo §1.3.2: the F-stratum **equals** the norm pre-image of the Q-stratum | **REFUTED as an identity** | exact integer counterexample at every split prime tested (6/6); ramified primes are a control that cannot cancel |
| 9 | Chapter-wide inequality/sign fuzz of the typescript | **NOT DONE** | out of this session's reach; see §3.4 |

Two of the four Phase-1 claims that the MIT verification page lists as still running at the time
of the record were settled here by substitution: `lake comparator` was replaced by
`con-leche --compare` (which implements the same record-by-record statement matching), and the
Lean-kernel replay of the export by `con-leche --verified`. Neither substitution is equivalent to
Lean's own kernel; see §2.6.

---

## 2. Phase 1 — formal audit of the Alpöge archive

### 2.1 Provenance and integrity

The mirror named in the brief (`Deicyde/riemann-hypothesis`) now redirects to
`leanprover-community/riemann-hypothesis`. I cloned it at depth 1:

| Item | Value |
|---|---|
| Commit audited | `2dea99006976a5104032e495d7513dee40fbb5ca` (2026-11-22 18:30 +1100, merge of PR #72) |
| `lean-toolchain` in the archive | `leanprover/lean4:v4.33.1` |
| Mathlib pin (`lake-manifest.json`) | `0df444a360eaa60ab8c11dca51a86af692955474` (tag `v4.33.1`) |
| Lean / exporter recorded in the export header | `4.33.1`, githash `819816b2e0a3bf405af45ae5c7af2491d8f5bee6`; `lean4export` 3.1.0 |
| Modules under `src/` at this commit | 164,283 `.lean` files, 931.2 MB (git blob sizes) |
| Original submission | committed as `40e56bab`; the archive's README states the cleanup removed 10,724 of its 175,187 files |

The 175,187 figure in the MIT page counts *all compiled modules* including Mathlib and Lean core;
the submission tree itself is the 164,283 above after cleanup. Both numbers are consistent with
the README's account and I use each for what it measures.

Every byte I checked was hash-verified against the publisher's `SHA256SUMS`:

| Artifact | Size (bytes) | SHA-256 | Result |
|---|---|---|---|
| `challenge.ndjson.zst` | 46,881,299 | `c24ef99d…2f678ac6` | matches |
| `challenge.ndjson` (unpacked) | 350,862,311 | `bd484ac9…dd6ab2b9` | matches |
| `solution.ndjson.zst` | 7,699,933,588 | `61a8938a…81b05381` | matches |
| `solution.ndjson` (unpacked, 61.5 GB) | 61,570,595,788 | `5ea74b91…f6be244e` | matches |
| `audit.log` | 2,062 | `0a1473fc…38d87a62` | matches |
| `comparator.json` | 460 | `8ea890e6…5b1582ff` | matches |

So the objects checked below are the objects the MIT page published, byte for byte. That is a
statement about transfer integrity, not about the proof.

### 2.2 Axioms — checked against the artifact, not the log

Three independent readings agree:

1. **Source scan.** A git-wide text scan of the 164,283 modules finds no line that declares
   `axiom`, `constant` or `opaque`, zero word-bounded `admit`, and exactly five `sorry` tokens,
   all in `src/Challenge.lean` (lines 19–27), the file the lakefile marks as adding "for
   Comparator; it is not part of the submission". Four `#print axioms` diagnostics exist in
   Formalism modules. (A line-anchored scan would miss a declaration behind attributes; the
   export scan below is what rules that out.)
2. **Export scan (executed here).** Streaming the 61.5 GB solution export and resolving its intern
   table yields **exactly three axiom declarations** — `propext`, `Quot.sound`,
   `Classical.choice` — and **zero occurrences of `sorryAx`**. This is stronger than a per-theorem
   dependency query for these five theorems: no other axiom exists in the object at all.
3. **Published audit.** `audit.log` reports the same three axioms for each of the five theorems
   against an environment of 15 (all in `Init`, including `sorryAx`, which the theorems do not use).

The three readings have different weights: (2) is executed on the artifact, (1) is executed on the
source, (3) is a document I hashed but did not produce. The agreement is the interesting part.

### 2.3 Statement fidelity

`src/Statements.lean` defines four `Prop`s (`RiemannZetaZerosOnLine`,
`DirichletLNonvanishingRightOfHalf`, `DirichletLZerosOnLine`, `PrimitiveDirichletLZerosOnLine`);
the Comparator challenge file contains the same four definitions, textually identical after
whitespace normalisation. The headline theorem is stated with Mathlib's own definition:

```lean
-- src/Statements.lean imports Mathlib.NumberTheory.LSeries.DirichletContinuation
theorem riemannHypothesis : RiemannHypothesis := rhOfAll     -- Main.lean
-- Mathlib: ∀ s, riemannZeta s = 0 → (¬∃ n, s = -2*(n+1)) → s ≠ 1 → s.re = 1/2
```

The executed check is `con-leche --compare challenge.ndjson solution.ndjson`, which checks the
solution, then checks the challenge accepting each of its axioms only if the solution holds a
constant of that name whose type is the same record by record. Result: `accepted 51692
declarations, 5 axioms justified by the solution`, with all five theorems named individually
(`riemannHypothesis`, `riemannZeta_eq_zero_re`, `LFunction_ne_zero_of_half_lt_re`,
`LFunction_eq_zero_re`, `LFunction_eq_zero_re_of_isPrimitive`). This is the check that rules out
"proved a different theorem" as the failure mode.

### 2.4 Independent kernel replay

`con-leche` (branch `compare`, commit `274f0138`, built from source with Lean 4.36.0 in 2 min,
594 jobs) re-checked the exported proof:

```
con-leche: checking: 1468418 declarations on 20 workers t=95.9s
con-leche: check done: 1468418 declarations t=561.6s (check 465.7s)
con-leche: done: parse 95.9s, check 465.7s, 20 workers t=561.6s
```

Exit 0, peak RSS ≈ 34.4 GB, 99.8% worker busy. **Negative control:** the same binary on the
challenge export alone rejects it —

```
con-leche: not implemented yet: use of the sorryAx axiom in value of riemannHypothesis
exit 2
```

— so acceptance is not vacuous. **Positive control:** the challenge's 51,692 declarations are then
accepted in 1.0 s once the solution justifies them.

One divergence from the MIT page must be recorded: it cites branch `compare` at `5dc36dc1`; the
branch head I built is `274f0138` (later, "task #627"). The checker therefore differs from theirs
by some commits, although the declaration counts it reports (1,468,418 and 51,692) coincide.

Note that lean4export is a *name-based, kernel-level* export: checking it exercises definitional
equality as recorded, not Lean's elaborator. It does not check the `.olean` binaries and does not
re-elaborate the 17 million lines.

### 2.5 Dependency map

Parsing 842,901 `import` lines and taking the transitive closure of the three roots
(`Main`, `Statements`, `Supplements.Kernels.MainTheorems`):

| Measure | Value |
|---|---|
| Modules reachable | 163,852 of 163,893 parsed (99.98%); 390 of the 164,283 files contain no `import` line and are leaves |
| Maximum import depth | 42 |
| By package | Development 130,642 · Formalism 18,246 · GroundTheory 8,499 · ReciprocityTheory 3,843 · CompanionTheory 2,024 · PositivityTheory 423 · Lemmata 167 · BuildAid 5 |
| External roots imported | Mathlib 141,555 edges; Lean core 12; Batteries 3 |

`src/Main.lean` is 12 lines: five aliases (`rhOfAll`, `allChi`, `claimAll.2.1`, `critAll`) whose
definitions sit in `src/Supplements/Kernels/MainTheorems.lean`, which reduces everything to
`UpperTheory.FinalTheorems.everyCharacter` and `Formalism.VW.rh_of_every`. The submission is
therefore not modular in the sense a reader might hope: the closure is essentially the whole
library, and the content is concentrated at one kernel module and one upper-theory theorem.

### 2.6 What this establishes, and the trust base

Established, on this machine: the published proof object is the published one (hashes), it uses
only the three standard axioms, it contains no `sorryAx`, it proves the five stated theorems, and
an independent checker implementing the kernel's rules accepts it.

Not established, and not claimed: that the mathematics is a proof of RH in any journal sense.
The kernel check relativises to Lean's logic, to Mathlib's definitions of `riemannZeta`,
`DirichletCharacter.LFunction` and `IsPrimitive`, and to the correctness of the two kernels
involved. In particular:

- **Mathlib's definition is not vacuous.** It is a well-formed predicate on `ℂ` naming
  `riemannZeta`; it is not `True`. A term inhabiting it is a proof of that formal statement.
- **Nielsen's objection is about meaning, not typing.** Her claim (13 pp., 2026-11-20) is that
  intermediate geometry/lattice predicates are discharged vacuously. Such a defect can make an
  *intermediate theory* empty, but it cannot by itself invalidate a kernel-accepted term of
  Mathlib's `RiemannHypothesis`, because that statement does not mention the disputed predicates.
  It can still make the archive's own theory carry no mathematics, which is the question the
  MIT page's "scope" row does not address. I did not run her dependency trace, and the
  identifier conflict recorded in `docs/alpoge_nielsen_dispute.md` (her `geoDegenerate` vs the
  third-party audit's report of only `nondegenerate` in the tree) is still unresolved here.
- **Substitutions.** I did not run `lake comparator` (needs Lean 4.36.0 plus ~100 GB RAM for the
  62 GB export; this machine has 63.3 GB), `nanoda`, or `leanchecker`, and I did not rebuild the
  library to print axioms locally. `con-leche` was used for the two checks those would have
  covered; it is one independent implementation, not three.

---

## 3. Phase 2 — Masullo, *The Music of the Primes*

Source: `masullo_music_of_the_primes_2026-11-20.pdf`, 940 pp., 6,756,996 bytes, SHA-256 prefix
`e039d3f6cf0a4b14`, archived in `references/`. Section and page numbers below are the printed ones.

### 3.1 §1.4.3 "Montel's Theorem" — the Archimedean bound

**Claim, quoted (p. 29; repeated verbatim as §1.8.4.3 on p. 54):**

> The integrals […] are bounded above by a common constant A > 0 **independent of z ∈ K and
> independent of the specific φ**.

**Data that fix the model (§1.4.2, p. 28):** φ_z(t) = t^{−z} for t > 1, φ_z(t) = 0 for t ∈ (0,1),
φ_z(1) = 1/2; φ_{h,ε,z} = h(t)(ρ_ε ∗ φ_z)(t), with h a bump function supported over (1,+∞),
valued in [0,1], "below 1_{(1,+∞)}, converging pointwise monotonically" to it; assumption (1) of
§1.4 makes φ smooth and compactly supported, so the t-integral has a finite cutoff T.

With |χ_v| = 1 the real-place term is

```
I(σ, δ) = ∫_{1+δ}^{T} t^{-σ-1/2} / (t-1) dt ,      z = σ + iτ
```

because |t^{−z}| = t^{−σ} and |t|^{1/2} dt/t = t^{−1/2} dt. The kernel 1/(t−1) is not integrable
at t = 1, and the draft imposes no vanishing of φ at t = 1: only the support condition, which each
h satisfies by vanishing on a *neighbourhood* of 1. Any monotone family h → 1_{(1,+∞)} must shrink
that neighbourhood to zero, so monotone convergence gives

```
sup over the family of I(σ, δ) = ∫_1^T t^{-σ-1/2}/(t-1) dt = +∞.
```

**Measurements** (mpmath, 30 digits, `scripts/audit/masullo_archimedean.py`):

| σ (fixed φ, δ = 0.25) | \|I\| |
|---|---|
| 0.00 | 2.867270 |
| 0.25 | 2.063268 |
| 0.50 | 1.609338 |
| 1.00 | 1.098416 |
| 2.00 | 0.621389 |
| 5.00 | 0.180161 |

| δ = 2^{−k} | \|I\| | log(1/δ) | \|I\| − log(1/δ) |
|---|---|---|---|
| 2^{−1} | 0.659438 | 0.693147 | −0.0337 |
| 2^{−4} | 2.249139 | 2.772589 | −0.5234 |
| 2^{−8} | 4.937316 | 5.545177 | −0.6079 |
| 2^{−12} | 7.704426 | 8.317766 | −0.6133 |
| 2^{−16} | 10.476671 | 11.090355 | −0.6137 |

Fitted slope d|I|/d log(1/δ) over the last decade: **0.9999**; the offset converges to ≈ −0.6137,
so |I| = log(1/δ) + O(1) exactly as the divergence argument predicts. The complex-place term,
whose singularity is two-dimensional and integrable, stays bounded over the same grid (1.62 at
δ = 2^{−12}, spread 0.85), which locates the defect in the real-place kernel rather than in the
character or the place. A 60-point randomised sweep over (σ, δ) reaches 10.0008, again at small δ.

**Verdict.** The claim is **REFUTED as stated**: the family is bounded in `z` at fixed φ (row 7 of
§1) but not in φ, so no single `A` exists. This is a quantifier/limit-interchange defect, not a
numerical accident: it is forced by the 1/(t−1) singularity and the requirement h ↑ 1_{(1,+∞)}.
The narrower statement the draft needs for Montel — uniformity in `z` on a compact `K` at *fixed*
test function — survives; what does not survive is extracting the h → 1 limit (used in §1.4.4 to
recover L′/L) while keeping the bound.

### 3.2 §1.3.2 — the norm-preimage identification of the strata

**Claim, quoted (pp. 25–26):**

> the stratum GL₁(𝔸_F)^{P_k} is the pre-image under the norm map GL₁(𝔸_F) → GL₁(𝔸_Q) of the kth
> divisorial stratum on GL₁(𝔸_Q),

with the explicit form GL₁(𝔸_F)^{P_k} = {g : g_v ∈ O^×_{F_v} for all v ∈ ⋃_{p∈T_k} S_p}, where
T_k is the first k rational primes.

**Construction.** Let p split in a quadratic field F, p = p₁p₂, and take the idele
`g_{p₁} = p`, `g_{p₂} = 1/p`, all other components 1. Then the local absolute values are p^{−1}
and p, and

```
N(g)_p = g_{p₁} · g_{p₂} = 1,
```

so N(g) is the identity idele of 𝔸_Q^×, a unit at every place and hence in *every* Q-stratum T_k.
But g is a non-unit above p, so g ∉ P_k once p ∈ T_k. Therefore N^{−1}(T_k) strictly contains
GL₁(𝔸_F)^{P_k}, i.e. the identification fails in one direction. The computation is exact (integer
arithmetic, no floating point); `scripts/audit/masullo_idele_strata.py`:

| Field | p | behaviour | N(g)_p | norm unit | in preimage | in stratum | violates |
|---|---|---|---|---|---|---|---|
| Q(√5) | 11 | split | 1 | yes | yes | no | **yes** |
| Q(√5) | 19 | split | 1 | yes | yes | no | **yes** |
| Q(√5) | 29 | split | 1 | yes | yes | no | **yes** |
| Q(√2) | 7 | split | 1 | yes | yes | no | **yes** |
| Q(√−3) | 7 | split | 1 | yes | yes | no | **yes** |
| Q(√−3) | 19 | split | 1 | yes | yes | no | **yes** |
| Q(√5) | 5 | ramified | 25 | no | no | no | no |
| Q(√−3) | 3 | ramified | 9 | no | no | no | no |

**Control.** At ramified p the local norm is N_{F_v/Q_p}(g) = g², so a unit norm forces a unit
component and the cancellation is impossible: the phenomenon is exactly a split-prime phenomenon,
which is why the counterexample is structural rather than a numerical coincidence.

**Correction to the brief.** p = 5 is *ramified* in Q(√5) (disc 5, 5 = (√5)²), not split; the
split primes there are 11, 19, 29, …. The construction is run on those, and 5 is kept as the
ramified control.

**Verdict.** **REFUTED as an identity.** The inclusion P_k ⊆ N^{−1}(T_k) holds; the reverse
inclusion fails, so the stratum is strictly smaller than the pre-image. Whether the argument only
needs the inclusion (and the word "is" is loose) is a question about how the stratification is
used later; the plain reading of the sentence is false.

### 3.3 Fuzz of the disputed bound

A 60-point randomised sweep over (σ ∈ [0,3], δ ∈ [2^{−16},2^{−1}]) of the same integral gives
sup |I| = 10.0008 at δ = 3.6·10^{−5}. This is an amplification of §3.1, not independent evidence:
it re-samples the family whose divergence is already proved, and its value is only that it makes
the growth visible for readers who distrust the asymptotic argument.

### 3.4 Not done

- The PhilArchive critique (`philarchive.org/archive/NIEIOM`) is behind a Cloudflare challenge:
  HTTP 403 with a "Just a moment…" body on repeated attempts (page fetch and `curl` with a browser
  user-agent). Its argument was therefore not available as input, and the tests above were derived
  from the draft alone.
- No chapter-wide fuzz of intermediate inequalities and finite sums. That would need the specific
  bounds extracted from the relevant chapters with their hypotheses; sampling the ones I did not
  read would have produced numbers about my reconstruction rather than about the draft. §1.4.3 was
  chosen because it is stated sharply enough to be decided.

---

## 4. Reproduction

All commands were run from `C:\Users\Milan\Projects\riemann-audit`; the scripts are in
`scripts/audit/`.

```powershell
# provenance
git clone --depth 1 https://github.com/leanprover-community/riemann-hypothesis alpoge-lean
git -C alpoge-lean config core.longpaths true    # otherwise the checkout stops at 260 chars
git -C alpoge-lean checkout -f HEAD

# source-level facts (git plumbing: 41 s for 164,283 files)
git -C alpoge-lean grep -n -E '\bsorry\b|\bsorryAx\b' -- src
git -C alpoge-lean grep -n -E '^[[:space:]]*(axiom|constant|opaque)\b' -- src
git -C alpoge-lean grep -n -E '^[[:space:]]*(public )?import ' -- src > out/imports_raw.txt
python scripts/audit/lean_closure.py

# published artefacts and their hashes
curl -O https://math.mit.edu/~drew/grh/challenge.ndjson.zst
curl -O https://math.mit.edu/~drew/grh/solution.ndjson.zst      # 7.7 GB
python scripts/audit/decompress_export.py solution.ndjson.zst solution.ndjson
python scripts/audit/scan_export_axioms.py                        # 3 axioms, 0 sorryAx

# independent checker
git clone -b compare https://github.com/leanprover/con-leche
lake build con-leche                                              # Lean 4.36.0
con-leche --compare --jobs=20 challenge.ndjson solution.ndjson    # exit 0, 9.5 min
con-leche --verified --jobs=12 challenge.ndjson                   # negative control: exit 2

# Phase 2
python scripts/audit/masullo_archimedean.py
python scripts/audit/masullo_idele_strata.py
```

Key runtimes on this machine: clone 3 min (plus a 1 min re-checkout), 7.7 GB download 45 min at
1.6–4.4 MB/s (the host throttles single connections; 24 parallel ranges were used), decompression
2 min at 625 MB/s, export axiom scan 4 min, checker 9.5 min. JSON outputs are in `out/`:
`lean_closure.json`, `solution_axioms.json`, `masullo_archimedean.json`,
`masullo_idele_strata.json`.

---

## 5. Limits

1. **One checker, not three.** `con-leche` accepted the export; `nanoda`, `leanchecker` and
   `lean4lean` were not run. The MIT page reports all of them passing on the same object, but that
   is their result, not mine.
2. **No local build.** I did not compile the library (the archive's own cache is 4.94 GB and the
   full build is hours), so no `#print axioms` was run by me on `.olean` files. Everything about
   axioms comes from the export and the source, both of which I hashed or scanned myself.
3. **Statement comparison is only as good as the challenge.** `con-leche --compare` establishes
   that the solution proves the five statements that `challenge.ndjson` states; that the challenge
   states Mathlib's `RiemannHypothesis` is visible in the file and in Mathlib's source.
4. **Masullo's program is not refuted.** Two steps are shown to fail as written: a uniform bound
   used for a limit extraction, and a set-theoretic identification of strata. Neither shows the
   trace-formula strategy cannot work, and I did not attempt to repair either step.
5. **What the Phase-1 result is, and is not.** The formal statement of RH as it appears in Mathlib
   is proved by this archive, modulo Lean's kernel, the three standard axioms, and Mathlib's
   definitions of ζ, of Dirichlet L-functions and of primitivity. Whether that counts as a proof of
   the Riemann Hypothesis in the ordinary mathematical sense turns on trusting those definitions
   and that kernel, which is a judgment this audit does not make and is not competent to settle.
   What the audit does establish is narrower and checkable: the term inhabits the stated type, no
   axiom beyond the standard three occurs anywhere in the 61.5 GB object, the statements are the
   ones the challenge names, and an independent checker accepts all 1,468,418 declarations. The
   `RH is open` line in `docs/claimed_proof_triage.md` §5 is a statement about this repository's
   own screening record and its numerics, and nothing here revises it; what is new is that for this
   archive the formal chain closes, and that Nielsen's objection is a claim about the meaning of
   intermediate definitions rather than about the term (§2.6).
