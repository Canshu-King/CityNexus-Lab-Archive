# CityNexus V18.2 — Agent Run Timeline Design

Handoff reference for the isolated V18.2 ExperienceLab build.
Source of truth: `reference-app/src/components/AgentRunTimeline.tsx`,
`RuntimeTruthBadge.tsx`, `CopilotDock.tsx`, `data/hermesFixture.ts`, `types.ts`,
`tests/acceptance.spec.ts`, and `evidence/playwright_results.txt`.
The main Codex worktree (`D:\moodle\CityNexus`) was inspected read-only and was
not modified.

> 中文备注：本文档描述“Agent 运行时间线”的完整事件词汇、状态机、录播回放规则、
> 实时（LIVE）契约、审批面板与移动端折叠行为，供合并时对照。

---

## 1. Event vocabulary and status mapping

`AgentEventType` (`types.ts`) is the closed vocabulary. `statusForEvent()` maps
each event to one `TimelineStepStatus`; `labelForEvent()` produces the visible
label. The `default` branch returns `done`, so only the event types listed
explicitly below deviate from `done`.

| `event_type` | `statusForEvent()` | `labelForEvent()` (English) | Notes / 中文备注 |
|---|---|---|---|
| `semantic.interpreted` | `done` | Understood request | DeepSeek semantic compile. 语义理解完成 |
| `mission.planned` | `done` | Mission planned | CityNexus mission plan. 任务已规划 |
| `run.started` | `done` | Run started | Native Hermes run accepted. 运行已开始 |
| `tool.started` | `active` | `Checking Journey` / `Checking protected commitments` / `Searching alternatives` / `Requesting replan`; fallback `Started · <human tool>` | Only event that yields `active`. 工具执行中 |
| `tool.completed` | `done` | `Checked Journey` / `Checked protected commitments` / `Searched alternatives` / `Requested replan`; fallback `Completed · <human tool>` | May carry `duration_ms`. 工具完成 |
| `tool.failed` | `failed` | `Failed · <human tool>` | May carry `duration_ms` (fixture uses 6000 ms). 工具失败 |
| `gateway.checked` | `done` | Gateway checked | Policy gateway. 网关策略检查 |
| `guardian.checked` | `done` | Guardian checked | Guardian feasibility check. 守护者检查 |
| `proposal.created` | `done` | Proposal created | Persisted as `PRESENTED`; carries `proposal_id`. 方案已创建 |
| `approval.required` | `approval` | Waiting for approval | Carries `approval_id` + `proposal_id`; opens the approval panel. 需要审批 |
| `run.completed` | `done` | Run completed | Carries final `run_status: "success"`. 运行完成 |
| `run.failed` | `failed` | Run failed | Carries `run_status: "failed"`. 运行失败 |
| `run.stopped` | `stopped` | Run stopped | Carries `run_status: "stopped"`. 运行已停止 |

Fixture vocabulary order (`HERMES_RECORDED_RUN`, 14 events):
`semantic.interpreted → mission.planned → run.started → (tool.started → tool.completed) ×3
→ gateway.checked → guardian.checked → tool.started → proposal.created → approval.required`.
`HERMES_APPROVED_RUN` appends `run.completed`. `HERMES_FAILED_RUN` ends with
`tool.failed → run.failed`. `HERMES_STOPPED_RUN` ends with `run.stopped`.

---

## 2. Timeline step states

`TimelineStepStatus` = `pending | active | done | approval | failed | stopped`.
`deriveTimelineSteps()` is a 1:1 projection of the **visible** events, so every
rendered `<li class="timeline-step ...">` currently carries one of `active`,
`done`, `approval`, `failed`, `stopped`.

