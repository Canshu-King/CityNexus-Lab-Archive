# PRODUCT_BREAKTHROUGH_REPORT.md

## Verdict

**`BLOCKED_FOR_REAL_USER_TRIAL`**

The Snapshot M truth gaps are closed and real consumer-product work landed
tonight (consumer booking import, Activity Detail coordinates, truthful cost
states, Trip bookings tab restructured). The visible same-Xiamen end-to-end
chain required for READY was **not** completed in one browser session, so READY
is not claimed.

## Execution order followed

1. Read `README_FIRST.md`, `OVERNIGHT_MASTER_MISSION.md`,
   `TIME_BUDGET_AND_STOP_RULES.md`, `PRODUCT_BUILD_BACKLOG.md`,
   `VISIBLE_UI_ACCEPTANCE.md`, `AUTONOMOUS_PRODUCT_LAB.md`.
2. Executed the embedded **Snapshot M RoadPrep** first, inside the 60–90 minute
   box.
3. Then moved to consumer-product work.

## Phase 1 — Snapshot M truth closure (timeboxed)

Probe first, against the authoritative backend:

```
FAIL case_no_silent_duration_shrink
  => hotel selection silently shortened activity from 2:00:00 to 1:00:00
FAIL case_pinned_pair_requires_travel
  => pinned nodes were accepted despite only 10 minutes gap for 30 minutes travel
```

Both reproduced exactly. Fixes:

* **No silent duration shrink.** `flexible` means movable in time, not
  disposable in duration. A visit that cannot fit its own day now raises
  `STAY_ITINERARY_CONFLICT:NO_SAME_DAY_SLOT` instead of being shortened.
* **Pinned reachability.** Every consecutive pinned pair must satisfy
  `previous.end + travel(previous, next) <= next.start`, otherwise
  `STAY_PINNED_MOBILITY_CONFLICT`. Two operations at the *same property*
  (luggage drop → check-in) cost no travel.
* **Luggage drop respects real travel.** It was hard-coded to
  `arrival + 60 minutes`, which could place the drop before the arrival leg was
  possible. It is now derived from the actual inbound travel time.
* **Fastest feasible mode.** Reachability used WALK only, making a
  hotel-to-airport leg look like a 170-minute impossibility. It now takes the
  fastest feasible mode, so the rule reflects real traveller behaviour while
  still refusing genuinely unreachable pinned truth.
* **Activity Detail coordinates come from the Place row.**
  `activity_schema()` / `plan_schema()` now resolve Place coordinates, CRS,
  category and opening hours, so Activity Detail shows real coordinates even
  when the activity metadata lacks them.
* **Known-free vs unknown price.** Covered by permanent tests against
  `_place_metadata`: `cost_minor = 0` with KNOWN evidence stays
  `price_known = True` (UI: 免费), unknown stays `price_known = False`
  (UI: 暂无价格).

Probe after the fix:

```
PASS case_no_silent_duration_shrink
PASS case_pinned_pair_requires_travel
```

Seven permanent regressions were added in
`backend/tests/test_snapshot_m_truth_edges.py`.

## Phase 2 — Consumer product

### Consumer booking import — DONE

Trips → 预订 previously rendered the **raw-JSON workbench** on the golden path.
It now renders the consumer flow first:

* **粘贴确认信息** — paste a confirmation; the deterministic parser extracts
  the reference and times, then shows a draft.
* **手动填写** — a new manual form (type / title / confirmation number / from /
  to / departs / arrives / amount) for a traveller who has a booking but no text
  to paste. It posts through the same `inbox/import` path, so it lands in the
  identical preview → confirm flow.
* **Preview** — the draft shows the extracted fields with editable anchor role,
  departure and arrival before anything is committed.
* **Confirm** — commit only after explicit confirmation.
* **Raw JSON** — moved behind a **高级 / 开发者** disclosure.

Verified in a real browser (390x844, Chinese locale, one journey):

```
open-bookings-tab   200
manual-tab-present  yes
manual-form-open    opened
preview-draft       shown
ERRORS: 0
```

Screenshots: `screenshots/after/B1_manual_form.png`,
`B2_manual_preview.png`.

### Activity Detail — DONE (truthfulness)

Coordinates now come from the real Place row. Cost shows three distinct states
(免费 / currency+amount / 暂无价格). "附近" is only used when a stop is actually
within 1.5 km; otherwise the copy says plainly that the stops are other stops on
the same trip, with real distances shown.

### Trip structure — retained and improved

行程 / 住宿 / 预订 / 花费 sub-tabs; itinerary is the default tab; the raw-JSON
workbench is demoted behind Advanced.

## What was NOT completed

* The **full visible same-Xiamen chain** (create → AI → candidates → select →
  itinerary → activity detail → hotel → booking import → Copilot → map → live →
  disruption → accept → final state) was not driven as one browser session.
  `VISIBLE_UI_TRACE.json` is therefore **absent** rather than fabricated.
* **Today** still leads with generic copy rather than current-trip state.
* **Copilot** does not yet answer `鼓浪屿好玩吗？` with a useful traveller answer.
* **Me** still shows 权限边界 / ADVISORY as primary content.
* **Hotel comparison** differentiation and the **Live** traveller-first
  viewport were not reworked tonight.
* Budget sanity advisory not built.

These are listed in `REMAINING_PRODUCT_GAPS.md`.

## Honest statement

The night produced real, verified product work — not another backend-only
package. But the acceptance gate is the visible same-Xiamen flow, and it was not
completed. The verdict is therefore BLOCKED, not READY.
