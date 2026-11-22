<!--
Riemann Framework
Copyright (C) 2026 MILAN NIKOLIC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

# A verification agent for claimed proofs of the Riemann hypothesis

This document describes `python/riemann_framework/claim_audit.py`: what it does with a
claimed proof, what it refuses to do, and what its first end-to-end case, the 2026 Alpöge
release, came out as. Its role is **verification, auditing and status tracking**. It does
not discover anything, it cannot adjudicate the Riemann hypothesis, and no output of it is
evidence for or against that hypothesis.

## 1. The problem this solves

A claimed proof arrives as a PDF, sometimes with a formalisation attached. Three questions
follow, and they are usually conflated:

1. Is the arithmetic or the finite content of the argument right?
2. Is there a proof term of the right type, and is it the right type?
3. Who has checked it, and what did they conclude?

The first question is sometimes answerable by computation and never answers RH. The second
is answerable by a kernel and answers something narrower than it looks. The third is not a
mathematical question at all, and it is the one most often mistaken for a verdict. The
agent answers the three separately, each with a named trust base, and prints the residual
limit next to every result.

It exists because the alternative is worse. Feeding a proof-shaped claim into this
repository's vetting pipeline produces `passed=True` for anything non-affine, and the triage
note records why that is noise wearing the clothes of a result
([`claimed_proof_triage.md`](claimed_proof_triage.md) §2). The agent's design constraint is
that **no line of its output may be readable as "the hypothesis is true"**.

## 2. The three levels

### Level 1, numerical consistency: falsification, run by this repository

Every level-1 check is a call into a module of `riemann_framework`, not a computation
written inside the agent. The registry enforces the difference: each `Probe` names its
instrument, the tests confirm the module exists, and a test confirms that the probe's own
source imports it. "The repository was the instrument" is checkable rather than asserted.

| probe | instrument | decides | can it ever support RH? |
|:---|:---|:---|:---|
| `numerical_domain` | `dh_filter` inventory | whether any inventoried instrument accepts the claim as input | no |
| `dh_screen` | `dh_filter.screen_inputs` | whether the claim's declared inputs survive the Davenport–Heilbronn substitution | no: it can reject an argument, never confirm one |
| `zero_consistency` | `zeros.verify_first_n_zeros` | whether the first zeros are zeros and on the line | no: `mp.zetazero` searches the line |
| `proportion_constants` | `proportion_certificates` | whether the constant chain of the proportion theorems reproduces | no: arithmetic about a proportion |

For a claim that *asserts a proof exists*, the honest level-1 verdict is `outside domain`,
and it comes from the inventory rather than from a sentence in a document: nine inputs are
inventoried, and none of them is a proof, a theorem or a term. A proof claim has nowhere to
enter.

### Level 2, formal: five questions asked of the artefact

| question | decided by | what it does **not** decide |
|:---|:---|:---|
| does it compile | Lean, via `lake env lean` | that the term means anything |
| is it free of `sorry` | Lean's warning plus a comment-stripped source census | that `sorry` in a *statement* file is a hole: the evidence line says which case it is, and `sorryAx` in the axiom list decides |
| are the axioms justified | `#print axioms`, compared against `propext`, `Classical.choice`, `Quot.sound` | that a term using only these proves anything outside the formal system |
| is the theorem the Riemann hypothesis | for a `Prop` definition, `example : target = RiemannHypothesis := rfl`, which the kernel decides exactly; for a theorem, the printed type compared to the expected text after normalisation | that the proof is non-vacuous; and a text comparison is a comparison, not a bisimulation |
| are the definitions non-vacuous | **nothing here** | everything: this is the question the Alpöge–Nielsen dispute turns on |

The last row is the design. `_non_vacuity_finding` has no branch that returns anything other
than `undetermined`; what it can do is locate the definitional shapes an objection names
(`fun _ _ _ => True`, a proposition defined as an alias, a structure field fixed by `rfl`)
in the module's source, so a reader knows where to look. Locating is not proving dependence,
and the absence of a located shape is not a proof of the opposite.

### The dependency trace: the fifth question, decided

The vacuity question is not a kernel question and it is not a reading question. It is a
question about the compiled term: **is a definition the objection names reachable from the
theorem?** `lean/RiemannFramework/DependencyTrace.lean` answers it. `#deps <name>` walks
`Environment.find?` over the constant's type and value, collects everything reachable
transitively, and prints the closure between two markers. `dependency_trace` in the agent
wraps it, intersects the closure with the names the record declares, and reports one of three
things:

| outcome | status | verdict | what it means |
|:---|:---|:---|:---|
| a flagged name is in the closure | `checked_failed` | undetermined | the objection's route exists in this term |
| no flagged name is in the closure | `checked_ok` | validated (term) | the term does not pass through those definitions |
| the trace did not run | `not_run` | not assessed | nothing was asked; the driver is printed |

