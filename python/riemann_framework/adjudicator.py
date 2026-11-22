# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Five probes, one aggregation, and no verdict that means "true".

This module is the executable form of the strongest claim the protocol makes: that
**kernel acceptance is necessary but not sufficient** for a formalised proof to establish
what it claims. It takes a claimed formalisation, runs five probes that answer different
questions, aggregates them by a rule that no single probe can override, and renders the
remaining gap as a colour-coded graph.

The five probes, and what each one actually is
----------------------------------------------
The specification names external tools for three of the five. Those tools are not
installed here, are not version-pinned here, and nothing in this module pretends to have
run them. What is implemented is a native equivalent for each, and the substitution is
recorded per probe so a reader can tell the difference between "this mechanism ran" and
"this mechanism's name appears in a report":

``KERNEL``
    `lake build` plus `#print axioms`, exactly as specified. Native, no substitution.

``MUTATION``
    A native engine, not `laud`. It copies the source file, applies one literal
    rewrite, compiles the copy, and attributes compile errors to the enclosing
    declaration. Four operators: ``VACUOUS_TRUTH`` (a hypothesis's type replaced by
    `True`), ``UNUSED_HYP`` (a hypothesis removed), ``BOUNDARY_SHIFT`` (a boundary
    literal shifted) and ``CONTENT_FLIP`` (a definition's body replaced by its
    canonical alternative). The first two are vacuity markers; the last is the
    load-bearing test, and it is the sharpest instrument in the panel: a theorem that
    still compiles after a suspect definition has been flipped to `False` does not use
    that definition's content at all. A mutant whose anchor is not on this machine is
    reported ``not run`` with its reason, never ``killed``: the live run on the published
    archive found that distinction by crashing on it.

``VACUITY``
    A textual census (``claim_audit.vacuity_census``), not the `is-my-lean-proof-vacuous`
    plugin. A **locator**: it finds the shapes an objection names and cannot show that
    any theorem depends on them.

``PROOF_REVIEW``
    The four layers, implemented as gates rather than as a checklist a person ticks:
    L1 soundness (the kernel probe), L2 statement faithfulness (the statement-identity
    check), L3 non-triviality (no surviving vacuity mutant and a clean trace), L4
    reporting (every finding carries a limit). L2 refutes when it fails, because a term of
    a different proposition refutes the identification the claim makes; L1 withholds
    rather than refutes, because a term that does not compile has not been read and
    killed. The vocabulary reserves `rejected` for screens, not for absent artefacts.

``DEPENDENCY_TRACE``
    ``#deps`` and ``#depsm`` over ``Environment.find?``: a forward transitive closure of
    the theorem over types and values, intersected with a suspect set, computed twice —
    once with Lean's own ``Expr.getUsedConstants`` and once with a structural recursion
    written out in the module — and compared. Identical closures corroborate the
    extraction; a difference leaves the probe ``undetermined`` with the reconciliation
    named. From the specification this probe inherits the rule and not the tool: the
    second extractor it names is `laud graph`, which is not installed here.

**`#print axioms` is never used as a dependency tracer.** Three declarations at different
depths can report the same three axioms and have completely different closures, because a
vacuous definition is a definition and not an axiom. The axiom audit answers "which
axioms", the trace answers "which definitions", and the two are not substitutes. Every
report this module emits repeats that sentence.

The aggregation rule
--------------------
Five probes, one table, and the falsification condition the specification states:

1. any probe returns `rejected` -> `rejected`;
2. every probe `outside domain` -> `outside domain`;
3. `kernel` and `dependency trace` both `validated (term)` and the review's L1/L2 gates
   pass and no vacuity mutant survives -> `validated (term)`;
4. otherwise `undetermined`, with the named computations that would move it.

Rule 3 is the whole point. A report cannot reach `validated (term)` while a `vacuous
truth` or `unused hypothesis` mutant survives, or while the trace was never run: the
aggregation refuses on the agent's behalf, so the overclaim cannot be made by forgetting a
probe. This is tested by driving each condition into its failing branch. The trace's
`validated (term)` is itself two facts, not one — a clean closure *and* a second
extractor's agreement on it — so an uncorroborated closure withholds the verdict one level
below the aggregation, where the specification puts the cross-validation.

The graph
---------
Nodes are coloured by the convention: **red** for a suspect the closure reaches (a
load-bearing vacuous witness), **amber** for a flagged definition the closure does *not*
reach (the objection does not bite on it), **green** for a theorem under adjudication,
**grey** for a count of closure members the figure does not enumerate. Flags come from
the probes rather than from a list written by hand in the record. Edges are reachability
claims from one closure computation, not a per-node edge set: a true edge list would need
one `#deps` run per node, and the report says so next to the legend rather than implying a
completeness it does not have.

