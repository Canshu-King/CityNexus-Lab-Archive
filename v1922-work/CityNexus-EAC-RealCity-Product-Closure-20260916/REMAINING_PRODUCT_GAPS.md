# REMAINING_PRODUCT_GAPS.md

Ordered by how much each blocks a READY verdict.

## Blocking

1. **Order import is not a consumer flow.** Trips → 预订 still asks for a JSON
   payload. The mission requires: paste confirmation *text* / manual entry →
   parsed preview with editable fields → explicit confirm. The safety property
   (nothing is committed without confirmation) already holds; the *product* does
   not.
2. **Activity detail screen (reference 08).** Per-stop time, duration, type and
   protected state exist inside the itinerary, but there is no dedicated screen
   with transit, cost breakdown, "why we recommend this", add/replace and map.
3. **Visual parity with the reference system.** Cards, sub-tabs, sticky CTAs and
   Chinese copy are in. Typography scale, spacing rhythm, illustration and
   overall polish are still closer to the previous console than to the ten
   reference screens.

## Important, not blocking

4. **Today hero copy.** Still partly generic ("Your next city, already
   considered"). Should answer 现在该做什么 / 下一步 / 有没有风险 for the actual
   trip, e.g. 厦门之旅.
5. **Stay naming.** Chinese OSM hotels frequently have no `name` tag, so some
   cards read "酒店" plus an address. Honest, but not a great consumer
   experience.
6. **Stay price.** OSM has no rates. Prices show as 暂无价格. A real rate
   provider (or captured inventory) is needed before price comparison is
   meaningful.
7. **Budget advisory.** `EAC_NEXT_MISSION.md` asks for a warning when duration /
   party / budget is implausible (e.g. 39 days, 2 people, CNY 3000). Not built.
8. **Map tiles.** `tile.openstreetmap.org` is blocked on this network, so the
   raster basemap does not load. The map still renders route geometry and
   markers from real coordinates, and now degrades to a readable canvas — but a
   reachable or self-hosted tile source is needed for a real basemap.
9. **Multi-day realism.** The itinerary groups by date and has a week strip, but
   no journey in this environment had more than three days, so the >7-day path
   was not exercised with real data.
10. **Overpass fragility.** The public mirrors time out under load; the provider
    rotates mirrors and falls back to Nominatim, and discovery was retried
    during the run, but a paid/self-hosted OSM endpoint would be more reliable.

## Environment facts that shaped this round

* Live `DEEPSEEK_API_KEY` from the user environment was injected into the
  backend child process only. It was never printed, logged or packaged.
* Live providers used: Overpass (mirror rotation), Nominatim, Photon,
  Open-Meteo, DeepSeek.
* Journey subject: `89695905-f434-447b-9477-72abffc1903d`, `CN-XIAMEN`, dates
  2026-11-06 → 2026-11-08, 2 travellers, CNY 3000 total / CNY 1000 stay.

## Explicitly out of scope

No V19.3 architecture work. No unrelated backend expansion beyond the fixes the
driven Xiamen run required.
