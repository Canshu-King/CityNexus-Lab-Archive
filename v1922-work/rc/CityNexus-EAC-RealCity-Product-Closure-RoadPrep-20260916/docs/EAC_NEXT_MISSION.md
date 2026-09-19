# EAC NEXT MISSION — REAL-CITY PRODUCT CLOSURE

Authoritative repository:

D:\moodle\CityNexus

Freeze the previous result as Snapshot H:

CityNexus-EAC-Overnight-Mobile-Product-Rescue-V2-20260916.zip

Read:

README_FIRST.md
docs/INDEPENDENT_AUDIT.md
docs/SAME_JOURNEY_PROOF.md
docs/UI_CLOSURE_SPEC.md

Also keep using the prior 10-screen UI reference package:

CityNexus-EAC-Overnight-Mobile-Product-Rescue-V2-UIReference-20260916.zip

Do not start broad new backend architecture.

The mission is to convert the structural rescue into one real-city consumer
workflow.

==================================================
P0 — ONE XIA MEN JOURNEY, END TO END
==================================================

The previous package mixed:
- Xiamen create-flow evidence
with
- sealed Tianjin plan-generation evidence.

That is not an acceptable end-to-end proof.

Create one Xiamen journey through visible UI and keep the SAME journey_id from
creation through replan.

Do not use /demo/reset for the acceptance run.

Create SAME_JOURNEY_TRACE.json.

At every stage record:
journey_id
city_code
plan id
route
action
status/result

If live DeepSeek/provider credentials are already configured in the user's
environment, use them without printing or persisting secrets.

If they are unavailable, do not claim READY.

==================================================
P0 — REAL XIA MEN PLANNING
==================================================

For the newly-created Xiamen journey:

natural language
-> semantic interpretation
-> Xiamen place/provider retrieval
-> candidate composition
-> feasibility
-> plan persistence
-> compare
-> select

The visible plan must contain Xiamen places.

No Old Town Gate / Riverside Museum / Nexus City evidence may be used to pass
the Xiamen gate.

If real provider resolution is missing, implement/fix the integration path
rather than falling back to Tianjin.

==================================================
P1 — HOTEL COMPARE/SELECT
==================================================

Implement the actual consumer hotel flow.

Show only provider-backed facts where available:
- name
- area
- price
- cancellation/breakfast if known
- distance/travel relationship to itinerary
- reason recommended

Select hotel
-> authoritative Journey/stay selection updates
-> Trip view reflects the selected stay

Do not mark PASS because a Stay Explorer route exists.

==================================================
P1 — LIVE DISRUPTION -> GOVERNED REPLAN
==================================================

Drive a real test event through the existing Event/ReplanProposal architecture.

Visible traveler flow:

发生了什么
-> 哪些活动受影响
-> 哪些已确认事项不变
-> 推荐的新顺序/替代方案
-> 接受新方案 / 仅调整今天 / 稍后提醒

After accept:
- correct plan/replan state persists
- recovery state is consistent
- protected commitments remain protected

This must be driven end to end.

==================================================
P1 — ACTIVITY DETAIL
==================================================

Create a real activity-detail screen with:
- place
- hours if known
- duration
- cost if known
- transit
- why recommended
- add/replace
- map
- nearby suggestions where backed by data

==================================================
P1 — ORDER IMPORT
==================================================

Move raw Reservation JSON out of the ordinary Trips experience.

Consumer flow:
- upload screenshot if supported
- paste confirmation text
- manual entry
- parsed preview
- user confirmation
- create booking/commitment

Never create a commitment from uncertain extraction without confirmation.

Raw JSON remains only under Advanced/Developer tools.

==================================================
P1 — REBUILD TRIPS IA
==================================================

Do not concatenate the entire product into one scrolling document.

Refactor Trips into a mobile product structure:
- itinerary
- bookings
- stay
- spend
- travel documents / companions if available

Use tabs/cards/subroutes.

The default Trips screen must be useful within one phone screen before scroll.

==================================================
P1 — VISUAL IMPLEMENTATION
==================================================

Snapshot H mostly reused the old console styling.

Now implement the prior UI reference direction materially.

Acceptance screenshots should visibly resemble the reference system:
- hierarchy
- spacing
- cards
- touch controls
- sticky actions
- compact information density
- Chinese traveler copy

Do not pixel-copy fabricated values.
Do not use browser-default raw controls as the primary visual system.

==================================================
P1 — CHINESE-FIRST PRODUCT ACCEPTANCE
==================================================

Run the entire canonical acceptance journey in Chinese.

Language switch:
中文 -> EN -> 中文

must preserve state.

Default traveler surfaces may not expose:
provider evidence
deterministic gate
authority envelope
Twin context
PlanVersion
C4

Those may remain in Advanced/Developer routes.

==================================================
P1 — BUDGET SANITY
==================================================

If trip duration / party size / budget appears extremely constrained,
show an advisory warning.

Example:
39 days / 2 people / CNY 3000

Do not silently treat that as a normal comfortable budget.

Allow the traveler to:
- adjust budget
- continue intentionally

==================================================
FINAL ACCEPTANCE
==================================================

A READY verdict requires the same Xiamen journey to complete:

create
-> AI
-> real Xiamen candidates
-> compare
-> choose
-> itinerary
-> activity detail
-> Xiamen map
-> hotel compare/select
-> booking import/confirm
-> live
-> disruption
-> governed replan
-> accept
-> consistent final state

No demo journey substitution.

Also run:
- backend focused truth suites
- broad regression
- frontend build
- relevant E2E
- 390x844
- 430x932
- Xiaomi-like viewport

Final verdict:

BLOCKED_FOR_REAL_USER_TRIAL

or

READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

Target package:

CityNexus-EAC-RealCity-Product-Closure-20260916.zip

Include:
- SAME_JOURNEY_TRACE.json
- REAL_XIAMEN_CHAIN_RESULTS.md
- HOTEL_FLOW_RESULTS.md
- LIVE_REPLAN_RESULTS.md
- ORDER_IMPORT_RESULTS.md
- UI_REFERENCE_PARITY.md
- USER_JOURNEY_RESULTS.md
- REMAINING_PRODUCT_GAPS.md
- TEST_RESULTS.md
- CHANGED_FILES.txt
- before/after screenshots
- source patch / changed sources

Do not stop at "route opens".
Stop only when the user-visible task completes, or return BLOCKED honestly.
