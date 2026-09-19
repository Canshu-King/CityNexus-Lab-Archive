#!/usr/bin/env bash
# V18.2 Agent Safety & Black-Box - run every suite against an isolated stack.
#
#   backend : 8021   (Codex owns 8000)
#   frontend: 4173   (Codex owns 5173)
#
# Usage:  bash scripts/run_all.sh [lab_root]
set -u

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
PY="${V182_PY:-D:/moodle/CityNexus/backend/.venv/Scripts/python.exe}"
NODE="${V182_NODE:-C:/Users/仓鼠王/.workbuddy-ai/binaries/node/versions/22.22.2-2/node.exe}"
BE="http://127.0.0.1:8021"
FE="http://127.0.0.1:4173"

cd "$ROOT" || exit 1

echo "== 0. health =="
curl -s --max-time 5 "$BE/api/v1/health" || { echo "backend 8021 is down"; exit 1; }
echo

echo "== 1. authority matrix (offline) =="
"$PY" tests/test_authority_matrix.py --repo repo_copy/backend || echo "  ^ failures above"

echo "== 2. agent safety red team =="
"$PY" tests/blackbox_agent_safety.py --base-url "$BE" --db citynexus_v182.db || true

echo "== 3. runtime truth =="
"$PY" tests/runtime_truth.py --base-url "$BE" || true

echo "== 4. semantic boundary =="
"$PY" tests/semantic_boundary.py --base-url "$BE" --repo repo_copy/backend \
      --db citynexus_v182.db || true

echo "== 5. multi-step agent =="
"$PY" tests/multistep_agent.py --base-url "$BE" || true

echo "== 6. frontend runtime truth (desktop + mobile) =="
if curl -s -o /dev/null --max-time 5 "$FE/"; then
  "$NODE" tests/frontend_runtime_truth.mjs --base "$FE" || true
else
  echo "frontend 4173 is down - skipping Family F"
fi

echo
echo "per-suite JSON in evidence/results_*.json"
