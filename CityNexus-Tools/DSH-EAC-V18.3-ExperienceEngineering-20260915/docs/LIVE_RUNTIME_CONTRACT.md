# CityNexus V18.3 Live Runtime Contract

Source of truth (read-only reference):
`D:\moodle\CityNexus\backend\app\agent\runtime_events.py`,
`D:\moodle\CityNexus\frontend\src\api\citynexus.ts`,
`D:\moodle\CityNexus\backend\app\main.py`.

This reference app must not change any backend schema. It normalizes live
REST/SSE payloads into the stable `NormalizedAgentEvent` shape used by
`AgentRunTimeline`.

---

## 1. Runtime identity

| Contract value | Meaning | Experience adapter |
| --- | --- | --- |
| `HERMES_NATIVE_MCP` | native Hermes run through the CityNexus MCP boundary | `LiveCityNexusAdapter` (LIVE) |
| `NATIVE_DEEPSEEK_TOOL_LOOP` | legacy native DeepSeek tool loop | `LiveCityNexusAdapter` (LIVE) |
| `HERMES_COMPAT_ENDPOINT` | compatibility endpoint | `LiveCityNexusAdapter` (LIVE) |
| `DIRECT` | semantic/direct answer, no agent run | `LiveCityNexusAdapter` (LIVE) |
| `NOT_CONFIGURED` / unavailable | runtime cannot start a native run | UI maps to `UNAVAILABLE` |
| `FALLBACK` | deterministic/offline answer path | `OfflineSnapshotAdapter` or explicit fallback |

Rules:
- Only a real backend response/event may produce `source: "LIVE"`.
- Recorded fixtures always produce `source: "RECORDED_FIXTURE"`.
- Cached snapshots always produce `source: "OFFLINE"` and expose `lastUpdated`.

## 2. Run and step fields

`AgentRun` (frontend API type):
`run_id`, `mission_id`, `journey_id`, `provider_key`, `runtime_identity`,
`model_key`, `status`, `outcome`, `failure_reason`, `mission_status`,
`created_at`, `started_at`, `completed_at`, `tool_steps`, `mission_plan`,
`native_events_url`, `events_url`, `timeline_url`, `initial_events`,
`protected_commitments`.

`AgentRunStep`: `id?`, `sequence_no`, `tool_name`, `arguments`, `result`,
`decision`, `status`, `created_at`, `completed_at`.

`NativeRuntimeEvent`: `event_type`, `run_id`, `tool_name`, `friendly_label`,
`status`, `timestamp`, `duration_ms`, `result_summary`, `policy_decision`,
`raw_event_type`, `source`, `approval_id`, `proposal_id`, `mission_id`,
`approval_status`, `approval_method`.

## 3. Normalized event vocabulary

Exactly these types survive normalization; anything else becomes `unknown`
with `unknown: true` and a preserved `raw_event_type`:

`semantic.interpreted`,
`mission.planned`,
`run.started`,
`tool.started`,
`tool.completed`,
`tool.failed`,
`gateway.checked`,
`guardian.checked`,
`proposal.created`,
`approval.required`,
`run.completed`,
`run.failed`,
`run.stopped`.

Noise events are dropped: `message.delta`, `reasoning.available`,
`reasoning.delta`, `content.delta`, `heartbeat`.

Optional fields that must not crash the UI when missing:
`timestamp`, `duration_ms`, `tool_name`, `status`, `result_summary`,
`policy_decision`, `approval_id`, `proposal_id`, `mission_id`, `sequence_no`.

