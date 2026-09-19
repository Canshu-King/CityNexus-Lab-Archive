# MOCK_MOBILITY_LIMITATION — fabricated fallback travel time

Status: **OPEN — pre-existing defect, root cause identified, NOT fixed in this package.**
Discovered while closing the R1 closure/replan blocker on 2026-09-17.

## Summary

`data/mock/mobility_matrix.json` contains **9 explicit route entries** plus a
single `default_minutes` value. Every route pair that is *not* one of those 9
silently receives `default_minutes` = **20 minutes**, which is not a measurement
of anything. It is a constant.

```json
{ "minutes": { ...9 entries... }, "default_minutes": 20 }
```

`MockMobilityProvider.estimate_minutes` (backend/app/integrations/mock/providers.py):

```python
key = f"{origin_place_id}|{destination_place_id}"
return int(self._fixture["minutes"].get(key, self._fixture["default_minutes"]))
```

## Why this matters

A replan creates adjacencies that did not exist in the frozen baseline. For each
new leg the system calls `_replan_estimate` (backend/app/main.py), which calls
`MobilitySnapshot.estimate_minutes`. When the pair is absent from the frozen
snapshot it captures a *runtime* snapshot from the configured provider. With no
live routing provider configured (`live_valhalla_url` unset) that provider is the
mock, so **every new leg becomes exactly 20 minutes**.

Measured on journey `d9e7067b-e7b9-42f1-81f3-196eaaf0e5c9` (real Xiamen journey,
live Overpass POIs). Every leg of every proposed plan was 20 minutes:

```
a82fa86c...arrival-anchor -> real-place-c270d43c4e4c734b010cedf5 = 20
real-place-c270d43c4e4c734b010cedf5 -> v12:...:departure-anchor  = 20
... 115 calls, all 20 ...
```

Compare the *real* legs of the same journey, frozen from the selected plan:

```
arrival-anchor      -> real-place-07e76... = 11
real-place-0f6a7... -> real-place-1564f... = 11
real-place-1564f... -> stay:...:check-in   =  7
```

## Consequence (user-visible)

The re-timing pass shifts unlocked rows by the inflated 20-minute legs. The
locked check-in at 06:00 is pinned truth and never moves, so the schedule is
pushed into it and the deterministic gate correctly refuses the plan:

```
HTTP 422 no feasible replan proposal:
  ACTIVITY_OVERLAP,
  INSUFFICIENT_TRAVEL_GAP:real-place-1564f860645d87ceaae7949a|stay:osm:node/583066505:check-in
```

7 of 8 mutable stops fail this way. The traveller is told no replacement exists
even though genuine, closer alternatives were found (e.g. 香村瓦缸煨汤馆 is 816 m
from the closed venue and only 575 m from the next locked stop).

The gate is *correct* to refuse: the proposed schedule genuinely overlaps. The
lie is upstream, in the fabricated 20-minute travel time.

## Not fixed here

This package deliberately does **not** change the mobility provider or the
replan estimator. Doing so is a behavioural change to travel-time truth and is
out of scope for the R1 evidence-correction package.

### Options for the follow-up

1. Configure a real routing provider (`live_valhalla_url` / Valhalla matrix) so
   new pairs are measured instead of defaulted.
2. If the mock must remain, fail closed: a pair with no real measurement should
   surface `MOBILITY_DATA_UNAVAILABLE` for the *proposal* rather than being
   silently priced at 20 minutes. `_trip_studio_fact` already does this on the
   planning path (`failures.append(f"MOBILITY_DATA_UNAVAILABLE:{from_key}|{to_key}")`);
   the replan path does not.
3. Derive the fallback from geometry (the codebase already has a deterministic
   distance-based generator, `_mode_fact` in backend/app/stay_mobility.py, used
   by the stay calendar) instead of a constant.

Option 2 is the minimal honesty fix and matches the project's truth rules.

## Evidence

- journey: `d9e7067b-e7b9-42f1-81f3-196eaaf0e5c9` (Xiamen, 14 stops, 1 booking)
- base snapshot: `v12-stay-7db53514d6790472f4ff871b3b9b3c91` (provider `citynexus-synthetic-fixture`)
- `_replan_estimate` instrumentation: 115 calls, all `= 20`
- raw: `REPLAN_422_INSTRUMENTATION.txt`, `MOCK_MOBILITY_FIXTURE.json`
