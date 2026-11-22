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
"""Guards that the suite only imports dependencies the repository declares.

The failure this file exists for happened on the first CI run and not locally.
`scripts/audit/three_checks.py` imported `factorint` from sympy -- never used it,
but the import alone makes the module unimportable without sympy -- and
`tests/test_idele_split_lean.py` imports that script to compare its split-prime
certificate against `lean/RiemannFramework/IdeleSplit.lean`. sympy 1.14.0
happens to be installed on the author's machine; CI installs exactly
`python/requirements.txt`, which does not contain it, so the suite was green
here and red there.

Nothing in the repository compared its imports against what it declares, so
drift of this kind could only be found by a machine that lacked the package.
This file makes that comparison local and mechanical. It is the same lesson as
`test_no_package_module_imports_sympy` in `test_graded_prime_monoid.py`, widened
from the package to the scripts, the examples and the tests, and it now covers
every third-party name rather than one.

The scan parses import statements, because a substring search flags the prose
that explains why a dependency was *removed*.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = REPO_ROOT / "python"
REQUIREMENTS = PYTHON_DIR / "requirements.txt"
PYPROJECT = REPO_ROOT / "pyproject.toml"
DECOMPRESS = REPO_ROOT / "scripts" / "audit" / "decompress_export.py"

#: Everything that ships Python in this repository.
SCAN_DIRS = (
    PYTHON_DIR / "riemann_framework",
    PYTHON_DIR / "tests",
    PYTHON_DIR / "examples",
    REPO_ROOT / "scripts",
)

#: Third-party modules imported on purpose, with the reason they are not declared.
#:
#: An entry here is a claim about *where* the dependency is used and *how* its
#: absence behaves; `test_the_optional_dependency_is_explained_and_degrades`
#: checks both, so the allowlist cannot become a place to park an accident.
OPTIONAL: dict[str, str] = {
    "zstandard": (
        "python-zstandard streams the 61.5 GB Lean export once, in "
        "scripts/audit/decompress_export.py. No test needs it, no package module "
        "imports it, and its import is guarded so the script explains itself on a "
        "checkout that lacks it."
    ),
}


def stdlib_names() -> frozenset[str]:
    """The standard library, as this interpreter reports it."""
    return frozenset(sys.stdlib_module_names) | {"__future__"}


def declared_names(path: Path = REQUIREMENTS) -> set[str]:
    """Top-level distribution names from `python/requirements.txt`."""
    names: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name = re.split(r"[<>=!~\[;\s]", line, maxsplit=1)[0].strip().lower()
        if name:
            names.add(name.replace("-", "_"))
    return names


def pyproject_names(path: Path = PYPROJECT) -> set[str]:
    """Distribution names from `pyproject.toml`: dependencies and every extra."""
    import tomllib

    project = tomllib.loads(path.read_text(encoding="utf-8"))["project"]
    requirements: list[str] = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        requirements.extend(group)
    names: set[str] = set()
    for requirement in requirements:
        name = re.split(r"[<>=!~\[;\s]", requirement.strip(), maxsplit=1)[0]
        names.add(name.lower().replace("-", "_").replace(".", "_"))
    return names


def first_party_names() -> set[str]:
    """Names a file in this repository can be imported by without declaring it.

    Scripts are imported by path (the suite does that with `verify_pdf.py` and
    `three_checks.py`), but sibling-module imports by bare name exist too, and a
    guard that did not know about them would fail on the repository's own code.
    """
    names: set[str] = set()
    for base in (PYTHON_DIR, REPO_ROOT / "scripts"):
        for path in base.rglob("*.py"):
            names.add(path.stem)
        for path in base.rglob("*"):
            if path.is_dir() and any(path.glob("*.py")):
                names.add(path.name)
    return names


def _label(path: Path, root: Path) -> str:
    """A repository-relative POSIX path when the file is in the repository.

    Paths are normalised so the guard's report reads the same on Windows and on
    the Linux runner, and a file outside the repository (the driven test writes
    one into a temporary directory) is still labelled and not silently dropped.
    """
    for base in (REPO_ROOT, root):
        try:
            return path.relative_to(base).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def imported_names(root: Path) -> dict[str, set[str]]:
    """`{top-level module: files importing it}` under `root`."""
    found: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # a relative import is inside the package
                    continue
                names = [(node.module or "").split(".")[0]]
            for name in filter(None, names):
                found.setdefault(name, set()).add(_label(path, root))
    return found


def undeclared_imports(root: Path) -> dict[str, set[str]]:
    """Imports that are not stdlib, not declared, not first-party, not optional."""
    allowed = stdlib_names() | declared_names() | first_party_names() | set(OPTIONAL)
    return {name: files for name, files in imported_names(root).items() if name not in allowed}


def test_every_import_is_standard_library_or_declared():
    """The guard proper, over the package, the tests, the examples and the scripts."""
    offenders: dict[str, set[str]] = {}
    for base in SCAN_DIRS:
        assert base.is_dir(), base
        for name, files in undeclared_imports(base).items():
            offenders.setdefault(name, set()).update(files)

    assert not offenders, (
        "these imports are neither in the standard library nor in "
        "python/requirements.txt, so CI fails while this disk passes:\n"
        + "\n".join(
            f"  {name}: " + ", ".join(sorted(files)) for name, files in sorted(offenders.items())
        )
        + "\nEither delete the import or declare the dependency; if it is genuinely "
        "optional, add it to OPTIONAL with the reason its absence behaves."
    )


def test_the_declared_set_is_parsed_from_the_requirements_file():
    """Non-vacuity: if the parser returned nothing, every check above would pass."""
    declared = declared_names()
    assert declared == {"mpmath", "numpy", "scipy", "matplotlib", "pytest"}, declared


def test_the_requirements_file_and_the_metadata_declare_the_same_set():
    """Two files say what to install, so they have to say the same thing.

    CI installs `python/requirements.txt`; a reader who runs `pip install .` gets
    `pyproject.toml`'s declaration plus its extras. If the two drift, one of them
    is describing an environment that does not exist, and the guard above would
    pass in whichever one it consulted. This test makes the drift loud.
    """
    declared_pyproject = pyproject_names()
    assert declared_pyproject == declared_names(), (
        "python/requirements.txt and pyproject.toml disagree about what to install: "
        f"requirements only {sorted(declared_names() - declared_pyproject)}, "
        f"metadata only {sorted(declared_pyproject - declared_names())}"
    )


def test_the_scanner_finds_the_known_third_party_imports():
    """Non-vacuity for the AST scan itself: it must see the declared dependencies."""
    seen = set(imported_names(PYTHON_DIR / "riemann_framework"))
    assert {"mpmath", "numpy"} <= seen, sorted(seen)
    assert "zstandard" in imported_names(REPO_ROOT / "scripts")


def test_the_scanner_flags_an_undeclared_import(tmp_path):
    """Driven at the historical failure: the import that made CI red.

    A file that imports `factorint` from sympy is written into a temporary tree
    and must be reported, along with the file that holds the import.
    """
    offender = tmp_path / "three_checks_regression.py"
    offender.write_text(
        "\"\"\"The shape of the import that broke CI.\"\"\"\nfrom sympy import factorint\n",
        encoding="utf-8",
    )

    flagged = undeclared_imports(tmp_path)
    assert set(flagged) == {"sympy"}, flagged
    assert flagged["sympy"], "the offending file was not recorded"


def test_the_optional_dependency_is_explained_and_degrades():
    """`zstandard` is imported in one place, with a reason, and absence is survivable.

    The check runs the module with `zstandard` blocked, which is the state CI is
    in. A bare import would raise `ModuleNotFoundError` from the module body, and
    an unguarded call would raise `AttributeError` from `zstd.ZstdDecompressor`;
    both are worse than a message that names the package.
    """
    holders = imported_names(REPO_ROOT / "scripts").get("zstandard", set())
    assert holders == {"scripts/audit/decompress_export.py"}, holders
    assert OPTIONAL["zstandard"].strip(), "an OPTIONAL entry without a reason is a silencer"

    spec = importlib.util.spec_from_file_location("decompress_export_without_zstandard", DECOMPRESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        with mock.patch.dict(sys.modules, {"zstandard": None}):
            spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)

    assert module.zstd is None
    with pytest.raises(SystemExit) as excinfo:
        module.decompress(Path("export.ndjson.zst"), Path("export.ndjson"))
    message = str(excinfo.value)
    assert "zstandard" in message and "pip install" in message, message
