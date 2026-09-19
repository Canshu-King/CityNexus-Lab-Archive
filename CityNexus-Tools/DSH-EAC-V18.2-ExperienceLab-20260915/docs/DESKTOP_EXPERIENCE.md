# Desktop Experience — CityNexus V18.2 Reference

> **Scope**: `reference-app` desktop behavior at **1440 × 900** (`desktop-chromium`), with the
> intermediate 1024–1279px layout called out where it differs.
> **Grounding**: `src/App.tsx`, `src/components/*.tsx`, `src/styles/app.css`,
> `src/i18n.tsx`, `tests/acceptance.spec.ts`, `evidence/playwright_results.txt`.
> **Honesty rule**: every recorded run is labelled `RECORDED_FIXTURE`; the UI never labels a
> fixture `LIVE`.

---

## 1. Navigation IA

The desktop shell is a three-column layout — nav, main, Copilot — on a sticky top bar.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ topbar: ◈ CityNexus   [V18 Experience Reference] [Isolated reference…]  EN/中文 │
├───────────────┬───────────────────────────────────────┬──────────────────┤
│ TODAY         │  main heading (route-heading)         │  Copilot dock    │
│  Journey      │  RuntimeStatusBanner (only if ≠ ready)│  (open by default│
│  Live         │  route content…                       │   ≥1024px)       │
│  Map          │                                       │                  │
│ PLAN          │                                       │                  │
│  Studio/Stay/Discover                                 │                  │
│ TRAVEL        │                                       │                  │
│  Wallet/Copilot                                       │                  │
│ SYSTEM ▸      │  (collapsed by default)               │                  │
│  Recovery/Intelligence/Twin                           │                  │
└───────────────┴───────────────────────────────────────┴──────────────────┘
```

`DESKTOP_GROUPS` in `src/components/TravelerNav.tsx` defines four groups:

| Group | Label (EN / 中文) | Items (route) | Notes |
| --- | --- | --- | --- |
| **TODAY** | Today / 今天 | Journey (`journey`), Live (`live`), Map (`map`) | Primary group |
| **PLAN** | Plan / 计划 | Studio (`studio`), Stay (`stay`), Discover (`discover`) | Reference placeholders |
| **TRAVEL** | Travel / 出行 | Wallet (`wallet`), Copilot (`copilot`) | Copilot also has a dock |
| **SYSTEM** | System / 系统 | Recovery (`recovery`), Intelligence (`intelligence`), Twin (`twin`) | **Secondary / collapsed by default** |

- **SYSTEM is secondary and collapsed by default.** It renders as a
  `.desktop-nav__group-toggle` button with `aria-expanded={false}`; its items are not in the DOM
  until expanded. Acceptance test 1 asserts `nav-recovery` has count 0 before the toggle click and
  becomes visible after (along with `nav-intelligence`, `nav-twin`).
- The active item gets `.active`, `aria-current="page"`, and an inset accent bar
  (`box-shadow: inset 3px 0 0 var(--accent)`).
- Route aliases: `#/today` → `journey`; an unknown/empty hash → `journey`. Route space:
  `journey, live, map, studio, stay, discover, wallet, copilot, recovery, intelligence, twin, me`.
- `<h1>` is bound to `data-testid="route-heading"`; the header also shows
  `天津/Tianjin · V18.2-reference-r1`.
- The top bar carries `app.brand`, `app.reference`, `app.isolated`, a warning pill when runtime
  status ≠ `ready` (`data-testid="topbar-runtime-status"`), and the locale toggle.

**Bilingual note / 术语**: group labels are `nav.today` 今天, `nav.plan` 计划, `nav.travel` 出行,
`nav.system` 系统. The locale toggle shows the *target* language (`中文` in EN, `EN` in zh-CN).

---

## 2. Journey Pulse (primary surface)

`JourneyPulse` (`src/components/JourneyPulse.tsx`) is the first content block on `/#/journey` and
`/#/live`. It is fed by `PULSE` in `src/data/journey.ts`. The header carries the localized
"JOURNEY PULSE / 行程脉搏" kicker, the title *"Only what matters right now."*, and a compact
`RuntimeTruthBadge` (`DIRECT` + `RECORDED_FIXTURE`).

Four cards, each with its own test id, are laid out in a 2×2 grid (`repeat(2, minmax(0,1fr))`):

