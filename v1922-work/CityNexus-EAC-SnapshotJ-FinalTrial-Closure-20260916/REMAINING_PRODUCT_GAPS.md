# REMAINING_PRODUCT_GAPS.md

## Blocking

1. **The canonical visible-UI acceptance run was not completed.**
   `docs/VISIBLE_UI_ACCEPTANCE.md` requires create → AI → compare → choose →
   itinerary → hotel → booking import → Copilot → live → accept, all through the
   browser on one Xiamen journey. Only the backend defects were driven this
   round, so `VISIBLE_UI_TRACE.json` is **not** in this package.
2. **Live B5 acceptance not completed.** The identity mismatch is fixed and
   demonstrated offline, but `real Xiamen plan → choose hotel → reload → close a
   mutable POI → material replan` was not driven against live provider data,
   because public Overpass retrieval was intermittent.
3. **Consumer order import is not built.** Trips → 预订 is still a JSON
   workbench; the mission requires paste-text / manual form / screenshot →
   parsed preview → explicit confirm, with raw JSON behind Advanced.
4. **Activity detail screen is missing** (reference 08).
5. **Copilot product cleanup is not done** — the default view still shows
   authority/semantic boundary wording and gives no useful answer to
   鼓浪屿好玩吗？
6. **Visual product pass is not done.**

## Important, not blocking

7. **Cross-journey candidate pollution.** While fixing B5 it became clear that
   the closure-replacement candidate query filters by `city_code` only, so
   POIs materialised by *another* journey in the same city can enter the
   candidate pool. The server-owned structural providers are now excluded, but
   the general question of how discoverable POIs should be shared or scoped per
   journey is still open and worth a deliberate decision.
8. **Public Overpass reliability.** The mirrors time out under load; the
   provider rotates mirrors and falls back to Nominatim, but a paid or
   self-hosted endpoint would make live runs reproducible.
9. **Stay price is unknown** (OSM has no rates) and **stay names are often
   generic** in China.
10. **Map tiles are blocked on this network**; the map still renders real
    coordinates and degrades to a readable canvas.
11. **Budget advisory is missing.**

## What this round changed

All five named backend truth gaps were addressed:

* **B1** structural stay operations survive augmentation (they were dropped);
* **B2** locked activities keep their authoritative window;
* **B3** precise replan reasons are reachable (the branch was dead code);
* **B4** ambiguous physical disruptions are no longer guessed;
* **B5** the mobility identity mismatch is fixed at all three root causes.

Seven new regression tests lock the behaviour in, with **zero new regressions**
across the 716-test suite.

## Explicitly out of scope

No V19.3/V20 architecture work.
