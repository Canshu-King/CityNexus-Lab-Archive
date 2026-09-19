# WEB_MOBILE_RESULTS.md

**Scope:** current Web/Mobile runtime truth — the brief's "current Web/Mobile runtime truth"
focus item.
**Stack under test:** **Snapshot B** (identical to the live main tree on every capability
surface — see `SNAPSHOT_B_RESULTS.md` §6)
**Isolation:** backend uvicorn on **8050**, frontend Vite on **4203**, throwaway DB
`evidence/_db/web_lab_b.db`, `CITYNEXUS_AI_ENABLED=false`, Vite `cacheDir` in `%TEMP%`,
`node_modules` reused from the main tree via a directory junction.
**Probe:** `tools/v191_web_mobile.mjs` (Playwright, system Chrome,
`--no-proxy-server` + `proxy: {server: "direct://"}`)
**Evidence:** `evidence/screenshots/` (64 route screenshots + 8 probe screenshots),
`evidence/web_mobile_results.json`, `web_mobile_summary.json`, `web_mobile_focus.json`,
`web_mobile_zoom200.json`, `web_mobile_capability.json`, `web_mobile_bootstrap.json`

---

## 1. Matrix

**4 viewports × reduced-motion on/off × 8 routes = 64 cells.**

Viewports: `390×844`, `430×932`, `1280×720`, `1440×900`
Routes: `hub`, `live`, `map`, `studio`, `bookings`, `agent`, `authoritative`, `twin`

| Measure | Value |
|---|---|
| Cells planned | 64 |
| Cells loaded | **64 / 64** |
| Screenshots written | **64** (+8 probe screenshots) |
| Distinct screens rendered | 16 |
| `pageErrors` | **0** |
| Cells with horizontal overflow | **0** |
| Cells rendering capability vocabulary | 32 |

**The app boots and renders in every cell, with no page errors and no horizontal overflow at
any viewport or reduced-motion setting.** The frontend under test is confirmed to be the
V19.1 build — the bootstrap sample text contains
`CityNexus JOURNEY INTELLIGENCE WORKSPACE / Trip operations / Journey Hub / Live Journey /
Trip Studio / Travel Wallet / Copilot / Recovery Intelligence / Traveler Twin`.

## 2. Accessibility probes

### 2.1 Keyboard focus — 16 elements tabbed

Every element reached by `Tab` has a visible focus indicator:

| Property | Observed |
|---|---|
| `visibleFocus` | **`true`** for all 16 |
| `outlineStyle` / `outlineWidth` | `solid` / `3px` for all 16 |
| `boxShadow` present | 1 of 16 (`Open Trip Studio`) |

Sample order: `Menu` (aria `Open navigation`) → `中文` (aria `Switch language`) → `TI` →
`中文` (aria `Switch language`) → `Try another city` → `Open Trip Studio` → `View plan →` →
`Compare stays →` …

**No focus-trap and no invisible-focus element found.** Two entries carry an empty `aria`
label (`TI`, `Try another city`, `Open Trip Studio`, `View plan →`, `Compare stays →`) — see
§3.

### 2.2 200 % zoom — 8/8 routes pass

| Route | `scrollWidth` | `clientWidth` | Horizontal overflow |
|---|---|---|---|
| `hub` | 640 | 640 | no |
| `live` | 640 | 640 | no |
| `map` | 640 | 640 | no |
| `studio` | 640 | 640 | no |
| `bookings` | 640 | 640 | no |
| `agent` | 640 | 640 | no |
| `authoritative` | 640 | 640 | no |
| `twin` | 640 | 640 | no |

No horizontal overflow at 200 % zoom on any route.

### 2.3 Capability-state probe

The probe declared a HARD `STEP_FREE_REQUIRED` directly through the backend and then checked
whether any route renders the capability or its evidence state:

| Check | Result |
|---|---|
| `clear` capabilities → 200 | yes |
| Declare HARD `STEP_FREE_REQUIRED` with unknown provider evidence → 200 | yes |
| `capabilityProbeAnyRouteShowsCapability` | **`true`** |
| `capabilityProbeAnyRouteShowsEvidenceState` | **`true`** |

So the capability **and its evidence state** do reach the UI. The capability round-trips
through the real frontend. (This does not test whether the evidence state shown matches the
gate's view — `EAC_REFERENCE` shows those two can disagree; see
`ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md` §4.)

## 3. Accessibility debt found in the rendered DOM

| Measure | Value | Note |
|---|---|---|
| `namelessStatusNodes` | **248** | status/`role=status` nodes with no accessible name |
| `clippedTextNodes` | **24** | text clipped by its container |
| `unlabelledControls` | **40** | interactive controls with no accessible name |
| `colourOnlyStatusNodes` | **0** | **good** — no status conveyed by colour alone |

`colourOnlyStatusNodes: 0` is a genuinely good result. The 248 nameless status nodes and 40
unlabelled controls are the main outstanding a11y debt: a screen-reader user gets no
announcement for a large fraction of the live state, and 40 controls cannot be identified.
Tag: `FINAL_V19`.

## 4. Bootstrap

The probe reuses the sealed demo rather than constructing state: it clicks
**"Use the sealed Tianjin demo"**, then persists `storageState` (localStorage
`citynexus.v8.journey_id` = `84c68e9a-4ba9-4470-b2eb-882bdc2b222f`) for the remaining cells.
`web_mobile_bootstrap.json` → `seeded: true`. So the 64 cells all ran against one consistent
sealed journey, not 64 divergent states.

## 5. Verdict table

| # | Finding | Result | Tag |
|---|---|---|---|
| 1 | App boots and renders on all 4 viewports × 2 motion settings × 8 routes | **holds** — 64/64, 0 page errors | — |
| 2 | No horizontal overflow at any viewport | **holds** | — |
| 3 | No horizontal overflow at 200 % zoom | **holds** — 8/8 routes | — |
| 4 | Every tabbable element has a visible focus indicator | **holds** — 16/16, 3 px solid outline | — |
| 5 | Status is never conveyed by colour alone | **holds** — 0 colour-only status nodes | — |
| 6 | Status nodes have accessible names | **VIOLATED** — 248 nameless | `FINAL_V19` |
| 7 | Interactive controls have accessible names | **VIOLATED** — 40 unlabelled | `FINAL_V19` |
| 8 | Text is not clipped | **VIOLATED** — 24 clipped text nodes | `FINAL_V19` |
| 9 | A declared HARD capability reaches the UI, with its evidence state | **holds** — both `true` | — |
| 10 | Reduced-motion is respected | **holds** — no page errors in either setting | — |

## 6. Recommendation (not applied)

1. Give the 248 status nodes and 40 controls accessible names
   (`aria-label` / `aria-labelledby`), starting with the live-journey status region.
2. Fix the 24 clipped text nodes at the two smallest viewports.
3. When merging `EAC_REFERENCE`, make the UI's evidence state and the gate's evidence state
   come from the same projection, otherwise the UI can display "unknown" for a place the
   planner treats as verified.
4. Keep the reduced-motion and 200 %-zoom probes in CI — they are cheap and both currently
   pass, which is worth protecting.
