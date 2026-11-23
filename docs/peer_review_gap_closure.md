# Peer review on executing the gap-closing computation: translation and response

**Provenance.** The review translated here was received in German on 23 November 2026, after the
submission of the structural revision of the evaluation paper. It asks for the computations that
the protocol names but does not execute: the dependency closure of the final theorem of the 2026
Alpöge archive, the cross-validation of that closure by a second extractor, and the mutation-based
classification of the definitions the vacuity objection names. It closes with five points on how
the paper should position itself against the current state of the debate. The German text is
reproduced verbatim in Appendix A; the translation in §1 is the basis of the response in §5.

**Scope of the response.** The computations are the empirical part of the review and are reported
in §3 with the commands that produced them and the hashes of the artefacts. The positioning points
are addressed in §6 and, where the paper needed them, in the paper itself. No verdict in this
document means that the Riemann hypothesis is true, and the vocabulary is the paper's six-term
one: `rejected`, `outside domain`, `undetermined`, `validated (finite)`,
`validated (elementary)`, `validated (term)`.

---

## 1. Translation

### 1.1 The five steps

**Step 1: execute the decisive dependency trace (C1 and C2).** The paper names the dependency
analysis as decisive but does not carry it out. The transitive closure of the final theorem
`RiemannHypothesis` must be computed.

*C1, the primary closure by `#deps`.* Implement a Lean 4 script that follows the "Shape 1: forward
transitive closure" recipe: iterate `Expr.getUsedConstants` over both the type and the value of
every reached declaration until a fixed point is attained. This is the only method that answers
the question "what does this proof depend on?". `#print axioms` is not a substitute, because it
shows only the fundamental axioms, not the specific declarations.

*C2, the secondary closure by `laud graph`.* As an independent counter-check, run
`laud graph src --entry RiemannHypothesis --tree --max-depth 20`. The tool produces an ASCII
dependency tree that can be parsed.

**Step 2: cross-validate the closure (C3).** Compare the results of C1 and C2. If the sets differ,
that is a critical finding, which must be reported as `UNDETERMINED` with the named computation
"reconcile closure mismatch". Only when both independent extractors return the same closure may it
count as verified.

**Step 3: carry out the load-bearing analysis (C4).** This is the step that answers the decisive
question: is a definition marked as vacuous actually load-bearing for the proof? *Mutation
experiment.* For every declaration in the cross-validated closure that `Lean Vacuity Check` or
`lean-proof-review` marks as vacuous, perform a targeted mutation: replace the definition with a
trivially vacuous analogue and recompile the project. *Evaluation.* If the final theorem still
typechecks afterwards, the definition is load-bearing (the vacuity critique applies); if
compilation fails, it is not load-bearing (the critique dissipates). *Tools.* Use
`laud mutate src --lake --run` for the `VACUOUS_TRUTH` mutant, supplemented by the targeted checks
of `Lean Vacuity Check` (for semantic vacuity) and `lean-proof-review` (for the L1–L4 checklist).

**Step 4: synthesis and documentation.** Assemble all results in the artefacts already designed:
`closure_crossvalidated.json` (C1, C2 and C3), `load_bearing.json` (the C4 outcome for every
marked declaration), `dependency_graph.html` (the colour-coded graph separating the red set, in
the closure and marked and load-bearing, from the yellow set, mathematically required but not in
the closure), and `gap_statement.md` (the mechanically generated prose whose §4 lists exactly the
proof obligations that would have to be discharged to remove the red nodes).

**Step 5: compliance with scientific standards.** *Reproducibility:* archive all artefacts with
SHA-256 hashes, and document the exact commands and the Lean toolchain used
(`leanprover/lean4:v4.33.1`). *Transparency:* for every verdict, document the check applied and
its raw result, for example the list of surviving mutants. *Precise language:* avoid every
overclaim, and distinguish strictly between "the kernel accepts the term" and "the term
establishes the mathematical statement".

**Conclusion of the review.** The decisive blank space is the execution of the computations that
have been named precisely. With the tools named above — `laud`, `Lean Vacuity Check`,
`lean-proof-review` and the `#deps` recipe — the gap can be closed. The result would no longer be
a mere framework but a concrete, reproducible, forensic analysis of the Alpöge archive that shows
exactly which definitions are load-bearing and vacuous, and which mathematical proof obligations
follow. That is the step that turns the work from a methodological specification into a robust
scientific result.

