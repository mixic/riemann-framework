#!/usr/bin/env bash
# A8: reproduce the artefact suite and the paper's verdict.
# Linux/macOS. The Windows Lean toolchain cannot build the archive: Lean writes files such as
# `<Module>.olean.private.hash` beside each olean, and the longest module exceeds the 260-character
# path limit the Windows file API enforces for the toolchain.
#
# Usage:  bash reproduction.sh [WORKDIR]
set -euo pipefail

WORKDIR="${1:-alpoge-work}"
ARCHIVE_COMMIT="1cc42d2c900ba764cb63e3c36383c720f30a77ca"
ARCHIVE_URL="https://github.com/Deicyde/riemann-hypothesis"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$WORKDIR"
cd "$WORKDIR"
if [[ ! -d alpoge-lean/.git ]]; then
  git clone "$ARCHIVE_URL" alpoge-lean
fi
git -C alpoge-lean checkout "$ARCHIVE_COMMIT"
git -C alpoge-lean log -1 --format='archive commit %H %ad' --date=iso

command -v elan >/dev/null || { echo "elan is required: https://leanprover.github.io/elan/" >&2; exit 1; }
(
  cd alpoge-lean
  lake update
  lake exe cache get
  lake build Main
)

python3 "$HERE/scripts/audit/rh_gap_closer.py" --claim alpoge_2026 \
  --archive "$(cd alpoge-lean && pwd)" --theorem Main.riemannHypothesis --module Main --timeout 7200

# The fresh report is packaged by the finalizer; copy it over the archived copy first.
cp -f "$HERE/out/gap_closer/alpoge_2026/"*.json "$HERE/out/gap_closer/alpoge_2026/"*.txt \
      "$HERE/out/gap_closer/alpoge_2026/"*.html "$HERE/out/gap_closer/alpoge_2026/"*.md \
      "$HERE/docs/gap_closer/alpoge_2026/" 2>/dev/null || true
python3 "$HERE/scripts/finalize_rh_paper.py"
python3 "$HERE/scripts/audit/verify_manifest.py" "$HERE/output/rh_paper_finalizer"
python3 "$HERE/scripts/audit/paper_readiness.py" "$HERE/output/rh_paper_finalizer"

echo
echo "Reproduction complete. Compare output/rh_paper_finalizer/ with the committed suite."
