# EAC OVERNIGHT MASTER MISSION V2

You are the primary CityNexus implementation agent for an 8–9 hour overnight mobile-product rescue.

Authoritative repository:

D:\moodle\CityNexus

This V2 mission supersedes the previous overnight mobile rescue prompt.

The user has now used the product on a real Xiaomi 13 Ultra and concluded that the current UI is not logically usable.

Your job is not to defend the current interface.
Your job is to turn the existing CityNexus engineering capability into a coherent consumer travel product.

Read in order:

1. README_FIRST.md
2. docs/DESIGN_CORRECTIONS_REQUIRED.md
3. docs/PRODUCT_FLOW_SPEC.md
4. docs/UI_REFERENCE_INDEX.md
5. evidence/real_phone_before/
6. ui_reference/final_10/

==================================================
MISSION PRINCIPLE
==================================================

A user should not need to know:

- hidden URLs
- PlanVersion
- C4
- semantic keys
- provider evidence
- deterministic gates
- internal action enums
- implementation architecture

to use CityNexus.

By morning, a first-time traveler must be able to:

open app
-> create trip
-> tell AI what they want
-> see truthful planning progress
-> compare candidate plans
-> choose a plan
-> inspect a multi-day itinerary
-> inspect activities and hotels
-> use map
-> ask Copilot questions
-> survive route/runtime errors
-> enter live journey
-> understand a disruption
-> accept a governed replan

==================================================
PHASE 0 — BACKEND TRUTH CLOSURE
==================================================

First finish the embedded V19.2.5 C4 interior-boundary hotfix under:

reference/backend_truth/

Do not spend the whole night here.

Verify:

MID_TRIP before ARRIVAL -> reject
MID_TRIP after DEPARTURE -> reject
role-less locked activity outside ARRIVAL/DEPARTURE -> reject
valid controls -> pass

Then freeze backend truth and move to product work.

==================================================
PHASE 1 — REPRODUCE CURRENT REAL-PHONE FAILURES
==================================================

Start actual backend/frontend.

Use:
- 390x844
- 430x932
- Xiaomi-13-Ultra-like mobile viewport

Clear local browser state.

Reproduce before fixing:

- root/legacy entry confusion
- giant setup form
- invisible CTA/theme-token defect
- no obvious place to enter itinerary
- raw REQUEST_PLACE_SEARCH
- wallet white screen
- Xiamen journey showing Tianjin fallback map
- Copilot overlay consuming too much space
- primary nav missing a real Trips entry
- multi-day journey treated like a single city-day flow

Document actual root causes.

==================================================
PHASE 2 — IMPLEMENT THE PRODUCT INFORMATION ARCHITECTURE
==================================================

Formal bottom navigation must be:

Today / 今天
Trips / 行程
Map / 地图
Copilot
Me / 我的

Remove Wallet from the primary bottom navigation.

Move wallet/bookings/documents into Trips or Me.

Keep the mobile drawer for advanced/secondary functions.

Default `/` must enter the modern traveler product, not LegacyApp.

==================================================
PHASE 3 — IMPLEMENT THE NEW CREATE-TRIP FLOW
==================================================

Follow:
- UI reference 03
- UI reference 04
- required Step 3 from PRODUCT_FLOW_SPEC

Step 1:
destination + arrival/departure facts

Step 2:
travelers + rooms + budget + pace + interests + special requirements

Step 3:
review and confirm

Important:
- infer country/timezone/currency from city where confident;
- put technical values in Advanced settings;
- sticky visible CTA;
- preserve values when going back;
- language toggle works;
- primary CTA cannot be invisible.

==================================================
PHASE 4 — BUILD THE ACTUAL "PLAN MY TRIP" EXPERIENCE
==================================================

Follow UI references 05, 06, 07.

The user must be able to type natural language.

Example:

“我和朋友两个人去厦门，想轻松一点，想去鼓浪屿、环岛路，想吃沙茶面和海鲜，不想太赶，也想找性价比高的酒店。”

Use existing DeepSeek / Provider / Journey / PlanVersion capabilities truthfully.

No raw internal action enum.

Generation state:
- real stages
- do not fake exact percentage unless backend provides it

Plan comparison:
- multiple styles
- real budget relationship
- intensity
- travel/walking burden
- suggested accommodation area
- highlights
- choose plan

If the backend cannot actually produce some field, do not fabricate it just to match the screenshot.

==================================================
PHASE 5 — TRIP DETAIL / ACTIVITY / HOTEL
==================================================

Follow:
- 02_trip_detail_multiday.png
- 08_activity_detail.png
- 09_hotel_comparison.png

Trip detail:
- multi-day
- week/date selection
- day timeline
- confirmed reservations
- map preview
- add/reorder/replan

