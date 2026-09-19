# WorkBuddy V18.1 — Native Hermes Black-Box Validation Report

**Date:** 2026-09-15 · **Window:** ~01:17–03:17 (+08:00) · **Mode:** unattended (user asleep)
**Isolated workspace:** `D:\moodle\CityNexus-Tools\WorkBuddy-V18.1-BlackBox-20260915`
**Authoritative worktree (NOT modified):** `D:\moodle\CityNexus` (owned by Codex)

## 0. Verdict in one paragraph

The V18.1 **semantic layer is solid** (14/14 deterministic policy checks pass) and the
**CityNexus MCP V2 surface is real** (11-tool allowlist enforced, a real `inspect_journey`
call returned live server data). But the **`HERMES_NATIVE_MCP` runtime identity is asserted
from gateway reachability alone, not from a proven native run** — the authoritative
runtime itself reports `native_mcp_proven: false`. Two concrete defects were reproduced:
the three native-Hermes proxy endpoints **500 / abort the stream** when native Hermes is
unconfigured (root cause: the client is constructed outside the `try/except`), and
`/agent/hermes/capabilities` **omits the `ready` key** in its unconfigured branch.
A true end-to-end "Hermes drives a CityNexus MCP tool" run was **NOT executed** because
doing so would either write to the authoritative database (its MCP server is pinned to
`http://127.0.0.1:8000`) or require standing up a second Hermes gateway; the exact
recipe to prove it is in §5 and `HERMES_NATIVE_ACCEPTANCE_RESULTS.md`.

## 1. Method & isolation

| Item | Value |
|---|---|
| Authoritative tree | `D:\moodle\CityNexus` — **read-only**; only HTTP GET probes + a file copy |
| Isolated backend | `127.0.0.1:8020`, running a **read-only copy** of `backend/` (270 files) with its **own** sqlite DB |
| Isolated DB | `citynexus_v18.db` inside the workspace (never the authoritative DB) |
| Python | main tree venv (`backend\.venv`) used read-only for imports |
| Hermes gateway | shared `127.0.0.1:8652` (Codex-owned) — **not started, not stopped, not reconfigured** |
| Frontend | live `5173` (Codex-owned) — read-only HTTP + source inspection |

No production code was modified. Only `tests/`, `scripts/`, `docs/`, `evidence/` were written.

## 2. Results summary (executed)

Combined across three suites — **PASS 28 / FAIL 6 / NOT_TESTED 5** (see `evidence/results.json`).

| Family | What it proves | Result |
|---|---|---|
| **A — Runtime truth** | identity derivation, audit flag, capabilities, tool surface | 4 PASS / 1 FAIL |
| **E — Routing** | DIRECT stays DIRECT; Hermes-suitable falls back explicitly | 5 PASS |
| **F — Semantic truth** | envelope → safe route, not overridden by substring rules | 14 PASS (offline) + 5 NOT_TESTED (live, no model) |
| **MCP — MCP V2 surface** | allowlist, real tool call, read-only hints | 4 PASS / 1 FAIL |
| **D/X — Stop + proxy robustness** | clean 502 vs unhandled 500 | 1 PASS / 4 FAIL |

## 3. Confirmed defects (reproducible)

### F1 — Native-Hermes proxy endpoints return 500 instead of 502 (Medium)
- `GET /api/v1/agent/hermes/runs/{id}` → **500** (expected clean 502)
- `POST /api/v1/journeys/{id}/agent/hermes/runs/{id}/stop` → **500** (expected clean 502)
- `GET /api/v1/agent/hermes/runs/{id}/events` → **stream aborted** (transport error, no status)
- **Root cause:** in `backend/app/main.py`, `client = HermesNativeClient()` is constructed
  **before** the `try:` block in all three handlers, so the `ValueError("native Hermes API is
  not configured")` raised by an unconfigured client escapes the `except (httpx.HTTPError,
  ValueError) → HTTPException(502)` mapping. (lines ~487–521)
- **Impact:** a user who hits Stop / run-status while the gateway is down (as happened at
  03:06 tonight) gets an opaque 500 and, for the events stream, a silently broken timeline.

### F2 — `/agent/hermes/capabilities` omits `ready` when unconfigured (Low)
- Unconfigured branch returns `{configured:false, reachable:false, runs:false, events:false,
  approval:false, profile, provider, model}` — **no `ready` key**.
