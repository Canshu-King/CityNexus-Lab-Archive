# REMAINING_PRODUCT_GAPS.md

Ordered by how much each blocks a READY verdict.

## Blocking

1. **The canonical visible-UI acceptance run was not completed.** The two P0
   truth blockers were fixed and driven, and the affected flows were exercised
   through the real API and targeted UI, but the full 22-step
   `docs/VISIBLE_UI_ACCEPTANCE.md` chain was not driven end to end in one
   browser session. `VISIBLE_UI_TRACE.json` is therefore **not** in this
   package. No READY claim is possible without it.
2. **Consumer order import is not built.** Trips → 预订 is still a JSON
   workbench. Required: paste confirmation text / manual form / screenshot →
   parsed preview with editable fields → explicit confirm, with raw JSON moved
   behind Advanced.
3. **Activity detail screen is missing** (reference 08). The itinerary shows
   time, duration and type per stop; there is no dedicated page with transit,
   cost, why-recommended, nearby suggestions and add/replace.
4. **Copilot product cleanup is not done.** The default view still surfaces
   authority/semantic boundary wording (`UNVERIFIED`, `UNKNOWN`,
   `NONESARCH`) and does not give a useful Chinese answer to 鼓浪屿好玩吗？
5. **Visual product pass is not done.** Cards, sub-tabs and Chinese copy exist,
   but the acceptance screens still read closer to the previous console than to
   the ten reference images.

## Important, not blocking

6. **A CLOSURE on a POI inside a stay-materialised plan is refused, not
   repaired.** After a stay is selected, the replan path cannot fully resolve
   the stay plan's mobility identity, so recovery returns
   `mobility evidence unavailable`. The refusal is honest — it never fakes a
   repair — but a real traveller would get no recovery path. This is the most
   valuable next backend fix.
7. **Stay names are often generic.** Chinese OSM hotels frequently carry no
   `name` tag, so some cards show "酒店" plus an address.
8. **Stay price is unknown.** OSM has no rates, so price shows as 暂无价格. A
   rate provider or captured inventory is required for price comparison.
9. **Budget advisory is missing.** No warning for implausible
   duration/party/budget combinations.
10. **Map tiles are blocked** on this network (`tile.openstreetmap.org`). The
    map still renders route geometry and markers from real coordinates and
    degrades to a readable canvas.
11. **Long-trip itinerary** (>7 days) was not exercised; no journey here
    exceeded three days.

## What this round did change

The two Road-Prep truth blockers are fixed and regression-protected:

* **T1** — a stay selection augments the chosen itinerary instead of erasing the
  real-city POIs (6 POIs preserved, 2 nights inserted, anchors pinned, gate
  passes).
* **T2** — no CLOSURE/WEATHER event can settle as an accepted no-op; a physical
  disruption either produces a material change or an explicit refusal.

Plus four regression tests that lock both behaviours in.

## Explicitly out of scope

No V19.3/V20 architecture work. No unrelated backend expansion.
