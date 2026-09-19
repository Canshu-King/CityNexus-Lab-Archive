# V18.1 Black-Box Tests

Self-contained black-box suites for the V18.1 Native Hermes validation. None of them modify the
authoritative worktree (`D:\moodle\CityNexus`); they only make HTTP calls and import a
read-only copy of the code.

## Prerequisites

- A **running CityNexus backend**. Prefer an **isolated** instance (its own DB), e.g.:

  ```bash
  WS=D:/moodle/CityNexus-Tools/WorkBuddy-V18.1-BlackBox-20260915
  cd "$WS/repo_copy/backend"
  PYTHONPATH="$WS/repo_copy/backend" \
  CITYNEXUS_DATABASE_URL="sqlite:///$WS/citynexus_v18.db" \
  CITYNEXUS_AI_ENABLED=false \
  "D:/moodle/CityNexus/backend/.venv/Scripts/python.exe" \
      -m uvicorn app.main:app --host 127.0.0.1 --port 8020
  ```

  To exercise the DeepSeek envelope live, set `CITYNEXUS_AI_ENABLED=true` and
  `CITYNEXUS_AI_API_KEY`/`DEEPSEEK_API_KEY`.

## Run

```bash
# 1) HTTP black-box (runtime truth, routing, stop, proxy robustness, semantic live)
python tests/blackbox_v18_1.py --base-url http://127.0.0.1:8020 \
    --out evidence/results_isolated.json --label isolated-8020

# 2) Deterministic semantic policy (offline, no server)
python tests/semantic_policy_offline.py --repo <repo_copy>/backend \
    --out evidence/results_semantic.json

# 3) MCP V2 surface (needs the agent-mcp package on PYTHONPATH)
PYTHONPATH=<repo_copy>/agent-mcp python tests/mcp_v2_probe.py \
    --base-url http://127.0.0.1:8020 --journey-id <uuid> \
    --out evidence/results_mcp.json
```

`--journey-id` for suite 3 can be read from `evidence/results_isolated.json`
(`meta.bootstrap.journey_id`) after suite 1 has run.

## What each suite covers

| Suite | Families |
|---|---|
| `blackbox_v18_1.py` | A runtime truth · E routing · D stop · X proxy robustness · F semantic (live) |
| `semantic_policy_offline.py` | F semantic policy table + schema validation + anti-override seam |
| `mcp_v2_probe.py` | MCP V2 allowlist · V1 subset · real `inspect_journey` call · read-only hints |

## Reading results

Each suite writes a JSON file with `{meta, summary:{PASS,FAIL,NOT_TESTED}, scenarios:[…]}`.
`evidence/results.json` merges all three. A `FAIL` is a reproducible defect candidate; a
`NOT_TESTED` records an unexecuted check **with its reason** (never silently skipped).
