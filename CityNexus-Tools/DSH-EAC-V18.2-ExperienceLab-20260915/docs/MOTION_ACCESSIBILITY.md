# Motion & Accessibility — CityNexus V18.2 Experience Lab

Reference build: `reference-app/` (isolated; the main worktree `D:\moodle\CityNexus` is never modified).
This document describes the motion system and the accessibility contract of the V18.2 reference UI, with the evidence that verifies it.

> 中文摘要：本文记录 V18.2 参考实现的动效令牌（90/160/220/420/650ms）、缓动曲线、View Transition 渐进增强、MapLibre 相机契约、`prefers-reduced-motion` 降级、键盘与 ARIA 可访问性、触控目标与安全区，以及 Playwright 测试证据。

Primary source files:

| File | Role |
| --- | --- |
| `reference-app/src/motion.ts` | Token map, reduced-motion helpers, View Transition wrapper, MapLibre camera option builders |
| `reference-app/src/styles/tokens.css` | CSS custom properties, reduced-motion collapse, View Transition pseudo-element animations |
| `reference-app/src/styles/app.css` | Component transitions/animations, focus-visible, 44px targets, safe-area insets |
| `reference-app/src/App.tsx` | Route navigation + `withViewTransition`, reduced-motion attribute sync |
| `reference-app/src/components/CopilotDock.tsx` | Dock open/close, dialog semantics, focus management, `aria-live` |
| `reference-app/src/components/AgentRunTimeline.tsx` | Timeline step animation, replay, reduced-motion jump-to-end, `aria-live` |
| `reference-app/src/components/MapBottomSheet.tsx` | Bottom-sheet height motion, `role="slider"` handle, keyboard control |
| `reference-app/src/components/MapCanvas.tsx` | MapLibre `flyTo`/`fitBounds` usage and camera duration |
| `reference-app/src/components/TravelerNav.tsx` | `aria-expanded`, `aria-current` |
| `reference-app/tests/acceptance.spec.ts` | 13 Playwright acceptance tests |

---

## 1. Motion tokens

Motion is expressed once as semantic tokens and consumed from both TypeScript and CSS.

| Token | Duration | TypeScript (`MOTION_TOKENS_MS`) | CSS custom property | Typical use |
| --- | --- | --- | --- | --- |
| `instant` | **90 ms** | `TOKEN_MS.instant` | `--cn-motion-instant` | Immediate acknowledgements / reserved |
| `fast` | **160 ms** | `TOKEN_MS.fast` | `--cn-motion-fast` | Button state, timeline step entrance, route-out |
| `base` | **220 ms** | `TOKEN_MS.base` | `--cn-motion-base` | Route-in, pulse cards, bottom-sheet height |
| `slow` | **420 ms** | `TOKEN_MS.slow` | `--cn-motion-slow` | Longer emphasis / reserved |
| `map` | **650 ms** | `TOKEN_MS.map` | `--cn-motion-map` | MapLibre camera (`flyTo` / `fitBounds`) |

### Easing tokens

| Token | Value | Used by |
| --- | --- | --- |
| `--cn-ease-standard` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | UI state transitions (`.btn`, bottom-sheet height) |
| `--cn-ease-enter` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrance animations (route-in, `card-in`, `step-in`) |

### TypeScript motion API (`src/motion.ts`)

- `MOTION_TOKENS_MS` — the single numeric source of the table above.
- `motionDuration(token)` — returns the token in ms, or `0` when reduced motion is on.
- `prefersReducedMotion()` — reads `window.matchMedia("(prefers-reduced-motion: reduce)")`, SSR-safe.
- `syncReducedMotionAttribute()` — keeps `<html data-reduced-motion="true|false">` in sync and returns a cleanup that removes the `change` listener.
- `withViewTransition(update)` — progressive-enhancement wrapper for route changes (see §3).
- `mapCameraOptions(command)` / `fitBoundsOptions(command)` — MapLibre option builders (see §4).

### CSS transition / animation usage

| Selector | Declaration | Token |
| --- | --- | --- |
| `.btn` | `transition: transform … , border-color …` | `--cn-motion-fast` + `--cn-ease-standard` |
| `.sheet` (`max-width: 1023px`) | `transition: height …` | `--cn-motion-base` + `--cn-ease-standard` |
| `.pulse-card` | `animation: card-in … both` | `--cn-motion-base` + `--cn-ease-enter` |
| `.timeline-step` | `animation: step-in … both` | `--cn-motion-fast` + `--cn-ease-enter` |
| `::view-transition-old(root)` | `animation: cn-route-out … both` | `--cn-motion-fast` |
| `::view-transition-new(root)` | `animation: cn-route-in … both` | `--cn-motion-base` + `--cn-ease-enter` |

