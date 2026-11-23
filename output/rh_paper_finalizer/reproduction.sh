#!/usr/bin/env sh
set -eu
export LEAN_TOOLCHAIN=leanprover/lean4:v4.33.1
echo "Pinned archive toolchain: $LEAN_TOOLCHAIN"
echo "Repository control toolchain: $(cat lean-toolchain)"
py -m pytest python/tests/test_gap_closer.py -q
py scripts/audit/rh_gap_closer.py --local-control --claim alpoge_2026
py scripts/audit/rh_gap_closer.py --claim alpoge_2026 --archive external/alpoge-lean
py scripts/finalize_rh_paper.py
