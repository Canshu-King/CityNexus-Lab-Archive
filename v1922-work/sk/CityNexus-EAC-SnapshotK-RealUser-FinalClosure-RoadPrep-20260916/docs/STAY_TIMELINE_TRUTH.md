# Stay timeline truth contract

## Scheduling model

Do not solve stay augmentation by:

1. scheduling every carried activity;
2. then appending hotel structural operations.

Instead build one temporal constraint calendar.

Pinned items first:
- ARRIVAL / DEPARTURE
- locked/C4 activities
- required CHECK_IN window/operation
- required CHECK_OUT window/operation
- STAY nights
- required LUGGAGE_DROP

Then schedule flexible activities into remaining free intervals.

## Required invariants

1. ARRIVAL < any city activity.
2. LUGGAGE_DROP, when required, occurs before luggage-dependent sightseeing.
3. CHECK_IN occurs before the first STAY.
4. each STAY occurs while the traveller is checked in.
5. CHECK_OUT occurs after the final STAY.
6. CHECK_OUT occurs before DEPARTURE.
7. locked activity start/end is byte-identical before/after hotel selection.
8. no flexible activity overlaps a locked activity.
9. no structural operation overlaps another pinned operation.
10. if the calendar cannot fit the itinerary:
    return an explicit stay/itinerary conflict.
    Do not delete the POI, move locked truth, or create an impossible timeline.

## Required regressions

- 8 flexible POIs across 3 days + 2 nights:
  CHECK_IN must still precede first STAY.
- flexible 2-hour activity + locked 12:00-13:00:
  flexible activity must be placed entirely before or after.
- impossible locked windows:
  explicit conflict.
- baggage required:
  LUGGAGE_DROP survives and is correctly ordered.
- selected real-city POIs survive hotel selection.
