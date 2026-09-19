# MOBILE_DELTA_RESULTS.md — Focused mobile trial (G05)

## Scope

Only the two mandated viewports and only the flows this round changed. The
broad responsive shell was verified in earlier rounds and was not redone. SSE
reconnect and backend reconnect were not touched, so those flows were not
re-run.

## Environment

| Item | Value |
| --- | --- |
| Viewports | 390x844, 430x932 (emulated, `isMobile`, `hasTouch`, reduced motion) |
| Browser | headless Chrome via Playwright |
| Frontend | `snapshot_d/frontend` on 127.0.0.1:4214 (Vite) |
| Backend | `snapshot_d/backend` on 127.0.0.1:8000 (uvicorn), throwaway SQLite |
| AI | disabled (deterministic) |

## Results — 18 flow runs, 0 page errors, 0 horizontal overflow

| Flow | 390x844 | 430x932 |
| --- | --- | --- |
| ARRIVAL boundary | `no_flexible_before_arrival = true` | true |
| DEPARTURE boundary | `no_flexible_after_departure = true` | true |
| Mid-trip HARD recovery | panel visible; label "Acknowledge warning" | same |
| Acknowledge warning | backend 200, `resolved=false`, banner visible, `needs_review=true` | same |
| No alternative | `RECOVERY_REQUIRED_NO_ALTERNATIVE`, `replan_attempted=true` | same |
| Feasible replacement resolves | recovery `null`, `needs_review=false`, panel gone | same |
| Stale candidate warning | `stale=true`, `selectable=false`, start 409, panel visible | same |
| GPS allowed | rendered, no overflow | same |
| GPS denied | rendered, no overflow | same |

Notable measured values:

* ARRIVAL 12:30 -> anchor ends 12:50; every flexible activity starts at or
  after that.
* DEPARTURE 15:30 -> anchor starts 15:10; every flexible activity ends at or
  before that.
* The acknowledgement button label is `Acknowledge warning` on both viewports
  (`ui_acknowledge_is_governed = true`), replacing the unsafe
  `Continue without changes`.
* The recovery banner remains visible after acknowledgement, and the backend
  reports `resolved = false`.

## Evidence

`evidence/mobile_v1923_d.json` — per-viewport, per-flow records including
`no_flexible_before_arrival`, `no_flexible_after_departure`,
`ui_acknowledge_label`, `banner_still_visible`, `state`, `stale`,
`selectable`, `start_status`, `horizontal_overflow` and `page_errors`.

## Explicit non-claims

* **No physical-device testing.** Every measurement is from emulated viewports
  in headless Chrome on the build host. It does not establish behaviour on real
  phone hardware, real GPS hardware, real network conditions, battery/thermal
  behaviour, or real touch ergonomics.
* No real payment was executed.