### 1.2 The five positioning points

1. **Position the official statement of the Lean community explicitly.** The paper mentions the
   certification but should name its reach and its limits. On 21 November 2026 the Lean and
   Mathlib communities officially confirmed that the proof passes the kernel. That certification
   refers expressly to the formal correctness of the term (the statement is correct, the code
   compiles, the axioms are clean). It is not a statement about the mathematical validity of the
   definitions on which the term rests. The paper should not merely record this distinction but
   work it out as a central finding: the community certification is a strong signal at the kernel
   level and leaves the semantic level raised by Nielsen entirely untouched.

2. **Treat the vacuity critique as an independent, citeable position.** Nielsen's *Invalidity of
   the Alpöge proposed proof of the Riemann hypothesis* is a detailed, source-code-based analysis.
   The paper lists its individual points (`anyGeometry`, `hExpl6`, and others), but should present
   it as a structured, independent critique that poses the decisive question: the kernel verifies
   a derivation relative to the given definitions; it does not verify that those definitions carry
   the mathematics their names claim, and here they do not. This is the core of the paper's own
   research question and should be cited and situated as such.

3. **Bring out the tool-supported operationalisation as a methodological contribution.** The
   framework is not a theoretical exercise. It operationalises the question raised by Nielsen and
   others with concrete, existing tools. The paper should name explicitly the tools and methods it
   uses for the decisive dependency trace and the load-bearing analysis: for the closure, the
   "Shape 1: forward transitive closure" recipe that iterates `Expr.getUsedConstants` over the type
   and the value of every reached declaration, which is the de facto standard for this task, with
   `#print axioms` explicitly not a substitute; for the vacuity check, `laud mutate`, a tool
   developed specifically for auditing massive machine-generated Lean repositories, which stresses
   theorems against `VACUOUS_TRUTH` and `UNUSED_HYP`; and for the cross-validation, the combination
   of `#deps` and `laud graph` as two independent extractors, which is a methodological strength to
   be emphasised.

4. **Formulate the "epistemic gap" as the central result.** The work should not only propose a
   protocol but report the outcome of applying it. The decisive insight is that kernel acceptance
   is a necessary but not a sufficient condition for mathematical validity. This should be
   formulated as the core finding: there is an epistemic gap between what the kernel confirms (the
   existence of a term of type `RiemannHypothesis`) and what the mathematical community means by a
   proof (the establishment of mathematical truth by non-vacuous arguments).

5. **Give a clear outlook on the work still to be done.** Because the decisive dependency trace
   for the Alpöge archive has not been performed publicly, the paper should close with a precise
   research programme: the cross-validated closure, the load-bearing analysis for every marked
   declaration, and the resulting graphical presentation of the red and yellow nodes.

---

## 2. Method

### 2.1 Instruments, and what was actually available

The review names four instruments. Three of them do not exist as executable checkers in this
environment or in the public registries consulted: `laud graph`, `laud mutate`, `Lean Vacuity
Check` and `lean-proof-review` are absent from the machine, and the public packages under the
latter two names are prompt-level *skills* rather than programs that emit the structured output
the review assumes. The engine therefore implements the instruments it can, uses the repository's
own second extractor for C2, and records every substitution in every artefact:

| specified instrument | what ran | recorded as |
|:---|:---|:---|
| C1, `#deps` with `Expr.getUsedConstants` | `lean/RiemannFramework/DependencyTrace.lean`, `#deps`, fixed-point traversal over type and value | identical to the specification |
| C2, `laud graph --tree` | `#depsm`, a structural recursion written out case by case over the constructors of `Expr`, in the same file | a substitution on the same environment, printed in `closure_crossvalidated.json` and in every report |
| C3, comparison | `gap_closer.cross_validate`, exact set difference, no averaging | as specified, with a named reconciliation when the sets differ |
| C4, `laud mutate --run` | the repository's mutation runner (`adjudicator.run_mutant`), which rewrites a declared anchor in a copy of the source and recompiles | as specified where a vacuous-analogue mutant is declared; content flips are labelled as such and do not count as C4 |
| vacuity flags | the textual census (`census_flags`), `(?:def|abbrev) ... := (fun ... => True | True)` | heuristic; the plugin's semantic flags were not available |

