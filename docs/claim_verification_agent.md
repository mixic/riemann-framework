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
and the absence of a located shape is not a proof of the opposite. A dependency walk of the
exported term is what would settle it, and it is named as the decisive check in
[`alpoge_nielsen_dispute.md`](alpoge_nielsen_dispute.md) §5.

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
| 1 | the first three non-trivial zeros are zeros and on the line | `checked_ok` | validated (finite) |
| 2 | the published archive compiles | `checked_ok`, replayed | not assessed |
| 2 | it is free of `sorry` | `checked_ok`, replayed: 5 `sorry`, all in the Comparator's `Challenge.lean` | not assessed |
| 2 | its axioms are the standard three | `checked_ok`, replayed: no `sorryAx`, 1,468,418 declarations accepted | not assessed |
| 2 | the theorem is the Riemann hypothesis | `checked_ok`, replayed: `con-leche --compare` | validated (term) |
| 2 | its definitions are non-vacuous | `undetermined` | undetermined |
| 3 | peer review | `recorded`: no journal article exists; the primary document is four pages and states no mathematics | not assessed |
| 3 | community statement | `recorded`, 2026-11-21 | not assessed |
| 3 | independent replay | `recorded`: `con-leche` exit 0, negative control exit 2 with `sorryAx` | not assessed |
| 3 | Clay status | `recorded`: unsolved, prize unawarded | not assessed |

Two facts about that table are the point of the whole exercise. The term is `validated
(term)` **and** the fifth question is `undetermined`, at the same time, about the same
artefact. A kernel can certify a term of Mathlib's `RiemannHypothesis` and be silent about
whether the library's internal definitions carry any mathematics; Nielsen's objection is
consistent with every row above, and so is the joint statement of the Lean and Mathlib
communities. The agent does not choose between them, because nothing it runs bears on the
choice.

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

That is a file whose contents are known, and the agent's answers match: the calibration is
the reason to trust the replay on the other target, which nobody can run here. It also shows
the verdict discipline: a statement that is definitionally equal to `RiemannHypothesis`
earns `undetermined`, not `validated (term)`, because the term it belongs to carries a hole.

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
- **It cannot resolve non-vacuity.** See §2. This is the residual limit, and it is the one
  that matters for the 2026 claim.
- **It cannot decide peer review.** A claim is `recorded` as peer-reviewed or not, on the
  strength of a citation. Whether a referee read the paper is not something a test can see.
- **It cannot make a numerical check into evidence.** The zero check is in the panel because
  it is the check most often mistaken for evidence; its `limits` line says why it is not.
- **It does not adjudicate the claim, and it does not adjudicate the claimant.** The report
  is a status record. The standing position of this repository is unchanged by any line of
  it: RH is open.

## 6. Adding a claim

A record is one JSON file in `claims/`. Required keys: `id`, `title`, `claimant`, `date`,
`statement`, `statement_location`, `declared_inputs`, `probes`. Optional: `document`,
`formal`, `institutional`, `objections`, `notes`. The loader rejects unknown keys, because a
typo in a key is otherwise an ignored field and an unstated premise in the report.

```console
python scripts/audit_claim.py --claim claims/alpoge_2026.json        # three levels, live Lean
python scripts/audit_claim.py --all --no-lean                        # replay only, fast
python scripts/audit_claim.py --claim claims/alpoge_2026.json \
    --lean-root D:\archives\alpoge-lean                              # an archive kept elsewhere
```

Reports are written to `out/claims/<id>.md` and `out/claims/<id>.json` (git-ignored) and
printed unless `--quiet`. The JSON is the structured form: claim, document, evidence
classes, every finding with its level, status, verdict, instrument, evidence and limit, the
objections, and the formal targets with their reproduction commands. `--strict` exits
non-zero when any check came back `checked_failed`, which is what CI should run.

The claim record is data, not code. Adding a claim does not change the agent, and the agent
never fetches, reads or interprets the document it audits: it re-hashes it and quotes from
the record.

## 7. Files

| file | role |
|:---|:---|
| `python/riemann_framework/claim_audit.py` | the agent: records, Lean machinery, probes, report renderer |
| `python/tests/test_claim_audit.py` | 39 fast tests: vocabulary, instruments, refusals, parsers |
| `python/tests/test_alpoge_claim.py` | 14 tests, one live Lean audit: the case study and its negative control |
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