Keyframes live in `tokens.css` (`cn-route-out`, `cn-route-in`) and `app.css` (`card-in`, `step-in`).

> 中文：动效只有一套令牌，TS 与 CSS 共用；`slow` 为未来预留，当前主要由 `fast/base/map` 承担交互反馈。

---

## 2. `prefers-reduced-motion` behaviour

Reduced motion is enforced at three layers so that meaning is never lost — only time is removed.

### 2.1 CSS collapse (`tokens.css`)

```css
@media (prefers-reduced-motion: reduce) {
  :root {
    --cn-motion-instant: 0ms;
    --cn-motion-fast: 0ms;
    --cn-motion-base: 0ms;
    --cn-motion-slow: 0ms;
    --cn-motion-map: 0ms;
  }
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
  ::view-transition-old(root),
  ::view-transition-new(root) { animation: none !important; }
}
```

- Tokens collapse to **0 ms**; any remaining CSS animation/transition is pinned to **0.001 ms** and plays once.
- View Transition pseudo-element animations are disabled outright.
- Smooth scrolling is turned off.

### 2.2 TypeScript collapse (`motion.ts`)

- `motionDuration(token)` returns `0` whenever `prefersReducedMotion()` is true, so MapLibre cameras jump instead of flying.
- `AgentRunTimeline.startReplay()` checks `prefersReducedMotion()` first and sets the visible event count to the full recorded length, so replay is instant.
- `withViewTransition(update)` calls `update()` directly (synchronous) when reduced motion is requested or the API is missing.

### 2.3 State clarity is preserved

Reduced motion changes **duration only**. Content, status, ARIA state and DOM structure are identical:

- Route updates still happen: `window.location.hash`, `setRoute(target)`, and any copilot open/close side effect run inside the same `update()` closure — synchronously, never deferred.
- Timeline steps still appear; they just appear with no entrance animation.
- Map camera state still updates; `data-camera-duration` becomes `"0"` and the camera teleports.
- `<html data-reduced-motion>` is set to `"true"` so CSS and tests can assert the mode.

---

## 3. Route transitions — View Transition API progressive enhancement

`App.navigate()` is the only route entry point and wraps all work in `withViewTransition()`:

```ts
withViewTransition(() => {
  window.location.hash = `#/${target}`;
  setRoute(target);
  if (target === "copilot") setCopilotOpen(true);
  if (window.matchMedia("(max-width: 1023px)").matches && target !== "copilot") setCopilotOpen(false);
});
```

`withViewTransition(update)`:

1. If `prefersReducedMotion()` is true → run `update()` synchronously.
2. Else if `document.startViewTransition` is unavailable → run `update()` synchronously.
3. Else → `document.startViewTransition(update)`.

Cross-fade/rise is provided by `::view-transition-old(root)` (`cn-route-out`, fast) and `::view-transition-new(root)` (`cn-route-in`, base + enter easing). On non-supporting engines and in reduced-motion mode the app degrades to a plain synchronous route swap — the test suite does not depend on the animation.

> 中文：View Transition 只是渐进增强；不支持或用户要求减少动态时，路由仍同步切换。

---

## 4. MapLibre `flyTo` / `fitBounds` contract

`MapCanvas.tsx` imports `maplibregl` and drives the camera through the pure helpers in `motion.ts`:

```ts
// flyTo (center)
map.flyTo(mapCameraOptions(command) as FlyToOptions);
// { center, zoom, duration: command.animate ? motionDuration(command.duration_token) : 0 }

// fitBounds
map.fitBounds(command.bounds, fitBoundsOptions(command));
// { bounds, duration: command.animate ? motionDuration(command.duration_token) : 0, padding: 48 }
```

Contract points:

- The camera command type is `MapCameraCommand` (`center?`, `zoom?`, `bounds?`, `duration_token`, `animate`).
- `duration_token: "map"` is the default camera token (**650 ms**); with reduced motion or `animate: false` the duration is **0**.
- `fitBounds` uses a fixed **48 px** padding so route bounds never hug the viewport edge.
- The canvas root exposes machine-readable contract markers:
  - `data-camera-contract="flyTo/fitBounds"`
  - `data-camera-duration={motionDuration("map")}` → `"650"` normally, `"0"` under reduced motion
  - `data-map-ready`, `data-map-mode="maplibre" | "fallback-static"`
- The reference build uses a **recorded GeoJSON fixture** (`recorded-fixture://route-rain-001`), no network tiles. If WebGL/MapLibre fails it renders a static SVG route fallback (`role="img"`) and marks `data-map-mode="fallback-static"`.
- The status line `map-camera-status` reports `flyTo · 650ms` / `fitBounds · 650ms` (or `0ms`) so the active camera contract is visible.