- A consumer that reads `caps["ready"]` (as the UI's runtime-chain logic does) will `KeyError`
  in the unconfigured state. `native_hermes_status()` should always emit `ready`.

### F3 — `readOnlyHint` absent from the adapter descriptor list (Low)
- `CityNexusMCPServer.list_tools_v2()` (via `MCPToolDescriptor.as_dict()`) returns **no**
  `annotations.readOnlyHint`, while the FastMCP-built path (`build_mcp_v2_server`) *does*
  set `readOnlyHint` from the `read_only` set. Consumers of the adapter list cannot tell
  inspect from mutate. (M5 in `results_mcp.json`.)

## 4. What is genuinely good (verified)

- **Semantic envelope → route mapping is correct and safe** (F1–F14): HYPOTHETICAL → WHAT_IF,
  UNVERIFIED → VERIFY_FACT, NEGATED/HISTORICAL → UNKNOWN, PERSONAL → no city Event, and only
  `DISRUPTION_REPORT + ASSERTED + (NOW|FUTURE) + city event type` creates an Event. Malformed
  envelopes (missing key, out-of-enum, confidence out of range) are rejected.
- **The semantic policy is not re-overridden by substring rules**: a hypothetical "如果明天下雨
  会怎样？" resolves to WHAT_IF with `create_event=False` even though the deterministic
  fallback classifier is tempted toward DISRUPTION_REPORT.
- **DIRECT requests never fake Hermes**: EXPLAIN_PLAN / WHAT_IF returned `agent_run=null` and
  `mode=FALLBACK`, `provider=deterministic` — no `HERMES_NATIVE_MCP` identity was claimed.
- **MCP V2 allowlist is exact** (11 tools), the V1 surface is the pinned 6-tool subset,
  unknown tools raise `ValueError`, and a **real `inspect_journey` call returned server data**.
- **The UI is gated on truth**: `CopilotDock.tsx:133-134` renders the `AgentRunRail` and the
  **Stop** control only when `runtime_identity === "HERMES_NATIVE_MCP"`; `lastRuntime` falls
  back to `"DIRECT"`.

## 5. The one thing not proven — and how to prove it

**Not proven:** that a real Hermes run drives a real CityNexus MCP tool event end-to-end.

**Why it was not executed:** the Hermes profile's MCP server is pinned to the authoritative
backend (`CITYNEXUS_API_BASE_URL: http://127.0.0.1:8000`). Triggering a run therefore routes
MCP tools (including mutating ones like `request_replan`) into the **authoritative database** —
which this task forbids writing to. Standing up a parallel gateway was judged too costly/risky
inside the 2-hour budget while Codex was actively restarting the shared one.

**Recipe to prove it safely** (isolated, no authoritative writes) — full detail in
`HERMES_NATIVE_ACCEPTANCE_RESULTS.md` §Recipe.

## 6. Environment observations (important for Codex)

1. **The authoritative stack was unstable tonight.** The Hermes gateway PID changed
   `20124 → 56800` during a 5-minute window (`.hermes-gateway-key` rewritten at 01:20), and at
   **03:06 all three ports (8000, 5173, 8652) were down simultaneously**. Black-box truth is
   therefore time-sensitive; a "ready" reading is only valid for that instant.
2. **The Hermes runtime lives inside the Codex MSIX package**
   (`…\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\hermes\hermes-agent`), not at the
   path `.start-hermes.ps1` documents (`%LOCALAPPDATA%\hermes\hermes-agent`). The venv's
   `python.exe` shim is **broken** from an external shell (it resolves to a non-existent
   `.hermes-runtime` python), so the MCP server cannot be launched with it directly.
3. `.hermes-gateway-pid` was stale (40116) versus the live listener (20124/56800).

## 7. Deliverables

| File | Contents |
|---|---|
| `WORKBUDDY_V18_1_BLACKBOX_REPORT.md` | this report |
| `HERMES_NATIVE_ACCEPTANCE_RESULTS.md` | binary/profile/MCP/gateway/run/tool-event/frontend matrix + recipe |
| `SEMANTIC_ROUTING_RESULTS.md` | scenario E + F detail |
| `FRONTEND_RUNTIME_RESULTS.md` | Copilot Dock / timeline / Stop / mobile assessment |
| `CODEX_HANDOFF_AFTER_V18_1.md` | failures + low-conflict assets to merge |
| `evidence/results.json` | merged machine-readable results |
| `evidence/test_results.txt` | human-readable transcript |
| `evidence/live_runtime_snapshot.json` | read-only snapshot of the authoritative runtime |
| `tests/` | `blackbox_v18_1.py`, `semantic_policy_offline.py`, `mcp_v2_probe.py`, `README.md` |

## 8. Limitations

- Live DeepSeek semantic-envelope checks (F1–F5 live) were **NOT_TESTED**: the isolated
  instance ran with `CITYNEXUS_AI_ENABLED=false` (no model credential was used), so the
  deterministic fallback path was exercised. The envelope **policy** was covered fully offline.
- Desktop/Mobile interactive UI drives (G/H) were **NOT_TESTED**: driving the live UI would
  create state in the authoritative database, and the live frontend was down at probe time.
- Full-chain Hermes E2E (**B**) **NOT_TESTED** (see §5).
