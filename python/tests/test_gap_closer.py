"""The gap closer: four computations, the refusal logic, the five colours, and the artefacts.

These tests do not run Lean. They establish the parts that can be decided mechanically: the
census scan, the per-declaration classification, the aggregation precedence and its refusals,
the self-audit conditions of the specification, the five-colour graph invariants, and the six
artefacts with their hashes. The Lean computations themselves are exercised by
`scripts/audit/rh_gap_closer.py --local-control`.
"""

from __future__ import annotations

import json
from pathlib import Path

from riemann_framework.adjudicator import Mutant, MutationOutcome
from riemann_framework.claim_audit import Verdict
from riemann_framework.gap_closer import (
    AMBER,
    BLUE,
    GREEN,
    RED,
    YELLOW,
    VOCABULARY,
    Computation,
    DeclarationRecord,
    aggregate,
    build_report,
    census_flags,
    classify,
    render_gap_statement,
    render_graph,
    self_audit,
    write_artefacts,
)

SOURCE = """
def vacuousGeometry (_D _J _X : Nat) : Prop := True
def honestDef (n : Nat) : Nat := n + 1
theorem geometry_is_vacuous : ∀ D J X : Nat, vacuousGeometry D J X := fun _ _ _ => trivial
"""


def mutant(identifier: str, declaration: str, theorem: str, *, replace: str = "False") -> Mutant:
    return Mutant(
        id=identifier,
        operator="CONTENT_FLIP",
        source="lean/X.lean",
        find=f"def {declaration} (_D _J _X : Nat) : Prop := True",
        replace=f"def {declaration} (_D _J _X : Nat) : Prop := {replace}",
        theorem=theorem,
    )


def outcome(identifier: str, declaration: str, theorem: str, *, ran: bool = True, survived: bool = False) -> MutationOutcome:
    return MutationOutcome(
        mutant=mutant(identifier, declaration, theorem),
        ran=ran,
        compiled=True,
        failed_declarations=(),
        survived=survived,
        unattributed=(),
        reason="" if ran else "the mutant did not run",
    )


def ran(name: str, names: tuple[str, ...] = ()) -> Computation:
    return Computation(name, "instrument", "checked_ok", "ran", {"names": set(names)})


def test_the_vocabulary_is_the_paper_six():
    assert tuple(item.value for item in VOCABULARY) == (
        "rejected",
        "outside domain",
        "undetermined",
        "validated (finite)",
        "validated (elementary)",
        "validated (term)",
    )


def test_the_census_finds_the_trivially_true_definitions_only():
    assert census_flags(SOURCE) == ("vacuousGeometry",)


def test_a_surviving_vacuous_rewrite_is_critical_and_red():
    records = classify({"X.vacuousGeometry"}, {"vacuousGeometry"}, [outcome("m", "vacuousGeometry", "t", survived=True)])
    assert records[0].vacuity_critical is True
    assert records[0].colour == RED


def test_a_killed_rewrite_is_not_critical_and_amber():
    records = classify({"X.vacuousGeometry"}, {"vacuousGeometry"}, [outcome("m", "vacuousGeometry", "t", survived=False)])
    assert records[0].vacuity_critical is False
    assert records[0].colour == AMBER


def test_a_flagged_declaration_outside_the_closure_is_blue():
    records = classify({"X.other"}, {"vacuousGeometry"}, [])
    assert records[0].in_closure is False
    assert records[0].colour == BLUE


def test_the_positive_verdict_needs_all_four_computations():
    verdict, named = aggregate(
        (ran("C1"), ran("C2"), ran("C3")),
        (),
        kernel=Verdict.VALIDATED_TERM,
    )
    assert verdict is Verdict.UNDETERMINED
    assert named and "C4" in named[0]


def test_a_clean_run_with_all_four_reaches_the_term_verdict():
    verdict, named = aggregate(
        (ran("C1"), ran("C2"), ran("C3"), ran("C4")),
        (),
        kernel=Verdict.VALIDATED_TERM,
    )
    assert verdict is Verdict.VALIDATED_TERM
    assert named == ()


