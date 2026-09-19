# CityNexus V18.2 — Recovery & Approval UX

Handoff reference for the isolated V18.2 ExperienceLab build.
Source of truth: `reference-app/src/components/RecoveryDiff.tsx`,
`AgentRunTimeline.tsx`, `RuntimeTruthBadge.tsx`, `data/journey.ts`
(`RECOVERY` fixture), `data/hermesFixture.ts`, `types.ts`,
`tests/acceptance.spec.ts`, and `evidence/playwright_results.txt`.
The main Codex worktree (`D:\moodle\CityNexus`) was inspected read-only and was
not modified.

> 中文备注：本文档描述“恢复方案对比”与“审批状态机”的旅行者可读设计、证据状态、
> 视觉区分、文案准则，以及合并到主工作区时的文件级建议。

---

## 1. Traveler-readable recovery diff (BEFORE / AFTER)

`RecoveryDiff` renders one panel, `data-testid="recovery-diff"`
(`<section class="recovery" data-evidence-state={proposal.evidence_state}>`),
designed to be read without any internal vocabulary. The root exposes the
evidence state machine-readably, not only on the inner banner.

**Header**
- Kicker `recovery.kicker` = "RECOVERY"; title `recovery.title` = "Recovery before / after";
  trigger copy `pick(proposal.trigger, locale)` — fixture:
  "Recorded rain band · outdoor market window exposure" (中文：录制降雨带 · 户外市场时间窗暴露).
- `RuntimeTruthBadge` with
  `{ semantic: "DeepSeek", execution: "DIRECT", truth: "CityNexus", source: "RECORDED_FIXTURE" }`.
  CityNexus is the truth; the ticket is a recorded fixture, not a live mutation.

**Two columns**
- `<article class="recovery-col before" data-testid="recovery-before">` — heading
  `recovery.before` ("Before" / 变更前).
- `<article class="recovery-col after" data-testid="recovery-after">` — heading
  `recovery.after` ("After" / 变更后). On screens ≤ 640 px both columns stack
  (`grid-template-columns: minmax(0, 1fr)`), so the comparison stays readable on
  mobile. 移动端上下堆叠显示。

**Each activity row** (`ActivityRow`) shows, in order:
1. **Time** — `<time>{activity.start_at.slice(11, 16)}</time>`, i.e. `HH:MM`.
2. **Title** — the activity name in the active locale.
3. **Facts** — `{environment} · {walking_min} walking · {place}`. Environment is
   localized via `environment.indoor` / `environment.outdoor` /
   `environment.transit` = Indoor / Outdoor / Transit (室内 / 户外 / 交通).
4. **Protected badge** — if `activity.protected`, a `<em>C4</em>` chip.
5. **Changed badge** — in the AFTER column only, an activity with
   `status === "candidate"` gets `<em class="changed-tag">CHANGED</em>`
   (中文无独立标记，沿用 CHANGED).

**Fixture content under test:** BEFORE = "Ancient Culture Street market window"
(outdoor, 11:10, 22 walking); AFTER = "Tianjin Museum indoor window" (indoor,
11:10, 8 walking, candidate/CHANGED).

---

## 2. WHY reasons and PROTECTED commitments

- **WHY** — heading `recovery.why` ("Why" / 原因), list
  `data-testid="recovery-why"`, each `<li>` prefixed by a CSS `→` arrow. Fixture
  reasons:
  1. "Heavy rain forecast during the outdoor window"
  2. "Reduced walking from 22 min to 8 min"
  3. "Protected 17:30 hotel and departure buffer untouched"
  These explain *why the change is being suggested*, in traveler language, before
  any approval control.
- **PROTECTED** — heading `recovery.protectedList` ("Protected" / 受保护), list
  `data-testid="recovery-protected-list"`, each item rendered as
  `✓ {commitment}` in accent green. Fixture commitments:
  - ✓ Haihe River cruise · C4
  - ✓ Riverside hotel check-in
  - ✓ Departure transfer buffer
  The checkmarks are the core trust signal: the proposal preserves confirmed
  commitments. 受保护承诺保持不变是核心信任信号。

