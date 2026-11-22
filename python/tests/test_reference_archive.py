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
"""Guards the reference archive against silent replacement and dead citation.

`references/` holds third-party PDFs that `docs/` quotes: a personal remark, a
13-page objection, and a 940-page draft. Two of the three are the kind that change
without notice -- a draft its author says he is still filling in, and a statement on
a personal site -- so the archive records a hash, and this test enforces it.

Three failure modes are caught:

* a PDF is replaced, revised or truncated: the SHA-256 in `references/README.md`
  stops matching, which is the point of storing the hash at all;
* a file is dropped in the folder and never indexed, or an index entry outlives its
  file, which is how an archive rots into a list of things that used to be there;
* an entry says it is cited by a document that does not actually name it. A record
  that nothing points at is not a reference, it is a download.

What this cannot check is whether the file is what it claims to be. Only reading it
can, and that is what the hashes make possible for a later reader.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_DIR = REPO_ROOT / "references"
INDEX_PATH = REFERENCES_DIR / "README.md"
DOCS_DIR = REPO_ROOT / "docs"

#: The three documents the archive was created for. Named here so that a wholesale
#: replacement of the index -- the way this guard could pass for the wrong reason --
#: fails instead of quietly redefining what "the archive" means.
EXPECTED = (
    "alpoge_remark_2026-11-20.pdf",
    "nielsen_invalidity_2026-11-20.pdf",
    "masullo_music_of_the_primes_2026-11-20.pdf",
)

_SECTION = re.compile(r"^### `([^`]+)`\s*$", re.MULTILINE)
_SHA256 = re.compile(r"^-\s*sha256:\s*`([0-9a-f]{64})`\s*$", re.MULTILINE)
_BYTES = re.compile(r"^-\s*bytes:\s*(\d+)\s*$", re.MULTILINE)
_CITED = re.compile(r"^-\s*cited by:\s*(.+)$", re.MULTILINE)
_DOC = re.compile(r"docs/([\w.-]+\.md)")


def index_text() -> str:
    return INDEX_PATH.read_text(encoding="utf-8")


def records() -> dict[str, str]:
    """`{file name: section body}` for every `### `name.pdf`` heading."""
    text = index_text()
    starts = [(match.start(), match.group(1)) for match in _SECTION.finditer(text)]
    sections: dict[str, str] = {}
    for position, (start, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(text)
        sections[name] = text[start:end]
    return sections


def archived_files() -> set[str]:
    return {path.name for path in REFERENCES_DIR.iterdir() if path.is_file()}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_index_is_parseable():
    """A guard on the guard: the parser must find records, hashes and sizes."""
    sections = records()
    assert len(sections) >= 3, sections
    for name, body in sections.items():
        assert _SHA256.search(body), f"no sha256 recorded for {name}"
        assert _BYTES.search(body), f"no byte count recorded for {name}"
        assert _CITED.search(body), f"no citation recorded for {name}"


def test_the_three_documents_are_indexed():
    """Non-vacuity for the whole file: the archive is about these three."""
    missing = [name for name in EXPECTED if name not in records()]
    assert not missing, (
        "these documents are no longer indexed in references/README.md:\n"
        + "\n".join(f"  {name}" for name in missing)
    )


def test_every_archived_file_is_indexed():
    unindexed = sorted(archived_files() - set(records()) - {"README.md"})
    assert not unindexed, (
        "these files are in references/ but not indexed in references/README.md:\n"
        + "\n".join(f"  {name}" for name in unindexed)
    )


def test_every_indexed_file_exists():
    missing = sorted(name for name in records() if not (REFERENCES_DIR / name).is_file())
    assert not missing, (
        "references/README.md indexes files that are not there:\n"
        + "\n".join(f"  {name}" for name in missing)
    )


@pytest.mark.parametrize("name", EXPECTED)
def test_the_hash_and_the_size_match(name: str):
    """The whole point of the archive: a silent revision becomes a red test.

    Driven against the real file rather than a fixed string, so a legitimate new
    version replaces the recorded hash instead of quietly passing under the old one.
    """
    path = REFERENCES_DIR / name
    assert path.is_file(), f"{name} is missing from references/"
    body = records()[name]
    recorded_hash = _SHA256.search(body)
    recorded_bytes = _BYTES.search(body)
    assert recorded_hash and recorded_bytes

    assert digest(path) == recorded_hash.group(1), (
        f"{name} has changed since it was indexed: the file is not the document "
        f"this repository quotes. Archive the new version under a new name and index "
        f"it, rather than overwriting the recorded hash."
    )
    assert path.stat().st_size == int(recorded_bytes.group(1))


def test_every_record_is_cited_by_a_document_that_names_the_file():
    """A record nothing points at is a download, not a reference.

    The citation must be real in both directions: the indexed document exists, and
    it mentions the PDF by the name the archive stores it under. `docs/` is full of
    prose about these claims; the file name is the checkable part.
    """
    problems: list[str] = []
    for name, body in records().items():
        cited = _CITED.search(body)
        assert cited, name
        documents = _DOC.findall(cited.group(1))
        if not documents:
            problems.append(f"{name}: cites no document under docs/")
            continue
        for document in documents:
            path = DOCS_DIR / document
            if not path.is_file():
                problems.append(f"{name}: cites {document}, which does not exist")
                continue
            if name not in path.read_text(encoding="utf-8"):
                problems.append(f"{name}: {document} never names the file")
    assert not problems, "dead citations in references/README.md:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


def test_the_documentation_points_back_at_the_archive():
    """The archive is discoverable from the reading path, not just from `ls`.

    Both records introduced for these documents, and the triage note that defines the
    repository's standing position, must link to `references/` -- otherwise a reader
    arrives at a claim and never learns that the source is in the tree.
    """
    for document in (
        "alpoge_nielsen_dispute.md",
        "masullo_grh_draft.md",
        "claimed_proof_triage.md",
    ):
        text = (DOCS_DIR / document).read_text(encoding="utf-8")
        assert "references/" in text, (
            f"docs/{document} never points at references/; the archived document it "
            f"quotes is unreachable from it"
        )