| Status | Meaning | Mark / CSS behaviour |
|---|---|---|
| `pending` | Reserved for a step that is not yet materialized. `deriveTimelineSteps()` never emits it today; future server-side "planned but not started" steps can. | Default muted dot (`--muted`), 4px halo. 预留：尚未产生的步骤 |
| `active` | A tool is currently running (`tool.started`). | Blue `--info` dot + 5px halo |
| `done` | Event completed successfully (the default). | Accent `--accent` dot |
| `approval` | High-impact change waiting for the traveler (`approval.required`). | Warn `--warn` dot |
| `failed` | Tool or run failure. | Danger `--danger` dot |
| `stopped` | Run ended as stopped (`run.stopped`). | Gray `#9aa7ad` dot |

The short status chip on each row is `t('timeline.status.<status>')`:
`pending / active / done / approval required / failed / stopped`.

---

## 3. Run statuses

`runStatusFor(events, stoppedLocally)` returns a string rendered as
`timeline.run.<status>` and written to `data-run-status` on the timeline section
and `data-status` on `timeline-summary`. Precedence, top to bottom:

1. `stoppedLocally === true` → `stopped` (local stop immediately wins).
2. No visible events → `idle` ("Not started").
3. Last visible event is `run.failed` or `tool.failed` → `failed`.
4. Last visible event is `run.stopped` → `stopped`.
5. Last event is `approval.required` **or** its `run_status === "approval_required"` → `approval_required`.
6. Last event is `run.completed` **or** its `run_status === "success"` → `success`.
7. Otherwise → `running`.

| Run status | UI label (EN) | Notes |
|---|---|---|
| `idle` | Not started | 0 recorded events visible |
| `running` | Running | Any non-terminal visible state |
| `success` | Completed | `run.completed` / `run_status: success` |
| `failed` | Failed | `tool.failed` or `run.failed` |
| `stopped` | Stopped | `run.stopped` or local stop |
| `approval_required` | Waiting for approval | `approval.required` / matching `run_status` |

Because the fixture is stepped one event at a time, `data-run-status` changes as
`visibleCount` grows: event 13 (`proposal.created`, `run_status: approval_required`)
already reads `approval_required`; event 12 still reads `running`.

---

## 4. Human labels, durations, timestamps

`HUMAN_TOOL` maps machine tool names to the short noun used in summaries and
fallbacks; `TOOL_LABELS` maps the same names to the started/done verb phrases.

| Tool name | `HUMAN_TOOL` (noun) | `started` label | `done` label |
|---|---|---|---|
| `inspect_journey` | `journey` | Checking Journey | Checked Journey |
| `inspect_twin` | `protected commitments` | Checking protected commitments | Checked protected commitments |
| `search_city_services` | `alternatives` | Searching alternatives | Searched alternatives |
| `request_replan` | `replan` | Requesting replan | Requested replan |
| unknown | raw tool name | `Started · <tool>` | `Completed · <tool>` |

- **Durations** are milliseconds from `AgentRunEvent.duration_ms`. They appear
  in two places: the row's `<code class="timeline-step__tool">` as
  `tool_name · {duration_ms}ms`, and the summary line as `· {duration_ms}ms`.
  Recorded values: 180 ms and 140 ms (completed inspections), 620 ms
  (city-service search), 6000 ms (failed inspection). Events without a recorded
  duration render no `ms` suffix (never a fabricated number).
- **Timestamps** come from the recorded ISO string. The `<time>` element keeps
  the full value in `dateTime` and displays `timestamp.slice(11, 23)` →
  `HH:MM:SS.mmm` (e.g. `08:12:00.420`). 时间戳原样来自录制事件。

---

## 5. Recorded fixture replay rules

`AgentRunTimeline` is the replay engine for `fixture` runs:

- Initial `visibleCount` is `0` for fixtures and `sourceEvents.length` when
  `isLive`. 初始只显示 0 条录制事件。
- `visibleCount` advances **only** on:
  1. explicit user action — `timeline-next` (`Next event`), `timeline-prev`
     (`Previous event`), `timeline-replay` (`Replay recorded timeline`);
  2. `requestAnimationFrame` replay of recorded event gaps while `replaying`.
