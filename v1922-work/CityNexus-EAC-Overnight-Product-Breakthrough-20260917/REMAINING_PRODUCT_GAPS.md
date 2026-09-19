# REMAINING_PRODUCT_GAPS.md

## Blocking a READY verdict

1. **The full visible same-Xiamen chain was not completed.** Create → AI →
   candidates → select → itinerary → activity detail → hotel → booking import →
   Copilot → map → live → disruption → accept → final state was not driven as one
   browser session, so `VISIBLE_UI_TRACE.json` is absent.
2. **Today is still generic.** It leads with 你的下一座城市，已被充分考虑 rather
   than the current trip (厦门之旅 / date / next action / today's plan / booking
   summary / risk / AI CTA).
3. **Copilot does not answer 鼓浪屿好玩吗？ usefully.** Vocabulary cleanup is done;
   answer quality with trip context and human action buttons is not.
4. **Me still shows 权限边界 / ADVISORY as primary content** instead of profile,
   preferences, documents, wallet, language and app settings.
5. **Hotel cards are not meaningfully differentiated** by real data.
6. **The Live traveller-first viewport** was not reworked.
7. **Material implementation of the ten reference screens is partial.**
8. **Budget sanity advisory** (e.g. 39 days / 2 people / CNY 3000) is not built.

## Important, not blocking

9. **Booking confirm → appears in Trips** was not asserted through the browser.
10. **Hostile-user loops** (five personas) were not run.
11. **Failure states** for disconnect-during-flow, refresh-during-load,
    double-tap, provider-unavailable and stale/recovery were not exercised.
12. **Stay price unknown** (OSM has no rates) and **Chinese stay names often
    generic**.
13. **Public Overpass reliability**; the provider now honours the environment
    proxy by default, which suits the user's Mihomo network.
14. **Map tiles blocked on this network**; the map renders real coordinates and
    degrades to a readable canvas.

## Closed tonight

* **Snapshot M truth edges** — no silent duration shrink; pinned reachability;
  luggage drop respects real travel; fastest feasible mode; superseded property
  operations dropped; Activity Detail coordinates from the Place row; known-free
  vs unknown price. Seven permanent regressions.
* **Consumer booking import** — manual entry form added, consumer flow promoted
  to the golden path, raw JSON moved behind Advanced, top-level draft handling
  fixed and verified in a browser.
* **Activity Detail truthfulness** — real coordinates, three distinct cost
  states, 附近 only when spatially true.

## Explicitly out of scope

No V19.3/V20 architecture work.
