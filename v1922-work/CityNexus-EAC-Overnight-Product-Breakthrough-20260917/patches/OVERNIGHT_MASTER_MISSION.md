# OVERNIGHT MASTER MISSION

You are the primary implementation agent for CityNexus.

This is not another maintenance sprint.

This is the overnight product breakthrough sprint.

The user has already spent many rounds watching backend tests turn green while
the mobile product remains confusing, technical, and incomplete.

Tonight must materially change the actual application.

==================================================
0. NON-NEGOTIABLE PRINCIPLES
==================================================

1. Do not wait for the user.
2. Do not ask for minor product decisions.
3. Make conservative, reversible decisions and document them.
4. Never print or persist secrets.
5. Use the user's existing DeepSeek/provider configuration when available.
6. If an external provider is unavailable, keep building the product around
   honest loading/failure states rather than blocking the entire night.
7. Do not use `/demo/reset` as acceptance evidence.
8. Do not substitute API calls for critical traveler actions.
9. A route opening is not a completed feature.
10. A passing backend suite is not a usable product.
11. Do not return another backend-only package.
12. Do not stop early because the first acceptance run is green.

==================================================
1. FIRST: CLOSE SNAPSHOT M TRUTH GAPS
==================================================

Use the embedded:

reference/CityNexus-EAC-SnapshotM-TruthToProduct-FinalRoadPrep-20260917.zip

Read and execute its mission first.

Specifically close:

- no silent activity-duration shrink when selecting a hotel;
- pinned-to-pinned mobility reachability;
- Activity Detail coordinates from Place;
- known-free vs unknown-price truth;
- network AUTO documentation/implementation mismatch;
- permanent regression tests for those cases.

TIMEBOX:

Aim to finish this phase in 60–90 minutes.

Do not spend the entire night discovering increasingly obscure scheduler
edge cases.

If a true P0 emerges, fix it.
Otherwise move to product work.

==================================================
2. CONSUMER BOOKING IMPORT
==================================================

The normal traveler must never be required to paste raw reservation JSON.

Implement a consumer flow:

Entry:
- paste booking/confirmation text;
- manual form;
- image/screenshot upload only if the current stack truthfully supports it.

Parsing:
- use deterministic parsing first where possible;
- use AI extraction only as advisory;
- show extracted fields before committing.

Preview:
- type: flight / train / hotel / ticket / reservation;
- title/provider;
- confirmation/reference;
- start/end;
- location;
- amount/currency if known;
- traveler/guest count where known.

User can edit before confirming.

Commit only after explicit confirmation.

Then:
- create Booking / Commitment through authoritative existing backend path;
- show it in Trips and Today where relevant.

Raw JSON:
- Advanced/Developer only.

Required browser evidence:
text paste -> parsed preview -> edit -> confirm -> booking appears.

==================================================
3. TODAY / HOME MUST BECOME A REAL TRAVEL DASHBOARD
==================================================

Replace generic product copy with current-trip truth.

The first screen must answer within one viewport:

- Where am I going?
- When?
- What is next?
- What needs attention?
- What has been confirmed?
- What can AI help with?

For the acceptance Xiamen journey show traveler-facing content such as:

- 厦门之旅
- date / current day
- next action
- today's plan summary
- selected hotel / booking summary
- disruption/risk if any
- compact AI planning / Copilot CTA

Remove generic engineering/marketing filler from the primary experience.

No:
- `STILL UP`
- `PLANNING READY`
- `One Day in Nexus City`
- exposed internal status enums

==================================================
4. TRIPS MUST BECOME THE PRODUCT CONTROL CENTER
==================================================

Do not create another long technical scroll dump.

Structure the Trip screen around traveler tasks:

- 行程
- 住宿
- 预订
- 花费 / 预算
- 资料 / 同行人 when available

The default trip screen should show:
- trip identity;
- date span;
- multi-day overview;
- today's or selected-day timeline;
- confirmed anchors;
- open gaps;
- hotel status;
- primary actions.

Use day/week grouping for long trips.

Preserve the actual day structure after hotel selection.

No silent cross-day compaction.

