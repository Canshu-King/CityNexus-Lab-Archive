# C4_TEMPORAL_RESULTS.md — C4 temporal boundaries (P0-1, T01–T05)

## Required invariant

* a confirmed ARRIVAL is a **lower** boundary for city activity;
* a confirmed DEPARTURE is an **upper** boundary for city activity;
* MID_TRIP is an interior exact/pinned commitment;
* multiple anchors must be chronologically consistent and routable;
* travel time to and from anchors is respected;
* optional POIs outside the usable interval are removed/re-timed;
* impossible anchor sets return a precise conflict.

## Defect reproduced against Snapshot E

Direct execution of `schedule_template_with_anchors()` on the submitted
V19.2.2 source produced, before the fix:

```
ARRIVAL 12:30
  POI1     09:00-10:15
  POI2     10:30-11:45
  ARRIVAL  12:30-12:50
  POI3     13:20-14:40
```

```
DEPARTURE 15:30
  POI1       09:00-10:15
  POI2       13:20-14:40
  DEPARTURE  15:10-15:30
  POI3       15:50-16:50
  POI4       17:10-18:40
```

The anchors were inserted as points, not enforced as boundaries.

## Implementation

`app/planning/anchor_schedule.py`:

* `_anchor_windows()` — the exact span each anchor occupies (DEPARTURE is
  anchored on its END, everything else on its START).
* `validate_anchor_timeline()` — returns a precise reason or `None`:
  `C4_ANCHOR_OUTSIDE_JOURNEY:<key>`, `C4_ANCHOR_OVERLAP:<a>|<b>`,
  `C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE:<a>|<b>`.
* `usable_city_interval()` — `[max(arrival end), min(departure start)]`.
* `schedule_template_with_anchors()` — packs flexible POIs into the gaps
  before each anchor with real frozen travel time, then only up to the usable
  end. A POI that cannot fit is dropped; the function returns `None` when the
  anchors themselves are inconsistent.

`app/services.py::_anchor_block_reason()` now prefers the precise structural
reason over a generic blocked list, so an impossible reservation reports
`C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE:...` rather than an anonymous sentence.

## Verified behaviour

| ID | Case | Result |
| --- | --- | --- |
| T01 | journey 09:00–19:00, ARRIVAL 12:30 | **no** flexible activity starts before the arrival anchor completes |
| T02 | journey 09:00–19:00, DEPARTURE 15:30 | **no** flexible activity ends after the departure anchor begins |
| T03/T04 | ARRIVAL 10:00 + MID_TRIP 13:00 + DEPARTURE 17:00 | monotonic ordering, all activity inside the usable interval, chronologically sorted |
| T05 | ARRIVAL 18:00 after DEPARTURE 10:00 | 422 with `C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE`, **no plan persisted** |

Example after the fix (ARRIVAL 12:30):

```
ARRIVAL  12:30-12:50
POI      13:10-14:25
POI      14:40-15:55
POI      16:10-17:10
POI      17:25-18:25
```

Example after the fix (DEPARTURE 15:30):

```
POI        09:00-10:15
POI        10:30-11:45
POI        12:00-13:00
POI        13:20-14:40
DEPARTURE  15:10-15:30
```

## Evidence

* `tests/test_v1923_final_code_gate.py` — T01/T02/T03/T05 assert **actual ordered
  timestamps**, not a non-empty plan count.
* `evidence/mobile_v1923_d.json` — `ARRIVAL_BOUNDARY` and `DEPARTURE_BOUNDARY`
  flows for both mandated viewports.
* `evidence/v1923_gate_run.txt` — 74 passed.

## Not weakened

`LOCKED_COMMITMENT` still hard-fails any candidate that does not contain the
committed anchor. The change makes the constraint satisfiable *and* temporally
coherent; it does not relax it.
