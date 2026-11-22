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
"""The gap closer: execute the closure, classify the flagged declarations, refuse the overclaim.

The evaluation paper distinguishes three questions of increasing strength: whether the term
typechecks (the kernel answers it), whether a named definition is reachable from the term (a
transitive dependency trace answers it), and whether the vacuity objection bites (a mutation of
the definition answers it). The paper names the last two for the 2026 archive and does not
execute them, because the archive is 931 MB of git blobs and 61.5 GB of export and is not held
on the machine where the paper was built.

This module is the engine that executes them. It performs four computations:

* C1, the primary closure, by Lean's own ``Expr.getUsedConstants`` (``#deps``);
* C2, the second closure, by an extractor that must not share C1's traversal logic. The
  specification names ``laud graph``; that tool is not available here, so the second extractor
  is this repository's structural recursion (``#depsm``), and the substitution is recorded on
  every report rather than assumed away;
* C3, the comparison of the two closures, which is a verdict in its own right: a difference is
  left ``undetermined`` with a named reconciliation, never averaged;
* C4, the mutation of every flagged declaration that the closure reaches, which classifies the
  objection as biting or not biting.

Two semantics are fixed here and stated in every report, because the vocabulary of the
specification carries them ambiguously.

*Load-bearing* is used in the specification's sense: a flagged declaration is
``vacuity-critical`` when a vacuous rewrite of it leaves the target theorem compiling, i.e. the
proof does not need the definition's content. That is the set the aggregation treats as
blocking. A rewrite that breaks the theorem is ``vacuity-exonerated``: the proof does depend on
the definition's content, so the objection does not bite at that node.

*Identity mutation.* When a flagged definition is already the trivially vacuous form the rewrite
would install (``:= True``, ``fun _ _ _ => True``), the vacuous analogue is the definition and
C4 is the identity. The report records that case as ``identity_mutation`` and does not score it
as either a survival or a kill; a reader is told that the vacuity there is established by
reading the definition, not by mutation.

No verdict in this module means that the Riemann hypothesis is true, and the strongest positive
verdict it can emit is ``validated (term)``, which is a statement about a term.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .adjudicator import MutationOutcome, Mutant
from .claim_audit import Status, Verdict, dependency_trace, TraceRequest

#: The six-term vocabulary of the paper. `NOT_ASSESSED` is deliberately not in it.
VOCABULARY: tuple[Verdict, ...] = (
    Verdict.REJECTED,
    Verdict.OUTSIDE_DOMAIN,
    Verdict.UNDETERMINED,
    Verdict.VALIDATED_FINITE,
    Verdict.VALIDATED_ELEMENTARY,
    Verdict.VALIDATED_TERM,
)

STANDING = (
    "No verdict here means that the Riemann hypothesis is true. The strongest positive verdict "
    "is validated (term), which concerns a term and the definitions it invokes, not the "
    "mathematics those definitions are meant to carry."
)

#: Phrases that would turn a gap statement into a proof claim. The self-audit refuses them.
FORBIDDEN = (
    "riemann hypothesis is true",
    "riemann hypothesis is proved",
    "riemann hypothesis is proven",
    "proves the riemann hypothesis",
    "rh is true",
    "rh is proved",
    "settles rh",
)

#: Classification of one flagged declaration.
RED = "red"
AMBER = "amber"
GREEN = "green"
BLUE = "blue"
YELLOW = "yellow"


@dataclass(frozen=True)
class Computation:
    """One of C1--C4, with what it returned and how it was executed."""

    name: str
    instrument: str
    status: str
    detail: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    named_computation: str | None = None
    substitute: str | None = None

    @property
    def ran(self) -> bool:
        return self.status == "checked_ok"

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "instrument": self.instrument,
            "status": self.status,
            "detail": self.detail,
            "substitute": self.substitute,
            "named_computation": self.named_computation,
            "payload": _jsonable(self.payload),
        }


@dataclass(frozen=True)
class DeclarationRecord:
    """One flagged declaration, and what the closure and the mutation say about it."""

    name: str
    in_closure: bool
    flagged: bool
    vacuity_critical: bool | None
    mutant: str
    evidence: str

    @property
    def colour(self) -> str:
        if self.flagged and self.in_closure:
            return RED if self.vacuity_critical else AMBER
        if self.flagged and not self.in_closure:
            return BLUE
        return GREEN

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "in_closure": self.in_closure,
            "flagged": self.flagged,
            "vacuity_critical": self.vacuity_critical,
            "colour": self.colour,
            "mutant": self.mutant,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class GapReport:
    claim: str
    target: str
    module: str
    computations: tuple[Computation, ...]
    declarations: tuple[DeclarationRecord, ...]
    required: tuple[str, ...]
    verdict: Verdict
    named_computations: tuple[str, ...]
    checks: tuple[Check, ...] = ()
    kernel: Verdict = Verdict.UNDETERMINED
    dh_verdict: Verdict = Verdict.NOT_ASSESSED
    notes: tuple[str, ...] = ()

    def computation(self, name: str) -> Computation | None:
        return next((item for item in self.computations if item.name == name), None)

    @property
    def red(self) -> tuple[str, ...]:
        return tuple(sorted(item.name for item in self.declarations if item.colour == RED))

    @property
    def amber(self) -> tuple[str, ...]:
        return tuple(sorted(item.name for item in self.declarations if item.colour == AMBER))

    @property
    def blue(self) -> tuple[str, ...]:
        return tuple(sorted(item.name for item in self.declarations if item.colour == BLUE))

    @property
    def green(self) -> tuple[str, ...]:
        return tuple(sorted(item.name for item in self.declarations if item.colour == GREEN))

    @property
    def failed_checks(self) -> tuple[Check, ...]:
        return tuple(check for check in self.checks if not check.ok)

    def summary(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "target": self.target,
            "module": self.module,
            "verdict": self.verdict.value,
            "named_computations": list(self.named_computations),
            "kernel": self.kernel.value,
            "dh_screen": self.dh_verdict.value,
            "computations": [item.summary() for item in self.computations],
            "declarations": [item.summary() for item in self.declarations],
            "required": list(self.required),
            "colours": {
                "red": list(self.red),
                "amber": list(self.amber),
                "blue": list(self.blue),
                "green": list(self.green),
            },
            "self_audit": [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in self.checks],
            "notes": list(self.notes),
            "standing": STANDING,
        }


# ---------------------------------------------------------------- scans and matching
_FLAG_RE = re.compile(
    r"(?:^|\n)\s*(?:def|abbrev)\s+([A-Za-z_][\w.']*)[^\n]*?:=\s*(?:fun\b[^\n]*?=>\s*True|True)\s*$",
    re.MULTILINE,
)


def census_flags(source: str) -> tuple[str, ...]:
    """Declarations whose body is the trivially true shape, from the text alone.

    This is the heuristic scan the specification calls VACUITY_SCAN. It is a candidate list,
    not a classification: the plugin is absent, so what the engine can do with it is check
    reachability and mutation, and say which of the three meanings of "vacuous" it is using.
    """
    return tuple(sorted({m.group(1).split(".")[-1] for m in _FLAG_RE.finditer(source)}))


def answers_to(name: str, closure: Iterable[str]) -> str | None:
    """The closure member that is `name`, or ends with it as a dotted suffix."""
    for member in closure:
        if member == name or member.endswith("." + name):
            return member
    return None


def classify(
    closure: Iterable[str],
    flags: Iterable[str],
    outcomes: Sequence[MutationOutcome],
    *,
    identity_mutants: Iterable[str] = (),
    critical_by_inspection: Iterable[str] = (),
) -> tuple[DeclarationRecord, ...]:
    """The per-declaration table: reachability, mutation outcome, colour."""
    names = tuple(closure)
    identity = set(identity_mutants)
    inspected = set(critical_by_inspection)
    by_declaration: dict[str, list[MutationOutcome]] = {}
    for outcome in outcomes:
        declaration = getattr(outcome.mutant, "declaration", None) or outcome.mutant.theorem
        by_declaration.setdefault(str(declaration).split(".")[-1], []).append(outcome)

    records: list[DeclarationRecord] = []
    for flag in sorted(set(flags)):
        reached = answers_to(flag, names)
        outcome_list = by_declaration.get(flag, [])
        ran = [item for item in outcome_list if item.ran]
        critical: bool | None = None
        mutant = ""
        if flag in inspected:
            critical = True
            mutant = "inspection"
            evidence = (
                "the definition is literally the trivially true shape, so the theorem's content "
                "is carried by a vacuous definition; classified by inspection, not by mutation"
                + (
                    f" (the declared rewrite ran and was {'survived' if ran[0].survived else 'killed'}, "
                    "which calibrates the engine but is not a vacuous analogue)"
                    if ran
                    else ""
                )
            )
        elif flag in identity:
            mutant = "identity_mutation"
            evidence = (
                "the flagged definition is already the trivially vacuous form; the vacuous "
                "rewrite is the definition, so the mutation cannot discriminate and the vacuity "
                "is established by reading the definition"
            )
        elif ran:
            survived = [item for item in ran if item.survived]
            critical = bool(survived)
            mutant = survived[0].mutant.id if survived else ran[0].mutant.id
            evidence = (
                "vacuous rewrite survived: the proof does not need the definition's content"
                if critical
                else "vacuous rewrite killed: the proof needs the definition's content"
            )
        else:
            evidence = "; ".join(item.reason for item in outcome_list) or "no mutation was declared"
            mutant = outcome_list[0].mutant.id if outcome_list else ""

        records.append(
            DeclarationRecord(
                name=flag,
                in_closure=reached is not None,
                flagged=True,
                vacuity_critical=critical,
                mutant=mutant,
                evidence=evidence,
            )
        )
    return tuple(records)


# ---------------------------------------------------------------- aggregation
def aggregate(
    computations: Sequence[Computation],
    records: Sequence[DeclarationRecord],
    *,
    kernel: Verdict,
    dh_verdict: Verdict = Verdict.NOT_ASSESSED,
    discrepancy: bool = False,
) -> tuple[Verdict, tuple[str, ...]]:
    """The specification's precedence, with the refusal that makes it honest.

    The precedence table of the specification has two rows that cannot both hold: row 4 makes
    a clean kernel with no load-bearing vacuous nodes ``validated (term)``, and row 5 makes a
    clean kernel ``undetermined`` when the load-bearing set is empty. The reading implemented
    here is the one that follows from the refusal rule: a positive verdict needs every
    computation to have run, and it is withheld whenever the vacuity set is non-empty. No
    report can reach ``validated (term)`` while C1--C4 have not all executed.
    """
    if dh_verdict is Verdict.REJECTED:
        return Verdict.REJECTED, ()
    if kernel is Verdict.REJECTED:
        return Verdict.UNDETERMINED, ("discharge the sorry or the failed kernel check",)
    if discrepancy:
        return Verdict.UNDETERMINED, (
            "reconcile the closure mismatch between #deps and the second extractor",
        )
    required = ("C1", "C2", "C3", "C4")
    ran = {item.name for item in computations if item.ran}
    absent = [name for name in required if name not in ran]
    by_name = {item.name: item for item in computations}
    missing = tuple(
        f"run {name} ({by_name[name].named_computation if name in by_name and by_name[name].named_computation else 'no named computation recorded'})"
        for name in absent
    )

    # The vacuity witness is named first when one exists: it is the observation the report is
    # about, and it does not disappear once every computation has run.
    critical = tuple(item.name for item in records if item.vacuity_critical)
    if critical:
        witnesses = tuple(
            f"discharge the vacuity witness {name}: replace it with a definition whose content "
            f"the proof uses, or record it as load-bearing and reopen the objection"
            for name in critical
        )
        return Verdict.UNDETERMINED, witnesses + missing
    if missing:
        return Verdict.UNDETERMINED, missing
    if kernel is Verdict.VALIDATED_TERM:
        return Verdict.VALIDATED_TERM, ()
    return Verdict.UNDETERMINED, ("run the kernel check to completion",)


def self_audit(
    report: GapReport,
    *,
    gap_text: str,
    closure: Iterable[str],
    yellow: Iterable[str],
    trace_instrument: str,
) -> tuple[Check, ...]:
    """The specification's falsification conditions, checked against the report itself."""
    checks: list[Check] = []
    critical = [item for item in report.declarations if item.vacuity_critical]
    checks.append(
        Check(
            "no validated term over a vacuity witness",
            not (report.verdict is Verdict.VALIDATED_TERM and critical),
            f"{len(critical)} vacuity-critical declaration(s)",
        )
    )
    checks.append(
        Check(
            "four computations executed before a term verdict",
            not (report.verdict is Verdict.VALIDATED_TERM)
            or all(item.ran for item in report.computations),
            ", ".join(f"{item.name}={item.status}" for item in report.computations),
        )
    )
    discrepancy = report.computation("C3")
    silent = (
        discrepancy is not None
        and bool(discrepancy.payload.get("only_in_deps") or discrepancy.payload.get("only_in_laud"))
        and report.verdict is not Verdict.UNDETERMINED
    )
    checks.append(Check("closure discrepancy not silently resolved", not silent, "C3 compared"))
    checks.append(
        Check(
            "#print axioms is not used as the tracer",
            trace_instrument == "not run"
            or "getUsedConstants" in trace_instrument
            or "depsm" in trace_instrument,
            trace_instrument,
        )
    )
    closure_set = set(closure)
    red_ok = all(answers_to(item.name, closure_set) for item in report.declarations if item.colour == RED)
    yellow_ok = not any(answers_to(name, closure_set) for name in yellow)
    checks.append(Check("red nodes are in the closure", red_ok, f"{len(report.red)} red"))
    checks.append(Check("yellow nodes are outside the closure", yellow_ok, f"{len(tuple(yellow))} yellow"))
    hit = _asserts_proof(gap_text)
    checks.append(Check("gap statement asserts no proof", hit is None, hit or "none"))
    return tuple(checks)


