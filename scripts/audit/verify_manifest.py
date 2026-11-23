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
"""Verify the SHA-256 manifest of a gap-closer artefact directory.

Usage:  python scripts/audit/verify_manifest.py <directory>

The manifest lists each artefact's path and digest. A mismatch, a missing file, or a file that
the manifest does not cover makes the check fail, so an edited artefact cannot pass unnoticed.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    manifest = directory / "MANIFEST.sha256"
    if not manifest.is_file():
        print(f"no manifest at {manifest}", file=sys.stderr)
        return 1

    failures = 0
    covered: set[Path] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        path = directory / name
        covered.add(path)
        if not path.is_file():
            print(f"MISSING {name}")
            failures += 1
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            print(f"MISMATCH {name}: manifest {digest[:16]}, file {actual[:16]}")
            failures += 1

    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256" and path not in covered:
            print(f"UNCOVERED {path.relative_to(directory).as_posix()}")
            failures += 1

    print(f"{len(covered)} files checked, {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
