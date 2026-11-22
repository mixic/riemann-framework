"""Stream-decompress a .ndjson.zst export (no zstd CLI needed on this machine)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import zstandard as zstd

CHUNK = 1 << 24


def decompress(src: Path, dst: Path) -> None:
    # The export is written with `zstd -19 --long=30`, i.e. a 1 GiB window;
    # python-zstandard refuses that unless the window budget is raised.
    dctx = zstd.ZstdDecompressor(max_window_size=1 << 31)
    total = 0
    t0 = time.time()
    with src.open("rb") as fin, dctx.stream_reader(fin, read_size=CHUNK) as reader, dst.open("wb") as fout:
        while True:
            block = reader.read(CHUNK)
            if not block:
                break
            fout.write(block)
            total += len(block)
            if total % (1 << 30) < CHUNK:
                print(f"  {total / 2**30:.1f} GiB  {time.time() - t0:.0f}s", flush=True)
    print(f"done: {dst} {total} bytes ({total / 2**30:.1f} GiB) in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    decompress(Path(sys.argv[1]), Path(sys.argv[2]))
