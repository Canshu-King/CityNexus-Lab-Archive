# DSH-EAC V18.2 Experience Report

> **Artifact**: Isolated CityNexus V18.2 frontend experience reference build ("Experience Lab")
> **Lab root**: `D:\moodle\CityNexus-Tools\DSH-EAC-V18.2-ExperienceLab-20260915`
> **Reference app**: `D:\moodle\CityNexus-Tools\DSH-EAC-V18.2-ExperienceLab-20260915\reference-app`
> **Main Codex worktree**: `D:\moodle\CityNexus` — **READ-ONLY, never modified**
> **Evidence**: `evidence/build_results.txt`, `evidence/playwright_results.txt`, `evidence/screenshots/`
> **Package**: `citynexus-v18-experience-reference` `18.0.0-reference.1` (build label **V18.2**)
> **Report date**: 2026-09-15

---

## 1. Executive summary

This lab answers one question: *what does the CityNexus V18.2 runtime feel like to a traveler when
the internal architecture is translated into a calm, truthful UI?* The reference app is a
self-contained Vite + React 19 + MapLibre build that renders an isolated, bilingual
(English / 简体中文) journey experience over **recorded fixtures only**. It is not wired to the
CityNexus backend, does not import main-worktree application code, and does not mutate any
PlanVersion, Gateway policy, or domain fact.

The build compiles (`tsc --noEmit` **PASS**, `vite build` **PASS**) and the final Playwright run is
green: **36 passed, 6 skipped (viewport-specific), 0 failed** on the current 14-test evidence
run (the original 13-test sign-off snapshot recorded **33 passed, 6 skipped, 0 failed**), across three viewports
(desktop 1440×900, mobile 390×844, mobile-large 430×932).

The design contract is consistent from data to pixels:

- **Human → DeepSeek Semantic Compiler → DIRECT / Hermes Native → CityNexus MCP → Gateway / Guardian → Domain truth**
  is expressed as intent chips, a runtime-truth badge, a server-truth agent timeline, explicit
  Gateway/Guardian steps, and an evidence-backed recovery diff with traveler approval.
- **Data honesty is enforced visually**: every recorded replay is labelled `RECORDED_FIXTURE`; nothing
  is labelled `LIVE`; replay advances only from the recorded event array via
  `requestAnimationFrame`, never from a `setTimeout` / `setInterval` progress timer.
- **Primary content leads, internals follow**: the Journey page opens on Journey Pulse
  (NOW / NEXT / RISK / PRIMARY ACTION), then Today timeline and Live map, with technical detail
  collapsed by default.

---

## 2. Scope, isolation, and backend-untouched statement

**The backend is untouched. `D:\moodle\CityNexus` was never modified by this work.**

| Item | Statement |
| --- | --- |
| Main Codex worktree | `D:\moodle\CityNexus` is treated as read-only. No file under it was created, edited, or deleted by this lab. |
| Reference app isolation | All V18.2 source lives under `...\DSH-EAC-V18.2-ExperienceLab-20260915\reference-app`. It is a standalone app, not a route or subtree of the main worktree. |
| Backend / domain | No API call, WebSocket, provider request, PlanVersion write, Gateway decision, Guardian decision, or domain mutation is performed. All data is `RECORDED_FIXTURE`. |
| Map data | The map uses an inline recorded GeoJSON route/stop set (`recorded-fixture://route-rain-001`). No network tile source is configured; `attributionControl` is off, and a static SVG route is shown if MapLibre/WebGL is unavailable. |
| Dependency resolution | `reference-app/node_modules` is a **symlink** to `D:\moodle\CityNexus\frontend\node_modules`, used read-only so the isolated app can build without a second install. This does not write into the main worktree. For a clean, reproducible merge, install dependencies separately (see §7). |
| Merge artifact | `patches/V18_2_EXPERIENCE_REFERENCE.patch` is a **reference merge patch** that proposes a new low-conflict subtree (`frontend/src/features/experience-lab/**`). It is not applied to the main worktree by this lab. |

**Isolation banner in the product**: the top bar renders `V18 Experience Reference` and
`Isolated reference · Codex worktree untouched` (`app.reference` / `app.isolated`), and the footer
reads `Isolated CityNexus V18 Experience Lab build · no main-tree mutation` (`shell.footer`).

---

## 3. Architecture-to-experience mapping