`#print axioms` is not used anywhere in the chain. The trace module collects constants through
`Expr.getUsedConstants` (C1) and through the hand-written recursion (C2); the axiom audit appears
only as a separate kernel-layer fact in the paper, never as a tracer.

### 2.2 The archive and its snapshot

The published archive is `https://github.com/Deicyde/riemann-hypothesis`. Its state changes: the
paper records a snapshot at commit `2dea990`, pinned to Lean `v4.33.1` and Mathlib `0df444a3`,
while the public default branch at the time of this run is commit `1cc42d2` (23 November 2026,
09:12 +1100), pinned to Lean `v4.36.0` and Mathlib `fc4f59e5`. The paper's snapshot commit is not
reachable as a shallow ref, so the execution reported below is against `1cc42d2`, and every
artefact names that commit. A closure computed at `1cc42d2` is evidence about the archive as
served on 23 November 2026, not about the snapshot the paper archives.

### 2.3 The four computations

The engine is `python/riemann_framework/gap_closer.py`; the command line is
`python scripts/audit/rh_gap_closer.py`. C1 and C2 write one probe file that imports the trace
module and the target module and elaborates `#deps <target>` and `#depsm <target>`; the output is
parsed between the `DEPS_BEGIN`/`DEPS_END` markers. C3 compares the two name sets exactly. C4
replaces the declared anchor with a vacuous analogue in a copy of the source, recompiles the
target theorem, and records whether the theorem survived; a kill means the proof needs the
definition's content, a survival means it does not. The aggregation of the six-term vocabulary is
implemented in `gap_closer.aggregate`, including the refusal that a `validated (term)` verdict
cannot be emitted while any of C1–C4 has not run.

### 2.4 Verdict algebra, and the specification's ambiguous rows

The review's precedence table contains two rows that cannot both hold: a clean kernel with no
load-bearing vacuous nodes is `validated (term)` by one row and `undetermined` by the next. The
implementation resolves the contradiction in the direction that preserves the refusal: a
load-bearing vacuity witness always withholds the term verdict, and a positive verdict always
requires all four computations. The resolution is stated in the module docstring and in the paper's
Appendix D.2, so a reader can disagree with it in the open rather than discover it in an edge case.

### 2.5 What C4 can and cannot decide

The specification's C4 replaces a flagged definition with a trivially vacuous analogue and asks
whether the theorem still compiles. When the definition is *already* the trivially true form, the
vacuous analogue is the definition, and the mutation is the identity: the vacuity of such a
declaration is established by reading it, not by mutating it. C4 discriminates only where the
suspicion is a definition that is semantically off without being literally `True`. That limit is
recorded in every report that scores a declaration by inspection rather than by mutation.

---

## 3. Execution record

### 3.1 The control: computations C1–C3 executed

The control target is `RiemannFramework.geometry_is_vacuous`, whose file contains two deliberate
`sorry`s, so the kernel verdict is withheld. It is the only artefact on this machine on which the
closure computations can be executed end to end:

| computation | result |
|:---|:---|
| C1, `#deps` | closure of 4 names: `Nat`, `RiemannFramework.geometry_is_vacuous`, `RiemannFramework.vacuousGeometry`, `True` |
| C2, `#depsm` | closure of 4 names, identical |
| C3, comparison | the two closures agree; no reconciliation needed |
| C4, vacuous-analogue mutation | `not run`: the record's mutant is a content flip (`True` to `False`), not a vacuous analogue; it was executed and killed, which calibrates the engine |

`vacuousGeometry` is in the closure, is flagged by the census, and is vacuous by inspection
(`:= True`); it is recorded red, and the verdict is `undetermined` with two named computations:
discharge the witness, and declare a vacuous analogue. The self-audit conditions all pass.

### 3.2 The archive: the trace was attempted, and is blocked by the platform

The archive was cloned and its environment prepared. Table 3 records what ran; the table is the
honest answer to Step 1 for the archive, and it is not a closure.

