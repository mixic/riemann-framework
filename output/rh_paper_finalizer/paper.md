<!--
Riemann Framework
Copyright (C) 2026 MILAN NIKOLIC
-->

# From Kernel Acceptance to Mathematical Validity: A Reproducible Gap Analysis of the 2026 Alpöge Archive

**Milan Nikolić**
Independent Researcher
m_nikolic@yahoo.com

**Verdict:** `UNDETERMINED`
**Named computation:** `complete RH-GAP-CLOSER first`

## Abstract

Lean kernel acceptance and mathematical validity are related but different objects.
This paper distinguishes them through a dependency trace and a load-bearing mutation
analysis of a claimed Lean 4 formalisation. For the 2026 Alpöge archive, the available
pipeline does not yet execute C1-C4 on the published target. It therefore emits no
claim that RH is proved and no claim that the archive is mathematically valid. The
executed local control cross-validates C1 and C2 on
`RiemannFramework.geometry_is_vacuous`, agrees on a closure of four names, and leaves C4
unrun because no vacuous-analogue mutant was declared. The central empirical finding is
that kernel acceptance is necessary but not sufficient for semantic validity, and that
the distinction can be represented mechanically as reachability, load-bearing status,
and an explicitly named residual computation.

## 1. Introduction

The paper's central claim is epistemic: **kernel acceptance is a necessary but not
sufficient condition for mathematical validity.** A proof term may compile and have a
clean axiom audit while its definitions fail to carry the mathematics their names suggest.
Whether a particular term routes through such a definition is a per-declaration question
that can be tested by a transitive closure and targeted mutation.

The Alpöge archive is the first worked example of this general phenomenon, not a verdict
on RH. The framework is general and is intended for future Lean 4 claims of Millennium
Problem solutions.

## 2. The Alpöge Archive

The published record identifies a Lean library released on 20 November 2026, with 17.4
million source lines and 175,187 modules. The repository is recorded as Lean 4 v4.33.1
with dependencies on Mathlib alone. These are factual archive characteristics; they are
not a correctness result.

The 2026 snapshot used in the repository's records is commit `2dea990`, with Mathlib
`0df444a3`. A live public checkout may differ: the execution environment here reached
commit `1cc42d2` when attempting a fresh archive run.

## 3. The Lean Certification

On 21 November 2026, the Lean and Mathlib communities certified the term-level object:
the statement matches `Mathlib.RiemannHypothesis`, the proof term inhabits that type, the
build compiles, and the axiom set is
`{propext, Classical.choice, Quot.sound}`.

This establishes formal kernel acceptance. It does not establish that every definition
against which the term is typed carries the mathematics its name claims. This is not a
deficiency of the Lean community: Lean certifies exactly what Lean certifies.

## 4. Nielsen's Critique

Nielsen's *The Invalidity of Alpöge's Proposed Proof of the Riemann Hypothesis*,
20 November 2026, PhilArchive (NIEIOT-2), identifies four concrete findings:

1. `anyGeometry := True`, a predicate that is constantly true.
2. a degenerate geometric model in which sections are the whole field, norms and volumes
   vanish, and curves are points.
3. `hExpl6` is set to the height, and `h_eq := fun _ => rfl` proves that height equation
   by definition.
4. the degree statement fixing the line-bundle degree is unsatisfiable as stated.

Nielsen's strongest claim is:

> “The kernel verifies a derivation relative to the given definitions. It does not verify
> that these definitions carry the mathematics their names claim. Here they do not.”

Nielsen's analysis does not execute a transitive dependency trace, run a load-bearing
mutation probe, or produce a per-declaration classification. It reads source and
identifies candidates. This paper fills that computational gap only to the extent the
available archive and tools permit.

## 5. The Nikolić Screening Protocol

The protocol separates three questions:

| Question | Instrument | Verdict level |
|---|---|---|
| Does the term typecheck? | Lean kernel | term and axiom acceptance |
| Is a named declaration reachable? | C1/C2 transitive closure | reachability |
| Does vacuity survive a targeted mutation? | C4 load-bearing probe | load-bearing status |

The six verdict values are `rejected`, `outside domain`, `undetermined`,
`validated (finite)`, `validated (elementary)`, and `validated (term)`.
No value means that RH is true.

## 6. The Tooling Stack

**C1: `#deps`.** A fixed-point forward closure over
`Expr.getUsedConstants`, iterating over both the type and value of reached declarations.
`#print axioms` is not a substitute because it reports axioms, not declaration reachability.

**C2: the second closure.** The specified independent extractor is `laud graph`.
That tool is unavailable here, so C2 uses the repository's `#depsm` structural recursion.
The substitution is recorded rather than silently accepted.

**Lean Vacuity Check.** The semantic plugin described by the protocol is not available as
an executable in this environment. The implemented census is a textual heuristic for
`:= True` and `fun _ _ _ => True`; it is not treated as a semantic proof.

**`lean-proof-review`.** The repository implements the L1-L4 audit concept separately.
L1/L2 findings block the positive verdict and require explicit discharge.

**Mutation.** `laud mutate --run` is represented by the repository mutation runner.
The relevant operators are `VACUOUS_TRUTH`, `UNUSED_HYP`, and `BOUNDARY_SHIFT`. A
surviving rewrite means the target may not need the replaced content; a killed rewrite
means it does. An identity rewrite does not score content.

**Cross-validation.** C1 and C2 must agree exactly. A single extractor is insufficient
for the closure claim.

## 7. The Executed Trace

### 7.1 Local control

