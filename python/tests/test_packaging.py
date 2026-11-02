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
"""Packaging guards: the metadata, the dependency list, and the one version.

These parse the real files rather than restating them. The check that matters most is
`test_every_third_party_import_is_declared`: a module that imports `scipy` while
`pyproject.toml` does not mention it installs cleanly and fails at first use, which is the
packaging version of the drift the documentation guard exists to catch.
"""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
PACKAGE_DIR = PROJECT_ROOT / "python" / "riemann_framework"
INIT_FILE = PACKAGE_DIR / "__init__.py"


def metadata() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def declared_dependencies() -> set[str]:
    """Every distribution named anywhere in the project table, extras included."""
    project = metadata()["project"]
    names: set[str] = set()
    for requirement in project.get("dependencies", []):
        names.add(_distribution_name(requirement))
    for group in project.get("optional-dependencies", {}).values():
        for requirement in group:
            names.add(_distribution_name(requirement))
    return names


def _distribution_name(requirement: str) -> str:
    """`numpy>=1.26` -> `numpy`; `mpmath` -> `mpmath`."""
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    if match is None:  # pragma: no cover - the requirements are literals
        raise ValueError(f"cannot read a distribution name from {requirement!r}")
    return match.group(1).lower().replace("-", "_").replace(".", "_")


def third_party_imports() -> set[str]:
    """Top-level module names imported anywhere in the package, minus stdlib and self."""
    roots: set[str] = set()
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    roots.add(node.module.split(".")[0])
    standard = set(sys.stdlib_module_names)
    return {
        name
        for name in roots
        if name not in standard and name not in {"riemann_framework", "__future__"}
    }


def test_the_metadata_loads():
    project = metadata()["project"]
    assert project["name"] == "riemann-framework"
    assert project["requires-python"].startswith(">=")
    assert "version" in project["dynamic"]


def test_the_version_has_one_source():
    """`__init__.py` owns the version and the backend reads it from there."""
    project = metadata()["project"]
    attribute = metadata()["tool"]["setuptools"]["dynamic"]["version"]["attr"]
    assert attribute == "riemann_framework.__version__"

    source = INIT_FILE.read_text(encoding="utf-8")
    match = re.search(r'^__version__ = "([^"]+)"$', source, re.MULTILINE)
    assert match is not None, "the package version is not a simple assignment"
    assert re.fullmatch(r"\d+\.\d+\.\d+", match.group(1)), match.group(1)
    assert "version" not in project, "the version is declared twice"


def test_the_licence_matches_the_licence_file():
    project = metadata()["project"]
    assert project["license"] == "GPL-3.0-or-later"
    assert project["license-files"] == ["LICENSE"]
    licence = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in licence
    assert "Version 3" in licence


def test_every_third_party_import_is_declared():
    """The guard that catches a module using a library the package does not install."""
    imported = third_party_imports()
    declared = declared_dependencies()
    missing = sorted(imported - declared)
    assert not missing, (
        "these modules are imported by the package but no requirement declares them:\n"
        + "\n".join(f"  {name}" for name in missing)
    )


def test_the_declared_package_directory_holds_every_module():
    package_dir = metadata()["tool"]["setuptools"]["package-dir"]["riemann_framework"]
    declared = PROJECT_ROOT / package_dir
    assert declared == PACKAGE_DIR
    assert INIT_FILE.exists(), "a package directory needs an __init__.py to install"
    modules = {path.stem for path in PACKAGE_DIR.glob("*.py")}
    assert len(modules) >= 30, sorted(modules)
    assert modules >= {"statistics", "desymmetrisation", "boundary_map", "diagnose"}


def test_the_readme_is_the_declared_description():
    project = metadata()["project"]
    assert project["readme"] == "README.md"
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Riemann Framework")


def test_the_extras_cover_the_plotting_layer():
    """matplotlib is an extra, so the plotting modules need it listed somewhere."""
    imported = third_party_imports()
    extras = metadata()["project"]["optional-dependencies"]
    plotting = {_distribution_name(item) for item in extras.get("plots", [])}
    assert "matplotlib" in imported
    assert "matplotlib" in plotting