| Card | Test id | Content (reference data) |
| --- | --- | --- |
| **NOW / 现在** | `pulse-now` | "Five Great Avenues morning walk / 五大道晨间步行" · `08:41` · `on route · 12 min ahead` · recorded-fixture note |
| **NEXT / 下一步** | `pulse-next` | "Haihe River cruise / 海河游船" · `09:30` · `37 min buffer` · "Protected commitment. Do not trade this buffer for a market stop." |
| **RISK / 风险** | `pulse-risk` | `Watch · Rain band arriving 11:20` · `RECORDED_FIXTURE` badge · 68% shower band detail |
| **PRIMARY ACTION / 首要动作** | `pulse-action` | "Review rain-safe recovery" · reason line · primary button → `recovery` |

Design intent:

- Order and weight encode priority: NOW and NEXT are informational; RISK is colour-coded by level
  (`low`/`watch`/`high` → accent/warn/danger borders); PRIMARY ACTION is the only card with a
  filled CTA and a gradient background.
- Risk source is shown inline as `RECORDED_FIXTURE`, not hidden in disclosure.
- The card text never contains internal terms: test 1 asserts the pulse text does **not** contain
  `PlanVersion` or `CP-SAT`.

---

## 3. Today timeline

`TodayTimeline` (`src/components/TodayTimeline.tsx`, `data-testid="today-timeline"`) renders the
seven `ACTIVITIES` in order. Each row shows:

- a fixed 52px time column (`HH:MM` from `start_at`),
- the localized activity title (overflow-wrapped),
- `Environment · status` (`Indoor/Outdoor/Transit` · `now/upcoming/done/proposed`),
- a `Protected / 受保护` pill when `protected` is true.

The current activity (`status: "current"`) gets an accent left border. Protected commitments visible
here include the Haihe cruise, hotel check-in, and departure transfer buffer.

On the Journey page the timeline sits beside the Live map in `.journey-lower`
(`minmax(0,0.9fr) minmax(0,1.1fr)`), below Journey Pulse. Acceptance test 2 asserts Pulse is above
both Today timeline and Live map.

---

## 4. Live map

`MapCanvas` (`src/components/MapCanvas.tsx`, `data-testid="map-canvas"`) uses MapLibre GL with an
**inline recorded style** — no network tile source, `attributionControl: false`:

- route: `recorded-fixture://route-rain-001` (a 5-point LineString across Tianjin);
- stops: Wudadao, **Haihe cruise · C4** (protected, larger amber circle), Ancient Culture Street,
  Tianjin Museum (blue circles).

Exposed contract attributes:

| Attribute | Meaning |
| --- | --- |
| `data-map-ready` | `true` after `load` |
| `data-map-mode` | `maplibre` or `fallback-static` |
| `data-camera-contract` | `flyTo/fitBounds` |
| `data-camera-duration` | `motionDuration("map")` → `650` normally, `0` under reduced motion |

Controls (bottom overlay, `min-height: 44px`):

- **Recenter** → `map.flyTo(mapCameraOptions(CAMERA))` with the `map` duration token (650ms).
- **Fit route** → `map.fitBounds(bounds, fitBoundsOptions(...))` with padding 48 and the `map` token.
- **Camera contract** readout (`data-testid="map-camera-status"`) shows `flyTo · 650ms` /
  `fitBounds · 650ms` after use.

If MapLibre/WebGL throws or emits `error`, `data-map-mode="fallback-static"` and a static SVG route
with the localized note `WebGL unavailable · static route evidence shown` is shown. On the dedicated
`/#/map` route the map is the large pane (`min-height: 560px`) beside the `MapBottomSheet`
(desktop grid `minmax(0,1fr) 340px`); on the Journey page it is a preview (`min-height: 420px`).

---

## 5. Copilot dock behavior

`CopilotDock` (`src/components/CopilotDock.tsx`, `data-testid="copilot-dock"`) is the right column
at ≥1280px and an in-flow panel at 1024–1279px.

### 5.1 Open / collapsed states

| State | Class | Desktop behavior |
| --- | --- | --- |
| Open | `.copilot.is-open` | `.copilot-panel` sticky at `top: 84px`, `max-height: calc(100vh - 108px)`, scrollable |
| Collapsed | `.copilot.is-collapsed` | `.copilot-edge` button (`min-height: 84px`) with a status dot; `.copilot-mini` composer only at ≤1279px |