The distinction between the first two rows is the difference between Nielsen and Alpöge, and
it is now mechanical. What it still does not give you is *semantic* dependence: a flagged
definition can appear in the closure because an unused hypothesis mentions it. A hit is
therefore evidence that the route exists, not proof that the conclusion uses it; the
`limits` line on every trace finding says so.

**Both controls are in the record.** A checker that has never been driven at a known answer is
a checker nobody should trust, so the record traces two theorems whose closures are known:

| theorem | expected | observed |
|:---|:---|:---|
| `RiemannFramework.geometry_is_vacuous` | reaches `vacuousGeometry` | closure of 4, reaches 1 flagged definition |
| `RiemannFramework.closed_false_impossible` | reaches it not | closure of 5, reaches none |

The first is the positive control: a theorem that *states* the vacuity must have the vacuous
predicate in its closure. The second is the negative control: a theorem about the same
inductive, which never mentions the predicate, must come back clean. Both are asserted in
`test_alpoge_claim.py`.

**On the published archive the trace has not been run here, and the report says so.** The
archive is 931 MB of git blobs and 61.5 GB of export, it pins Lean v4.33.1 against this
repository's v4.34.0-rc2, and it is not held on this machine. The finding is `not_run`, its
evidence carries the exact driver a reader can run, and the record's `commands` list the whole
sequence. The trace module imports only `Lean` core, so it needs no Mathlib and the version
gap is a nameable risk rather than a blocker; it is stated rather than assumed away. This is
the one place where the agent's report is weaker than a full audit, and it is the place the
paper's own §5.2 verdict (`undetermined`) already reflected.

### The circularity screen: the dual of the Davenport–Heilbronn screen

The DH screen asks whether an argument would also prove a statement that is false. This asks
whether it already assumes a statement that is true: is a declared input **equivalent** to RH?
The two are duals, and an argument can pass one and fail the other, which is the reviewer's
point about transfer versus circularity made concrete.

