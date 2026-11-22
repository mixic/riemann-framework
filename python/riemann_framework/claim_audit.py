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
"""An audit agent for a claimed proof of the Riemann hypothesis.

The input is a *claim*: a document with a hash, a statement extracted from it with a
location, optionally a formalisation, the declared inputs it rests on, and the
objections on record. The output is a report with three levels and no verdict on the
hypothesis itself.

Why three levels, and why none of them adjudicates
--------------------------------------------------
[`docs/claimed_proof_triage.md`](../../docs/claimed_proof_triage.md) §5 fixes the
standing position: RH is open, and no instrument in this repository can move it. What
the repository can do is say, per claim and per instrument, **what was checked and by
what**. The levels differ in trust base and in how they fail:

``numerical``
    Falsification tests run by this repository's own modules. A numerical instrument
    can refute a quantitative claim; it cannot confirm one. A claim that asserts the
    *existence of a proof* is outside the input domain of every instrument in the
    inventory, so the usual level-1 result for a proof claim is ``outside domain``
    (Definition 3 of the paper): a fact about the instruments, not about the claim.

``formal``
    Five questions asked of the artefact by compiling it. Four are decided by Lean's
    kernel and by the toolchain: does it compile, is it free of ``sorry``, are its
    axioms among the standard three, and is the theorem's statement Mathlib's
    ``RiemannHypothesis``. The fifth, whether the definitions the proof routes through
    are non-vacuous, is **not** decided here and is never reported as decided: what
    the agent can do is locate the definitional escape hatches that an objection names
    and report that it located them. Locating is not proving dependence, and the
    difference is the whole of the Alpöge–Nielsen dispute.

``institutional``
    Peer review, community certification, independent replay, stated objections, Clay
    status. These are *recorded* with a source and a date, never *checked*: this
    module cannot read a journal's decision letter, and an institution's statement is
    not a theorem. The document hash at level 0 is the one thing on this level that is
    mechanically verified.

The status vocabulary is deliberately not boolean. ``checked_ok`` and
``checked_failed`` are mechanical facts about a check that ran; ``recorded`` means a
named source says so and this module did not verify it; ``undetermined`` means the
question is real and nothing here decides it; ``not_run`` means the artefact is absent
from this machine; ``not_applicable`` means the claim supplies no input for the check.
A ``Finding`` also carries a verdict from the paper's six-word vocabulary where one
follows from the check, and ``not assessed`` otherwise. No word in either vocabulary
means *true*.

What the agent cannot establish, stated here rather than discovered by a reader
-------------------------------------------------------------------------------
* **Statement identity is compared, not proved equivalent.** The type text Lean prints
  is compared to an expected text after normalisation. When the target is a
  ``Prop``-valued definition the agent can do better and ask the kernel directly
  (``example : target = RiemannHypothesis := rfl``); that check is exact, and the text
  comparison exists for theorems, where no such term can be written because a proof is
  not a proposition.
* **A certified statement is not a faithful one.** A kernel can accept a term whose
  internal definitions carry no mathematics. That is Nielsen's objection, it is
  recorded in [`docs/alpoge_nielsen_dispute.md`](../../docs/alpoge_nielsen_dispute.md),
  and no function here resolves it.
* **An absent artefact is not a passed check.** When the formalisation is not on this
  machine the level-2 findings are replayed from the audit record and labelled with
  the date of that record and the command that produced it.
* **A quote is not an assertion.** The report may quote a claimant or an institution
  saying whatever they said. Every sentence the agent writes itself is checked against
  a list of proof claims before the report is returned; quoted material is rendered as
  a block quote and exempt, because a report that cannot quote its subject cannot be
  honest about it.

Nothing here proves or disproves the Riemann hypothesis. Nothing here evaluates a
claimant as a mathematician. The reports are status records with named trust bases.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

#: Axioms Lean and Mathlib are entitled to use without an argument. Anything else in a
#: `#print axioms` list is a dependency the artefact chose, and `sorryAx` is a hole.
STANDARD_AXIOMS: frozenset[str] = frozenset(
    {"propext", "Classical.choice", "Quot.sound"}
)

#: The sentence every report carries. Tests assert it is present in every render, so a
#: report that quietly started adjudicating would fail rather than mislead.
STANDING_POSITION = (
    "RH is open. This report records what could be checked, by which instrument, and "
    "what could not be checked at all. It is not a verdict on the claim, it is not "
    "evidence for or against the Riemann hypothesis, and no entry in it means that "
    "the hypothesis is true or false."
)

#: Phrases the agent may not assert in its own voice. Kept lower-case and matched
#: against lower-cased, space-stripped text. Quoted material is exempt by construction:
#: `render_markdown` only scans the sentences it generates.
FORBIDDEN_ASSERTIONS: tuple[str, ...] = (
    "provestheriemannhypothesis",
    "provesthattheriemannhypothesis",
    "disprovestheriemannhypothesis",
    "riemannhypothesisisproved",
    "riemannhypothesisisfalse",
    "settlesrh",
    "confirmstheriemannhypothesis",
)


class Level(str, Enum):
    """Which of the three levels a finding belongs to."""

    NUMERICAL = "numerical"
    FORMAL = "formal"
    INSTITUTIONAL = "institutional"


class Status(str, Enum):
    """What happened to one check.

    ``checked_ok`` / ``checked_failed`` are mechanical: the check ran and the condition
    held or did not. ``recorded`` is a citation, not a check. ``undetermined`` is a
    real question nothing here decides. ``not_run`` is an absent artefact.
    ``not_applicable`` is a claim that supplies no input.
    """

    CHECKED_OK = "checked_ok"
    CHECKED_FAILED = "checked_failed"
    RECORDED = "recorded"
    UNDETERMINED = "undetermined"
    NOT_RUN = "not_run"
    NOT_APPLICABLE = "not_applicable"


class Verdict(str, Enum):
    """The paper's six-verdict vocabulary, plus the absence of a verdict.

    The strings are the paper's, character for character, and
    `tests/test_claim_audit.py` compares them against `paper/evaluation_protocol.tex` so
    the two cannot drift into different vocabularies. None of them means "true".
    """

    REJECTED = "rejected"
    OUTSIDE_DOMAIN = "outside domain"
    UNDETERMINED = "undetermined"
    VALIDATED_FINITE = "validated (finite)"
    VALIDATED_ELEMENTARY = "validated (elementary)"
    VALIDATED_TERM = "validated (term)"
    NOT_ASSESSED = "not assessed"


class Instrument(str, Enum):
    """Which of the panel's instruments produced a finding.

    Distinct from `Verdict`: the verdict is what was concluded, the instrument is what
    concluded it. The aggregation rule in `ClaimReport.overall` reads this field, because
    the paper's central claim about the panel is that *a kernel pass is not a term verdict*
    until a dependency trace has run. Two findings can share a status and differ in
    instrument, and that difference decides the panel's answer.
    """

    KERNEL = "kernel"
    DEPENDENCY_TRACE = "dependency trace"
    VACUITY_SCAN = "vacuity scan"
    CIRCULARITY = "circularity screen"
    DH_SCREEN = "Davenport-Heilbronn screen"
    NUMERICAL = "numerical instrument"
    READING = "reading"
    NONE = "none"


class LeanQuestion(str, Enum):
    """The five questions asked of a formal artefact.

    The first four are decided by the kernel or the toolchain. The fifth is not decided
    by anything here, and reporting it as decided would be the error this agent exists
    to avoid; see `_non_vacuity_finding`.
    """

    COMPILES = "does it compile"
    NO_SORRY = "is it free of sorry"
    AXIOMS_JUSTIFIED = "are the axioms the standard three"
    STATEMENT_MATCHES = "is the theorem the Riemann hypothesis"
    DEFINITIONS_NON_VACUOUS = "are the definitions non-vacuous"


LEAN_QUESTIONS: tuple[LeanQuestion, ...] = (
    LeanQuestion.COMPILES,
    LeanQuestion.NO_SORRY,
    LeanQuestion.AXIOMS_JUSTIFIED,
    LeanQuestion.STATEMENT_MATCHES,
    LeanQuestion.DEFINITIONS_NON_VACUOUS,
)


# ============================================================
# Records
# ============================================================

def _cell(text: str) -> str:
    """Make `text` safe inside a Markdown table cell.

    Evidence lines carry Lean output, which contains pipes (`|...|`), backslashes and
    newlines. Unescaped, one of them ends the row and the table silently loses a column;
    that is a rendering bug a reader would blame on the claim.
    """
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


@dataclass(frozen=True)
class Finding:
    """One check, what it established, and what it does not establish.

    Every field is rendered; none is optional. `limits` is not decoration: a finding
    without a stated limit is the failure mode the paper is written against, so it is
    required and the tests check it is non-empty.

    `instrument_class` is defaulted so that a finding built before the panel had
    instruments still constructs; every finding the agent produces sets it, and the
    aggregation rule in `ClaimReport.overall` reads it rather than parsing the
    human-readable `instrument` string.
    """

    level: Level
    check: str
    status: Status
    verdict: Verdict
    instrument: str
    evidence: str
    limits: str
    instrument_class: Instrument = Instrument.READING
    #: Machine-readable payload for the probes that produce one (the trace records its
    #: closure size, the suspects it reached and the flag set it was given). Kept out of
    #: vidence so a renderer never has to parse prose to colour a graph node.
    details: Mapping[str, Any] = field(default_factory=dict)

    def as_row(self) -> str:
        """One table row, with the pipe characters the evidence may contain escaped."""
        return (
            f"| {_cell(self.check)} | `{self.status.value}` | {self.verdict.value} "
            f"| {_cell(self.evidence)} |"
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "level": self.level.value,
            "check": self.check,
            "status": self.status.value,
            "verdict": self.verdict.value,
            "instrument": self.instrument,
            "instrument_class": self.instrument_class.value,
            "details": dict(self.details),
            "evidence": self.evidence,
            "limits": self.limits,
        }


@dataclass(frozen=True)
class Objection:
    """A position on record that disputes the claim, and what would decide it."""

    source: str
    summary: str
    status: Status
    decisive_question: str

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "summary": self.summary,
            "status": self.status.value,
            "decisive_question": self.decisive_question,
        }


@dataclass(frozen=True)
class InstitutionalFact:
    """A dated statement by an institution, and where it is written down."""

    kind: str
    value: str
    source: str
    date: str
    note: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "value": self.value,
            "source": self.source,
            "date": self.date,
            "note": self.note,
        }


@dataclass(frozen=True)
class Document:
    """The primary document, archived byte for byte, with its hash and page count."""

    path: str
    sha256: str
    bytes: int
    pages: int
    url: str
    retrieved: str

    def resolve(self, repo_root: Path) -> Path:
        candidate = Path(self.path)
        return candidate if candidate.is_absolute() else repo_root / candidate

    def verify(self, repo_root: Path) -> tuple[bool, str]:
        """Re-hash the file and compare.

        Returns `(matches, evidence)`. A missing file is a `False` with that reason in
        the evidence, because "verified: 0 bytes" is exactly the silent success this
        repository keeps finding in its own history.
        """
        path = self.resolve(repo_root)
        if not path.is_file():
            return False, f"file absent: {self.path}"
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != self.bytes:
            return False, f"{self.path}: {len(data)} bytes, recorded {self.bytes}"
        if digest != self.sha256:
            return False, f"{self.path} hashes to {digest[:16]}, recorded {self.sha256[:16]}"
        return True, f"{self.path}: {self.bytes} bytes, sha256 {digest[:16]}, {self.pages} pp."


@dataclass(frozen=True)
class StatementTarget:
    """A name whose statement is compared against `expected`.

    `mode` is `"check"` for a theorem (Lean prints its type) or `"print"` for a
    `Prop`-valued definition (Lean prints its body; the type is just `Prop`).
    ``defeq`` asks the kernel directly when the target is a proposition, which is exact
    and strictly stronger than the text comparison.
    """

    name: str
    expected: str = "RiemannHypothesis"
    mode: str = "check"
    defeq: bool = False


@dataclass(frozen=True)
class TraceRequest:
    """A theorem to trace, and the names the objection says it reaches.

    `suspects` is what makes the trace decisive rather than encyclopaedic: the closure of
    a Matlib-backed theorem runs to thousands of names, and the interesting question is
    only whether *these* are among them. A name matching by suffix is accepted (`anyGeometry`
    matches `Development...anyGeometry`) because objection documents quote short names.
    """

    theorem: str
    suspects: tuple[str, ...]


@dataclass(frozen=True)
class FormalTarget:
    """A formal artefact, where it lives, and what was already established about it.

    `root` is relative to the repository root, or absolute. When it is absent from this
    machine the level-2 findings are replayed from `recorded`, which is why the record
    carries a date and the commands that produced it.
    """

    role: str
    root: str
    module: str
    statements: tuple[StatementTarget, ...]
    axiom_targets: tuple[str, ...]
    recorded: Mapping[str, Any]
    recorded_on: str
    commands: tuple[str, ...]
    note: str = ""
    imports: tuple[str, ...] = ()
    trace: tuple[TraceRequest, ...] = ()

    def root_path(self, repo_root: Path) -> Path:
        candidate = Path(self.root)
        return candidate if candidate.is_absolute() else repo_root / candidate

    def present(self, repo_root: Path) -> bool:
        return self.root_path(repo_root).is_dir()


@dataclass(frozen=True)
class Claim:
    """A claimed proof, as the agent needs it.

    Everything here is supplied by a reviewer and is data, not code: the agent does not
    fetch, read, or interpret the document, it re-hashes it and quotes from the record.
    """

    id: str
    title: str
    claimant: str
    date: str
    statement: str
    statement_location: str
    declared_inputs: tuple[str, ...]
    probes: tuple[str, ...]
    document: Document | None = None
    formal: tuple[FormalTarget, ...] = ()
    institutional: tuple[InstitutionalFact, ...] = ()
    objections: tuple[Objection, ...] = ()
    notes: str = ""

    @classmethod
    def from_json(cls, path: Path) -> "Claim":
        """Load a claim record, naming every missing or malformed key.

        A record that silently defaults a field would produce a report with an
        unstated premise in it, so the loader is strict: unknown top-level keys are
        reported too, because a typo in a key is otherwise an ignored field.
        """
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, source=str(path))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], source: str = "<dict>") -> "Claim":
        required = ("id", "title", "claimant", "date", "statement",
                    "statement_location", "declared_inputs", "probes")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"{source}: missing required keys {missing}")
        known = set(required) | {"document", "formal", "institutional", "objections",
                                 "notes"}
        unknown = sorted(set(data) - known)
        if unknown:
            raise ValueError(f"{source}: unknown keys {unknown}")
        document = Document(**data["document"]) if data.get("document") else None
        formal = tuple(
            FormalTarget(
                role=entry["role"],
                root=entry["root"],
                module=entry["module"],
                statements=tuple(StatementTarget(**item)
                                 for item in entry.get("statements", ())),
                axiom_targets=tuple(entry.get("axiom_targets", ())),
                recorded=dict(entry.get("recorded", {})),
                recorded_on=entry.get("recorded_on", ""),
                commands=tuple(entry.get("commands", ())),
                note=entry.get("note", ""),
                imports=tuple(entry.get("imports", ())),
                trace=tuple(
                    TraceRequest(
                        theorem=request["theorem"],
                        suspects=tuple(request.get("suspects", ())),
                    )
                    for request in entry.get("trace", ())
                ),
            )
            for entry in data.get("formal", ())
        )
        return cls(
            id=data["id"],
            title=data["title"],
            claimant=data["claimant"],
            date=data["date"],
            statement=data["statement"],
            statement_location=data["statement_location"],
            declared_inputs=tuple(data["declared_inputs"]),
            probes=tuple(data["probes"]),
            document=document,
            formal=formal,
            institutional=tuple(InstitutionalFact(**item)
                                for item in data.get("institutional", ())),
            objections=tuple(Objection(status=Status(item["status"]), **{
                key: value for key, value in item.items() if key != "status"
            }) for item in data.get("objections", ())),
            notes=data.get("notes", ""),
        )


# ============================================================
# Lean machinery
# ============================================================

#: Lean's `sorry` warning differs in quoting across versions, so both are accepted.
_SORRY_WARNING = re.compile(r"declaration uses [`']sorry[`']")
_MARKER = re.compile(r"^===(.+?)===$", re.MULTILINE)
_AXIOMS_NONE = re.compile(r"^'([^']+)' does not depend on any axioms$", re.MULTILINE)
_AXIOMS_SOME = re.compile(
    r"^'([^']+)' depends on axioms: \[(.*?)\]$", re.MULTILINE
)


def lean_environment() -> dict[str, str]:
    """`os.environ` with elan's bin directory on `PATH`.

    `lake` is installed through elan, which puts its shims in `~/.elan/bin` and is not
    on `PATH` in every shell this repository is run from. Adding it here rather than
    asking the caller to export it is what makes the agent reproducible.
    """
    env = dict(os.environ)
    elan = Path.home() / ".elan" / "bin"
    if elan.is_dir():
        entries = env.get("PATH", "").split(os.pathsep)
        if str(elan) not in entries:
            env["PATH"] = os.pathsep.join([str(elan), *entries])
    return env


def strip_lean_comments(source: str) -> str:
    """Remove `--` line comments and (nested) `/- -/` block comments.

    Necessary before counting `sorry`: `lean/RiemannFramework/Dispute.lean` discusses
    the word in its docstrings, and a census that counted prose would report a hole
    where there is none. The reverse error is the one that matters, so the function
    errs towards keeping ambiguous text and is tested on both shapes.
    """
    out: list[str] = []
    index = 0
    depth = 0
    while index < len(source):
        pair = source[index:index + 2]
        if depth == 0 and pair == "--":
            newline = source.find("\n", index)
            index = len(source) if newline < 0 else newline
            continue
        if pair == "/-":
            depth += 1
            index += 2
            continue
        if pair == "-/" and depth:
            depth -= 1
            index += 2
            continue
        if depth == 0:
            out.append(source[index])
        index += 1
    return "".join(out)


_DECLARATION = re.compile(
    r"(?m)^\s*(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(?:theorem|lemma|def|abbrev|example|instance)\s+([A-Za-z_][\w'.]*)"
)


def sorry_census(source: str) -> dict[str, Any]:
    """Count `sorry` and `admit` tokens outside comments, and name their declarations.

    Reads the *source*; Lean's own warning is the authoritative signal and is parsed
    separately from the compile output. Two independent signals that disagree are more
    informative than either alone, so both are reported.

    The declaration names are the part that makes the count usable: "2 holes" is a
    number, and "2 holes in `alpoge_position` and `nielsen_position`" is a fact about
    which claims are unfinished. When a hole is not inside a named declaration, the line
    number is reported instead, because a wrong name would be worse than a line number.
    """
    code = strip_lean_comments(source)
    lines = code.splitlines()
    named: list[str] = []
    counts = {"sorry": 0, "admit": 0}
    for number, line in enumerate(lines, start=1):
        for token in counts:
            if re.search(rf"\b{token}\b", line):
                counts[token] += 1
                named.append(_enclosing_declaration(lines, number) or f"line {number}")
    return {**counts, "declarations": named}


def _enclosing_declaration(lines: Sequence[str], number: int) -> str | None:
    """The name of the nearest declaration above (or on) line `number`, 1-based."""
    for index in range(min(number, len(lines)) - 1, -1, -1):
        match = _DECLARATION.match(lines[index])
        if match:
            return match.group(1)
    return None


def vacuity_census(source: str) -> dict[str, Any]:
    """Locate the definitional shapes an objection of the Alpöge–Nielsen kind names.

    Three patterns are counted, all of them textual:

    * a definition whose body is literally `True`, or a lambda returning `True`
      (`fun _ _ _ => True`), which is the `anyGeometry` shape;
    * a definition of a proposition as an alias, which is where a statement can be
      renamed without being restated;
    * a structure field whose value is fixed by `rfl`, which is the height-equation
      shape: an equation that holds because the quantity was defined to be its own
      formula.

    **This is a locator, not a proof of dependence.** It does not know whether the
    archive's conclusion passes through any of these, and no arithmetic here can. That
    question is Nielsen's, and [`docs/alpoge_nielsen_dispute.md`] records it as open.
    """
    code = strip_lean_comments(source)
    true_bodied = re.findall(
        r"(?m)^\s*(?:def|abbrev|private def|noncomputable def)\s+(\w+)\b[^\n]*"
        r":\s*Prop\s*:=\s*(?:fun\b[^\n]*=>\s*)?True\b",
        code,
    )
    fun_true = re.findall(r"fun\s+(?:_\s+)*_\s*=>\s*True\b", code)
    alias = re.findall(
        r"(?m)^\s*(?:def|abbrev)\s+(\w+)[^\n]*:\s*Prop\s*:=\s*([A-Za-z_][\w.]*)\s*$", code
    )
    rfl_fields = re.findall(r":=\s*by\s+rfl\b|:=\s*rfl\b", code)
    return {
        "true_bodied_definitions": sorted(set(true_bodied)),
        "true_lambdas": len(fun_true),
        "proposition_aliases": [f"{name} := {target}" for name, target in alias],
        "rfl_defined_values": len(rfl_fields),
    }


def split_sections(output: str) -> dict[str, str]:
    """Split Lean's stdout on the `===key===` markers the probe source emits."""
    marks = list(_MARKER.finditer(output))
    sections: dict[str, str] = {}
    for position, match in enumerate(marks):
        end = marks[position + 1].start() if position + 1 < len(marks) else len(output)
        sections[match.group(1)] = output[match.end():end].strip()
    return sections


