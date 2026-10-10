#!/usr/bin/env bash
# Bounded Chen-Yang-inspired CAD hypothesis/refinement launcher.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"
MODE="${1:-demo}"
if [[ "$#" -gt 0 ]]; then shift; fi
case "$MODE" in
  demo) exec python3 -m cad_rule_agent.harness demo "$@" ;;
  codex) exec python3 -m cad_rule_agent.harness codex "$@" ;;
  *) echo "Usage: bash harness/run.sh demo|codex [--goal PATH --run-dir PATH --max-rounds N]" >&2; exit 2 ;;
esac