# ---------------------------------------------------------------- renderers
def render_closure_txt(names: Sequence[str], *, header: str) -> str:
    lines = [f"# {header}", f"# {len(names)} names"]
    lines.extend(sorted(names))
    return "\n".join(lines) + "\n"


def render_crossvalidated(report: GapReport, first: Computation, second: Computation) -> str:
    payload = {
        "claim": report.claim,
        "target": report.target,
        "module": report.module,
        "c1": first.summary(),
        "c2": second.summary(),
        "status": report.computation("C3").status if report.computation("C3") else "not_run",
        "only_in_deps": _jsonable(first.payload.get("names", []) - second.payload.get("names", []))
        if first.ran and second.ran
        else None,
        "only_in_laud": _jsonable(second.payload.get("names", []) - first.payload.get("names", []))
        if first.ran and second.ran
        else None,
        "common": sorted(first.payload.get("names", set()) & second.payload.get("names", set()))
        if first.ran and second.ran
        else None,
        "verdict": report.verdict.value,
        "named_computations": list(report.named_computations),
        "standing": STANDING,
    }
    return json.dumps(payload, indent=2) + "\n"


def render_load_bearing(report: GapReport) -> str:
    return json.dumps(
        {
            "target": report.target,
            "verdict": report.verdict.value,
            "declarations": [item.summary() for item in report.declarations],
            "colours": {
                "red": list(report.red),
                "amber": list(report.amber),
                "blue": list(report.blue),
                "green": list(report.green),
            },
            "standing": STANDING,
        },
        indent=2,
    ) + "\n"