- Initial state: `window.matchMedia("(min-width: 1024px)").matches` → **open by default on desktop**.
- Navigating to `#/copilot` forces open.
- The status dot is `.live` (accent) when the latest runtime is `ready`, `.active` (info) when a
  fixture is attached, `.warn` (danger) otherwise.

### 5.2 Panel contents (top → bottom)

1. Header: kicker `COPILOT DOCK`, title, subtitle `DeepSeek meaning · runtime truth`, close `×`
   (44×44, `copilot.close`).
2. `RuntimeTruthBadge` for the latest message runtime.
3. `RuntimeStatusBanner` when that runtime status ≠ `ready`, with a journey-return action.
4. `.copilot-history` (`aria-live="polite"`) — empty-state guidance or message bubbles.
   Each `.bubble` has `data-testid="copilot-message"` and `data-role` (`user`/`assistant`);
   chips expose the semantic intent (`data-testid="semantic-interpretation"`), the What-If status,
   and the execution identity (`data-testid="runtime-execution"`).
5. Mission strip (`data-testid="copilot-mission"`): `Current mission` + scenario + `Approval needed`
   chip when the fixture contains `approval.required`.
6. Recorded-scenario switcher: `fixture-completed`, `fixture-approved`, `fixture-failed`,
   `fixture-stopped`.
7. `AgentRunTimeline` for the active fixture (full/expanded on desktop — `compact` is false).
8. Quick actions: `copilot-quick-whatif`, `copilot-quick-hermes`, `copilot-quick-fallback`,
   `copilot-quick-unavailable`.
9. Composer: `<textarea data-testid="copilot-input">` + send button
   (`data-testid="copilot-send"`).

### 5.3 Keyboard and focus

- **Escape** anywhere while open closes the dock (`window keydown` listener), sets
  `restoreFocusRef`, and returns focus to the collapsed `.copilot-edge` button.
- The collapsed edge button is a real `<button>`; **Enter** re-opens and focuses the input/close.
- On open, focus moves to the close button (desktop) or the input (mobile) via a 0ms focus nudge.
- Acceptance test 12: open → Escape → edge focused → Enter → panel open with
  `copilot-input` visible → Escape → edge focused again.

### 5.4 Message routing (reference heuristics)

- **What-If** quick action → user bubble + assistant bubble with `WHAT_IF`, runtime `DIRECT`,
  `simulation_only · no mutation`, Changed/Protected details, and a recovery shortcut.
  No `agent-run-timeline` is created (acceptance test 3).
- **Hermes** quick action → assistant bubble with `REQUEST_REPLAN`, runtime `HERMES_NATIVE_MCP`, and
  the recorded fixture attached.
- Free text matching `/replan|替代|rain|雨|alternative|change/i` → Hermes fixture; otherwise →
  DIRECT What-If. This regex is a reference stand-in for the real semantic compiler.

---

## 6. Runtime truth

`src/components/RuntimeTruthBadge.tsx` renders the three-part truth contract
**Semantic → Execution → Truth** plus a source badge and (when needed) a status chip.

| Element | Test id | Notes |
| --- | --- | --- |
| Badge container | `runtime-truth` | `data-source`, `data-execution`, `data-runtime-status` |
| Execution value | `runtime-execution` | `DIRECT` / `Hermes / CityNexus Truth` / `FALLBACK` / `UNAVAILABLE` |
| Source badge | `runtime-source` | `LIVE`, `RECORDED_FIXTURE`, or `OFFLINE` |
| Status chip | `runtime-status-chip` | Only when status ≠ `ready` |
| Status banner | `runtime-status-banner` | `data-status`; hidden when `ready`; `role="status"` + action button |
| Top-bar warning pill | `topbar-runtime-status` | Shown when status ≠ `ready` |

The **Me** page exposes the demo matrix: `runtime-state-value`, buttons
`runtime-demo-ready / runtime-demo-hermes_unavailable / runtime-demo-deepseek_unavailable /
runtime-demo-provider_unavailable / runtime-demo-offline_stale`, and `reduced-motion-state`.
The same statuses are addressable as `/?runtime=<status>`.

Message copy is deliberately honest, e.g.:

- `hermes_unavailable`: "CityNexus can still answer DIRECT and deterministic questions. No live
  Hermes tool run was started."
- `deepseek_unavailable`: "Semantic interpretation is degraded. Deterministic CityNexus facts and
  saved plans remain available."
- `provider_unavailable`: "The last verified provider snapshot is shown as stale. No replacement
  facts are invented."