The chain documented in `reference-app/src/types.ts` is rendered as traveler-facing UI, not as
internal vocabulary. The primary view never leads with internal architecture terms.

```
Human
  └─ DeepSeek Semantic Compiler        (intent: EXPLAIN_PLAN / WHAT_IF / REQUEST_REPLAN)
       └─ DIRECT  or  Hermes Native     (execution identity; What-If is DIRECT, no agent run)
            └─ CityNexus MCP            (tool loop: inspect_journey / inspect_twin /
                                         search_city_services / request_replan)
                 └─ Gateway / Guardian  (policy + commitment feasibility checks)
                      └─ Domain truth   (proposal → approval → child PlanVersion authoritative;
                                         runtime status banner; recovery evidence)
```

| Architecture layer | Traveler-facing surface | What the traveler sees | Grounding |
| --- | --- | --- | --- |
| **Human** | Copilot composer, mini composer, quick-action chips, locale toggle | A plain-language ask in EN or 中文; no technical syntax required | `CopilotDock.tsx`, `i18n.tsx` |
| **DeepSeek Semantic Compiler** | Intent chip on the assistant bubble; first timeline step | `WHAT_IF` / `REQUEST_REPLAN` / `EXPLAIN_PLAN` chip; timeline step **"Understood request"** (`semantic.interpreted`) | `CopilotDock.tsx`, `AgentRunTimeline.tsx`, `hermesFixture.ts` |
| **DIRECT / Hermes Native** | `RuntimeTruthBadge` execution value + Copilot status dot | `DIRECT` (semantic only, **no agent run**) or `Hermes / CityNexus Truth` (`HERMES_NATIVE_MCP`); also `FALLBACK`, `UNAVAILABLE` | `RuntimeTruthBadge.tsx`, `CopilotDock.tsx`, `types.ts` |
| **CityNexus MCP** | Agent run timeline tool steps | Humanized labels ("Checking Journey", "Searching alternatives", "Requesting replan") plus the raw `tool_name` in a code chip and recorded `duration_ms` | `AgentRunTimeline.tsx`, `hermesFixture.ts` |
| **Gateway / Guardian** | Dedicated timeline steps | **"Gateway checked"** (`gateway.checked`) and **"Guardian checked"** (`guardian.checked`) | `hermesFixture.ts`, `AgentRunTimeline.tsx` |
| **Domain truth** | Runtime-truth badge **Truth: CityNexus**; proposal summary; approval panel; recovery diff; runtime status banner | Proposal → approval → authoritative-child-PlanVersion copy; before/after plan with deltas and evidence; deterministic facts stay available when a provider is down | `RuntimeTruthBadge.tsx`, `RecoveryDiff.tsx`, `App.tsx`, `journey.ts` |

**Attribution is explicit**: DeepSeek owns *meaning* (`Semantic: DeepSeek`); CityNexus owns the
*facts* (`Truth: CityNexus`). The badge never claims DeepSeek is the source of truth.

---

## 4. What was built

### 4.1 Runtime identities and statuses

Supported runtime identities (`RuntimeIdentity` in `types.ts`):

| Identity | Reference UI |
| --- | --- |
| `DIRECT` | What-If / preview path; copilot execution chip `DIRECT`; technical evidence `Execution: DIRECT` |
| `HERMES_NATIVE_MCP` | Recorded Hermes run; execution label `Hermes / CityNexus Truth` |
| `HERMES_COMPAT_ENDPOINT` | **Typed contract only** — not demonstrated in the reference UI |
| `NATIVE_DEEPSEEK_TOOL_LOOP` | **Typed contract only** — not demonstrated in the reference UI |
| `FALLBACK` | Copilot quick action "FALLBACK"; degrades to deterministic CityNexus facts |
| `UNAVAILABLE` | Copilot quick action "UNAVAILABLE"; "Hermes is unavailable… did not invent a run" |

Supported runtime statuses (`RuntimeStatus`), all reachable via `/?runtime=<status>` and the
`Me` page demo buttons: `ready`, `hermes_unavailable`, `deepseek_unavailable`,
`provider_unavailable`, `offline_stale`. Non-`ready` statuses render a top-bar warning pill, a
`RuntimeStatusBanner` with a useful next action, and (where applicable) a runtime status chip on the
truth badge. A fifth demo state (`ready` → shown as `LIVE`) is the default.

### 4.2 Agent event vocabulary

