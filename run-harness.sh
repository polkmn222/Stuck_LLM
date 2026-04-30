#!/usr/bin/env zsh
set -euo pipefail

cd "$(dirname "$0")"
exec python3 scripts/harness/run_harness.py "$@"