def render_graph(report: GapReport, *, required: Sequence[str] = ()) -> str:
    """A self-contained five-colour graph; no external assets."""
    colours = {
        RED: "#c62828",
        AMBER: "#ef9f27",
        GREEN: "#2e7d32",
        BLUE: "#1565c0",
        YELLOW: "#f9d64a",
    }
    nodes: list[tuple[str, str]] = [(item.name, item.colour) for item in report.declarations]
    nodes.extend((name, YELLOW) for name in required if name not in {n for n, _ in nodes})
    width = 720
    height = 120 + 46 * max(1, len(nodes))
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        f"<title>Dependency graph: {report.claim}</title>",
        "<style>body{font-family:system-ui,sans-serif;margin:2rem;color:#111}",
        ".legend span{display:inline-block;margin-right:1rem}",
        ".sw{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:.35rem}",
        "p.note{max-width:46rem}</style></head><body>",
        f"<h1>Dependency graph: {_escape(report.claim)}</h1>",
        f"<p class=\"note\">Target <code>{_escape(report.target)}</code>, verdict "
        f"<strong>{report.verdict.value}</strong>. Every edge is reachability from one closure "
        "computation, not a per-node edge set.</p>",
        "<p class=\"legend\">",
        *[
            f'<span data-colour="{key}"><i class="sw" style="background:{colours[key]}"></i>'
            f'<b>{key}</b>: {_escape(label)}</span>'
            for key, label in (
                (RED, "in closure, flagged, vacuity-critical"),
                (AMBER, "in closure, flagged, not critical"),
                (GREEN, "in closure, not flagged"),
                (BLUE, "flagged, not in closure"),
                (YELLOW, "required, not in closure"),
            )
        ],
        "</p>",
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'role="img" aria-label="dependency graph">',
    ]
    centre = width // 2
    parts.append(f'<circle cx="{centre}" cy="60" r="16" fill="#455a64"/>')
    parts.append(
        f'<text x="{centre + 26}" y="65" font-size="14">{_escape(report.target)}</text>'
    )
    y = 120
    for name, colour in nodes:
        parts.append(f'<line x1="{centre}" y1="76" x2="{centre}" y2="{y - 12}" stroke="#bbb"/>')
        parts.append(f'<circle cx="{centre}" cy="{y}" r="10" fill="{colours.get(colour, "#999")}"/>')
        label = f"{name} [{colour}]"
        parts.append(f'<text x="{centre + 18}" y="{y + 5}" font-size="13">{_escape(label)}</text>')
        y += 46
    parts.append("</svg>")
    if report.failed_checks:
        parts.append("<h2>Self-audit failures</h2><ul>")
        parts.extend(
            f"<li>{_escape(check.name)}: {_escape(check.detail)}</li>"
            for check in report.failed_checks
        )
        parts.append("</ul>")
    parts.append(f"<p class=\"note\">{_escape(STANDING)}</p>")
    parts.append("</body></html>")
    return "\n".join(parts) + "\n"


