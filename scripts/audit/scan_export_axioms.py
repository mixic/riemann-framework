"""Enumerate the axiom declarations that the solution export actually contains.

The NDJSON export interns every name as {"in":<idx>,"str":{"pre":<idx>,"str":"<s>"}}
and declares an axiom as {"axiom":{"isUnsafe":...,"levelParams":[...],"name":<idx>,...}}.
This streams the 61.5 GB file in chunks, resolves the intern table, and prints the
axiom names, so that the claim "only the three standard axioms" can be checked
against the artefact rather than against a log someone else wrote.

Also counts `sorryAx` occurrences, which is the marker a sorry-based proof leaves.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SRC = Path(r"C:\Users\Milan\Projects\riemann-audit\exports\solution.ndjson")
OUT = Path(r"C:\Users\Milan\Projects\riemann-audit\out")

CHUNK = 1 << 26
TAIL = 1 << 16

# intern entry: {"in":N,"str":{"pre":P,"str":"NAME"}}
INTERN = re.compile(rb'\{"in":(\d+),"str":\{"pre":(\d+),"str":"((?:[^"\\]|\\.)*)"\}\}')
AXIOM = re.compile(rb'\{"axiom":\{"isUnsafe":(?:true|false),"levelParams":\[[^\]]*\],"name":(\d+)')


def main() -> int:
    intern: dict[int, tuple[int, bytes]] = {}
    axiom_idxs: list[int] = []
    sorry = 0
    consumed = 0
    tail = b""
    with SRC.open("rb") as f:
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            data = tail + block
            for m in INTERN.finditer(data):
                intern[int(m.group(1))] = (int(m.group(2)), m.group(3))
            for m in AXIOM.finditer(data):
                axiom_idxs.append(int(m.group(1)))
            sorry += data.count(b"sorryAx")
            tail = data[-TAIL:]
            consumed += len(block)
            if consumed % (1 << 31) < CHUNK:
                print(f"  {consumed / 2**30:.1f} GiB, axioms so far {len(axiom_idxs)}", flush=True)

    def name(idx: int) -> str:
        # Lean names are hierarchical: an entry with pre = p continues the name
        # interned at p, joined by a dot. pre = 0 means a root name.
        parts: list[str] = []
        seen = 0
        while idx != 0 and seen < 200:
            pre, s = intern.get(idx, (0, b"<missing>"))
            parts.append(s.decode("utf-8", "replace"))
            idx = pre
            seen += 1
        return ".".join(reversed(parts))

    names = sorted({name(i) for i in axiom_idxs})
    result = {
        "bytes_scanned": consumed,
        "axiom_declarations": len(axiom_idxs),
        "axiom_names": names,
        "sorryAx_occurrences": sorry,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "solution_axioms.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"scanned {consumed} bytes")
    print(f"axiom declarations: {len(axiom_idxs)}")
    print("names:", json.dumps(names, indent=0))
    print(f"sorryAx occurrences: {sorry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