The table is total over the inventory: `RH_EQUIVALENT_INPUTS` holds the one row that is an
equivalence (`li_positivity`, Li's criterion), and `NOT_RH_EQUIVALENT` records why each of the
other eight is not. A test asserts the two sets partition `dh_filter.DH_INPUTS`, so "not
flagged" means "considered and rejected", never "not thought about".

The sharp case is that row's double status. `li_positivity` **fails for Davenport–Heilbronn**,
so an argument that declares only it is marked `eligible` by the filter, and `eligible` is
supposed to be permission to continue. It is *also* equivalent to RH, so the same declaration
is what makes the argument circular. Eligibility and circularity are then the same fact about
the argument, and the report says so in one sentence. The verdict is `rejected`, with the limit
spelled out: this rejects the argument as a route to the hypothesis, not the hypothesis, not
the input, and not the claimant.

### The verdict algebra

`Verdict` is the paper's six words. `Instrument` says which part of the panel produced a
finding, and the aggregation rule reads the instrument, not the prose:

1. `rejected` dominates. A logical screen that fired ends the evaluation.
2. When formal artefacts were supplied, the panel's answer is the best of *their* verdicts.
3. A kernel pass counts as `validated (term)` **only** together with a dependency trace that
   came back clean. Kernel and no trace is `undetermined` by construction. This is the rule
   the review asked for, and it has its own tests.
4. When no artefact was supplied, the strongest validated numerical verdict is the panel's
   answer, because that is all the panel has.
5. Otherwise `undetermined`, with the computations that would decide it.

The consequence for the first case is the honest one: the published statement is
`validated (term)` **and** the panel verdict is `undetermined`, in the same report, because
the trace has not run. Before this revision the report's term-level verdict was the closest
thing to a panel verdict it had, and that was too strong.

**Replay is not a run.** When the artefact is not on the machine, the four decidable
questions are replayed from the claim record, and their instrument line says
`audit record of <date>` rather than `this machine, live`. `E3` is only reached by a compile
that happened here. A target with neither a run nor a record is `not_run`, never
`undetermined`: nothing was asked, and a status that suggested otherwise would be the
failure mode this repository keeps finding in its own documents.

### Level 3, institutional: recorded, never checked

Peer review, community statements, independent replays, objections on record, Clay status.
Each entry carries a source and a date and is reported as `recorded`, because this module
cannot read a referee report and an institution's confidence is not a theorem. The one
mechanical check on this level is the hash: `references/` holds the document, the record
holds its SHA-256, and a single changed byte turns the `E0` finding red.

## 3. The Alpöge case, end to end

`claims/alpoge_2026.json` is the record; `python scripts/audit_claim.py --claim
claims/alpoge_2026.json` reproduces the report into `out/claims/`. What it prints, as of
this commit:

| level | check | result | verdict |
|:---|:---|:---|:---|
| 1 | the claim enters an instrument's domain | `not_applicable` | outside domain |
| 1 | the declared inputs survive the Davenport–Heilbronn substitution | `checked_ok`: `needs_sourcing` | undetermined |
| 1 | the declared inputs are not RH-equivalent restatements | `not_applicable`: the record declares no inputs | not assessed |
| 1 | the first three non-trivial zeros are zeros and on the line | `checked_ok` | validated (finite) |
| 2 | the published archive compiles | `checked_ok`, replayed | not assessed |
| 2 | it is free of `sorry` | `checked_ok`, replayed: 5 `sorry`, all in the Comparator's `Challenge.lean` | not assessed |
| 2 | its axioms are the standard three | `checked_ok`, replayed: no `sorryAx`, 1,468,418 declarations accepted | not assessed |
| 2 | the theorem is the Riemann hypothesis | `checked_ok`, replayed: `con-leche --compare` | validated (term) |
| 2 | its definitions are non-vacuous | `undetermined` | undetermined |
| 2 | the dependency trace reaches `anyGeometry` etc. | `not_run`: the archive is not here; the driver is printed | not assessed |
| 3 | peer review | `recorded`: no journal article exists; the primary document is four pages and states no mathematics | not assessed |
| 3 | community statement | `recorded`, 2026-11-21 | not assessed |
| 3 | independent replay | `recorded`: `con-leche` exit 0, negative control exit 2 with `sorryAx` | not assessed |
| 3 | Clay status | `recorded`: unsolved, prize unawarded | not assessed |

**Panel verdict: `undetermined`.** Per artefact: the published archive `undetermined`, this
repository's recording `undetermined`.

Three facts about that table are the point of the whole exercise. The term is `validated
(term)` **and** the fifth question is `undetermined`, **and** the panel is `undetermined`,
at the same time, about the same artefact. A kernel can certify a term of Mathlib's
`RiemannHypothesis` and be silent about whether the library's internal definitions carry any
mathematics; Nielsen's objection is consistent with every row above, and so is the joint
statement of the Lean and Mathlib communities. The agent does not choose between them,
because nothing it runs bears on the choice, and the panel verdict refuses to promote the
kernel's answer to the panel's.

The record also carries a **live negative control**: `lean/RiemannFramework/Dispute.lean`,
this repository's own encoding of the dispute, in which Alpöge's position is stated with
`sorry` and the structural core of Nielsen's objection is proved without one. The five
questions on it come out as

| question | status | evidence |
|:---|:---|:---|
| compiles | `checked_ok` | `lake build` exit 0, `lake env lean` exit 0 |
| free of `sorry` | `checked_failed` | 2 `sorry`, in `alpoge_position` and `nielsen_position` |
| axioms justified | `checked_failed` | `RiemannFramework.alpoge_position: sorryAx is present` |
| the statement is RH | `checked_ok` | `RiemannFramework.RiemannHypothesisStatement = RiemannHypothesis` closed by `rfl` |
| definitions non-vacuous | `undetermined` | `True`-bodied: `vacuousGeometry` |
| dependency trace of `geometry_is_vacuous` | `checked_failed` | closure of 4, reaches `RiemannFramework.vacuousGeometry` |
| dependency trace of `closed_false_impossible` | `checked_ok` | closure of 5, reaches none |

That is a file whose contents are known, and the agent's answers match: the calibration is
the reason to trust the replay on the other target, which nobody can run here. It also shows
the verdict discipline: a statement that is definitionally equal to `RiemannHypothesis`
earns `undetermined`, not `validated (term)`, because the term it belongs to carries a hole.
And the two trace rows are the calibration of the decisive instrument itself, one positive
and one negative.

## 4. The overclaiming controls

These are mechanical, and each has a test that fails if it stops working.

- **Vocabulary.** Seven values: the paper's six verdicts plus `not assessed`. A test reads
  `paper/evaluation_protocol.tex` and requires each of the six to appear there, so the agent
  and the paper cannot drift into different vocabularies.
- **Standing sentence.** Every render contains the sentence beginning "RH is open". A test
  asserts it, and a report that lost it would fail rather than mislead.
- **Voice guard.** `render_markdown` scans the lines the agent writes, not the lines it
  quotes, against a list of proof claims, and raises rather than returning a document that
  asserts one. Quoted material is block-quoted and exempt: a report that cannot quote its
  subject cannot be honest about it.
- **Statuses are not booleans.** `checked_ok`, `checked_failed`, `recorded`, `undetermined`,
  `not_run`, `not_applicable`. Four of the six are ways of *not* having decided something,
  and they are not interchangeable: a census over an absent source may not report "nothing
  found", and an absent artefact is not `undetermined`.
- **A verdict belongs to one row.** `validated (term)` appears only on the statement row, and
  only when all four decidable questions came back `checked_ok`. Repeating it beside "does
  it compile" would let one passing check stand in for the result.
- **The falsification conditions are printed.** Section 6 of every report lists what would
  change it, generated from the finding statuses, before the reader reaches the objections.

## 5. What the agent cannot do

- **It cannot read the proof.** It compiles, counts and compares. Whether an argument is
  mathematics is not a question a hasher answers.
- **It cannot decide statement identity for a theorem.** For a `Prop`-valued definition the
  check is exact (`rfl` is definitional equality, decided by the kernel). For a theorem, the
  printed type is compared to expected text after folding layout and notation, which is
  weaker: two statements differing only in layout compare equal, and a statement differing
  mathematically will not. `con-leche --compare` is the stronger instrument, and the record
  names it where it was used.
- **It cannot resolve non-vacuity semantically.** The dependency trace decides *syntactic*
  reachability: does the compiled term mention the definition. Whether the definition's
  content is load-bearing is a further question, and a definition can be reached through an
  unused hypothesis. See §2.
- **It cannot decide peer review.** A claim is `recorded` as peer-reviewed or not, on the
  strength of a citation. Whether a referee read the paper is not something a test can see.
- **It cannot make a numerical check into evidence.** The zero check is in the panel because
  it is the check most often mistaken for evidence; its `limits` line says why it is not.
- **It cannot detect circularity it has not seen before.** The screen is total over the
  inventory and blind to everything outside it: an argument that restates RH in vocabulary
  the inventory does not hold is not caught.
- **It does not adjudicate the claim, and it does not adjudicate the claimant.** The report
  is a status record. The standing position of this repository is unchanged by any line of
  it: RH is open.

## 6. Adding a claim

A record is one JSON file in `claims/`. Required keys: `id`, `title`, `claimant`, `date`,
`statement`, `statement_location`, `declared_inputs`, `probes`. Optional: `document`,
`formal`, `institutional`, `objections`, `notes`. A formal target may declare `trace` entries
of the form `{"theorem": ..., "suspects": [...]}`, which is how the decisive computation is
named in the record before it is run. The loader rejects unknown keys, because a typo in a
key is otherwise an ignored field and an unstated premise in the report.

```console
python scripts/audit_claim.py --claim claims/alpoge_2026.json        # three levels, live Lean
python scripts/audit_claim.py --all --no-lean                        # replay only, fast
python scripts/audit_claim.py --claim claims/alpoge_2026.json \
    --lean-root D:\archives\alpoge-lean                              # an archive kept elsewhere
```

Reports are written to `out/claims/<id>.md` and `out/claims/<id>.json` (git-ignored) and
printed unless `--quiet`. The JSON is the structured form: claim, document, evidence
classes, the panel verdict and the per-artefact verdicts, every finding with its level,
status, verdict, instrument class, evidence and limit, the objections, and the formal targets
with their reproduction commands. `--strict` exits non-zero when any check came back
`checked_failed`, which is what CI should run.

The claim record is data, not code. Adding a claim does not change the agent, and the agent
never fetches, reads or interprets the document it audits: it re-hashes it and quotes from
the record.

## 7. Files

| file | role |
|:---|:---|
| `python/riemann_framework/claim_audit.py` | the agent: records, Lean machinery, probes, verdict algebra, report renderer |
| `lean/RiemannFramework/DependencyTrace.lean` | `#deps`: transitive dependency closure, Lean core only |
| `python/tests/test_claim_audit.py` | 59 fast tests: vocabulary, instruments, verdict algebra, circularity, parsers |
| `python/tests/test_alpoge_claim.py` | 21 tests, one live Lean audit: the case study, both trace controls, and the panel verdict |
| `scripts/audit_claim.py` | the command: one claim, or all, Markdown and JSON out |
| `claims/alpoge_2026.json` | the first claim record, with the replayed audit evidence |
| `python/riemann_framework/dh_filter.py` | the contrapositive screen level 1 runs |
| `python/riemann_framework/zeros.py`, `proportion_certificates.py` | the other level-1 instruments |
| `lean/RiemannFramework/Dispute.lean` | the live negative control: two positions, two `sorry`s |
| `docs/alpoge_nielsen_dispute.md` | what the dispute is, and the check that would settle it |

## 8. Standing position

RH is open. The agent audits claims, tracks their status, and reports what was checked and
by what. It has no verdict on the hypothesis, it cannot produce one, and every report it
writes says so on its second line.
