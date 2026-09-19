# Backend truth gaps found in Snapshot J

## B1 — CHECK_IN / CHECK_OUT / LUGGAGE_DROP are dropped during stay augmentation

This is a concrete code defect.

`build_candidate_nodes()` creates structural nodes with roles:

- `LUGGAGE_DROP`
- `CHECK_IN`
- `STAY`
- `CHECK_OUT`

But `_reschedule_with_carried()` starts with:

```python
stays = [node for node in anchors if str(node.role).upper() == "STAY"]
```

and later searches:

```python
check_in_nodes = [n for n in stays if ":check-in" in str(n.key)]
check_out_nodes = [n for n in stays if ":check-out" in str(n.key)]
```

Those lists can never contain nodes whose role is `CHECK_IN` or `CHECK_OUT`.

The output of `_reschedule_with_carried()` only includes:

- arrival
- rescheduled carried activities
- `new_stays`
- departure

Therefore CHECK_IN, CHECK_OUT and LUGGAGE_DROP can disappear when an existing
itinerary is carried forward.

The submitted T1 evidence itself shows this symptom:

before hotel:
real POIs

after hotel:
arrival
POIs
Overnight
POIs
Overnight
departure

There is no explicit check-in or check-out in that final sequence.

### Required fix

Preserve every structural stay operation explicitly:

- LUGGAGE_DROP when required
- CHECK_IN
- each STAY/NIGHT
- CHECK_OUT

Do not classify all of them as `STAY`.

Add regression assertions that the final materialised plan contains the required
operations and that their temporal order is valid.

---

## B2 — locked carried activities are still re-timed

`_carried_itinerary_nodes()` correctly copies:

```python
locked=bool(item.locked)
```

But `_reschedule_with_carried()` then computes a new start/end for every carried
activity without special handling for `node.locked`.

That means a locked/confirmed activity can be moved merely because the user
selected a hotel.

Even if the final feasibility gate catches some C4 violations, the planner
should not first mutate locked truth and then hope a downstream gate rejects it.

### Required invariant

For carried `locked=True` activities:

- preserve authoritative start/end;
- schedule flexible activities around them;
- if hotel/check-in creates a conflict:
  - choose another hotel schedule,
  - move only flexible activities,
  - or report an explicit conflict.

Never silently move the locked item.

Add tests:
- locked POI + hotel selection keeps exact time;
- C4/confirmed activity + hotel selection keeps commitment;
- impossible hotel + locked activity returns explicit conflict rather than
  moving the commitment.

---

## B3 — explicit unresolved replan reason is currently dead code

Snapshot J adds:

```python
heuristic_specs_unresolved_reason = ...
```

and later:

```python
details = ", ".join(sorted(failed_reasons)) or "NO_DISTINCT_CANDIDATE"
if not details and heuristic_specs_unresolved_reason:
    raise HTTPException(422, heuristic_specs_unresolved_reason)
```

But `details` is always non-empty because it falls back to
`"NO_DISTINCT_CANDIDATE"`.

Therefore that `if not details` branch is unreachable.

The intended precise errors:

- `REPLAN_TARGET_UNRESOLVED`
- `REPLAN_PROTECTED_CONFLICT`
- `REPLAN_NO_ALTERNATIVE`

are not guaranteed to surface through this path.

### Required fix

Check `heuristic_specs_unresolved_reason` before assigning the generic fallback,
or otherwise return a structured reason directly.

Add exact-response tests.

---

## B4 — no-target physical disruption is guessed, not clarified

For CLOSURE/WEATHER with no resolved target, Snapshot J now falls back to:

1. `journey.current_activity_id`
2. otherwise the first non-terminal non-anchor activity.

That is convenient for a test, but unsafe as a general product truth policy.

A user/provider statement like:

> “有个景点关了”

does not prove which activity is closed.

### Required policy

Use a target automatically only when it is actually grounded by:
- explicit affected activity/place id;
- trusted provider linkage;
- high-confidence semantic target resolution.

If ambiguous:
- ask for clarification / review;
- do not silently choose the current or first activity.

A dedicated explicit UI test fixture may specify the target id.

---

## B5 — stay-materialised plans still cannot recover from a POI closure

The package itself reports:

> CLOSURE on a POI inside a stay-materialised plan is refused with
> `mobility evidence unavailable`.

This should be treated as a blocker for the real travel trial, because the
normal user path is:

choose itinerary
-> choose hotel
-> start trip
-> disruption

The system must recover on the actual stay-enriched plan, not only on the
pre-hotel plan.

### Required fix

Align:
- semantic activity identity;
- frozen mobility evidence;
- stay-inserted nodes;
- recovery route keys.

Then prove:

selected Xiamen plan
-> select stay
-> reload
-> close a mutable POI
-> material replan / explicit NO_ALTERNATIVE

No `mobility evidence unavailable` identity mismatch.