==================================================
5. ACTIVITY DETAIL MUST BE ACTUALLY USEFUL
==================================================

Keep and finish the Activity Detail implementation.

Use real Place coordinates.

Show only truthful fields:
- name;
- place;
- opening hours if known;
- recommended duration;
- known-free / known-paid / unknown cost;
- why recommended;
- transit/route relationship where supported;
- current day/time slot;
- nearby places only when actual spatial distance supports "nearby".

Traveler actions:
- map;
- replace;
- move;
- add/save where supported;
- ask Copilot.

No fabricated provider facts.

==================================================
6. HOTEL COMPARE / SELECT MUST FEEL LIKE A REAL PRODUCT
==================================================

Hotels must be meaningfully differentiated by real data.

Where available show:
- real property name;
- area/address;
- price;
- cancellation/breakfast;
- actual relationship to itinerary;
- fit around arrival/departure;
- why recommended.

Unknown values stay unknown.

Do not repeat identical fake metrics across every card.

Selection must:
- preserve POIs;
- preserve intended day structure;
- preserve original activity durations;
- preserve locked/C4 truth;
- preserve CHECK_IN/STAY/CHECK_OUT;
- pass travel-time feasibility;
- update Trips.

If a hotel cannot fit:
show a conflict or proposed adjustment.
Do not silently rewrite the trip.

==================================================
7. COPILOT MUST ANSWER LIKE A TRAVEL ASSISTANT
==================================================

Default traveler view must not expose:
- semantic boundary;
- authority boundary;
- What-if Studio;
- UNVERIFIED;
- UNKNOWN;
- NONESEARCH;
- raw internal action enums;
- PlanVersion / C4 / JourneyTwin vocabulary.

For the acceptance question:

`鼓浪屿好玩吗？`

Expected product behavior:

- useful Chinese answer;
- current Xiamen-trip context;
- truthful provider/AI confidence;
- human action buttons such as:
  - 加入行程
  - 安排到第2天
  - 地图查看
  - 搜索更多

If live verification is unavailable:
say so plainly and offer a next action.

Do not turn the user into a policy debugger.

==================================================
8. MAP
==================================================

Xiamen journey must show Xiamen coordinates.

Priority:
1. current device position when granted;
2. selected activity;
3. itinerary Place coordinates;
4. arrival/departure;
5. resolved city center;
6. honest no-location state.

Never fabricate Tianjin or any other fallback city.

Map action from Activity Detail must select the exact Place.

==================================================
9. LIVE JOURNEY + GOVERNED REPLAN
==================================================

Traveler-facing first viewport:

- current stop / current time;
- next stop;
- route summary;
- disruption;
- affected activities;
- protected/unchanged commitments;
- proposed change;
- actions.

Actions:
- 接受新方案
- 仅调整今天
- 稍后提醒 / 查看详情

Engineering diagnostics:
- mode matrix;
- raw mobility evidence;
- guardian diagnostics;
- semantic/recovery internals

must live under Advanced.

Acceptance disruption:
- explicitly target a real mutable Xiamen POI;
- proposal must contain a material diff;
- no stable-copy fake fix;
- after accept, Trips/Live/backend truth agree.

Also separately test a protected hotel/commitment disruption:
the system must report a protected/manual-recovery state, not fake a repair.

==================================================
10. ME / SETTINGS
==================================================

Normal Me screen:
- profile;
- travel preferences;
- documents;
- wallet/bookings;
- language;
- app settings;
- advanced tools entry.

Move:
- 权限边界
- ADVISORY
- RECORD_ONLY
- delegation internals

behind Advanced/Developer.

==================================================
11. BUDGET SANITY
==================================================

Implement traveler-facing budget sanity.

Example:
39 days / 2 people / CNY 3000

Do not silently treat it as a comfortable normal budget.

Show:
- approximate daily budget;
- advisory warning;
- edit budget;
- continue intentionally.

Do not invent exact spend forecasts without data.

==================================================
12. MOBILE VISUAL IMPLEMENTATION
==================================================

Use the existing 10-screen UI reference package materially.

Do not merely keep the old console and rename sections.