---

## 5. Where motion is used

| Area | Trigger | Motion applied | Reduced motion |
| --- | --- | --- | --- |
| **Route transitions** | `App.navigate()` (nav buttons, hashchange) | View Transition `cn-route-out` (fast) + `cn-route-in` (base, enter) | Synchronous swap, `animation: none` |
| **Copilot dock open/close** | `CopilotDock` toggles `is-open` / `is-collapsed`; panel mounts/unmounts | No panel-level keyframe is declared, so the swap itself is instant by construction; inner `.btn` / `.chip-btn` use `--cn-motion-fast`; route-driven opens also get the route transition | Instant; focus behaviour unchanged |
| **Agent timeline changes** | New `timeline-step` rows from replay / next / fixture switch | `step-in` entrance on each step (`--cn-motion-fast`, enter easing); replay driven by `requestAnimationFrame`, never a timer that "invents" events | Replay jumps to full recorded length; steps render with zero-duration entrance |
| **Recovery diff** | `#/recovery` render, approval actions | Content arrives with the route transition; `data-approval-state` re-colours the panel; `.btn` state uses fast token | Instant colour/state change |
| **Approval panel** | Timeline reaches `approval.required`; approve / reject / request changes | Approval step uses `step-in`; `data-approval-state` (proposal_only → approval_required → approved / rejected / review_requested) changes border/background | Instant state change; decision semantics preserved |
| **Mobile bottom sheet** | Sheet tabs `24` / `55` / `90`, drag handle, ArrowUp/ArrowDown | `.sheet { transition: height var(--cn-motion-base) var(--cn-ease-standard) }` (`≤1023px` only) | Transition duration pinned to 0.001 ms |
| **Map camera** | "Recenter" (flyTo) and "Fit route" (fitBounds) | MapLibre animated camera with `--cn-motion-map` = 650 ms, 48 px bounds padding | `duration: 0` (teleport); `data-camera-duration="0"` |

> 中文：动效覆盖路由、副驾面板、时间线、恢复对比/审批、移动底部抽屉和地图相机；降级时只去掉时间，不改变状态。

---

## 6. Accessibility

### 6.1 Keyboard navigation (Tab / Enter / Escape)

- All interactive controls are native `<button type="button">` (nav items, quick prompts, approval actions, map controls, sheet tabs, locale toggle) and are reachable with **Tab**.
- **Enter/Space** activates every button natively; the mobile timeline expand/collapse can be focused and confirmed with **Enter** (acceptance test 7 does exactly this).
- **Escape** closes the Copilot dock from anywhere in the page (`CopilotDock` window `keydown` listener) and returns focus.
- The bottom-sheet handle supports **ArrowUp / ArrowDown** to step through `24 → 55 → 90` (`role="slider"`), plus the three tab buttons.

### 6.2 Focus-visible outline

```css
:focus-visible {
  outline: 3px solid var(--accent-strong); /* #7bf0cf */
  outline-offset: 2px;
}
```

A single global rule gives every keyboard-focused control a high-contrast outline. Controls are not `outline: none`.

### 6.3 Dialog focus behaviour (Copilot)

- The open panel is `role="dialog"` with an `aria-label`.
- On open, focus moves into the panel: the close button on desktop, or the textarea (falling back to the close button) on mobile.
- **Escape** closes the dock; the component records `restoreFocusRef` and, on close, returns focus to the collapsed **edge button** (`.copilot-edge`, `ref={edgeRef}`).
- Acceptance test 12 verifies the full loop: dock open → Escape → `is-collapsed` + edge focused → Enter → `is-open` + input visible → Escape → edge focused again.

### 6.4 ARIA and semantics

| Element | Attribute |
| --- | --- |
| Copilot message history | `aria-live="polite"` (`copilot-history`) |
| Agent run timeline section | `aria-live="polite"` (`agent-run-timeline`) |
| Copilot panel | `role="dialog"` + `aria-label` |
| Bottom-sheet handle | `role="slider"`, `aria-valuemin={24}`, `aria-valuemax={90}`, `aria-valuenow`, `tabIndex={0}`, `aria-label="Map sheet height"` |
| Sheet state switcher | `role="tablist"` + `role="tab"` + `aria-selected` |
| SYSTEM nav group toggle | `aria-expanded={systemOpen}` |
| Active nav items (desktop + mobile) | `aria-current="page"` |
| Approval panels / fixture switcher / runtime demo | `role="group"` + `aria-label` |
| Runtime outage banner, local "stopped" notices | `role="status"` |
| Decorative glyphs (brand mark, nav icons, step marks) | `aria-hidden="true"` |
| Static map fallback SVG | `role="img"` + `aria-label` |