def _checked_type(section: str) -> tuple[str, str]:
    """`('#check' section) -> (binder prefix or name, type text)`."""
    lines = [line for line in section.splitlines() if line.strip()]
    if not lines:
        return "", ""
    head = lines[0]
    if " : " not in head:
        return "", head
    name, rest = head.split(" : ", 1)
    continuation = [line.strip() for line in lines[1:]]
    return name, " ".join([rest, *continuation]).strip()


_GLYPHS = {
    "∀": "forall ",
    "→": "->",
    "↔": "<->",
    "¬": "not ",
    "∧": "and ",
    "∨": "or ",
    "ℂ": "Complex",
    "ℕ": "Nat",
    "ℤ": "Int",
    "ℝ": "Real",
    "ℚ": "Rat",
    "·": "*",
}


def normalise_statement(text: str) -> str:
    """Fold layout and common notation so two printings can be compared.

    The comparison can only become *more* permissive under normalisation, never less,
    and it is a text comparison in any case: two distinct statements that differ only by
    layout would compare equal, while a statement that differs mathematically will not.
    Where the target is a proposition the agent does not rely on this and asks the
    kernel instead (`StatementTarget.defeq`).
    """
    for glyph, replacement in _GLYPHS.items():
        text = text.replace(glyph, replacement)
    text = re.sub(r"\s+", " ", text).strip().rstrip(";")
    return text.replace(" ", "")