All 13 event types in `AgentEventType` are present across the four recorded fixtures
(`HERMES_FIXTURES`: `completed`, `approved`, `failed`, `stopped`):

`semantic.interpreted`, `mission.planned`, `run.started`, `tool.started`, `tool.completed`,
`tool.failed`, `gateway.checked`, `guardian.checked`, `proposal.created`, `approval.required`,
`run.completed`, `run.failed`, `run.stopped`.

Each event carries `source: "RECORDED_FIXTURE"`, `sequence_no`, `timestamp`, `summary`, optional
`tool_name` / `duration_ms`, and `run_status`. The timeline derives status per step:
`tool.started → active`, `tool.failed` / `run.failed → failed`, `approval.required → approval`,
`run.stopped → stopped`, everything else `done`.

### 4.3 Approval states

`ApprovalState` = `proposal_only`, `approval_required`, `approved`, `rejected`, `review_requested`.
The timeline approval panel and the recovery approval panel both expose
`data-approval-state` for testing and render localized copy for each state
(e.g. `Approved · child PlanVersion is authoritative`). Approval is presented as a traveler
decision, with CityNexus as the authority that protects confirmed commitments. When recovery
evidence is `unresolved` or `stale` (reachable via `?evidence=…`), the panel starts at
`proposal_only` and the approve action is disabled.

### 4.4 Motion

Motion tokens are defined once in `src/motion.ts` and `src/styles/tokens.css`:

| Token | CSS variable | Duration |
| --- | --- | --- |
| `instant` | `--cn-motion-instant` | 90 ms |
| `fast` | `--cn-motion-fast` | 160 ms |
| `base` | `--cn-motion-base` | 220 ms |
| `slow` | `--cn-motion-slow` | 420 ms |
| `map` | `--cn-motion-map` | 650 ms |

- **View Transition API** is a progressive enhancement: `withViewTransition()` applies the route
  change synchronously when the API is missing or reduced motion is requested.
- **`prefers-reduced-motion: reduce`** collapses tokens to `0ms` and caps animation/transition
  durations at `0.001ms`; `html[data-reduced-motion="true"]` is kept in sync by
  `syncReducedMotionAttribute()` for CSS and tests.
- **MapLibre contract**: `mapCameraOptions()` (→ `flyTo`) and `fitBoundsOptions()` (→ `fitBounds`)
  both consume the `map` duration token; the rendered map exposes
  `data-camera-contract="flyTo/fitBounds"` and `data-camera-duration`.

### 4.5 Accessibility and data honesty

- Semantic `<button>` elements throughout (nav, chips, approval, timeline controls, sheet tabs).
- Global `:focus-visible` outline (3px `--accent-strong`, 2px offset).
- **Escape** closes the Copilot dock and focus returns to the collapsed edge button
  (`restoreFocusRef` → `edgeRef.current.focus()`).
- Minimum 44px touch targets on buttons, nav items, sheet tabs, chips, and inputs.
- Safe-area padding via `env(safe-area-inset-bottom)` on the bottom nav, sheets, and dock.
- ARIA: `role="dialog"` on the Copilot panel, `role="slider"` + `aria-valuemin/max/now` on the
  map sheet handle, `role="tablist"`/`role="tab"` + `aria-selected` on sheet tabs,
  `aria-current="page"` on active nav, `aria-expanded` on the SYSTEM group toggle,
  `aria-live="polite"` on the timeline and Copilot history.
- **Data honesty**: `sourceLabel()` returns `LIVE` only for the (unwired) live path; all recorded
  fixtures render `RECORDED_FIXTURE`, with a dashed fixture banner stating
  "Replaying recorded events only · progress never advances on a timer."

---

## 5. What was verified

### 5.1 Build and typecheck — `evidence/build_results.txt`

| Check | Result |
| --- | --- |
| Node | `v24.14.0` |
| npm | `11.9.0` |
| `tsc --noEmit` | **PASS** (uses local minimal React shims in `src/shims.d.ts` because `@types/react` is not installed) |
| Bundler | `vite v7.3.6 building client environment for production` |
| Modules transformed | **48** |
| `dist/index.html` | 0.52 kB (gzip 0.33 kB) |
| `dist/assets/index-BKSB7NqH.css` | 91.17 kB (gzip 14.61 kB) |
| `dist/assets/index-CskFWU4_.js` | 1,324.79 kB (gzip 368.69 kB) |
| Build time | 1.99 s |
| Warning | Chunk > 500 kB after minification (code-splitting recommended) |

