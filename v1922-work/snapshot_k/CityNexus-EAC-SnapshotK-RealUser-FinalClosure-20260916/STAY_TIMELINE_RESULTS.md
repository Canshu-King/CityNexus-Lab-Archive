# STAY_TIMELINE_RESULTS.md — pinned temporal-constraint calendar

## The two P0s, reproduced first

`probes/snapshot_k_stay_timeline_probe.py` was run against the authoritative
backend **before** any change:

```
FAIL case_multiday_checkin
  => CHECK_IN occurs after first STAY: 2026-11-07T10:22:00+08:00 vs 2026-11-06T22:00:00+08:00
FAIL case_flexible_locked_overlap
  => flexible activity overlaps locked truth:
     2026-11-06T10:25:00+08:00-12:25 vs 2026-11-06T12:00:00+08:00-13:00
```

Both reproduced exactly as the independent replay reported.

## Why the old approach could not be patched

The previous implementation walked the carried activities forward with a
`cursor` and then appended the stay nodes, with a second `_enforce_sequence`
pass trying to repair the result. Because flexible stops were placed *before*
the structural operations were known, CHECK_IN could be pushed past the first
night, and a flexible stop could be laid straight over a locked window. Adding
more `max()` calls only moves the failure around.

## What replaced it

`_reschedule_with_carried()` is now a **pinned temporal-constraint calendar**
(`docs/STAY_TIMELINE_TRUTH.md`):

1. **Reserve pinned truth first** — ARRIVAL, DEPARTURE, every locked / C4
   activity, LUGGAGE_DROP, CHECK_IN, each STAY night, CHECK_OUT. Their
   timestamps are copied verbatim; nothing is allowed to move them.
2. **Compute the free intervals** between consecutive pinned items inside the
   journey window.
3. **Place flexible activities only inside those intervals**, in order,
   honouring their own duration and the real travel gap from the previous stop
   (the same `_mode_fact` durations the feasibility gate validates).
4. **If an activity cannot fit, raise `StayItineraryConflict`** with the
   offending keys. It never deletes the traveller's stop, never moves locked
   truth, and never emits an impossible timeline.

`build_candidate_nodes()` now returns the calendar output directly. The old
cursor-filtering tail that could silently drop nodes is gone.

## Invariants now enforced structurally

| # | Invariant | Test |
| --- | --- | --- |
| 1 | ARRIVAL before any city activity | `test_check_in_precedes_first_stay_on_multiday_itinerary` |
| 2 | LUGGAGE_DROP before dependent sightseeing | `test_luggage_drop_survives_and_precedes_check_in` |
| 3 | **CHECK_IN before the first STAY** | `test_check_in_precedes_first_stay_on_multiday_itinerary` |
| 4 | each STAY while checked in | same |
| 5 | CHECK_OUT after the final STAY | `test_check_out_follows_last_stay_and_precedes_departure` |
| 6 | CHECK_OUT before DEPARTURE | same |
| 7 | locked start/end byte-identical | `test_locked_activity_timestamp_is_byte_identical` |
| 8 | **no flexible overlap with locked** | `test_flexible_activity_never_overlaps_locked_truth` |
| 9 | no structural overlap | `test_no_structural_operation_overlaps_another` |
| 10 | impossible calendar → explicit conflict | `test_impossible_calendar_raises_explicit_conflict` |
| — | selected POIs all survive | `test_all_selected_pois_survive_a_tight_calendar` |

## Probe result after the fix

```
PASS case_multiday_checkin
PASS case_flexible_locked_overlap
```

## Disruption target truth (tightened)

Snapshot J allowed a target-less `CLOSURE` / `WEATHER` to resolve to
`journey.current_activity_id`. Snapshot K tightens that: **the traveller being
somewhere does not prove that place is the one that closed.**

A target is now used automatically only when the event itself grounds it:

* an explicit `affected_activity_id` / `affected_place_id`, or
* an explicit assertion from the reporter that the disruption is at their
  current position (`payload.at_current_location`).

Anything else returns `REPLAN_TARGET_UNRESOLVED` and writes an audit record
`replan.target_unresolved` with
`policy = "no_guess_current_or_first_activity"`.

### Tests updated for the tightened policy

Four pre-existing tests drove a *started* journey and posted a target-less
CLOSURE, relying on the old implicit behaviour. They now assert
`payload.at_current_location`, which is exactly the grounding a reporter
provides. One further test (`test_aav2_02`) previously asserted that an
AI-only hypothesis could not escalate; it now asserts the stronger property
that an ungrounded retry is refused outright.

These are behaviour corrections, not weakened assertions: every one of them
still fails if the system guesses a target.
