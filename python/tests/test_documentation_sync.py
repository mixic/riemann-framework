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
"""Guards that the documentation still matches the code.

The failure mode this repository actually has is not a wrong theorem; it is a
document that was true when written and stopped being true quietly. It has
happened at least four times:

* the README test count was stale by 50 (589 stated, 640 real), and
  `test_prime_certificate.py` was missing from the table entirely;
* `docs/bb84_implementation.md` said "the other three" attack classes were
  unimplemented and that "the decoy-state mitigation is named rather than
  implemented", while `decoy_state_report`, `finite_key_report` and
  `minimum_rounds` were all in the code and tested;
* `docs/quantum_chaos_claims.md` claimed pair correlation was implemented when
  only gap statistics were;
* `docs/claimed_proof_triage.md` recorded a pipeline crash as "documented rather
  than fixed" until it was fixed.

Only the *measurable* subset can be guarded mechanically: counts, paths, and the
existence of the things the README points at. Prose that contradicts the code --
"three of four" when it is two -- cannot be caught by any check in this file, and
this file must not be read as claiming otherwise. What it does catch is the
cheap, recurring half, which is where most of the drift has actually been.

Every check below parses a real artefact (a live pytest collection, the README
tables, the filesystem) rather than a hardcoded expectation, so the guard cannot
drift in the same way the documents did.
"""

from __future__ import annotations

import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
PYTHON_DIR = REPO_ROOT / "python"
MODULE_DIR = PYTHON_DIR / "riemann_framework"
TESTS_DIR = PYTHON_DIR / "tests"
DOCS_DIR = REPO_ROOT / "docs"


@lru_cache(maxsize=1)
def readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def collected_counts() -> dict[str, int]:
    """Live per-file test counts, from `pytest --collect-only`.

    Collected rather than counted from `def test_` in the source: parametrised
    tests expand at collection, so the two numbers differ (one `def` in
    `test_finite_field_curves.py` covers eight cases). The README table is meant
    to record what pytest reports, so that is what is compared.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        cwd=PYTHON_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:  # pragma: no cover - collection itself failing
        raise AssertionError(
            "pytest --collect-only failed, so the docs guard cannot run:\n"
            + result.stdout[-2000:]
            + result.stderr[-2000:]
        )
    counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        if "::" not in line:
            continue
        path = line.split("::")[0].strip().replace("\\", "/")
        if not path.startswith("tests/"):
            continue
        name = path.rsplit("/", 1)[-1]
        counts[name] = counts.get(name, 0) + 1
    return counts


def documented_test_rows() -> dict[str, int]:
    """`{test_file: count}` from the README's test table."""
    rows = re.findall(
        r"^\|\s*`(test_\w+\.py)`\s*\|\s*(\d+)\s*\|", readme_text(), re.MULTILINE
    )
    return {name: int(count) for name, count in rows}


def documented_total() -> int | None:
    """The total the README states, in either of its two places."""
    for pattern in (r"\*\*(\d+) tests pass\*\*", r"\*\*(\d+) tests passing\*\*"):
        match = re.search(pattern, readme_text())
        if match:
            return int(match.group(1))
    return None


# ============================================================
# Test counts
# ============================================================

def test_the_readme_states_a_total():
    """A guard on the guard: the parser must find the number it compares."""
    assert documented_total() is not None, (
        "no '**N tests pass**' or '**N tests passing**' found in README.md"
    )


def test_the_readme_test_table_is_not_empty():
    assert len(documented_test_rows()) >= 20, documented_test_rows()


def test_every_documented_test_count_matches_pytest():
    """The per-file table, against a live collection.

    This is the check that would have caught the count being stale by 50.
    """
    actual = collected_counts()
    documented = documented_test_rows()
    mismatches = {
        name: (documented[name], actual.get(name))
        for name in documented
        if actual.get(name) != documented[name]
    }
    assert not mismatches, (
        "README test table disagrees with `pytest --collect-only` "
        "(documented, actual):\n"
        + "\n".join(
            f"  {name}: documented {doc}, actual {act}"
            for name, (doc, act) in sorted(mismatches.items())
        )
    )