### 6.5 Touch targets (44 px)

- Global `button { min-height: 44px; cursor: pointer; }`.
- `.locale-toggle`, `.icon-btn` → `min-height: 44px; min-width: 44px`.
- `.desktop-nav__item`, `.chip-btn`, `.sheet__tab`, `.bottom-nav__item`, `.technical summary`, `.fixture-switcher .chip-btn` → `min-height: 44px`.
- `.copilot-form textarea`, `.copilot-mini input` → `min-height: 44px`.
- Acceptance test 8 measures all five `.bottom-nav-item` heights and asserts `>= 44`.

### 6.6 Mobile safe-area insets

`index.html` sets `viewport-fit=cover`. `app.css` then pads fixed/anchor elements with `env(safe-area-inset-bottom, 0px)`:

- `.app` bottom padding, `.bottom-nav` height + padding,
- `.sheet` and `.copilot-panel` bottom padding and offsets,
- `.copilot.is-collapsed` bottom offset (`nav-height + 8px + inset`),
- a later rule lifts `.sheet` above the mini composer (`nav-height + 76px + inset`).

This keeps the bottom nav, sheet and collapsed composer clear of the home indicator/gesture bar.

### 6.7 Contrast and readable text

- Dark theme tokens in `tokens.css`: background `#071217`, raised `#0d1d25`, text `#eaf6f4`, muted `#93aeb4`, accent `#42d3b0`, strong accent `#7bf0cf`, warn `#f5b942`, danger `#ff6b5f`, info `#7bd8ff`.
- Muted text is deliberately light on dark; warning/danger states pair a coloured border with a coloured surface and non-colour text labels (e.g. "Approval required", "failed", "stopped"), so colour is not the only signal.
- Long content never overflows: `overflow-wrap: anywhere` on pulse cards, bubbles, timeline bodies, recovery rows; `min-width: 0` on grid/flex children; `html[lang="zh-CN"]` adds letter-spacing and `word-break: break-word` for CJK.
- Long tool names are clipped with an ellipsis but retain a `title` attribute and the short human label.

### 6.8 Reduced-motion mode (user-facing)

- `App` calls `syncReducedMotionAttribute()` so `<html data-reduced-motion>` is always correct.
- "Me" route exposes the live value via `data-testid="reduced-motion-state"`.
- No functionality is gated behind motion; reduced motion is a first-class mode (see §2).

---

## 7. Test evidence

All results below come from `evidence/playwright_results.txt` (42 test executions: **36 passed, 6 skipped**, 30.0 s) produced by `reference-app/tests/acceptance.spec.ts` and the three projects in `reference-app/playwright.config.ts`.

### Projects (viewports)

| Project | Viewport | Notes |
| --- | --- | --- |
| `desktop-chromium` | 1440 × 900 | Desktop-only tests 1 and 12 run here |
| `mobile-chromium` | 390 × 844 (DSF 2, touch, `isMobile`) | Mobile-only tests 7 and 8 run here |
| `mobile-large-chromium` | 430 × 932 (DSF 2, touch, `isMobile`) | Mobile-only tests 7 and 8; desktop-only tests skipped |

The 6 skips are the expected cross-project gates (tests 1 & 12 skip on both mobile projects; tests 7 & 8 skip on desktop).

### Acceptance tests (`reference-app/tests/acceptance.spec.ts`)

| # | Test | Accessibility / motion signal |
| --- | --- | --- |
| 1 | desktop shell keeps SYSTEM secondary and Journey Pulse primary | `aria-expanded` collapse of SYSTEM group; `details` closed by default |
| 2 | journey page orders Pulse → Today timeline → Live map, detail collapsed | **no horizontal overflow** (`scrollWidth - innerWidth <= 1`) |
| 3 | DIRECT What-If creates no Agent run | source honesty: DIRECT ≠ Agent run |
| 4 | recorded Hermes run is truthful, approval-gated, never advances on a timer | `data-source="RECORDED_FIXTURE"`, no timer progress |
| 5 | failed and stopped runs stay readable; long tool names contained | long-content containment vs viewport width |
| 6 | recovery diff explains why, protects commitments, approval distinct | approve/reject classes and ARIA-labelled group |
| 7 | mobile mini composer and bottom sheet surface mission, step, approval | **keyboard flow** (`.focus()` + Enter), no horizontal overflow |
| 8 | mobile map sheet content changes by 24/55/90 | **touch targets** (bottom-nav items ≥ 44 px), no horizontal overflow |
| 9 | Chinese long content stays readable without horizontal overflow | CJK readability, no horizontal overflow |
| 10 | reduced motion keeps state clarity with zero-duration motion | **reduced motion**: `data-reduced-motion="true"`, animation < 0.01 s, `data-camera-duration="0"` |
| 11 | failure and offline states show a useful next action | `role="status"` banner + actionable button on 4 runtime states |
| 12 | Copilot is keyboard openable and Escape returns focus | **keyboard flow**: Escape closes, edge button focused, Enter reopens |
| 13 | key routes produce no console or page errors | **no console/page errors** across journey, live, map, copilot, wallet, recovery, intelligence, twin, me |