def parse_axioms(output: str) -> dict[str, list[str] | None]:
    """Parse `#print axioms` results out of a probe's output.

    Returns `{name: [axioms]}` where an empty list means Lean said "does not depend on
    any axioms"; a name Lean could not find is simply absent from the mapping, which is
    why the caller treats absence as a problem rather than as a clean result.
    """
    found: dict[str, list[str] | None] = {}
    for name, body in _AXIOMS_SOME.findall(output):
        found[name] = [item.strip() for item in body.split(",") if item.strip()]
    for name in _AXIOMS_NONE.findall(output):
        found[name] = []
    return found


def axioms_justified(axioms: Sequence[str]) -> tuple[bool, str]:
    """Are these the axioms an artefact is allowed to use?

    `sorryAx` is singled out in the message because it is the failure mode that
    typechecks: a file with a `sorry` compiles, and its axiom list is the only place
    the hole is visible at this level.
    """
    extra = sorted(set(axioms) - STANDARD_AXIOMS)
    if not extra:
        return True, "nothing beyond the standard three"
    if "sorryAx" in extra:
        return False, "sorryAx is present, so the term is completed by a hole"
    return False, "non-standard axioms: " + ", ".join(extra)


@dataclass
class LeanRun:
    """The result of one `lake env lean` invocation, plus what was asked of it."""

    returncode: int
    output: str
    source: str
    path: Path
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def run_lean(
    project_root: Path,
    source: str,
    *,
    name: str = "probe",
    timeout: int = 1800,
    scratch_dir: Path | None = None,
) -> LeanRun:
    """Write `source` to a scratch file under `out/claims/_scratch` and compile it.

    The scratch directory is inside the project so that `lake env lean` resolves the
    project's own modules and its `.olean` files; it is git-ignored, and the file is
    left on disk after the run because a failing probe is only diagnosable from its
    source. `lake` is not launched through a shell, so no quoting rules apply.
    """
    scratch = scratch_dir or (project_root / "out" / "claims" / "_scratch")
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / f"{name}.lean"
    path.write_text(source, encoding="utf-8")
    try:
        result = subprocess.run(
            ["lake", "env", "lean", str(path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=lean_environment(),
        )
    except subprocess.TimeoutExpired as expired:
        output = (expired.stdout or "") + (expired.stderr or "")
        if isinstance(output, bytes):
            output = output.decode("utf-8", "replace")
        return LeanRun(1, output, source, path, timed_out=True)
    except OSError as error:
        # No elan, no lake, no Lean: a machine without the toolchain must produce a
        # report that says so, not a traceback that hides which question went unasked.
        return LeanRun(127, f"toolchain unavailable: {error}", source, path)
    return LeanRun(result.returncode, result.stdout + result.stderr, source, path)


def build_module(project_root: Path, module: str, timeout: int = 3600) -> LeanRun:
    """`lake build <module>`, so that `import <module>` resolves in a probe."""
    scratch = project_root / "out" / "claims" / "_scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            ["lake", "build", module],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=lean_environment(),
        )
    except subprocess.TimeoutExpired as expired:
        output = (expired.stdout or "") + (expired.stderr or "")
        if isinstance(output, bytes):
            output = output.decode("utf-8", "replace")
        return LeanRun(1, output, "", scratch, timed_out=True)
    except OSError as error:
        return LeanRun(127, f"toolchain unavailable: {error}", "", scratch)
    return LeanRun(result.returncode, result.stdout + result.stderr, "", scratch)


def _probe_source(target: FormalTarget) -> str:
    """The Lean source for a target's checks and axiom queries.

    Only `#check` and `#print axioms` are emitted, both of which can fail only when a
    name is missing: a mismatch in a statement does not abort the file, which matters
    because a mismatch is a finding rather than an error.
    """
    lines = ["-- generated by riemann_framework.claim_audit; not part of the library"]
    lines.extend(f"import {module}" for module in _imports(target))
    lines.append("")
    for statement in target.statements:
        lines.append(f'#eval IO.println "===type:{statement.name}==="')
        lines.append(f"#check @{statement.name}")
        if statement.mode == "print":
            lines.append(f'#eval IO.println "===body:{statement.name}==="')
            lines.append(f"#print {statement.name}")
    for name in target.axiom_targets:
        lines.append(f'#eval IO.println "===axioms:{name}==="')
        lines.append(f"#print axioms {name}")
    lines.append('#eval IO.println "===end==="')
    return "\n".join(lines) + "\n"


def _defeq_source(target: FormalTarget, statement: StatementTarget) -> str:
    """The kernel check for a proposition: `target = expected` by `rfl`.

    This file is expected *not* to compile when the identity fails, so it is always run
    on its own. `rfl` closes the goal only when the two sides are definitionally equal,
    which is exactly the question, and it is decided by the kernel rather than by
    comparing printed text.
    """
    lines = ["-- generated by riemann_framework.claim_audit; not part of the library"]
    lines.extend(f"import {module}" for module in _imports(target))
    lines.append("")
    lines.append(
        f"example : {statement.name} = {statement.expected} := rfl"
    )
    return "\n".join(lines) + "\n"


def _imports(target: FormalTarget) -> tuple[str, ...]:
    """Modules a probe must import: the target's own module, then the ones it needs.

    A record that compares a project module's statement to `RiemannHypothesis` names
    `Mathlib` explicitly in `imports`, because the expected statement lives there and
    the probe has to see both to compare them.
    """
    imports = [target.module] if target.module else []
    for module in target.imports:
        if module not in imports:
            imports.append(module)
    return tuple(imports)


@dataclass(frozen=True)
class FormalResult:
    """Everything the probe established about one formal target."""

    target: FormalTarget
    statuses: Mapping[LeanQuestion, Status]
    evidence: Mapping[LeanQuestion, str]
    build: LeanRun | None
    probe: LeanRun | None
    census: Mapping[str, Any]
    #: True when the module's source was actually read by `vacuity_census`. The
    #: difference between "scanned and nothing found" and "nothing to scan" is the
    #: difference between a weak statement and a false one.
    scanned: bool = False

    @property
    def live(self) -> bool:
        return self.probe is not None


def formal_check(
    target: FormalTarget,
    repo_root: Path,
    *,
    live: bool = True,
    timeout: int = 1800,
) -> FormalResult:
    """Run the four decidable questions, and locate what the fifth is about.

    When the artefact is absent, or `live` is false, the four are replayed from
    `target.recorded` and the statuses carry that provenance in their evidence. The
    fifth is never decided either way: `_non_vacuity_finding` always returns
    `undetermined`, with the located shapes as evidence.
    """
    root = target.root_path(repo_root)
    present = target.present(repo_root)
    census_source = ""
    if present:
        module_file = _module_path(root, target.module)
        if module_file.is_file():
            census_source = module_file.read_text(encoding="utf-8")
    scanned = bool(census_source)
    census = vacuity_census(census_source) if scanned else {
        "true_bodied_definitions": [], "true_lambdas": 0,
        "proposition_aliases": [], "rfl_defined_values": 0,
    }

    if not (live and present):
        return _replayed_result(target, census, present, scanned)

    build = build_module(root, target.module, timeout=timeout) if target.module else None
    probe = run_lean(root, _probe_source(target), name=f"probe_{_slug(target.role)}",
                     timeout=timeout)
    statuses: dict[LeanQuestion, Status] = {}
    evidence: dict[LeanQuestion, str] = {}

    compiled = probe.ok
    warning = _SORRY_WARNING.search(probe.output)
    holes: int | None = None
    where = ""
    if scanned:
        counts = sorry_census(census_source)
        holes = counts["sorry"] + counts["admit"]
        if counts["declarations"]:
            where = ": " + ", ".join(
                f"`{name}`" for name in counts["declarations"]
            )
    statuses[LeanQuestion.COMPILES] = (
        Status.CHECKED_OK if compiled else Status.CHECKED_FAILED
    )
    first_line = next(
        (line.strip() for line in probe.output.splitlines() if line.strip()), ""
    )
    evidence[LeanQuestion.COMPILES] = (
        f"`lake build {target.module}` exit {build.returncode if build else 'n/a'}; "
        f"`lake env lean` exit {probe.returncode}"
        + ("" if compiled else f": {first_line[:200]}")
    )

    if not compiled:
        statuses[LeanQuestion.NO_SORRY] = Status.UNDETERMINED
        evidence[LeanQuestion.NO_SORRY] = "not reachable: the file does not compile"
    elif warning or holes:
        statuses[LeanQuestion.NO_SORRY] = Status.CHECKED_FAILED
        evidence[LeanQuestion.NO_SORRY] = (
            (
                f"{holes} `sorry`/`admit` in the module source{where}"
                if holes is not None else
                "the module source was not found, so only Lean's warning was available"
            )
            + (", Lean warned `declaration uses sorry`" if warning else "")
        )
    elif holes is None:
        statuses[LeanQuestion.NO_SORRY] = Status.CHECKED_OK
        evidence[LeanQuestion.NO_SORRY] = (
            "no `sorry` warning from Lean; the module source was not found, so the "
            "source census could not run"
        )
    else:
        statuses[LeanQuestion.NO_SORRY] = Status.CHECKED_OK
        evidence[LeanQuestion.NO_SORRY] = (
            "no `sorry`/`admit` in the module source and no `sorry` warning from Lean"
        )

    axioms = parse_axioms(probe.output)
    observed: list[str] = []
    problem = ""
    for name in target.axiom_targets:
        found = axioms.get(name)
        if found is None:
            problem = problem or f"`#print axioms {name}` produced nothing"
            continue
        observed.append(f"{name}: [{', '.join(found) or 'none'}]")
        justified, reason = axioms_justified(found)
        if not justified:
            problem = problem or f"{name}: {reason}"
    if problem:
        statuses[LeanQuestion.AXIOMS_JUSTIFIED] = Status.CHECKED_FAILED
        evidence[LeanQuestion.AXIOMS_JUSTIFIED] = problem
    elif observed:
        statuses[LeanQuestion.AXIOMS_JUSTIFIED] = Status.CHECKED_OK
        evidence[LeanQuestion.AXIOMS_JUSTIFIED] = "; ".join(observed)
    else:
        statuses[LeanQuestion.AXIOMS_JUSTIFIED] = Status.NOT_APPLICABLE
        evidence[LeanQuestion.AXIOMS_JUSTIFIED] = "no axiom target was declared"

    statement_status, statement_evidence = _statement_result(target, probe, repo_root,
                                                            timeout=timeout)
    statuses[LeanQuestion.STATEMENT_MATCHES] = statement_status
    evidence[LeanQuestion.STATEMENT_MATCHES] = statement_evidence

    return FormalResult(
        target=target,
        statuses=statuses,
        evidence=evidence,
        build=build,
        probe=probe,
        census=census,
        scanned=scanned,
    )


def _statement_result(
    target: FormalTarget, probe: LeanRun, repo_root: Path, *, timeout: int
) -> tuple[Status, str]:
    """Compare each declared statement to the expected one, preferring the kernel."""
    if not target.statements:
        return Status.NOT_APPLICABLE, "no statement target was declared"
    sections = split_sections(probe.output)
    notes: list[str] = []
    failures = 0
    undetermined = 0
    for statement in target.statements:
        if statement.defeq:
            check = run_lean(
                target.root_path(repo_root),
                _defeq_source(target, statement),
                name=f"defeq_{_slug(statement.name)}",
                timeout=timeout,
            )
            if check.ok:
                notes.append(
                    f"`{statement.name} = {statement.expected}` closed by `rfl`: "
                    "definitionally equal, kernel-checked"
                )
                continue
            failures += 1
            notes.append(
                f"`{statement.name} = {statement.expected}` failed under `rfl`: "
                + _first_error(check.output)
            )
            continue
        key = f"body:{statement.name}" if statement.mode == "print" else f"type:{statement.name}"
        raw = sections.get(key)
        if raw is None:
            undetermined += 1
            notes.append(f"`{statement.name}` produced no output")
            continue
        if statement.mode == "print":
            body = raw.split(":=", 1)[-1] if ":=" in raw else raw
        else:
            _, body = _checked_type(raw)
        if normalise_statement(body) == normalise_statement(statement.expected):
            notes.append(
                f"`{statement.name}` prints as `{body.strip()}`: matches "
                f"`{statement.expected}` after normalisation"
            )
        else:
            failures += 1
            notes.append(
                f"`{statement.name}` prints as `{body.strip()}`, not "
                f"`{statement.expected}`"
            )
    if failures:
        return Status.CHECKED_FAILED, "; ".join(notes)
    if undetermined:
        return Status.UNDETERMINED, "; ".join(notes)
    return Status.CHECKED_OK, "; ".join(notes)


def _first_error(output: str) -> str:
    for line in output.splitlines():
        if "error" in line:
            return line.strip()[:240]
    return output.strip().splitlines()[0][:240] if output.strip() else "no output"


def _module_path(root: Path, module: str) -> Path:
    """Best-effort source path for a module name (`A.B` -> `A/B.lean` under `lean/`)."""
    if not module:
        return root
    relative = Path(*module.split(".")).with_suffix(".lean")
    for base in (root / "lean", root):
        candidate = base / relative
        if candidate.is_file():
            return candidate
    return root / "lean" / relative


def _replayed_result(
    target: FormalTarget,
    census: Mapping[str, Any],
    present: bool,
    scanned: bool = False,
) -> FormalResult:
    """Level 2 when the artefact is not here: the record, labelled as a record.

    A target with neither a live run nor a recorded result is reported as `not_run`.
    It is not reported as `undetermined`, because `undetermined` would suggest that
    something was asked and could not be answered, and nothing was asked.
    """
    recorded = target.recorded
    statuses: dict[LeanQuestion, Status] = {}
    evidence: dict[LeanQuestion, str] = {}
    questions = (LeanQuestion.COMPILES, LeanQuestion.NO_SORRY,
                 LeanQuestion.AXIOMS_JUSTIFIED, LeanQuestion.STATEMENT_MATCHES)
    if not recorded:
        why = (
            "the artefact is present but live Lean was not requested"
            if present else "the artefact is not on this machine"
        )
        unreached = {question: Status.NOT_RUN for question in questions}
        reasons = {question: f"not run: {why}" for question in questions}
        return FormalResult(
            target=target, statuses=unreached, evidence=reasons,
            build=None, probe=None, census=census, scanned=scanned,
        )

    def recorded_status(value: Any) -> Status:
        if value is True:
            return Status.CHECKED_OK
        if value is False:
            return Status.CHECKED_FAILED
        return Status.UNDETERMINED

    statuses[LeanQuestion.COMPILES] = recorded_status(recorded.get("compiles"))
    evidence[LeanQuestion.COMPILES] = str(recorded.get("compiles_evidence", "")) or (
        "replayed; see the recorded commands"
    )
    statuses[LeanQuestion.NO_SORRY] = recorded_status(recorded.get("sorry_free"))
    evidence[LeanQuestion.NO_SORRY] = str(recorded.get("sorry_evidence", "")) or (
        "replayed; see the recorded commands"
    )
    statuses[LeanQuestion.AXIOMS_JUSTIFIED] = recorded_status(
        recorded.get("axioms_justified")
    )
    evidence[LeanQuestion.AXIOMS_JUSTIFIED] = str(
        recorded.get("axioms_evidence", "")
    ) or "replayed; see the recorded commands"
    statuses[LeanQuestion.STATEMENT_MATCHES] = recorded_status(
        recorded.get("statement_matches")
    )
    evidence[LeanQuestion.STATEMENT_MATCHES] = str(
        recorded.get("statement_evidence", "")
    ) or "replayed; see the recorded commands"

    reason = (
        "replayed from the audit record of " + (target.recorded_on or "an unrecorded date")
        + ("; the archive is present but live Lean was not requested"
           if present else "; the artefact is not on this machine")
    )
    for question in questions:
        evidence[question] = f"{evidence[question]} ({reason})"
    return FormalResult(
        target=target,
        statuses=statuses,
        evidence=evidence,
        build=None,
        probe=None,
        census=census,
        scanned=scanned,
    )


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()[:48] or "target"


# ============================================================
# The dependency trace: the fifth question, decided
# ============================================================

#: The module that provides `#deps`. Only `import Lean` is needed, so the same source
#: compiles in a foreign project that depends on Mathlib alone.
TRACE_MODULE = "RiemannFramework.DependencyTrace"

_DEPS_BEGIN = "DEPS_BEGIN"
_DEPS_END = "DEPS_END"


def parse_deps(output: str) -> dict[str, set[str]]:
    """`{theorem: closure}` from the `DEPS_BEGIN`/`DEPS_END` blocks of a trace run.

    The theorem name is on the begin marker, so a driver that traces several theorems in
    one file yields one block per theorem rather than a concatenation nobody can attribute.
    """
    blocks: dict[str, set[str]] = {}
    current: str | None = None
    for line in output.splitlines():
        text = line.strip()
        if text.startswith(_DEPS_BEGIN):
            current = text[len(_DEPS_BEGIN):].strip() or "<unnamed>"
            blocks.setdefault(current, set())
        elif text.startswith(_DEPS_END):
            current = None
        elif current is not None and text and not text.startswith("DEPS_COUNT"):
            blocks[current].add(text)
    return blocks


def suspect_reachable(closure: set[str], suspect: str) -> str | None:
    """The fully qualified name in `closure` that answers to `suspect`, or None.

    Objection documents quote short names (`anyGeometry`); the environment holds
    qualified ones (`RiemannFramework...anyGeometry`). Exact match or a dotted suffix
    match, so the comparison works in both directions and never guesses at a prefix.
    """
    if suspect in closure:
        return suspect
    suffix = "." + suspect
    for name in closure:
        if name.endswith(suffix):
            return name
    return None


def dependency_trace(
    project_root: Path,
    module: str,
    request: TraceRequest,
    *,
    trace_module: str = TRACE_MODULE,
    timeout: int = 3600,
    name_prefix: str = "deps",
    extractor: str = "deps",
) -> tuple[Status, dict[str, Any]]:
    """Run one extractor on one theorem and intersect the closure with the suspects.

    Returns `(status, details)`. `details` always carries the closure size and, when the
    trace ran, which suspects were reached: those two numbers are what a reviewer needs to
    see, because "not reached" is only meaningful next to the size of what *was*.

    `details["names"]` is the closure itself, a `set`, and is deliberately **not** part of
    a finding: a Mathlib-backed closure runs to thousands of names and would bury the
    report. The caller that needs it — the cross-validation — compares the two sets and
    records only the difference.
    """
    imports = [m for m in (trace_module, module) if m]
    source = "\n".join(f"import {m}" for m in dict.fromkeys(imports))
    source += f"\n\n#{extractor} {request.theorem}\n"
    run = run_lean(
        project_root, source, name=f"{name_prefix}_{_slug(request.theorem)}",
        timeout=timeout,
    )
    blocks = parse_deps(run.output)
    closure = blocks.get(request.theorem, set())
    if len(blocks) == 1 and not closure:
        closure = next(iter(blocks.values()))
    if not run.ok or not closure:
        return Status.NOT_RUN, {
            "extractor": extractor,
            "closure": 0,
            "names": set(),
            "reached": [],
            "run": run,
            "output": run.output,
        }
    reached = []
    for suspect in request.suspects:
        found = suspect_reachable(closure, suspect)
        if found is not None:
            reached.append(found)
    return Status.CHECKED_FAILED if reached else Status.CHECKED_OK, {
        "extractor": extractor,
        "closure": len(closure),
        "names": set(closure),
        "reached": sorted(set(reached)),
        "run": run,
        "output": run.output,
    }


#: How many names of a disagreement are printed before the record switches to a count.
#: A diff of two thousand Mathlib names helps nobody; the first few usually name the cause.
DISCREPANCY_SAMPLE = 12


def compare_closures(
    theorem: str,
    first: dict[str, Any],
    second: dict[str, Any],
) -> dict[str, Any]:
    """Compare two closures of the same theorem and record the difference.

    The rule the specification states, applied without a fallback that could hide a
    disagreement: identical closures corroborate the extraction; different closures leave
    the trace `undetermined` and name the reconciliation as the computation that would
    settle it. A disagreement is never averaged, never resolved in favour of the first
    extractor, and never dropped because the two agree on the suspects: the closure is the
    object being certified, so its bounds have to agree and not only its intersection with
    a list written by hand.
    """
    left = set(first.get("names", ()))
    right = set(second.get("names", ()))
    only_left = sorted(left - right)
    only_right = sorted(right - left)
    agreement = bool(left) and left == right
    payload: dict[str, Any] = {
        "theorem": theorem,
        "extractors": [first.get("extractor", "deps"), second.get("extractor", "depsm")],
        "counts": {
            first.get("extractor", "deps"): len(left),
            second.get("extractor", "depsm"): len(right),
        },
        "agreement": agreement,
        "discrepancy": not agreement,
        "only_in_" + str(first.get("extractor", "deps")): only_left[:DISCREPANCY_SAMPLE],
        "only_in_" + str(second.get("extractor", "depsm")): only_right[:DISCREPANCY_SAMPLE],
        "only_in_first_count": len(only_left),
        "only_in_second_count": len(only_right),
        "reached": {
            str(first.get("extractor", "deps")): list(first.get("reached", [])),
            str(second.get("extractor", "depsm")): list(second.get("reached", [])),
        },
        "verdict": (
            Verdict.VALIDATED_TERM.value if agreement else Verdict.UNDETERMINED.value
        ),
        "named_computation": (
            None if agreement
            else "reconcile the closure mismatch between `#deps` and `#depsm` for "
                 f"`{theorem}`: {len(only_left)} name(s) in the first and not the second, "
                 f"{len(only_right)} in the second and not the first"
        ),
        "scope": (
            "Both extractors read the same environment and differ only in how they walk "
            "an expression, so agreement rules out a defect in this module's traversal, "
            "not a defect in Lean's environment or in the definitions a closure passes "
            "through. The MIT verification page states the same limit for its own "
            "checks; it is not closed here."
        ),
    }
    return payload


def cross_validate_closures(
    project_root: Path,
    module: str,
    request: TraceRequest,
    *,
    first: tuple[Status, dict[str, Any]],
    timeout: int,
    trace_module: str = TRACE_MODULE,
) -> dict[str, Any]:
    """Run the second extractor and record how the two closures compare.

    Both extractors are always attempted, so that a failure of one is *recorded* rather
    than turning into a missing number: the rule is that one extractor failing falls back
    to the other and reports the failed one as `undetermined` with a named repair, while
    both failing leaves the trace `undetermined` with no closure at all.
    """
    _, first_details = first
    _, second_details = dependency_trace(
        project_root, module, request, timeout=timeout,
        trace_module=trace_module, name_prefix="depsm", extractor="depsm",
    )
    first_ran = bool(first_details.get("names"))
    second_ran = bool(second_details.get("names"))
    if first_ran and second_ran:
        payload = compare_closures(request.theorem, first_details, second_details)
        payload["supplied_by"] = "deps"
        return payload
    ran = "deps" if first_ran else "depsm" if second_ran else None
    failed = None if ran is None else ("depsm" if ran == "deps" else "deps")
    payload = {
        "theorem": request.theorem,
        "extractors": ["deps", "depsm"],
        "agreement": False,
        "discrepancy": None,
        "fallback": ran,
        "failed": failed,
        "counts": {
            "deps": len(first_details.get("names", ())),
            "depsm": len(second_details.get("names", ())),
        },
        "verdict": Verdict.UNDETERMINED.value,
        "named_computation": (
            "no extractor produced a closure: run `#deps` and `#depsm` on "
            f"`{request.theorem}` in a project that builds"
            if ran is None
            else f"repair the `#{failed}` extractor on `{request.theorem}` and rerun the "
                 f"cross-validation; `#{ran}` supplied the closure in the meantime"
        ),
        "scope": (
            "One extractor's closure is a single instrument reading, and a single "
            "reading is what this protocol exists to stop promoting to a verdict. The "
            "fallback is recorded, not used as if the two had agreed."
        ),
    }
    return payload


def trace_with_cross_validation(
    project_root: Path,
    module: str,
    request: TraceRequest,
    *,
    timeout: int,
    trace_module: str = TRACE_MODULE,
) -> tuple[Status, dict[str, Any]]:
    """Both extractors, merged into one record the finding can be built from.

    The closure reported is the first extractor's when it ran, otherwise the second's,
    and `cross_validation.fallback` says which. A reader who wants the disagreement gets
    it in the same payload; a reader who wants the closure gets one number, not two.
    """
    first = dependency_trace(
        project_root, module, request, timeout=timeout,
        trace_module=trace_module, name_prefix="deps", extractor="deps",
    )
    cross = cross_validate_closures(
        project_root, module, request, first=first, timeout=timeout,
        trace_module=trace_module,
    )
    status, details = first
    if status is Status.NOT_RUN and cross.get("fallback") == "depsm":
        status, details = dependency_trace(
            project_root, module, request, timeout=timeout,
            trace_module=trace_module, name_prefix="depsm", extractor="depsm",
        )
    merged = dict(details)
    merged["cross_validation"] = cross
    merged["extractor"] = details.get("extractor", "deps")
    return status, merged

def trace_finding(
    target: FormalTarget,
    request: TraceRequest,
    repo_root: Path,
    *,
    live: bool,
    timeout: int,
) -> Finding:
    """The trace as a finding: decided, failed, or not run with the command that would.

    The three cases are kept apart because they mean different things. A trace that ran
    and reached a flagged definition **decides the objection in its favour**: the term
    really does pass through the vacuous obligation. A trace that ran and reached none
    refutes it *for those names*. A trace that did not run proves nothing, and says so
    with the exact command a reader can run.
    """
    root = target.root_path(repo_root)
    present = target.present(repo_root)
    instrument = (
        "`#deps` and `#depsm` over Lean's environment, compared; " + target.role
    )
    limits = (
        "Syntactic reachability, not semantic dependence: a flagged definition can appear "
        "in the closure because an unused hypothesis mentions it, so a hit is evidence "
        "that the objection's route exists rather than proof that the conclusion uses it. "
        "Absence is the stronger half: a name outside the closure cannot have contributed "
        "to the term at all. The closure is taken over types and values, not over the "
        "tactics that produced them. The two extractors share Lean's environment, so their "
        "agreement rules out a defect in this module's traversal and not a defect in the "
        "definitions the closure passes through."
    )
    if not (live and present):
        why = (
            "the artefact is present but live Lean was not requested"
            if present else "the artefact is not on this machine"
        )
        command = (
            "import " + TRACE_MODULE + "\n#import " + (target.module or "<module>")
            + "\n#deps " + request.theorem
        )
        return Finding(
            level=Level.FORMAL,
            check=f"{target.role}: dependency trace of `{request.theorem}`",
            status=Status.NOT_RUN,
            verdict=Verdict.NOT_ASSESSED,
            instrument=f"`#deps`; not run ({why})",
            evidence=(
                f"not run: {why}. The trace is the decisive computation for the vacuity "
                f"question and it is pending here. With the artefact in place, the driver "
                f"is:\n\n```lean\n{command}\n```\n"
            ),
            limits=limits,
            instrument_class=Instrument.DEPENDENCY_TRACE,
        )
    status, details = trace_with_cross_validation(
        root, target.module, request, timeout=timeout
    )
    if status is Status.NOT_RUN:
        first = next(
            (line.strip() for line in str(details["output"]).splitlines() if line.strip()),
            "",
        )
        return Finding(
            level=Level.FORMAL,
            check=f"{target.role}: dependency trace of `{request.theorem}`",
            status=Status.NOT_RUN,
            verdict=Verdict.NOT_ASSESSED,
            instrument=instrument,
            evidence=f"the trace did not produce a closure: {first[:240]}",
            limits=limits,
            instrument_class=Instrument.DEPENDENCY_TRACE,
        )
    reached = details["reached"]
    cross = dict(details.get("cross_validation", {}))
    payload = {
        "theorem": request.theorem,
        "module": target.module,
        "closure": details["closure"],
        "reached": list(reached),
        "suspects": list(request.suspects),
        "role": target.role,
        "extractor": details.get("extractor", "deps"),
        "cross_validation": cross,
    }
    if status is Status.CHECKED_FAILED:
        return Finding(
            level=Level.FORMAL,
            check=f"{target.role}: dependency trace of `{request.theorem}`",
            status=Status.CHECKED_FAILED,
            verdict=Verdict.UNDETERMINED,
            instrument=instrument,
            evidence=(
                f"the closure of `{request.theorem}` has {details['closure']} constants "
                f"and reaches {len(reached)} flagged definition(s): "
                + ", ".join(f"`{name}`" for name in reached)
                + ". The objection's route exists in this term; whether it is "
                "load-bearing is the named computation below."
            ),
            limits=limits,
            instrument_class=Instrument.DEPENDENCY_TRACE,
            details=payload,
        )
    return Finding(
        level=Level.FORMAL,
        check=f"{target.role}: dependency trace of `{request.theorem}`",
        status=Status.CHECKED_OK,
        verdict=Verdict.VALIDATED_TERM,
        instrument=instrument,
        evidence=(
            f"the closure of `{request.theorem}` has {details['closure']} constants and "
            f"reaches none of {len(request.suspects)} flagged definition(s): "
            + ", ".join(f"`{name}`" for name in request.suspects)
            + (
                f". Cross-validation: `#deps` and `#depsm` agree exactly on all "
                f"{details['closure']} names."
                if cross.get("agreement")
                else ". Cross-validation: the extraction is not corroborated ("
                     + (cross.get("named_computation") or "the second extractor did not run")
                     + ")."
            )
        ),
        limits=limits,
        instrument_class=Instrument.DEPENDENCY_TRACE,
        details=payload,
    )


def target_verdict(kernel_ok: bool, trace_statuses: Sequence[Status]) -> Verdict:
    """The verdict one formal artefact supports, and no stronger.

    This is the paper's rule in code: a kernel pass is a term verdict only together with a
    trace that came back clean. Kernel and no trace is `undetermined`, not `validated
    (term)`; a trace that reached a flagged definition is also `undetermined`, because the
    objection survives and the computation that would settle it is named.
    """
    if not kernel_ok:
        return Verdict.UNDETERMINED
    if any(status is Status.CHECKED_FAILED for status in trace_statuses):
        return Verdict.UNDETERMINED
    if trace_statuses and all(status is Status.CHECKED_OK for status in trace_statuses):
        return Verdict.VALIDATED_TERM
    return Verdict.UNDETERMINED


# ============================================================
# Level 1: the repository's own instruments
# ============================================================

@dataclass(frozen=True)
class Probe:
    """One falsification test, and the module that performs it.

    `instrument` names a module in this package and the tests check three things about
    it: the module exists, the probe function's source mentions it, and the probe runs
    without raising. The second is the one that matters: it is the difference between
    "the audit used the repository's instrument" and "the audit says it did".
    """

    key: str
    instrument: str
    decides: str
    run: Callable[[Claim], Finding]


def probe_numerical_domain(claim: Claim) -> Finding:
    """Can any instrument in the inventory take this claim as input?

    Asks the inventory rather than asserting an answer. Every row is an input to an
    argument, not a proof, and none of them is a document, a theorem, or a term; so a
    claim whose content is "a proof of RH exists" has no row to enter at.
    """
    from . import dh_filter

    rows = dh_filter.inventory_table()
    keys = ", ".join(row["key"] for row in rows)
    return Finding(
        level=Level.NUMERICAL,
        check="the claim enters an instrument's domain",
        status=Status.NOT_APPLICABLE,
        verdict=Verdict.OUTSIDE_DOMAIN,
        instrument="riemann_framework.dh_filter (inventory)",
        instrument_class=Instrument.DH_SCREEN,
        evidence=(
            f"{len(rows)} inventoried inputs, none of which is a proof, a theorem or "
            f"a term: {keys}. A claim that asserts a proof exists is not a statement "
            "about spectra, expressions or finite certificates."
        ),
        limits=(
            "This is a fact about the instruments, not about the claim. The paper "
            "calls it `outside domain`; it says the repository has nothing to point at "
            "the claim, not that the claim is wrong."
        ),
    )


def probe_dh_screen(claim: Claim) -> Finding:
    """Point the Davenport–Heilbronn contrapositive at the claim's declared inputs.

    The filter's rule: an argument that goes through unchanged where RH fails cannot
    establish RH. `dead` means it found a transferable-input-only argument (rejected);
    `eligible` means at least one declared input fails for DH, which is permission to
    continue and nothing more; `needs_sourcing` means the filter cannot tell.
    """
    from . import dh_filter

    result = dh_filter.screen_inputs(claim.id, list(claim.declared_inputs))
    verdict = {
        dh_filter.DHVerdict.DEAD: Verdict.REJECTED,
        dh_filter.DHVerdict.ELIGIBLE: Verdict.UNDETERMINED,
        dh_filter.DHVerdict.NEEDS_SOURCING: Verdict.UNDETERMINED,
    }[result.verdict]
    status = (
        Status.CHECKED_FAILED if result.verdict is dh_filter.DHVerdict.DEAD
        else Status.CHECKED_OK
    )
    return Finding(
        level=Level.NUMERICAL,
        check="declared inputs survive the Davenport–Heilbronn substitution",
        status=status,
        verdict=verdict,
        instrument="riemann_framework.dh_filter",
        instrument_class=Instrument.DH_SCREEN,
        evidence=(
            f"declared inputs {sorted(claim.declared_inputs)}; filter verdict "
            f"`{result.verdict.value}`. {result.summary}"
        ),
        limits=(
            "The filter classifies declared inputs only, and a declaration is a "
            "claimant's own inventory. `eligible` is permission, not promise: it says "
            "the argument has somewhere for its arithmetic to live."
        ),
    )


def probe_zero_consistency(claim: Claim) -> Finding:
    """Check the first few zeros are zeros and on the line.

    `mpmath.zetazero` returns zeros on the critical line by construction, so the
    on-line half of this check is arithmetic consistency and not a test of the
    hypothesis. Reported for exactly that reason: it is the check most often mistaken
    for evidence.
    """
    from . import zeros

    rows = zeros.verify_first_n_zeros(3)
    on_line = all(row["on_critical_line"] for row in rows)
    located = ", ".join(
        f"rho_{row['n']} = 1/2 + {float(row['im']):.6f}i" for row in rows
    )
    return Finding(
        level=Level.NUMERICAL,
        check="the first three non-trivial zeros are zeros and on the line",
        status=Status.CHECKED_OK if on_line else Status.CHECKED_FAILED,
        verdict=Verdict.VALIDATED_FINITE,
        instrument="riemann_framework.zeros",
        instrument_class=Instrument.NUMERICAL,
        evidence=f"{located}; all on the critical line at the working precision",
        limits=(
            "A finite computation about three zeros. The zeros were *found* by a "
            "routine that searches the critical line, so the on-line column cannot "
            "fail and is not evidence for the hypothesis; see `docs/verification_report.md`."
        ),
    )


def probe_proportion_constants(claim: Claim) -> Finding:
    """Recompute the constant chain of the proportion theorems.

    Applies when the claim sits next to the Alpöge–Furman / Lamzouri proportion
    results, whose constants are pure arithmetic. `2 - R(psi)` and `(3 - R(psi))/2` are
    checked to the published values; a slip there would be invisible in prose.
    """
    from . import proportion_certificates

    checks = proportion_certificates.constant_chain_matches_paper()
    constants = proportion_certificates.montgomery_taylor_constants()
    failed = sorted(name for name, ok in checks.items() if not ok)
    return Finding(
        level=Level.NUMERICAL,
        check="the proportion constants reproduce the published figures",
        status=Status.CHECKED_FAILED if failed else Status.CHECKED_OK,
        verdict=Verdict.VALIDATED_FINITE,
        instrument="riemann_framework.proportion_certificates",
        instrument_class=Instrument.NUMERICAL,
        evidence=(
            (f"failed: {failed}" if failed else "all six comparisons hold")
            + f"; 2 - R(psi_MT) = {constants['simple_montgomery_taylor']:.10f}, "
            f"(3 - R(psi_MT))/2 = {constants['distinct_montgomery_taylor']:.10f}"
        ),
        limits=(
            "Arithmetic about a proportion of zeros. It is not a statement about the "
            "hypothesis, and neither paper claims one; the constants are shared by "
            "arguments whose ceiling their own authors state."
        ),
    )


#: Inventory inputs that are **equivalent** to the Riemann hypothesis, with the source of
#: the equivalence. An argument whose only Davenport-Heilbronn-discriminating input sits
#: here does not establish RH: it assumes it.
#:
#: The table is one row long because the inventory has one such row, and that is a fact
#: worth stating rather than a gap: `dh_filter.py` documents `li_positivity` as "the
#: RH-equivalent positivity lambda_n >= 0 for all n (Li's criterion)". The classification
#: below is total over the inventory, so a reader can see the other eight were considered
#: and why each is not an equivalence.
RH_EQUIVALENT_INPUTS: dict[str, tuple[str, str]] = {
    "li_positivity": (
        "Li's criterion: lambda_n >= 0 for all n is equivalent to RH, and Keiper's "
        "sequence is equivalent to it",
        "Li (1997), J. Number Theory 65; Keiper (1992); as recorded in the inventory row",
    ),
}

#: The rest of the inventory, and why each is *not* an RH-equivalence. A total function
#: over the inventory is what keeps the screen from looking vacuous: "not flagged" has to
#: mean "considered and rejected", not "not thought about".
NOT_RH_EQUIVALENT: dict[str, str] = {
    "functional_equation": "a completion property the Davenport-Heilbronn function shares",
    "real_coefficients": "a symmetry of the coefficient field, also shared",
    "zero_symmetry": "a consequence of the two symmetries above, not of RH",
    "hadamard_product": "order and entireness, which DH also has",
    "euler_product": (
        "a structural property whose *absence* for DH is what makes DH a counterexample "
        "source; having one for zeta is not equivalent to RH"
    ),
    "explicit_formula_prime_side": (
        "the explicit formula is a theorem (Guinand-Weil) for both functions; RH is "
        "equivalent to a positivity on the arithmetic side, which is a different input"
    ),
    "riemann_von_mangoldt_count": "a zero-counting asymptotic that holds unconditionally",
    "gue_pair_correlation": (
        "a statistical conjecture about spacings; nothing here establishes an "
        "equivalence to RH, and this repository's own screen records it as unsourced"
    ),
}


def probe_circularity(claim: Claim) -> Finding:
    """Does the argument assume the thing it claims to prove?

    The dual of the Davenport-Heilbronn screen. DH asks whether an argument would also
    prove a false statement; this asks whether it already assumes a true one. Both are
    cheap, and neither is sufficient: an argument can pass DH (its inputs fail for DH) and
    still be circular, which is exactly what happens when the discriminating input is
    Li's criterion. The screen classifies declared inputs only, and a claim that declares
    none is unscreened rather than circular.
    """
    from . import dh_filter

    inventory = dh_filter.DH_INPUTS
    unknown = [key for key in claim.declared_inputs if key not in inventory]
    if unknown:
        raise ValueError(
            f"{claim.id}: declared inputs {unknown} are not in the DH inventory "
            f"({sorted(inventory)}); the circularity screen classifies inventory keys only"
        )
    declared = [key for key in claim.declared_inputs if key in RH_EQUIVALENT_INPUTS]
    if not claim.declared_inputs:
        return Finding(
            level=Level.NUMERICAL,
            check="the declared inputs are not equivalent to the Riemann hypothesis",
            status=Status.NOT_APPLICABLE,
            verdict=Verdict.NOT_ASSESSED,
            instrument="riemann_framework.dh_filter inventory, plus the equivalence table",
            evidence=(
                "the record declares no inputs, so there is nothing to classify. An "
                "undeclared argument is unscreened, not circular: the screen reads a "
                "declaration, and a claim that supplies none is a claim the screen "
                "cannot read."
            ),
            limits=(
                "This is not a pass. The circularity screen is total over the inventory "
                "and blind to everything outside it: an argument that restates RH in "
                "vocabulary the inventory does not hold is not caught here."
            ),
            instrument_class=Instrument.CIRCULARITY,
        )
    if not declared:
        return Finding(
            level=Level.NUMERICAL,
            check="the declared inputs are not equivalent to the Riemann hypothesis",
            status=Status.CHECKED_OK,
            verdict=Verdict.NOT_ASSESSED,
            instrument="riemann_framework.dh_filter inventory, plus the equivalence table",
            evidence=(
                f"declared inputs {sorted(claim.declared_inputs)}; none is in the "
                f"RH-equivalence table, which holds {sorted(RH_EQUIVALENT_INPUTS)}. Each "
                "of the other inventoried inputs was classified as not equivalent, with "
                "the reason recorded in `NOT_RH_EQUIVALENT`."
            ),
            limits=(
                "Passing means the argument does not assume one of the known RH "
                "restatements. It does not mean the argument is non-circular: circularity "
                "can hide in a definition the inventory has never seen, and an argument "
                "can also assume something *stronger* than RH, which would prove it "
                "without being equivalent to it."
            ),
            instrument_class=Instrument.CIRCULARITY,
        )
    statements = "; ".join(
        f"`{key}`: {RH_EQUIVALENT_INPUTS[key][0]} ({RH_EQUIVALENT_INPUTS[key][1]})"
        for key in declared
    )
    # The sharp case is the one already in the inventory: an input that is RH-equivalent
    # *and* fails for Davenport-Heilbronn is what makes `eligible` uninformative, because
    # the filter marks the argument eligible for exactly the reason it cannot be a proof.
    discriminators = [
        key for key in declared if inventory[key].status is dh_filter.InputStatus.FAILS
    ]
    sharp = ""
    if discriminators:
        sharp = (
            f" {', '.join(f'`{key}`' for key in discriminators)} also fails for "
            "Davenport-Heilbronn, so the filter marks this argument `eligible` on the "
            "strength of the very input that makes it circular: eligibility and "
            "circularity are the same fact about it."
        )
    return Finding(
        level=Level.NUMERICAL,
        check="the declared inputs are not equivalent to the Riemann hypothesis",
        status=Status.CHECKED_FAILED,
        verdict=Verdict.REJECTED,
        instrument="riemann_framework.dh_filter inventory, plus the equivalence table",
        evidence=(
            f"the argument declares {statements}." + sharp + " An input equivalent to the "
            "hypothesis makes the DH screen's `eligible` verdict carry no information "
            "about whether the argument proves RH: an argument resting on it says nothing "
            "that the hypothesis did not already say."
        ),
        limits=(
            "This rejects the argument as a route to the hypothesis, not the hypothesis "
            "and not the input: Li's criterion is a theorem for zeta, and the argument "
            "may be a perfectly good proof that RH implies RH. What it cannot be is a "
            "proof of RH."
        ),
        instrument_class=Instrument.CIRCULARITY,
    )


PROBES: dict[str, Probe] = {
    "numerical_domain": Probe(
        key="numerical_domain",
        instrument="dh_filter",
        decides="whether any inventoried instrument accepts the claim as input",
        run=probe_numerical_domain,
    ),
    "dh_screen": Probe(
        key="dh_screen",
        instrument="dh_filter",
        decides="whether the claim's declared inputs survive the DH substitution",
        run=probe_dh_screen,
    ),
    "circularity": Probe(
        key="circularity",
        instrument="dh_filter",
        decides="whether the declared inputs are RH-equivalent restatements",
        run=probe_circularity,
    ),
    "zero_consistency": Probe(
        key="zero_consistency",
        instrument="zeros",
        decides="whether the first zeros are zeros and on the line",
        run=probe_zero_consistency,
    ),
    "proportion_constants": Probe(
        key="proportion_constants",
        instrument="proportion_certificates",
        decides="whether the proportion constants reproduce",
        run=probe_proportion_constants,
    ),
}


# ============================================================
# Levels 2 and 3 as findings
# ============================================================

def _formal_findings(result: FormalResult) -> list[Finding]:
    """Turn one `FormalResult` into the five findings, in the order of the questions."""
    target = result.target
    role = target.role
    live = result.live
    not_run = all(
        result.statuses[question] is Status.NOT_RUN
        for question in (LeanQuestion.COMPILES, LeanQuestion.NO_SORRY,
                         LeanQuestion.AXIOMS_JUSTIFIED, LeanQuestion.STATEMENT_MATCHES)
    )
    source = (
        "this machine, live" if live
        else "not run" if not_run
        else f"audit record of {target.recorded_on or 'an unrecorded date'}"
    )
    limitations = {
        LeanQuestion.COMPILES: (
            "Compiling establishes that the term elaborates. It establishes nothing "
            "about what the term means."
        ),
        LeanQuestion.NO_SORRY: (
            "`sorry` in a statement file is not a hole in the proof; `sorryAx` in the "
            "axiom list is. The evidence line says which case this is."
        ),
        LeanQuestion.AXIOMS_JUSTIFIED: (
            "The standard three are the axioms Lean's own logic and Mathlib use. A "
            "term that uses them is a term of the stated type; it is not thereby a "
            "proof of anything outside the formal system."
        ),
        LeanQuestion.STATEMENT_MATCHES: (
            "A matching statement is the certified half of the claim. It does not make "
            "the proof non-vacuous: a faithful statement can be proved through "
            "definitions that carry no mathematics, which is the objection on record."
        ),
        LeanQuestion.DEFINITIONS_NON_VACUOUS: (
            "This is the question the dispute turns on and nothing here decides it. "
            "The census locates definitional shapes; whether the conclusion's proof "
            "term passes through them is a dependency trace that has not been done."
        ),
    }
    findings: list[Finding] = []
    decided = _formal_verdict(result)
    for question in (LeanQuestion.COMPILES, LeanQuestion.NO_SORRY,
                     LeanQuestion.AXIOMS_JUSTIFIED, LeanQuestion.STATEMENT_MATCHES):
        findings.append(
            Finding(
                level=Level.FORMAL,
                check=f"{role}: {question.value}",
                status=result.statuses[question],
                # The verdict belongs to the term, and the term is the statement row:
                # repeating `validated (term)` next to "does it compile" would let a
                # reader take one passing check for the whole result.
                verdict=(
                    decided if question is LeanQuestion.STATEMENT_MATCHES
                    else Verdict.NOT_ASSESSED
                ),
                instrument=f"Lean, via `lake env lean`; {source}",
                evidence=result.evidence[question],
                limits=limitations[question],
                instrument_class=Instrument.KERNEL,
            )
        )
    findings.append(_non_vacuity_finding(result))
    return findings


def _formal_verdict(result: FormalResult) -> Verdict:
    """The strongest verdict the four decidable questions support, and no stronger.

    `validated (term)` requires all four: a term that compiles, carries no hole, uses
    only the standard axioms, and has the stated type. Anything less is
    `undetermined`, and a `checked_failed` is still `undetermined` as a verdict on the
    *claim*: a file that does not compile has not been rejected by a logical screen,
    it has failed to be an artefact. A target that was not run at all gets no verdict,
    because a verdict from a check that never happened is the noise this agent exists
    to refuse.
    """
    questions = (LeanQuestion.COMPILES, LeanQuestion.NO_SORRY,
                 LeanQuestion.AXIOMS_JUSTIFIED, LeanQuestion.STATEMENT_MATCHES)
    statuses = [result.statuses[question] for question in questions]
    if all(status is Status.NOT_RUN for status in statuses):
        return Verdict.NOT_ASSESSED
    if all(status is Status.NOT_APPLICABLE for status in statuses):
        return Verdict.NOT_ASSESSED
    if all(status is Status.CHECKED_OK for status in statuses):
        return Verdict.VALIDATED_TERM
    return Verdict.UNDETERMINED


def _non_vacuity_finding(result: FormalResult) -> Finding:
    """Question five: always `undetermined`, with the located shapes as evidence.

    The honest output. A census of `fun _ _ _ => True` and `rfl`-defined fields can find
    the shapes an objection names, and it cannot say whether the conclusion depends on
    them. Reporting a status for this question other than `undetermined` would be the
    exact error the agent is built to avoid, so this function has no branch that returns
    one.
    """
    census = result.census
    names = list(census.get("true_bodied_definitions", []))
    aliases = [
        entry for entry in census.get("proposition_aliases", [])
        if entry.split(" :=")[0].strip() not in names
    ]
    lambdas = int(census.get("true_lambdas", 0))
    rfls = int(census.get("rfl_defined_values", 0))
    located = []
    if names:
        located.append("`True`-bodied: " + ", ".join(names))
    if lambdas:
        located.append(f"{lambdas} lambda(s) returning `True`")
    if aliases:
        located.append("proposition aliases: " + ", ".join(aliases))
    if rfls:
        located.append(f"{rfls} value(s) fixed by `rfl`")
    if located:
        evidence = "; ".join(located)
    elif result.scanned:
        evidence = (
            "the module source was read and contains no definitional escape hatch of "
            "the named shapes"
        )
    else:
        evidence = (
            "nothing was scanned: the artefact's source is not on this machine, so the "
            "census cannot report either way. The sites the objection names are in §5"
        )
    return Finding(
        level=Level.FORMAL,
        check=f"{result.target.role}: {LeanQuestion.DEFINITIONS_NON_VACUOUS.value}",
        status=Status.UNDETERMINED,
        verdict=Verdict.UNDETERMINED,
        instrument="textual census, not a dependency trace",
        evidence=evidence,
        limits=(
            "A locator. Whether the archive's conclusion passes through any of these "
            "definitions is a question about a 61 GB proof term's dependency graph, "
            "and it is the one question nobody has settled. Locating is not proving "
            "dependence, and the absence of a located shape is not a proof of "
            "non-vacuity either. The dependency trace findings below are what decides "
            "it, and `target_verdict` refuses a term verdict until they are clean."
        ),
        instrument_class=Instrument.VACUITY_SCAN,
        details={
            "true_bodied": names,
            "aliases": aliases,
            "true_lambdas": lambdas,
            "rfl_values": rfls,
            "scanned": result.scanned,
        },
    )


def _no_formalisation_findings(claim: Claim) -> list[Finding]:
    """The five questions, still asked, when the claim supplies no artefact.

    A report that simply omitted level 2 would look like a report whose level 2 passed.
    The questions are printed with `not_applicable` so a reader can see that the claim,
    not the audit, is what is missing.
    """
    return [
        Finding(
            level=Level.FORMAL,
            check=f"no formal artefact supplied: {question.value}",
            status=Status.NOT_APPLICABLE,
            verdict=Verdict.NOT_ASSESSED,
            instrument="none",
            instrument_class=Instrument.NONE,
            evidence="the claim record declares no formal target",
            limits=(
                "Nothing was asked. A prose claim can be a real proof and a formalised "
                "one cannot be checked for faithfulness by a kernel; the absence of an "
                "artefact removes only the second kind of check."
            ),
        )
        for question in LEAN_QUESTIONS
    ]


def _institutional_findings(claim: Claim, repo_root: Path) -> list[Finding]:
    """Level 3: the record, each entry with its source, plus the one hash it can check."""
    findings: list[Finding] = []
    if claim.document is not None:
        matches, evidence = claim.document.verify(repo_root)
        findings.append(
            Finding(
                level=Level.INSTITUTIONAL,
                check="E0: the primary document is archived and unchanged",
                status=Status.CHECKED_OK if matches else Status.CHECKED_FAILED,
                verdict=Verdict.NOT_ASSESSED,
                instrument="SHA-256 against `references/`",
                instrument_class=Instrument.NONE,
                evidence=evidence,
                limits=(
                    "A hash establishes that this file is the one the record was made "
                    "from. It establishes nothing about what the file says."
                ),
            )
        )
    else:
        findings.append(
            Finding(
                level=Level.INSTITUTIONAL,
                check="E0: the primary document is archived and unchanged",
                status=Status.NOT_APPLICABLE,
                verdict=Verdict.NOT_ASSESSED,
                instrument="none",
                evidence="the claim record names no archived document",
                limits="A claim without a hashable document cannot be rejoined later.",
            )
        )
    for fact in claim.institutional:
        findings.append(
            Finding(
                level=Level.INSTITUTIONAL,
                check=f"{fact.kind}: {fact.value}",
                status=Status.RECORDED,
                verdict=Verdict.NOT_ASSESSED,
                instrument=fact.source,
                instrument_class=Instrument.READING,
                evidence=fact.date + (f"; {fact.note}" if fact.note else ""),
                limits=(
                    "Recorded from the named source and not verified here. An "
                    "institution's statement is evidence of a community's judgement, "
                    "not of a theorem; the two are different objects."
                ),
            )
        )
    return findings


def panel_verdict(findings: Sequence[Finding],
                  target_verdicts: Sequence[Verdict]) -> Verdict:
    """The strongest verdict the whole panel supports, and no stronger.

    The rules, in the order they apply:

    1. `rejected` dominates. A logical screen that fired ends the evaluation, because
       nothing downstream can make an argument that proves a false analogue, or assumes
       the thing it claims to prove, into an argument that does not.
    2. When formal artefacts were supplied, the panel's answer is the best of *their*
       verdicts. A finite arithmetic check that happened to pass alongside says nothing
       about the claim; promoting it would let a consistency observation stand in for
       the thing under evaluation.
    3. When no artefact was supplied (or none answered), the strongest validated
       numerical verdict is the panel's answer, because that is all the panel has.
    4. Otherwise `undetermined`, and the report carries the computations that would
       decide it.
    """
    verdicts = [finding.verdict for finding in findings]
    if Verdict.REJECTED in verdicts:
        return Verdict.REJECTED
    if target_verdicts:
        if Verdict.VALIDATED_TERM in target_verdicts:
            return Verdict.VALIDATED_TERM
        if not all(verdict is Verdict.NOT_ASSESSED for verdict in target_verdicts):
            return Verdict.UNDETERMINED
    if Verdict.VALIDATED_ELEMENTARY in verdicts:
        return Verdict.VALIDATED_ELEMENTARY
    if Verdict.VALIDATED_FINITE in verdicts:
        return Verdict.VALIDATED_FINITE
    if not verdicts:
        return Verdict.NOT_ASSESSED
    if all(verdict is Verdict.NOT_ASSESSED for verdict in verdicts):
        return Verdict.NOT_ASSESSED
    if all(verdict in (Verdict.NOT_ASSESSED, Verdict.OUTSIDE_DOMAIN)
           for verdict in verdicts):
        return Verdict.OUTSIDE_DOMAIN
    return Verdict.UNDETERMINED


def evidence_classes(claim: Claim, findings: Sequence[Finding]) -> tuple[str, str]:
    """Which of the paper's five evidence classes the record reaches, and why.

    The classes are nested in **cost, not in strength** (paper §4), so this is reported
    as a set with its reasons, never as a score. `E3` without `E1` is a formalisation
    whose statement is not written down anywhere; that is not better, it is differently
    placed.
    """
    reached: list[str] = []
    reasons: list[str] = []
    if any(f.check.startswith("E0") and f.status is Status.CHECKED_OK for f in findings):
        reached.append("E0")
        reasons.append("E0: the document is archived and hashes to the recorded value")
    if claim.statement.strip() and claim.statement_location.strip():
        reached.append("E1")
        where = claim.statement_location.strip().splitlines()[0].strip()
        if len(where) > 80:
            where = where[:77].rstrip() + "..."
        reasons.append(f"E1: a statement is quoted at {where}")
    if claim.declared_inputs:
        reached.append("E2")
        reasons.append(
            "E2: declared inputs identified and classified by the DH filter"
        )
    if any(
        f.level is Level.FORMAL
        and f.check.endswith(LeanQuestion.COMPILES.value)
        and f.status is Status.CHECKED_OK
        and "this machine, live" in f.instrument
        for f in findings
    ):
        # E3 is "a machine-checkable artefact compiles", and a replay is not a compile
        # on this machine. Reporting E3 off a recorded run would be the class ladder
        # doing the work the evidence is supposed to do.
        reached.append("E3")
        reasons.append("E3: a machine-checkable artefact compiles here")
    if any(
        fact.kind == "independent_replay" and "reproduced" in fact.value.lower()
        for fact in claim.institutional
    ):
        reached.append("E4")
        reasons.append("E4: an independent party is recorded as reproducing a check")
    if not reached:
        return "none", "no class is reached; the record has no document and no statement"
    return ", ".join(reached), "; ".join(reasons)


# ============================================================
# The report
# ============================================================

@dataclass(frozen=True)
class ClaimReport:
    """A claim's audit, and the sentences that keep it from being read as a verdict."""

    claim: Claim
    findings: tuple[Finding, ...]
    evidence: str
    evidence_reasons: str
    position: str = STANDING_POSITION
    #: `(role, verdict)` per formal artefact, plus the panel verdict those support. The
    #: pair is kept rather than collapsed so a report cannot show a term verdict it did
    #: not earn: the panel verdict is the one the whole panel supports.
    targets: tuple[tuple[str, Verdict], ...] = ()
    panel: Verdict = Verdict.NOT_ASSESSED

    @property
    def by_level(self) -> dict[Level, list[Finding]]:
        grouped: dict[Level, list[Finding]] = {level: [] for level in Level}
        for finding in self.findings:
            grouped[finding.level].append(finding)
        return grouped

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": {
                "id": self.claim.id,
                "title": self.claim.title,
                "claimant": self.claim.claimant,
                "date": self.claim.date,
                "statement": self.claim.statement,
                "statement_location": self.claim.statement_location,
                "declared_inputs": list(self.claim.declared_inputs),
                "probes": list(self.claim.probes),
                "notes": self.claim.notes,
            },
            "document": (None if self.claim.document is None else {
                "path": self.claim.document.path,
                "sha256": self.claim.document.sha256,
                "bytes": self.claim.document.bytes,
                "pages": self.claim.document.pages,
                "url": self.claim.document.url,
                "retrieved": self.claim.document.retrieved,
            }),
            "evidence_classes": self.evidence,
            "evidence_reasons": self.evidence_reasons,
            "panel_verdict": self.panel.value,
            "target_verdicts": [
                {"role": role, "verdict": verdict.value}
                for role, verdict in self.targets
            ],
            "findings": [finding.as_dict() for finding in self.findings],
            "objections": [objection.as_dict() for objection in self.claim.objections],
            "formal": [
                {
                    "role": target.role,
                    "root": target.root,
                    "module": target.module,
                    "recorded_on": target.recorded_on,
                    "commands": list(target.commands),
                    "note": target.note,
                }
                for target in self.claim.formal
            ],
            "position": self.position,
        }

    def render_markdown(self) -> str:
        """The report, as the document a reviewer reads.

        Every sentence this function writes is scanned for a proof claim before the
        document is returned; quoted material is rendered as a block quote and is
        exempt. A report that cannot say what its subject says would be useless, and a
        report that says it in its own voice would be the failure this repository keeps
        guarding against.
        """
        claim = self.claim
        lines: list[str] = []
        lines.append(f"# Claim audit: {claim.title}")
        lines.append("")
        lines.append(f"**Claim** `{claim.id}` &nbsp; **Claimant** {claim.claimant} "
                     f"&nbsp; **Date** {claim.date}")
        if claim.document is not None:
            document = claim.document
            lines.append("")
            lines.append(
                f"**Document** `{document.path}` &nbsp; sha256 "
                f"`{document.sha256[:16]}...` &nbsp; {document.bytes} bytes &nbsp; "
                f"{document.pages} pp. &nbsp; retrieved {document.retrieved}"
            )
        lines.append("")
        lines.append(f"**Evidence classes reached** {self.evidence}")
        lines.append("")
        lines.append(f"**Panel verdict** `{self.panel.value}`")
        if self.targets:
            lines.append("")
            lines.append(
                "Per formal artefact: "
                + "; ".join(
                    f"{role} `{verdict.value}`" for role, verdict in self.targets
                )
                + "."
            )
        lines.append("")
        lines.append(
            "The panel verdict is the strongest verdict *the panel* supports, not the "
            "strongest any one check reached. A kernel pass counts as `validated (term)` "
            "only together with a dependency trace that came back clean; a kernel pass "
            "without a trace is `undetermined` by construction, and so is a trace that "
            "reached a definition the objection named."
        )
        lines.append("")
        lines.append(f"> {self.position}")
        lines.append("")
        lines.append("## 1. The claim, as stated")
        lines.append("")
        for paragraph in claim.statement.strip().split("\n\n"):
            lines.append(f"> {paragraph.strip()}")
            lines.append("")
        lines.append(f"**Where it is stated.** {claim.statement_location}")
        if claim.declared_inputs:
            lines.append("")
            lines.append(
                "**Declared inputs:** "
                + ", ".join(f"`{key}`" for key in claim.declared_inputs)
            )
        lines.append("")

        for number, (level, title) in enumerate(
            (
                (Level.NUMERICAL, "Level 1, numerical consistency"),
                (Level.FORMAL, "Level 2, formal"),
                (Level.INSTITUTIONAL, "Level 3, institutional"),
            ),
            start=2,
        ):
            lines.append(f"## {number}. {title}")
            lines.append("")
            grouped = self.by_level[level]
            if not grouped:
                lines.append("No check at this level applies to the claim.")
                lines.append("")
                continue
            lines.append("| check | status | verdict | what was observed |")
            lines.append("|:---|:---|:---|:---|")
            for finding in grouped:
                lines.append(finding.as_row())
            lines.append("")
            lines.append("<details><summary>Instrument, and what each check does "
                         "not establish</summary>")
            lines.append("")
            for finding in grouped:
                lines.append(f"- **{finding.check}** ({finding.instrument}): "
                             f"{finding.limits}")
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("## 5. Objections on record")
        lines.append("")
        if claim.objections:
            lines.append("| objection | source | status | what would decide it |")
            lines.append("|:---|:---|:---|:---|")
            for objection in claim.objections:
                lines.append(
                    f"| {objection.summary} | {objection.source} | "
                    f"`{objection.status.value}` | {objection.decisive_question} |"
                )
        else:
            lines.append("None recorded.")
        lines.append("")

        lines.append("## 6. What would change this report")
        lines.append("")
        for item in _falsifiers(claim, self):
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## 7. Reproduction")
        lines.append("")
        for target in claim.formal:
            lines.append(f"**{target.role}** (`{target.root}`)"
                         + (f", recorded {target.recorded_on}" if target.recorded_on else "")
                         + (f". {target.note}" if target.note else ""))
            lines.append("")
            for command in target.commands:
                lines.append(f"    {command}")
            lines.append("")
        lines.append(
            "The audit itself, from the repository root: "
            "`python scripts/audit_claim.py --claim claims/"
            f"{claim.id}.json`"
        )
        lines.append("")

        lines.append("## 8. Standing position")
        lines.append("")
        lines.append(self.position)
        lines.append("")
        lines.append("**Evidence classes.** " + self.evidence_reasons)
        lines.append("")
        text = "\n".join(lines)
        _assert_no_proof_claim(text)
        return text


