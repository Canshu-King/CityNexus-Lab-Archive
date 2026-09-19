# Stay Calendar V2 contract

The current pinned calendar is directionally correct, but "no overlap" is not
enough. A travel itinerary also needs transition time and day semantics.

## Pinned truth

Reserve first:
- ARRIVAL / DEPARTURE
- locked/C4 activities
- LUGGAGE_DROP
- CHECK_IN
- STAY
- CHECK_OUT

Validate all pinned intervals:
- sorted;
- inside journey window;
- no overlap;
- correct check-in/stay/check-out ordering.

If pinned truth conflicts:
`STAY_PINNED_CONFLICT`
or another precise product contract.

## Flexible placement

For each original flexible activity:

1. preserve its local date unless the user accepts a cross-day change;
2. preserve its approximate day order/window where feasible;
3. find a free slot on that date;
4. include travel from the actual previous node;
5. include travel to the next pinned boundary;
6. never overlap pinned/locked truth.

A free interval should conceptually contain:

left_boundary_node
available_time
right_boundary_node

not just `[start, end]`.

Feasibility condition:

`start >= left.end + travel(left, activity)`

and

`activity.end + travel(activity, right) <= right.start`

for the first/last activity adjacent to pinned boundaries.

For multiple flexible stops inside one interval, enforce every leg.

## Cross-day change policy

Hotel selection is not permission to rewrite the user's daily itinerary.

If a hotel makes the original day impossible:
- try another feasible same-day placement;
- otherwise report a visible conflict;
- or create a governed proposed adjustment requiring user acceptance.

Never silently move Day-2 content to Day 1.

## Required regressions

1. first activity after ARRIVAL includes inbound travel.
2. last activity before CHECK_IN leaves outbound travel.
3. activity after CHECK_IN uses hotel/check-in as travel origin.
4. locked activity overlapping CHECK_IN -> explicit conflict.
5. Day-2 POI remains Day 2 after hotel selection.
6. Day-3 POI remains Day 3 after hotel selection.
7. impossible same-day fit -> explicit conflict/proposal, not silent cross-day move.
8. all existing Snapshot K timeline tests remain green.
