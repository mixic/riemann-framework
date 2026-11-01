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
"""Guards on the manuscript's figure references.

A figure line is `![caption](path)`. Three things can go wrong with one, and each has
bitten this build:

* the same figure is referenced twice, so a converter can emit two copies, and a
  truncated second copy renders as a stream of axis numbers rather than an image;
* the path names a file that does not exist, which renders as a missing-image box;
* the caption does not start with `Fig. N.`, which makes the text references
  ("(Fig. 3)") point at the wrong place.

These are tests rather than a rewriting script on purpose: prose is edited by hand, and
a tool that silently deletes a line from a manuscript is riskier than a test that says
which line is wrong.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANUSCRIPT = PROJECT_ROOT / "docs" / "desymmetrisation_paper.md"

#: The four figures the manuscript is built around, in order.
EXPECTED = (
    ("Fig. 1.", "output/desymmetrisation.png"),
    ("Fig. 2.", "output/desymmetrisation_warning.png"),
    ("Fig. 3.", "output/desymmetrisation_coverage.png"),
    ("Fig. 4.", "output/desymmetrisation_flow.png"),
)

#: A figure line. The caption is greedy because captions contain square brackets
#: ("the Poisson window [0.36, 0.41]"), which a `[^\]]*` pattern cannot match — the
#: first version of this guard silently missed Fig. 1 for exactly that reason.
IMAGE_LINE = re.compile(r"^\s*!\[(.*)\]\(([^()]+)\)\s*$")


def _figure_lines() -> list[tuple[int, str, str]]:
    """`(line number, caption, path)` for every figure line in the manuscript."""
    found = []
    for number, line in enumerate(MANUSCRIPT.read_text(encoding="utf-8").splitlines(), 1):
        match = IMAGE_LINE.match(line)
        if match:
            found.append((number, match.group(1), match.group(2).strip()))
    return found


def test_the_manuscript_has_exactly_the_four_figures():
    lines = _figure_lines()
    assert len(lines) == 4, (
        f"expected four figure lines, found {len(lines)}: "
        + ", ".join(f"line {number}" for number, _, _ in lines)
    )
    assert [(caption[:7], path) for _, caption, path in lines] == list(EXPECTED)


def test_no_figure_is_referenced_twice():
    """A duplicate reference is how a page came to be filled with axis numbers."""
    paths = Counter(path for _, _, path in _figure_lines())
    duplicated = {path: count for path, count in paths.items() if count > 1}
    assert not duplicated, f"duplicated figure paths: {duplicated}"


def test_every_referenced_figure_exists():
    missing = [
        (number, path)
        for number, _, path in _figure_lines()
        if not (PROJECT_ROOT / path).exists()
    ]
    assert not missing, f"figure files missing on disk: {missing}"
    for _, caption, path in _figure_lines():
        header = (PROJECT_ROOT / path).read_bytes()[:8]
        assert header == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"


def test_the_captions_are_numbered_and_ordered():
    captions = [caption for _, caption, _ in _figure_lines()]
    for index, caption in enumerate(captions, start=1):
        assert caption.startswith(f"Fig. {index}."), (
            f"caption {index} starts {caption[:20]!r}, expected 'Fig. {index}.'"
        )
        assert len(caption) > 80, f"caption {index} is too short to be self-contained"
