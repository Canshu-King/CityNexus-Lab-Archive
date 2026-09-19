# HOTEL_FLOW_RESULTS.md — real hotel compare / select

## The gap this closes

Snapshot H could not produce a Xiamen stay at all:

* `CapturedAccommodationProvider` only knows the Tianjin fixture;
* `LiveAccommodationProvider.discover()` returns `()` unconditionally.

So `/stays/offers/capture` returned zero offers for any real city and the Trips
page had nothing to compare. Calling that "PASS because the route exists" is
exactly what `SAME_JOURNEY_PROOF.md` forbids.

## What was implemented

`backend/app/integrations/stay_osm.py` — a real provider:

1. resolves the city anchor with **Photon**;
2. queries **Overpass** (`tourism=hotel|guest_house|hostel`) with mirror
   rotation (`overpass-api.de` → `kumi.systems` → `private.coffee`);
3. tops up from **Nominatim** free-text search when the Overpass result is thin
   or unavailable;
4. deduplicates on **OSM identity**, not on name, because several distinct
   Chinese properties are all tagged `酒店`.

`capture_accommodation_offers()` now uses the fixture only when the city
actually has one, and otherwise uses this provider.

## Provider-backed facts only

| Field | Status |
| --- | --- |
| property name | provider (OSM `name` / `name:zh`, else the address) |
| coordinates | provider, WGS84, used for the walking/itinerary relationship |
| walking burden | computed from the journey's own mobility evidence |
| arrival / departure fit | computed by the existing option ranker |
| refundability | provider; OSM has none, so `false` is reported honestly |
| **price** | **not available from OSM** — shown as 暂无价格 / "Price unavailable" |

Price is deliberately **not** invented. A fabricated nightly rate would be a
truth violation of exactly the kind the earlier gates were created to stop.

## Verified in the same Xiamen journey

| Check | Result |
| --- | --- |
| `stays/offers/capture` | offers captured under `city_code=CN-XIAMEN` |
| `stay-options/generate` | **4 options** |
| Names visible | 厦门康莱德酒店, 厦门磐基酒店, 汉庭酒店, 厦门艾美酒店 |
| Coordinates | real Xiamen lat/lon per option |
| Walking minute per option | present |
| Select | 200; authoritative stay selection updated; Trips reflects it |
| UI | `HotelsPanel` renders cards with price / walking / fit / cancellation / reason |
| Price unknown | displayed as 暂无价格, never a fake number |
| Empty state | explicit "暂时没有可比较的住宿" when the provider returns nothing |

## UI changes

* Trips is no longer one long document: it has **行程 / 住宿 / 预订 / 花费**
  sub-tabs, and 住宿 hosts the comparison.
* `HotelsPanel` reads `/experience` first and only pays for a live capture when
  nothing has been captured yet, so opening the tab is not a slow provider call
  on every visit.
* Selecting a stay calls the existing authoritative
  `stay-options/{id}/select`, so the Trip view and the backend cannot disagree.

## Honest limitation

Chinese OSM hotels are often unnamed nodes. Where neither `name` nor a
distinguishing address exists the card reads "酒店"; the traveller is told it is
a provider entry rather than shown an invented brand.