The control target `RiemannFramework.geometry_is_vacuous` has C1 and C2 available:

| Computation | Result |
|---|---|
| C1 `#deps` | 4 names: `Nat`, target, `vacuousGeometry`, `True` |
| C2 `#depsm` | same 4 names |
| C3 cross-validation | exact agreement |
| C4 mutation | not run as a vacuous-analogue mutation |

The control is a calibration of the trace, not a model of the published proof.
`vacuousGeometry` is red in the local graph only because it is literally `:= True`
and is reached by the target. C4 has not discharged it.

### 7.2 Published archive

The archive run was attempted. It did not return C1-C3 on
`Main.riemannHypothesis`: Windows path-length and missing/private-olean failures prevented
the build. C4 was not run. Therefore the published closure, cross-validation partition,
and load-bearing classification are not known by this pipeline.

The exact outputs are in `closure_deps.txt`, `closure_laud.txt`,
`closure_crossvalidated.json`, `load_bearing.json`, and the raw logs in `probe_logs/`.

### 7.3 Residual limits

The trace is syntactic: reachability does not prove load-bearing or mathematical vacuity.
The mutation test can distinguish some used hypotheses but cannot discriminate all
circularity from discrimination. The DH screen cannot tell discrimination from circularity,
and this protocol preserves that limitation.

## 8. The Verdict

**Protocol verdict:** `UNDETERMINED`

**Named computation:** `complete RH-GAP-CLOSER first`

The verdict is the only defensible output until C1-C4 complete on the real archive. It
does not settle Alpöge, Nielsen, or RH.

## 9. The General Claim

The central result is methodological and empirical: **kernel acceptance is necessary but
not sufficient for mathematical validity**. A clean axiom audit can coexist with vacuous
internal definitions. Per-declaration reachability and mutation turn that possibility into
a reproducible question.

The framework is general. The prediction is that future Lean 4 claims of open-problem
solutions may recur with clean kernels and contested definitions. Its value is to make
the contest mechanical rather than rhetorical.

## 10. Forward Programme

For the Alpöge archive, remaining work is C1-C4: a cross-validated closure, a
load-bearing classification of every flagged declaration, and an exact red/amber/
yellow/green graph. These computations must report only what the pipeline actually returns.

For the framework, apply the same process to Lean 4 claims concerning Navier-Stokes,
P versus NP, Hodge, and other Millennium Problem claims.

For the community, Lean 4 archives claiming open-problem solutions should ship a public,
machine-readable dependency manifest identifying load-bearing and vacuous declarations.

## 11. Falsification

The paper's central claim would be refuted if:

1. the cross-validated closure contains no definition that is both flagged and
   load-bearing under mutation;
2. an independent third-party replication using the artefacts and reproduction script
   produces a different closure or classification;
3. a published, peer-reviewed mathematical argument establishes that the disputed
   definitions are not vacuous in the sense claimed; or
4. an official statement from the Lean community, Mathlib, or the Clay Institute says that
   the 21 November 2026 certification was intended to settle mathematical validity rather
   than kernel acceptance.

## Appendix A: `#deps` Lean Script

The repository implementation is [`lean/RiemannFramework/DependencyTrace.lean`](lean/RiemannFramework/DependencyTrace.lean).
It exposes:

```lean
elab "#deps " n:ident : command => do
  let env ← Lean.getEnv
  let deps := closure env n.getId
  let names := deps.toList.map (fun name => toString name)
  logInfo m!"DEPS_BEGIN {n.getId}"
  logInfo m!"DEPS_COUNT {names.length}"
  for name in names do
    logInfo m!"{name}"
  logInfo m!"DEPS_END"
```

The complete implementation includes `closure`, `visit`, `usedConstantsManual`,
`visitManual`, `closureManual`, and `#depscmp`.

## Appendix B: `laud graph` Invocation

The specified invocation is:

```sh
laud graph src --entry RiemannHypothesis --tree --max-depth 20
```

This environment has no `laud graph`; C2 substitutes `#depsm` and records the substitution
in every artefact.

## Appendix C: Mutation Probe Configuration

The configuration record is `claims/alpoge_2026.json`. The archive mutant is
`flip-anygeometry-on-the-published-archive`, a `CONTENT_FLIP` mutant, and is
**NOT CHECKED HERE** until the exact source anchor is established.

The local negative and positive controls are:

```lean
def vacuousGeometry (_D _J _X : Nat) : Prop := True
theorem geometry_is_vacuous : ∀ D J X : Nat, vacuousGeometry D J X :=
  fun _ _ _ => trivial
```

The mutation operators named by the protocol are `VACUOUS_TRUTH`, `UNUSED_HYP`,
and `BOUNDARY_SHIFT`.

## Appendix D: Probe Log Summary

Raw process logs are pointers in `probe_logs/`:

- `probe_logs/control_gap_closer.txt`
- `probe_logs/archive_gap_closer.txt`
- `probe_logs/pytest_gap_closer.txt`
- `probe_logs/control/` — local control artefacts

The archive log records C1-C4 as not run. The control log records C1-C3 as checked
and C4 as not run. No raw log is converted into a positive archive verdict.

## References

- Alpöge, L. *Remark*, 20 November 2026.
- Lean and Mathlib communities. *Lean verification of the Riemann Hypothesis*, 21 November 2026.
- Nielsen, J. L. *The Invalidity of Alpöge's Proposed Proof of the Riemann Hypothesis*, PhilArchive NIEIOT-2, 20 November 2026.
- Sutherland, A. *Verification files for the Lean proof of the Riemann Hypothesis*, MIT, 2026.
