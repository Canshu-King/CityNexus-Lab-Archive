# TRUTH_BLOCKER_RESULTS.md — the two P0 fixes

The Road-Prep named two truth blockers as highest priority. Both are fixed.

---

## T1 — a stay selection no longer erases the chosen itinerary

### What was wrong

`build_candidate_nodes()` built the stay graph **from scratch**: arrival anchor,
check-in, one node per night, check-out, departure anchor. The materialiser then
wrote that as the plan. Nothing read the traveller's existing plan, so every
real-city POI silently disappeared.

Reproduced before the fix on a live Xiamen journey:

```
BEFORE  stops 6 : OSM restaurant · OSM cafe · OSM cafe · 星巴克 · 厦门市图书馆殿前分馆 · OSM cafe
AFTER   stops 6 : 厦门高崎国际机场 · Check in · 酒店 · Overnight · 酒店 · Overnight · 酒店 · Check out · 酒店 · 厦门北站
                  ^ zero POIs survived
```

### What changed

`build_candidate_nodes()` now **augments** rather than replaces:

1. `_carried_itinerary_nodes()` reads the current selected/active plan's own
   activities (resolving coordinates from their `Place` rows) and carries every
   schedulable stop forward. Anchors and stay nodes are excluded because the
   stay graph rebuilds them.
2. `_reschedule_with_carried()` re-times the carried stops as a real sequence:
   order preserved, own duration preserved, a genuine travel gap between
   consecutive stops, sightseeing confined to waking hours, and multi-day trips
   rolling to the next morning instead of running to 03:00.
3. `_enforce_sequence()` guarantees the final sequence never overlaps and never
   sits closer than the journey's own mobility evidence allows.
4. The travel gap comes from **`_mode_fact`**, the same generator that
   materialises every stay leg and the same values the feasibility gate later
   validates. Earlier attempts used a local distance heuristic and produced
   schedules that looked feasible and then failed the gate.

### Verified on a live Xiamen journey

`evidence/T1_STAY_PRESERVATION_EVIDENCE.json`, journey
`abd8ed7b-585e-4bfd-bddc-83d45cdc4975`, `CN-XIAMEN`:

```
BEFORE  plan 8f4f64ac  poi=6  stay=0  anchor=0
AFTER   plan dca74c6b  poi=6  stay=2  anchor=2   gate = PASSED
```

Final active plan:

```
 1 arrival    10:00-10:20  厦门高崎国际机场
 2 activity   14:09-15:09  OSM restaurant
 3 activity   17:05-18:05  OSM cafe
 4 stay       22:00-06:00  Overnight · 厦门康莱德酒店     <- night 1
 5 activity   09:00-10:00  OSM cafe
 6 activity   11:20-12:20  星巴克
 7 activity   13:25-14:25  厦门市图书馆殿前分馆
 8 activity   15:08-16:08  OSM cafe
 9 stay       22:00-06:00  Overnight · 厦门康莱德酒店     <- night 2
10 departure  19:50-20:00  厦门北站
```

All six real Xiamen POIs survive, both nights are inserted, and both structural
anchors stay exactly on their original times.

---

## T2 — a physical disruption can no longer settle as a no-op

### What was wrong

When no material repair was available, the replan engine fell through to

```python
heuristic_specs.append(_ReplanCandidateSpec(family="F0_STABLE_COPY"))
```

which is an unchanged copy of the plan. For a CLOSURE that was then accepted,
producing exactly the Snapshot I trace:

```
CLOSURE -> proposal removed=0 added=0 -> ACCEPTED
```

### What changed

1. `F0_STABLE_COPY` is now generated **only for non-physical events**. For
   `CLOSURE` / `WEATHER` the engine records an explicit unresolved reason
   instead:
   * no resolvable target -> `REPLAN_TARGET_UNRESOLVED`
   * target is protected or locked -> `REPLAN_PROTECTED_CONFLICT`
   * movable target but no repair -> `REPLAN_NO_ALTERNATIVE`
2. A `CLOSURE` / `WEATHER` event with no explicit target now resolves the target
   from the traveller's **execution position** (falling back to the first
   non-terminal, non-anchor stop) rather than falling through to a stable copy.

### Verified

`evidence/T2_NOOP_REPLAN_EVIDENCE.json`:

| Case | Result |
| --- | --- |
| CLOSURE on a mutable real POI (plain plan) | **PASS — material**: `removed=1`, status `PRESENTED` |
| CLOSURE on a protected stay node | **PASS — honest refusal**: `closed activity is protected and cannot be replaced automatically` |
| CLOSURE on a POI inside a stay-materialised plan | **refused honestly** (`mobility evidence unavailable`) — see the gap below |

**No CLOSURE or WEATHER event settled as an accepted no-op anywhere.**

---

## Remaining T2-related gap (recorded, not hidden)

After a stay is selected, a CLOSURE on one of the carried POIs is refused with
`mobility evidence unavailable` rather than producing a material repair. The
stay-materialised plan's mobility identity is not yet fully aligned with the
replan path, so the recovery is honest but not yet useful. This is a real
remaining defect and is listed in `REMAINING_PRODUCT_GAPS.md`.

## Regression protection

`backend/tests/test_final_consumer_truth_blockers.py` (4 tests):

* `test_t1_stay_augments_instead_of_erasing_pois`
* `test_t1_stay_sequence_is_ordered_and_gapped`
* `test_t2_closure_on_mutable_poi_is_never_a_noop`
* `test_t2_stable_copy_is_not_generated_for_physical_disruption`