> `evidence/build_results.txt` was regenerated during handoff after acceptance test 14 was
> added, so the table reports the current build (`index-CskFWU4_.js`, 1.99 s). The earlier
> 13-test sign-off build produced `index-C00xwsjl.js` (1,324.39 kB, gzip 368.56 kB, 2.00 s).

### 5.2 Playwright acceptance — `evidence/playwright_results.txt`

| Metric | Result |
| --- | --- |
| Command | `playwright test` (`@playwright/test` ^1.54.0) |
| Total tests | **42** (14 acceptance tests × 3 projects), 1 worker; the earlier 13-test sign-off run had **39** |
| **Final outcome** | **36 passed, 6 skipped (viewport-specific), 0 failed** (current 14-test evidence); the 13-test sign-off snapshot recorded **33 passed, 6 skipped, 0 failed** |
| Wall time | 30.0 s (13-test snapshot: 29.3 s) |
| `retries` / `workers` / `timeout` | 0 / 1 / 45 s (expect 8 s) |
| Reporter | list |
| Server | `node scripts/serve-dist.mjs` on `http://127.0.0.1:4179` (health at `/__health`) |
| Data honesty assertions | `data-source="RECORDED_FIXTURE"`, fixture banner text, "no timer" hold at 0 steps for 1.5 s |

**Projects (viewports)**, from `reference-app/playwright.config.ts`:

| Project | Viewport | Device flags |
| --- | --- | --- |
| `desktop-chromium` | 1440 × 900 | Desktop Chrome |
| `mobile-chromium` | 390 × 844 | deviceScaleFactor 2, `hasTouch`, `isMobile` |
| `mobile-large-chromium` | 430 × 932 | deviceScaleFactor 2, `hasTouch`, `isMobile` |

### 5.3 Acceptance test matrix (14 tests)

| # | Test | desktop 1440×900 | mobile 390×844 | mobile-large 430×932 |
| --- | --- | --- | --- | --- |
| 1 | desktop shell keeps SYSTEM secondary and Journey Pulse primary | ✅ | ⏭ skip | ⏭ skip |
| 2 | journey page orders Pulse → Today timeline → Live map, detail collapsed | ✅ | ✅ | ✅ |
| 3 | DIRECT What-If creates no Agent run | ✅ | ✅ | ✅ |
| 4 | recorded Hermes run truthful, approval-gated, never advances on a timer | ✅ | ✅ | ✅ |
| 5 | failed and stopped runs readable; long tool names contained | ✅ | ✅ | ✅ |
| 6 | recovery diff explains why, protects commitments, approval distinct | ✅ | ✅ | ✅ |
| 7 | mobile mini composer + bottom sheet surface mission/step/approval | ⏭ skip | ✅ | ✅ |
| 8 | mobile map sheet content changes by 24/55/90 state | ⏭ skip | ✅ | ✅ |
| 9 | Chinese long content readable, no horizontal overflow | ✅ | ✅ | ✅ |
| 10 | reduced motion keeps clarity with zero-duration motion | ✅ | ✅ | ✅ |
| 11 | failure and offline states show a useful next action | ✅ | ✅ | ✅ |
| 12 | Copilot keyboard openable and Escape returns focus | ✅ | ⏭ skip | ⏭ skip |
| 13 | key routes produce no console or page errors | ✅ | ✅ | ✅ |
| 14 | unresolved and stale evidence block approval with a clear next action | ✅ | ✅ | ✅ |
| | **Per-project (14-test suite)** | **12 pass / 2 skip** | **12 pass / 2 skip** | **12 pass / 2 skip** |

The 6 skips are deliberate: tests 7 and 8 are mobile-only (skipped once on desktop), tests 1 and 12
are desktop-only (skipped twice each on the two mobile projects).

### 5.4 Notable verified behaviors

- **No timer-driven progress**: after opening a recorded Hermes run, the step count stays at 0 for
  1.5 s; steps only advance via **Next event** or the rAF replay. `AgentRunTimeline.tsx` contains
  the only `requestAnimationFrame` progress loop; there is no `setInterval` and no progress
  `setTimeout`. (The sole `setTimeout` in `src/` is a 0 ms focus nudge in `CopilotDock.tsx`, not
  progress.)
