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
"""End to end: the audit agent on its first real claim, with Lean running.

The claim is the 2026 Alpöge release and Nielsen's objection to it. What this file checks
is *the agent*, not the claim: that the archived document still hashes to its record, that
the absent 61 GB archive is replayed and labelled as a replay, and that the live half of
the record behaves exactly as the record says it does.

The live half is `lean/RiemannFramework/Dispute.lean`, which is the repository's own
recording of the dispute: Alpöge's position stated with `sorry`, Nielsen's structural core
proved without one. Running the five questions on it is a **negative control with a known
answer**. The agent must find

* that it compiles,
* that it carries two `sorry`s, in `alpoge_position` and `nielsen_position`,
* that its axiom list contains `sorryAx` and is therefore not justified,
* that its statement is kernel-equal to Mathlib's `RiemannHypothesis`,
* and that non-vacuity is not decided by anything here.

An agent that reported anything else would be wrong about a file whose contents are known,
which is the only way to calibrate a checker before pointing it at a file nobody has read.

Nothing here is evidence for or against the Riemann hypothesis. The published archive's
numbers are a replay of `docs/verification_report.md`; the live numbers are about this
repository's own 200-line file.
"""

from __future__ import annotations

import json
import shutil
import uuid
import subprocess
import sys
from pathlib import Path

import pytest

from riemann_framework.claim_audit import (
    STANDING_POSITION,
    Claim,
    ClaimReport,
    LeanQuestion,
    Status,
    Verdict,
    audit_claim,
    lean_environment,
    normalise_statement,
    run_lean,
    split_sections,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ALPOGE = REPO_ROOT / "claims" / "alpoge_2026.json"
CLAIM_SCRIPT = REPO_ROOT / "scripts" / "audit_claim.py"

PUBLISHED = "the published archive"

#: Lean is optional here for the same reason it is optional in `test_formal_proof.py`: CI
#: runs the Python suite on an image with no toolchain, and a live audit on such a machine
#: would report a failed compile for a file nobody asked it to compile. The marker consults
#: the same `PATH` that `run_lean` will use, so the skip and the run cannot disagree about
#: whether Lean is there.
def lake_available() -> bool:
    return shutil.which("lake", path=lean_environment()["PATH"]) is not None


requires_lean = pytest.mark.skipif(
    not lake_available(), reason="Lean toolchain (lake) not available"
)

CALIBRATION = "this repository's recording"


@pytest.fixture(scope="module")
def report() -> ClaimReport:
    """One live audit, shared by the assertions below: compiling Mathlib is not cheap."""
    return audit_claim(Claim.from_json(ALPOGE), REPO_ROOT, live_lean=True, timeout=1800)


@pytest.fixture(scope="module")
def offline_report() -> ClaimReport:
    """The same record with every formal check replayed: no Lean, no compile.

    Used for the assertions about what the report says when a computation has *not* been
    run, which is the state of the published archive's trace on every machine that does
    not hold it.
    """
    return audit_claim(Claim.from_json(ALPOGE), REPO_ROOT, live_lean=False)


def formal(report: ClaimReport, role: str, question: LeanQuestion):
    matches = [
        finding for finding in report.findings
        if finding.level.value == "formal"
        and finding.check.startswith(role)
        and finding.check.endswith(question.value)
    ]
    assert len(matches) == 1, [finding.check for finding in report.findings]
    return matches[0]


# ============================================================
# The record
# ============================================================

@pytest.fixture()
def scratch() -> Path:
    """A throwaway directory inside the repository.

    	mp_path is not used here: the suite runs under a file sandbox whose temporary
    area is not listable, and a fixture that cannot create its directory fails the test
    for a reason that has nothing to do with the code. out/ is git-ignored, so a
    directory here is as disposable as one outside the tree and is visible while the
    test is failing, which the temporary one is not.
    """
    path = REPO_ROOT / "out" / "claims" / "_test_scratch" / uuid.uuid4().hex
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)



def test_the_archived_document_still_hashes_to_the_record() -> None:
    claim = Claim.from_json(ALPOGE)
    assert claim.document is not None
    matches, evidence = claim.document.verify(REPO_ROOT)
    assert matches, evidence
    assert claim.document.pages == 4


@requires_lean
def test_the_published_archive_is_replayed_and_says_so(report: ClaimReport) -> None:
    """No artefact on this machine means no live claim about the artefact."""
    for question in (
        LeanQuestion.COMPILES, LeanQuestion.NO_SORRY,
        LeanQuestion.AXIOMS_JUSTIFIED, LeanQuestion.STATEMENT_MATCHES,
    ):
        finding = formal(report, PUBLISHED, question)
        assert finding.status is Status.CHECKED_OK
        assert "audit record of 2026-11-22" in finding.instrument
        assert "this machine, live" not in finding.instrument


@requires_lean
def test_the_published_term_reaches_the_term_verdict(report: ClaimReport) -> None:
    """Four replayed checks that all hold: the paper's `validated (term)`, no higher."""
    finding = formal(report, PUBLISHED, LeanQuestion.STATEMENT_MATCHES)
    assert finding.verdict is Verdict.VALIDATED_TERM


