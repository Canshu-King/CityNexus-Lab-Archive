# EAC Xiaomi Trial Final Hotfix v2 Mission

Authoritative repository:

D:\moodle\CityNexus

Use CURRENT repository state.

Do not roll back.

Do not start Frontend vNext / router refactor yet.

This round closes only confirmed trial blockers.

==================================================
STEP 1 — R1-a / R1-b recovery truth
==================================================

Fix:
- null protected-activity false positive;
- target identity propagation after semantic impact resolution;
- deterministic fallback for an unresolved named venue.

Regression:
booking-first journey
-> planning
-> explicit named mutable-POI closure
-> proposal succeeds or honest NO_ALTERNATIVE
-> not a false "protected" 422.

==================================================
STEP 2 — Live proposal UX
==================================================

Before rendering:
- canonicalize semantic diff identity;
- dedupe equivalent proposals.

For genuine alternatives display:
- what is removed;
- what is added/replaced;
- time/day effect if known;
- why this option differs.

Never present two indistinguishable "接受新方案" buttons.

==================================================
STEP 3 — Consumer language cleanup
==================================================

Booking:
- map role/status/extraction/anchor/payment/artifact/provider fields to human copy;
- move raw values to Advanced.

Copilot:
- remove raw tool_name from default mission rail;
- humanize statuses.

Trips:
- localize check_out/departure/museum/etc.

Do not expose internal enums by default.

==================================================
STEP 4 — Copilot dock avoidance
==================================================

When create/planning/booking/modal/sheet/high-priority Live surface is open:
- auto-minimize or hide dock;
OR
- ensure z-index/layout never obstructs primary actions.

Test:
- 390x844
- 412x915 Xiaomi-like
- 430x932

==================================================
STEP 5 — AI success fail-closed
==================================================

Baseline plan snapshot is a prerequisite for run-specific success attribution.

If baseline fetch fails:
- do not substitute empty set;
- do not claim success;
- show honest "无法确认本次是否生成新方案，请重试/刷新" state.

Add regression:
old plan exists
+ baseline GET fails
+ new planning run creates nothing
+ later plans GET succeeds
=> NOT success.

==================================================
STEP 6 — final product truth trace
==================================================

Use a fresh Xiamen journey.

Important new requirement:
the journey MUST import/confirm a booking before the closure/replan step.

Then:
create
-> AI plan
-> select
-> hotel
-> booking import/confirm
-> Copilot
-> Live
-> explicit mutable POI closure
-> proposal
-> accept
-> final state.

Capture ID-level before/proposal/after evidence.

==================================================
STEP 7 — evidence + regression
==================================================

Produce focused tests for every fixed blocker.

Do not reuse pre-fix screenshots.

Target output:

`CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-v2-20260918.zip`

Final verdict only:

`BLOCKED_FOR_REAL_USER_TRIAL`

or

`READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL`