- `offline_stale`: "Cached journey facts are read-only and clearly marked stale."

---

## 7. Agent timeline on desktop

`AgentRunTimeline` (`src/components/AgentRunTimeline.tsx`, `data-testid="agent-run-timeline"`,
`data-source`, `data-run-status`, `aria-live="polite"`) is the server-truth surface.

- Header: kicker `AGENT RUN TIMELINE`, title *"Server-truth tool progress"*, compact
  `RuntimeTruthBadge`.
- Fixture banner (`data-testid="timeline-source"`) whenever `source === "RECORDED_FIXTURE"`:
  *"RECORDED_FIXTURE · Replaying recorded events only · progress never advances on a timer."*
- Summary (`data-testid="timeline-summary"`, `data-status`): run status label + current step label,
  humanized tool name, and recorded `duration_ms`.
- Steps (`<li data-testid="timeline-step" data-status data-tool>`): status dot
  (done/active/approval/failed/stopped), human label, raw tool name in a code chip
  (ellipsized with `title`), summary, `HH:MM:SS.mmm` timestamp, and a status keyword.
- Proposal summary (`data-testid="proposal-summary"`) appears once a `proposal.created` event is
  visible.
- Approval panel (`data-testid="approval-panel"`, `data-approval-state`) with `btn--approve`
  (`approval-approve`), `btn--reject` (`approval-reject`), and neutral `approval-review`.
- Controls: `timeline-prev` (disabled at 0), `timeline-next` (disabled at end), `timeline-replay`
  (primary), `timeline-stop` (non-live only). Event counter
  (`data-testid="timeline-count"`): "{visible} of {total} recorded events".

**Progress semantics (critical)**

- A recorded run starts at **0 visible events**; nothing auto-advances. Test 4 waits 1.5s and
  confirms the count stays 0.
- **Replay** advances one event per recorded inter-event gap (clamped to 120–900ms) inside a
  `requestAnimationFrame` loop. There is no `setInterval`, and no progress `setTimeout`.
- **Stop** halts replay locally and shows *"Replay stopped locally. No server event was
  fabricated."* (`data-run-status="stopped"`).
- Under `prefers-reduced-motion`, replay jumps straight to the full event set.

**Recorded fixtures** (`src/data/hermesFixture.ts`):

| Fixture | Events | Final run status |
| --- | --- | --- |
| `completed` (`HERMES_RECORDED_RUN`) | 14 | `approval_required` (proposal + approval) |
| `approved` (`HERMES_APPROVED_RUN`) | 15 | `success` (child PlanVersion authoritative) |
| `failed` (`HERMES_FAILED_RUN`) | 6 | `failed` (provider timeout, next action: retry or keep plan) |
| `stopped` (`HERMES_STOPPED_RUN`) | 5 | `stopped` (includes a deliberately long tool name) |

All 13 `AgentEventType` values appear across the fixtures. Tool names are humanized for the primary
label and shown raw for disclosure:

| Raw tool | Human label prefix | Domain meaning |
| --- | --- | --- |
| `inspect_journey` | Checking/Checked Journey | Active journey facts |
| `inspect_twin` | Checking/Checked protected commitments | C4 feasibility |
| `search_city_services` | Searching/Searched alternatives | Indoor candidates |
| `request_replan` | Requesting/Requested replan | CityNexus-owned proposal |

---

## 8. Recovery and approval

`RecoveryDiff` (`src/components/RecoveryDiff.tsx`, `data-testid="recovery-diff"`) renders the
`RECOVERY` proposal from `src/data/journey.ts`.

| Region | Test id | Content |
| --- | --- | --- |
| Header | — | `RECOVERY / 恢复`, trigger copy, compact truth badge (`DIRECT` + `RECORDED_FIXTURE`) |
| Before | `recovery-before` | Ancient Culture Street market window: Outdoor · 22 walking · place |
| After | `recovery-after` | Tianjin Museum indoor window (moved earlier), `CHANGED` tag: Indoor · 8 walking |
| WHY | `recovery-why` | Heavy rain; walking 22→8; protected 17:30 hotel + departure untouched |
| Protected | `recovery-protected-list` | Haihe River cruise · C4, Riverside hotel check-in, Departure transfer buffer |
| Metrics | `recovery-time-delta` = `0 min`, `recovery-cost-delta` = `¥0`, `recovery-walking-delta` = `-14 min` | |
| Evidence | `recovery-diff[data-evidence-state]`, `.recovery__evidence[data-evidence-state]` | `verified` → "Verified evidence · approval may proceed"; `?evidence=unresolved` / `?evidence=stale` → approve disabled, panel starts `proposal_only` |
| Approval | `recovery-approval`, `data-approval-state` | `recovery-approve`, `recovery-reject`, `recovery-review`, `recovery-approval-state` |
| Technical | `<details class="technical">` | `route_provenance`, `source_provider`, `snapshot_id`, `Source: RECORDED_FIXTURE · Fixture replay · no backend mutation` |