def render_gap_statement(report: GapReport) -> str:
    lines = [
        f"# Gap statement: {report.claim}",
        "",
        STANDING,
        "",
        f"**Target.** `{report.target}` in "
        + (f"`{report.module}`" if report.module else "the archive, whose module is not yet identified")
        + ".",
        f"**Verdict.** `{report.verdict.value}`.",
        "",
        "## 1. Computations",
        "",
    ]
    for item in report.computations:
        substitute = f" Substitution: {item.substitute}." if item.substitute else ""
        lines.append(f"- **{item.name}**, `{item.instrument}`: `{item.status}`. {item.detail}.{substitute}")
    lines += ["", "## 2. Closure", ""]
    c1 = report.computation("C1")
    c2 = report.computation("C2")
    if c1 and c1.ran:
        lines.append(f"- C1 names: {len(c1.payload.get('names', []))}")
    else:
        lines.append("- C1 names: not computed")
    if c2 and c2.ran:
        lines.append(f"- C2 names: {len(c2.payload.get('names', []))}")
    else:
        lines.append("- C2 names: not computed")
    lines += ["", "## 3. Flagged declarations", ""]
    if report.declarations:
        for item in report.declarations:
            critical = (
                "critical" if item.vacuity_critical else
                "not critical" if item.vacuity_critical is False else "not scored"
            )
            lines.append(
                f"- `{item.name}`: in closure {item.in_closure}, {critical}. {item.evidence}"
            )
    else:
        lines.append("- none")
    lines += ["", "## 4. What would move the verdict", ""]
    if report.verdict is Verdict.VALIDATED_TERM:
        lines.append("- nothing: the term verdict is the strongest this protocol issues, and it is not a claim about the mathematics")
    elif report.named_computations:
        for item in report.named_computations:
            lines.append(f"- {item}")
    else:
        lines.append("- no named computation recorded, which is a protocol violation")
    lines += ["", "## 5. What this does not say", "",
              "- It does not say the Riemann hypothesis is true, proved or refuted.",
              "- It does not say the archive's definitions carry the mathematics their names suggest.",
              "- It does not adjudicate the authors.", ""]
    return "\n".join(lines)


