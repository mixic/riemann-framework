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
"""Guards the claim-audit agent: its vocabulary, its instruments, and its refusals.

The failure modes this file is aimed at are the ones this repository has actually had,
all of them in documents rather than in theorems:

* a report that reads like a verdict. The six-verdict vocabulary is compared against the
  paper's own text, the standing sentence is required in every render, and a finding
  written in the agent's own voice that asserts a proof makes the render fail;
* a check that ran on nothing and reported success. `not_run`, `not_applicable` and
  `undetermined` are distinct statuses here, and the tests pin the distinctions: a
  census over an absent source may not report "nothing found", and E3 may not be claimed
  off a replayed compile;
* a probe that says it used an instrument. Every `Probe` names a module of this package,
  the probe's own source must mention that module, and its output is compared against a
  direct call of the module, so "the repository was the instrument" is checkable rather
  than asserted.

The live Lean half of the agent is exercised in `test_alpoge_claim.py`, which compiles;
this file stays fast enough to run on every edit.
"""

from __future__ import annotations

import importlib
import inspect
import json
import shutil
import uuid
from pathlib import Path

import pytest

from riemann_framework import claim_audit, dh_filter, proportion_certificates, zeros
from riemann_framework.claim_audit import (
    FORBIDDEN_ASSERTIONS,
    LEAN_QUESTIONS,
    PROBES,
    STANDING_POSITION,
    Claim,
    ClaimReport,
    Document,
    Finding,
    FormalTarget,
    LeanQuestion,
    Level,
    Status,
    Verdict,
    audit_claim,
    normalise_statement,
    parse_axioms,
    sorry_census,
    split_sections,
    strip_lean_comments,
    vacuity_census,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = REPO_ROOT / "claims"
ALPOGE = CLAIMS_DIR / "alpoge_2026.json"
PAPER_TEX = REPO_ROOT / "paper" / "evaluation_protocol.tex"
DISPUTE = REPO_ROOT / "lean" / "RiemannFramework" / "Dispute.lean"


def make_claim(**overrides) -> Claim:
    """A minimal claim record, with nothing in it that a probe could trip over."""
    base = {
        "id": "probe_claim",
        "title": "A claim, for testing the agent",
        "claimant": "nobody",
        "date": "2026-11-22",
        "statement": "a statement",
        "statement_location": "nowhere in particular",
        "declared_inputs": (),
        "probes": (),
    }
    base.update(overrides)
    return Claim(**base)


@pytest.fixture(scope="module")
def alpoge_claim() -> Claim:
    return Claim.from_json(ALPOGE)


@pytest.fixture(scope="module")
def offline_report(alpoge_claim: Claim) -> ClaimReport:
    """The Alpöge record with every formal check replayed, no Lean compiled."""
    return audit_claim(alpoge_claim, REPO_ROOT, live_lean=False)


# ============================================================
# The vocabulary
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



def test_the_verdict_vocabulary_is_the_papers_vocabulary() -> None:
    """Six verdicts, character for character, and no seventh meaning "true"."""
    tex = PAPER_TEX.read_text(encoding="utf-8")
    for verdict in Verdict:
        if verdict is Verdict.NOT_ASSESSED:
            continue
        assert verdict.value in tex, (
            f"the agent's verdict {verdict.value!r} does not appear in the paper, so "
            "the two vocabularies have drifted apart"
        )


def test_no_verdict_word_means_true() -> None:
    for verdict in Verdict:
        assert verdict.value not in ("true", "proved", "correct", "confirmed")
    assert Verdict.NOT_ASSESSED.value == "not assessed"


def test_every_finding_carries_a_stated_limit(offline_report: ClaimReport) -> None:
    """A finding without a limit is the failure mode the paper is written against."""
    for finding in offline_report.findings:
        assert finding.limits.strip(), finding.as_dict()
        assert finding.instrument.strip(), finding.as_dict()
        assert finding.evidence.strip(), finding.as_dict()


def test_every_report_carries_the_standing_position(
    offline_report: ClaimReport,
) -> None:
    markdown = offline_report.render_markdown()
    assert STANDING_POSITION in markdown
    assert "RH is open" in markdown


def test_no_report_asserts_a_proof_or_a_disproof(offline_report: ClaimReport) -> None:
    """The guard is the assertion: `render_markdown` raises rather than returns."""
    markdown = offline_report.render_markdown()
    claim_audit._assert_no_proof_claim(markdown)
    owned = "\n".join(
        line for line in markdown.splitlines() if not line.lstrip().startswith(">")
    ).replace(" ", "").lower()
    for phrase in FORBIDDEN_ASSERTIONS:
        assert phrase not in owned


def test_the_guard_fires_on_the_agents_own_voice() -> None:
    """Driven into failing, so a passing render above means something."""
    finding = Finding(
        level=Level.NUMERICAL,
        check="a check",
        status=Status.CHECKED_OK,
        verdict=Verdict.VALIDATED_FINITE,
        instrument="an instrument",
        evidence="this proves the Riemann hypothesis",
        limits="none",
    )
    report = ClaimReport(
        claim=make_claim(), findings=(finding,), evidence="E1",
        evidence_reasons="E1: quoted",
    )
    with pytest.raises(ValueError, match="proof claim"):
        report.render_markdown()


def test_a_quotation_may_say_what_the_claimant_said() -> None:
    """The exemption that makes the guard usable: a report must be able to quote."""
    claim = make_claim(
        statement="the author states that this proves the Riemann hypothesis"
    )
    report = ClaimReport(
        claim=claim, findings=(), evidence="E1", evidence_reasons="E1: quoted"
    )
    markdown = report.render_markdown()
    assert "proves the Riemann hypothesis" in markdown


# ============================================================
# The instruments
# ============================================================

def test_every_probe_names_a_real_module_of_this_package() -> None:
    for key, probe in PROBES.items():
        module = importlib.import_module(f"riemann_framework.{probe.instrument}")
        assert module is not None, key
        assert probe.decides, key


def test_every_probe_actually_calls_the_module_it_names() -> None:
    """Not "the probe says it used the instrument": its source has to show it.

    This is the check that keeps the phrase "the repository was the instrument" honest.
    A probe rewritten to compute in place would fail here rather than silently turning
    the audit into its own authority.
    """
    for key, probe in PROBES.items():
        source = inspect.getsource(probe.run)
        assert f"import {probe.instrument}" in source or f". {probe.instrument}" in source, (
            f"{key} claims the instrument {probe.instrument!r} but never imports it"
        )


def test_every_probe_function_is_registered() -> None:
    defined = {
        name for name, value in vars(claim_audit).items()
        if name.startswith("probe_") and callable(value)
    }
    registered = {probe.run.__name__ for probe in PROBES.values()}
    assert defined == registered


def test_the_zero_probe_reports_what_the_module_reports() -> None:
    finding = claim_audit.probe_zero_consistency(make_claim())
    rows = zeros.verify_first_n_zeros(3)
    for row in rows:
        assert f"{float(row['im']):.6f}" in finding.evidence
    assert finding.status is Status.CHECKED_OK
    assert finding.verdict is Verdict.VALIDATED_FINITE


def test_the_proportion_probe_reports_what_the_module_reports() -> None:
    finding = claim_audit.probe_proportion_constants(make_claim())
    constants = proportion_certificates.montgomery_taylor_constants()
    assert f"{constants['simple_montgomery_taylor']:.10f}" in finding.evidence
    assert f"{constants['distinct_montgomery_taylor']:.10f}" in finding.evidence
    assert finding.status is Status.CHECKED_OK


def test_the_dh_probe_maps_every_filter_verdict() -> None:
    """`dead` is the one verdict the contrapositive supports; the other two are not."""
    fails = [
        key for key, row in dh_filter.DH_INPUTS.items()
        if row.status is dh_filter.InputStatus.FAILS
    ]
    transfers = [
        key for key, row in dh_filter.DH_INPUTS.items()
        if row.status is dh_filter.InputStatus.TRANSFERS
    ]
    assert fails and transfers, "the inventory has lost one of its two halves"

    eligible = claim_audit.probe_dh_screen(make_claim(declared_inputs=(fails[0],)))
    assert eligible.status is Status.CHECKED_OK
    assert eligible.verdict is Verdict.UNDETERMINED
    assert "eligible" in eligible.evidence

    dead = claim_audit.probe_dh_screen(make_claim(declared_inputs=tuple(transfers)))
    assert dead.status is Status.CHECKED_FAILED
    assert dead.verdict is Verdict.REJECTED
    assert "dead" in dead.evidence


def test_the_dh_probe_cannot_screen_an_undeclared_claim() -> None:
    """An empty declaration is unscreened, not dead, and the probe says so."""
    finding = claim_audit.probe_dh_screen(make_claim(declared_inputs=()))
    assert "needs_sourcing" in finding.evidence
    assert finding.verdict is Verdict.UNDETERMINED


def test_the_numerical_domain_probe_asks_the_inventory(
    offline_report: ClaimReport,
) -> None:
    domain = [
        finding for finding in offline_report.findings
        if "instrument's domain" in finding.check
    ]
    assert len(domain) == 1
    assert domain[0].verdict is Verdict.OUTSIDE_DOMAIN
    for row in dh_filter.inventory_table():
        assert row["key"] in domain[0].evidence


# ============================================================
# Refusals: the statuses that are not successes
# ============================================================

def test_a_changed_document_fails_the_e0_check(scratch: Path) -> None:
    path = scratch / "document.txt"
    path.write_text("the bytes that were archived", encoding="utf-8")
    document = Document(
        path=str(path), sha256="0" * 64, bytes=path.stat().st_size, pages=1,
        url="", retrieved="2026-11-22",
    )
    report = audit_claim(make_claim(document=document), REPO_ROOT, live_lean=False)
    e0 = next(f for f in report.findings if f.check.startswith("E0"))
    assert e0.status is Status.CHECKED_FAILED
    assert "hashes to" in e0.evidence


def test_an_unchanged_document_passes_the_e0_check(scratch: Path) -> None:
    import hashlib

    path = scratch / "document.txt"
    path.write_text("the bytes that were archived", encoding="utf-8")
    data = path.read_bytes()
    document = Document(
        path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
        pages=1, url="", retrieved="2026-11-22",
    )
    report = audit_claim(make_claim(document=document), REPO_ROOT, live_lean=False)
    e0 = next(f for f in report.findings if f.check.startswith("E0"))
    assert e0.status is Status.CHECKED_OK


def test_an_absent_artefact_is_not_run_and_not_undetermined() -> None:
    """`undetermined` would say something was asked; nothing was."""
    report = audit_claim(
        make_claim(
            formal=(
                FormalTarget(
                    role="an artefact that is not here",
                    root="external/definitely-not-here",
                    module="Nothing.Here",
                    statements=(),
                    axiom_targets=(),
                    recorded={},
                    recorded_on="",
                    commands=(),
                ),
            )
        ),
        REPO_ROOT,
        live_lean=True,
    )
    formal = [f for f in report.findings if f.level is Level.FORMAL]
    assert formal
    for finding in formal:
        if finding.check.endswith(LeanQuestion.DEFINITIONS_NON_VACUOUS.value):
            # The fifth question is undetermined whether or not the artefact is here:
            # nothing in this repository decides it, so absence cannot change it.
            assert finding.status is Status.UNDETERMINED, finding.as_dict()
            assert "nothing was scanned" in finding.evidence
            continue
        assert finding.status is Status.NOT_RUN, finding.as_dict()
        assert "not run" in finding.instrument


def test_a_claim_without_a_formalisation_still_prints_the_five_questions() -> None:
    report = audit_claim(make_claim(), REPO_ROOT, live_lean=False)
    formal = [f for f in report.findings if f.level is Level.FORMAL]
    assert len(formal) == len(LEAN_QUESTIONS)
    for finding in formal:
        assert finding.status is Status.NOT_APPLICABLE
        assert "no formal artefact supplied" in finding.check


def test_the_fifth_question_is_never_decided(offline_report: ClaimReport) -> None:
    """The one check that must not have a passing branch."""
    fifth = [
        finding for finding in offline_report.findings
        if finding.check.endswith(LeanQuestion.DEFINITIONS_NON_VACUOUS.value)
    ]
    assert fifth
    for finding in fifth:
        assert finding.status is Status.UNDETERMINED
        assert finding.verdict is Verdict.UNDETERMINED


def test_a_replayed_compile_does_not_reach_e3(alpoge_claim: Claim) -> None:
    """E3 is "compiles here". A record of a run elsewhere is a different class."""
    report = audit_claim(alpoge_claim, REPO_ROOT, live_lean=False)
    assert "E3" not in report.evidence, report.evidence


def test_evidence_classes_are_a_set_and_not_a_score(scratch: Path) -> None:
    import hashlib

    path = scratch / "document.txt"
    path.write_text("bytes", encoding="utf-8")
    data = path.read_bytes()
    claim = make_claim(
        document=Document(
            path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
            pages=1, url="", retrieved="2026-11-22",
        ),
        declared_inputs=(),
    )
    report = audit_claim(claim, REPO_ROOT, live_lean=False)
    assert report.evidence == "E0, E1", report.evidence
    assert "E2" not in report.evidence and "E4" not in report.evidence


# ============================================================
# The parsers
# ============================================================

def test_sorry_census_ignores_prose_and_names_the_declarations() -> None:
    source = (
        "/-- This theorem is `sorry`-free; the word appears here only. -/\n"
        "-- sorry in a line comment\n"
        "theorem clean : True := trivial\n"
        "theorem hole : True := by sorry\n"
        "theorem other : True := by sorry\n"
    )
    counts = sorry_census(source)
    assert counts["sorry"] == 2
    assert counts["declarations"] == ["hole", "other"]


def test_sorry_census_counts_admit_too() -> None:
    assert sorry_census("example : True := by admit")["admit"] == 1


def test_strip_lean_comments_handles_nesting() -> None:
    source = "/- outer /- inner -/ still a comment -/ theorem t : True := trivial"
    assert "comment" not in strip_lean_comments(source)
    assert "theorem t" in strip_lean_comments(source)


def test_vacuity_census_finds_the_alpoge_nielsen_shapes() -> None:
    source = (
        "def anyGeometry (_D _J _X : Nat) : Prop := fun _ _ _ => True\n"
        "def Statement : Prop := RiemannHypothesis\n"
        "structure Height where\n  value : Nat\n"
        "def h_eq : Height.value = Height.value := rfl\n"
    )
    census = vacuity_census(source)
    assert "anyGeometry" in census["true_bodied_definitions"]
    assert census["true_lambdas"] >= 1
    assert any("RiemannHypothesis" in alias for alias in census["proposition_aliases"])
    assert census["rfl_defined_values"] >= 1


def test_vacuity_census_on_the_repository_s_own_dispute_file() -> None:
    """The locator finds the shape in the file that encodes the objection."""
    census = vacuity_census(DISPUTE.read_text(encoding="utf-8"))
    assert "vacuousGeometry" in census["true_bodied_definitions"]
    assert any(
        "RiemannHypothesisStatement" in alias
        for alias in census["proposition_aliases"]
    )


def test_vacuity_census_finds_nothing_in_a_clean_definition() -> None:
    census = vacuity_census("def two : Nat := 2\ntheorem t : two = 2 := rfl\n")
    assert census["true_bodied_definitions"] == []
    assert census["true_lambdas"] == 0


def test_the_axiom_parser_reads_both_shapes_lean_prints() -> None:
    output = (
        "'RiemannFramework.closed_of_vacuous' does not depend on any axioms\n"
        "'RiemannFramework.alpoge_position' depends on axioms: [propext, sorryAx, "
        "Classical.choice, Quot.sound]\n"
    )
    parsed = parse_axioms(output)
    assert parsed["RiemannFramework.closed_of_vacuous"] == []
    assert "sorryAx" in parsed["RiemannFramework.alpoge_position"]


def test_split_sections_uses_the_probe_markers() -> None:
    output = "noise\n===type:A===\nA : Prop\n===axioms:B===\n'B' does not depend on any axioms\n===end===\n"
    sections = split_sections(output)
    assert sections["type:A"] == "A : Prop"
    assert "does not depend" in sections["axioms:B"]


def test_normalise_statement_folds_layout_and_glyphs() -> None:
    printed = (
        "∀ (a : RiemannFramework.Archive),\n"
        "  a.routesThroughVacuous = true → ∀ (P : Prop), ¬RiemannFramework.Grounds a P"
    )
    rewritten = (
        "forall (a : RiemannFramework.Archive), a.routesThroughVacuous = true -> "
        "forall (P : Prop), not RiemannFramework.Grounds a P"
    )
    assert normalise_statement(printed) == normalise_statement(rewritten)
    assert normalise_statement("RiemannHypothesis") != normalise_statement(
        "forall (n : Nat), n = n"
    )


def test_axioms_are_justified_only_by_the_standard_three() -> None:
    ok, _ = claim_audit.axioms_justified(["propext", "Classical.choice", "Quot.sound"])
    assert ok
    ok, reason = claim_audit.axioms_justified(["propext", "sorryAx"])
    assert not ok and "hole" in reason
    ok, reason = claim_audit.axioms_justified(["propext", "mystery"])
    assert not ok and "mystery" in reason


# ============================================================
# The record and its report
# ============================================================

def test_the_alpoge_record_is_internally_consistent(alpoge_claim: Claim) -> None:
    assert alpoge_claim.document is not None
    matches, evidence = alpoge_claim.document.verify(REPO_ROOT)
    assert matches, evidence
    assert alpoge_claim.declared_inputs == ()
    assert len(alpoge_claim.formal) == 2
    assert {target.role for target in alpoge_claim.formal} == {
        "the published archive (absent from this machine by default)",
        "this repository's recording of the dispute (live)",
    }


def test_the_report_serialises_with_string_statuses(
    offline_report: ClaimReport,
) -> None:
    payload = offline_report.to_dict()
    text = json.dumps(payload, ensure_ascii=False)
    reloaded = json.loads(text)
    assert reloaded["position"] == STANDING_POSITION
    assert len(reloaded["findings"]) == len(offline_report.findings)
    for finding in reloaded["findings"]:
        assert finding["status"] in {status.value for status in Status}
        assert finding["verdict"] in {verdict.value for verdict in Verdict}


def test_table_cells_escape_pipes() -> None:
    finding = Finding(
        level=Level.FORMAL, check="a | check", status=Status.CHECKED_OK,
        verdict=Verdict.NOT_ASSESSED, instrument="x", evidence="Lean said a | b",
        limits="y",
    )
    row = finding.as_row()
    assert "\\|" in row
    assert row.count("|") - row.count("\\|") == 5


def test_unknown_probes_are_refused_before_anything_runs() -> None:
    with pytest.raises(ValueError, match="unknown probes"):
        audit_claim(make_claim(probes=("no_such_probe",)), REPO_ROOT, live_lean=False)


def test_the_loader_names_missing_and_unknown_keys(scratch: Path) -> None:
    missing = scratch / "missing.json"
    missing.write_text('{"id": "x"}', encoding="utf-8")
    with pytest.raises(ValueError, match="missing required keys"):
        Claim.from_json(missing)

    unknown = scratch / "unknown.json"
    record = json.loads(ALPOGE.read_text(encoding="utf-8"))
    record["declared_input"] = []
    unknown.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown keys"):
        Claim.from_json(unknown)


def test_the_reports_say_which_level_each_finding_belongs_to(
    offline_report: ClaimReport,
) -> None:
    grouped = offline_report.by_level
    assert set(grouped) == set(Level)
    assert grouped[Level.NUMERICAL] and grouped[Level.FORMAL]
    assert grouped[Level.INSTITUTIONAL]


def test_the_alpoge_report_reports_the_unscreened_filter(offline_report: ClaimReport) -> None:
    screen = next(
        finding for finding in offline_report.findings
        if "Davenport–Heilbronn" in finding.check
    )
    assert "needs_sourcing" in screen.evidence
    assert screen.verdict is Verdict.UNDETERMINED