What it cannot do, in one place
-------------------------------
It cannot decide whether a definition's content is *mathematically* the right content; it
can only show whether a theorem's proof uses it. It cannot run on an archive that is not on
the machine. Its two extractors share one environment, so their agreement rules out a
defect in this module and not a defect in Lean or in the definitions a closure passes
through. It does not repair proofs, does not search for them, and has no verdict on the
Riemann hypothesis. The word "valid" does not appear in its vocabulary: the strongest thing
it can say is ``validated (term)``, which is a statement about a term.
"""

from __future__ import annotations

import html
import json
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from .claim_audit import (
    Claim,
    ClaimReport,
    Finding,
    Instrument,
    Level,
    Status,
    Verdict,
    audit_claim,
    run_lean,
)

#: The sentence every report carries, because the temptation it forecloses is the whole
#: subject of the module.
AXIOM_TRAP_NOTE = (
    "`#print axioms` is not a dependency tracer: a vacuous definition is a definition, "
    "not an axiom, so a clean axiom audit is silent about it. Only the forward closure "
    "can say whether the theorem reaches it."
)

STANDING_POSITION = (
    "An adjudication is a statement about a term, and it is not a certification of "
    "mathematics. `validated (term)` means a proof term inhabits the stated type; for a "
    "faithful statement under a sound kernel that is a derivation of the proposition "
    "relative to the definitions the statement invokes, and it settles neither whether "
    "those definitions are the intended ones nor whether the argument is the argument "
    "claimed. No verdict here certifies the Riemann hypothesis: the framework records "
    "what an instrument established, and it has no instrument that decides whether the "
    "formalised statement is the statement mathematics intends."
)


class Probe(str, Enum):
    """The five probes, in the order the report prints them."""

    KERNEL = "KERNEL"
    MUTATION = "MUTATION"
    VACUITY = "VACUITY"
    PROOF_REVIEW = "PROOF_REVIEW"
    DEPENDENCY_TRACE = "DEPENDENCY_TRACE"


#: Probes whose survival is a vacuity marker, and therefore blocks `validated (term)`.
#: `CONTENT_FLIP` is absent on purpose: a flipped definition that a theorem survives is
#: evidence the definition is *not* load-bearing, which is the opposite of an objection.
BLOCKING_OPERATORS = ("VACUOUS_TRUTH", "UNUSED_HYP")


@dataclass(frozen=True)
class ProbeResult:
    """One probe's verdict, its evidence, and what would change it.

    `named_computation` is required for `undetermined`, checked at construction. A report
    that says "undetermined" without naming the computation that would settle it is the
    thing the protocol exists to prevent.
    """

    probe: Probe
    verdict: Verdict
    status: Status
    evidence: str
    named_computation: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.verdict is Verdict.UNDETERMINED and not self.named_computation:
            raise ValueError(
                f"{self.probe.value}: an undetermined probe must name its computation"
            )

    @property
    def blocked(self) -> bool:
        return self.verdict is not Verdict.VALIDATED_TERM

    def as_dict(self) -> dict[str, Any]:
        return {
            "probe": self.probe.value,
            "verdict": self.verdict.value,
            "status": self.status.value,
            "evidence": self.evidence,
            "named_computation": self.named_computation,
            "details": dict(self.details),
        }


# ============================================================
# The mutation engine
# ============================================================

_DECLARATION = re.compile(
    r"(?m)^\s*(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(?:theorem|lemma|def|abbrev|example|instance|structure|inductive)\s+"
    r"([A-Za-z_][\w'.]*)"
)
_ERROR_LINE = re.compile(r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+):\s*error", re.MULTILINE)


@dataclass(frozen=True)
class Mutant:
    """One literal rewrite of one source file, with the theorem it is testing.

    The engine refuses a mutant whose `find` text is not unique in the source: applying an
    ambiguous rewrite would silently test something other than what the record says.
    """

    id: str
    operator: str
    source: str
    find: str
    replace: str
    theorem: str
    note: str = ""

    @classmethod
    def from_record(cls, entry: Mapping[str, Any]) -> "Mutant":
        required = ("id", "operator", "source", "find", "replace", "theorem")
        missing = [key for key in required if key not in entry]
        if missing:
            raise ValueError(f"mutant {entry.get('id')!r}: missing {missing}")
        return cls(
            id=entry["id"],
            operator=entry["operator"],
            source=entry["source"],
            find=entry["find"],
            replace=entry["replace"],
            theorem=entry["theorem"],
            note=entry.get("note", ""),
        )

    @property
    def declaration(self) -> str | None:
        """The declaration the rewrite lands in, read off the anchor.

        The record says what it rewrites in `find`, so the name is derivable rather than
        stored twice; a mutant whose anchor names no declaration returns None and is
        recorded as unattributed rather than guessed at.
        """
        match = _DECLARATION.match(self.find)
        return match.group(1) if match else None


def enclosing_declaration(source: str, line: int) -> str | None:
    """The declaration whose body contains `line` (1-based), or None.

    Compile errors are reported by position; the probe needs the declaration name to
    attribute a kill. The scan is textual and one-directional, which is enough because
    Lean's own declarations start at column zero or after indentation in a namespace.
    """
    best: str | None = None
    for match in _DECLARATION.finditer(source):
        start = source.count("\n", 0, match.start()) + 1
        if start <= line:
            best = match.group(1)
        else:
            break
    return best


@dataclass(frozen=True)
class MutationOutcome:
    """What one mutant did to one theorem.

    `ran` is separate from `compiled` on purpose. A mutant whose source is not on this
    machine did not compile and did not survive, and reporting it as "killed" would be a
    verdict from a check that never happened; the first version of this engine did
    exactly that, and the live run on the published archive found it by crashing.
    """

    mutant: Mutant
    ran: bool
    compiled: bool
    failed_declarations: tuple[str, ...]
    survived: bool
    unattributed: bool
    reason: str = ""

    @property
    def killed(self) -> bool:
        return self.ran and not self.survived

    @property
    def is_vacuity_marker(self) -> bool:
        return self.mutant.operator in BLOCKING_OPERATORS

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.mutant.id,
            "operator": self.mutant.operator,
            "theorem": self.mutant.theorem,
            "ran": self.ran,
            "compiled": self.compiled,
            "failed_declarations": list(self.failed_declarations),
            "survived": self.survived,
            "unattributed": self.unattributed,
            "vacuity_marker": self.is_vacuity_marker,
            "note": self.mutant.note,
            "reason": self.reason,
        }


#: Compile results, keyed by the rewrite rather than by the mutant: two records may test
#: the same flipped definition against different theorems, and one compile answers both.
_COMPILED: dict[tuple, tuple[bool, tuple[str, ...]]] = {}


def _compile_mutant(
    project_root: Path, mutant: Mutant, timeout: int
) -> tuple[bool, tuple[str, ...]]:
    """Compile the mutated copy once; return `(compiled, failed declarations)`.

    The copy is written under `out/adjudication/_mutants/` and the tracked file is never
    touched: a checker that edits the tree it is checking can leave it edited, and an
    interrupted run would then look like a mutation that stayed.
    """
    key = (str(project_root.resolve()), mutant.source, mutant.find, mutant.replace)
    if key in _COMPILED:
        return _COMPILED[key]
    source_path = (project_root / mutant.source).resolve()
    text = source_path.read_text(encoding="utf-8")
    occurrences = text.count(mutant.find)
    if occurrences != 1:
        raise ValueError(
            f"mutant {mutant.id!r}: the anchor occurs {occurrences} times in "
            f"{mutant.source}; a mutant must be unambiguous"
        )
    mutated = text.replace(mutant.find, mutant.replace, 1)
    run = run_lean(
        project_root, mutated, name=f"mutant_{mutant.id}", timeout=timeout
    )
    failed: list[str] = []
    for match in _ERROR_LINE.finditer(run.output):
        # The line number is in the message; the *offset* is an offset into the
        # compiler's output, not into the source. The first version counted newlines in
        # the source up to `match.start()`, which put every error on line 1 or 2 and
        # therefore attributed nothing: every mutant came back "survived". The controls
        # in `test_alpoge_claim.py` now pin a kill, which is what this bug needed.
        line = int(match.group("line"))
        name = enclosing_declaration(mutated, line)
        if name and name not in failed:
            failed.append(name)
    result = (run.ok, tuple(failed))
    _COMPILED[key] = result
    return result


def run_mutant(
    project_root: Path,
    mutant: Mutant,
    *,
    timeout: int = 1800,
) -> MutationOutcome:
    """One mutant against one theorem: killed if that theorem appears among the errors.

    A mutant whose anchor is not on this machine is recorded as not run, with the reason.
    That case is not hypothetical: the claim record declares a mutant against the
    published archive, and the archive is not here.
    """
    source_path = (project_root / mutant.source).resolve()
    if not source_path.is_file():
        return MutationOutcome(
            mutant=mutant, ran=False, compiled=False, failed_declarations=(),
            survived=False, unattributed=True,
            reason=f"the mutant's source is not on this machine: {mutant.source}",
        )
    try:
        compiled, failed = _compile_mutant(project_root, mutant, timeout)
    except ValueError as error:
        return MutationOutcome(
            mutant=mutant, ran=False, compiled=False, failed_declarations=(),
            survived=False, unattributed=True, reason=str(error),
        )
    survived = mutant.theorem not in failed
    return MutationOutcome(
        mutant=mutant,
        ran=True,
        compiled=compiled,
        failed_declarations=failed,
        survived=survived,
        unattributed=bool(not survived and not failed),
    )


# ============================================================
# The probes
# ============================================================

def _formal_findings(report: ClaimReport) -> list[Finding]:
    return [f for f in report.findings if f.level is Level.FORMAL]


def probe_kernel(report: ClaimReport) -> ProbeResult:
    """`lake build` + `#print axioms`: does a term of the stated type exist?"""
    findings = [
        f for f in _formal_findings(report)
        if f.instrument_class is Instrument.KERNEL
    ]
    if not findings:
        return ProbeResult(
            Probe.KERNEL, Verdict.OUTSIDE_DOMAIN, Status.NOT_APPLICABLE,
            "the claim supplies no formal artefact, so no kernel question was asked",
        )
    failed = [f for f in findings if f.status is Status.CHECKED_FAILED]
    if failed:
        return ProbeResult(
            Probe.KERNEL, Verdict.UNDETERMINED, Status.CHECKED_FAILED,
            "; ".join(f"{f.check}: {f.evidence}" for f in failed)[:600],
            named_computation=(
                "discharge the failing kernel condition: "
                + "; ".join(f.check for f in failed)
            ),
            details={"failed": [f.check for f in failed]},
        )
    return ProbeResult(
        Probe.KERNEL, Verdict.VALIDATED_TERM, Status.CHECKED_OK,
        "compiled, no `sorry`, axioms within {propext, Classical.choice, Quot.sound}, "
        "statement identified",
        details={"findings": len(findings)},
    )


def probe_vacuity(report: ClaimReport) -> ProbeResult:
    """The census: where the objectional shapes are, textually.

    Deliberately weak. A clean census earns `validated (term)` only in the heuristic
    sense the specification allows, and the aggregation rule is written so that this
    verdict alone can never promote a report past `undetermined`.
    """
    census = [
        f for f in report.findings
        if f.instrument_class is Instrument.VACUITY_SCAN
    ]
    flagged: list[str] = []
    for finding in census:
        for name in finding.details.get("true_bodied", []):
            if name not in flagged:
                flagged.append(name)
    if not census:
        return ProbeResult(
            Probe.VACUITY, Verdict.OUTSIDE_DOMAIN, Status.NOT_APPLICABLE,
            "no artefact was scanned, so the census has nothing to report",
        )
    scanned = [finding for finding in census if finding.details.get("scanned")]
    if not scanned:
        # An artefact that is not on the machine produces a census with `scanned: false`
        # and no shapes. Reading that as "no shapes found" would turn an absence of the
        # evidence into evidence of absence, which is the same error as reading a clean
        # axiom audit as a dependency result.
        return ProbeResult(
            Probe.VACUITY, Verdict.UNDETERMINED, Status.NOT_RUN,
            "the census could not read the artefact, so it located nothing rather than "
            "finding nothing",
            named_computation=(
                "put the artefact's source on this machine and rerun the census"
            ),
            details={"flagged": [], "scanned": False},
        )
    if flagged:
        return ProbeResult(
            Probe.VACUITY, Verdict.UNDETERMINED, Status.CHECKED_FAILED,
            "the census flagged " + ", ".join(f"`{name}`" for name in flagged),
            named_computation=(
                "run the dependency trace on " + ", ".join(flagged)
                + ", then mutate each and recompile"
            ),
            details={"flagged": flagged},
        )
    return ProbeResult(
        Probe.VACUITY, Verdict.VALIDATED_TERM, Status.CHECKED_OK,
        "the census located no `True`-bodied predicate, no proposition alias and no "
        "`rfl`-fixed value in the scanned source (heuristic; the trace decides)",
        details={"flagged": []},
    )


def mutation_verdict(
    outcomes: Sequence[MutationOutcome],
    *,
    declared: bool,
    live: bool,
) -> ProbeResult:
    """Aggregate the mutant outcomes into the probe's verdict.

    Split from the runner so that the outcomes are computed once and both the probe and
    the report read the same objects; a second run could differ, and a report whose table
    disagreed with its own evidence would be worse than no report.
    """
    if not declared:
        return ProbeResult(
            Probe.MUTATION, Verdict.OUTSIDE_DOMAIN, Status.NOT_APPLICABLE,
            "no mutant was declared, so mutation testing was not attempted",
        )
    if not live or not outcomes:
        return ProbeResult(
            Probe.MUTATION, Verdict.UNDETERMINED, Status.NOT_RUN,
            "mutation testing needs a Lean toolchain; it was not requested",
            named_computation="rerun with live Lean: `python scripts/adjudicate.py`",
        )
    not_run = [o for o in outcomes if not o.ran]
    survivors = [o for o in outcomes if o.ran and o.survived]
    blocking = [o for o in survivors if o.is_vacuity_marker]
    summary = "; ".join(
        f"{o.mutant.id} ({o.mutant.operator}) -> "
        + (
            "not run" if not o.ran
            else "survived" if o.survived
            else "killed"
        )
        + f" for `{o.mutant.theorem}`"
        for o in outcomes
    )
    if blocking:
        return ProbeResult(
            Probe.MUTATION, Verdict.UNDETERMINED, Status.CHECKED_FAILED, summary,
            named_computation=(
                "eliminate the surviving vacuity mutant(s): "
                + ", ".join(f"{o.mutant.id} [{o.mutant.operator}]" for o in blocking)
                + "; the hypothesis each one removes is doing no work in that proof"
            ),
            details={"outcomes": [o.as_dict() for o in outcomes]},
        )
    if not_run:
        return ProbeResult(
            Probe.MUTATION, Verdict.UNDETERMINED, Status.NOT_RUN, summary,
            named_computation=(
                "make the declared mutant runnable and rerun it: "
                + "; ".join(f"{o.mutant.id}: {o.reason}" for o in not_run)
            ),
            details={"outcomes": [o.as_dict() for o in outcomes]},
        )
    return ProbeResult(
        Probe.MUTATION, Verdict.VALIDATED_TERM, Status.CHECKED_OK, summary,
        details={"outcomes": [o.as_dict() for o in outcomes]},
    )


def probe_proof_review(
    report: ClaimReport,
    kernel: ProbeResult,
    trace: ProbeResult,
    mutation: ProbeResult,
) -> ProbeResult:
    """The four layers, as gates.

    L1 and L2 blocking is the specification's hard requirement, and it is implemented as
    precedence rather than as a warning: a report whose L1 or L2 *fails* is `rejected` even
    if every other probe is clean, because a term that does not compile or a statement
    that is not the claimed one has not been adjudicated at all.

    A layer that did not run is a third case, and it is not a failure. The first version
    of this function collapsed them, and a run without Lean — where the live target is
    `not_run` by request — came back `rejected`, which is a verdict from a check that never
    happened. `not established` withholds the verdict; it does not accuse the artefact.
    """
    statement_rows = [
        f for f in _formal_findings(report)
        if f.check.endswith("the Riemann hypothesis")
    ]
    if kernel.verdict is Verdict.VALIDATED_TERM:
        l1 = "passed"
    elif kernel.status is Status.CHECKED_FAILED:
        l1 = "failed"
    else:
        l1 = "not established"
    l2 = _gate(statement_rows)
    l3 = (
        trace.verdict is Verdict.VALIDATED_TERM
        and mutation.verdict is Verdict.VALIDATED_TERM
    )
    l4 = all(f.limits.strip() for f in report.findings) and bool(report.findings)
    layers = {
        "L1_soundness": l1,
        "L2_statement_faithfulness": l2,
        "L3_non_triviality": "passed" if l3 else "not established",
        "L4_reporting": "passed" if l4 else "failed",
    }
    failed = [name for name in ("L1_soundness", "L2_statement_faithfulness")
              if layers[name] == "failed"]
    if failed:
        # A statement that is not the claimed one refutes the identification the claim
        # makes, and that is a logical screen: `rejected`. A term that does not compile,
        # or that is completed by `sorryAx`, has not been rejected by a screen at all: it
        # has failed to be an artefact, and the vocabulary reserves `rejected` for
        # arguments that were read and killed. The paper's Definition of the verdicts and
        # `claim_audit._formal_verdict` already say this; the first version of this
        # function did not, and the live control came back `rejected` for containing the
        # two `sorry`s it is built to contain.
        if "L2_statement_faithfulness" in failed:
            return ProbeResult(
                Probe.PROOF_REVIEW, Verdict.REJECTED, Status.CHECKED_FAILED,
                "the statement-identity layer failed: the artefact proves a different "
                "proposition from the one the claim names.",
                named_computation=(
                    "state the claimed proposition as the artefact's type and rerun the "
                    "review"
                ),
                details={"layers": layers, "blocking_failures": failed},
            )
        return ProbeResult(
            Probe.PROOF_REVIEW, Verdict.UNDETERMINED, Status.CHECKED_FAILED,
            "L1 fails: " + ", ".join(failed)
            + ". The artefact establishes nothing, so there is nothing to review; this is "
            "not a rejection, because no screen was applied to an argument.",
            named_computation=(
                "discharge the failing kernel condition: "
                + "; ".join(f"{name} is not established" for name in failed)
            ),
            details={"layers": layers, "blocking_failures": failed},
        )
    pending = [
        name for name in ("L1_soundness", "L2_statement_faithfulness")
        if layers[name] != "passed"
    ]
    if pending:
        return ProbeResult(
            Probe.PROOF_REVIEW, Verdict.UNDETERMINED, Status.NOT_RUN,
            "blocking layer(s) not established: " + ", ".join(pending)
            + ". Nothing failed here; the checks did not run, and an unrun check is not a "
            "pass.",
            named_computation=(
                "run the kernel probe with Lean and the statement-identity check on a "
                "target that builds, then rerun the review"
            ),
            details={"layers": layers, "pending": pending},
        )
    if not l3:
        return ProbeResult(
            Probe.PROOF_REVIEW, Verdict.UNDETERMINED, Status.CHECKED_OK,
            "L1 and L2 pass; L3 fails because "
            + ("the trace is not clean" if trace.verdict is not Verdict.VALIDATED_TERM
               else "a vacuity mutant survives"),
            named_computation=(
                trace.named_computation or mutation.named_computation
                or "make L3 pass"
            ),
            details={"layers": layers},
        )
    return ProbeResult(
        Probe.PROOF_REVIEW, Verdict.VALIDATED_TERM, Status.CHECKED_OK,
        "L1-L4 pass" + ("" if l4 else " (L4: a finding is missing its limit)"),
        details={"layers": layers},
    )


def _gate(findings: Sequence[Finding]) -> str:
    """`passed`, `failed` or `not established` for one layer's findings.

    `not established` covers the three ways a finding can be present and silent — not run,
    recorded from someone else's run, undetermined — and it is the difference between "we
    have not asked" and "the answer was no".
    """
    statuses = {finding.status for finding in findings}
    if Status.CHECKED_FAILED in statuses:
        return "failed"
    if findings and statuses == {Status.CHECKED_OK}:
        return "passed"
    return "not established"


def probe_dependency_trace(report: ClaimReport) -> ProbeResult:
    """The decisive probe: does the closure reach a flagged definition, and is the closure
    itself corroborated?

    Two questions, one verdict, and the second is not optional. A closure is a claim about
    a term, and a claim about a term that rests on one traversal is a claim with an
    unexamined premise; so the specification's rule is applied here as written: identical
    closures from two extractors corroborate the extraction, a difference leaves the probe
    `undetermined` with the reconciliation named, and fallback to one extractor is a
    recorded fallback rather than a pass.
    """
    findings = [
        f for f in report.findings
        if f.instrument_class is Instrument.DEPENDENCY_TRACE
    ]
    if not findings:
        return ProbeResult(
            Probe.DEPENDENCY_TRACE, Verdict.OUTSIDE_DOMAIN, Status.NOT_APPLICABLE,
            "the claim declares no trace target, so no closure was computed",
        )
    not_run = [f for f in findings if f.status is Status.NOT_RUN]
    reached: list[str] = []
    closures: list[dict[str, Any]] = []
    cross: list[dict[str, Any]] = []
    for finding in findings:
        payload = dict(finding.details)
        if payload:
            closures.append(payload)
            reached.extend(payload.get("reached", []))
            if payload.get("cross_validation"):
                cross.append(dict(payload["cross_validation"]))
    if reached:
        return ProbeResult(
            Probe.DEPENDENCY_TRACE, Verdict.UNDETERMINED, Status.CHECKED_FAILED,
            "the closure reaches " + ", ".join(f"`{n}`" for n in sorted(set(reached))),
            named_computation=(
                "refactor so the theorem does not reach "
                + ", ".join(sorted(set(reached)))
            ),
            details={"reached": sorted(set(reached)), "closures": closures},
        )
    if not_run:
        return ProbeResult(
            Probe.DEPENDENCY_TRACE, Verdict.UNDETERMINED, Status.NOT_RUN,
            "the trace did not run: " + not_run[0].evidence.split("\n")[0][:300],
            named_computation=(
                "run the trace with the artefact in place; the driver is in the finding"
            ),
            details={"not_run": len(not_run), "closures": closures},
        )
    disagreements = [c for c in cross if c.get("discrepancy") is True]
    uncorroborated = [c for c in cross if c.get("agreement") is not True]
    if disagreements:
        first = disagreements[0]
        return ProbeResult(
            Probe.DEPENDENCY_TRACE, Verdict.UNDETERMINED, Status.CHECKED_FAILED,
            "the two extractors disagree on `" + str(first.get("theorem"))
            + "`: " + str(first.get("only_in_first_count")) + " name(s) only in `#deps`, "
            + str(first.get("only_in_second_count")) + " only in `#depsm`",
            named_computation=first.get("named_computation")
            or "reconcile the closure mismatch",
            details={
                "reached": [], "closures": closures, "cross_validation": cross,
                "discrepancy": True,
            },
        )
    if uncorroborated or not cross:
        why = (
            "no cross-validation record was produced, so the closure is one instrument's "
            "reading"
            if not cross else str(uncorroborated[0].get("named_computation"))
        )
        return ProbeResult(
            Probe.DEPENDENCY_TRACE, Verdict.UNDETERMINED, Status.CHECKED_OK,
            "the closure reaches none of the declared suspects, but " + why,
            named_computation=why,
            details={"reached": [], "closures": closures, "cross_validation": cross},
        )
    return ProbeResult(
        Probe.DEPENDENCY_TRACE, Verdict.VALIDATED_TERM, Status.CHECKED_OK,
        "; ".join(
            f"`{c.get('theorem')}`'s closure of {c.get('closure')} reaches none of its "
            f"{len(c.get('suspects', []))} suspects, and both extractors agree on all "
            f"{c.get('closure')} names"
            for c in closures
        ) or "every declared trace came back clean",
        details={
            "reached": [], "closures": closures, "cross_validation": cross,
            "discrepancy": False,
        },
    )


# ============================================================
# Aggregation
# ============================================================

def aggregate(probes: Sequence[ProbeResult]) -> Verdict:
    """The specification's table, plus its falsification condition.

    The condition is enforced structurally rather than remembered: `validated (term)`
    requires the kernel probe, the trace probe *and* the review to agree, and a surviving
    vacuity mutant forces the review to withhold. Deleting a probe cannot promote the
    report; only running it can.
    """
    by_probe = {probe.probe: probe for probe in probes}
    if any(probe.verdict is Verdict.REJECTED for probe in probes):
        return Verdict.REJECTED
    if probes and all(p.verdict is Verdict.OUTSIDE_DOMAIN for p in probes):
        return Verdict.OUTSIDE_DOMAIN
    kernel = by_probe.get(Probe.KERNEL)
    trace = by_probe.get(Probe.DEPENDENCY_TRACE)
    review = by_probe.get(Probe.PROOF_REVIEW)
    if kernel is None or trace is None or review is None:
        return Verdict.UNDETERMINED
    if (
        kernel.verdict is Verdict.VALIDATED_TERM
        and trace.verdict is Verdict.VALIDATED_TERM
        and review.verdict is Verdict.VALIDATED_TERM
    ):
        return Verdict.VALIDATED_TERM
    return Verdict.UNDETERMINED


def named_computations(probes: Sequence[ProbeResult]) -> tuple[str, ...]:
    """Every distinct computation that would move a probe off `undetermined`."""
    seen: list[str] = []
    for probe in probes:
        if probe.verdict is Verdict.UNDETERMINED and probe.named_computation:
            entry = f"{probe.probe.value}: {probe.named_computation}"
            if entry not in seen:
                seen.append(entry)
    return tuple(seen)


# ============================================================
# The graph
# ============================================================

#: Green: in the closure, no flag. Amber: flagged, not reached. Red: flagged and
#: reached. Grey: outside the closure.
COLOURS = {
    "green": "#2e7d32",
    "amber": "#ef6c00",
    "red": "#c62828",
    "grey": "#9e9e9e",
}


@dataclass(frozen=True)
class GraphNode:
    name: str
    colour: str
    role: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "colour": self.colour, "role": self.role}


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str

    def as_dict(self) -> dict[str, str]:
        return {"source": self.source, "target": self.target,
                "relation": self.relation}


@dataclass(frozen=True)
class Graph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    caveat: str

    def counts(self) -> dict[str, int]:
        counts = {name: 0 for name in COLOURS}
        for node in self.nodes:
            counts[node.colour] = counts.get(node.colour, 0) + 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.as_dict() for node in self.nodes],
            "edges": [edge.as_dict() for edge in self.edges],
            "counts": self.counts(),
            "caveat": self.caveat,
        }

    @property
    def red(self) -> tuple[str, ...]:
        return tuple(n.name for n in self.nodes if n.colour == "red")


def discovered_flags(report: ClaimReport) -> tuple[str, ...]:
    """The names the probes flagged, as distinct from the names the record declared.

    The graph is coloured from what the instruments found, not from a list written by
    hand in the claim record. The census locates `True`-bodied definitions; each one is a
    flag here whether or not the record named it. A mutant's anchor contributes to the
    *review* and to a node's role text rather than to a flag, because a mutant rewrites a
    declaration and does not by itself say which node an objection is about.
    """
    flags: list[str] = []
    for finding in report.findings:
        if finding.instrument_class is not Instrument.VACUITY_SCAN:
            continue
        for name in finding.details.get("true_bodied", ()):
            text = str(name)
            if text not in flags:
                flags.append(text)
    return tuple(flags)


def load_bearing(outcomes: Sequence[MutationOutcome]) -> tuple[str, ...]:
    """Declarations a killed content flip implicates: the theorem's proof needed them.

    This is the dynamic counterpart of the trace's `reached`, and it is not a substitute
    for it: a flip is killed when *any* declaration in the file stops compiling, so the
    attribution is to the mutant's own anchor and to nothing else.
    """
    names: list[str] = []
    for outcome in outcomes:
        if not (outcome.ran and outcome.killed):
            continue
        if outcome.mutant.operator != "CONTENT_FLIP":
            continue
        name = outcome.mutant.declaration
        if name and name not in names:
            names.append(name)
    return tuple(names)


def _answers_to(suspect: str, reached: Sequence[str]) -> bool:
    """Does any fully qualified name in `reached` answer to the short `suspect`?

    The closure is printed with qualified names (`RiemannFramework.vacuousGeometry`) and
    the record quotes short ones (`vacuousGeometry`), so an exact-match test colours a
    reached suspect amber. It did, in the first live run: the graph showed zero red nodes
    while the trace probe was reporting a hit in the same report.
    """
    suffix = "." + suspect
    return any(name == suspect or name.endswith(suffix) for name in reached)


def build_graph(
    trace: ProbeResult,
    *,
    theorems: Sequence[str] = (),
    flagged: Sequence[str] = (),
    load_bearing_names: Sequence[str] = (),
) -> Graph:
    """Colour the suspects and the load-bearing members of the closure.

    The closure of a Mathlib-backed theorem runs to thousands of names, so the graph
    carries the suspects, the theorems and a bounded sample of the rest; the counts in the
    report carry the total. Edges are reachability from the single closure computation,
    which is stated next to the legend.

    The four colours are the ones the instruments can decide. The specification also names
    a fifth, for a definition the mathematics requires and the closure does not reach;
    nothing in this repository computes "what the mathematics requires", so there is no
    fifth colour and the absence is stated rather than filled with a guess.
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    seen: set[str] = set()
    for theorem in theorems:
        if theorem not in seen:
            seen.add(theorem)
            nodes.append(GraphNode(theorem, "green", "theorem under adjudication"))
    reached = list(trace.details.get("reached", []))
    suspects: list[str] = []
    closures = trace.details.get("closures", [])
    for payload in closures:
        for suspect in payload.get("suspects", []):
            if suspect not in suspects:
                suspects.append(suspect)
    for name in flagged:
        if name not in suspects:
            suspects.append(name)
    for suspect in suspects:
        colour = "red" if _answers_to(suspect, reached) else "amber"
        role = (
            "flagged and reached: a load-bearing vacuous witness"
            if colour == "red"
            else "flagged but not reached: the objection does not bite here"
        )
        if suspect in load_bearing_names and colour == "amber":
            role += "; a content flip of it is killed, so it is load-bearing elsewhere"
        if suspect not in seen:
            seen.add(suspect)
            nodes.append(GraphNode(suspect, colour, role))
        for theorem in theorems:
            edges.append(GraphEdge(theorem, suspect, "reaches" if colour == "red"
                                   else "does not reach"))
    for payload in closures:
        theorem = str(payload.get("theorem", ""))
        closure = int(payload.get("closure", 0))
        if theorem and closure and theorem not in seen:
            seen.add(theorem)
            nodes.append(GraphNode(theorem, "green", "theorem under adjudication"))
        if theorem:
            nodes.append(
                GraphNode(
                    f"{closure} further constants",
                    "grey",
                    "closure members not shown (count, not names)",
                )
            )
            seen.add(f"{closure} further constants")
    caveat = (
        "Edges are reachability claims from one forward-closure computation, not a "
        "per-node edge set: an edge-complete graph would need one `#deps` run per node. "
        "Grey counts the closure members this figure does not enumerate. Red is a "
        "load-bearing suspect, amber a flagged definition the closure never reaches. "
        "There is no colour for `mathematically required but not reached`: no instrument "
        "here decides what the mathematics requires."
    )
    return Graph(tuple(nodes), tuple(edges), caveat)


