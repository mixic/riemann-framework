"""The declaration scan: what it finds, what it cannot see, and why it is not a verdict.

The failure it exists for is a *silent* omission -- an input the argument uses that the
declaration never mentions, which the DH and circularity screens cannot see because they
read declarations. The tests below establish the lexicographic mechanics, drive the
instrument into reporting an unreconciled mention, and pin the property that matters most:
a scan that finds nothing must not be reported as success.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from riemann_framework.dh_filter import DH_INPUTS
from riemann_framework.input_omission import (
    PHRASES,
    normalise,
    reconcile,
    scan,
)
from riemann_framework.trace_formula_screen import DECLARED, NOT_DECLARED


def test_every_inventory_row_has_vocabulary():
    assert set(PHRASES) == set(DH_INPUTS), set(PHRASES) ^ set(DH_INPUTS)
    for key, phrases in PHRASES.items():
        assert phrases, key
        assert all(phrase == phrase.lower() and phrase.strip() for phrase in phrases), key


def test_the_ledgers_are_disjoint_and_reference_the_inventory():
    declared = {item.key for item in DECLARED}
    excluded = {item.key for item in NOT_DECLARED}
    assert not declared & excluded, declared & excluded
    assert declared | excluded <= set(DH_INPUTS)
    for item in (*DECLARED, *NOT_DECLARED):
        assert item.where.strip() and item.why.strip(), item.key


def test_a_mention_is_found_in_plain_prose():
    found = scan("The argument uses the Euler product at every prime.")
    assert found["euler_product"].count == 1
    assert "euler product" in found["euler_product"].phrases


def test_hyphenation_plural_and_typographic_apostrophe_are_folded():
    """PDF text breaks phrases in ways a literal search misses, so normalisation is tested."""
    found = scan("Partial Euler-\nproducts appear here; the functional-\nequations too.")
    assert found["euler_product"].count == 1
    assert found["functional_equation"].count == 1
    assert normalise("Li\u2019s criterion") == "Li's criterion"
    assert scan("Li's criterion is not used")["li_positivity"].count == 1


def test_a_mention_outside_both_ledgers_is_unreconciled():
    """The one outcome that matters: a hypothesis the declaration does not account for."""
    report = reconcile("The proof uses the zero-counting asymptotic for N(T).")
    assert report.status == "unreconciled"
    assert [item.key for item in report.unreconciled] == ["riemann_von_mangoldt_count"]
    assert report.declared == () and report.excluded == ()


def test_every_mention_is_classified_declared_or_excluded():
    text = " ".join(
        [
            "The Euler product is used.",
            "Weil's explicit formula is used.",
            "The functional equation is used.",
            "Li's criterion is not used.",
            "Pair correlation is not used.",
            "The Hadamard product is not stated.",
        ]
    )
    report = reconcile(text)
    assert report.status == "reconciled"
    assert {item.key for item in report.declared} == {item.key for item in DECLARED}
    assert {item.key for item in report.excluded} == {item.key for item in NOT_DECLARED}
    assert report.unreconciled == ()


def test_a_document_that_names_nothing_is_not_a_pass():
    """Vacuity guard: no mentions is a failed engagement, never a clean declaration."""
    report = reconcile("This document is about coffee.")
    assert report.status == "no_mentions"
    assert report.total_mentions == 0
    assert len(report.unmentioned) == len(PHRASES)


def test_the_report_is_json_serialisable():
    report = reconcile("The Euler product is used.")
    payload = json.loads(json.dumps(report.summary()))
    assert payload["status"] == "reconciled"
    assert payload["declared"][0]["key"] == "euler_product"


def test_the_command_line_reports_the_reconciliation_on_a_text_extract(tmp_path):
    sample = tmp_path / "draft.txt"
    sample.write_text("The Euler product is used; the zero-counting asymptotic is not.", encoding="utf-8")
    out = tmp_path / "report.json"
    script = Path(__file__).resolve().parents[2] / "scripts" / "audit" / "scan_declared_inputs.py"

    result = subprocess.run(
        [sys.executable, str(script), "--text", str(sample), "--json", str(out)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0, result.stderr
    assert "status: unreconciled" in result.stdout, result.stdout
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["report"]["unreconciled"][0]["key"] == "riemann_von_mangoldt_count"
