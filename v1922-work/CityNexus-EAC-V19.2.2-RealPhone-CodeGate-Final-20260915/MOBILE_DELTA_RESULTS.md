# MOBILE_DELTA_RESULTS.md — Focused mobile trial flows

## Scope discipline

The broad responsive shell was already verified in the previous round
(64/64 cells, 0 page errors, 0 horizontal overflow) and was **not** redone.
This round tests only the two mandated viewports and only the flows affected by
the new recovery / stale UI.

## Environment

| Item | Value |
| --- | --- |
| Viewports | 390x844, 430x932 (emulated, `isMobile`, `hasTouch`, reduced motion) |
| Browser | headless Chrome via Playwright 1.63 |
| Frontend | `snapshot_d/frontend` served by Vite 7.3.6 on 127.0.0.1:4214 |
| Backend | `snapshot_d/backend` served by uvicorn on 127.0.0.1:8000, throwaway SQLite |
| AI | disabled (deterministic) |

## Results

| Flow | 390x844 | 430x932 |
| --- | --- | --- |
| **C4 anchored journey** (plans / select / start) | 3 / 200 / 200 | 3 / 200 / 200 |
| **Mid-trip HARD recovery** | panel visible; replan + acknowledge present | panel visible; replan + acknowledge present |
| **Stale evidence warning** | start 409 `STALE_RECOMPOSE_REQUIRED`; panel visible ("Trip evidence needs re-syncing") | same |
| **GPS allowed** | rendered; no horizontal overflow | rendered; no horizontal overflow |
| **GPS denied** | rendered; no horizontal overflow | rendered; no horizontal overflow |

* Route rendered in both viewports: `/v8/authoritative` (C4 / recovery / stale)
  and `/v8/live` (GPS).
* **Page errors: 0** across all flows and viewports.
* **Horizontal overflow: 0** across all flows and viewports.
* SSE reconnect and backend reconnect were **not touched** by this round, so
  those flows were not re-run (per the stated scope).

## Evidence

`evidence/mobile_probe_d.json` contains the per-viewport, per-flow records,
including `ui_panel_visible`, `ui_replan_action`, `ui_acknowledge_action`,
`experience_flags_staleness`, `start_status`, `horizontal_overflow` and
`page_errors`.

## Explicit non-claims

* **No physical-device testing.** Every measurement above is from emulated
  viewports in headless Chrome on the build host. It does not establish
  behaviour on real phone hardware, real GPS hardware, real network conditions,
  real battery/thermal behaviour, or real touch ergonomics.
* No real payment was executed.
