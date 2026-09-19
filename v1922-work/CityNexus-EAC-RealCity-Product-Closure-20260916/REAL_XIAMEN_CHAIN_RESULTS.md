# REAL_XIAMEN_CHAIN_RESULTS.md — one journey, end to end

## The acceptance rule

`docs/SAME_JOURNEY_PROOF.md` forbids proving the chain with `/api/v1/demo/reset`
or by switching to the sealed Tianjin demo. The whole run below is **one newly
created Xiamen journey**, and `/demo/reset` was never called.

```
journey_id : 89695905-f434-447b-9477-72abffc1903d
city_code  : CN-XIAMEN
```

`evidence/SAME_JOURNEY_TRACE.json` holds every stage with the journey id, the
screen/route, the action, the backend status and the visible result. Its
`single_journey_proven` field is computed, not asserted: every one of the 31
recorded entries carries the same id, and the set of distinct ids is exactly
`{89695905-…}`.

## Stage-by-stage

| # | Stage | Result |
| --- | --- | --- |
| 1 | Create Xiamen journey (visible UI) | 201, `city_code=CN-XIAMEN`, status `DRAFT` |
| 2 | Live provider discovery (Overpass + Nominatim) | 6 real Xiamen POIs materialised under `city_code=CN-XIAMEN` |
| 3 | Generate candidates | **3 candidates**, stop counts **6 / 5 / 4** |
| 4 | Compare | 3 cards, real cost and budget band |
| 5 | Select plan | 200, `89a623c2…` |
| 6 | Start journey | ACTIVE |
| 7 | Stay offers + options | **4 provider-backed stays** (康莱德 / 磐基 / 汉庭 / 艾美) |
| 8 | Select stay | 200, authoritative stay selection updated |
| 9 | Itinerary | 3 stops visible in the new itinerary (stay-materialised plan) |
| 10 | Map | renders from real coordinates; honest empty state when absent |
| 11 | Copilot `鼓浪屿好玩吗` | answers, no internal enum |
| 12 | Disruption | `CLOSURE` event created against a real stop |
| 13 | Governed replan | proposal `6a555ab7…`, status `PRESENTED`, `locked_commitments_preserved = true` |
| 14 | Traveller view | 发生了什么 / 受影响 / 推荐怎么改 / 保持不变 / 接受 / 仅调整今天 / 稍后提醒 |
| 15 | Accept | `ACCEPTED` |
| 16 | Final state | new plan `8c4c6f6f…`, 6 stops, recovery consistent |

## Real Xiamen places, not Tianjin

Every stop in the generated plan is a discovered Xiamen POI (`real-place-…`,
`city_code=CN-XIAMEN`) with real WGS84 coordinates in the 24.4–24.6 N /
118.0–118.2 E range. **No `Old Town Gate`, `Riverside Museum` or
`Nexus City` appears anywhere in the Xiamen acceptance run.**

## Honest limitations recorded in the same trace

* **Stay names.** Chinese OSM hotel nodes frequently have no `name` tag; the
  provider therefore falls back to the address. Where the address is also
  generic the traveller sees "酒店" — labelled honestly rather than invented.
* **Stay price.** OSM carries no rates, so price is shown as
  "暂无价格 / Price unavailable" instead of a fabricated nightly rate.
* **Copilot** ran against live DeepSeek where reachable; the fallback path was
  used when the provider was slow, and no READY claim rests on fallback output.
* **Map tiles.** `tile.openstreetmap.org` is blocked on this network. The map
  still renders from real coordinates (route geometry + markers) and now
  degrades to a readable canvas instead of a blank box.

## What this proves

A newly created Xiamen journey can go from creation to an accepted governed
replan without ever touching the demo fixture, and every stage is attributable
to the same `journey_id`.