- **Long tool names stay contained**: the deliberately long
  `citynexus.search_city_services_for_rain_safe_indoor_activity_candidates` name renders inside its
  viewport width (ellipsis + `min-width: 0` grid).
- **Reduced motion**: `.pulse-card` computed `animation-duration < 0.01s`, and the map reports
  `data-camera-duration="0"`.
- **No console/page errors** across `journey, live, map, copilot, wallet, recovery, intelligence,
  twin, me`.
- **No horizontal overflow** (`scrollWidth - innerWidth <= 1`) on journey, Copilot, map, and
  recovery, including `?locale=zh`.
- **Runtime failure/offline** (`hermes_unavailable`, `deepseek_unavailable`,
  `provider_unavailable`, `offline_stale`) each show a visible banner with an action button while
  Journey Pulse stays visible.
- **Evidence gates approval**: `?evidence=unresolved` / `?evidence=stale` set
  `data-evidence-state` on the recovery root and `.recovery__evidence`, disable the approve
  button, and start the panel at `Proposal only · no decision yet` (test 14).

---

## 6. Screenshot index

All screenshots live in `evidence/screenshots/`. The **V18.2 evidence set** (15 files, written
2026-09-15 01:50–01:51) is produced by `reference-app/tests/visual.spec.ts`. It is the only
screenshot set shipped with this delivery.

### 6.1 Final V18.2 set — desktop (`desktop-chromium`, 1440×900)

| File | Route / action | What it evidences |
| --- | --- | --- |
| `v18.2-desktop-journey.png` | `/#/journey` | Journey Pulse primary, TODAY shell |
| `v18.2-desktop-copilot-approval.png` | `/#/copilot` → quick Hermes → 14× Next | Agent timeline at approval state, distinct approve/reject |
| `v18.2-desktop-recovery.png` | `/#/recovery` | Recovery before/after diff, protected commitments, deltas |
| `v18.2-desktop-map.png` | `/#/map` | MapLibre canvas + recorded route |
| `v18.2-desktop-zh-journey.png` | `/?locale=zh#/journey` | Chinese long-content layout (`你的下一座城市…`) |
| `v18.2-desktop-hermes-unavailable.png` | `/?runtime=hermes_unavailable#/journey` | Runtime status banner + next action |
| `v18.2-desktop-reduced-motion.png` | reduced motion emulate | `data-reduced-motion="true"` clarity |

### 6.2 Final V18.2 set — mobile (`mobile-chromium`, 390×844)

| File | Route / action | What it evidences |
| --- | --- | --- |
| `v18.2-mobile-journey.png` | `/#/journey` | First-viewport priority + bottom nav |
| `v18.2-mobile-copilot-current-step.png` | `/#/copilot` → quick Hermes | Compact timeline, "Expand full technical timeline" |
| `v18.2-mobile-copilot-expanded.png` | …then expand + 2× Next | Step detail after explicit expansion |
| `v18.2-mobile-recovery.png` | `/#/recovery` | Recovery diff stacked for mobile |
| `v18.2-mobile-map-24.png` | `/#/map` → 24% | NOW / ETA / next activity |
| `v18.2-mobile-map-55.png` | `/#/map` → 55% | Route / transport / next commitment |
| `v18.2-mobile-map-90.png` | `/#/map` → 90% | Full activity / evidence / recovery details |
| `v18.2-mobile-zh-journey.png` | `/?locale=zh#/journey` | Chinese long-content mobile layout |

### 6.3 Screenshot coverage note

The delivery contains the 15 V18.2 screenshots listed above. `visual.spec.ts` captures
`desktop-chromium` and `mobile-chromium`; the acceptance suite additionally *runs* on
`mobile-large-chromium` (430×932) so the layout is verified there, but no separate 430×932
screenshot set is shipped. See §7.

---

## 7. Limitations and next steps

1. **UI-only reference.** No backend request or mutation is performed; there is no PlanVersion,
   Gateway, Guardian, or domain write path. Every run is a recorded fixture.
2. **LIVE path is unwired.** `AgentRunTimeline` accepts `liveEventsUrl` / `liveEvents` and
   `sourceLabel()` can return `LIVE`, but App/Copilot never pass live events, so the `LIVE`
   rendering path is unexercised by tests. Merge must supply the real SSE/stream source and add
   live-run tests.
