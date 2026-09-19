# LIVE_REPLAN_RESULTS.md

## Status: PARTIAL

## Backend truth enforced (earlier rounds, retained)

* A `CLOSURE` / `WEATHER` event must have an **explicitly grounded** target.
  `journey.current_activity_id` alone is not proof; the event must carry an
  explicit activity/place id or assert `payload.at_current_location`.
  Otherwise the request returns `REPLAN_TARGET_UNRESOLVED` and writes an audit
  record with `policy = "no_guess_current_or_first_activity"`.
* `F0_STABLE_COPY` is never generated for a physical disruption, so a closure can
  no longer settle as an accepted no-op.
* Mobility identity is aligned end to end (activity metadata is merged not
  replaced; server-owned structural Places are excluded from the replacement
  pool; structural `semantic_key` resolves through activity metadata).

## Not done tonight

* The **traveller-first Live viewport** rework (now / next stop / route /
  disruption / affected / unchanged / proposed change / actions) with
  engineering diagnostics moved behind Advanced.
* The browser-driven **accept through UI** step and the final Trips/Live/backend
  agreement check.

## Previously verified (offline, deterministic)

* CLOSURE on a mutable real POI produced a material proposal (`removed=1`,
  status `PRESENTED`).
* CLOSURE on a protected stay node returned an explicit refusal
  (`closed activity is protected and cannot be replaced automatically`).
* No CLOSURE/WEATHER event settled as an accepted no-op.
