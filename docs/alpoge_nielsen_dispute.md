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

# The Alpöge–Nielsen dispute, recorded and not adjudicated

Two documents appeared within a day of each other, and they disagree. This note records what
each says, which of their claims has been checked and by whom, and which question decides the
disagreement. It does not decide it, and no statement in this repository changes because of it:
the position in [`claimed_proof_triage.md`](claimed_proof_triage.md) §5 still holds, in the sense
that nothing here is a verdict.

Both documents are now stored, byte for byte, under [`references/`](../references/README.md),
with a hash and a page count.

## 1. What happened, with sources and dates

| date | item | what it is |
|:---|:---|:---|
| 2026-11-20 13:52 | [Alpöge, `remark.pdf`](https://alpo.ge/remark.pdf) | a personal statement of belief: that he and Claude discovered a proof of RH and of GRH, "formalised without assumptions" |
| 2026-11-20 | the released Lean library | 17.4 million lines, 175,187 modules, stated dependency on Mathlib alone |
| 2026-11-21 | [Lean and Mathlib joint statement](https://leanprover-community.github.io/blog/posts/riemann-hypothesis/) | "We have full confidence that Alpöge's proof of the Riemann Hypothesis is correct"; all four of the Xena Project criteria said to be satisfied |
| 2026-11-21 12:55 UTC | [Sutherland's verification page](https://math.mit.edu/~drew/grh/) | the checklist: kernels, axiom audit, export hashes, statement comparison |
| 2026-11-20, PDF built 2026-11-21 16:50 | [Nielsen, *The Invalidity of Alpöge's Proposed Proof of the Riemann Hypothesis*](https://philarchive.org/rec/NIEIOT-2) | the objection this note is about: 13 pages |
| 2026-11-22 | a [third-party audit of her code claims](https://dev.to/frankchu/grh-proofs-geometry-is-fun-true-in-24-files-2n2b) | checks her central definition claim against the source |

**On sourcing — this section used to be weaker.** Until 2026-11-22 this note quoted Nielsen only
through the abstract reproduced by that third-party audit, because PhilArchive answers automated
fetches with a Cloudflare challenge (HTTP 403) and this repository's tooling could not get past
it. A copy of the paper has since been obtained by other means and is archived as
`references/nielsen_invalidity_2026-11-20.pdf`. Everything attributed to her below is now quoted
from the paper itself, with its section numbers, and the summary that the audit gave of her
argument has been replaced by her argument. Her affiliation on the title page is the Center for
Topological Physics, Lawrence, Kansas; the paper has not been peer-reviewed; and her §10 states
the limits of her own method. Those are facts about sourcing and scope, not about whether she is
right.

## 2. The two positions

**Alpöge's, as certified.** The statement proved is Mathlib's own `RiemannHypothesis`; the proof
term has that type; the term is accepted by Lean's kernel and by independent checkers; the
statement of the challenge file matches the theorem proved. The joint statement puts it at
"both the statement and the proof … are correct".

The remark itself is four pages and contains no mathematics: it states the belief, thanks
collaborators, gives a timeline of the argument, and explains the choice of medium —

> It being obviously inappropriate to attempt to post some massive unreadable travesty of "slop",
> I decided to only present Lean.

That sentence matters for what follows, because it means there is no prose argument to read. The
only object available for inspection is the formalization.

**Nielsen's, as she states it.** Her §8 collects the findings into seven items: the geometric
conditions are vacuously true because the predicate is `True`; the geometric object is a model in
which sections are the whole field, norms and volumes are zero and curves are a point; the map
from the lattice to sections is the zero map; the lattice identification holds by definition
because the lattice fields were defined as copies; the statement fixing the line-bundle degree is
vacuously true because its hypothesis cannot be met; the row-side and divisor-side geometries are
never identified; and the height equation that carries the divisor side into the conclusion holds
by `rfl` because the height is assigned to be its own formula.

Two of these carry the weight and are worth naming precisely:

- In `Development/AbelianVarietyTheory/Definitions/AutomorphicMembership/OverIx.lean`, `GeoP`
  has two inhabitants: `geoOf`, which demands a witness, and `anyGeometry := fun _ _ _ => True`.
  The concluding construction uses the second, at `EveryCharacterE.lean` lines 57, 60 and 64.
  `GeoCl`, the wrapper that looks like it restores a requirement, is an inductive whose `base`
  constructor accepts any proof of the underlying predicate, so `GeoCl.base trivial` discharges
  it at every input. She counts `anyGeometry` at 118 occurrences in 24 files, and `GeoCl` on
  seven lines, none of them a case analysis or an induction.
- The height that the divisor link squeezes between a lower bound and the main term is not
  derived: in `Definitions/GlobalTwisting/SetUnipotentTranslate.lean` ending at line 400, `ht`
  is defined as `hExpl6 …`, `setDiv` writes it into the datum, and `h_eq := fun _ => rfl` proves
  the height equation by definition. She finds the field constructed at four sites, two by `rfl`
  and two by copying, and no site where it is proved from geometry.

Her conclusion is not that RH is false, and not that the term fails to typecheck. Her Appendix A
says both explicitly:

> This paper does not show that the term fails to typecheck, and it does not show that
> `RiemannHypothesis` is underivable. … My claim is about the proof that was proposed.

The consequence she draws is that the proof **establishes nothing**, because the obligations it
discharges are vacuous and the lemmas written to extract content from them are never called.

## 3. What each kind of check establishes

This is the heart of the matter, and it is why both sides can be right simultaneously.

| check | establishes | does **not** establish |
|:---|:---|:---|
| `#print axioms`, kernel replay, nanoda, con-leche | the proof term has the claimed type and uses only standard axioms | that any *definition inside the library* means what its name suggests |
| comparator, `con-leche --compare` | the proved theorem is Mathlib's `RiemannHypothesis`, not a lookalike | the same, for internal definitions |
| the arithmetic cross-check (Robin, Lagarias) | that the result has consequences independent of Mathlib's ζ | that the geometric route is non-vacuous |
| reading the dependency graph | **whether the conclusion is reached through the vacuous predicate** | whether the analytic idea is correct |

The four Xena criteria are criteria about the *statement* and the *term*. A predicate defined as
`fun _ _ _ => True` typechecks, and a certificate built from it is a valid term. So a kernel can
certify a proof whose internal bookkeeping carries no mathematics, and it will do so without
error. This repository already recorded the weaker version of the same caveat in
[`claimed_proof_triage.md`](claimed_proof_triage.md) §4: *a formalisation can compile and be a
faithful proof of a mis-stated theorem*. Here the statement is certified to be the right one, and
the gap has moved inside: a faithful statement can be proved through vacuous definitions.

## 4. What has been independently checked, and what has not

Nielsen's paper is a reading of the source at the mirror `github.com/Deicyde/riemann-hypothesis`,
commit `712a6aef`; her §10 states that she read about 70 of 175,187 files, most in full, that her
counts are text searches over every `.lean` file, and that she did **not** build the archive, run
`#print axioms`, or produce a compiled dependency trace. She also states what she did not cover:
the bundle `Hyps` has about fifty fields, and she follows the geometric and lattice ones only.

The third-party audit checked the claim that is checkable by reading, and reached a different
answer on one item:

- **agreed**: `anyGeometry` is `fun _ _ _ => True`, six lines from `geoOf`, which does demand a
  witness;
- **agreed**: `anyGeometry` appears in 24 files and `geoOf` in 12, so the vacuous predicate is not
  a corner;
- **agreed**: `GeoCl` carries a certificate through its `base` and `step` constructors, so with
  `anyGeometry` every `base` obligation is discharged by `trivial`;
- **disputed**: she names `geoDegenerate`, `algDegenerate`, `padDegenerate` and `mdlJunk` as "the
  release's own" names for the degenerate model, while the audit reports that every `degenerate`
  hit in the tree is the ordinary word `nondegenerate`. One of the two is wrong. The test is a
  single search — `grep -c geoDegenerate` over the archive — and it is decidable; a case-sensitive
  search for `degenerate` would not match `geoDegenerate`, which is a plausible way the audit's
  count came out as it did. **Neither side of this has been checked here: this repository does
  not hold the 61.5 GB archive.**
- **not verified here**: her extraction-lemma count — `geoOf_surf`,
  `HasTrueSurf.secondChernDegree_vanishes_trueSurfaces`, `HasTrueSurf.degCh2_eq_zero`,
  `GeoTiedP.geoTied`, `GeoTiedP.formsTieX` and `degree_value_of_determinant`, each said to occur
  exactly once, at its own declaration;
- **open, and decisive**: whether `riemannHypothesis`'s compiled dependency chain actually passes
  through `anyGeometry`, `geoDegenerate`, `divXFl` and `x0`. She establishes the route from
  `divEx_prov` to the final bundle from the *source* of `hypsE` and the files it calls, not from
  the elaborated term, and says so.

If the chain runs through the vacuous predicate, both the certification and the objection are
true at once, and the proof establishes the statement only in the sense that a term of the right
type exists. If it does not, the `True` predicate is dead weight and the proof stands.

## 5. What would settle it

Nielsen's §9 lists four checks, each runnable by anyone with a build of the release:

1. **Independent kernel replay** — the mirror's Comparator run under Lean 4.36.0 plus nanoda,
   listing the axioms used. She notes the result was pending when she wrote, and that the project
   is pinned to Lean 4.33.1, which predates 4.34.1.
2. **Dependency walk** — the transitive dependencies of `riemannHypothesis`, reporting whether
   `anyGeometry`, `geoDegenerate`, `divXFl` and `x0` are among them. This turns her source-level
   finding into a statement about the compiled term.
3. **The degree equation** — whether `FrobeniusOrbitPlaceCount` is ever proved for a datum built
   on `divXFl`. If it is, the release asserts that `dFl` vanishes there.
4. **The remaining hypotheses** — `Holds R F`, `Pins`, the family class chosen inside `Hyps`, and
   the analytic step `zeroFreeOn_of_tiedWin_cyc`, which is where any real content must be, since
   it is not in the geometric or lattice witnesses.

Check 2 is the one this note would run first, and neither the 61 GB export nor four independent
checkers can answer it. Reading the exported dependency graph can.

## 6. This repository's position

Recorded, not adjudicated, and with no change to any claim of this repository:

- the [triage note](claimed_proof_triage.md) continues to say that RH is open, because nothing
  here adjudicates the dispute;
- [`lean/RiemannFramework/Dispute.lean`](../lean/RiemannFramework/Dispute.lean) records the two
  positions as Lean propositions. Its structural content is **proved** (a certificate predicate
  that is constantly `True` discharges its closure without a witness, which is the checkable core
  of the objection); the two contingent claims about the archive, and the disputed statement
  itself, are `sorry`, and the file is registered in `OPEN_RH_FILES` so that the test suite cannot
  ever report it complete;
- no number in any other document was changed.

If the certification survives the dependency trace, the `sorry`-carrying file remains an honest
record of a dispute that was settled against one side. If it does not, the file is already the
record of why.

## Sources

- Alpöge, L. *Remark*, 2026-11-20. Archived as `references/alpoge_remark_2026-11-20.pdf`.
- Lean and Mathlib communities. *Lean verification of the Riemann Hypothesis*, 2026-11-21.
- Sutherland, A. *Verification files for the Lean proof of the Riemann Hypothesis*, MIT,
  updated 2026-11-21 12:55 UTC.
- Nielsen, J. L. *The Invalidity of Alpöge's Proposed Proof of the Riemann Hypothesis*,
  PhilArchive NIEIOT-2, 2026-11-20; §1–§11 and Appendix A. Archived as
  `references/nielsen_invalidity_2026-11-20.pdf`.
- Chu, F. *GRH proof's geometry is `fun _ _ _ => True`, in 24 files*, 2026-11-22 (third-party
  audit of the code claims).