### Mapping to the requested evidence categories

- **Keyboard flow** → test 12 (Copilot Tab/Enter/Escape + focus return), test 7 (timeline expand via focus + Enter); sheet handle ArrowUp/ArrowDown is implemented but not asserted by a dedicated test.
- **Reduced motion** → test 10.
- **Touch targets** → test 8 (bottom-nav items ≥ 44 px).
- **No horizontal overflow** → tests 2, 7, 8, 9.
- **No console/page errors** → test 13.

### Visual evidence

`reference-app/tests/visual.spec.ts` writes the screenshot set into `evidence/screenshots/` (see §8).

### Build evidence

`evidence/build_results.txt`: `tsc --noEmit` PASS; `vite build` 48 modules, `dist/assets/index-*.js` 1,324.79 kB (gzip 368.69 kB), `dist/assets/index-*.css` 91.17 kB (gzip 14.61 kB). Report also flags the >500 kB chunk warning.

---

## 8. Evidence paths

| Artifact | Path |
| --- | --- |
| Playwright results | `evidence/playwright_results.txt` |
| Build/typecheck results | `evidence/build_results.txt` |
| Desktop screenshots | `evidence/screenshots/v18.2-desktop-{journey,copilot-approval,recovery,map,zh-journey,hermes-unavailable,reduced-motion}.png` |
| Mobile screenshots | `evidence/screenshots/v18.2-mobile-{journey,copilot-current-step,copilot-expanded,recovery,map-24,map-55,map-90,zh-journey}.png` |
| Focused test sources | `reference-app/tests/acceptance.spec.ts`, `reference-app/tests/visual.spec.ts`, mirrored in `tests/` |
| Test runner config | `reference-app/playwright.config.ts` |

---

## 9. Known limitations / next steps

1. **Two token sources.** `MOTION_TOKENS_MS` (TS) and `--cn-motion-*` (CSS) are hand-kept in sync; consider generating the CSS custom properties from one source when the tokens are adopted into the main tree.
2. **Media query is sampled, not subscribed.** `prefersReducedMotion()` is read at call time; only `<html data-reduced-motion>` listens for changes. Flipping the OS setting mid-replay will not cancel an in-flight replay.
3. **Copilot dialog is not a full focus trap.** `role="dialog"` + Escape + focus restore exist, but Tab can move outside the panel and there is no `aria-modal`/inert background. Add an explicit focus trap if it becomes a true modal.
4. **Sheet handle hit area.** The visible grab pill is 22 px tall (below 44 px). Keyboard arrows and the three 44 px sheet tabs compensate, but enlarging the handle hit box is a worthwhile follow-up.
5. **Tab pattern is partial.** Sheet tabs use `role="tab"`/`aria-selected` but not roving tabindex or Left/Right arrow navigation; every tab is independently tabbable.
6. **View Transition support.** Chromium-first; Firefox/Safari take the synchronous fallback (intended, tested structurally). Don't make correctness depend on it.
7. **Bundle weight.** `maplibre-gl` dominates the build (`~1.3 MB` raw / `368 KB` gzip). Lazy-load or code-split the feature before main-tree adoption.
8. **No formal a11y audit.** Current assurance is structural Playwright assertions plus manual token review; no axe/Lighthouse/contrast-ratio sweep has been recorded.
9. **Recorded data only.** Map geometry and agent events are `RECORDED_FIXTURE`; there are no network tiles and no live runtime calls in the reference build.
10. **Residual untranslated copy.** A few fallback strings in `CopilotDock` (e.g. the fallback/unavailable prompts) are English-only even in the Chinese locale.

> 中文：后续重点是单一令牌源、完整焦点陷阱、把手触控尺寸、maplibre 懒加载与自动化无障碍扫描。
