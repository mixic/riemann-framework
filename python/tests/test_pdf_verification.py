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
"""Guards for the typeset manuscript and for the verifier that checks it.

The verifier exists because a build can be wrong in a way no byte-level check of the
object table reveals: an earlier Chrome build had the right page count, the right page
size and four embedded figures, and printed a date header and a `file:///` footer on
every page. These tests keep that guard honest — they run it against the committed PDF,
and they drive the header pattern with the text it is meant to catch.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFIER = PROJECT_ROOT / "scripts" / "verify_pdf.py"
PDF = PROJECT_ROOT / "output" / "desymmetrisation_paper.pdf"

requires_pdf = pytest.mark.skipif(
    not PDF.exists() or not VERIFIER.exists(),
    reason="the built PDF or the verifier is not present",
)


def _load_verifier():
    """Import scripts/verify_pdf.py, which is a script rather than a package module.

    The module has to be registered in `sys.modules` before it is executed: `@dataclass`
    resolves annotations through the module's own entry, and without it the import fails
    with `sys.modules.get(cls.__module__)` being `None`.
    """
    spec = importlib.util.spec_from_file_location("verify_pdf_under_test", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@requires_pdf
def test_the_committed_pdf_passes_its_own_checks():
    """The guard, run the way a reader would run it."""
    result = subprocess.run(
        [sys.executable, str(VERIFIER)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: all" in result.stdout


@requires_pdf
def test_the_reader_recovers_the_title_and_the_author_block():
    """The text layer is readable: a garbled one would fail every content check."""
    verifier = _load_verifier()
    text = verifier.extract_text(PDF)
    assert len(text.pages) == 11
    assert not text.pages_without_text
    assert "DesymmetrizationofQuantumSpectra" in text.flat
    assert "MilanNikolic" in text.flat
    assert "IndependentResearcher" in text.flat


@requires_pdf
def test_the_reader_keeps_fonts_apart():
    """The bug that made the first version useless: one merged table for all fonts.

    LaTeX uses several one-byte fonts whose codes collide, so a merged table turns the
    text into mojibake. The committed PDF uses at least two fonts, and the text is
    readable, which is only possible with per-font tables.
    """
    verifier = _load_verifier()
    text = verifier.extract_text(PDF)
    assert len(text.fonts) >= 2
    assert "theposterior" in text.flat.lower()


def test_the_header_pattern_matches_browser_furniture():
    """Driven with the exact text the Chrome build printed on every page."""
    verifier = _load_verifier()
    assert verifier.HEADER_DATE_FLAT.search("11/1/26,9:34AM")
    assert verifier.HEADER_DATE.search("11/1/26, 9:34 AM")
    assert verifier.HEADER_DATE.search("1/1/26, 8:13 AM")
    assert not verifier.HEADER_DATE.search("no date or time stamp here")
    assert not verifier.HEADER_DATE_FLAT.search("Figure 4 of the manuscript")
