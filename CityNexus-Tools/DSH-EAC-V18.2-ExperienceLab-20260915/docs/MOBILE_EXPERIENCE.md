# Mobile Experience — CityNexus V18.2 Reference

> **Scope**: `reference-app` mobile behavior at **390 × 844** (`mobile-chromium`) and
> **430 × 932** (`mobile-large-chromium`), both `deviceScaleFactor: 2`, `hasTouch: true`,
> `isMobile: true`.
> **Grounding**: `src/App.tsx`, `src/components/*.tsx`, `src/styles/app.css`, `src/i18n.tsx`,
> `tests/acceptance.spec.ts`, `reference-app/playwright.config.ts`,
> `evidence/playwright_results.txt`, `evidence/screenshots/`.
> **Honesty rule**: every recorded run is labelled `RECORDED_FIXTURE`; the UI never labels a
> fixture `LIVE`.

---

## 1. 390 × 844 vs 430 × 932 behavior

The reference has **one mobile breakpoint** (`max-width: 1023px`) and one phone-density breakpoint
(`max-width: 640px`). Both mobile projects fall under both, so they share the same layout mode:

| Concern | 390 × 844 | 430 × 932 | Mechanism |
| --- | --- | --- | --- |
| App mode | mobile | mobile | `matchMedia("(max-width: 1023px)")` → `isMobile=true` |
| Grid | single column | single column | `.layout { grid-template-columns: minmax(0,1fr) }` |
| Desktop nav | hidden | hidden | `.desktop-nav { display: none }` |
| Bottom nav | shown, 5 items | shown, 5 items | `.bottom-nav { display: grid; grid-template-columns: repeat(5, …) }` |
| Pulse/recovery/metrics | single column | single column | `≤640px` collapse of `pulse__grid`, `recovery__grid`, `recovery__metrics` |
| Copilot | collapsed mini composer | collapsed mini composer | `copilotOpen` initial = `matchMedia("(min-width:1024px)")` → false |
| Map sheet | fixed 24/55/90 | fixed 24/55/90 | `--sheet-height` + `transition: height base 220ms` |

The practical difference is **comfort, not structure**: 430×932 has ~40px more horizontal room and
~88px more vertical room, so long lines wrap less and slightly more of the NEXT / PRIMARY ACTION
cards is visible before scrolling. There is **no 430-specific rule**, and `visual.spec.ts` captures
screenshots only on 390×844 — the 430 viewport is exercised by the acceptance suite, not by the
screenshot set (see §10).

---

## 2. Bottom navigation

`MobileNav` (`src/components/TravelerNav.tsx`, `data-testid="bottom-nav"`) is a fixed, 5-column
grid pinned to the bottom of the viewport.

| Order | Route | Label (EN / 中文) | Icon |
| --- | --- | --- | --- |
| 1 | `journey` | Today / 今天 | ◎ |
| 2 | `map` | Map / 地图 | ⌖ |
| 3 | `copilot` | Copilot / 副驾 | ✧ |
| 4 | `wallet` | Wallet / 钱包 | ▭ |
| 5 | `me` | Me / 我的 | ☺ |

- Each item is a semantic `<button>` with `data-testid="bottom-nav-item"`, `aria-current="page"`
  when active, and a `min-height: 44px` hit area.
- The nav reserves `--nav-height: 64px` plus `env(safe-area-inset-bottom)`.
- The page reserves space for it: `.layout { padding-bottom: calc(var(--nav-height) + 84px) }`,
  preventing content from being hidden behind the nav and composer.
- Tapping Copilot navigates to `#/copilot` and forces the Copilot panel open.
- Acceptance test 8 asserts exactly **5** bottom-nav items and that every item is **≥ 44px** tall.

---

## 3. First-viewport priority

On `/#/journey` the mobile DOM order is deliberately traveler-first:

1. **Top bar** — brand, `V18 Experience Reference`, runtime warning pill (if any), locale toggle.
2. **Route heading** — kicker + `<h1 data-testid="route-heading">` (`Your next city, already
   considered.` / `你的下一座城市，已经替你考虑。`) + `Tianjin · V18.2-reference-r1`.
3. **Runtime status banner** — only when `?runtime=` is not `ready`.
4. **Lede** — one calm sentence.
5. **Journey Pulse** — NOW → NEXT → RISK → PRIMARY ACTION, stacked single-column.
6. **Today timeline**, then **Live map preview**.

Because the whole stack is single-column and the pulse is not collapsed, the **NOW card and the
start of NEXT are visible in the first 844–932px viewport**, with RISK and PRIMARY ACTION one short
scroll away. The map and timeline never push the pulse down. Acceptance test 2 verifies
`pulse.y < min(timeline.y, map.y)` on all three viewports.

