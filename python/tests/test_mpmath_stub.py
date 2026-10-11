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
"""Guards on the hand-written `mpmath` stub.

`typings/mpmath/__init__.pyi` is the **only** view any type checker has of
`mpmath` in this repository: `pyrightconfig.json` sets `stubPath`, and pyright
reports the consequence itself as `reportMissingModuleSource` -- it resolves
`mpmath` to the stub, never to the installed package. So every name the stub
omits becomes an editor error in whatever module uses it.

That has happened three times, each found in Pylance rather than in CI:

  `workdps`   the DH filter and its tests
  `floor`     the imaginary-time and prime-orbit modules
  `nstr`      not missing, but declared `n: int = ...`, which some checkers
              reject as assigning `EllipsisType` to `int`

Two checks follow, and both are factored so a test can drive them into failing:
a check that cannot fail is not evidence of anything, which is the same standard
the rest of the suite is held to. Neither check needs a third-party dependency
beyond pytest, and between them they run in well under a second.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
STUB_PATH = REPO_ROOT / "typings" / "mpmath" / "__init__.pyi"

#: Directories whose `mp.*` usage the stub has to cover. `python/` is the package
#: and its tests; `scripts/` is checked too, because pyright analyses the whole
#: tree and a runner is as capable of hitting a missing name as a module.
SCAN_DIRS = (REPO_ROOT / "python", REPO_ROOT / "scripts")

#: The alias every module in this repository uses for `mpmath`.
ALIAS = "mp"


# ============================================================
# Parsing the stub
# ============================================================

def parse_stub(source: str) -> ast.Module:
    """Parse stub source, raising a readable error if it is malformed."""
    try:
        return ast.parse(source)
    except SyntaxError as exc:  # pragma: no cover - only on a broken stub
        raise AssertionError(f"{STUB_PATH} does not parse: {exc}") from exc


def declared_names(tree: ast.Module) -> set[str]:
    """Module-level names the stub defines.

    Functions (`def workdps`), classes (`class mpf`), and annotated or plain
    assignments (`pi: Any`). Class *members* are deliberately not collected: a
    call site can only reach what is attached to the module.
    """
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            names.update(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
    return names


# ============================================================
# Check 1: coverage
# ============================================================

def find_mp_usages(directories=SCAN_DIRS) -> dict[str, set[str]]:
    """Every `mp.<name>` attribute access in the tree, mapped to its files.

    Walks the **AST** rather than scanning text, so `mp.workdps` inside a
    docstring or a comment is not mistaken for a call site. A text scan was what
    produced the earlier one-off survey; this is stricter and cannot be fooled by
    prose.
    """
    usages: dict[str, set[str]] = {}
    for directory in directories:
        for path in sorted(directory.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):  # pragma: no cover
                continue
            relative = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == ALIAS
                ):
                    usages.setdefault(node.attr, set()).add(relative)
    return usages


def missing_names(usages: dict[str, set[str]], declared: set[str]) -> dict[str, set[str]]:
    """The used-and-not-declared subset, keeping the files for the message."""
    return {name: files for name, files in usages.items() if name not in declared}


# ============================================================
# Check 2: well-formedness of defaults
# ============================================================

def _is_ellipsis(node: ast.expr | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is Ellipsis


def _is_typed_beyond_any(arg: ast.arg) -> bool:
    """True when the parameter carries an annotation other than bare `Any`.

    `Any = ...` is the safe stub idiom: `Any` accepts `EllipsisType`. A narrower
    annotation does not, which is the whole failure mode this check exists for.
    """
    annotation = arg.annotation
    if annotation is None:
        return False
    return not (isinstance(annotation, ast.Name) and annotation.id == "Any")


def typed_ellipsis_defaults(tree: ast.Module) -> list[str]:
    """Parameters annotated with a concrete type that default to `...`.

    Returns `function(parameter)` strings, so a failure names the offender rather
    than just the file. Handles positional, keyword-only, and the tail alignment
    of `args.defaults` against the positional parameters.
    """
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args
        positional = list(getattr(args, "posonlyargs", [])) + list(args.args)
        # `defaults` lines up with the TAIL of the positional parameters.
        offset = len(positional) - len(args.defaults)
        for index, default in enumerate(args.defaults):
            parameter = positional[offset + index]
            if _is_ellipsis(default) and _is_typed_beyond_any(parameter):
                offenders.append(f"{node.name}({parameter.arg})")
        for parameter, default in zip(args.kwonlyargs, args.kw_defaults):
            if default is not None and _is_ellipsis(default) and _is_typed_beyond_any(parameter):
                offenders.append(f"{node.name}({parameter.arg})")
    return offenders


# ============================================================
# The stub as it is
# ============================================================

def test_the_stub_exists_and_parses():
    assert STUB_PATH.exists(), f"missing {STUB_PATH}"
    parse_stub(STUB_PATH.read_text(encoding="utf-8"))


def test_every_used_mpmath_name_is_declared():
    """The coverage guard, and what would have caught `workdps` and `floor`.

    A missing name is invisible until something uses it, at which point it
    surfaces in the editor of whoever wrote that line. This moves the discovery
    into CI, where it belongs.
    """
    declared = declared_names(parse_stub(STUB_PATH.read_text(encoding="utf-8")))
    missing = missing_names(find_mp_usages(), declared)
    assert not missing, (
        "these `mp.` names are used in the tree but not declared in "
        f"{STUB_PATH.relative_to(REPO_ROOT)}, so a checker cannot resolve them:\n"
        + "\n".join(
            f"  mp.{name}  used in {', '.join(sorted(files))}"
            for name, files in sorted(missing.items())
        )
    )


def test_no_typed_parameter_defaults_to_ellipsis():
    """The well-formedness guard, and what would have caught the `nstr` error.

    `def nstr(x: Any, n: int = ...)` was rejected by Pylance with "Expression of
    type EllipsisType cannot be assigned to parameter of type int". The idiom is
    fine when the parameter is `Any`; it is not when it is `int`.
    """
    tree = parse_stub(STUB_PATH.read_text(encoding="utf-8"))
    offenders = typed_ellipsis_defaults(tree)
    assert not offenders, (
        "these parameters are annotated with a concrete type but default to `...`, "
        "which a checker may reject as assigning EllipsisType to that type:\n"
        + "\n".join(f"  {name}" for name in offenders)
        + "\n  Give the real default instead, as `nstr(x: Any, n: int = 6)` does."
    )


def test_the_stub_declares_something_substantial():
    """A guard on the guards: an empty or truncated stub would pass both.

    If the stub were replaced by a stub with no declarations, the coverage check
    would fail loudly -- but if it were replaced by one declaring only `Any`, the
    coverage check could pass vacuously while every annotation was gone. This
    pins that the stub still describes the API.
    """
    declared = declared_names(parse_stub(STUB_PATH.read_text(encoding="utf-8")))
    for required in ("mpf", "mpc", "nstr", "zeta", "workdps", "pi", "e", "mp"):
        assert required in declared, f"{required} vanished from the stub"
    assert len(declared) > 20


# ============================================================
# The checks can fail
# ============================================================

def test_the_coverage_check_detects_a_missing_name():
    """Driven into failing, so the passing run above means something."""
    usages = {"workdps": {"python/x.py"}, "zeta": {"python/y.py"}}
    declared = {"zeta"}
    assert missing_names(usages, declared) == {"workdps": {"python/x.py"}}


def test_the_coverage_check_would_flag_the_real_regressions():
    """The three names that actually went missing, replayed against a stub."""
    usages = {name: {"python/x.py"} for name in ("workdps", "floor", "arg", "fsum")}
    declared = {"zeta", "mpf"}  # as the stub was before the fixes
    assert set(missing_names(usages, declared)) == {"workdps", "floor", "arg", "fsum"}


def test_the_ellipsis_check_detects_the_nstr_construction():
    """The exact shape that was in the stub, and must never come back."""
    bad = ast.parse("def nstr(x: Any, n: int = ..., **kwargs: Any) -> str: ...")
    assert typed_ellipsis_defaults(bad) == ["nstr(n)"]


def test_the_ellipsis_check_allows_the_two_legitimate_forms():
    """It must not fire on these, or it would be noise rather than a guard."""
    good = ast.parse(
        "def a(x: Any = ...) -> Any: ...\n"           # `Any` accepts Ellipsis
        "def b(x: Any, n: int = 6) -> str: ...\n"     # a real default
    )
    assert typed_ellipsis_defaults(good) == []


def test_the_ellipsis_check_catches_a_keyword_only_offender():
    tree = ast.parse("def c(x: Any, *, flag: bool = ...) -> Any: ...")
    assert typed_ellipsis_defaults(tree) == ["c(flag)"]


def test_the_ellipsis_check_separates_a_mixed_default_list():
    """One offender and one real default in the same list, plus an undefaulted head.

    The first draft of this test expected only the keyword-only offender and was
    wrong: `d(n)` is a genuine offence. The checker was right and the expectation
    was not, which is the useful direction for that to go.
    """
    tree = ast.parse("def d(x: Any, n: int = ..., m: int = 3) -> Any: ...")
    assert typed_ellipsis_defaults(tree) == ["d(n)"]


def test_the_ellipsis_check_aligns_defaults_to_the_tail():
    """`defaults` lines up with the LAST positional parameters, not the first.

    Getting this wrong would misreport which parameter is at fault, or miss one
    entirely, on any signature with a mix of defaulted and undefaulted arguments.
    """
    tree = ast.parse("def f(a: int, b: Any = ..., c: int = ...) -> None: ...")
    assert typed_ellipsis_defaults(tree) == ["f(c)"]


def test_the_scanner_finds_names_through_the_ast():
    """Non-vacuity: the scanner actually reads the tree it is pointed at."""
    usages = find_mp_usages()
    assert usages, "no `mp.*` usage found at all -- is SCAN_DIRS wrong?"
    assert "zeta" in usages
    assert any("riemann_framework" in f for f in usages["zeta"])
    # `mp.mp.dps` reaches the stub through `mp`, not through a second name.
    assert "mp" in usages


def test_the_scanner_ignores_names_in_comments_and_strings():
    """AST-based, so prose about `mp.something` is not a call site.

    The pre-fix survey was a text regex, which would have counted these.
    """
    source = (
        "# mentions mp.not_a_real_name in a comment\n"
        'DOC = "and mp.also_not_real in a string"\n'
        "value = mp.zeta(2)\n"
    )
    tree = ast.parse(source)
    found = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == ALIAS
    }
    assert found == {"zeta"}