def test_a_critical_declaration_blocks_the_term_verdict():
    records = (
        DeclarationRecord("vacuousGeometry", True, True, True, "m", "survived"),
    )
    verdict, named = aggregate(
        (ran("C1"), ran("C2"), ran("C3"), ran("C4")),
        records,
        kernel=Verdict.VALIDATED_TERM,
    )
    assert verdict is Verdict.UNDETERMINED
    assert any("vacuousGeometry" in item for item in named)


def test_a_closure_discrepancy_blocks_and_names_the_reconciliation():
    verdict, named = aggregate(
        (ran("C1"), ran("C2"), ran("C3", ("A",)), ran("C4")),
        (),
        kernel=Verdict.VALIDATED_TERM,
        discrepancy=True,
    )
    assert verdict is Verdict.UNDETERMINED
    assert "reconcile" in named[0]


def test_a_dh_rejection_dominates():
    verdict, _ = aggregate((ran("C1"),), (), kernel=Verdict.VALIDATED_TERM, dh_verdict=Verdict.REJECTED)
    assert verdict is Verdict.REJECTED


def test_self_audit_catches_a_yellow_node_inside_the_closure(tmp_path):
    report = build_report(
        claim="c",
        target="t",
        module="m",
        computations=(ran("C1"), ran("C2"), ran("C3"), ran("C4")),
        kernel=Verdict.VALIDATED_TERM,
        required=("vacuousGeometry",),
        closure={"X.vacuousGeometry"},
    )
    assert any(not check.ok for check in report.checks), report.checks
    assert report.verdict is Verdict.UNDETERMINED


def test_self_audit_refuses_a_gap_statement_that_asserts_proof():
    report = build_report(
        claim="c",
        target="t",
        module="m",
        computations=(ran("C1"), ran("C2"), ran("C3"), ran("C4")),
        kernel=Verdict.VALIDATED_TERM,
    )
    checks = self_audit(
        report,
        gap_text="the Riemann hypothesis is proved by this archive",
        closure=set(),
        yellow=(),
        trace_instrument="getUsedConstants",
    )
    assert any(not check.ok and "asserts no proof" in check.name for check in checks)


def test_a_not_run_report_names_the_computations_and_never_validates():
    not_run = tuple(
        Computation(name, "instrument", "not_run", "archive absent", named_computation=f"run {name}")
        for name in ("C1", "C2", "C3", "C4")
    )
    report = build_report(
        claim="alpoge_2026",
        target="riemannHypothesis",
        module="",
        computations=not_run,
        kernel=Verdict.VALIDATED_TERM,
    )
    assert report.verdict is Verdict.UNDETERMINED
    assert len(report.named_computations) == 4


def test_the_graph_uses_the_five_colours_and_marks_required_work():
    report = build_report(
        claim="c",
        target="t",
        module="m",
        computations=(ran("C1"), ran("C2"), ran("C3"), ran("C4")),
        flags=("vacuousGeometry",),
        closure={"X.vacuousGeometry"},
        outcomes=(outcome("m", "vacuousGeometry", "t", survived=True),),
        kernel=Verdict.VALIDATED_TERM,
        required=("missingLemma",),
    )
    html = render_graph(report, required=report.required)
    for colour in (RED, AMBER, GREEN, BLUE, YELLOW):
        assert colour in html, colour
    assert "No verdict here means" in html


def test_the_six_artefacts_are_written_and_hashed(tmp_path):
    report = build_report(
        claim="c",
        target="t",
        module="m",
        computations=(ran("C1", ("A", "B")), ran("C2", ("A", "B")), ran("C3"), ran("C4")),
        kernel=Verdict.VALIDATED_TERM,
    )
    hashes = write_artefacts(report, tmp_path, first=report.computation("C1"), second=report.computation("C2"))
    expected = {
        "closure_deps.txt",
        "closure_laud.txt",
        "closure_crossvalidated.json",
        "load_bearing.json",
        "dependency_graph.html",
        "gap_statement.md",
    }
    assert set(hashes) == expected
    for name, digest in hashes.items():
        assert len(digest) == 64
        assert (tmp_path / name).is_file()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"] == hashes
    gap = (tmp_path / "gap_statement.md").read_text(encoding="utf-8")
    assert "## 4. What would move the verdict" in gap
    assert not report.failed_checks, [c.detail for c in report.failed_checks]
    assert "It does not say the Riemann hypothesis is true" in gap
    render_gap_statement(report)
