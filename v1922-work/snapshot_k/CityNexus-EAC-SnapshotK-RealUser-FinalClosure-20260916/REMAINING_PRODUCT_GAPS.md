# REMAINING_PRODUCT_GAPS.md

## Blocking a READY verdict

1. **The full same-Xiamen visible-browser chain was not completed.**
   `docs/REAL_USER_PRODUCT_GATE.md` requires create → select plan → select hotel
   → import booking → accept replan to be driven through the visible UI, and
   forbids substituting API calls. This round drove the itinerary, the new
   activity detail, the Copilot cleanup and a tab sweep in the browser, but not
   that whole sequence. `VISIBLE_UI_TRACE.json` is therefore absent.
2. **Consumer booking import is not built.** Trips → 预订 is still the JSON
   workbench. Required: paste confirmation text / manual form / screenshot →
   parsed preview with editable fields → explicit confirm, with raw JSON behind
   Advanced.
3. **Material implementation of all ten reference screens is partial.** Today,
   Trips, create wizard, plan comparison, hotels, Live and the new activity
   detail exist as product surfaces; the visual system is still not a material
   match to the reference images.
4. **Budget advisory is missing.**

## Important, not blocking

5. **Live B5 end-to-end acceptance not driven.** The mobility-identity mismatch
   is fixed and demonstrated offline; the live run needs a stable provider.
6. **Public Overpass reliability.** The mirrors time out under load; the provider
   rotates mirrors and falls back to Nominatim, but a self-hosted or paid
   endpoint would make live runs reproducible.
7. **Stay price is unknown** (OSM has no rates) and **Chinese stay names are
   often generic**.
8. **Map tiles are blocked on this network**; the map renders real coordinates
   and degrades to a readable canvas.
9. **Cross-journey candidate scoping.** Server-owned structural providers are
   now excluded from the replacement pool, but how discoverable POIs should be
   shared or scoped per journey is still an open product decision.
10. **`/v8/me` still shows 权限边界** in its heading. It is a settings surface
    rather than the golden path, but the wording could move behind Advanced too.

## Closed this round

* **Stay timeline P0s** — CHECK_IN before the first STAY, and no flexible
  activity overlapping locked truth. Both were reproduced with the Road-Prep
  probe first, then fixed by replacing cursor patching with a pinned
  temporal-constraint calendar, and are now protected by eight invariant tests.
* **Disruption target truth** — `current_activity_id` alone is no longer treated
  as proof; a target must be explicitly grounded or the request returns
  `REPLAN_TARGET_UNRESOLVED`.
* **Activity detail** — reference screen 08 is implemented and reachable from
  the itinerary, showing only provider-backed facts.
* **Copilot cleanup** — internal boundary vocabulary removed from the default
  view and moved behind 高级详情.

## Explicitly out of scope

No V19.3/V20 architecture work.