def test_every_test_file_has_a_documented_count():
    """A new test file must be added to the table, not just created.

    `test_prime_certificate.py` was missing from this table entirely while
    passing, which is how a 50-test gap went unnoticed.
    """
    rows = documented_test_rows()
    actual = collected_counts()
    missing = sorted(set(actual) - set(rows))
    assert not missing, (
        "these test files are collected but absent from the README table:\n"
        + "\n".join(f"  {name}: {actual[name]} tests" for name in missing)
    )


def test_the_documented_total_equals_the_sum_of_the_rows():
    rows = documented_test_rows()
    assert documented_total() == sum(rows.values()), (
        f"README states {documented_total()} tests in prose but its table sums to "
        f"{sum(rows.values())}"
    )


def test_the_documented_total_equals_the_live_collection():
    total = sum(collected_counts().values())
    assert documented_total() == total, (
        f"README states {documented_total()} tests; pytest collects {total}"
    )


# ============================================================
# The project structure tree
# ============================================================

def _module_files() -> list[str]:
    return sorted(
        path.name for path in MODULE_DIR.glob("*.py") if not path.name.startswith("_")
    )


def _test_files() -> list[str]:
    return sorted(path.name for path in TESTS_DIR.glob("test_*.py"))


def _doc_files() -> list[str]:
    return sorted(path.name for path in DOCS_DIR.glob("*.md"))


def test_the_structure_sections_are_not_vacuous():
    """If the parsers found nothing, the checks below would pass for free."""
    assert len(_module_files()) > 20
    assert len(_test_files()) > 20
    assert len(_doc_files()) > 15


def test_every_module_appears_in_the_readme():
    text = readme_text()
    missing = [name for name in _module_files() if name not in text]
    assert not missing, (
        "these modules are not mentioned anywhere in README.md:\n"
        + "\n".join(f"  {name}" for name in missing)
    )


def test_every_doc_appears_in_the_readme():
    text = readme_text()
    missing = [name for name in _doc_files() if name not in text]
    assert not missing, (
        "these documents are not mentioned anywhere in README.md:\n"
        + "\n".join(f"  {name}" for name in missing)
    )


def test_every_test_file_appears_in_the_readme():
    text = readme_text()
    missing = [name for name in _test_files() if name not in text]
    assert not missing, (
        "these test files are not mentioned anywhere in README.md:\n"
        + "\n".join(f"  {name}" for name in missing)
    )


# ============================================================
# Figures and links
# ============================================================

def _figure_paths() -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme_text())


def _internal_links() -> set[str]:
    links = set(re.findall(r"(?<!!)\[[^\]]*\]\(([^)#][^)]*)\)", readme_text()))
    return {
        link for link in links if not link.startswith(("http://", "https://", "mailto:"))
    }


