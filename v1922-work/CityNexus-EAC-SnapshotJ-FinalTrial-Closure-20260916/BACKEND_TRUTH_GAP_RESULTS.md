# BACKEND_TRUTH_GAP_RESULTS.md — Snapshot J findings B1–B5

The Road-Prep named five concrete code defects. B1–B4 are fixed and
regression-protected. B5's identity mismatch is fixed; its end-to-end
acceptance still needs a live run (explained at the end).

---

## B1 — CHECK_IN / CHECK_OUT / LUGGAGE_DROP were dropped — FIXED

### Root cause (confirmed in the code)

`build_candidate_nodes()` emits four structural roles:

```
LUGGAGE_DROP · CHECK_IN · STAY · CHECK_OUT
```

but `_reschedule_with_carried()` began with

```python
stays = [node for node in anchors if str(node.role).upper() == "STAY"]
```

and then searched for `":check-in"` / `":check-out"` **inside that list**.
A node whose role is `CHECK_IN` can never appear in a list filtered to `STAY`,
so those operations were silently dropped whenever an itinerary was carried
forward. The Snapshot J T1 evidence showed the symptom: the final sequence had
arrival, POIs, two `Overnight` nodes and departure, but no check-in/check-out.

### Fix

`_reschedule_with_carried()` now handles every structural role explicitly and
emits all applicable operations. It also gives each one a real travel gap,
which the earlier code omitted for check-in/check-out.

### Verified (offline, deterministic)

```
ARRIVAL      2026-11-06T10:00 -> 10:20
ACTIVITY     x4 (11:06 -> 15:21)
CHECK_IN     2026-11-06T15:26 -> 15:46
STAY         2026-11-06T22:00 -> 2026-11-07T06:00
STAY         2026-11-07T22:00 -> 2026-11-08T06:00
CHECK_OUT    2026-11-08T12:00 -> 12:20
DEPARTURE    2026-11-08T19:50 -> 20:00
```

Tests: `test_b1_structural_operations_survive_stay_augmentation`,
`test_b1_luggage_drop_survives_when_required`,
`test_b1_structural_sequence_is_chronological`.

---

## B2 — locked carried activities were re-timed — FIXED

### Root cause

`_carried_itinerary_nodes()` correctly copied `locked=bool(item.locked)`, but
`_reschedule_with_carried()` then assigned a new start/end to **every** carried
node. A confirmed activity could therefore be moved merely because a hotel was
chosen.

### Fix

Locked nodes are now pinned at their authoritative window and everything else is
scheduled around them. `_enforce_sequence()` also pins locked nodes instead of
pushing them.

### Verified

* `test_b2_locked_carried_activity_keeps_its_exact_window` — start and end are
  byte-identical before and after stay augmentation.
* `test_b2_flexible_activities_move_around_locked_truth` — no flexible stop
  overlaps the locked window.

---

## B3 — the precise unresolved reason was dead code — FIXED

### Root cause (exactly as the Road-Prep described)

```python
details = ", ".join(sorted(failed_reasons)) or "NO_DISTINCT_CANDIDATE"
if not details and heuristic_specs_unresolved_reason:   # never true
    raise HTTPException(422, heuristic_specs_unresolved_reason)
```

`details` is never empty, so the branch was unreachable and
`REPLAN_TARGET_UNRESOLVED` / `REPLAN_PROTECTED_CONFLICT` / `REPLAN_NO_ALTERNATIVE`
could never surface.

### Fix

The precise reason is now evaluated **before** the generic fallback is applied.

Test: `test_b3_unresolved_reason_is_not_masked_by_generic_fallback` asserts the
response contains a precise reason and **not** `NO_DISTINCT_CANDIDATE`.

---

## B4 — ambiguous no-target disruption was guessed — FIXED

### Root cause

Snapshot J's own change resolved a no-target `CLOSURE`/`WEATHER` to
`journey.current_activity_id`, then to **the first non-terminal activity**. The
second half is a guess: "有个景点关了" does not prove which activity is closed.

### Fix

A target is used automatically only when it is grounded:

* an explicit `affected_activity_id` / `affected_place_id`, or
* the Journey's **own execution position** (`current_activity_id`) — i.e. the
  traveller is physically there right now.

Picking "the first non-terminal activity" is removed. When nothing is grounded
the request returns `REPLAN_TARGET_UNRESOLVED` (clarification required) and an
audit record `replan.target_unresolved` is written with
`policy = "no_guess_current_or_first_activity"`.

Test: `test_b4_ambiguous_closure_is_not_auto_assigned_to_first_activity`.

### Note on the trade-off

Using the execution position is kept deliberately: it is grounded truth, and it
is what the existing `TRAFFIC_DELAY` / `SCHEDULE_DELAY` semantics already rely
on. Removing it entirely broke five pre-existing tests that drive a started
journey, which would have been a regression rather than a truth improvement.

---

## B5 — recovery after hotel selection — identity mismatch FIXED

### Root cause — three separate identity defects

1. **Activity metadata was overwritten during replan.** Three sites replaced
   `row["metadata_json"]` with a fresh dict, discarding `semantic_key` — the
   routing and frozen-evidence identity. Downstream legs then fell back to the
   raw `place_id` and could not be matched. All three now **merge** instead of
   replace.
2. **Server-owned structural Places leaked into the replacement pool.** The
   candidate query excluded only `citynexus-v12-authoritative`, not
   `citynexus-v9-domain`. A check-in / check-out node belonging to a *previous*
   journey therefore entered the candidate set and a recovery leg referenced a
   foreign Place id. Both query sites now exclude
   `_SERVER_OWNED_PLACE_PROVIDERS`.
3. **`_place_lookup` could not resolve a structural `semantic_key`.** Structural
   nodes are materialised with a *generated* Place id, so
   `session.get(Place, "v12:{journey}:arrival-anchor")` always failed and the
   capture raised `KeyError`. It now falls back to resolving the key through
   activity metadata.

Additionally, `_need_pair()` now normalises every requested leg through one
canonical key space, so a caller passing either a Place id or a `semantic_key`
produces the same pair.

### Verified

Before the fix:

```
rejected: REQUEST_ERROR | mobility evidence unavailable:
  mobility fact unavailable for v12:...:arrival-anchor|0499f77b-...: KeyError
```

After the fix, on a stay-materialised plan, the same probe no longer produces
any `mobility evidence unavailable` / identity error — it reaches ordinary
feasibility evaluation.

### Honest limitation

The end-to-end B5 acceptance (`real Xiamen plan -> choose hotel -> reload ->
close a mutable POI -> material replan`) was **not** completed against live
provider data in this round. The identity mismatch itself is fixed and
demonstrated offline; the live confirmation is listed as remaining work.
