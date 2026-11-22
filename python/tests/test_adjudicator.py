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
"""The adjudicator's rules, driven into every branch without a toolchain.

Two properties are worth more than all the rest, and both are tested by making them fail:
the aggregation cannot reach `validated (term)` while a probe is missing or a vacuity
mutant survives, and a check that did not run is never reported as a check that failed.
The second is not hypothetical: the first version collapsed them, and the live run
against the absent archive came back `rejected` from a review whose layers had never
executed.

No test in this file invokes Lean. The Lean-backed behaviour is in
`test_alpoge_claim.py`, which skips when the toolchain is absent; this file has to run
everywhere, because the rules are the part a reader is asked to trust.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from riemann_framework.adjudicator import (
    AXIOM_TRAP_NOTE,
    BLOCKING_OPERATORS,
    COLOURS,
    STANDING_POSITION,
    Adjudication,
    Graph,
    MutationOutcome,
    Mutant,
    Probe,
    ProbeResult,
    aggregate,
    build_graph,
    discovered_flags,
    enclosing_declaration,
    load_bearing,
    load_mutants,
    mutation_verdict,
    named_computations,
    probe_dependency_trace,
    probe_kernel,
    probe_proof_review,
    probe_vacuity,
    render_gap_statement,
    render_html,
    render_json,
    render_tex,
    run_mutant,
    tex_escape,
)
from riemann_framework.claim_audit import (
    DISCREPANCY_SAMPLE,
    Claim,
    ClaimReport,
    Finding,
    Instrument,
    Level,
    Status,
    Verdict,
    compare_closures,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CLAIM_PATH = REPO_ROOT / "claims" / "alpoge_2026.json"


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def claim() -> Claim:
    return Claim.from_json(CLAIM_PATH)


def formal(
    check: str,
    status: Status = Status.CHECKED_OK,
    verdict: Verdict = Verdict.NOT_ASSESSED,
    instrument: Instrument = Instrument.KERNEL,
    details: dict[str, Any] | None = None,
    evidence: str = "an observation",
) -> Finding:
    return Finding(
        level=Level.FORMAL,
        check=check,
        status=status,
        verdict=verdict,
        instrument="a probe",
        evidence=evidence,
        limits="a stated limit",
        instrument_class=instrument,
        details=details or {},
    )


def report(claim: Claim, *findings: Finding) -> ClaimReport:
    return ClaimReport(
        claim=claim, findings=tuple(findings), evidence="E3", evidence_reasons="E3: run"
    )


def trace_finding(
    theorem: str,
    closure: int,
    reached: list[str],
    suspects: list[str],
    *,
    cross: dict[str, Any] | None = None,
) -> Finding:
    payload: dict[str, Any] = {
        "theorem": theorem,
        "closure": closure,
        "reached": reached,
        "suspects": suspects,
        "extractor": "deps",
    }
    if cross is not None:
        payload["cross_validation"] = cross
    return formal(
        f"role: dependency trace of `{theorem}`",
        status=Status.CHECKED_FAILED if reached else Status.CHECKED_OK,
        verdict=Verdict.UNDETERMINED if reached else Verdict.VALIDATED_TERM,
        instrument=Instrument.DEPENDENCY_TRACE,
        details=payload,
    )


def agreeing(theorem: str, closure: int) -> dict[str, Any]:
    return compare_closures(
        theorem,
        {"extractor": "deps", "names": {f"n{i}" for i in range(closure)},
         "reached": [], "closure": closure},
        {"extractor": "depsm", "names": {f"n{i}" for i in range(closure)},
         "reached": [], "closure": closure},
    )


def disagreeing(theorem: str) -> dict[str, Any]:
    return compare_closures(
        theorem,
        {"extractor": "deps", "names": {"a", "b", "c"}, "reached": [], "closure": 3},
        {"extractor": "depsm", "names": {"a", "b", "d"}, "reached": [], "closure": 3},
    )


def outcome(
    operator: str = "CONTENT_FLIP",
    *,
    ran: bool = True,
    survived: bool = False,
    theorem: str = "t",
    find: str = "def d : Prop := True",
    failed: tuple[str, ...] = (),
) -> MutationOutcome:
    return MutationOutcome(
        mutant=Mutant(
            id=f"m-{operator}-{theorem}",
            operator=operator,
            source="x.lean",
            find=find,
            replace="def d : Prop := False",
            theorem=theorem,
        ),
        ran=ran,
        compiled=ran and not survived,
        failed_declarations=failed or ((theorem,) if not survived and ran else ()),
        survived=survived,
        unattributed=False,
        reason="" if ran else "the mutant's source is not on this machine: x.lean",
    )


# ============================================================
# The aggregation, and the falsification condition
# ============================================================

def all_passing(trace: ProbeResult | None = None) -> list[ProbeResult]:
    kernel = ProbeResult(Probe.KERNEL, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok")
    mutation = mutation_verdict([outcome()], declared=True, live=True)
    vacuity = ProbeResult(
        Probe.VACUITY, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "no shape"
    )
    trace = trace or ProbeResult(
        Probe.DEPENDENCY_TRACE, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "clean"
    )
    review = probe_proof_review(
        ClaimReport(
            claim=Claim.from_json(CLAIM_PATH),
            findings=(
                formal("role: is the theorem the Riemann hypothesis"),
            ),
            evidence="E3",
            evidence_reasons="E3: run",
        ),
        kernel,
        trace,
        mutation,
    )
    return [kernel, mutation, vacuity, review, trace]


def test_the_passing_panel_reaches_the_term_verdict(claim: Claim) -> None:
    probes = all_passing()
    assert aggregate(probes) is Verdict.VALIDATED_TERM


def test_a_missing_trace_withholds_the_verdict() -> None:
    """The falsification condition, first half: no trace, no term verdict."""
    probes = all_passing()[:-1]
    assert aggregate(probes) is Verdict.UNDETERMINED


def test_a_surviving_vacuity_mutant_forces_the_review_to_withhold() -> None:
    """The falsification condition, second half, at the level it is enforced.

    A `VACUOUS_TRUTH` mutant that survives means the hypothesis does no work. The
    mutation probe withholds, and the review has no branch that can pass L3 while it
    does, so the panel cannot reach `validated (term)` — it is not a matter of anyone
    remembering to check.
    """
    survivor = outcome("VACUOUS_TRUTH", survived=True)
    mutation = mutation_verdict([survivor], declared=True, live=True)
    assert mutation.verdict is Verdict.UNDETERMINED
    kernel = ProbeResult(Probe.KERNEL, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok")
    trace = ProbeResult(
        Probe.DEPENDENCY_TRACE, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "clean"
    )
    review = probe_proof_review(
        ClaimReport(
            claim=Claim.from_json(CLAIM_PATH),
            findings=(formal("role: is the theorem the Riemann hypothesis"),),
            evidence="E3",
            evidence_reasons="E3: run",
        ),
        kernel,
        trace,
        mutation,
    )
    assert review.verdict is Verdict.UNDETERMINED
    assert aggregate([kernel, mutation, review, trace]) is Verdict.UNDETERMINED


def test_rejected_dominates_everything() -> None:
    probes = all_passing()
    rejected = ProbeResult(
        Probe.PROOF_REVIEW, Verdict.REJECTED, Status.CHECKED_FAILED, "statement mismatch"
    )
    assert aggregate([rejected, *probes]) is Verdict.REJECTED


def test_outside_domain_requires_every_probe() -> None:
    probes = [
        ProbeResult(probe, Verdict.OUTSIDE_DOMAIN, Status.NOT_APPLICABLE, "no artefact")
        for probe in Probe
    ]
    assert aggregate(probes) is Verdict.OUTSIDE_DOMAIN
    probes[0] = ProbeResult(
        Probe.KERNEL, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok"
    )
    assert aggregate(probes) is Verdict.UNDETERMINED


def test_the_named_computations_are_the_undetermined_ones() -> None:
    probes = [
        ProbeResult(
            Probe.KERNEL, Verdict.UNDETERMINED, Status.NOT_RUN, "no lean",
            named_computation="run it",
        ),
        ProbeResult(Probe.VACUITY, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok"),
    ]
    assert named_computations(probes) == ("KERNEL: run it",)


def test_an_undetermined_probe_must_name_its_computation() -> None:
    with pytest.raises(ValueError, match="must name its computation"):
        ProbeResult(Probe.KERNEL, Verdict.UNDETERMINED, Status.NOT_RUN, "no lean")


# ============================================================
# A check that did not run is not a check that failed
# ============================================================

def test_a_not_run_statement_row_does_not_reject_the_review(claim: Claim) -> None:
    """The live bug: no Lean, everything `not_run`, review said `rejected`."""
    offline = report(
        claim,
        formal("live: is the theorem the Riemann hypothesis", status=Status.NOT_RUN),
    )
    kernel = ProbeResult(Probe.KERNEL, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "replay")
    trace = ProbeResult(
        Probe.DEPENDENCY_TRACE, Verdict.UNDETERMINED, Status.NOT_RUN, "no lean",
        named_computation="run it",
    )
    mutation = ProbeResult(
        Probe.MUTATION, Verdict.UNDETERMINED, Status.NOT_RUN, "no lean",
        named_computation="run it",
    )
    review = probe_proof_review(offline, kernel, trace, mutation)
    assert review.verdict is Verdict.UNDETERMINED
    assert review.status is Status.NOT_RUN
    assert "not established" in review.evidence
    assert review.details["layers"]["L2_statement_faithfulness"] == "not established"


def test_a_failed_statement_row_rejects_the_review(claim: Claim) -> None:
    mismatch = report(
        claim,
        formal(
            "live: is the theorem the Riemann hypothesis",
            status=Status.CHECKED_FAILED,
            verdict=Verdict.UNDETERMINED,
        ),
    )
    kernel = ProbeResult(Probe.KERNEL, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok")
    clean = ProbeResult(
        Probe.DEPENDENCY_TRACE, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "clean"
    )
    mutation = ProbeResult(
        Probe.MUTATION, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok"
    )
    review = probe_proof_review(mismatch, kernel, clean, mutation)
    assert review.verdict is Verdict.REJECTED
    assert review.details["blocking_failures"] == ["L2_statement_faithfulness"]


def test_a_failing_kernel_withholds_the_review_rather_than_rejecting_it(claim: Claim) -> None:
    """L1 is soundness, not a screen: `rejected` is for arguments that were read.

    Driven at the live control, which contains two `sorry`s by construction. The first
    version returned `rejected` for it, which reads as "an argument was refuted" and is
    false: no argument was read.
    """
    kernel = ProbeResult(
        Probe.KERNEL, Verdict.UNDETERMINED, Status.CHECKED_FAILED, "sorryAx present",
        named_computation="remove the two `sorry`s",
    )
    review = probe_proof_review(
        report(claim, formal("live: is the theorem the Riemann hypothesis")),
        kernel,
        ProbeResult(Probe.DEPENDENCY_TRACE, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok"),
        ProbeResult(Probe.MUTATION, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok"),
    )
    assert review.verdict is Verdict.UNDETERMINED
    assert review.status is Status.CHECKED_FAILED
    assert "not a rejection" in review.evidence
    assert aggregate([kernel, review]) is Verdict.UNDETERMINED


# ============================================================
# Mutation outcomes
# ============================================================

def test_an_absent_mutant_is_not_run_and_not_killed() -> None:
    """The archive is not on the machine, so its mutant cannot be evidence of anything."""
    declared = Mutant(
        id="published",
        operator="CONTENT_FLIP",
        source="external/does-not-exist/Anchor.lean",
        find="def anyGeometry (_D _J _X : Type) : Prop := True",
        replace="def anyGeometry (_D _J _X : Type) : Prop := False",
        theorem="riemannHypothesis",
    )
    result = run_mutant(Path.cwd(), declared, timeout=1)
    assert result.ran is False
    assert result.killed is False
    assert "not on this machine" in result.reason


def test_an_ambiguous_anchor_is_refused_rather_than_applied(tmp_path: Path) -> None:
    source = tmp_path / "Anchor.lean"
    source.write_text("def d : Prop := True\ndef d : Prop := True\n", encoding="utf-8")
    ambiguous = Mutant(
        id="ambiguous",
        operator="CONTENT_FLIP",
        source="Anchor.lean",
        find="def d : Prop := True",
        replace="def d : Prop := False",
        theorem="d",
    )
    result = run_mutant(tmp_path, ambiguous, timeout=1)
    assert result.ran is False
    assert "unambiguous" in result.reason


def test_a_declared_but_unrunnable_mutant_withholds_the_verdict() -> None:
    verdict = mutation_verdict(
        [outcome(ran=False)], declared=True, live=True
    )
    assert verdict.verdict is Verdict.UNDETERMINED
    assert verdict.status is Status.NOT_RUN
    assert "not on this machine" in (verdict.named_computation or "")


def test_a_surviving_content_flip_is_not_a_blocking_marker() -> None:
    """A flipped definition a theorem survives is evidence the definition is not used.

    That is the opposite of a vacuity objection, so it does not withhold the verdict;
    the two operators that do are named in `BLOCKING_OPERATORS`.
    """
    verdict = mutation_verdict(
        [outcome("CONTENT_FLIP", survived=True)], declared=True, live=True
    )
    assert verdict.verdict is Verdict.VALIDATED_TERM
    assert "CONTENT_FLIP" not in BLOCKING_OPERATORS


def test_the_blocking_operators_are_the_vacuity_markers() -> None:
    assert BLOCKING_OPERATORS == ("VACUOUS_TRUTH", "UNUSED_HYP")


def test_an_undeclared_mutant_is_outside_domain_not_a_pass() -> None:
    verdict = mutation_verdict([], declared=False, live=True)
    assert verdict.verdict is Verdict.OUTSIDE_DOMAIN


def test_enclosing_declaration_attributes_a_line_to_its_declaration() -> None:
    source = "namespace X\n\ndef a : Nat := 1\n\n theorem b : True := trivial\n"
    assert enclosing_declaration(source, 3) == "a"
    assert enclosing_declaration(source, 5) == "b"
    assert enclosing_declaration("", 1) is None


def test_a_mutants_declaration_is_read_off_its_anchor() -> None:
    mutant = Mutant(
        id="m", operator="CONTENT_FLIP", source="x", find="def anyGeometry (_D : Type) : Prop := True",
        replace="", theorem="t",
    )
    assert mutant.declaration == "anyGeometry"


# ============================================================
# The dual extractor, and the discrepancy record
# ============================================================

def test_identical_closures_are_corroborated() -> None:
    record = agreeing("RiemannFramework.geometry_is_vacuous", 4)
    assert record["agreement"] is True
    assert record["discrepancy"] is False
    assert record["named_computation"] is None
    assert record["verdict"] == Verdict.VALIDATED_TERM.value


def test_different_closures_are_recorded_and_never_reconciled() -> None:
    record = disagreeing("RiemannFramework.geometry_is_vacuous")
    assert record["agreement"] is False
    assert record["discrepancy"] is True
    assert record["only_in_deps"] == ["c"]
    assert record["only_in_depsm"] == ["d"]
    assert record["verdict"] == Verdict.UNDETERMINED.value
    assert "reconcile the closure mismatch" in (record["named_computation"] or "")


def test_a_large_disagreement_is_sampled_not_dropped() -> None:
    left = {f"l{i}" for i in range(DISCREPANCY_SAMPLE + 5)}
    right = {f"r{i}" for i in range(DISCREPANCY_SAMPLE + 7)}
    record = compare_closures(
        "t",
        {"extractor": "deps", "names": left, "reached": [], "closure": len(left)},
        {"extractor": "depsm", "names": right, "reached": [], "closure": len(right)},
    )
    assert len(record["only_in_deps"]) == DISCREPANCY_SAMPLE
    assert record["only_in_first_count"] == len(left)
    assert record["only_in_second_count"] == len(right)


def test_the_discrepancy_record_states_what_it_does_not_close() -> None:
    scope = agreeing("t", 1)["scope"]
    assert "same environment" in scope
    assert "not a defect in Lean" in scope


def test_an_uncorroborated_closure_withholds_the_trace_verdict(claim: Claim) -> None:
    clean = trace_finding("t", 3, [], ["s"], cross=disagreeing("t"))
    probe = probe_dependency_trace(report(claim, clean))
    assert probe.verdict is Verdict.UNDETERMINED
    assert probe.details["discrepancy"] is True
    assert "reconcile the closure mismatch" in (probe.named_computation or "")


def test_a_corroborated_clean_closure_validates_the_trace(claim: Claim) -> None:
    clean = trace_finding("t", 3, [], ["s"], cross=agreeing("t", 3))
    probe = probe_dependency_trace(report(claim, clean))
    assert probe.verdict is Verdict.VALIDATED_TERM
    assert "both extractors agree" in probe.evidence
    assert probe.details["discrepancy"] is False


def test_a_closure_without_a_cross_validation_is_not_corroborated(claim: Claim) -> None:
    clean = trace_finding("t", 3, [], ["s"])
    probe = probe_dependency_trace(report(claim, clean))
    assert probe.verdict is Verdict.UNDETERMINED
    assert "one instrument's reading" in probe.evidence


def test_a_reached_suspect_outranks_the_cross_validation(claim: Claim) -> None:
    dirty = trace_finding("t", 4, ["s"], ["s"], cross=agreeing("t", 4))
    probe = probe_dependency_trace(report(claim, dirty))
    assert probe.verdict is Verdict.UNDETERMINED
    assert "reaches" in probe.evidence


def test_the_trace_probe_is_outside_domain_without_a_target(claim: Claim) -> None:
    probe = probe_dependency_trace(report(claim))
    assert probe.verdict is Verdict.OUTSIDE_DOMAIN


def test_the_trace_probe_reports_a_trace_that_did_not_run(claim: Claim) -> None:
    pending = formal(
        "role: dependency trace of `t`",
        status=Status.NOT_RUN,
        instrument=Instrument.DEPENDENCY_TRACE,
        evidence="not run: the artefact is not on this machine",
    )
    probe = probe_dependency_trace(report(claim, pending))
    assert probe.verdict is Verdict.UNDETERMINED
    assert probe.status is Status.NOT_RUN


# ============================================================
# Probes that read the census
# ============================================================

def test_the_vacuity_census_locates_but_never_passes(claim: Claim) -> None:
    located = formal(
        "role: are the definitions non-vacuous",
        status=Status.UNDETERMINED,
        verdict=Verdict.UNDETERMINED,
        instrument=Instrument.VACUITY_SCAN,
        details={"true_bodied": ["anyGeometry"], "scanned": True},
    )
    probe = probe_vacuity(report(claim, located))
    assert probe.verdict is Verdict.UNDETERMINED
    assert probe.details["flagged"] == ["anyGeometry"]


def test_the_kernel_probe_reads_only_kernel_findings(claim: Claim) -> None:
    only_census = report(
        claim,
        formal(
            "role: are the definitions non-vacuous",
            status=Status.UNDETERMINED,
            verdict=Verdict.UNDETERMINED,
            instrument=Instrument.VACUITY_SCAN,
        ),
    )
    assert probe_kernel(only_census).verdict is Verdict.OUTSIDE_DOMAIN


# ============================================================
# The graph
# ============================================================

def graph_probe(reached: list[str], suspects: list[str], theorem: str = "t") -> ProbeResult:
    return ProbeResult(
        Probe.DEPENDENCY_TRACE,
        Verdict.UNDETERMINED if reached else Verdict.VALIDATED_TERM,
        Status.CHECKED_FAILED if reached else Status.CHECKED_OK,
        "a summary",
        named_computation="refactor" if reached else None,
        details={
            "reached": reached,
            "closures": [
                {"theorem": theorem, "closure": 9, "suspects": suspects,
                 "reached": reached}
            ],
        },
    )


def test_reached_is_red_and_unreached_is_amber() -> None:
    graph = build_graph(
        graph_probe(["reached"], ["reached", "not_there"]), theorems=["t"]
    )
    colours = {node.name: node.colour for node in graph.nodes}
    assert colours["reached"] == "red"
    assert colours["not_there"] == "amber"
    assert graph.red == ("reached",)
    assert set(graph.counts()) == set(COLOURS)


def test_the_graph_says_what_it_does_not_show() -> None:
    caveat = build_graph(graph_probe([], []), theorems=[]).caveat
    assert "not a per-node edge set" in caveat
    assert "mathematically required" in caveat


def test_flagged_names_come_from_the_probes_not_only_the_record(claim: Claim) -> None:
    census = formal(
        "role: are the definitions non-vacuous",
        status=Status.UNDETERMINED,
        verdict=Verdict.UNDETERMINED,
        instrument=Instrument.VACUITY_SCAN,
        details={"true_bodied": ["vacuousGeometry"]},
    )
    assert discovered_flags(report(claim, census)) == ("vacuousGeometry",)
    graph = build_graph(
        graph_probe([], []), flagged=discovered_flags(report(claim, census))
    )
    assert graph.nodes[0].name == "vacuousGeometry"
    assert graph.nodes[0].colour == "amber"


def test_a_killed_content_flip_marks_its_declaration_load_bearing() -> None:
    killed = outcome("CONTENT_FLIP", survived=False, find="def vacuousGeometry : Prop := True")
    survivor = outcome("CONTENT_FLIP", survived=True, find="def other : Prop := True")
    assert load_bearing([killed, survivor]) == ("vacuousGeometry",)
    graph = build_graph(
        graph_probe([], ["vacuousGeometry"]),
        load_bearing_names=load_bearing([killed, survivor]),
    )
    assert "load-bearing elsewhere" in graph.nodes[0].role


def test_edges_are_attributed_to_the_theorem_and_labelled() -> None:
    graph = build_graph(graph_probe(["s"], ["s"], theorem="thm"), theorems=["thm"])
    edges = {(edge.source, edge.target, edge.relation) for edge in graph.edges}
    assert ("thm", "s", "reaches") in edges


# ============================================================
# The deliverables
# ============================================================

def an_adjudication(
    claim: Claim,
    *,
    cross: dict[str, Any] | None = None,
    reached: list[str] | None = None,
) -> Adjudication:
    reached = reached or []
    clean = trace_finding("t", 3, reached, ["s"], cross=cross or agreeing("t", 3))
    statement = formal("role: is the theorem the Riemann hypothesis")
    panel_report = report(claim, clean, statement)
    trace = probe_dependency_trace(panel_report)
    kernel = ProbeResult(Probe.KERNEL, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok")
    mutation = ProbeResult(
        Probe.MUTATION, Verdict.VALIDATED_TERM, Status.CHECKED_OK, "ok"
    )
    review = probe_proof_review(panel_report, kernel, trace, mutation)
    probes = (kernel, mutation, trace, review)
    return Adjudication(
        claim_id="a_claim",
        probes=(kernel, mutation, trace, review),
        final_verdict=aggregate(probes),
        graph=build_graph(trace, theorems=["t"]),
        report=panel_report,
        mutants=(),
    )


def test_the_gap_statement_has_the_discrepancy_section(claim: Claim) -> None:
    markdown = render_gap_statement(an_adjudication(claim, cross=disagreeing("t")))
    assert "## 2b. Closure discrepancy" in markdown
    assert "**disagreement**" in markdown
    assert "`c`" in markdown and "`d`" in markdown


def test_the_gap_statement_reports_agreement_as_agreement(claim: Claim) -> None:
    markdown = render_gap_statement(an_adjudication(claim, cross=agreeing("t", 3)))
    assert "**disagreement**" not in markdown
    assert "agree on all 3 names" in markdown


def test_the_gap_statement_says_when_no_closure_exists(claim: Claim) -> None:
    trace = ProbeResult(
        Probe.DEPENDENCY_TRACE, Verdict.UNDETERMINED, Status.NOT_RUN, "no closure",
        named_computation="run it",
    )
    adjudication = Adjudication(
        claim_id="a_claim",
        probes=(trace,),
        final_verdict=Verdict.UNDETERMINED,
        graph=Graph((), (), "no edges"),
        report=report(claim),
    )
    markdown = render_gap_statement(adjudication)
    assert "No closure was computed" in markdown
    assert "No cross-validation record exists" in markdown


def test_every_deliverable_carries_the_two_limits(claim: Claim) -> None:
    adjudication = an_adjudication(claim)
    assert STANDING_POSITION in adjudication.as_dict()["position"]
    assert AXIOM_TRAP_NOTE in adjudication.as_dict()["axiom_trap_note"]
    assert AXIOM_TRAP_NOTE in render_gap_statement(adjudication)
    assert STANDING_POSITION in render_gap_statement(adjudication)
    assert AXIOM_TRAP_NOTE in render_html(adjudication)


def test_the_json_deliverable_is_the_whole_record(claim: Claim) -> None:
    data = json.loads(render_json(an_adjudication(claim)))
    assert data["final_verdict"] == Verdict.VALIDATED_TERM.value
    assert [probe["probe"] for probe in data["probes"]] == [
        "KERNEL", "MUTATION", "DEPENDENCY_TRACE", "PROOF_REVIEW"
    ]
    assert data["graph"]["counts"]["green"] >= 1
    assert "Riemann hypothesis" in data["position"]
    assert data["probes"][2]["details"]["cross_validation"][0]["agreement"] is True


def test_the_tex_table_escapes_names_and_carries_the_verdict_macro(claim: Claim) -> None:
    tex = render_tex(an_adjudication(claim))
    assert r"\providecommand{\verdict}" in tex
    assert r"\begin{tabularx}" in tex and r"\end{tabularx}" in tex
    assert tex.count(r"\\") >= 5
    escaped = tex_escape("RiemannFramework.geometry_is_vacuous")
    assert r"RiemannFramework.geometry\_is\_vacuous" == escaped
    assert tex_escape("50% & $x$ # 5") == r"50\% \& \$x\$ \# 5"


def test_the_html_graph_is_self_contained(claim: Claim) -> None:
    page = render_html(an_adjudication(claim))
    assert "<svg" in page
    assert "http://" not in page.replace("http://www.w3.org", "")
    assert "https://" not in page
    assert "<script" not in page
    for colour in COLOURS.values():
        assert colour in page
    assert "Closure cross-validation" in page


def test_the_html_marks_a_disagreement(claim: Claim) -> None:
    page = render_html(an_adjudication(claim, cross=disagreeing("t")))
    assert "disagreement" in page
    assert "reconcile the closure mismatch" in page


# ============================================================
# Records
# ============================================================

def test_the_record_declares_the_three_mutants_it_uses() -> None:
    mutants = load_mutants(CLAIM_PATH)
    operators = [mutant.operator for mutant in mutants]
    assert operators.count("CONTENT_FLIP") == 3
    assert operators.count("VACUOUS_TRUTH") == 1


def test_the_role_filter_selects_one_target() -> None:
    live = load_mutants(
        CLAIM_PATH, "this repository's recording of the dispute (live)"
    )
    assert len(live) == 3
    assert all(mutant.source.startswith("lean/") for mutant in live)


def test_an_incomplete_mutant_record_is_refused() -> None:
    with pytest.raises(ValueError, match="missing"):
        Mutant.from_record({"id": "m", "operator": "CONTENT_FLIP"})
