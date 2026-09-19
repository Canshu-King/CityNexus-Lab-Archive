# BUGS_FOUND_AND_FIXED.md

## Snapshot M truth edges

### M1 — hotel selection silently shortened a traveller's activity

* **Observed**: probe reported
  `hotel selection silently shortened activity from 2:00:00 to 1:00:00`.
* **Root cause**: Calendar V2 shortened a visit to fit a same-day window, which
  treats duration as disposable. The contract is that flexible means movable in
  time, not in duration.
* **Fix**: the original duration is preserved; an impossible same-day fit raises
  `STAY_ITINERARY_CONFLICT:NO_SAME_DAY_SLOT`.
* **Regression**: `test_120_minute_activity_with_only_20_minute_window_is_a_conflict`.

### M2 — pinned truth was not checked for reachability

* **Observed**: probe reported
  `pinned nodes were accepted despite only 10 minutes gap for 30 minutes travel`.
* **Root cause**: pinned validation only checked overlap, never whether the leg
  was actually possible.
* **Fix**: every consecutive pinned pair must satisfy
  `previous.end + travel(previous, next) <= next.start`, otherwise
  `STAY_PINNED_MOBILITY_CONFLICT`. Two operations at the same property cost no
  travel.
* **Regression**: `test_pinned_nodes_ten_minutes_apart_with_thirty_minutes_travel_conflict`.

### M3 — luggage drop used a hard-coded optimistic time

* **Observed**: adding M2 made the Tianjin flagship fail with
  `STAY_PINNED_MOBILITY_CONFLICT:luggage-drop`.
* **Root cause**: `drop_at = arrival_at + 60 minutes` ignored the real inbound
  leg, so the drop could be scheduled before the traveller could arrive.
* **Fix**: the drop time is derived from the actual inbound travel time.

### M4 — reachability used WALK only

* **Observed**: the same fixture then failed on `CHECK_OUT -> DEPARTURE` with a
  170-minute walking estimate.
* **Root cause**: `_travel_minutes` hard-coded the WALK profile, so a
  hotel-to-airport leg looked impossible.
* **Fix**: the fastest feasible mode is used — what a traveller actually does —
  while genuinely unreachable pinned truth is still refused.

### M5 — superseded hotel operations ran alongside the new hotel's

* **Observed**: `PINNED_OVERLAP:luggage-drop` where two different properties'
  luggage drops sat at the same clock time.
* **Root cause**: carried structural operations from the previous property were
  not filtered when the traveller switched hotel.
* **Fix**: `_offer_of()` extracts the property from a structural key, and
  operations belonging to a superseded property are dropped.

### M6 — Activity Detail could show no coordinates

* **Observed**: a plan materialised without coordinates in the activity metadata
  produced 暂无坐标 even though the Place row had coordinates.
* **Fix**: `activity_schema()` / `plan_schema()` resolve the Place row and merge
  `latitude`, `longitude`, `crs`, `category` and `opening_hours`.
* **Regression**: `test_real_place_coordinates_survive_into_the_plan_payload`.

## Consumer product

### P1 — the golden path asked travellers for raw reservation JSON

* **Observed**: Trips → 预订 rendered the structured-JSON workbench.
* **Fix**: the consumer flow (paste / manual form / preview / confirm) is now
  primary; raw JSON moved behind a 高级 / 开发者 disclosure.

### P2 — manual booking submit never produced a draft

* **Observed**: the manual form posted successfully but no preview appeared.
* **Root cause**: `/inbox/import` returns the draft at the **top level**, while
  the component read `result.draft`.
* **Fix**: the top-level draft is used.
* **Verified**: `preview-draft shown`, 0 browser errors.

## Regressions avoided (found and fixed during the night)

* Four existing fixtures failed when pinned reachability was introduced. Two
  were **real defects** (M4, M5); the rest needed a deterministic transition cost
  for co-located fixture coordinates so those tests assert structural invariants
  rather than distance heuristics. The reachability rule stayed fully active.
* A debug print inserted while diagnosing M4 broke the module with an
  `IndentationError`; it was removed and the module re-parsed before continuing.
