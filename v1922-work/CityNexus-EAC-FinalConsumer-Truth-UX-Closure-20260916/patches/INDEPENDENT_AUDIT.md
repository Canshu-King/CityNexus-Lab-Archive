# Independent audit — Snapshot I

## Verdict

`BLOCKED_FOR_REAL_USER_TRIAL`

Snapshot I closes the old "Xiamen create + Tianjin demo plan" problem at the backend level,
but the package still overstates several traveler-facing claims.

---

## Genuine gains

- one CN-XIAMEN journey id is used in the backend trace;
- live Xiamen POIs are discovered;
- 3 plan candidates are generated;
- hotel discovery exists for Xiamen;
- a selected stay is persisted;
- Xiamen map coordinates are used;
- raw REQUEST_PLACE_SEARCH is gone;
- a Live recovery surface exists;
- backend truth suites and broad regression show zero new failures;
- no secret-like API key material is packaged.

These are meaningful.

---

## Independent P0: stay selection destroys the sightseeing itinerary

The submitted browser evidence after stay selection shows the Xiamen trip reduced to:

- 厦门高崎国际机场
- Check in · 酒店
- Overnight · 酒店
- Check out · 酒店
- 厦门北站

The earlier real-city POIs are gone.

The submitted `build_candidate_nodes()` in `backend/app/stay_mobility.py` builds activities from:

`city_fixture(journey.city_code).get("activities", [])`

For a real non-fixture Xiamen journey, that fixture activity list is empty.

Therefore the stay materialization path can rebuild a plan around arrival/stay/departure and omit the selected real-city POIs.

This is a severe product-truth regression:

> choosing a hotel must enrich the selected itinerary, not erase the trip.

Required invariant:

selected sightseeing plan
+ selected stay
=
same sightseeing plan with stay/check-in/night/check-out inserted coherently.

The stay workflow must not replace the real-city plan with fixture-only activities.

---

## Independent P0: closure replan accepted a no-op

The package's own trace says:

`proposal-view -> removed=0 added=0`

then:

`accept -> ACCEPTED`

and a new plan id is created.

The disruption target is reported as:

`Check in · 酒店`

The submitted replan code has a generic fallback:

when no affected activity / replacement / delay / removal is resolved,
it appends:

`F0_STABLE_COPY`

That means a CLOSURE/WEATHER event can become an apparently valid "new plan" even when no actual itinerary change was made.

For an actual closure this is not acceptable.

Required:

- mutable POI closure:
  produce a material proposal (replace/remove/move/retime) or explicit NO_ALTERNATIVE;
- protected/locked hotel check-in closure:
  do not silently stable-copy; return a protected-conflict / manual-recovery state;
- unresolved closure target:
  require target clarification / impact resolution;
- never present a no-op stable copy as the solution to a disruption.

A new plan UUID is not proof that the journey changed.

---

## Evidence-integrity issue: "same journey" is not the same as "same visible UI flow"

`SAME_JOURNEY_TRACE.json` does keep one journey_id.

However the critical first stages are recorded as `source=backend` with `ts=n/a`:

- create
- discover
- generate
- select
- start
- stay generation/select
- disruption
- replan
- accept

The browser part begins later.

So the package proves same-journey backend continuity, but does NOT yet prove:

visible create
-> visible AI request
-> visible candidate comparison
-> visible select
-> visible itinerary

all on the same journey.

The final Xiaomi gate must use visible UI for the complete traveler path.
Direct API calls may prepare failure fixtures, but cannot substitute for the user task being accepted.

---

## Copilot remains product-incomplete

The submitted real browser screenshot for `鼓浪屿好玩吗？` still shows:

- 权限边界
- 语义边界
- UNVERIFIED
- UNKNOWN
- NONESEARCH
- What-if Studio / protected explanations

The visible answer is essentially:

"这是一条尚未核实的旅行信息..."

That is honest, but it is not the intended traveler answer.

Copilot should either:

1. actually resolve/search the place and answer usefully, with user actions; or
2. say it cannot verify right now and offer a human action such as "搜索鼓浪屿".

The default traveler view must not expose semantic envelopes or internal authority state.

---

## Hotel compare is technically present but not yet useful

The browser capture shows many hotel cards with:

- identical walking = 22 min
- identical arrival/departure fit = 1% / 1%
- unknown price
- several generic names

This is not yet meaningful hotel comparison.

Unknown price is correctly honest, but the product should distinguish:
- real distance/relationship per property;
- area;
- known provider name/address;
- availability of price;
- why this hotel is recommended.

If metrics are identical because the evaluator is using a shared/default relationship,
fix the ranking/evidence path rather than presenting fake differentiation.

Also reconcile report evidence:
the report says 4 options, while the browser capture shows more properties.
Run acceptance from a clean journey/database state.

---

## Order import still not consumer-grade

The normal UI still asks the traveler for reservation JSON.

That is a developer workbench.

Required:
paste confirmation text / manual form / upload when available
-> parsed preview
-> editable fields
-> explicit confirm
-> booking + commitment.

---

## Activity detail is still missing

No dedicated traveler page exists for:
- opening hours
- duration
- expected cost
- transit
- why recommended
- nearby food
- add/replace
- map.

---

## Visual/product gate still fails

Snapshot I is structurally cleaner than before, but the real screenshots still look much closer to
the old engineering console than to the supplied 10-screen product reference.

Examples:

- Today still starts with generic copy rather than actual Xiamen trip state.
- Trips is sparse/raw instead of a polished trip control center.
- Hotels is a long repeated-card list with weak differentiation.
- Live still exposes transport-mode controls, risk/guardian concepts and diagnostic cards after the recovery surface.
- Copilot still reads like an engineering audit surface.
- large amounts of English remain in Chinese-first flow.

This is not a visual nit. It directly affects whether a normal traveler understands what to do.

---

## Final independent status

`BLOCKED_PENDING_FINAL_CONSUMER_TRUTH_AND_UX_CLOSURE`