def _falsifiers(claim: Claim, report: ClaimReport) -> list[str]:
    """The fail conditions of *this* report, stated before anyone reads the verdicts.

    A record that cannot say what would make it wrong is the thing this repository keeps
    finding in its own history. The list is generated from the finding statuses, so a
    report cannot claim a check passed and then omit the condition under which it would
    stop passing.
    """
    items: list[str] = []
    if claim.document is not None:
        items.append(
            "A single changed byte in `" + claim.document.path + "` breaks the E0 "
            "hash, and the record would then be quoting a document nobody can find."
        )
    formal_ok = any(
        finding.level is Level.FORMAL and finding.status is Status.CHECKED_OK
        for finding in report.findings
    )
    if claim.formal and formal_ok:
        items.append(
            "A `sorry` or a non-standard axiom appearing in the artefact turns the "
            "term verdict into a failed check on the next run; `#print axioms` is the "
            "line that would show it."
        )
    if any(finding.level is Level.FORMAL and finding.status is Status.CHECKED_FAILED
           for finding in report.findings):
        items.append(
            "This is the report as it stands: at least one formal check failed, and "
            "the failure is the finding. Repairing the artefact would change it."
        )
    items.append(
        "A dependency trace showing that the conclusion's proof term avoids every "
        "located definitional escape hatch would move the fifth question off "
        "`undetermined`. Nothing in this repository can produce that trace today."
    )
    items.append(
        "Peer review of the claim, or its withdrawal, is an institutional event: it "
        "would be recorded here with a source and a date, and it would not change a "
        "single kernel result."
    )
    return items


