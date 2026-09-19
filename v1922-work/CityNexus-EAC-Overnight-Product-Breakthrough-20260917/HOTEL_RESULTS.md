# HOTEL_RESULTS.md

## Status: PARTIAL

## Backend behaviour enforced this round

Hotel selection must not rewrite the traveller's trip. The pinned constraint
calendar now guarantees:

* **original duration preserved** - a visit is never silently shortened; an
  impossible same-day fit raises `STAY_ITINERARY_CONFLICT:NO_SAME_DAY_SLOT`;
* **original local date preserved** - Day-2 content cannot be compressed into
  Day 1;
* **pinned reachability** - every consecutive pinned pair must satisfy
  `previous.end + travel <= next.start`, otherwise
  `STAY_PINNED_MOBILITY_CONFLICT`;
* **locked / C4 truth unchanged** - locked nodes keep byte-identical timestamps;
* **CHECK_IN / STAY / CHECK_OUT ordering** validated;
* **superseded property operations dropped** - switching hotel no longer runs the
  previous property's luggage-drop / check-in / night / check-out alongside the
  new one.

Protected by `test_snapshot_k_stay_timeline.py` (8 invariants) and
`test_snapshot_m_truth_edges.py` (7 regressions).

## Not done

* Meaningful differentiation across hotel cards using real data
  (area/address, cancellation, breakfast, itinerary relationship, fit around
  arrival/departure) was not reworked tonight.
* The in-UI hotel selection -> itinerary-day-preservation proof was not captured
  as browser evidence.

## Truth constraints that remain

* OSM carries no rates, so price stays 暂无价格 rather than invented.
* Chinese OSM hotel nodes frequently have no `name` tag, so some cards show a
  generic name plus address.