# ============================================================
# The live negative control
# ============================================================

@requires_lean
def test_the_live_calibration_compiles(report: ClaimReport) -> None:
    finding = formal(report, CALIBRATION, LeanQuestion.COMPILES)
    assert finding.status is Status.CHECKED_OK, finding.evidence
    assert "this machine, live" in finding.instrument
    assert "exit 0" in finding.evidence


@requires_lean
def test_the_live_calibration_reports_its_two_deliberate_sorries(
    report: ClaimReport,
) -> None:
    """The file records two positions with `sorry`; the agent must find both."""
    finding = formal(report, CALIBRATION, LeanQuestion.NO_SORRY)
    assert finding.status is Status.CHECKED_FAILED, finding.evidence
    assert "2 `sorry`/`admit`" in finding.evidence
    assert "alpoge_position" in finding.evidence
    assert "nielsen_position" in finding.evidence


@requires_lean
def test_the_live_calibration_reports_the_hole_in_its_axiom_list(
    report: ClaimReport,
) -> None:
    finding = formal(report, CALIBRATION, LeanQuestion.AXIOMS_JUSTIFIED)
    assert finding.status is Status.CHECKED_FAILED, finding.evidence
    assert "alpoge_position" in finding.evidence
    assert "sorryAx" in finding.evidence
    assert "hole" in finding.evidence


@requires_lean
def test_the_live_statement_is_kernel_equal_to_mathlib_s(report: ClaimReport) -> None:
    """`rfl` closes `statement = RiemannHypothesis`, which is defeq and not text."""
    finding = formal(report, CALIBRATION, LeanQuestion.STATEMENT_MATCHES)
    assert finding.status is Status.CHECKED_OK, finding.evidence
    assert "rfl" in finding.evidence
    assert "definitionally equal" in finding.evidence
    assert "kernel-checked" in finding.evidence


@requires_lean
def test_a_file_with_a_hole_does_not_get_the_term_verdict(report: ClaimReport) -> None:
    """The verdict is not awarded by the statement check alone."""
    finding = formal(report, CALIBRATION, LeanQuestion.STATEMENT_MATCHES)
    assert finding.verdict is Verdict.UNDETERMINED, finding.verdict


@requires_lean
def test_the_live_census_locates_the_vacuous_predicate(report: ClaimReport) -> None:
    finding = formal(report, CALIBRATION, LeanQuestion.DEFINITIONS_NON_VACUOUS)
    assert finding.status is Status.UNDETERMINED
    assert "vacuousGeometry" in finding.evidence


@requires_lean
def test_the_fifth_question_is_undetermined_for_both_targets(
    report: ClaimReport,
) -> None:
    for role in (PUBLISHED, CALIBRATION):
        finding = formal(report, role, LeanQuestion.DEFINITIONS_NON_VACUOUS)
        assert finding.status is Status.UNDETERMINED, finding.as_dict()
        assert finding.verdict is Verdict.UNDETERMINED


# ============================================================
# The comparator's discriminating power
# ============================================================

@requires_lean
def test_the_comparator_rejects_a_statement_that_is_not_riemann_hypothesis() -> None:
    """A negative control for the statement check, run against a real Lean printer.

    `vacuousGeometry` is a proposition in the same file as the statement under test. Its
    printed body is `True`. If the normalising comparison called that a match, the agent
    would certify any proposition that happens to live next to the right one.
    """
    source = "\n".join(
        [
            "import Mathlib",
            "import RiemannFramework.Dispute",
            "",
            '#eval IO.println "===body:vacuous==="',
            "#print RiemannFramework.vacuousGeometry",
            '#eval IO.println "===end==="',
            "",
        ]
    )
    run = run_lean(REPO_ROOT, source, name="lookalike_control", timeout=1800)
    assert run.ok, run.output[-2000:]
    body = split_sections(run.output)["body:vacuous"].split(":=", 1)[-1]
    assert "True" in body
    assert normalise_statement(body) != normalise_statement("RiemannHypothesis")


# ============================================================
# The report and the command
# ============================================================

@requires_lean
def test_the_report_names_the_objections_and_keeps_the_hypothesis_open(
    report: ClaimReport,
) -> None:
    markdown = report.render_markdown()
    assert STANDING_POSITION in markdown
    assert "Nielsen" in markdown
    assert "anyGeometry" in markdown
    assert "undetermined" in markdown
    assert "validated (term)" in markdown