# ============================================================
# The adjudication
# ============================================================

@dataclass(frozen=True)
class Adjudication:
    claim_id: str
    probes: tuple[ProbeResult, ...]
    final_verdict: Verdict
    graph: Graph
    report: ClaimReport
    mutants: tuple[MutationOutcome, ...] = ()
    role: str = ""

    @property
    def named(self) -> tuple[str, ...]:
        return named_computations(self.probes)

    def probe(self, which: Probe) -> ProbeResult:
        for result in self.probes:
            if result.probe is which:
                return result
        raise KeyError(which)

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim_id,
            "role": self.role,
            "final_verdict": self.final_verdict.value,
            "named_computations": list(self.named),
            "probes": [probe.as_dict() for probe in self.probes],
            "graph": self.graph.as_dict(),
            "mutants": [outcome.as_dict() for outcome in self.mutants],
            "axiom_trap_note": AXIOM_TRAP_NOTE,
            "position": STANDING_POSITION,
            "claim_report": self.report.to_dict(),
        }


def adjudicate(
    claim: Claim,
    project_root: Path,
    *,
    mutants: Sequence[Mutant] = (),
    live_lean: bool = True,
    timeout: int = 1800,
    role: str | None = None,
) -> Adjudication:
    """Run the five probes on one claimed artefact and aggregate them.

    The claim report is produced first, because four of the five probes read findings it
    already carries: running the kernel twice would be two statements of the same fact,
    and the second one could drift.

    `role` selects one formal target, and a panel is about one artefact. A claim record can
    carry its own negative control, and pooling the two makes the control's deliberate
    `sorry` the claim's verdict; the first live run did exactly that and was fixed by
    passing the role through to the audit rather than by special-casing the control.
    """
    report = audit_claim(
        claim, project_root, live_lean=live_lean, timeout=timeout, role=role
    )
    kernel = probe_kernel(report)
    vacuity = probe_vacuity(report)
    trace = probe_dependency_trace(report)
    outcomes = (
        tuple(run_mutant(project_root, mutant, timeout=timeout) for mutant in mutants)
        if mutants and live_lean else ()
    )
    mutation = mutation_verdict(outcomes, declared=bool(mutants), live=live_lean)
    review = probe_proof_review(report, kernel, trace, mutation)
    probes = (kernel, mutation, vacuity, review, trace)
    theorems = tuple(
        payload["theorem"]
        for payload in trace.details.get("closures", [])
        if payload.get("theorem")
    )
    if not theorems:
        theorems = tuple(
            request.theorem
            for target in claim.formal
            if role is None or target.role == role
            for request in target.trace
        )
    return Adjudication(
        claim_id=claim.id,
        probes=probes,
        final_verdict=aggregate(probes),
        graph=build_graph(
            trace,
            theorems=theorems,
            flagged=discovered_flags(report),
            load_bearing_names=load_bearing(outcomes),
        ),
        report=report,
        mutants=outcomes,
        role=role or "",
    )