---

## 3. Metrics and evidence states

**Metrics grid** (`.recovery__metrics`, three cells; stacks to one column ≤ 640 px):

| Metric | i18n key / label | `data-testid` | Formatting | Fixture value |
|---|---|---|---|---|
| Time delta | `recovery.timeDelta` / "Time delta" | `recovery-time-delta` | `signed(min)` → `0 min`, `+5 min`, `-14 min` | `0 min` |
| Cost delta | `recovery.costDelta` / "Cost delta" | `recovery-cost-delta` (`testIds.recoveryCostDelta`) | `¥0`, `+¥12.50`, `−¥8.00` (U+2212 for negative) | `¥0` |
| Walking delta | `recovery.walkingDelta` / "Walking delta" | `recovery-walking-delta` | `signed(min)` | `-14 min` |
| Travel delta | `recovery.travelDelta` / "Travel delta" | `recovery-travel-delta` (`testIds.recoveryTravelDelta`) | `signed(min)`; contract field `travel_delta_min` | `6` |

> **Merged contract:** the reference `RecoveryDiff` renders four metric cells
> (time, cost, walking, travel). `recovery-travel-delta` and
> `testIds.recoveryTravelDelta` are satisfied by the current build. 参考实现已渲染
> 交通时间变化指标。

**Evidence states** — `.recovery__evidence` carries `data-evidence-state` and
prints `t('recovery.evidence.<state>')`:

| State | Copy (EN) | Styling | Meaning |
|---|---|---|---|
| `verified` | "Verified evidence · approval may proceed" | Accent border/text | Evidence is complete; approval is allowed. |
| `unresolved` | "Evidence unresolved · review before approving" | Dashed neutral | Evidence is incomplete; approval must stay disabled. |
| `stale` | "Evidence stale · refresh before approving" | Dashed neutral | Evidence is outdated; refresh first. |

The `RECOVERY` fixture is `evidence_state: "verified"`, so the panel starts in
`approval_required`. The reference app can also be opened with demo overrides
`?evidence=unresolved#/recovery` and `?evidence=stale#/recovery`; in both cases
the root and banner report that state, `recovery-approve` is disabled, and the
approval state stays `proposal_only` with the review/refresh copy (acceptance
test 14). `verified_evidence` (`route_provenance`,
`source_provider`, `snapshot_id`) is disclosed behind the collapsed
`<details class="technical">` summary together with the explanation and
"RECORDED_FIXTURE · Fixture replay · no backend mutation".

---

## 4. Approval state machine

`ApprovalState` = `proposal_only | approval_required | approved | rejected |
review_requested`. Both `RecoveryDiff` and `AgentRunTimeline` expose the current
state on `data-approval-state` and render the sentence
`t('approval.state.<state>') · t('approval.authority')`.

| State | English copy | How the UI communicates it | Transition in |
|---|---|---|---|
| `proposal_only` | "Proposal only · no decision yet" | Proposal visible; no decision recorded. `RecoveryDiff` starts here when `evidence_state !== "verified"`. 仅方案，尚未决定 | initial (unverified evidence); timeline default |
| `approval_required` | "Approval required" | High-impact change awaits the traveler; warn-tinted panel. `RecoveryDiff` starts here when evidence is `verified`. 需要审批 | initial (verified evidence) |
| `approved` | "Approved · child PlanVersion is authoritative" | Panel turns accent; approval recorded as the authorizing decision. 已批准，子 PlanVersion 成为权威版本 | `approval-approve` / `recovery-approve` |
| `rejected` | "Rejected · current plan kept" | Panel turns danger-toned; no mutation. 已拒绝，保留当前计划 | `approval-reject` / `recovery-reject` |
| `review_requested` | "Changes requested · proposal returns to review" | Neutral; proposal returns to review rather than being applied. 已请求修改，方案返回复核 | `approval-review` / `recovery-review` |

**Decision buttons → state**
- Approve → `approved` (`.btn--approve` / `data-testid="approval-approve"` or
  `"recovery-approve"`).
- Reject and keep plan → `rejected` (`.btn--reject`).
- Request changes → `review_requested` (plain `.btn`).