- The three deltas answer "what changes?" — time, money, walking. The WHY list and PROTECTED list
  answer "why is this safe?".
- **Approval buttons are visually distinct**: `btn--approve` is a filled accent gradient (accept),
  `btn--reject` is a danger-outline "Keep current plan", and "Request changes" is neutral.
- Approve is **disabled unless evidence is `verified`**; the panel border/background shifts green on
  approved and red on rejected.
- Initial state is `approval_required` when evidence is verified, otherwise `proposal_only`.
- Acceptance test 6 clicks approve → `data-approval-state="approved"`, then review →
  `"review_requested"` with "Changes requested".
- Acceptance test 14 loads `/?evidence=unresolved#/recovery` and `/?evidence=stale#/recovery`,
  asserts the evidence state on the diff and evidence block, and asserts `recovery-approve` is
  **disabled** while the panel reads "Proposal only".

**Known copy inconsistency**: the Journey Pulse technical block hardcodes
`PlanVersion V18.1-reference-r1`, while `JOURNEY.planVersion` and the page header use
`V18.2-reference-r1`. Treat the hardcoded value as stale copy to fix at merge.

---

## 9. Technical disclosure

Internals are available but never lead:

- **Journey Pulse** — `<details class="technical" data-testid="technical-evidence">` is collapsed
  by default (`Technical evidence / 技术证据`) and contains data source, plan version, generated-at,
  and execution identity. Test 1 asserts it has no `open` attribute.
- **Journey page** — a muted line under the map says *"Technical detail stays collapsed until you
  need it."*
- **Recovery** — a `<details>` holds route provenance, provider, snapshot id, and the explanation.
- **Placeholder routes** (Studio, Stay, Discover, Intelligence, Twin) render an isolated-reference
  note plus a collapsed technical disclosure stating no PlanVersion/Gateway/domain mutation occurs.
- The primary surfaces (`pulse`, `recovery`) never expose `PlanVersion`, `CP-SAT`, raw tool ids, or
  Gateway policy language.

---

## 10. Component / testid inventory

### 10.1 Components (`src/components/`)

| Component | File | Responsibility |
| --- | --- | --- |
| `JourneyPulse` | `JourneyPulse.tsx` | NOW/NEXT/RISK/PRIMARY ACTION + collapsed technical evidence |
| `TodayTimeline` | `TodayTimeline.tsx` | Ordered day timeline |
| `DesktopNav`, `MobileNav`, `LocaleToggle` | `TravelerNav.tsx` | Grouped desktop IA, 5-item mobile nav, EN/中文 toggle |
| `CopilotDock` | `CopilotDock.tsx` | Persistent composer, runtime truth, messages, mission, fixtures, approval |
| `AgentRunTimeline` | `AgentRunTimeline.tsx` | Server-truth event replay + approval panel |
| `RecoveryDiff` | `RecoveryDiff.tsx` | Before/after recovery proposal + approval |
| `RuntimeTruthBadge`, `RuntimeStatusBanner` | `RuntimeTruthBadge.tsx` | Semantic/Execution/Truth badge + status banner |
| `MapCanvas` | `MapCanvas.tsx` | MapLibre route map + camera contract + static fallback |
| `MapBottomSheet` | `MapBottomSheet.tsx` | 24/55/90 sheet with drag + keyboard + tabs |

### 10.2 Central test ids (`src/testids.ts`)