# ============================================================
# Deliverables
# ============================================================

def render_json(adjudication: Adjudication) -> str:
    return json.dumps(adjudication.as_dict(), indent=2, ensure_ascii=False) + "\n"


_TEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex_escape(text: str) -> str:
    """Escape the characters LaTeX would otherwise read as markup.

    Underscores are the common case: Lean names are full of them, and an unescaped one
    turns a table row into a subscript and a compile error.
    """
    return "".join(_TEX_ESCAPES.get(char, char) for char in text)


def render_tex(adjudication: Adjudication) -> str:
    """A table and a paragraph a paper can `\\input` directly."""
    lines = [
        "% generated by riemann_framework.adjudicator; do not edit by hand",
        r"\providecommand{\verdict}[1]{\textsf{#1}}",
        r"\begin{table}[t]",
        r"\centering",
        r"\footnotesize",
        r"\begin{tabularx}{\textwidth}{@{}"
        r">{\raggedright\arraybackslash}p{2.7cm}"
        r">{\raggedright\arraybackslash}p{2.3cm}"
        r">{\raggedright\arraybackslash}X@{}}",
        r"\toprule",
        r"Probe & Verdict & What would change it \\",
        r"\midrule",
    ]
    for probe in adjudication.probes:
        change = probe.named_computation or "nothing: the probe is decided"
        lines.append(
            f"{tex_escape(probe.probe.value)} & "
            f"\\verdict{{{tex_escape(probe.verdict.value)}}} & "
            f"{tex_escape(change)} \\\\"
        )
    lines += [
        r"\midrule",
        f"\\multicolumn{{2}}{{@{{}}l}}{{Aggregated}} & "
        f"\\verdict{{{tex_escape(adjudication.final_verdict.value)}}} \\\\",
        r"\bottomrule",
        r"\end{tabularx}",
        r"\caption{Five probes on \\texttt{" + tex_escape(adjudication.claim_id)
        + (r"} (\texttt{" + tex_escape(adjudication.role) + "})" if adjudication.role else "}")
        + r" and the verdict they aggregate to. No row is a substitute for another: "
        r"the kernel row can be clean while the trace row is not, and the aggregation "
        r"refuses a term verdict in that case.}",
        r"\label{tab:adjudication}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def render_gap_statement(adjudication: Adjudication) -> str:
    """The prose paragraph: which computations would move the verdict, and no more.

    Section 2b is the cross-validation record, and it is a section rather than a footnote
    because it reports the one thing a single extractor cannot: whether the closure the
    verdict rests on is the same closure a second implementation computes. A disagreement
    is printed with both name lists; a fallback is printed as a fallback.
    """
    final = adjudication.final_verdict.value
    title = f"# Gap statement for `{adjudication.claim_id}`"
    if adjudication.role:
        title += f", artefact: {adjudication.role}"
    lines = [title, ""]
    lines.append("## 1. The verdict")
    lines.append("")
    lines.append(
        f"The five probes aggregate to **`{final}`**. "
        + (
            "That is the strongest verdict the panel supports: the kernel, the trace and "
            "the review agree, the two closure extractors agree, and no vacuity mutant "
            "survived."
            if adjudication.final_verdict is Verdict.VALIDATED_TERM
            else "Kernel acceptance is necessary but not sufficient here: each withheld "
                 "row in §3 names the computation that would decide it, and the panel "
                 "does not promote the rows that passed."
        )
    )
    lines.append("")
    lines.append("## 2. The closure")
    lines.append("")
    closures = [
        payload
        for payload in adjudication.probe(Probe.DEPENDENCY_TRACE).details.get(
            "closures", []
        )
        if payload.get("theorem")
    ]
    if not closures:
        lines.append(
            "No closure was computed, so there is nothing to report here: the trace "
            "probe is what produces one, and its row in §1 says why it did not run."
        )
    for payload in closures:
        reached = payload.get("reached", [])
        lines.append(
            f"- `{payload['theorem']}`: a closure of {payload.get('closure')} constants, "
            + (
                "reaching " + ", ".join(f"`{n}`" for n in reached)
                if reached else "reaching none of its declared suspects"
            )
            + f" (extractor: `#{payload.get('extractor', 'deps')}`)."
        )
    lines.append("")
    lines.append("## 2b. Closure discrepancy")
    lines.append("")
    cross = [
        payload["cross_validation"]
        for payload in closures
        if payload.get("cross_validation")
    ]
    if not cross:
        lines.append(
            "No cross-validation record exists: only one extractor's reading is on the "
            "table, and a single reading is not corroborated. The computation that would "
            "close this is `#depscmp` on the same theorem."
        )
    for entry in cross:
        theorem = entry.get("theorem", "?")
        if entry.get("discrepancy") is True:
            lines.append(
                f"- `{theorem}`: **disagreement**. `#deps` gives "
                f"{entry.get('counts', {}).get('deps')} names, `#depsm` gives "
                f"{entry.get('counts', {}).get('depsm')}. Only in `#deps`: "
                + (", ".join(f"`{n}`" for n in entry.get("only_in_deps", [])) or "none")
                + f" ({entry.get('only_in_first_count', 0)} total). Only in `#depsm`: "
                + (", ".join(f"`{n}`" for n in entry.get("only_in_depsm", [])) or "none")
                + f" ({entry.get('only_in_second_count', 0)} total). The difference is "
                "recorded, not resolved in favour of either extractor."
            )
        elif entry.get("agreement") is True:
            lines.append(
                f"- `{theorem}`: the two extractors agree on all "
                f"{entry.get('counts', {}).get('deps')} names, so the closure is one "
                "implementation's reading confirmed by an independent traversal. The "
                "shared environment remains a shared assumption, stated below."
            )
        else:
            lines.append(
                f"- `{theorem}`: **not corroborated**. "
                + str(entry.get("named_computation"))
                + "."
            )
    if cross:
        scope = cross[0].get("scope")
        if scope:
            lines.append("")
            lines.append(str(scope))
    lines.append("")
    lines.append("## 3. What would move it")
    lines.append("")
    if adjudication.named:
        for computation in adjudication.named:
            lines.append(f"- {computation}")
    else:
        lines.append("- Nothing: no probe is undetermined.")
    lines.append("")
    lines.append("## 4. What the graph shows")
    lines.append("")
    counts = adjudication.graph.counts()
    lines.append(
        f"{counts.get('red', 0)} red (flagged and reached), "
        f"{counts.get('amber', 0)} amber (flagged, not reached), "
        f"{counts.get('green', 0)} green, {counts.get('grey', 0)} grey entries."
    )
    if adjudication.graph.red:
        lines.append("")
        lines.append(
            "Reached suspects: "
            + ", ".join(f"`{name}`" for name in adjudication.graph.red)
            + ". Each is a definition whose content the theorem's proof does not need "
            "discharged honestly, and each is the object a refactor would have to remove."
        )
    lines.append("")
    lines.append("## 5. Two limits, stated with the verdict")
    lines.append("")
    lines.append("- " + AXIOM_TRAP_NOTE)
    lines.append("- " + STANDING_POSITION)
    lines.append("")
    return "\n".join(lines)


def render_html(adjudication: Adjudication) -> str:
    """A self-contained colour-coded graph: no network, no script, no external font."""
    graph = adjudication.graph
    radius = 250
    centre = (360, 340)
    placement: dict[str, tuple[float, float]] = {}
    ring = [n for n in graph.nodes if n.colour in ("red", "amber")]
    others = [n for n in graph.nodes if n.colour not in ("red", "amber")]
    for index, node in enumerate(ring):
        angle = 2 * 3.141592653589793 * index / max(len(ring), 1)
        placement[node.name] = (
            centre[0] + radius * math.cos(angle),
            centre[1] + radius * math.sin(angle),
        )
    for index, node in enumerate(others):
        angle = 2 * 3.141592653589793 * index / max(len(others), 1) + 0.4
        placement[node.name] = (
            centre[0] + 0.45 * radius * math.cos(angle),
            centre[1] + 0.45 * radius * math.sin(angle),
        )
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        "<title>Dependency graph: " + html.escape(adjudication.claim_id)
        + (": " + html.escape(adjudication.role) if adjudication.role else "")
        + "</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;margin:2rem;max-width:60rem}",
        "svg{background:#fafafa;border:1px solid #ddd}",
        "table{border-collapse:collapse;margin-top:1rem}",
        "td,th{border:1px solid #ccc;padding:.3rem .6rem;text-align:left;font-size:.9rem}",
        ".caveat{color:#555;font-size:.85rem;margin-top:1rem}",
        "</style></head><body>",
        f"<h1>Dependency graph: {html.escape(adjudication.claim_id)}</h1>",
        (
            f"<p><strong>Artefact:</strong> {html.escape(adjudication.role)}</p>"
            if adjudication.role else ""
        ),
        f"<p><strong>Aggregated verdict:</strong> "
        f"<code>{html.escape(adjudication.final_verdict.value)}</code></p>",
        f'<svg width="720" height="680" role="img" '
        f'aria-label="dependency graph of the adjudicated theorem">',
    ]
    for edge in graph.edges:
        start = placement.get(edge.source)
        end = placement.get(edge.target)
        if not start or not end:
            continue
        dash = "" if edge.relation == "reaches" else ' stroke-dasharray="4 4"'
        colour = COLOURS["red"] if edge.relation == "reaches" else COLOURS["amber"]
        parts.append(
            f'<line x1="{start[0]:.1f}" y1="{start[1]:.1f}" '
            f'x2="{end[0]:.1f}" y2="{end[1]:.1f}" '
            f'stroke="{colour}" stroke-width="1.6"{dash} opacity="0.75"/>'
        )
    for node in graph.nodes:
        x, y = placement[node.name]
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" '
            f'fill="{COLOURS[node.colour]}" stroke="#333" stroke-width="0.6"/>'
        )
        label = html.escape(node.name)
        parts.append(
            f'<text x="{x:.1f}" y="{y - 14:.1f}" font-size="11" '
            f'text-anchor="middle" fill="#222">{label}</text>'
        )
    parts.append("</svg>")
    parts.append('<p class="caveat">' + html.escape(graph.caveat) + "</p>")
    parts.append("<table><tr><th>colour</th><th>meaning</th><th>count</th></tr>")
    meanings = {
        "red": "flagged and reached: a load-bearing vacuous witness",
        "amber": "flagged but not reached: the objection does not bite",
        "green": "in the closure, no flag",
        "grey": "outside the closure, or a count of unenumerated members",
    }
    counts = graph.counts()
    for colour in ("red", "amber", "green", "grey"):
        parts.append(
            f'<tr><td><span style="display:inline-block;width:12px;height:12px;'
            f'background:{COLOURS[colour]}"></span> {colour}</td>'
            f"<td>{html.escape(meanings[colour])}</td><td>{counts.get(colour, 0)}</td></tr>"
        )
    parts.append("</table>")
    parts.append("<h2>Probes</h2><table><tr><th>probe</th><th>verdict</th>"
                 "<th>what would change it</th></tr>")
    for probe in adjudication.probes:
        parts.append(
            f"<tr><td>{html.escape(probe.probe.value)}</td>"
            f"<td>{html.escape(probe.verdict.value)}</td>"
            f"<td>{html.escape(probe.named_computation or 'decided')}</td></tr>"
        )
    parts.append("</table>")
    closures = [
        payload
        for payload in adjudication.probe(Probe.DEPENDENCY_TRACE).details.get(
            "closures", []
        )
        if payload.get("theorem")
    ]
    parts.append("<h2>Closure cross-validation</h2>")
    parts.append(
        "<p>The closure is computed twice, by Lean's own constant collector and by a "
        "structural recursion written out in the trace module. Two extractors, one "
        "environment: agreement rules out a defect in this repository's traversal, not a "
        "defect in Lean or in the definitions the closure passes through.</p>"
    )
    if not closures:
        parts.append('<p class="caveat">No closure was computed.</p>')
    for payload in closures:
        cross = payload.get("cross_validation") or {}
        theorem = html.escape(str(payload.get("theorem")))
        if cross.get("discrepancy") is True:
            parts.append(
                f"<p><strong>{theorem}</strong>: disagreement. "
                f"<code>#deps</code> {cross.get('counts', {}).get('deps')} names, "
                f"<code>#depsm</code> {cross.get('counts', {}).get('depsm')}; "
                + (", ".join(html.escape(n) for n in cross.get("only_in_deps", []))
                   or "no name only in `#deps`")
                + " / "
                + (", ".join(html.escape(n) for n in cross.get("only_in_depsm", []))
                   or "no name only in `#depsm`")
                + ".</p>"
            )
        elif cross.get("agreement") is True:
            parts.append(
                f"<p><strong>{theorem}</strong>: both extractors agree on all "
                f"{cross.get('counts', {}).get('deps')} names.</p>"
            )
        else:
            parts.append(
                f"<p><strong>{theorem}</strong>: not corroborated — "
                f"{html.escape(str(cross.get('named_computation') or 'no record'))}</p>"
            )
    parts.append('<p class="caveat">' + html.escape(AXIOM_TRAP_NOTE) + "</p>")
    parts.append('<p class="caveat">' + html.escape(STANDING_POSITION) + "</p>")
    parts.append("</body></html>")
    return "\n".join(parts) + "\n"