@lru_cache(maxsize=1)
def committed_output_figures() -> frozenset[str] | None:
    """Basenames of `output/*` files that git actually tracks, or None.

    `Path.exists()` is not the question CI asks. A generated plot can sit on the
    author's disk, be excluded by the `output/` allowlist in `.gitignore`, and
    never be committed -- so the local run passes and a clean checkout fails.
    That is exactly how `output/quantum_chaos_spacing.png` broke CI while the
    whole suite was green locally: the file was present here and ignored.

    Returns None outside a git work tree (a source tarball), where the
    comparison is not answerable and the existence check above must stand alone.
    """
    try:
        listed = subprocess.run(
            ["git", "ls-files", "-z", "--", "output"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return frozenset(
        Path(entry).name for entry in listed.stdout.split("\0") if entry.strip()
    )


def test_every_figure_reference_exists():
    figures = _figure_paths()
    assert figures, "no figures found in README.md -- has the format changed?"
    missing = [path for path in figures if not (REPO_ROOT / path).exists()]
    assert not missing, "README embeds figures that do not exist:\n" + "\n".join(
        f"  {path}" for path in missing
    )

    committed = committed_output_figures()
    if committed is None:
        return
    uncommitted = [
        path
        for path in figures
        if path.startswith("output/") and Path(path).name not in committed
    ]
    assert not uncommitted, (
        "README embeds figures that are on this disk but not committed, so a\n"
        "clean checkout (and hence CI) does not have them. Allowlist each one\n"
        "in .gitignore and `git add` it:\n"
        + "\n".join(f"  {path}" for path in uncommitted)
    )


def test_every_internal_link_resolves():
    links = _internal_links()
    assert links, "no internal links found in README.md"
    broken = sorted(
        link for link in links if not (REPO_ROOT / link.split("#")[0]).exists()
    )
    assert not broken, "README has broken internal links:\n" + "\n".join(
        f"  {link}" for link in broken
    )


def test_every_output_figure_is_shown_somewhere():
    """An allowlisted plot that no document displays is dead weight.

    `output/quantum_chaos_spacing.png` sat unshown for a long time before being
    embedded. Generated artefacts are in `.gitignore` by allowlist, so a figure
    can be committed and never referenced. The comparison is against *committed*
    files, not whatever is lying on this disk: a stale local plot is not
    something the README owes an image to.
    """
    shown = {path.split("/")[-1] for path in _figure_paths()}
    committed = committed_output_figures()
    if committed is None:
        present = {path.name for path in (REPO_ROOT / "output").glob("*.png")}
    else:
        present = {name for name in committed if name.endswith(".png")}
    orphans = sorted(present - shown)
    assert not orphans, (
        "these figures are in output/ but shown nowhere in README.md:\n"
        + "\n".join(f"  output/{name}" for name in orphans)
    )


# ============================================================
# The guard itself
# ============================================================

def test_the_count_guard_detects_a_stale_row(monkeypatch):
    """Driven into failing, so a passing run above means something.

    `documented_test_rows` is patched to report one more test for a real file;
    the comparison must notice.
    """
    actual = collected_counts()
    victim = next(iter(actual))
    wrong = dict(documented_test_rows())
    wrong[victim] = wrong.get(victim, 0) + 1

    mismatches = {
        name: (wrong[name], actual.get(name))
        for name in wrong
        if actual.get(name) != wrong[name]
    }
    assert victim in mismatches


def test_the_figure_parser_finds_the_new_layers():
    """Non-vacuity for the figure check: it sees the recent additions."""
    figures = " ".join(_figure_paths())
    for expected in (
        "finite_field_curves.png",
        "de_bruijn_newman.png",
        "quantum_chaos_claims.png",
        "quantum_chaos_spacing.png",
        "number_theory_claims.png",
    ):
        assert expected in figures, expected


def test_the_committed_figure_check_is_not_fooled_by_a_local_file():
    """Driven at the real bug: `exists()` on this disk is not `tracked` by git.

    Before this helper, the existence guard passed locally on
    `output/quantum_chaos_spacing.png` -- a real file, ignored by the `output/`
    allowlist, therefore absent from CI -- and the suite went green while CI
    went red. The helper has to separate the two universes, so both halves are
    asserted: the offending plot is now tracked, and a present-but-ignored path
    is still outside the set.
    """
    committed = committed_output_figures()
    if committed is None:
        pytest.skip("not a git work tree")

    assert "quantum_chaos_spacing.png" in committed, (
        "the README embeds output/quantum_chaos_spacing.png but git does not "
        "track it -- allowlist it in .gitignore and `git add` it"
    )

    probe = subprocess.run(
        ["git", "check-ignore", "-q", "output/not_an_allowlisted_plot.png"],
        cwd=REPO_ROOT,
    )
    assert probe.returncode == 0, (
        "the output/*.png allowlist stopped ignoring anything, so this test no "
        "longer demonstrates that an ignored file is excluded"
    )
    assert "not_an_allowlisted_plot.png" not in committed
