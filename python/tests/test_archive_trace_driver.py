"""The archive trace driver: preconditions, plan, and the not-run record.

The driver exists because the paper's decisive computation has never been run on the
published archive. Nothing here needs Lean: the tests pin the record's language (`not run`
with a reason, never `undetermined`), the plan's steps, and the shape of a completed
record, so that the only missing input when the archive is in place is the archive.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DRIVER = REPO_ROOT / "scripts" / "audit" / "trace_archive.py"


def load_driver():
    spec = importlib.util.spec_from_file_location("trace_archive_for_test", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fake_archive(tmp_path: Path, *, toolchain: str = "leanprover/lean4:v4.33.1", module: str = "") -> Path:
    archive = tmp_path / "archive"
    (archive / "Archive").mkdir(parents=True)
    (archive / "lakefile.lean").write_text("import Lake\nopen Lake DSL\n", encoding="utf-8")
    (archive / "lean-toolchain").write_text(toolchain + "\n", encoding="utf-8")
    if module:
        target = archive / Path(*module.split(".")).with_suffix(".lean")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("theorem riemannHypothesis : True := trivial\n", encoding="utf-8")
    return archive


def test_a_missing_archive_is_reported_not_run_with_the_path(tmp_path):
    driver = load_driver()
    record = driver.execute(tmp_path / "absent", "Statements", "riemannHypothesis")
    assert record["status"] == "not_run"
    assert "absent" in str(record["reason"])
    assert "results" not in record


def test_an_archive_without_a_lakefile_is_blocked(tmp_path):
    driver = load_driver()
    empty = tmp_path / "empty"
    empty.mkdir()
    checks = driver.preconditions(empty)
    assert not driver.ready(checks)
    assert any(check.name == "lakefile" and not check.ok for check in checks)


def test_a_toolchain_mismatch_is_a_recorded_risk_not_a_blocker(tmp_path):
    driver = load_driver()
    archive = fake_archive(tmp_path, toolchain="leanprover/lean4:v4.34.0-rc2")
    checks = driver.preconditions(archive)
    assert driver.ready(checks), [check for check in checks if check.blocking and not check.ok]
    toolchain = next(check for check in checks if check.name == "toolchain")
    assert not toolchain.ok and not toolchain.blocking
    assert "v4.34.0-rc2" in toolchain.detail and driver.EXPECTED_TOOLCHAIN in toolchain.detail


def test_the_plan_names_the_copy_the_target_and_the_record(tmp_path):
    driver = load_driver()
    archive = fake_archive(tmp_path, module="Archive.Statements")
    steps = driver.plan(archive, "Archive.Statements", "riemannHypothesis")
    text = "\n".join(steps)
    assert "DependencyTrace.lean" in text and "Archive.Statements" in text
    assert "#deps riemannHypothesis" in text and "#depsm riemannHypothesis" in text
    assert not (archive / driver.AUDIT_DIR).exists(), "the plan must not touch the archive"


def test_a_completed_run_writes_a_json_safe_record(tmp_path, monkeypatch):
    driver = load_driver()
    archive = fake_archive(tmp_path, module="Archive.Statements")

    def fake_trace(project_root, module, request, *, timeout, trace_module):
        assert Path(project_root) == archive
        assert module == "Archive.Statements"
        assert request.theorem == "riemannHypothesis"
        assert trace_module == "Audit.DependencyTrace"
        return "validated (term)", {
            "theorem": request.theorem,
            "agreement": True,
            "discrepancy": False,
            "counts": {"deps": 4, "depsm": 4},
            "names": {"A", "B"},
        }

    monkeypatch.setattr(driver, "trace_with_cross_validation", fake_trace)
    record = driver.execute(archive, "Archive.Statements", "riemannHypothesis")
    assert record["status"] == "validated (term)"
    written = json.loads(json.dumps(record))
    assert written["result"]["counts"]["deps"] == 4
    assert written["result"]["names"] == ["A", "B"], "sets must become sorted-free lists"
    assert (archive / "Audit" / "DependencyTrace.lean").is_file()


def test_the_command_line_prints_the_plan_and_exits_zero(tmp_path):
    driver = load_driver()
    archive = fake_archive(tmp_path, module="Archive.Statements")
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "--archive",
            str(archive),
            "--module",
            "Archive.Statements",
            "--plan",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stderr
    assert "status: planned" in result.stdout
    assert "elaborate '#deps riemannHypothesis'" in result.stdout