**Initialization nuance for merge:** `RecoveryDiff` derives the initial state
from evidence (`verified → approval_required`, otherwise `proposal_only`);
`AgentRunTimeline` always initializes to `proposal_only` even while the approval
step is visible. Both only change local state and call `onApproval?.(state)` /
nothing respectively — **no server mutation in the reference**. Real wiring must
persist the decision through the CityNexus approval API and then re-derive state
from the server. 审批状态必须最终以服务端记录为准。

**Authority invariant:** the state copy always appends
`approval.authority` = "CityNexus protects confirmed commitments and asks before
high-impact changes." Hermes never appears as the authorizer.

---

## 5. Visual distinction rules

| Control | Class | Visual rule | Why |
|---|---|---|---|
| Approve | `.btn--approve` | **Filled accent**: `linear-gradient(145deg, var(--accent), #1c9c84)`, dark text `#04120f`, transparent border, `font-weight: 800`. | The affirmative, constructive default. 实心强调色 |
| Reject and keep plan | `.btn--reject` | **Danger outline only**: border `rgba(255,107,95,.6)`, text `#ffb0a8`, low-alpha danger background. Not filled. | Destructive intent without shouting. 危险色描边，非实心 |
| Request changes | plain `.btn` | Neutral surface/border. | Neither accept nor destroy; returns to review. 中性按钮 |

**Panel-level state colour** (`.approval-panel`):
- Default / waiting: warn border + `rgba(245,185,66,.08)` background.
- `data-approval-state="approved"`: accent border/background.
- `data-approval-state="rejected"`: danger border/background.
- `review_requested` and `proposal_only` keep the neutral/warn treatment.

**Evidence gate (unresolved / stale):**
- `recovery-approve` is `disabled={proposal.evidence_state !== "verified"}`.
  The button stays visible (do not hide it) so the traveler sees the blocked
  action, and the evidence banner provides the next action:
  "Evidence unresolved · review before approving" /
  "Evidence stale · refresh before approving".
- The reject and request-changes actions remain available, so the traveler can
  always keep the current plan. 证据未验证时只禁用“批准”，其余动作仍可用。
- The timeline approval panel has no evidence prop today; its fixture path is
  always verified. When wiring live evidence, apply the same gate to
  `approval-approve`.