**Internal vocabulary never appears above the fold**: test 1 (desktop, same component) asserts the
pulse text excludes `PlanVersion` and `CP-SAT`, and the pulse technical `<details>` is collapsed.

---

## 4. Mini composer — idle and active states

When the Copilot dock is collapsed on mobile, it becomes a **persistent mini composer**
(`.copilot-mini`, `data-testid="copilot-mini-composer"`, `data-mini-state`) pinned
`left: 12px; right: 12px; bottom: calc(var(--nav-height) + 8px + safe-area)` with a high z-index so
it sits above sheets.

| State | `data-mini-state` | Placeholder text (EN / 中文) | Trigger |
| --- | --- | --- | --- |
| **Idle** | `idle` | `Ask CityNexus…` / `问问 CityNexus…` | No active fixture |
| **Active** | `active` | `Hermes · Searching alternatives…` / `Hermes · 正在搜索替代方案…` | An active recorded fixture is attached |

`const miniPlaceholder = activeFixture ? t("copilot.miniActive") : t("copilot.miniIdle")` —
so the composer's placeholder and `aria-label` flip to the active copy as soon as a run is attached.
The mini form contains a 44px input and a primary **Send** button; submitting routes the text
(Hermes vs. What-If), attaches the appropriate runtime/fixture, and then opens the Copilot panel.
Because the panel replaces the mini form, the **active** placeholder is visible when the panel is
collapsed again while a fixture is still attached.

Acceptance test 7 verifies: mini composer visible → `data-mini-state="idle"` →
placeholder matches `/Ask CityNexus/` → fill "Find a rain-safe alternative" → send → dock gains
`is-open` → mission strip shows "Rain-safe".

---

## 5. Copilot bottom sheet

When open on mobile, `CopilotDock` renders `.copilot-panel` as a **bottom sheet**:
`position: fixed; left/right: 0; bottom: var(--nav-height + safe-area); max-height: 82vh;
border-radius: 20px 20px 0 0; z-index: 36`.

Contents, in priority order:

| Region | Test id | Mobile behavior |
| --- | --- | --- |
| Header + close × | — | 44×44 close button; kicker/title/subtitle |
| Runtime truth | `runtime-truth` | Latest runtime, compact |
| Runtime banner | `runtime-status-banner` | Only when status ≠ `ready` |
| Conversation | `copilot-message` | User/assistant bubbles, intent + runtime chips |
| **Current mission** | `copilot-mission` | Scenario + `Approval needed` chip when `approval.required` is in the fixture |
| **Current step** | `timeline-summary` | Run status label + latest humanized step label |
| **Proposal** | `proposal-summary` | Appears once `proposal.created` is visible |
| **Approval** | `approval-panel` | Approve / Reject / Request changes, distinct styles + `data-approval-state` |
| Recorded scenarios | `fixture-completed/approved/failed/stopped` | Switch the replay |
| Quick actions | `copilot-quick-whatif`, `copilot-quick-hermes`, `copilot-quick-fallback`, `copilot-quick-unavailable` | One-tap intents |
| Composer | `copilot-input`, `copilot-send` | Free-text fallback |

**Technical timeline disclosure (mobile-specific)**

`showFullTimeline` starts **false** on mobile, so the `AgentRunTimeline` is rendered `compact` and
collapsed. The traveler first sees:

- the mission strip, the run-status/current-step summary, proposal and approval state;
- a single **"Expand full technical timeline / 展开完整技术时间线"** button
  (`data-testid="timeline-expand"`).

Only after tapping **Expand** does the full step list appear, with
`data-testid="timeline-collapse"` to hide it again. The `AgentRunTimeline` is only attached when a
fixture exists, so a DIRECT What-If shows **no** `agent-run-timeline` at all.

Acceptance test 7 confirms this exactly: after sending the rain-safe prompt, `timeline-expand` is
visible, `timeline-step` has count **0**; focusing the button and pressing **Enter** reveals
`timeline-collapse`; **Next event** produces one step; collapsing returns to count 0. No horizontal
overflow is allowed.

**Motion / replay on mobile**

- The timeline never auto-advances on a timer; replay uses `requestAnimationFrame` only.
- Under reduced motion, replay jumps to the full recorded set and the map sheet's height transition
  is effectively instant (`0.001ms` cap).

**Dismissal / focus**

- Escape closes the panel and returns focus to the collapsed edge button (shared desktop/mobile
  handler). On touch, the **×** button closes it.