`app-shell`, `journey-pulse`, `pulse-now`, `pulse-next`, `pulse-risk`, `pulse-action`,
`technical-evidence`, `runtime-truth`, `runtime-execution`, `runtime-source`, `agent-run-timeline`,
`timeline-step`, `timeline-source`, `timeline-next`, `timeline-prev`, `timeline-replay`,
`timeline-stop`, `copilot-dock`, `copilot-input`, `copilot-send`, `copilot-quick-whatif`,
`copilot-quick-hermes`, `copilot-message`, `copilot-mini-composer`, `recovery-diff`,
`recovery-before`, `recovery-after`, `recovery-cost-delta`, `recovery-travel-delta`,
`recovery-protected`, `map-canvas`, `map-sheet`, `sheet-24`, `sheet-55`, `sheet-90`,
`sheet-handle`, `bottom-nav`, `bottom-nav-item`, `desktop-nav`, `locale-toggle`, `route-heading`.

> `recovery-travel-delta` is rendered as the fourth recovery metric. The protected-commitment
> list uses the literal `recovery-protected-list` test id; `testIds.recoveryProtected` is retained
> in the shared test-id map for contract compatibility.

### 10.3 Inline literal test ids

`topbar-runtime-status`, `today-timeline`, `timeline-summary`, `timeline-count`, `timeline-expand`,
`timeline-collapse`, `proposal-summary`, `approval-panel`, `approval-approve`, `approval-reject`,
`approval-review`, `approval-state-copy`, `recovery-approval`, `recovery-approve`,
`recovery-reject`, `recovery-review`, `recovery-approval-state`, `recovery-why`,
`recovery-protected-list`, `recovery-time-delta`, `recovery-walking-delta`, `sheet-content-24`,
`sheet-content-55`, `sheet-content-90`, `map-camera-status`, `copilot-mission`,
`copilot-toggle-timeline`, `copilot-quick-fallback`, `copilot-quick-unavailable`,
`semantic-interpretation`, `runtime-status-chip`, `runtime-status-banner`, `runtime-state-value`,
`reduced-motion-state`, `fixture-completed`, `fixture-approved`, `fixture-failed`,
`fixture-stopped`, `runtime-demo-<status>`.

---

## 11. Responsive notes

| Breakpoint | Layout | Nav | Copilot |
| --- | --- | --- | --- |
| ≥1280px | `232px / minmax(0,1fr) / 380px` | Full grouped desktop nav | Sticky third column; open by default; no mini composer (`display:none`) |
| 1024–1279px | `200px / minmax(0,1fr)` | Full grouped desktop nav | Spans full width below main (`grid-column: 1/-1`), static; mini composer visible |
| ≤1023px | single column | Desktop nav hidden; 5-item bottom nav | Fixed above bottom nav; edge hidden, mini composer shown |
| ≤640px | single column | bottom nav | Pulse/recovery/metrics stack to one column; Copilot form becomes one column; top-bar meta wraps |

Other desktop details:

- `body { overflow-x: hidden }` and `.app { overflow-x: clip }` prevent horizontal scroll; long
  strings use `overflow-wrap: anywhere` and `min-width: 0` grid tracks.
- `today-timeline li` uses a `52px minmax(0,1fr) auto` grid; map controls wrap and stay ≥44px.
- `.timeline-step` uses `18px minmax(0,1fr) auto`, so the long tool name ellipsizes instead of
  widening the panel.

---

## 12. Bilingual terminology notes / 术语

| EN | 中文 | Desktop surface |
| --- | --- | --- |
| Journey Pulse | 行程脉搏 | Pulse header |
| NOW / NEXT / RISK / PRIMARY ACTION | 现在 / 下一步 / 风险 / 首要动作 | Pulse cards |
| Today timeline | 今日时间线 | Journey lower-left |
| Live map | 实时地图 | Journey lower-right / Map route |
| Copilot dock | 副驾侧栏 | Right column |
| Current mission | 当前任务 | Copilot mission strip |
| Approval / Approve / Reject / Request changes | 审批 / 批准恢复 / 拒绝并保留原计划 / 请求修改 | Timeline + recovery |
| Protected commitment | 受保护承诺 | Timeline/recovery pills |
| Evidence verified | 已验证证据 | Recovery evidence block |
| RECORDED_FIXTURE | 录制快照 | Source badges + fixture banner |
| Gateway / Guardian | 网关 / 守护者 | Timeline steps |
| Truth: CityNexus | 事实源：CityNexus | Truth badge |

Locale resolution: `?locale=zh` / `?locale=zh-CN`, then `localStorage["citynexus.reference.locale"]`,
then `en`. The locale sets `document.documentElement.lang` and the font stack includes
`"PingFang SC", "Microsoft YaHei"`; zh-specific rules add `word-break: break-word` to pulse titles,
timeline step titles, and recovery rows.
