# FINAL_HOTFIX_RESULTS

Round: narrow final hotfix + evidence closure. Repository: `D:\moodle\CityNexus`.
Generated: 2026-09-17T18:50:47.934545+08:00

## Verdict

**READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL**

## What was fixed in this round

| Blocker | Status | Fix |
|---|---|---|
| B1 stale final Copilot evidence | FIXED | `VISIBLE_UI_TRACE_FINAL.json` generated after the last source edit; Copilot captured live |
| B2 Me exposes ADVISORY / 权限边界 | FIXED | Me rebuilt: traveller facts first, policy internals under 高级详情 |
| B3 price + budget truth | FIXED | three cost states (免费 / 金额 / 暂无价格); no budget verdict without full price coverage; budget advisory added |
| B4 Wallet developer-shaped | FIXED | JSON behind 高级 with a guarded parse and a localised error; internal labels humanised |
| B5 deep links blank | FIXED | `/v8/today`, `/v8/copilot`, `/v8/bookings` and unknown paths all render |
| B6 old-plan AI false success | FIXED | success counts only artifacts this run created |
| secondary vocabulary | FIXED | What-if Studio / JourneyTwin / deterministic / DeepSeek removed from the default surfaces |
| evidence assertions | FIXED | stay truth reads the real payload and joins the offer; triple mapping states its entity set |

## Two additional real defects found while revalidating

1. **Stay calendar vs feasibility gate used two different leg generators.** The
   calendar reserved the slowest mode (up to 134 minutes) while the plan's own
   selected leg fact was the fastest (4-25 minutes). Every hotel was therefore
   rejected with a false `STAY_ITINERARY_CONFLICT:NO_SAME_DAY_SLOT`.
   `app/stay_mobility.py::_travel_minutes` now reserves the same leg the gate
   validates.
2. **The materialiser trusted stale adjacency facts.** After the calendar
   re-ordered the stops, `app/operations/v9.py::_selected_facts` matched
   previously captured `MobilityFact` rows belonging to a different adjacency,
   producing `INSUFFICIENT_TRAVEL_GAP` / `LEG_ARRIVES_LATE` on a feasible plan.
   Each leg is now re-derived from the calendar's own generator.

## Final trace

`VISIBLE_UI_TRACE_FINAL.json` — one journey `d3f0cf26-7e62-47a7-8c39-111c61adeb95`, 18 steps,
failed = None, console errors = 0.
Screenshots: `FINAL_XIAOMI_SCREENSHOTS/` at the Xiaomi 13 Ultra CSS size (412x915
at DPR 3.5).

## Test results

`python -m pytest -q` -> **748 passed, 0 failed, 15 skipped** (includes the new
`tests/test_final_hotfix_cost_and_routes.py`). Frontend production build succeeds.

## Known limitations (honest)

* Public OSM/Overpass/Nominatim providers are intermittently unreachable from
  the test network; the product reports this rather than inventing data.
* Discovered OSM attractions genuinely carry no ticket price, so they correctly
  read 暂无价格. The 免费 state is proven by unit test, not by an OSM POI, because
  OSM does not publish "free" as a fact.
