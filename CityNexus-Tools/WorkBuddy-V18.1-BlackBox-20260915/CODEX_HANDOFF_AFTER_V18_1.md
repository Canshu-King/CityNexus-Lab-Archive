# Codex Handoff — after V18.1 Black-Box Validation

## Proven failures (reproducible)

1. **Native-Hermes proxy endpoints 500 / abort the stream when native Hermes is unconfigured.**
   - `GET /api/v1/agent/hermes/runs/{run_id}` → 500 (should be 502)
   - `POST /api/v1/journeys/{id}/agent/hermes/runs/{run_id}/stop` → 500 (should be 502)
   - `GET /api/v1/agent/hermes/runs/{run_id}/events` → stream aborted, no status
   - **Root cause:** `client = HermesNativeClient()` is constructed **outside** the `try/except`
     in all three handlers (`backend/app/main.py` ~487–521). The unconfigured client raises
     `ValueError`, which escapes the `except (httpx.HTTPError, ValueError) → HTTPException(502)`.
   - **Fix:** move the construction inside the `try`, or pre-check configuration and raise 502.
   - Evidence: `evidence/results_isolated.json` (D1, X1, X2, X3).

2. **`/api/v1/agent/hermes/capabilities` omits the `ready` key in the unconfigured branch.**
   - `native_hermes_status()` should always include `ready` (it does only in the configured branch).
   - Evidence: `results_isolated.json` (A3).

3. **`readOnlyHint` missing from the adapter descriptor list.**
   - `CityNexusMCPServer.list_tools_v2()` (via `MCPToolDescriptor.as_dict()`) has no
     `annotations.readOnlyHint`; the FastMCP path does. Align the two.
   - Evidence: `evidence/results_mcp.json` (M5).

## Native Hermes truth (per link)

- binary: **PASS**
- profile: **PASS**
- MCP server (V2 surface, real `inspect_journey` call): **PASS**
- gateway `/v1/capabilities` ready: **PASS**
- run created: **NOT_TESTED**
- real MCP tool event inside a run: **NOT_TESTED**
- frontend event for a native run: **NOT_TESTED**

→ **Native Hermes E2E is NOT PROVEN.** `runtime_identity=HERMES_NATIVE_MCP` is derived from
gateway reachability alone while `native_mcp_proven=false`. Recommendation: make
`native_mcp_proven` derive from an observed MCP tool event in a completed run, and have the UI
gate the native rail/Stop on the proven flag.

## Semantic routing regressions

None found. 14/14 deterministic policy checks pass; DIRECT vs Hermes routing correct;
hypothetical/negated statements never create a city Event and are not overridden by the
substring fallback. See `SEMANTIC_ROUTING_RESULTS.md`.

## Frontend runtime truth

Copilot Dock is correctly gated on `runtime_identity` (shows `DIRECT` by default; renders the
timeline/Stop only for `HERMES_NATIVE_MCP`). Live render and mobile 390×844 were NOT_TESTED
(frontend down; interactive drive would write authoritative state). See
`FRONTEND_RUNTIME_RESULTS.md`.

## Low-conflict assets to merge (safe, no production code)

- `tests/blackbox_v18_1.py` — HTTP black-box suite (A/E/D/X/F-live)
- `tests/semantic_policy_offline.py` — deterministic semantic-policy suite (14 checks)
- `tests/mcp_v2_probe.py` — MCP V2 allowlist + real tool call probe
- `tests/README.md` — how to run them
- `evidence/*.json`, `evidence/test_results.txt` — recorded results

All three suites are self-contained, take a `--base-url`/`--repo` argument, and never modify
the authoritative tree. They are ready to drop into `backend/tests/` or a CI step.

## Do not merge

- `repo_copy/**` — a read-only snapshot of tonight's source; it is a **copy**, not a source of
  truth. Delete it after review.
- `evidence/_hermes_probe.txt`, `evidence/backend8020_run.log` — transient lab artifacts.

## Environment warnings for the next run

- The authoritative stack was **down at 03:06** (8000/5173/8652 all stopped) and the gateway
  restarted mid-window (PID 20124 → 56800). Treat any "ready" reading as time-sensitive.
- The Hermes runtime is inside the Codex MSIX package
  (`…\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\hermes\hermes-agent`), **not** at the
  path `.start-hermes.ps1` documents. Its venv `python.exe` shim is broken from an external
  shell. `.hermes-gateway-pid` was stale.