def _assert_no_proof_claim(text: str) -> None:
    """Fail if the agent's own voice asserts a proof or a disproof.

    Quoted lines (starting with `>`) are exempt: a report must be able to quote the
    claim it audits. Everything else is checked, which is what makes the guard mean
    something rather than firing on the first quotation.
    """
    owned = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(">")
    )
    flattened = re.sub(r"\s+", "", owned).lower()
    hits = [phrase for phrase in FORBIDDEN_ASSERTIONS if phrase in flattened]
    if hits:
        raise ValueError(
            "the report asserts a proof claim in its own voice: " + ", ".join(hits)
        )


# ============================================================
# The agent
# ============================================================

def audit_claim(
    claim: Claim,
    repo_root: Path,
    *,
    live_lean: bool = True,
    lean_root: Path | None = None,
    timeout: int = 1800,
    role: str | None = None,
) -> ClaimReport:
    """Audit one claim: run the probes, ask the five questions, collect the record.

    `live_lean=False` replays the formal record instead of compiling, which is what a
    reviewer on a machine without the artefact gets and what CI does for archives that
    cannot be downloaded in a test. The report says which mode produced it.

    `lean_root` redirects the formal targets that are *absent* from this machine, for an
    archive kept somewhere other than the path the record names. A target that is present
    is never redirected: pointing this repository's own live checks at somebody else's tree
    would report that tree's failure as this one's. The redirect moves where the agent
    looks, not what it claims.

    `role` restricts the formal levels to one target. A record can carry an artefact and a
    live negative control, and the first live run of the adjudicator pooled them: the
    control's two deliberate `sorry`s failed the kernel probe, which failed the review, and
    the claim came back `rejected` on the strength of a fixture. A panel is about one
    artefact; this parameter is how a caller says which.
    """
    unknown = [key for key in claim.probes if key not in PROBES]
    if unknown:
        raise ValueError(
            f"{claim.id}: unknown probes {unknown}; known probes are {sorted(PROBES)}"
        )
    findings: list[Finding] = [PROBES[key].run(claim) for key in claim.probes]
    targets = claim.formal
    if role is not None:
        selected = tuple(target for target in targets if target.role == role)
        if not selected:
            raise ValueError(
                f"{claim.id}: no formal target with role {role!r}; "
                f"roles are {[target.role for target in claim.formal]}"
            )
        targets = selected
    if lean_root is not None:
        # Only the artefacts that are *not here* are moved. Redirecting a target that is
        # present would point this repository's own live checks at somebody else's tree
        # and report the failure as that tree's.
        targets = tuple(
            FormalTarget(
                role=target.role,
                root=str(lean_root) if not target.present(repo_root) else target.root,
                module=target.module,
                statements=target.statements, axiom_targets=target.axiom_targets,
                recorded=target.recorded, recorded_on=target.recorded_on,
                commands=target.commands, note=target.note, imports=target.imports,
                trace=target.trace,
            )
            for target in targets
        )
    target_verdicts: list[tuple[str, Verdict]] = []
    for target in targets:
        owned: list[Finding] = _formal_findings(
            formal_check(target, repo_root, live=live_lean, timeout=timeout)
        )
        for request in target.trace:
            owned.append(
                trace_finding(target, request, repo_root, live=live_lean, timeout=timeout)
            )
        findings.extend(owned)
        kernel_ok = any(
            finding.instrument_class is Instrument.KERNEL
            and finding.verdict is Verdict.VALIDATED_TERM
            for finding in owned
        )
        trace_statuses = [
            finding.status for finding in owned
            if finding.instrument_class is Instrument.DEPENDENCY_TRACE
        ]
        target_verdicts.append((target.role, target_verdict(kernel_ok, trace_statuses)))
    if not targets:
        findings.extend(_no_formalisation_findings(claim))
    findings.extend(_institutional_findings(claim, repo_root))
    evidence, reasons = evidence_classes(claim, findings)
    return ClaimReport(
        claim=claim,
        findings=tuple(findings),
        evidence=evidence,
        evidence_reasons=reasons,
        targets=tuple(target_verdicts),
        panel=panel_verdict(findings, [verdict for _, verdict in target_verdicts]),
    )


def load_claims(directory: Path) -> list[Claim]:
    """Every `*.json` record in `directory`, in a stable order.

    Sorted by name so two runs of `--all` produce byte-identical reports; a directory
    scan that depended on the filesystem's order would make the reports diff noisily and
    the reproduction section wrong.
    """
    return [Claim.from_json(path) for path in sorted(directory.glob("*.json"))]
