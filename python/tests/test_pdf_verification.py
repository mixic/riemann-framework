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


def test_the_placement_reader_separates_natural_from_effective_size():
    """Driven with the byte pattern that produced the page-6 failure.

    A 1500-pixel figure at 150 dpi is 720pt wide; `width=\\linewidth` wraps it in a
    0.66 scale, so the effective width is right and the natural width is not. A viewer
    that ignores the outer matrix draws 720pt on a 595pt page.
    """
    verifier = _load_verifier()
    snippet = (
        b"q 0.66142 0 0 0.66142 0 0 cm q 720 0 0 432 0 0 cm /Im3 Do Q Q"
    )
    placed = verifier.image_placements(snippet)
    assert len(placed) == 1
    name, inner, effective, _, _ = placed[0]
    assert name == "Im3"
    assert inner == pytest.approx(720.0)
    assert effective == pytest.approx(476.2, abs=0.5)
    assert inner > verifier.PAGE_WIDTH, "the natural width must be recognisable as too wide"
    assert effective <= verifier.TEXT_WIDTH + 1.0


@requires_pdf
def test_the_figures_are_placed_inside_the_text_block():
    """The committed build: effective width fits the block, natural width fits the page."""
    verifier = _load_verifier()
    data = PDF.read_bytes()
    objects = verifier._objects(data)
    placements = []
    for number, body in objects.items():
        if not verifier.re.search(rb"/Type\s*/Page\b(?!s)", body):
            continue
        payload = b""
        for reference in verifier._refs(body, b"Contents"):
            payload += verifier._stream(objects.get(reference, b"")) or b""
        placements.extend(verifier.image_placements(payload))
    assert len(placements) == 4
    for name, inner, effective, _, _ in placements:
        assert effective <= verifier.TEXT_WIDTH + 1.0, name
        assert inner <= verifier.PAGE_WIDTH + 1.0, name