| step | result |
|:---|:---|
| clone `https://github.com/Deicyde/riemann-hypothesis` (shallow) | 149,397 source files; commit `1cc42d2`, 23 November 2026 09:12 +1100 |
| toolchain and Mathlib pins | Lean `v4.36.0`; Mathlib `fc4f59e5`; the paper's recorded snapshot (`2dea990`, Lean `v4.33.1`, Mathlib `0df444a3`) is not reachable as a shallow ref |
| Mathlib olean cache | 9,117 files fetched and decompressed |
| project CI cache (`scripts/ci-cache-get.py`) | 148,873 of 149,397 oleans installed (11.85 GB), then failed on the remaining modules |
| `lake build Main` | failed with `no such file or directory (error code: 2)` on `<Module>.olean.private.hash` paths |
| C1, C2, C3, C4 on `Main.riemannHypothesis` | `not run` |
| verdict | `undetermined` |

The cause is a platform limit, not a mathematical one. Lean writes auxiliary files next to each
olean, so a module whose source path is 234 characters becomes a build path of about 290 on this
drive, beyond the 260-character limit that the Windows file API enforces for the toolchain. The
failure reproduces on a named file, for example
`.lake\build\lib\lean\CompanionTheory\...\RightCasimirMemSubmodule.olean.private.hash`, and the
same limit explains why the cache restore stops where it does. Relocating the archive to a short
root does not fix it: the longest module still exceeds the limit by about fourteen characters.

The named computation is therefore precise: build and trace the archive on a filesystem without
the limit (Linux, WSL, or macOS). The clone used here was moved to `C:\alpoge-archive`, outside the
repository, because the repository's recorded state is that the archive is absent from the
machine; keeping the unbuildable checkout inside it would silently change what the audit's default
path replays. With the archive in place the command is:

```
python scripts/audit/rh_gap_closer.py --archive C:\alpoge-archive \
    --theorem Main.riemannHypothesis --module Main
```

`Main.riemannHypothesis` is the solution theorem (`theorem riemannHypothesis : RiemannHypothesis :=
Claim.zeta LFunction_ne_zero_of_half_lt_re`); `Challenge.riemannHypothesis` is the `sorry` variant
and is not the target. The probe imports `Main` and carries the trace elaborators inline, because
the archive has no library into which a copied trace module could be placed.

Nothing about the vacuity objection is concluded from this attempt. There is no closure, hence no
red, amber, blue or yellow set, and no statement about `anyGeometry`, `geoDegenerate`, `divXFl` or
`x0`. The archive report is `undetermined` with the build as its named computation, and its
artefacts are archived under `docs/gap_closer/alpoge_2026/` with the reason in place of the names.


---

## 4. Artefacts

Each report writes six artefacts and a SHA-256 manifest; the manifests are committed with the
reports under `docs/gap_closer/`:

| file | content |
|:---|:---|
| `closure_deps.txt` | C1 closure, sorted, one name per line, with the instrument and status in the header |
| `closure_laud.txt` | C2 closure, sorted, with the substitution stated in the header when `laud graph` was unavailable |
| `closure_crossvalidated.json` | C1 and C2 payloads, the two difference sets, the agreement status, the verdict and the standing position |
| `load_bearing.json` | one record per flagged declaration: in the closure, flagged, vacuity-critical, colour, mutant, evidence |
| `dependency_graph.html` | self-contained five-colour graph (green, blue, red, amber, yellow) with the self-audit failures when any exist |
| `gap_statement.md` | the mechanically generated statement, with §4 listing the named computations |

---

## 5. Response matrix

| review item | action | evidence |
|:---|:---|:---|
| Step 1, C1 | implemented and executed where the artefact is available; on the archive, `not run` is reported with the clone command, never an estimate | §3.1, §3.2; `closure_deps.txt` |
| Step 1, C2 | `laud graph` is not installed; the second extractor is `#depsm` over the same environment, and the substitution is printed in every report | §2.1; `closure_laud.txt` |
| Step 2, C3 | exact comparison, no averaging; a difference stops the report with the named reconciliation | §2.3; `closure_crossvalidated.json` |
| Step 3, C4 | mutation runner executed on declared mutants; vacuous-analogue mutants are distinguished from content flips; identity mutations are recorded as such | §2.5, §3.1; `load_bearing.json` |
| Step 4, synthesis | the six artefacts and manifest are written by `write_artefacts` | §4 |
| Step 5, standards | hashes, commands, toolchain and raw outputs archived; the six-term vocabulary; no overclaim | §4; `manifest.json` |
| c1, community certification | the kernel-level scope of the community statement is a central finding of the paper, not a footnote | §6; paper §5.1 |
| c2, Nielsen as an independent position | the objection is presented as a structured, citeable reading, and its own stated limits are quoted | §6; paper §5.1 |
| c3, tool operationalisation | the closure recipe, the two-extractor design and the mutation probe are named as the method | §2; paper Appendix D |
| c4, epistemic gap as the finding | the gap is stated as the paper's central result, with the kernel/definitions distinction | §6; paper §8 |
| c5, outlook | a named programme: cross-validated closure, per-declaration load-bearing analysis, red/yellow graph | §7; paper Appendix D.7 |