Required:
- real visual hierarchy;
- mobile card system;
- touch-sized controls;
- sticky primary CTA where appropriate;
- clear empty/error/loading states;
- compact density;
- no browser-default giant form feeling;
- no permanent Copilot overlay obscuring content.

Chinese-first screenshots.

The UI reference images are direction, not truth.
Text specifications override inconsistent generated demo numbers.

==================================================
13. ERROR / FAILURE STATES
==================================================

No white-screen traps.

Test and handle:
- backend offline;
- provider unavailable;
- DeepSeek unavailable;
- GPS denied;
- no map coordinates;
- no bookings;
- no plan;
- runtime component error;
- stale/recovery state.

Every state must tell the traveler:
- what happened;
- whether their trip data is safe;
- what they can do next.

==================================================
14. FULL SAME-XIAMEN VISIBLE UI ACCEPTANCE
==================================================

Use ONE fresh Xiamen journey.

Critical actions must be visible browser actions:

1. open `/`
2. create Xiamen trip
3. complete Step 1 / 2 / 3
4. confirm
5. tap AI planning
6. enter natural-language request
7. see honest planning stages
8. see >=2 genuinely different Xiamen candidates
9. compare
10. choose one in UI
11. Trips shows real multi-day Xiamen itinerary
12. open Activity Detail
13. open hotel compare
14. choose hotel in UI
15. prove itinerary days + durations survive
16. paste/import a reservation through consumer UI
17. confirm booking
18. ask `鼓浪屿好玩吗？`
19. receive useful traveler answer or useful search action
20. open Xiamen map
21. start/live
22. inject explicit mutable-POI disruption fixture
23. see material replan
24. accept through UI
25. verify final Trips/Live/backend state agrees
26. switch 中文 -> EN -> 中文 and preserve context
27. hard refresh and continue
28. browser back/forward and continue

Produce:

`VISIBLE_UI_TRACE.json`

Every important step:
- timestamp
- journey_id
- route
- user action
- visible result
- request status
- active/selected plan id when relevant

No journey switching.

==================================================
15. REAL USER / HOSTILE TEST LOOPS
==================================================

After the canonical flow passes, do not stop.

Run at least 5 independent first-time-user loops.

Personas:
- first-time tourist;
- budget traveler;
- long-trip traveler;
- traveler with hotel booking already made;
- traveler during a disruption.

For each:
- start fresh;
- use visible UI only;
- note confusion;
- fix P0/P1;
- rerun.

Also deliberately:
- double-tap CTAs;
- refresh during loading;
- navigate away/back;
- deny GPS;
- disconnect/reconnect backend;
- disable AI;
- create empty trip;
- create long trip;
- open every primary tab;
- open/close Copilot repeatedly.

==================================================
16. TEST / QUALITY GATES
==================================================

Backend:
- Snapshot M probe;
- permanent regressions;
- focused truth suites;
- broad regression;
- no new failures.

Frontend:
- build;
- typecheck/lint where available;
- browser E2E;
- runtime console clean for canonical flow.

Viewports:
- 390x844
- 430x932
- Xiaomi-like viewport

Capture before/after screenshots.

==================================================
17. OUTPUT
==================================================

Produce:

`CityNexus-EAC-Overnight-Product-Breakthrough-20260917.zip`

Required contents:

- PRODUCT_BREAKTHROUGH_REPORT.md
- VISIBLE_UI_TRACE.json
- SAME_JOURNEY_RESULTS.md
- BOOKING_IMPORT_RESULTS.md
- ACTIVITY_DETAIL_RESULTS.md
- COPILOT_RESULTS.md
- HOTEL_RESULTS.md
- LIVE_REPLAN_RESULTS.md
- MOBILE_UI_RESULTS.md
- FAILURE_STATE_RESULTS.md
- BUGS_FOUND_AND_FIXED.md
- REMAINING_PRODUCT_GAPS.md
- TEST_RESULTS.md
- CHANGED_FILES.txt
- screenshots/before/
- screenshots/after/
- source patch or changed source files needed for review

Final verdict exactly:

`BLOCKED_FOR_REAL_USER_TRIAL`

or

`READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL`

READY is allowed only if the visible same-Xiamen flow actually completes.