- The panel is `role="dialog"` with an `aria-label`; it is not `aria-modal` and does not trap focus
  (see the report's limitations).

---

## 6. Map bottom sheet — 24 / 55 / 90

`MapBottomSheet` (`src/components/MapBottomSheet.tsx`, `data-testid="map-sheet"`) is fixed above the
bottom nav on `/#/map` and defaults to **55%**.

Interaction:

- `role="slider"` handle (`data-testid="sheet-handle"`) with
  `aria-valuemin=24`, `aria-valuemax=90`, `aria-valuenow={state}`, `tabIndex=0`.
- Pointer drag with a **>40px** threshold moves one step in the order `["24","55","90"]`.
- **ArrowUp / ArrowDown** on the focused handle moves one step.
- Tab buttons (`role="tablist"` / `role="tab"` + `aria-selected`): `sheet-24`, `sheet-55`,
  `sheet-90`.
- Height comes from `--sheet-height` (`24% / 55% / 90%`) with a `base` (220ms) transition.

Content rendered per state (`sheet-content-24` / `sheet-content-55` / `sheet-content-90`):

| State | Tab label | Content |
| --- | --- | --- |
| **24% NOW/ETA/next** | Collapsed 24% / 收起 24% | **Now**: current activity + `08:41` + ETA (`on route · 12 min ahead`). **Next activity**: Haihe River cruise + `09:30` + `37 min buffer`. |
| **55% route/transport/next commitment** | Half 55% / 半屏 55% | **Route**: `Wudadao → Haihe dock → Ancient Culture Street · 6.4 km`. **Transport**: `Walk 22 min · Metro line 3 · Walk 8 min · recorded fixture`. **Next commitment**: Haihe River cruise · C4 protected · 37 min buffer. |
| **90% full activity/evidence/recovery details** | Expanded 90% / 展开 90% | **Full details** heading + the 7-activity list (time, localized title, environment + walking minutes, `C4` tag on protected rows) + **Recovery details** with the recorded rain trigger and a button to open `/#/recovery`. |

Acceptance test 8 clicks each tab and asserts `sheet-content-24` contains "Now",
`sheet-content-55` contains "Route", and `sheet-content-90` contains "Tianjin Museum"; it also
asserts the 5 bottom-nav items are ≥44px and there is no horizontal overflow.

The sheet leaves room for the mini composer: its bottom offset is
`calc(var(--nav-height) + 76px + env(safe-area-inset-bottom))`, which places it above the collapsed
Copilot composer rather than overlapping it.

---

## 7. Touch targets and safe areas

| Element | Guarantee | Source |
| --- | --- | --- |
| All buttons | `min-height: 44px` (global `button`) | `app.css` |
| Bottom-nav items | `min-height: 44px`, 5 equal columns | `.bottom-nav__item` |
| Sheet tabs / handle | tabs `min-height: 44px`; handle 22px tall × 64px wide with 40px drag threshold + keyboard | `.sheet__tab`, `.sheet__handle` |
| Chips / quick actions | `min-height: 44px` | `.chip-btn` |
| Inputs | `min-height: 44px` | `.copilot-mini input`, `.copilot-form textarea` |
| Icon buttons / locale | `44 × 44px` | `.locale-toggle`, `.icon-btn` |
| Map controls | `min-height: 44px` | `.map__controls .btn` |

Safe areas use `env(safe-area-inset-bottom, 0px)`:

- bottom nav: extra bottom padding + height `calc(var(--nav-height) + safe-area)`;
- sheets and Copilot panel: `padding-bottom: calc(14px + safe-area)`;
- collapsed dock: `bottom: calc(var(--nav-height) + 8px + safe-area)`;
- sheet: `bottom: calc(var(--nav-height) + 76px + safe-area)`;
- app: `padding-bottom: safe-area`.

Focus is visible on touch/ keyboard (`:focus-visible` 3px accent outline, 2px offset), and the
sheet handle exposes slider ARIA state (`aria-valuenow` changes with the 24/55/90 state).

---

## 8. Motion on mobile

- Tokens: `instant 90ms`, `fast 160ms`, `base 220ms`, `slow 420ms`, `map 650ms`
  (`tokens.css`, `motion.ts`).
- Sheet height animates with the `base` token; route changes use the View Transition API when
  available and reduced motion is off.
- `prefers-reduced-motion: reduce` sets the tokens to `0ms`, caps all animation/transition
  durations at `0.001ms`, and removes `::view-transition` animation. `html[data-reduced-motion]` is
  kept in sync and checked by acceptance test 10 (`.pulse-card` computed duration < 0.01s, map
  `data-camera-duration="0"`).

---

## 9. Long Chinese / English stress results

| Stress case | Assertion | Result |
| --- | --- | --- |
| Chinese Journey heading | `route-heading` contains `你的下一座城市` | ✅ all 3 viewports (test 9) |
| Chinese pulse title | `pulse-now` contains `五大道` | ✅ all 3 viewports (test 9) |
| Chinese recovery WHY | `recovery-why` contains `强降雨` | ✅ all 3 viewports (test 9) |
| Chinese/mobile no horizontal overflow | `documentElement.scrollWidth - innerWidth <= 1` | ✅ all 3 viewports (tests 2, 7, 8, 9) |
| Long English tool name | `citynexus.search_city_services_for_rain_safe_indoor_activity_candidates` contained within viewport width | ✅ all 3 viewports (test 5) |
| Long body strings | `overflow-wrap: anywhere` + `min-width: 0` grids; `body { overflow-x: hidden }` | by construction |

Chinese-specific handling: `document.documentElement.lang = "zh-CN"`, font stack
`"Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, …`, and
`html[lang="zh-CN"]` rules add `letter-spacing: 0.01em` + `word-break: break-word` to pulse titles,
timeline step titles, and recovery rows. The localized long copy lives in `i18n.tsx` (`zh` dict),
including the mini composer (`问问 CityNexus…` / `Hermes · 正在搜索替代方案…`).

The screenshot set includes `v18.2-mobile-zh-journey.png` (390×844) and
`v18.2-desktop-zh-journey.png` (1440×900) for visual review.

---

## 10. Test evidence

From `evidence/playwright_results.txt` (14 acceptance tests × 3 projects = 42 runs):
**36 passed, 6 skipped (viewport-specific), 0 failed**, 30.0s (the earlier 13-test sign-off
snapshot recorded **33 passed, 6 skipped, 0 failed**, 29.3s).

| Project | Viewport | Result |
| --- | --- | --- |
| `desktop-chromium` | 1440 × 900 | 12 passed / 2 skipped |
| `mobile-chromium` | **390 × 844** | 12 passed / 2 skipped |
| `mobile-large-chromium` | **430 × 932** | 12 passed / 2 skipped |

Mobile-relevant outcomes:

- **Test 2** (all viewports): Pulse → Today timeline → Live map order, no overflow.
- **Test 5** (all viewports): failed/stopped runs readable, long tool name contained.
- **Test 7** (mobile only, 390 + 430): mini composer idle→send→open, mission "Rain-safe",
  compact timeline hidden until `timeline-expand`, no overflow.
- **Test 8** (mobile only, 390 + 430): 24/55/90 sheet content, 5 nav items ≥44px, no overflow.
- **Test 9** (all viewports): Chinese long content, no overflow.
- **Test 10** (all viewports): reduced motion zero-duration.
- **Test 11** (all viewports): `hermes_unavailable`, `deepseek_unavailable`,
  `provider_unavailable`, `offline_stale` each show a banner + action.
- **Test 13** (all viewports): no console/page errors across key routes.
- **Test 14** (all viewports): `?evidence=unresolved` / `?evidence=stale` block approval with a
  clear next action.

Skipped on mobile: **test 1** (desktop shell) and **test 12** (desktop keyboard/Escape focus flow).
Those two behaviors are still implemented on mobile (Escape handler is shared), but they are
asserted only on desktop.

**Screenshot coverage caveat**: `tests/visual.spec.ts` captures the mobile set only on
`mobile-chromium` (390×844) — `v18.2-mobile-journey.png`,
`v18.2-mobile-copilot-current-step.png`, `v18.2-mobile-copilot-expanded.png`,
`v18.2-mobile-recovery.png`, `v18.2-mobile-map-24.png`, `v18.2-mobile-map-55.png`,
`v18.2-mobile-map-90.png`, `v18.2-mobile-zh-journey.png`. There is **no dedicated 430×932
screenshot set**; adding one is a recommended next step.

---

## 11. Bilingual terminology notes / 术语

| EN | 中文 | Mobile surface |
| --- | --- | --- |
| Bottom nav | 底部导航 | 5-item fixed bar |
| Mini composer | 迷你输入框 | Collapsed Copilot input above nav |
| Ask CityNexus… | 问问 CityNexus… | Idle placeholder |
| Hermes · Searching alternatives… | Hermes · 正在搜索替代方案… | Active placeholder |
| Bottom sheet | 底部面板 | Copilot panel + map sheet |
| Current mission / step | 当前任务 / 当前步骤 | Mission strip + timeline summary |
| Proposal / Approval | 方案 / 审批 | Summary + approval panel |
| Expand full technical timeline | 展开完整技术时间线 | Mobile-only disclosure |
| Collapsed 24% / Half 55% / Expanded 90% | 收起 24% / 半屏 55% / 展开 90% | Map sheet tabs |
| Protected (C4) | 受保护（C4） | Protected rows |
| RECORDED_FIXTURE | 录制快照 | Source badges + fixture banner |
| Today / Map / Copilot / Wallet / Me | 今天 / 地图 / 副驾 / 钱包 / 我的 | Bottom nav labels |

Locale resolution on mobile follows the same rules: `?locale=zh` / `?locale=zh-CN`, then
`localStorage["citynexus.reference.locale"]`, then `en`; the toggle switches EN ↔ 中文 and updates
`document.documentElement.lang`.