---

## 6. Epistemic position

The kernel answers a precise question: does this term inhabit this type, under this axiom set? The
2026 certification answers that question affirmatively for the archive's five principal theorems,
and the answer is not in dispute here. What the certification does not answer is whether the
definitions the term routes through carry the mathematics their names claim. That is not a defect
of the kernel; it is a question the kernel is not designed to ask, and `#print axioms` cannot ask
it either, because a vacuous definition is a definition and not an axiom.

The epistemic gap is therefore this: the kernel confirms the existence of a term of type
`RiemannHypothesis`, whereas a mathematical proof is normally taken to establish the truth of the
proposition by non-vacuous means. The first is necessary and the second is not implied by it. This
paper's contribution is to make that gap operational — to name the computation that decides
whether a given definition is reached and whether the proof needs its content — and to report the
gap as a result rather than a preface.

Nielsen's reading is treated as an independent, structured position and is cited as one. Its own
statement of limits is quoted rather than paraphrased away: about 70 files of 175,187 read, no
build, no axiom print, no compiled trace. The review's formulation of the objection's core — that
the kernel verifies a derivation relative to the given definitions and not that the definitions
carry their names' mathematics — is retained here as the review's formulation, not attributed to
Nielsen verbatim, because the sentence was not checked against her text.

---

## 7. The programme that remains

Three computations remain open for the archive, and each has a command and an artefact:

1. **C1 and C2 on the archive.** Build the archive's import closure under its own toolchain, copy
   the trace module in, and elaborate `#deps` and `#depsm` on `Main.riemannHypothesis`. The
   driver for this is `scripts/audit/trace_archive.py`; the engine is the same one that runs the
   control.
2. **C3 across two genuinely independent extractors.** The specification names `laud graph`; until
   it exists as a program, the second extractor shares the environment, so agreement corroborates
   the traversal and not the environment. Installing `laud` is therefore the one substitution that
   cannot be closed by writing code here.
3. **C4 for every flagged declaration.** Each requires a vacuous analogue taken from the archive's
   own source, not from the paper's paraphrase of it, and one recompilation per mutant. The red
   set is the set of definitions this step confirms; the yellow set is the mathematics the closure
   does not reach.

The red and yellow sets are the two numbers that would move the archive's verdict from
`undetermined`. They are not available until the archive is built and run; nothing in this
repository substitutes an estimate for them.

---

## 8. Submission readiness (RH-PAPER-FINALIZER)

The finalizer specification makes the paper conditional on an executed, cross-validated closure
and a load-bearing classification for every flagged declaration. Its own rule for an incomplete
precondition is explicit: emit `undetermined` with the named computation "complete RH-GAP-CLOSER
first", and do not assert in the paper what no artefact supports.

The finalizer's separate paper was merged into the evaluation paper, so the repository holds one
paper. Its content now sits in the paper's §5.1 (the archive attempt and Nielsen's findings), §3.4
(the falsification of the central claim), and §8 (the general claim and the community
recommendation). The artefact suite remains under `output/rh_paper_finalizer/` and carries A2–A10.
`scripts/audit/paper_readiness.py` checks that suite against the specification; its result is
committed as `docs/gap_closer/paper_readiness.json`:

| check | result |
|:---|:---|
| A1 `paper.pdf` | pass: `paper/evaluation_protocol.pdf`, 26 pages |
| A2 `closure_deps.txt` | fail: 0 names |
| A3 `closure_laud.txt` | fail: 0 names |
| A4 `closure_crossvalidated.json` | fail: status `not_run`, common closure empty |
| A5 `load_bearing.json` | fail: 0 classified declarations |
| A6 `dependency_graph.html` | pass: five-colour legend present |
| A7 `gap_statement.md` | pass: Section 4 names the computations |
| A8 `reproduction.sh` | pass: present, pinned commit, `bash -n` clean |
| A9 `probe_logs/` | pass: 10 files (control artefacts, archive log, pytest log) |
| A10 `MANIFEST.sha256` | pass: 17 files verify |
| R1 executed closure | fail: the archive closure did not run |
| R2 per-declaration classification | fail: nothing to classify |
| R3 verdict populated | pass: `undetermined` |
| R4 falsification stated | pass: Section 4 lists the moving computations |
| R5 no proof claim | pass: none in the paper or the gap statement |

**Verdict: `undetermined`. Named computation: complete RH-GAP-CLOSER first.**

This is the specification's own fallback, and it is also the merged paper's verdict for the
archive: §5.1 reports the attempt, the platform failure and the named computation, and §8 of the
paper states the general claim without promoting a term verdict. The paper is written and
reproducible; what it cannot do is report a closure that no run produced.

One correction belongs to this revision. The finalizer's draft quoted Nielsen as writing "the
kernel verifies a derivation relative to the given definitions ... carry the mathematics their
names claim". The archived PDF reads: "The kernel verifies a derivation relative to the definitions
it is given. It does not verify that those definitions carry the intended mathematics. Here they
do not." The merged paper quotes the verbatim sentence and keeps its own gloss outside the
quotation marks. A direct quotation that alters words is a defect of the same kind the paper is
about, and the archived PDF makes the check mechanical.

When the closure is executed on a filesystem without the Windows path limit, the same command
regenerates A2–A5 and A9, the manifest is regenerated, and the readiness check moves from
`undetermined` to the verdict the pipeline returns.

## Appendix A. The German original

The text below is reproduced as received. Section references inside it (C1–C5, Schritte 1–5) are
the review's own.

**Steps.** Um Ihre Arbeit auf das höchste wissenschaftliche Niveau zu heben, müssen die im
Protokoll identifizierten, aber noch nicht ausgeführten Berechnungen tatsächlich durchgeführt
werden. Der Kern ist, die entscheidende Dependency-Trace und die Load-Bearing-Analyse für das
Alpöge-Archiv auszuführen und zu dokumentieren.

*Schritt 1: Die entscheidende Dependency-Trace ausführen (C1 & C2).* Das Papier nennt die
Abhängigkeitsanalyse als entscheidend, führt sie aber nicht aus. Sie müssen die transitive Hülle
des finalen Theorems `RiemannHypothesis` berechnen. C1 – Primäre Closure via `#deps`:
Implementieren Sie ein Lean-4-Skript, das die Rezeptur „Shape 1: Forward Transitive Closure"
verwendet. Dieses Skript durchläuft `Expr.getUsedConstants` sowohl für den Typ als auch für den
Wert jeder erreichten Deklaration, bis ein Fixpunkt erreicht ist. Dies ist die einzige Methode, um
die Frage „Wovon hängt dieser Beweis ab?" zu beantworten. `#print axioms` ist dafür kein Ersatz,
da es nur die fundamentalen Axiome zeigt, nicht die spezifischen Deklarationen. C2 – Sekundäre
Closure via `laud graph`: Führen Sie als unabhängige Gegenprobe
`laud graph src --entry RiemannHypothesis --tree --max-depth 20` aus. Dieses Werkzeug erzeugt einen
ASCII-Abhängigkeitsbaum, der sich parsen lässt.

*Schritt 2: Kreuzvalidierung der Closure (C3).* Vergleichen Sie die Ergebnisse von C1 und C2.
Weichen die Mengen voneinander ab, ist das ein kritischer Befund, der als UNDETERMINED mit der
benannten Berechnung "reconcile closure mismatch" ausgewiesen werden muss. Nur wenn beide
unabhängigen Extraktoren dieselbe Closure liefern, kann diese als verifiziert gelten.