_ASSERT_RE = re.compile(
    r"\b(is|are|was|were|has been|have been|remains)\s+(true|proved|proven|settled)\b"
)
_NEGATION_RE = re.compile(r"\b(not|no|never|none|cannot|can't|does not|doesn't|refuses|withheld)\b")


def _asserts_proof(text: str) -> str | None:
    """The first sentence that asserts a proof, ignoring negated and attributed uses.

    A gap statement has to be able to say "this does not say the hypothesis is true"; a
    substring scan would flag its own disclaimer. The check is sentence-level and skips a
    sentence that contains a negation or withholds the claim.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        low = sentence.lower()
        if "riemann hypothesis" not in low and not re.search(r"\brh\b", low):
            continue
        if _ASSERT_RE.search(low) and not _NEGATION_RE.search(low):
            return sentence.strip()
    return None


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(str(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


# ---------------------------------------------------------------- assembly and writing
def build_report(
    *,
    claim: str,
    target: str,
    module: str,
    computations: Sequence[Computation],
    outcomes: Sequence[MutationOutcome] = (),
    flags: Sequence[str] = (),
    closure: Iterable[str] = (),
    identity_mutants: Sequence[str] = (),
    critical_by_inspection: Sequence[str] = (),
    required: Sequence[str] = (),
    kernel: Verdict = Verdict.UNDETERMINED,
    dh_verdict: Verdict = Verdict.NOT_ASSESSED,
    notes: Sequence[str] = (),
) -> GapReport:
    closure_set = set(closure)
    records = classify(
        closure_set,
        flags,
        outcomes,
        identity_mutants=identity_mutants,
        critical_by_inspection=critical_by_inspection,
    )
    c3 = next((item for item in computations if item.name == "C3"), None)
    discrepancy = bool(
        c3 and c3.payload.get("only_in_deps") is not None
        and (c3.payload.get("only_in_deps") or c3.payload.get("only_in_laud"))
    )
    verdict, named = aggregate(
        computations, records, kernel=kernel, dh_verdict=dh_verdict, discrepancy=discrepancy
    )
    draft = GapReport(
        claim=claim,
        target=target,
        module=module,
        computations=tuple(computations),
        declarations=records,
        required=tuple(required),
        verdict=verdict,
        named_computations=named,
        kernel=kernel,
        dh_verdict=dh_verdict,
        notes=tuple(notes),
    )
    trace_instrument = "getUsedConstants" if any(
        item.name == "C1" and item.ran for item in computations
    ) else "not run"
    text = render_gap_statement(draft)
    checks = self_audit(
        draft, gap_text=text, closure=closure_set, yellow=required, trace_instrument=trace_instrument
    )
    if any(not check.ok for check in checks):
        verdict = Verdict.UNDETERMINED
        named = named + ("self-audit failed: " + "; ".join(c.name for c in checks if not c.ok),)
        draft = GapReport(
            claim=draft.claim,
            target=draft.target,
            module=draft.module,
            computations=draft.computations,
            declarations=draft.declarations,
            required=draft.required,
            verdict=verdict,
            named_computations=named,
            checks=checks,
            kernel=kernel,
            dh_verdict=dh_verdict,
            notes=draft.notes,
        )
    else:
        draft = GapReport(
            claim=draft.claim,
            target=draft.target,
            module=draft.module,
            computations=draft.computations,
            declarations=draft.declarations,
            required=draft.required,
            verdict=verdict,
            named_computations=named,
            checks=checks,
            kernel=kernel,
            dh_verdict=dh_verdict,
            notes=draft.notes,
        )
    return draft


def write_artefacts(report: GapReport, out_dir: Path, *, first: Computation, second: Computation) -> dict[str, str]:
    """Six artefacts, each hashed, plus a manifest; returns `{filename: sha256}`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "closure_deps.txt": render_closure_txt(
            sorted(first.payload.get("names", ())) if first.ran else (),
            header=f"C1 closure for {report.target} ({first.instrument}, {first.status})",
        ),
        "closure_laud.txt": render_closure_txt(
            sorted(second.payload.get("names", ())) if second.ran else (),
            header=f"C2 closure for {report.target} ({second.instrument}, {second.status})",
        ),
        "closure_crossvalidated.json": render_crossvalidated(report, first, second),
        "load_bearing.json": render_load_bearing(report),
        "dependency_graph.html": render_graph(report, required=report.required),
        "gap_statement.md": render_gap_statement(report),
    }
    hashes: dict[str, str] = {}
    for name, content in files.items():
        path = out_dir / name
        path.write_text(content, encoding="utf-8")
        hashes[name] = sha256(content.encode("utf-8")).hexdigest()
    manifest = {
        "claim": report.claim,
        "verdict": report.verdict.value,
        "files": hashes,
        "standing": STANDING,
        "self_audit": [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in report.checks],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return hashes
