# Hermes Native Acceptance Results (V18.1)

Acceptance matrix for the chain:
`DeepSeek SemanticEnvelope → runtime router → DIRECT / HERMES_NATIVE_MCP → Hermes Runs/SSE
→ CityNexus MCP V2 → AgentToolGateway/Guardian → Desktop/Mobile Agent Timeline`

**Rule applied:** a native Hermes run counts as proven **only** when a real CityNexus MCP
tool event appears in the run's event stream. Reachability alone is not proof.

## Matrix

| # | Link | Status | Evidence |
|---|---|---|---|
| 1 | **binary** (hermes executable present) | **PASS** | `native_binary_detected: true` on the authoritative runtime; `hermes.exe` located at `…\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\hermes\hermes-agent\.venv\Scripts\hermes.exe` |
| 2 | **profile** (`citynexus`) | **PASS** | `D:\moodle\_v18_hermes_citynexus_profile\config.yaml` present; gateway reports `profile: citynexus`, `provider: deepseek`, `model: deepseek-v4-flash` |
| 3 | **MCP server** (citynexus-v2 surface) | **PASS** | `tests/mcp_v2_probe.py`: exact 11-tool allowlist, V1 6-tool subset, unknown tool rejected, **real `inspect_journey` call returned server data** (M1–M4) |
| 4 | **gateway** (`/v1/capabilities`) | **PASS** | authoritative `GET /api/v1/agent/hermes/capabilities` → `ready:true, runs:true, events:true, approval:true` |
| 5 | **run** (a native run is created) | **NOT_TESTED** | would require triggering a run; not executed (see below) |
| 6 | **tool-event** (real MCP tool inside a run) | **NOT_TESTED** | the decisive proof; not executed (see below) |
| 7 | **frontend-event** (timeline shows the run) | **NOT_TESTED** | live UI drive would write authoritative state; frontend was down at probe time |

**Overall native Hermes E2E: NOT PROVEN.** Links 1–4 are verified; links 5–7 are not.

## Why links 5–7 were not executed

The shared Hermes gateway's profile pins the CityNexus MCP server to the **authoritative**
backend:

```yaml
# D:\moodle\_v18_hermes_citynexus_profile\config.yaml
env:
  CITYNEXUS_API_BASE_URL: "http://127.0.0.1:8000"
```

Creating a run (via `POST /journeys/{id}/copilot/messages` with a REPLAN/DISRUPTION intent)
would make Hermes invoke MCP tools that call back into `http://127.0.0.1:8000`. Even read-only
tools read the authoritative DB, and a mutating tool (`request_replan`) would **write** to it.
The task forbids writing to the authoritative worktree, so the run was deliberately not fired.

Additional blocker: the shared gateway was being restarted by Codex during the window
(PID 20124 → 56800; all ports down at 03:06).

## Root-cause note: `native_mcp_proven` is a flag, not proof

`backend/app/agent/runtime_identity.py`:

```python
native_proven = bool(binary and _truthy(getattr(settings, "hermes_native_proven", None)))
...
if binary and native.get("ready"):
    return HERMES_NATIVE_MCP          # identity asserted from reachability ALONE
```

The authoritative runtime reported `runtime_identity: HERMES_NATIVE_MCP` **together with**
`native_mcp_proven: false`. So the identity answers "is a gateway reachable right now", while
`native_mcp_proven` (an env flag `CITYNEXUS_HERMES_NATIVE_PROVEN`) is the separate audit field.
**Recommendation:** promote `native_mcp_proven` from an env flag to a fact derived from an
observed MCP tool event in a completed run, so the identity cannot claim more than was proven.

## Recipe — prove links 5–7 safely (no authoritative writes)

1. Create an isolated Hermes profile `citynexus-bb` whose MCP server points at the isolated
   backend:
   ```yaml
   mcp_servers:
     citynexus:
       command: "<hermes venv python>"
       args: ["-m", "citynexus_mcp.server", "--v2"]
       env:
         PYTHONPATH: "<repo_copy>/agent-mcp"
         CITYNEXUS_API_BASE_URL: "http://127.0.0.1:8020"
       tools: { include: [inspect_journey, inspect_twin, list_replans, search_city_services,
                          request_replan, accept_replan, replace_activity, reschedule_activity,
                          create_booking, cancel_refundable_booking, request_commitment_change] }
   ```
2. Start a **private** gateway on a free port (e.g. 8662) with a fresh `API_SERVER_KEY` and the
   DeepSeek credential — an isolated process owned by the lab, never touching the shared one.
3. Point the isolated backend at it:
   `CITYNEXUS_HERMES_NATIVE_API_URL=http://127.0.0.1:8662`,
   `CITYNEXUS_HERMES_API_SERVER_KEY=<private key>`, `CITYNEXUS_HERMES_NATIVE_PROFILE=citynexus-bb`.
4. Create a journey in the isolated DB, then `POST …/copilot/messages` with the multi-step
   PLAN_ONLY request. Stream `GET /api/v1/agent/hermes/runs/{run_id}/events`.
5. **Accept only if** the stream contains a `tool_call`/`tool_result` event whose tool name is
   one of the 11 CityNexus tools. Record event type, tool name, lifecycle state, and terminal
   state. If no tool event appears, the run is **not** a native-MCP success.

Note: the hermes venv `python.exe` shim is currently broken from an external shell (resolves to
a non-existent `.hermes-runtime` interpreter); the runtime python must be resolved first.
