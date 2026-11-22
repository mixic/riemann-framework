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
"""Reconcile the hypotheses a document mentions against the ones its declaration lists.

The Davenport--Heilbronn and circularity screens read a *declaration*: what the author says
the argument uses, with a section reference. Section 6 of the evaluation paper records the
failure mode of that design -- an omitted input moves the verdict without changing the
argument -- and the mitigation given there is that an unclassifiable key degrades to
`unscreened` rather than passing. That mitigation covers a *wrong* declaration; it does not
cover a *silent* one, where the input is simply not mentioned in the declaration and the
screen never sees it.

This module adds the missing half. It scans the text of the primary document for the
inventory's own vocabulary and reports every hypothesis the text mentions, dividing the
mentions into three classes:

* **declared** -- listed in `trace_formula_screen.DECLARED`, with the section reference;
* **excluded** -- listed in `trace_formula_screen.NOT_DECLARED`, with a reason the author of
  the declaration states (e.g. the draft says it does not use Li's criterion);
* **unreconciled** -- mentioned in the text and absent from both lists. This is the failure
  the check exists to find: a hypothesis the argument names that the declaration does not
  account for either way.

The output is a reconciliation, not a verdict. A mention is not a use: a draft may discuss
Hadamard factorisations in order to set them aside, and this module cannot tell the two apart.
What it can do is make the difference visible and force it to be resolved in writing, which
is the difference between "the declaration was complete as far as we looked" and "the
declaration was complete".

The phrase lists are a heuristic, and are declared as one. They are matched
case-insensitively on word boundaries, so a paraphrase that avoids every listed phrase is
invisible here; the limits paragraph of the CLI says so, and the paper does not report the
result as a verdict.

No output of this module is evidence for or against the Riemann hypothesis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .trace_formula_screen import DECLARED, NOT_DECLARED, DeclaredInput

#: Textual vocabulary per inventory key. Matched case-insensitively on word boundaries.
#: A key with no phrase cannot be found, so the lists are kept exhaustive over the ways the
#: three documents read here name each hypothesis; a new source may need a new phrase, and
#: that is a change to the instrument rather than to its result.
PHRASES: dict[str, tuple[str, ...]] = {
    "functional_equation": ("functional equation", "functional equations"),
    "real_coefficients": ("real coefficients", "real-valued coefficients"),
    "zero_symmetry": ("zero symmetry", "symmetric zero", "zeros come in"),
    # "Hadamard" alone is not enough: the draft's three references are to Hadamard's Lemma
    # and to Hadamard--de la Vallee Poussin, neither of which is the factorisation row.
    "hadamard_product": ("hadamard product", "hadamard factori", "hadamard factorization"),
    "euler_product": ("euler product", "euler products"),
    "explicit_formula_prime_side": (
        "explicit formula",
        "explicit formulas",
        "prime side",
        "weil's explicit",
        "weil explicit",
    ),
    "li_positivity": (
        "li's criterion",
        "li criterion",
        "li's positivity",
        "positivity criterion",
        "lambda_n",
    ),
    "riemann_von_mangoldt_count": (
        "riemann-von mangoldt",
        "riemann von mangoldt",
        "zero-counting",
        "zero counting",
    ),
    "gue_pair_correlation": ("pair correlation", "pair correlations", "gue"),
}


@dataclass(frozen=True)
class Mention:
    """How often one hypothesis is named in a text, and by which phrases."""

    key: str
    count: int
    phrases: tuple[str, ...]

    def summary(self) -> dict[str, object]:
        return {"key": self.key, "count": self.count, "phrases": list(self.phrases)}


@dataclass(frozen=True)
class Reconciliation:
    """The three classes of mention, plus the inventory keys the text never names.

    `status` is `unreconciled` when any mention falls outside both ledgers, `no_mentions`
    when the text names none of the inventory's hypotheses, and `reconciled` otherwise. The
    `no_mentions` case is reported as a distinct status rather than as success: a scan that
    finds nothing has not shown the declaration to be complete, it has shown that the
    instrument did not engage with the document.
    """

    declared: tuple[Mention, ...]
    excluded: tuple[Mention, ...]
    unreconciled: tuple[Mention, ...]
    unmentioned: tuple[str, ...]
    status: str

    @property
    def total_mentions(self) -> int:
        return sum(item.count for item in (*self.declared, *self.excluded, *self.unreconciled))

    def summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "total_mentions": self.total_mentions,
            "declared": [item.summary() for item in self.declared],
            "excluded": [item.summary() for item in self.excluded],
            "unreconciled": [item.summary() for item in self.unreconciled],
            "unmentioned": list(self.unmentioned),
        }


def _pattern(phrase: str) -> re.Pattern[str]:
    """A word-boundary pattern that tolerates the ways PDF text breaks a phrase.

    Extracted text writes a hyphenated line break as ``prod-\\nuct`` and a compound as
    ``Euler-product`` or ``Euler product`` interchangeably; a literal search for
    ``Euler product`` finds 13 occurrences where the normalised text contains 57. The
    normalisation is therefore part of the instrument and is tested separately.
    """
    parts = [re.escape(part) for part in phrase.split()]
    body = r"[\s\-]+".join(parts)
    return re.compile(rf"(?<![a-z]){body}(?![a-z])", re.IGNORECASE)


def normalise(text: str) -> str:
    """Fold line breaks that split a phrase, the typographic apostrophe, and extra spaces.

    A hyphen at the end of a line becomes a hyphen, not a deletion: in this corpus the
    hyphen is usually the one in `Euler-product` or `functional-equation`, and the
    pattern builder already accepts a hyphen or a space between the words of a phrase.
    A word hyphenated *inside* a single-word phrase is not recovered, which is the limit
    of a lexicographic instrument and is stated in the module docstring.
    """
    text = text.replace("\u2019", "'")
    text = re.sub(r"-\s*\n\s*", "-", text)
    return re.sub(r"[ \t]+", " ", text)


def scan(text: str) -> dict[str, Mention]:
    """`{key: Mention}` for every inventory key whose vocabulary occurs in `text`."""
    text = normalise(text)
    found: dict[str, Mention] = {}
    for key, phrases in PHRASES.items():
        matched: list[str] = []
        count = 0
        for phrase in phrases:
            hits = len(_pattern(phrase).findall(text))
            if hits:
                matched.append(phrase)
                count += hits
        if count:
            found[key] = Mention(key=key, count=count, phrases=tuple(matched))
    return found


def reconcile(
    text: str,
    *,
    declared: tuple[DeclaredInput, ...] = DECLARED,
    excluded: tuple[DeclaredInput, ...] = NOT_DECLARED,
) -> Reconciliation:
    """Classify every mention the text contains, and report what it never names."""
    mentions = scan(text)
    declared_keys = {item.key for item in declared}
    excluded_keys = {item.key for item in excluded}

    declared_mentions = tuple(mentions[key] for key in sorted(declared_keys & set(mentions)))
    excluded_mentions = tuple(mentions[key] for key in sorted(excluded_keys & set(mentions)))
    unreconciled = tuple(
        mentions[key] for key in sorted(set(mentions) - declared_keys - excluded_keys)
    )
    unmentioned = tuple(sorted(set(PHRASES) - set(mentions)))

    if not mentions:
        status = "no_mentions"
    elif unreconciled:
        status = "unreconciled"
    else:
        status = "reconciled"
    return Reconciliation(
        declared=declared_mentions,
        excluded=excluded_mentions,
        unreconciled=unreconciled,
        unmentioned=unmentioned,
        status=status,
    )


def ledger() -> dict[str, dict[str, str]]:
    """The declaration and the exclusions, as `{key: {where, why}}`, for a printed report."""
    out: dict[str, dict[str, str]] = {}
    for item in DECLARED:
        out[item.key] = {"role": "declared", "where": item.where, "why": item.why}
    for item in NOT_DECLARED:
        out[item.key] = {"role": "excluded", "where": item.where, "why": item.why}
    return out
