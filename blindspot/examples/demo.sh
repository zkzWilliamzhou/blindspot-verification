#!/usr/bin/env bash
# Self-contained demo. No install, no network, no dependencies.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$HERE"

echo "1) The 30-second false-green demo (expected exit 1)"
python3 -m blindspot demo || true

echo
echo "2) Static inspection only, never executes"
python3 -m blindspot inspect "pytest -q | tail -1"

echo
echo "3) Machine-readable envelope for CI"
python3 -m blindspot run "echo hello" --json | python3 -m json.tool | head -30
