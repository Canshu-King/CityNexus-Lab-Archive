# EAC next task — Snapshot J final real-user closure

Authoritative repository:

D:\moodle\CityNexus

Freeze:

CityNexus-EAC-FinalConsumer-Truth-UX-Closure-20260916(1).zip

as Snapshot J.

Read:

README_FIRST.md
docs/INDEPENDENT_AUDIT.md
docs/BACKEND_TRUTH_GAPS.md
docs/PRODUCT_GAPS.md

Keep using the prior UI reference package.

Do not start unrelated architecture expansion.

==================================================
P0 — FIX STAY STRUCTURAL TRUTH
==================================================

Fix the stay augmentation defect where CHECK_IN / CHECK_OUT / LUGGAGE_DROP are
lost when carried itinerary nodes exist.

Required final sequence contains all applicable structural operations.

Add tests.

==================================================
P0 — PRESERVE LOCKED/C4 ACTIVITY TIME
==================================================

Hotel selection must not retime a carried locked activity.

Flexible activities move around locked truth.

If the hotel schedule is incompatible, return a precise conflict or choose a
different feasible option.

Add locked + C4 regression tests.

==================================================
P0 — FIX REPLAN REASON PATH
==================================================

`heuristic_specs_unresolved_reason` is currently masked by the generic
`NO_DISTINCT_CANDIDATE` fallback.

Make precise unresolved/protected/no-alternative reasons reachable and test the
actual response.

==================================================
P0 — STOP GUESSING AMBIGUOUS CLOSURE TARGETS
==================================================

Do not assign a no-target closure to the current/first activity unless the target
is grounded.

Explicit fixture tests may send affected_activity_id.

Ambiguous real input must become clarification/review-required.

==================================================
P0 — RECOVERY AFTER HOTEL SELECTION
==================================================

Fix the reported mobility identity mismatch.

Acceptance:

real Xiamen plan
-> choose hotel
-> POIs + check-in/out/stays preserved
-> reload
-> close a mutable POI
-> material replan or explicit NO_ALTERNATIVE
-> no mobility identity error

==================================================
P1 — COMPLETE THE CONSUMER PRODUCT
==================================================

Finish the still-open items in PRODUCT_GAPS.md:

- full browser-driven same-Xiamen journey
- consumer booking import
- activity detail
- useful Copilot
- visual product closure
- Chinese-first flow
- budget advisory

The user must not need raw JSON or engineering vocabulary.

==================================================
VISIBLE UI ACCEPTANCE
==================================================

Perform the complete canonical path through visible UI.

Direct API calls may only:
- prepare a disruption fixture,
- inspect final truth.

They may not substitute for:
- create
- choose plan
- choose hotel
- import booking
- accept replan.

Produce:

VISIBLE_UI_TRACE.json

with:
- timestamp
- journey_id
- route
- action
- visible result
- request status
- plan id when relevant.

One Xiamen journey id throughout.

==================================================
VISUAL GATE
==================================================

Use the existing 10-screen reference package materially.

A page does not pass because it rendered.

At minimum produce after screenshots for:

- Today
- Create 1/2/3
- AI intent
- AI progress
- Plan compare
- Trips
- Activity detail
- Hotels
- Booking import preview
- Map
- Copilot
- Live disruption
- Live after accept
- offline/error

390x844
430x932
Xiaomi-like viewport

==================================================
FINAL VERDICT
==================================================

Only:

BLOCKED_FOR_REAL_USER_TRIAL

or

READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

READY requires every P0 above closed and the visible consumer chain completed.

Target:

CityNexus-EAC-SnapshotJ-FinalTrial-Closure-20260916.zip

Stop after packaging.
