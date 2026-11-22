"""Import-closure analysis of the Alpoge archive, from a pre-extracted import list.

Input: out/imports_raw.txt, lines of the form `src/<Path>.lean:<lineno>:import <Module>`.
Output: out/lean_closure.json and a printed summary: how many modules the five
headline theorems can depend on, grouped by top-level package, with the depth
histogram of the import DAG from the roots.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

RAW = Path(r"C:\Users\Milan\Projects\riemann-audit\out\imports_raw.txt")
OUT = Path(r"C:\Users\Milan\Projects\riemann-audit\out")

ROOTS = ["Main", "Statements", "Supplements.Kernels.MainTheorems"]
LINE = re.compile(r"^(src/[^:]+\.lean):(\d+):\s*(?:public\s+)?import\s+([\w.']+)\s*$")


def main() -> int:
    imports: dict[str, list[str]] = {}
    modules: set[str] = set()
    for raw in RAW.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE.match(raw)
        if not m:
            continue
        path, _lineno, mod = m.groups()
        src_mod = path[len("src/") : -len(".lean")].replace("/", ".")
        modules.add(src_mod)
        imports.setdefault(src_mod, []).append(mod)

    # BFS from the roots. Only edges into submitted modules are followed; Mathlib
    # is outside the submission (it is a dependency, not part of the archive).
    depth = {r: 0 for r in ROOTS if r in modules}
    frontier, d = list(depth), 0
    while frontier:
        d += 1
        nxt = []
        for m in frontier:
            for i in imports.get(m, []):
                if i in modules and i not in depth:
                    depth[i] = d
                    nxt.append(i)
        frontier = nxt

    pkg = Counter(m.split(".")[0] for m in depth)
    hist = Counter(depth.values())
    external = Counter()
    for m in depth:
        for i in imports.get(m, []):
            if i not in modules:
                external[i.split(".")[0]] += 1

    result = {
        "modules_in_src": len(modules),
        "modules_in_closure": len(depth),
        "packages": dict(pkg.most_common()),
        "depth_histogram": dict(sorted(hist.items())),
        "max_depth": max(depth.values()) if depth else 0,
        "external_import_roots": dict(external.most_common(8)),
        "roots": ROOTS,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lean_closure.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"modules in src: {len(modules)}")
    print(f"closure of {ROOTS}: {len(depth)} modules")
    print("by package:", dict(pkg.most_common()))
    print("depth histogram (top 10):", dict(sorted(hist.items())[:10]))
    print("max depth:", max(depth.values()) if depth else 0)
    print("external roots:", dict(external.most_common(6)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
