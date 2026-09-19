# PRODUCT_RESULTS.md — consumer product work

The Road-Prep is explicit: after the narrow backend fixes, **stop backend
archaeology** and finish the consumer product. This round did that, within the
remaining budget.

## Completed this round

### Activity detail (reference screen 08) — DONE

`frontend/src/features/trip/ActivityDetail.tsx`, reachable by tapping any stop
on the itinerary.

Verified in a real browser (390x844 and 430x932), journey
`ee4e67aa-c680-42bc-bae7-fb7b808c35e2`:

```
/v8/trips   itinerary-open   4 stops
/v8/trips   activity-detail  opened    厦门景点0
/v8/trips   detail-fields    厦门景点0 | 1 小时 | 暂无价格 | 暂无数据 | 暂无坐标
/v8/trips   back-to-itinerary ok
```

The screen shows only provider-backed facts: title, day, start/end clock,
duration, travel-from-previous, cost, opening hours, category and coordinates.
Where the backend supplied nothing it says **暂无价格 / 暂无数据 / 暂无坐标**
rather than inventing a rating, ticket price or "why we recommend this".

Actions: 在地图上查看 (disabled when there are no coordinates), 问问 Copilot,
and a nearby-suggestions list built from the same plan's real stops.

### Copilot product cleanup — DONE

The default Copilot view no longer exposes internal vocabulary:

| Before | After |
| --- | --- |
| `Authority boundary` | removed; a single traveller sentence replaces it |
| "Reversible, low-risk changes may run inside your envelope…" | "我可以给出建议，但任何花钱或改动已确认预订的操作，都会先等你确认。" |
| `Semantic boundary` block always visible | moved behind an **高级详情 / Advanced details** disclosure |

Verified: a scripted sweep of `/v8/hub`, `/v8/trips`, `/v8/map`, `/v8/agent`,
`/v8/me`, `/v8/live` at both viewports found **no** occurrence of
`PlanVersion`, `C4_Anchored`, `semantic_key`, `Authority boundary`,
`Semantic boundary`, `NONESEARCH` or `REQUEST_PLACE_SEARCH`.

### Trips IA — already in place from Snapshot I, retained

Trips is a sub-tabbed workspace (行程 / 住宿 / 预订 / 花费) rather than one long
scrolling document, and the itinerary is the default tab.

## Screens captured this round

`screenshots/after/`: Today, Trips, Map, Copilot, Me, Live, Activity detail and
the itinerary — all at 390x844, with the tab sweep repeated at 430x932.

## Still open

| Item | Status |
| --- | --- |
| Consumer booking import | **NOT DONE** — still the JSON workbench under 预订 |
| Full same-Xiamen visible-browser chain | **NOT DONE** — see below |
| `VISIBLE_UI_TRACE.json` | **NOT PRODUCED** |
| Material implementation of all 10 reference screens | **PARTIAL** |
| Budget advisory | **NOT DONE** |

### Why the visible chain is not claimed

`docs/REAL_USER_PRODUCT_GATE.md` requires create → select plan → select hotel →
import booking → accept replan to be performed **through the visible UI**, and
explicitly says an API call may not substitute. This round drove:

* the itinerary and the new activity detail through the visible browser;
* the tab sweep, Copilot cleanup and overflow checks through the visible browser;

but it did **not** drive create → plan → hotel → import → accept as one
browser session. That would be an over-claim, so `VISIBLE_UI_TRACE.json` is
deliberately absent and the verdict stays BLOCKED.

## Honest note on the environment

Live Overpass retrieval was intermittent during this round (`ConnectTimeout` on
the public mirrors), so the stay/identity work was verified with deterministic
offline harnesses. Those harnesses are reproducible in about one second and are
included as evidence scripts.
