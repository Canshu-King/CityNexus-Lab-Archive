# Scheduler Truth V3

## Hard rule 1 — never silently shorten a traveller-selected activity

Flexible means movable in time, not disposable in duration.

Default contract:
- preserve original duration;
- preserve original local date;
- preserve sequence/order intent where feasible.

If a hotel structural window makes that impossible:
- return a precise conflict; or
- create an explicit proposed adjustment/diff for user confirmation.

Do not silently shrink a visit to 15 minutes.

## Hard rule 2 — pinned truth must be reachable, not merely non-overlapping

For every consecutive pinned node pair:

`previous.end + minimum_valid_travel(previous, next) <= next.start`

must hold.

Pinned nodes include:
- ARRIVAL
- DEPARTURE
- locked/C4 activity
- LUGGAGE_DROP
- CHECK_IN
- STAY where relevant to actual movement
- CHECK_OUT

If not reachable:
- `STAY_PINNED_MOBILITY_CONFLICT`
- option is not hard-constraint safe.

## Hard rule 3 — stay option status must reflect schedule truth

Do not set `hard_constraints_passed=True` based only on final departure margin.

The status must include:
- pinned interval validity;
- pinned travel reachability;
- flexible placement success;
- preserved locked/C4 truth;
- preserved activity duration unless an accepted proposal says otherwise.

## Permanent regression tests

Move the packaged probe cases into authoritative tests and add:

1. original 120-minute activity gets only 20-minute free window:
   conflict, not silent truncation.
2. known pinned nodes 10 minutes apart but 30 minutes travel:
   conflict.
3. known-free attraction remains `0 CNY / FREE_KNOWN`, not unknown.
4. real Place coordinates survive into the active-plan/activity-detail payload.