*Schritt 3: Die Load-Bearing-Analyse durchführen (C4).* Dies ist der Schritt, der die entscheidende
Frage beantwortet: Ist eine als vakuuös markierte Definition tatsächlich lasttragend für den
Beweis? Mutations-Experiment: Für jede Deklaration in der kreuzvalidierten Closure, die von Lean
Vacuity Check oder lean-proof-review als vakuuös markiert wurde, führen Sie eine gezielte Mutation
durch. Ersetzen Sie die Definition durch ein trivial vakuuöses Analogon und kompilieren Sie das
Projekt neu. Auswertung: Wenn das finale Theorem danach immer noch typcheckt, ist die Definition
load-bearing (die Vakuuitätskritik greift). Wenn die Kompilierung fehlschlägt, ist sie nicht
load-bearing (die Kritik verpufft). Werkzeuge: Nutzen Sie `laud mutate src --lake --run` für den
VACUOUS_TRUTH-Mutanten. Ergänzen Sie dies durch die gezielten Prüfungen von Lean Vacuity Check (für
semantische Vakuuität) und lean-proof-review (für die L1-L4-Checkliste).

*Schritt 4: Synthese und Dokumentation.* Führen Sie alle Ergebnisse in den bereits entworfenen
Artefakten zusammen: `closure_crossvalidated.json` dokumentiert die Ergebnisse von C1, C2 und C3.
`load_bearing.json` enthält für jede markierte Deklaration das Ergebnis des Mutations-experiments
(C4). `dependency_graph.html` ist der farbcodierte Graph, der die rote Menge (in Closure, markiert,
load-bearing) von der gelben Menge (mathematisch benötigt, nicht in Closure) trennt.
`gap_statement.md` ist die mechanisch generierte Prosa, die in §4 genau die Beweispflichten
auflistet, die erfüllt werden müssten, um die roten Knoten zu beseitigen.

*Schritt 5: Einhaltung wissenschaftlicher Standards.* Reproduzierbarkeit: Archivieren Sie alle
Artefakte mit SHA-256-Hashes. Dokumentieren Sie die exakten Befehle und die verwendete
Lean-Toolchain (`leanprover/lean4:v4.33.1`). Transparenz: Für jedes Urteil muss der verwendete
Prüfschritt und das Rohergebnis (z. B. die Liste der überlebenden Mutanten) dokumentiert sein.
Präzise Sprache: Vermeiden Sie jedes Overclaiming. Unterscheiden Sie strikt zwischen „Kernel
akzeptiert den Term" und „der Term etabliert die mathematische Aussage".

*Fazit.* Die entscheidende Leerstelle ist die Ausführung der von Ihnen präzise benannten
Berechnungen. Mit den oben genannten Schritten und den verfügbaren Werkzeugen (laud, Lean Vacuity
Check, lean-proof-review und der `#deps`-Rezeptur) können Sie diese Lücke schließen. Das Ergebnis
wird kein bloßes Rahmenwerk mehr sein, sondern eine konkrete, reproduzierbare und forensische
Analyse des Alpöge-Archivs, die exakt zeigt, welche Definitionen lasttragend vakuuös sind und
welche mathematischen Beweispflichten daraus folgen. Das ist der Schritt, der Ihre Arbeit von
einer methodischen Spezifikation zu einem belastbaren wissenschaftlichen Ergebnis macht.

