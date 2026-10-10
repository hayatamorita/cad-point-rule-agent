#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"
if [[ "$#" -lt 1 ]]; then
  echo "Usage: bash harness/verify.sh PATH_TO_CANDIDATE.json [--goal PATH]" >&2
  exit 2
fi
CANDIDATE="$1"
shift
exec python3 -m cad_rule_agent.harness verify --candidate "$CANDIDATE" "$@"
