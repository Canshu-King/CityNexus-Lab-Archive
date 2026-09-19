# EAC Final Task — Snapshot K

Authoritative repository:

D:\moodle\CityNexus

Freeze the submitted result as Snapshot K candidate.

Read:

README_FIRST.md
docs/INDEPENDENT_AUDIT.md
docs/STAY_TIMELINE_TRUTH.md
docs/REAL_USER_PRODUCT_GATE.md

Run the supplied stay-timeline probe first.

Do NOT start unrelated architecture work.

==================================================
P0 — REPLACE SEQUENTIAL STAY AUGMENTATION WITH A CONSTRAINT CALENDAR
==================================================

The current algorithm can:

- check in after the first overnight;
- overlap a flexible activity with locked truth.

Fix the scheduling model.

Pinned temporal facts must be reserved first:

- ARRIVAL / DEPARTURE
- locked/C4 activities
- CHECK_IN / CHECK_OUT
- STAY nights
- required LUGGAGE_DROP

Then place flexible activities into real free windows.

Do not merely add more `max(cursor, ...)` clauses.

Required tests are in STAY_TIMELINE_TRUTH.md.

==================================================
P0 — PHYSICAL DISRUPTION TARGETS MUST BE GROUNDED
==================================================

For CLOSURE / WEATHER:

Do not silently infer the target solely from `journey.current_activity_id`.

Current position may be offered as a clarification candidate, but the affected
target used for automatic replan requires:

- explicit activity/place id; or
- provider-linked entity; or
- high-confidence semantic resolution.

Update old fixture tests to specify a target where the test means a targeted
closure.

Ambiguous input:
-> clarification/review state.

==================================================
P0 — PROVE STAY + RECOVERY
==================================================

Complete:

real Xiamen plan
-> choose hotel
-> reload
-> confirm POIs + check-in/out/stays + locked truth
-> close an explicitly targeted mutable Xiamen POI
-> material replan OR honest NO_ALTERNATIVE
-> no mobility identity error

==================================================
P1 — PROXY POLICY
==================================================

Do not hardcode public discovery to ignore all environment proxy settings.

Make proxy trust/provider routing configurable.

The product must work both:
- direct-network environment;
- user environment requiring proxy.

Never print credentials/proxy secrets.

==================================================
P1 — NOW FINISH THE PRODUCT
==================================================

No more backend-only package after these P0 fixes.

Implement the still-open consumer tasks:

- consumer booking import
- activity detail
- useful Copilot traveler answer
- material reference-UI implementation
- Chinese-first core journey
- full visible same-Xiamen browser run

Use the existing 10-screen reference package.

==================================================
FINAL VISIBLE ACCEPTANCE
==================================================

One fresh Xiamen journey through UI:

create
-> AI request
-> real candidate plans
-> choose
-> itinerary
-> activity detail
-> hotel compare/select
-> prove itinerary survives
-> booking import
-> Copilot
-> map
-> start/live
-> explicit mutable-POI closure fixture
-> material replan
-> accept in UI
-> final truth consistent

Produce:

VISIBLE_UI_TRACE.json

and after screenshots.

==================================================
FINAL VERDICT
==================================================

Only:

BLOCKED_FOR_REAL_USER_TRIAL

or

READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

Target package:

CityNexus-EAC-SnapshotK-RealUser-FinalClosure-20260916.zip
