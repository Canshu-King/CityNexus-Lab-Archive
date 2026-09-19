# Independent audit of Snapshot K

## Confirmed real progress

The package is not a duplicate and contains new backend + frontend work.

Confirmed from source/reports/screenshots:
- pinned-calendar rewrite exists;
- CHECK_IN-before-first-STAY regression was added;
- flexible-vs-locked overlap regression was added;
- ambiguous CLOSURE no longer blindly guesses the current activity unless the
  event explicitly asserts it happened at the current location;
- ActivityDetail.tsx exists and is wired from Trips;
- Copilot's always-visible authority/semantic boundary copy was reduced;
- broad backend reports zero new failures;
- frontend build reports green;
- EAC correctly keeps the verdict BLOCKED.

## New truth gap S1 — travel time around pinned boundaries is ignored

In `_reschedule_with_carried()` the free intervals are built between pinned
items, but flexible placement only computes:

`_travel_minutes(previous_flexible, current_flexible)`

The first flexible item has `previous=None`, so it can start exactly at
ARRIVAL.end with zero travel time from the arrival location.

Likewise, the algorithm tests only:

`candidate + duration <= interval_end`

It does not reserve travel from the flexible activity to the *next pinned item*
such as CHECK_IN or a locked/C4 appointment.

It also does not use the preceding pinned node as the travel origin after a
CHECK_IN/STAY/locked window.

Result: a calendar can be non-overlapping yet still physically impossible.

Required:
- every free interval has a left pinned boundary and right pinned boundary;
- first flexible activity must include travel from the left boundary;
- final flexible activity must leave enough travel time to the right boundary;
- when moving into a new interval, travel origin becomes the left pinned node,
  not the last flexible item from a previous interval/day.

## New truth gap S2 — hotel selection can silently collapse a multi-day plan

The scheduler ignores each flexible activity's original date/time and greedily
places activities into the earliest free interval where they fit.

A Day-2 or Day-3 POI can therefore move into Day 1 merely because Day 1 has room.

This violates the user's chosen itinerary semantics.

Hotel selection should not silently transform:

Day 1 / Day 2 / Day 3

into:

all POIs on Day 1 + empty hotel nights.

Required policy:
- preserve original local date and approximate time window by default;
- shift within the same day only as needed;
- cross-day movement is a material itinerary change and must be surfaced as a
  proposal/diff for user acceptance;
- if the selected stay cannot fit without moving activities across days,
  return a stay conflict or a governed adjustment proposal.

## New truth gap S3 — overlapping pinned truths are not rejected

Pinned nodes are sorted and used to compute free intervals, but the function
does not reject pinned-vs-pinned overlap.

Example:
- confirmed activity 12:15–13:00
- hotel CHECK_IN 12:00–12:30

Both remain pinned and can be emitted overlapping.

The current `test_no_structural_operation_overlaps_another()` only checks a
friendly fixture. It does not test a structural node overlapping a locked/C4
activity.

Required:
- validate the pinned calendar before placing flexible activities;
- any overlap among pinned truth returns an explicit conflict;
- do not rely on a later gate to discover an impossible candidate.

## Product truth issue — "nearby suggestions" are not actually nearby

`ActivityDetail` receives:

all other activities in the same active plan

as `nearby`.

No distance calculation is performed.

The UI then says:

"附近的建议"

and:

"来自同一城市的真实地点数据"

This is not evidence of proximity.

Until real spatial distance is computed:
- label the section `行程中的其他地点`, or
- compute distance and only call it nearby when it actually is.

## Product status

Snapshot K still correctly blocks itself:
- consumer booking import missing;
- visible same-Xiamen end-to-end run missing;
- full reference-quality UI missing;
- budget advisory missing;
- live stay+replan acceptance missing.

Independent verdict remains:

`BLOCKED_FOR_REAL_USER_TRIAL`