**Avoid giant red error walls.** Danger is scoped to the reject outline and the
rejected panel state. Runtime failures use `.runtime-banner` (neutral layout,
one next-action button) plus `RuntimeStatusBanner`; the copy explains what still
works ("CityNexus can still answer DIRECT and deterministic questions. No live
Hermes tool run was started."). No full-bleed red screens, no blocking modals.
避免整屏红色错误墙；危险色仅用于局部、可恢复的控件。

---

## 6. Language guidelines

**Never imply Hermes is the authorization authority.**
- Hermes is **execution**; CityNexus is **truth / authority**. The badge encodes
  this structurally: `semantic: DeepSeek`, `execution: Hermes …`,
  `truth: CityNexus`.
- Do write: "CityNexus protects confirmed commitments and asks before
  high-impact changes"; "Approval recorded by CityNexus · child PlanVersion
  became authoritative"; "CityNexus requires traveler approval before this
  high-impact recovery".
- Do not write: "Hermes approved", "Hermes will apply the change", "the agent
  decided", or anything that makes the execution engine the decider.
  Hermes 只负责执行，绝不作为授权主体。

**CityNexus protects confirmed commitments and asks before high-impact
changes.** Recovery copy leads with preservation (`✓` protected list, "keeps
protected commitments feasible") and only then presents the change.

**Avoid giant red error walls.** Prefer calm, specific, single-next-action
language: state what happened, what is still safe/available, and one button.
Failure copy should not blame the traveler and should not invent alternatives.

**Truthful fixture language.** Reference copy says "Fixture replay · no backend
mutation" and "Recorded …"; approvals in the reference do not mutate anything.
Do not upgrade recorded results to LIVE wording. 录制内容不得表述为实时结果。

**Bilingual.** All user-facing strings live in the `en` / `zh-CN` dictionaries
in `i18n.tsx`; keep keys mirrored and keep Chinese long-form readable (no
horizontal overflow — acceptance test 9).

---

## 7. Data / test-id inventory

**Recovery panel (`RecoveryDiff.tsx`)**
| Selector | Value | Element |
|---|---|---|
| Panel | `recovery-diff` + `data-evidence-state` | `<section class="recovery">` |
| BEFORE column | `recovery-before` | `<article class="recovery-col before">` |
| AFTER column | `recovery-after` | `<article class="recovery-col after">` |
| WHY list | `recovery-why` | `<ul>` of reasons |
| Protected list | `recovery-protected-list` | `<ul>` of `✓` commitments |
| Time delta | `recovery-time-delta` | `<b>` |
| Cost delta | `recovery-cost-delta` | `<b>` |
| Walking delta | `recovery-walking-delta` | `<b>` |
| Travel delta | `recovery-travel-delta` | rendered as the fourth metric cell (`+6 min` in the fixture) |
| Evidence | (class `.recovery__evidence`) `data-evidence-state` | banner |
| Approval group | `recovery-approval` + `data-approval-state` | `role="group"` |
| Approve / Reject / Review | `recovery-approve` / `recovery-reject` / `recovery-review` | buttons |
| State copy | `recovery-approval-state` | `<p>` |

**Timeline approval panel (`AgentRunTimeline.tsx`)**
| Selector | Value | Element |
|---|---|---|
| Proposal summary | `proposal-summary` | `<div class="proposal-summary">` |
| Approval group | `approval-panel` + `data-approval-state` | `role="group"` |
| Approve / Reject / Review | `approval-approve` / `approval-reject` / `approval-review` | buttons |
| State copy | `approval-state-copy` | `<p>` |
| Step status hook | `timeline-step` + `data-status` / `data-tool` | rows |

**Types driving the UI:** `RecoveryProposal` (`before`, `after`, `removed`,
`added`, `why`, `protected_commitments`, `time_delta_min`, `cost_delta_minor`,
`travel_delta_min`, `walking_delta_min`, `protected_commitments_preserved`,
`evidence_state`, `verified_evidence`, `explanation`), `JourneyActivity`
(`environment`, `walking_min`, `protected`, `status`), `ApprovalState`,
`AgentRunEvent`.

---

## 8. Playwright coverage

`tests/acceptance.spec.ts` (14 acceptance tests), run against the production
`dist` via `scripts/serve-dist.mjs` on `http://127.0.0.1:4179`:

| Test | Recovery / approval assertion |
|---|---|
| 4 · recorded Hermes run truthful, approval-gated, never timer-driven | `data-source="RECORDED_FIXTURE"`; 14 next clicks → `data-run-status="approval_required"`; `approval-panel` visible; `approval-approve` has `btn--approve`; `approval-reject` has `btn--reject`; click approve → `data-approval-state="approved"`; `approval-state-copy` contains "Approved". |
| 6 · recovery diff explains why, protects commitments, makes approval distinct | `recovery-diff` visible; BEFORE contains "Ancient Culture Street"; AFTER contains "Tianjin Museum"; WHY contains "Heavy rain"; protected list contains "Haihe River cruise"; time delta exactly `0 min`; cost delta `¥0`; walking delta `-14 min`; `recovery-approve` has `btn--approve`; `recovery-reject` has `btn--reject`; approve → state `approved`; review → state `review_requested`; state copy contains "Changes requested". |
| 9 · Chinese long content readable | `?locale=zh#/recovery` → `recovery-why` contains "强降雨"; page horizontal overflow ≤ 1 px. |
| 13 · key routes produce no console/page errors | `/recovery` renders `route-heading`; no console/page errors. |
| 14 · unresolved and stale evidence block approval with a clear next action | `?evidence=unresolved#/recovery` → `recovery-diff` and `.recovery__evidence` report `data-evidence-state="unresolved"`, `recovery-approve` is disabled, `recovery-approval-state` contains "Proposal only"; `?evidence=stale#/recovery` → banner reports `stale` and `recovery-approve` is disabled. |

`tests/visual.spec.ts` emits `v18.2-desktop-recovery.png` and
`v18.2-mobile-recovery.png` as the recovery frames of its desktop and mobile
evidence sets. The `?evidence=unresolved` / `?evidence=stale` demos above are
covered by acceptance test 14 on every viewport project.

**Observed results** (`evidence/playwright_results.txt`, 2026-09-15):
**42 total · 36 passed · 6 skipped · 0 failed · 30.0 s** across
`desktop-chromium` (1440×900), `mobile-chromium` (390×844) and
`mobile-large-chromium` (430×932). Recovery/approval tests 4, 6, 13 and 14 run
(and pass) on all three projects; the 6 skips are the form-factor-gated tests.
`evidence/build_results.txt`: `tsc --noEmit` PASS; `vite build` PASS.

---

## 9. Merge guidance

The reference build is isolated. Merge by **porting components and contracts**,
not by copying the reference app's wiring. 参考应用为隔离验证；合并时只移植组件与契约。

**New, self-contained files in the reference build (low-conflict — port
candidates):**
- `components/AgentRunTimeline.tsx` + `components/RuntimeTruthBadge.tsx` (pair;
  the timeline depends on the badge). The main worktree has no equivalent
  component yet, so these are the cleanest port.
- `components/RecoveryDiff.tsx` (traveler-facing view; the main worktree keeps
  `V14RecoveryTruthPanel` as the server-backed authority).
- `data/hermesFixture.ts` (recorded fixtures only; no runtime dependency).
- Contract types to add under the main worktree's contracts layer:
  `AgentEventType`, `AgentRunEvent`, `AgentRunFixture`, `TimelineStepStatus`,
  `TimelineStep`, `RuntimeTruth`, `RuntimeIdentity`, `ApprovalState`,
  `RecoveryProposal`, `JourneyActivity`.
- Test specs `tests/acceptance.spec.ts` (timeline/recovery blocks) and
  `tests/visual.spec.ts` screenshots.
- The reference `components/CopilotDock.tsx` is a **UX specification**, not a
  drop-in: the main worktree already has its own API-backed
  `features/agent/CopilotDock.tsx` (see below). Port the reference's timeline /
  approval UX rules into that component instead of replacing it.

These files only import each other, React, and i18n helpers, so they conflict
minimally. 这些组件彼此独立，冲突面小。

**Existing-file wiring that is reference-only (adapt, do not copy wholesale):**
- `reference-app/src/App.tsx` — local hash routing, `activeFixture` state and
  route → component map. In the main worktree this role belongs to
  `frontend/src/app/V8Experience.tsx` + `frontend/src/routes/v8Routes.ts`.
- `reference-app/src/i18n.tsx` — flat `en`/`zh-CN` dictionaries. The main
  worktree uses `frontend/src/i18n/LocaleContext.tsx` (+ `tripOperations.ts`);
  migrate keys into that system, keeping `approval.*`, `recovery.*`,
  `timeline.*` names.
- `reference-app/src/testids.ts` — the main worktree owns
  `frontend/src/contracts/testIds.ts` with different names
  (`replanPanel`, `replanEvidence`, `replanDiff`, `replanDeltas`,
  `protectedCommitment`, `acceptReplan`, `rejectReplan`). **Add** the reference
  keys (`recovery-diff`, `recovery-*`, `approval-*`, `agent-run-timeline`,
  `timeline-*`) without renaming existing ones. 新增键，不改名。
- `reference-app/src/styles/app.css` — merge the `.timeline-step*`,
  `.approval-panel`, `.btn--approve`, `.btn--reject`, `.recovery*` rules into
  `frontend/src/styles.css`; do not replace the whole stylesheet.
- `reference-app/src/motion.ts` — the main worktree already has
  `frontend/src/lib/viewTransition.ts`; keep reduced-motion handling there.
- `data/journey.ts` — sample/reference data only; replace with real API data.

**Component-level integration notes** (main-worktree state observed
2026-09-15; the worktree was being actively updated, so re-check before merging)
- `features/agent/AgentRunRail.tsx` (`pending | active | done | approval |
  failed`) is now imported by the main `features/agent/CopilotDock.tsx`, so it is
  live code — keep it. It has no `stopped`, `duration_ms`, replay, or LIVE path.
  Either extend the rail or render the reference `AgentRunTimeline` instead;
  `AgentRunTimeline` owns `stopped`, durations, recorded replay, LIVE, and the
  approval panel.
- The main worktree now has an API-backed `features/agent/CopilotDock.tsx`: it
  already declares the same 13-event `EVENT_TYPES`, streams `run.events_url`
  through `new EventSource(...)`, stores merged events, and calls
  `cityNexusApi.approveAgentAction(journeyId, approvalId)`. **Do not overwrite it
  with the reference dock.** Port the reference UX into it:
  - map `run.events_url` → the reference `liveEventsUrl` and
    `initial_events` / SSE payloads → `liveEvents` / `AgentRunEvent[]`
    (`NativeRuntimeEvent` already carries `duration_ms` and `runtime_identity`);
  - add `stopped` as a first-class step/run status (main `statusForEvent`
    currently maps `run.stopped` → `failed` and defaults unknown events to
    `active`, while the reference maps only `tool.started` → `active` and
    `run.stopped` → `stopped`);
  - adopt the reference duration formatting (`{duration_ms}ms`), recorded-replay
    rules, runtime truth badge, and the proposal/approval panel copy.
- The reference `AgentRunTimeline` is presentational (fixture + `liveEvents`),
  while the main dock owns API/SSE state. Wire the dock's merged `events` array
  into the timeline component rather than duplicating transport.
- The main worktree already has a server-backed
  `features/recovery/V14RecoveryTruthPanel.tsx` (fetches
  `/api/v1/journeys/{id}/replans`, accepts a `PRESENTED` proposal via the API).
  `RecoveryDiff` is the **traveler-readable presentation layer** over the same
  proposal contract: map `diff.removed` / `diff.added`,
  `diff.cost_delta_minor`, `diff.travel_delta_min`,
  `locked_commitments_preserved`, `verified_evidence`, and `explanation` into
  `RecoveryProposal`. Keep V14 (or the authoritative API) as the single data and
  mutation path; `RecoveryDiff` must not invent mutations.
- Prefer `frontend/src/contracts/replan.ts` / `journeyTwin.ts` (or the generated
  API types) as the home for merged types; keep a single source of truth rather
  than duplicating `RecoveryProposal`.

**Behavioral invariants to preserve after merge**
- Recorded fixtures never present as LIVE; no timer-driven progress.
- `data-run-status` / `data-approval-state` / `data-evidence-state` are the
  machine-readable state hooks the tests rely on.
- Approval is a CityNexus decision: persist through the approval API, then
  re-derive UI state from the server record. The reference components are
  presentational only. 审批必须由 CityNexus 服务端记录并回读。

---

## 10. Bilingual quick glossary

| English | 中文 |
|---|---|
| Recovery before / after | 恢复前 / 后对比 |
| BEFORE / AFTER | 变更前 / 变更后 |
| Why | 原因 |
| Protected commitments | 受保护承诺 |
| Time / Cost / Walking / Travel delta | 时间 / 费用 / 步行 / 交通时间变化 |
| Verified / unresolved / stale evidence | 已验证 / 未解决 / 已过期证据 |
| Proposal only · no decision yet | 仅方案 · 尚未决定 |
| Approval required | 需要审批 |
| Approve recovery / Reject and keep plan / Request changes | 批准恢复 / 拒绝并保留原计划 / 请求修改 |
| Approved · child PlanVersion is authoritative | 已批准 · 子 PlanVersion 成为权威版本 |
| Rejected · current plan kept | 已拒绝 · 保留当前计划 |
| Changes requested · proposal returns to review | 已请求修改 · 方案返回复核 |
| CityNexus protects confirmed commitments and asks before high-impact changes | CityNexus 保护已确认承诺，并在高影响变更前征得同意 |
| Fixture replay · no backend mutation | 录制回放 · 不修改后端 |

