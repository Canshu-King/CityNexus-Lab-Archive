#!/usr/bin/env bash
# Run the whole V18.1 black-box suite against an isolated backend and merge results.
# Usage: BASE_URL=http://127.0.0.1:8020 REPO=<repo_copy>/backend AGENT_MCP=<repo_copy>/agent-mcp ./scripts/run_all.sh
set -euo pipefail
WS="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PY:-python}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8020}"
REPO="${REPO:-$WS/repo_copy/backend}"
AGENT_MCP="${AGENT_MCP:-$WS/repo_copy/agent-mcp}"

echo "== 1) HTTP black-box =="
"$PY" "$WS/tests/blackbox_v18_1.py" --base-url "$BASE_URL" \
    --out "$WS/evidence/results_isolated.json" --label isolated

JID="$("$PY" -c "import json;print(json.load(open(r'$WS/evidence/results_isolated.json',encoding='utf-8'))['meta']['bootstrap'].get('journey_id') or '')")"

echo "== 2) semantic policy (offline) =="
"$PY" "$WS/tests/semantic_policy_offline.py" --repo "$REPO" \
    --out "$WS/evidence/results_semantic.json"

echo "== 3) MCP V2 surface =="
PYTHONPATH="$AGENT_MCP" "$PY" "$WS/tests/mcp_v2_probe.py" --base-url "$BASE_URL" \
    --journey-id "$JID" --out "$WS/evidence/results_mcp.json"

echo "== merge =="
"$PY" - "$WS" <<'PY'
import json, os, sys, datetime
ws = sys.argv[1]; ev = os.path.join(ws, "evidence")
merged = {"meta": {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "lab": "CityNexus V18.1 Black-Box", "harness_dir": "tests/"}, "suites": {}, "summary": {}}
tot = {"PASS": 0, "FAIL": 0, "NOT_TESTED": 0}
for name, f in [("backend_isolated", "results_isolated.json"),
                ("semantic_policy", "results_semantic.json"),
                ("mcp_v2", "results_mcp.json")]:
    p = os.path.join(ev, f)
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    merged["suites"][name] = d
    for k in tot:
        tot[k] += d.get("summary", {}).get(k, 0)
merged["summary"] = tot
json.dump(merged, open(os.path.join(ev, "results.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("TOTAL", tot)
PY
echo "done -> $WS/evidence/results.json"