3. **Two typed identities are not demoed.** `HERMES_COMPAT_ENDPOINT` and
   `NATIVE_DEEPSEEK_TOOL_LOOP` exist in `RuntimeIdentity` but have no reference surface.
4. **Typecheck uses local shims.** `@types/react` is not installed; `src/shims.d.ts` provides
   minimal ambient types so `tsc --noEmit` passes. The merge should use the host app's real React
   types and remove the shims.
5. **Bundle size.** The production JS is 1,324.79 kB (368.69 kB gzip) and Vite warns about the
   >500 kB chunk. MapLibre dominates; add route-level code splitting / manual chunks before merge.
6. **Dependency resolution is a symlink.** `reference-app/node_modules` points at the main
   worktree's `frontend/node_modules` (read-only reuse). For CI reproducibility, install this
   subtree's dependencies independently and pin them.
7. **Screenshot coverage.** No `mobile-large-chromium` (430×932) screenshots; add a 430×932 visual
   set for parity with the acceptance matrix.
8. **Recovery model vs. render — resolved.** `travel_delta_min` is now rendered as the fourth
   recovery metric (`recovery-travel-delta`, `+6 min`). The protected list uses
   `recovery-protected-list`; `testIds.recoveryProtected` remains reserved for a future singular
   badge.
9. **Intent routing is heuristic.** Copilot routes free text with a regex
   (`/replan|替代|rain|雨|alternative|change/i`); this is a reference stand-in for the real DeepSeek
   Semantic Compiler.
10. **No persistence.** Runtime status is driven by the `?runtime=` query param and Me-page demo
    buttons; nothing is stored server-side, and a reload resets state.
11. **Chinese stress coverage is partial.** Test 9 covers Journey and Recovery in `zh-CN`; Copilot,
    map, and timeline long-Chinese cases are not separately asserted.
12. **Dialog hardening.** The Copilot panel is `role="dialog"` with Escape-close and focus return,
    but it is not `aria-modal` and does not trap Tab focus. Recommend hardening during merge.
13. **Map camera contract** is asserted through data attributes and code paths; there is no
    visual/coordinate assertion of `flyTo` / `fitBounds` behavior.

---

## 8. Bilingual terminology notes / 术语对照

| English | 简体中文 | Notes |
| --- | --- | --- |
| Journey Pulse | 行程脉搏 | NOW / NEXT / RISK / PRIMARY ACTION |
| NOW / NEXT / RISK / PRIMARY ACTION | 现在 / 下一步 / 风险 / 首要动作 | First viewport on Journey |
| Today timeline | 今日时间线 | Ordered day activities |
| Live map | 实时地图 | MapLibre + recorded route |
| Copilot dock | 副驾侧栏 | Persistent composer + mission sheet |
| Bottom sheet | 底部面板 | 24% / 55% / 90% states |
| Recovery | 恢复 | Before/after proposal |
| Protected commitment (C4) | 受保护承诺（C4） | Must stay feasible |
| Approval | 审批 | approve / reject / request changes |
| RECORDED_FIXTURE | 录制快照 / 录制回放 | Never labelled LIVE |
| Runtime identity | 运行时身份 | DIRECT / Hermes Native / … |
| Runtime status | 运行时状态 | ready / unavailable / offline_stale |
| Gateway / Guardian | 网关 / 守护者 | Policy + commitment feasibility |
| Semantic Compiler | 语义编译器 | DeepSeek owns meaning |
| PlanVersion | 计划版本 | CityNexus owns the fact |
| Time / Cost / Walking delta | 时间 / 费用 / 步行变化 | Recovery metrics |
| Evidence verified / unresolved / stale | 已验证 / 未解决 / 已过期 | Gates approval |

---

## 9. Explicit statement: backend untouched

**No backend, main-worktree source, PlanVersion, Gateway policy, Guardian decision, provider
integration, or domain fact was modified, written, or called by this reference build.**

- Working artifacts are confined to
  `D:\moodle\CityNexus-Tools\DSH-EAC-V18.2-ExperienceLab-20260915`.
- `D:\moodle\CityNexus` remains read-only; its only involvements are (a) the read-only
  `node_modules` symlink and (b) the reference merge patch stored in the lab, which is **not
  applied**.
- All runtime behavior shown in the UI is a replay of `RECORDED_FIXTURE` data and is labelled as
  such.

*Prepared for DSH-EAC V18.2 experience review and CityNexus merge planning.*
