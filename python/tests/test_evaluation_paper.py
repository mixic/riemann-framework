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
"""Guards the evaluation paper against the two failures that would matter.

A paper about verdicts that is itself unverifiable is worthless, so this file pins
the parts of `paper/evaluation_protocol.pdf` that a reader could be misled by:

* the sentence that keeps the Riemann hypothesis open has to survive editing -- if an
  author (or a language model) rewrites it into a claim, the suite goes red;
* the vocabulary has to stay the six-verdict one, with no word meaning "true";
* the hashes the paper prints have to be the hashes of the archived files, byte for
  byte, because a paper quoting a stale hash is quoting a document nobody can find;
* the PDF has to be the compiled one, not a placeholder.

What the test cannot check is whether the verdicts are correct. That is what the
paper's own falsification criteria are for, and they are printed in it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = REPO_ROOT / "paper"
PDF = PAPER_DIR / "evaluation_protocol.pdf"
TEX = PAPER_DIR / "evaluation_protocol.tex"
REFERENCES = REPO_ROOT / "references"
VERIFIER = REPO_ROOT / "scripts" / "verify_pdf.py"


def _load_verifier():
    """Import `scripts/verify_pdf.py`, which is a script rather than a package module.

    Same loader as `test_pdf_verification.py`, for the same reason: `@dataclass` resolves
    annotations through the module's own `sys.modules` entry, so the module must be
    registered before it is executed.
    """
    spec = importlib.util.spec_from_file_location("verify_pdf_for_paper", VERIFIER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: Sentences whose disappearance would turn the paper into a claim.
OPEN_SENTENCE = "TheRiemannhypothesisremainsopen"

#: Phrases that would mean the paper had made the claim it exists to avoid.
FORBIDDEN = (
    "weprovetheRiemannhypothesis",
    "provestheRiemannhypothesis",
    "Riemannhypothesisisproved",
    "disprovestheRiemannhypothesis",
    "settlesRH",
)


@pytest.fixture(scope="module")
def paper_text() -> str:
    """The PDF's text layer, flattened the way the other PDF checks flatten it."""
    return _load_verifier().extract_text(PDF).flat


def test_the_pdf_is_the_compiled_paper() -> None:
    """A real article, not a stub: page count and text-layer size both checked.

    Numbers are lower bounds with the observed values written into the message, so a
    regeneration that drops a section fails here rather than passing silently.
    """
    assert PDF.is_file(), f"{PDF} is missing"
    text = _load_verifier().extract_text(PDF)
    assert len(text.pages) >= 12, f"paper is {len(text.pages)} pages"
    assert len(text.text) >= 30_000, f"text layer is {len(text.text)} characters"
    assert text.pages_without_text == [], text.pages_without_text


def test_the_paper_keeps_the_hypothesis_open(paper_text: str) -> None:
    """The one sentence that must not be edited away."""
    assert OPEN_SENTENCE in paper_text, (
        "the paper no longer states that the Riemann hypothesis remains open; this is "
        "the sentence the whole document is disciplined around"
    )


def test_the_paper_makes_no_claim_of_a_proof(paper_text: str) -> None:
    """The failure mode this repository keeps guarding against, in the paper itself."""
    hits = [phrase for phrase in FORBIDDEN if phrase in paper_text]
    assert not hits, f"the paper contains a proof claim: {hits}"


def test_the_verdict_vocabulary_has_no_word_meaning_true(paper_text: str) -> None:
    """Every verdict word is present, and none of them means 'true'.

    The vocabulary is the paper's method: `rejected`, `outside domain`,
    `undetermined`, `validated (finite)`, `validated (elementary)`, `validated (term)`. If a later edit
    adds `confirmed`, the test cannot see it, but it can see that the five are there
    and that the abstract's two hardest verdicts are used in the body.
    """
    for word in ("rejected", "outsidedomain", "undetermined", "validated(finite)",
                 "validated(elementary)", "validated(term)"):
        assert word in paper_text, word
    assert "outsideeverydomain" in paper_text


def test_the_printed_hashes_are_the_archived_hashes() -> None:
    """The paper's evidence table is checked against the files it indexes.

    The `.tex` prints the first 16 hex digits of each document's SHA-256; the files
    are in `references/`. A regenerated paper that quotes an old hash, or a replaced
    PDF, makes this fail -- which is the point of both the hash and the test.
    """
    tex = TEX.read_text(encoding="utf-8")
    pairs = (
        ("alpoge_remark_2026-11-20.pdf", "3fc97784b71ddd44"),
        ("nielsen_invalidity_2026-11-20.pdf", "2f8bd3c47c211457"),
        ("masullo_music_of_the_primes_2026-11-20.pdf", "e039d3f6cf0a4b14"),
    )
    for name, prefix in pairs:
        assert prefix in tex, f"{prefix} is not quoted in the paper"
        path = REFERENCES / name
        assert path.is_file(), f"{name} is not archived"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest.startswith(prefix), (
            f"{name} hashes to {digest[:16]}, but the paper quotes {prefix}"
        )


def test_the_falsification_criteria_are_printed(paper_text: str) -> None:
    """A study that cannot fail is not a study, so the fail conditions are in the PDF."""
    assert "Pre-registeredfalsificationcriteriaforthisstudy" in paper_text or (
        "falsificationcriteria" in paper_text
    )
    assert "beoverturnedby" in paper_text


def test_the_paper_names_the_repository_it_was_computed_from(paper_text: str) -> None:
    """Reproducibility claim: the commands and the file names must appear.

    `claims/` is in the list because the appendix describing the audit agent names the
    directory its records live in: a paper that described the procedure and not its input
    would be describing a method with nothing to run on.
    """
    for token in ("pythonscripts/run_dh_filter.py", "1424tests", "references/",
                  "ideas/", "claims/"):
        assert token.replace(" ", "") in paper_text.replace(" ", ""), token