## 4. SSE transport

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/agent/hermes/runs/{run_id}/events` | raw native Hermes SSE stream |
| `GET /api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}/events` | journey-scoped SSE proxy |
| `GET /api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}` | run status hydrating |
| `GET /api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}/timeline` | full timeline + observability |
| `POST /api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}/stop` | stop semantics |
| `POST /api/v1/journeys/{journey_id}/copilot/messages` | semantic Copilot request |

SSE frames use `event: <normalized event_type>` and `data: <normalized JSON>`.
`data` already contains `sequence_no`, `run_id`, `timestamp`, `source`,
`tool_name`, `status`, `duration_ms`, `result_summary`, and optional ids.

Reconnect rules:
- Track the last accepted `sequence_no`.
- Deduplicate by event id or `run_id + sequence_no + event_type + tool_name`.
- Reconnect with bounded backoff (max 3 attempts); never fabricate events.
- On reconnect, hydrate REST truth first, then continue SSE.
- Missing/duplicate/out-of-order events are normalized; stable order is
  `sequence_no`, then timestamp, then arrival.

## 5. Approval contract

Frontend approval statuses: `PENDING`, `APPROVED`, `CONSUMED`, `EXPIRED`,
`REVOKED`.

Endpoint: `POST /api/v1/journeys/{journey_id}/agent/approvals/{approval_id}/approve`
with body `{ approval_method }` where method is `USER_CONFIRMATION`,
`STEP_UP`, or `WEBAUTHN`.

Experience lifecycle states:

| State | Trigger |
| --- | --- |
| `proposal_only` | proposal exists, no approval required yet |
| `approval_required` | server approval pending |
| `submitting` | request in flight; destructive buttons disabled |
| `approved` | server says APPROVED/CONSUMED |
| `rejected` | server says REVOKED or user rejected |
| `review_requested` | user asked for changes; no backend mutation |
| `expired` | server says EXPIRED or deadline passed |
| `superseded` | HTTP 409 / proposal replaced by a newer proposal |
| `failed` | network loss, 5xx, validation failure |

Error mapping:
- double-click: same idempotency key returns the first settled result.
- HTTP 409: `superseded` or `already_consumed`, `retryable: false`.
- HTTP 404: `failed`, `retryable: false`.
- HTTP 410 / expired body: `expired`, `retryable: false`.
- network/offline: `failed` with `reason: network_loss|offline`, `retryable: true`.
- The UI must never show authoritative success before server truth arrives.

## 6. Stop semantics

`POST .../stop` requests stop. The run remains non-terminal until a
`run.stopped` event arrives (or REST hydration reports `stopped`). The UI may
show `stopping` locally but must not fabricate `run.stopped` or advance an
agent timeline with `setTimeout`/`setInterval`.

## 7. Map contract

MapLibre camera contract: `flyTo`, `fitBounds`, duration tokens
`instant 90ms / fast 160ms / base 220ms / slow 420ms / map 650ms`.
Reduced motion sets duration to 0. MapLibre is dynamically imported only on
map routes; non-map routes must not create WebGL.

## 8. Adapter mapping

| Method | RecordedFixtureAdapter | LiveCityNexusAdapter | OfflineSnapshotAdapter |
| --- | --- | --- | --- |
| `getJourneyPulse` | fixture pulse | journey/twin projection | cached snapshot |
| `getRuntimeStatus` | `DIRECT`/`HERMES_NATIVE_MCP`, RECORDED_FIXTURE | `/agent/runtime-status` | `UNAVAILABLE`, OFFLINE |
| `startCopilotMission` | recorded response | `POST /copilot/messages` | offline rejection with next action |
| `subscribeRunEvents` | rAF replay of fixture | EventSource + normalize | one-shot cached events |
| `stopRun` | local replay stop | `POST .../stop` | offline failure |
| `submitApprovalDecision` | deterministic reference lifecycle | real approve endpoint | `failed: offline` |
| `getRecoveryDiff` | fixture recovery | persisted replans projection | cached recovery |
| `getMapState` | fixture route | route evidence + twin | cached route |

## 9. Honesty rules

1. Only real backend data may show `LIVE`.
2. Recorded replay shows `RECORDED_FIXTURE` on the timeline, badge and notice.
3. Offline/stale shows `OFFLINE`, a last-updated stamp, and disables destructive
   approval actions.
4. Unknown future events are preserved and displayed as unknown, never dropped
   silently or treated as success.