def test_the_command_writes_both_reports(scratch: Path) -> None:
    result = subprocess.run(
        [
            sys.executable, str(CLAIM_SCRIPT),
            "--claim", str(ALPOGE),
            "--no-lean",
            "--quiet",
            "--out", str(scratch),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    markdown = (scratch / "alpoge_2026.md").read_text(encoding="utf-8")
    payload = json.loads((scratch / "alpoge_2026.json").read_text(encoding="utf-8"))
    assert STANDING_POSITION in markdown
    assert payload["claim"]["id"] == "alpoge_2026"
    assert payload["evidence_classes"] == "E0, E1, E4"


# ============================================================
# The decisive computation: the dependency trace, with both controls
# ============================================================

def trace_findings(report: ClaimReport) -> list:
    return [
        finding for finding in report.findings
        if "dependency trace" in finding.check
    ]


@requires_lean
def test_the_trace_positive_control_reaches_the_vacuous_definition(
    report: ClaimReport,
) -> None:
    """`geometry_is_vacuous` states the vacuity, so its closure must contain it.

    A trace that reported "clean" here would be broken, and the whole instrument would be
    worthless on the archive nobody can check. This is the calibration.
    """
    finding = next(
        item for item in trace_findings(report)
        if "geometry_is_vacuous" in item.check
    )
    assert finding.status is Status.CHECKED_FAILED, finding.evidence
    assert finding.verdict is Verdict.UNDETERMINED
    assert "vacuousGeometry" in finding.evidence
    assert "reaches 1 flagged" in finding.evidence


@requires_lean
def test_the_trace_negative_control_avoids_it(report: ClaimReport) -> None:
    """A theorem that does not mention the vacuous predicate must come back clean."""
    finding = next(
        item for item in trace_findings(report)
        if "closed_false_impossible" in item.check
    )
    assert finding.status is Status.CHECKED_OK, finding.evidence
    assert finding.verdict is Verdict.VALIDATED_TERM
    assert "reaches none" in finding.evidence


@requires_lean
def test_the_trace_reports_the_size_of_what_it_measured(report: ClaimReport) -> None:
    """`not reached` is only meaningful next to the size of what was searched."""
    for finding in trace_findings(report):
        if finding.status is Status.CHECKED_OK:
            assert "closure" in finding.evidence


def test_the_published_trace_is_pending_and_carries_its_command(
    offline_report: ClaimReport,
) -> None:
    """The reviewer's third point: the decisive computation is named, not performed."""
    finding = next(
        item for item in trace_findings(offline_report)
        if "riemannHypothesis" in item.check
    )
    assert finding.status is Status.NOT_RUN
    assert finding.verdict is Verdict.NOT_ASSESSED
    assert "#deps riemannHypothesis" in finding.evidence
    assert "anyGeometry" in finding.evidence or "pending" in finding.evidence


def test_the_panel_verdict_is_undetermined_not_validated(offline_report: ClaimReport) -> None:
    """A term verdict and a panel verdict are different objects.

    The published statement row is `validated (term)`; the panel is `undetermined`,
    because the trace that would make the term verdict a panel verdict has not run and
    the vacuity objection is therefore still live. Collapsing the two would be the
    overclaim the review names.
    """
    assert offline_report.panel is Verdict.UNDETERMINED, offline_report.panel
    term_rows = [
        finding for finding in offline_report.findings
        if finding.verdict is Verdict.VALIDATED_TERM
    ]
    assert term_rows, "the replayed kernel evidence should still earn the term verdict"
    assert all("dependency trace" not in row.check for row in term_rows)


def test_the_report_states_why_the_panel_is_weaker_than_the_term(
    offline_report: ClaimReport,
) -> None:
    markdown = offline_report.render_markdown()
    assert "Panel verdict" in markdown
    assert "undetermined" in markdown
    assert "without a trace is `undetermined` by construction" in markdown


def test_the_circularity_screen_reports_an_unscreened_claim(
    offline_report: ClaimReport,
) -> None:
    """The release states no prose inputs, so the dual screen cannot read it either."""
    finding = next(
        item for item in offline_report.findings
        if "equivalent to the Riemann hypothesis" in item.check
    )
    assert finding.status is Status.NOT_APPLICABLE
    assert "unscreened" in finding.evidence


def test_the_command_is_strict_when_asked(scratch: Path) -> None:
    """`--strict` turns a failed check into a non-zero exit, for CI.

    Driven with a record whose document hash is wrong, because that is a checked failure
    the offline path can produce: the default run documents it and exits 0, and the
    strict run makes it red.
    """
    record = json.loads(ALPOGE.read_text(encoding="utf-8"))
    record["document"]["sha256"] = "0" * 64
    corrupted = scratch / "corrupted.json"
    corrupted.write_text(json.dumps(record), encoding="utf-8")

    common = [
        sys.executable, str(CLAIM_SCRIPT),
        "--claim", str(corrupted), "--no-lean", "--quiet",
        "--out", str(scratch / "reports"),
    ]
    lenient = subprocess.run(common, cwd=REPO_ROOT, capture_output=True, text=True,
                             timeout=600)
    assert lenient.returncode == 0, lenient.stderr[-2000:]

    strict = subprocess.run(
        [*common, "--strict"], cwd=REPO_ROOT, capture_output=True, text=True,
        timeout=600,
    )
    assert strict.returncode == 1
    assert "1 failed" in strict.stderr