- **No `setTimeout`/`setInterval` advances progress.** The only timer in the
  Copilot feature is the `setTimeout(..., 0)` used by `CopilotDock` to schedule
  focus when the panel opens; it does not touch `visibleCount`. 进度绝不使用
  计时器伪造。
- The rAF replay computes the gap from the **recorded** timestamps:
  `recordedGap = clamp(Date.parse(next.timestamp) − Date.parse(current.timestamp), 120, 900)` ms,
  and advances at most one event per frame once that long has elapsed
  (`max(120, min(900, …))`). First event uses a 120 ms floor.
- `prefersReducedMotion()` short-circuits replay: `startReplay()` sets
  `visibleCount = sourceEvents.length` immediately and never animates.
- `timeline-stop` (shown only for `!isLive`) calls `stopReplay()`: it sets
  `replaying = false`, `replayStopped = true`, calls `onStop?.()`, and forces
  run status to `stopped`. It never appends a synthetic event.
- **Badge / source truth:** the header renders `RuntimeTruthBadge` with
  `source = "RECORDED_FIXTURE"`; the badge shows `RECORDED_FIXTURE` and its
  title tooltip is `runtime.fixtureNote` ("Recorded Hermes event replay. This is
  not a live run."). The timeline also sets `data-source="RECORDED_FIXTURE"` and
  shows `<p data-testid="timeline-source">` with the `timeline.recorded` banner
  "Replaying recorded events only · progress never advances on a timer."
- **Replay-stopped text:** when `replayStopped` is true the UI renders a
  `role="status"` banner with `timeline.stoppedLocally`:
  **"Replay stopped locally. No server event was fabricated."**
  （中文："回放已在本地停止，未伪造任何服务端事件。"）
- Event count footer: `timeline.eventCount` → "{visible} of {total} recorded events".

Acceptance test 4 protects this: after opening the recorded Hermes run it waits
1500 ms and asserts `timeline-step` count is still `0` before any click.

---

## 6. LIVE contract

`AgentRunTimeline` accepts:

```ts
fixture?: AgentRunFixture;
liveEventsUrl?: string;      // EventSource-shaped endpoint URL
liveEvents?: AgentRunEvent[]; // already-parsed events
onStop?: () => void;
onApproval?: (state: ApprovalState) => void;
compact?: boolean;
```

- `isLive = Boolean(liveEventsUrl || (liveEvents && liveEvents.length > 0))`.
- `sourceEvents = liveEvents ?? fixture?.events ?? []`.
- When live, `visibleCount` starts at the full array (live events are already
  server truth; the timeline does not replay them), `data-source="LIVE"`,
  `sourceLabel()` returns `LIVE`, and the fixture banner is hidden.
- **EventSource-shaped API:** the component intentionally consumes the
  `liveEventsUrl` + parsed `liveEvents` pair rather than constructing an
  `EventSource` itself. The merge adapter in the main worktree should open
  `new EventSource(liveEventsUrl)`, parse `message` payloads into
  `AgentRunEvent[]`, and pass them as `liveEvents`; the component then renders
  them as LIVE. This keeps transport out of the presentational component.
- **Runtime identity labels** (`RuntimeTruthBadge`, truth object built as
  `{ semantic: "DeepSeek", execution, truth: "CityNexus", source, status: "ready" }`):
  - `runtime.semantic` → **DeepSeek** (semantic layer).
  - `runtime.execution` → `executionLabel(execution)`; for the standard path
    `HERMES_NATIVE_MCP` maps to `runtime.hermes` = **"Hermes / CityNexus Truth"**.
    `DIRECT`, `FALLBACK`, `UNAVAILABLE` have their own labels.
  - `runtime.truth` → **CityNexus** (authority; never Hermes).
  - `runtime.source` → `LIVE` | `RECORDED_FIXTURE` | `OFFLINE`.
  - The raw identity is also exposed on `data-execution` (e.g.
    `data-execution="HERMES_NATIVE_MCP"`), and source on `data-source`.
- In the current reference build every Copilot truth object is
  `source: "RECORDED_FIXTURE"` (DIRECT and Hermes alike), so the honest state is
  never mislabelled LIVE. LIVE only appears when real `liveEvents` are supplied.

---

## 7. Approval panel UX inside the timeline

`approval.required` adds an `approval` step, which mounts the panel below the
step list (`steps.some(s => s.status === "approval")`).

1. **Proposal summary** — shown when any visible event is `proposal.created`:
   `<div class="proposal-summary" data-testid="proposal-summary">`, title
   `approval.proposal` ("Proposal summary"), copy `approval.proposalDetail`
   ("Indoor museum window replaces the outdoor market window; cost unchanged.").
2. **Approval panel** — `<div class="approval-panel" data-testid="approval-panel"
   data-approval-state={approvalState} role="group" aria-label="Approval required">`
   with title `approval.title` ("Approval required") and impact copy
   `approval.impact` ("This change replaces an outdoor activity and keeps
   protected commitments feasible.").
3. **Actions** (all render at once):
   - `data-testid="approval-approve"` → `Approve recovery` → `decide("approved")`.
   - `data-testid="approval-reject"` → `Reject and keep plan` → `decide("rejected")`.
   - `data-testid="approval-review"` → `Request changes` → `decide("review_requested")`.
4. **State copy after decision** — `data-testid="approval-state-copy"` prints
   `t('approval.state.<approvalState>') · t('approval.authority')`.
   - `approved` → "Approved · child PlanVersion is authoritative"
   - `rejected` → "Rejected · current plan kept"
   - `review_requested` → "Changes requested · proposal returns to review"
   - `proposal_only` → "Proposal only · no decision yet"
   - **Authority sentence (always appended):** "CityNexus protects confirmed
     commitments and asks before high-impact changes."
5. **CityNexus is the authority.** The badge keeps `truth: "CityNexus"` and
   `execution: "Hermes …"`. Hermes is execution only; it never authorizes.
   `decide()` only sets local `approvalState` and calls the optional
   `onApproval(state)` callback — the reference component performs no mutation
   and fabricates no server event. `AgentRunTimeline` initializes
   `approvalState` to `"proposal_only"` (the panel is visible because of the
   step status, while the state copy reads "no decision yet"); the
   `RecoveryDiff` counterpart initializes to `approval_required` when evidence
   is `verified`. Merge wiring should drive `approvalState` from the server
   approval record rather than from the component default.

---

## 8. Layout and design notes

- **Step marks:** `.timeline-step` is a 3-column grid
  (`18px | minmax(0, 1fr) | auto`) with a 10px round
  `.timeline-step__mark`. Colour per status: pending `--muted`, active `--info`
  (halo `rgba(123,216,255,.18)`), done `--accent`, approval `--warn`, failed
  `--danger`, stopped `#9aa7ad`. The list is capped at `max-height: 340px;
  overflow: auto`. Each row animates in with `step-in`
  (`--cn-motion-fast`), which collapses to ~0 ms under
  `@media (prefers-reduced-motion: reduce)`.
- **`data-status` / `data-*` hooks:**
  - section: `data-testid="agent-run-timeline"`, `data-source`, `data-run-status`, `aria-live="polite"`.
  - summary: `data-testid="timeline-summary"`, `data-status={runStatus}`.
  - row `<li>`: `data-testid="timeline-step"`, `data-status={step.status}`,
    `data-tool={step.toolName ?? ""}`.
  - evidence rows also use `data-evidence-state` and
    `data-approval-state` (see recovery doc).
- **`data-testid` inventory:** `agent-run-timeline`, `timeline-step`,
  `timeline-source`, `timeline-summary`, `timeline-count`, `timeline-expand`,
  `timeline-collapse`, `timeline-prev`, `timeline-next`, `timeline-replay`,
  `timeline-stop`, `proposal-summary`, `approval-panel`, `approval-approve`,
  `approval-reject`, `approval-review`, `approval-state-copy`,
  `runtime-truth`, `runtime-execution`, `runtime-source`, `runtime-status-chip`.
- **Compact / mobile behaviour:** `compact` starts with `expanded = !compact`.
  When compact and collapsed the full `<ol>` is not rendered; instead the user
  gets `timeline-expand` ("Expand full technical timeline"). Expanding renders
  the steps plus `timeline-collapse` ("Collapse technical timeline").
  `CopilotDock` passes `compact={isMobile && !showFullTimeline}` and also offers
  a `copilot-toggle-timeline` button on mobile. The summary (current run status
  + current step label, tool noun and duration) stays visible in the collapsed
  state. This is the "current step first, full technical timeline on demand"
  pattern. 移动端默认只显示当前步骤，展开后才显示完整技术时间线。
- **Long tool name containment:** `.timeline-step__tool` is
  `display:block; max-width:100%; overflow:hidden; text-overflow:ellipsis;
  white-space:nowrap`, inside a `minmax(0,1fr)` column with `.timeline-step
  { min-width: 0 }`. The long-name fixture
  `citynexus.search_city_services_for_rain_safe_indoor_activity_candidates`
  therefore truncates with an ellipsis (full value kept in the `title`
  attribute) and never causes horizontal overflow. Free text uses
  `overflow-wrap: anywhere`. Test 5 asserts the tool box width stays within the
  viewport; tests 2/7/9 assert page overflow ≤ 1px.

---

## 9. Test evidence

`evidence/playwright_results.txt` (run 2026-09-15, 3 projects × 14 tests):
**42 tests total · 36 passed · 6 skipped · 0 failed** (30.0 s).
Each project runs the 11 applicable tests and skips the 2 that are gated to the
other form factor; desktop skips mobile tests 7–8, mobile projects skip
desktop-only tests 1 and 12.

Concrete timeline / approval coverage in `tests/acceptance.spec.ts`:

| Test | What it proves |
|---|---|
| 3 · DIRECT What-If creates no Agent run | A DIRECT what-if shows `WHAT_IF` + `DIRECT` and `agent-run-timeline` count is `0` (no fabricated run). |
| 4 · recorded Hermes run is truthful, approval-gated, never timer-driven | `data-source="RECORDED_FIXTURE"`; `timeline-source` shows the replay banner; `timeline-step` count `0`; after `waitForTimeout(1500)` still `0`; 14 × `timeline-next` → 14 steps; `data-run-status="approval_required"`; first row "Understood request"; row 3 matches `/Check/`; `approval-panel` visible; approve has `btn--approve`, reject has `btn--reject`; clicking approve sets `data-approval-state="approved"` and copy contains "Approved". |
| 5 · failed/stopped readable; long names contained | `fixture-failed` → after 6 next clicks `data-run-status="failed"`, last row `data-status="failed"` and contains "provider"; `fixture-stopped` → 5 next clicks → `data-run-status="stopped"`, last row `data-status="stopped"`; long tool name box width ≤ viewport width. |
| 9 · Chinese long content readable | `?locale=zh` recovery/journey render Chinese copy with no horizontal overflow. |
| 13 · key routes produce no console/page errors | All 9 key routes render `route-heading`; console error list must be empty. |

`tests/visual.spec.ts` captures the evidence screenshots, including
`v18.2-desktop-copilot-approval.png` (timeline advanced to the approval panel)
and `v18.2-mobile-copilot-current-step.png` /
`v18.2-mobile-copilot-expanded.png` (compact vs expanded timeline).

---

## 10. Bilingual quick glossary

| English | 中文 |
|---|---|
| Agent Run Timeline | Agent 运行时间线 |
| Recorded fixture replay | 录制事件回放 |
| Approval required | 需要审批 |
| Approve recovery / Reject and keep plan / Request changes | 批准恢复 / 拒绝并保留原计划 / 请求修改 |
| CityNexus is authoritative; Hermes executes | CityNexus 是权威；Hermes 只负责执行 |
| No server event was fabricated | 未伪造任何服务端事件 |
| Expand full technical timeline | 展开完整技术时间线 |