# ============================================================
# Records
# ============================================================

def load_mutants(path: Path, role: str | None = None) -> tuple[Mutant, ...]:
    """`mutants` entries from a claim record, optionally filtered to one formal target.

    The record is the same one the audit reads, so a mutation cannot be declared in a
    report that has no claim behind it.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    mutants: list[Mutant] = []
    for target in data.get("formal", ()):
        if role is not None and target.get("role") != role:
            continue
        for entry in target.get("mutants", ()):
            mutants.append(Mutant.from_record(entry))
    return tuple(mutants)


def write_deliverables(
    adjudication: Adjudication, out_dir: Path
) -> dict[str, Path]:
    """The four artefacts the specification asks for, written and returned."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "report.json": out_dir / "report.json",
        "report.tex": out_dir / "report.tex",
        "dependency_graph.html": out_dir / "dependency_graph.html",
        "gap_statement.md": out_dir / "gap_statement.md",
    }
    paths["report.json"].write_text(render_json(adjudication), encoding="utf-8")
    paths["report.tex"].write_text(render_tex(adjudication), encoding="utf-8")
    paths["dependency_graph.html"].write_text(render_html(adjudication), encoding="utf-8")
    paths["gap_statement.md"].write_text(
        render_gap_statement(adjudication), encoding="utf-8"
    )
    return paths