Activity:
- human-readable opening hours
- duration
- cost
- reason for recommendation
- transit
- add/replace/map

Hotels:
- price
- area
- distance from itinerary
- reason recommended
- compare/select

Use real provider facts where available.
Missing data must be shown as missing.

==================================================
PHASE 6 — MAP TRUTH
==================================================

Remove traveler-facing hardcoded Tianjin fallback.

Xiamen journey must never silently render Tianjin.

If trustworthy coordinates are missing:
show an explicit no-location state.

Test:
- Xiamen with data
- Xiamen without route
- GPS allowed
- GPS denied

==================================================
PHASE 7 — COPILOT RESCUE
==================================================

Raw action strings are forbidden.

Bad:
REQUEST_PLACE_SEARCH

Good:
“我来搜索鼓浪屿，并结合你当前的厦门行程看看是否适合安排。”

Where safe:
execute action.

Where confirmation is needed:
show human action chips.

Any action that mutates itinerary should:
- explain change
- require suitable confirmation
or
- provide undo where appropriate

Copilot must know current trip context.

Use compact launcher / intentional sheet.
Do not permanently cover half the screen.

==================================================
PHASE 8 — LIVE JOURNEY + GOVERNED REPLAN
==================================================

Follow UI reference 10.

Surface backend Event / Recovery / ReplanProposal as traveler language:

- what happened
- what is affected
- recommended new order
- what remains unchanged
- accept new plan
- adjust today only
- remind later

Never let acknowledgement visually imply HARD issue is solved.

==================================================
PHASE 9 — ORDER IMPORT + C4 PRODUCT ENTRY
==================================================

Implement a usable order-import flow even though it is not one of the ten standalone screenshots.

At least support the product shell for:

- upload screenshot if current stack supports it
- paste reservation text
- manual entry

Then:
parse
-> show extracted reservation
-> user confirms
-> create booking/commitment through existing backend path

Do not create silent commitments from uncertain OCR/AI text.

==================================================
PHASE 10 — ERROR BOUNDARY / EMPTY / FAILURE STATES
==================================================

Known Wallet crash must be fixed.

Add route/product Error Boundary.

No white screen may trap the user.

Required failure states:
- backend offline
- DeepSeek unavailable
- provider unavailable
- no location data
- GPS denied
- no bookings
- no plan
- route/component runtime error

Always give:
- what happened
- what is safe
- retry/back/home

==================================================
PHASE 11 — AUTONOMOUS REAL-USER LOOP
==================================================

This is mandatory.

After implementation, STOP CODING and USE THE APP.

Pretend you do not know hidden routes or architecture.

Fresh browser.

Complete the entire flow through visible UI only.

Then deliberately:
- use browser back
- hard refresh
- change language CN -> EN -> CN
- open every primary tab
- open drawer
- open/close Copilot repeatedly
- double-tap CTAs
- disconnect backend
- reconnect backend
- simulate AI failure
- deny GPS
- load stale plan
- enter recovery
- use long trip
- use short trip
- test empty data

For every P0/P1:
fix it
then restart the scenario.

Do not call a screen passed because it merely rendered.

==================================================
PHASE 12 — MOTION / MOBILE QUALITY
==================================================

Preserve:
- drawer slide
- bottom-sheet transition
- route transitions
- loading/skeleton
- pressed/disabled states
- reduced-motion support

No animation that delays a task.

No primary CTA after absurd scrolling if a sticky CTA is appropriate.

==================================================
TEST / RELEASE
==================================================

Required:

- V19.2.5 C4 truth probe
- relevant backend suites
- broad backend regression
- frontend build
- typecheck/lint if present
- browser mobile E2E
- 390x844
- 430x932
- Xiaomi-like viewport
- OpenAPI if API changed

==================================================
DO NOT STOP EARLY
==================================================

This is an 8–9 hour overnight mission.

If green early:
keep using the product as different user personas.

Do NOT spend leftover time inventing unrelated backend architecture.

==================================================
MORNING OUTPUT
==================================================

Produce:

CityNexus-EAC-Overnight-Mobile-Product-Rescue-V2-20260916.zip

Include:

- PRODUCT_RESCUE_REPORT.md
- USER_JOURNEY_RESULTS.md
- BUGS_FOUND_AND_FIXED.md
- REMAINING_PRODUCT_GAPS.md
- UI_IMPLEMENTATION_MAP.md
- TEST_RESULTS.md
- CHANGED_FILES.txt
- source patch / changed source
- screenshots/before/
- screenshots/after/
- browser flow evidence

Final verdict only:

BLOCKED_FOR_REAL_USER_TRIAL

or

READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

READY is allowed only if you personally complete the visible end-to-end traveler workflow in the browser.

Start now and continue through the full overnight window.
