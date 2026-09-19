# BUGS_FOUND_AND_FIXED.md

Every item was observed in a real browser, fixed, and re-verified. Nothing here
is theoretical.

## P0-1 — `/` entered LegacyApp, not the modern product

* **Observed**: `main.tsx` routed on `pathname.startsWith("/v8")`, so `/`
  rendered `LegacyApp`. A first-time user could not reach the modern product
  without typing a hidden URL — the exact anti-goal.
* **Fix**: `App()` returns `<V8Experience/>` by default; `LegacyApp` only at
  `/legacy`.
* **Verified**: `evidence/audit1.json` → `looks_legacy: false`, zero errors.

## P0-2 — Wallet / bookings white screen

* **Observed**: the bookings surface rendered **blank** with
  `ReferenceError: data is not defined`.
* **Root cause**: `function Bookings({ selected, wallet, onImport, busy })`
  declared `data: V8Data` in its prop **type** but never destructured it, while
  the body read `data.journey.budget.currency`. The throw unmounted the whole
  tree.
* **Fix**: destructure `data`. Both call sites already passed it.
* **Verified**: `evidence/audit2b.json` → `trips` renders, no errors.

## P0-3 — primary navigation had no Trips entry, Wallet occupied a golden slot

* **Fix**: `mobileRoutes` → Today / Trips / Map / Copilot / Me; a real `trips`
  route composes the itinerary with the bookings surface.
* **Verified**: DOM labels `["Today","Trips","Map","Copilot","Me"]`; then
  localised to `今天/行程/地图/Copilot/我的`.

## P0-4 — no error boundary: any runtime error trapped the user

* **Observed**: P0-2 proved it — one `ReferenceError` replaced the entire app
  with a white screen and no way back.
* **Fix**: `frontend/src/components/ProductErrorBoundary.tsx`, wired in
  `main.tsx`. Bilingual, states what happened, reassures trip data is safe, and
  offers retry / back to Today / reload plus collapsible technical detail.

## P0-5 — map silently rendered Tianjin for any journey

* **Observed**: `MapPanel.tsx` and `JourneyMap.tsx` fell back to the hardcoded
  coordinate `[117.19, 39.13]` (Tianjin). A Xiamen journey with no coordinates
  would silently show Tianjin.
* **Fix**: removed the fallback everywhere; when no trustworthy coordinates
  exist the map renders an explicit **"尚未获取地图位置"** state. `JourneyMap`
  gained null-safety so a missing route cannot crash the map.
* **Verified**: `evidence/walk2.json` → `empty_state: true`, `map_panel: false`,
  no Tianjin anywhere in the frontend.

## P0-6 — the 行程 tab showed no itinerary at all

* **Observed**: the Trip Studio's day view is keyed on a **stay option**
  (`selected?.days`). With no stay selected, `day_cards = 0` even when a plan
  was chosen and active — the "行程" tab answered none of its three questions.
* **Fix**: new `TripItinerary` groups the authoritative plan's activities by the
  traveller's local date, independent of any stay. Long trips get a **week
  selector** instead of a 39-item day strip (corrections §8).
* **Verified**: `evidence/walk9.json` → real day with 6 stops, times and
  durations; `evidence/gate.json` item 08 `stops=6`.

## P0-7 — backend outage silently looked like "you have no trip"

* **Observed**: when `load()` failed, boot **deleted** the journey id and fell
  through to the create-trip screen. A traveller with a trip would think it had
  vanished.
* **Fix**: a network/backend failure (`TypeError`) is now distinguished from
  "journey not found": the id is kept and an honest panel appears —
  **"连不上服务器 / 你的行程数据没有丢失 / 重试"**.
* **Verified**: `evidence/walkB.json` → offline text is the honest panel and it
  recovers after the backend returns.

## P0-8 — Chinese devices opened in English; language toggle untestable

* **Observed**: locale initialised only from `localStorage`, defaulting to
  `"en"`; `navigator.language` was ignored.
* **Fix**: default from `navigator.language` when the traveller has not chosen;
  added `data-testid="topbar-language"`.
* **Verified**: `evidence/walkC.json` → 菜单 → Menu → 菜单, itinerary intact.

## P1-9 — Copilot exposed internal vocabulary

* **Observed**: Copilot showed `NEEDS CLARIFICATION`,
  `Deterministic fallback`, `Interpretation: deterministic fallback`; the lede
  read "DeepSeek interprets the request; Hermes can propose the next tool step.
  The gateway checks the resulting action against your envelope and captured
  provider facts." Today showed "deterministic gate"; Trips showed
  "Deterministic feasibility passed"; prices showed "Provider price
  unavailable".
* **Fix**: 28 traveller-language replacements across EN and ZH, e.g.
  "I need one more detail", "Answered offline", "What I understood",
  "All safety checks passed", "Price not available". The prohibited list
  (`REQUEST_PLACE_SEARCH`, `REQUEST_REPLAN`, `ACCEPT_REPLAN`, `PlanVersion`,
  `C4_Anchored`, `semantic_key`) appears nowhere.
* **Verified**: `evidence/walk6.json`, `walk7.json`, `gate.json` item 13.

## P1-10 — Copilot could only be submitted with the mouse

* **Observed**: the chat textarea had no Enter handler; Enter inserted a newline
  and nothing happened.
* **Fix**: Enter sends, Shift+Enter makes a new line.

## P1-11 — Copilot panel ate most of the phone screen

* **Observed**: `.cn-copilot-panel` was `max-height: min(690px, 100vh-44px)` —
  **82%** of an 844px screen — and the dock sat at `bottom: 22px`, overlapping
  the bottom navigation.
* **Fix**: a phone media query caps the panel at `min(62vh, 460px)` with internal
  scrolling and lifts the dock to `bottom: calc(84px + safe-area)`.
* **Verified**: `evidence/walk3.json` → panel **32%** of screen, nav overlap
  **0px**.

## P1-12 — vague / jargon copy on Today

* **Fix**: `nav.hub` "Journey Hub" → "Today"/"今天" so the breadcrumb matches
  the bottom navigation; Copilot lede rewritten in traveller language.

## P2-13 — remaining technical prose (open)

"provider evidence" and similar phrases may still appear in secondary screens.
Logged in `REMAINING_PRODUCT_GAPS.md`; not fixed this session.
