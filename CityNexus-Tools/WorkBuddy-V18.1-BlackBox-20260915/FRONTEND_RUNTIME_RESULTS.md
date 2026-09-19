# Frontend Runtime Results (V18.1)

Scope: black-box verification of the **Copilot Dock** (semantic runtime, execution runtime,
truth authority, ordered real event timeline, Stop control, panel re-open persistence) and the
**390×844 mobile** view.

## Method

- Read-only HTTP probe of the live frontend (`127.0.0.1:5173`) — **NOT reachable at probe
  time** (port down; Codex restarting its stack).
- Read-only source inspection of `D:\moodle\CityNexus\frontend\src` (no modifications).
- Interactive UI drives (create journey → send copilot message → observe timeline) were
  **NOT_TESTED**: they would create state in the authoritative database, which is forbidden.

## G — Desktop Copilot Dock (source-verified)

| Requirement | Evidence | Status |
|---|---|---|
| Dock exists & is mounted | `src/features/agent/CopilotDock.tsx`; rendered by `src/app/V8Experience.tsx:815` | **PASS (source)** |
| Semantic runtime shown | `CopilotDock.tsx:84` `setLastRuntime(response.agent_run?.runtime_identity ?? "DIRECT")` — shows `DIRECT` when no run | **PASS (source)** |
| Execution runtime / timeline | `CopilotDock.tsx:133` renders `<AgentRunRail steps={steps} />` **only when** `runtime_identity === "HERMES_NATIVE_MCP"` and `steps.length > 0` | **PASS (source)** |
| Stop control | `CopilotDock.tsx:134` Stop button **only when** `runtime_identity === "HERMES_NATIVE_MCP"` and the run is not in a terminal state | **PASS (source)** |
| Truth authority | `src/features/intelligence/ControlTowerPanel.tsx:17` derives the runtime chain from `runtimeStatus?.runtime_identity === "HERMES_NATIVE_MCP"` | **PASS (source)** |
| Ordered real event timeline | `AgentRunRail` consumes `steps`; events come from `/api/v1/agent/hermes/runs/{id}/events` | **PARTIAL** — wiring present; live ordering **NOT_TESTED** |
| Panel re-open persistence | not verified in source in the window | **NOT_TESTED** |
| Live render at 5173 | port down at probe time | **NOT_TESTED** |

**Design note (correct gating):** the Dock only shows a Hermes run rail / Stop when the
backend reports `HERMES_NATIVE_MCP`. Combined with `lastRuntime` defaulting to `"DIRECT"`,
the UI does **not** fake native participation. This matches the desired A1/A2 behaviour and is
the frontend half of the "runtime truth" requirement.

## H — Mobile 390×844

**NOT_TESTED** — requires a live frontend plus a browser drive; the frontend was down and the
drive would touch authoritative state. Recommended follow-up (safe): point an isolated
frontend at the isolated backend and drive with Playwright at 390×844.

## Risk flagged for Codex

Because the Dock gates the timeline and Stop on the **server-provided** `runtime_identity`, the
`native_mcp_proven: false` gap (see `HERMES_NATIVE_ACCEPTANCE_RESULTS.md`) means the UI can
display a native Hermes rail / Stop control for a run that was never proven to have invoked a
CityNexus MCP tool. If the intent is "only show native when proven", the Dock should gate on a
*proven* flag, not merely on a reachable gateway.