**Positioning points.** *1. Die offizielle Position der Lean-Community explizit einordnen.* Ihr
Papier erwähnt die Zertifizierung, aber Sie sollten die Tragweite und die Grenzen dieser
Zertifizierung klar benennen. Die Lean- und Mathlib-Communities haben am 21. November 2026
offiziell bestätigt, dass der Beweis den Kernel besteht. Diese Zertifizierung bezieht sich jedoch
ausdrücklich auf die formale Korrektheit des Terms (die Aussage ist korrekt, der Code kompiliert,
die Axiome sind sauber). Sie ist keine Aussage über die mathematische Gültigkeit der Definitionen,
auf denen der Term beruht. Ihre Arbeit sollte diese Unterscheidung nicht nur konstatieren, sondern
als zentralen Befund herausarbeiten: Die Community-Zertifizierung ist ein starkes Signal für die
Kernel-Ebene, lässt aber die von Nielsen aufgeworfene semantische Ebene vollständig unberührt.
*2. Die vacuity-Kritik als eigenständige, zitierfähige Position behandeln.* Nielsens Paper
„Invalidity of the Alpoge Proposed Proof of the Riemann Hypothesis" ist eine detaillierte,
quellcodebasierte Analyse. Sie listen die einzelnen Punkte (anyGeometry, hExpl6, etc.) auf, aber
Sie sollten sie als strukturierte, eigenständige Kritik präsentieren, die die entscheidende Frage
aufwirft: „Der Kernel verifiziert eine Ableitung relativ zu den gegebenen Definitionen. Er
verifiziert nicht, dass diese Definitionen die Mathematik tragen, die ihre Namen beanspruchen.
Hier tun sie es nicht." Dies ist der Kern Ihrer eigenen Forschungsfrage und sollte als solcher
explizit zitiert und eingeordnet werden. *3. Die werkzeuggestützte Operationalisierung als
methodischen Beitrag hervorheben.* Ihr Framework ist nicht nur eine theoretische Übung. Es
operationalisiert die von Nielsen und anderen aufgeworfene Frage mit konkreten, existierenden
Werkzeugen. Sie sollten explizit die Werkzeuge und Methoden nennen, die Sie für die entscheidende
Dependency-Trace und Load-Bearing-Analyse einsetzen werden: Für die Closure: Die „Shape 1: Forward
Transitive Closure"-Rezeptur, die `Expr.getUsedConstants` über Typ und Wert jeder erreichten
Deklaration iteriert, ist der de facto-Standard für diese Aufgabe. `#print axioms` ist dafür
explizit kein Ersatz. Für die Vakuuitätsprüfung: `laud mutate` ist ein speziell für die Prüfung
massiver, KI-generierter Lean-Repositories entwickeltes Werkzeug, das Theoreme gegen VACUOUS_TRUTH
und UNUSED_HYP stresstestet. Für die Kreuzvalidierung: Die Kombination aus `#deps` und `laud graph`
als zwei unabhängige Extraktoren ist eine methodische Stärke, die Sie hervorheben sollten.
*4. Die „epistemische Lücke" als zentrales Ergebnis Ihrer Arbeit formulieren.* Ihre Arbeit sollte
nicht nur ein Protokoll vorschlagen, sondern das Ergebnis der Anwendung dieses Protokolls liefern.
Die entscheidende Erkenntnis ist, dass die Kernel-Akzeptanz eine notwendige, aber keine
hinreichende Bedingung für mathematische Gültigkeit ist. Formulieren Sie dies als den Kernbefund
Ihrer Analyse: Es existiert eine epistemische Lücke zwischen dem, was der Kernel bestätigt (die
Existenz eines Terms vom Typ `RiemannHypothesis`), und dem, was die mathematische Gemeinschaft
unter einem Beweis versteht (die Etablierung der mathematischen Wahrheit durch nicht-vakuuöse
Argumente). *5. Einen klaren Ausblick auf die noch zu leistende Arbeit geben.* Da die entscheidende
Dependency-Trace für das Alpöge-Archiv noch nicht öffentlich durchgeführt wurde, sollte Ihr Papier
mit einem präzisen Forschungsprogramm schließen. Benennen Sie die konkreten, offenen Berechnungen,
die Ihre Arbeit oder nachfolgende Arbeiten durchführen müssen: die cross-validierte Closure, die
Load-Bearing-Analyse für jede markierte Deklaration und die daraus resultierende grafische
Aufbereitung der „roten" und „gelben" Knoten.

## Appendix B. Commands

```
git -c core.longpaths=true clone --depth 1 https://github.com/Deicyde/riemann-hypothesis external/alpoge-lean
git -C external/alpoge-lean config core.longpaths true
git -C external/alpoge-lean log -1 --format='%H %ad' --date=iso
lake -d external/alpoge-lean update
lake -d external/alpoge-lean exe cache get
python scripts/audit/rh_gap_closer.py --claim alpoge_2026 --archive external/alpoge-lean
python scripts/audit/rh_gap_closer.py --claim alpoge_2026 --local-control
```

In this run the checkout was moved to `C:\alpoge-archive` after the attempt, and the archive
command used the absolute path there. CI runners and Linux checkouts need no move: the 260-character
limit is a Windows property of the Lean toolchain, not of the archive.
