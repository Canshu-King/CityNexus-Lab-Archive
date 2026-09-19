# EAC FINAL CONSUMER CLOSURE MISSION

Authoritative repository:

D:\moodle\CityNexus

Freeze Snapshot I:

CityNexus-EAC-RealCity-Product-Closure-20260916.zip

Read:
README_FIRST.md
docs/INDEPENDENT_AUDIT.md
docs/TRUTH_BLOCKERS.md
docs/VISIBLE_UI_ACCEPTANCE.md
docs/VISUAL_PRODUCT_GATE.md

Keep using the prior 10-screen UI reference package.

Do not start V19.3/V20 architecture work.

==================================================
P0 — FIX STAY PLAN DESTRUCTION
==================================================

Selecting a hotel must augment the existing selected Xiamen itinerary.

Do not rebuild real-city activities from `city_fixture()`.

Use the current selected/active plan as the source of truth:
- preserve valid real-city POIs;
- insert check-in/stay/check-out nodes;
- resolve schedule conflicts explicitly;
- preserve C4/arrival/departure;
- show a diff for any movement/removal.

Regression:
real Xiamen plan >=3 POIs
-> select hotel
-> reload
-> same POIs still present
-> stay nodes added
-> gate passes.

==================================================
P0 — FORBID NO-OP DISRUPTION REPLANS
==================================================

Current acceptance trace contains:
CLOSURE
-> proposal removed=0 added=0
-> ACCEPTED

This is not a valid recovery proof.

For CLOSURE/WEATHER:

- unresolved target -> explicit clarification/impact-unresolved state
- protected target -> protected conflict/manual recovery
- mutable target -> material proposal
- no feasible material repair -> NO_ALTERNATIVE

Do NOT generate/present F0_STABLE_COPY as the successful recovery for an unresolved closure.

Add tests.

Acceptance run:
close a real mutable Xiamen POI.
Proposal must contain an actual material diff.
Accept through visible UI.

Separately test protected hotel/check-in closure and verify the product does NOT fake a repair.

==================================================
P0 — FULL VISIBLE UI SAME-JOURNEY RUN
==================================================

The previous same-journey proof was backend-heavy.

Now complete docs/VISIBLE_UI_ACCEPTANCE.md exactly.

Critical actions must be performed in the visible browser:
- create
- AI planning request
- candidate compare
- choose plan
- choose hotel
- import booking
- Copilot
- accept replan

Produce VISIBLE_UI_TRACE.json.

==================================================
P1 — CONSUMER ORDER IMPORT
==================================================

Replace the normal JSON box with:

- paste confirmation text
- manual form
- upload/screenshot when supported
- parsed preview
- editable fields
- explicit confirm

Raw JSON goes to Advanced/Developer only.

==================================================
P1 — ACTIVITY DETAIL
==================================================

Implement the dedicated traveler activity detail page.

Use reference 08:
- title/place
- opening hours
- duration
- cost
- transit
- why recommended
- nearby suggestions
- map
- add/replace.

No invented provider facts.

==================================================
P1 — COPILOT PRODUCT CLEANUP
==================================================

Default Copilot traveler view must not show:
- authority boundary
- semantic boundary
- UNVERIFIED
- UNKNOWN
- NONESEARCH
- What-if Studio/internal policy wording.

For `鼓浪屿好玩吗？`:
- use live DeepSeek/provider path when available;
- answer in useful Chinese with current-trip context;
- show human actions such as 搜索/加入行程/地图查看;
- if not verifiable, say so simply and offer the next action.

Internal semantic envelope may live behind Advanced details only.

==================================================
P1 — HOTEL COMPARISON QUALITY
==================================================

Fix any reason all hotel metrics are identical.

On a clean acceptance run:
- counts reconcile;
- cards correspond to unique provider identities;
- distance/relationship is property-specific;
- unknown price remains honest;
- generic names include useful address/area when available.

Do not fake prices.

==================================================
P1 — VISUAL PRODUCT PASS
==================================================

Materially implement the reference UI system.

Prioritize:
- Today
- Trips
- Copilot
- Hotels
- Live
- create wizard.

Move diagnostics/engineering controls behind Advanced.

Canonical screenshots must be Chinese-first.

==================================================
TESTS
==================================================

Run:
- existing V19.2–V19.2.5 truth suites
- new stay-preservation tests
- new no-op-replan tests
- broad backend regression
- frontend build
- mobile E2E 390x844 / 430x932 / Xiaomi-like viewport

No new backend regression.

==================================================
FINAL VERDICT
==================================================

Only:
BLOCKED_FOR_REAL_USER_TRIAL
or
READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

READY requires:
- same Xiamen journey visible UI chain
- stay does not erase POIs
- material disruption replan
- consumer booking import
- activity detail
- useful Copilot answer
- visual/product gate acceptable

Target:
CityNexus-EAC-FinalConsumer-Truth-UX-Closure-20260916.zip

Stop after packaging.
