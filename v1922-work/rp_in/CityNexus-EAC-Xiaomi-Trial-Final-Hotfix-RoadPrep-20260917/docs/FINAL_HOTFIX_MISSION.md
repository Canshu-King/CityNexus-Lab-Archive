# EAC Final Xiaomi Trial Hotfix Mission

Authoritative repository:

D:\moodle\CityNexus

Use the CURRENT repository state.

Do not roll back to an older snapshot.

Read the embedded WorkBuddy result and this RoadPrep.

This round is narrow.

==================================================
1. REVALIDATE BEFORE EDITING
==================================================

For each blocker B1-B6:
- reproduce against CURRENT code;
- mark FIXED / STILL_OPEN / PARTIAL;
- save one minimal proof.

If already fixed after the exported package:
do not re-implement it.

==================================================
2. FIX ONLY STILL-OPEN BLOCKERS
==================================================

Priority order:

P0/P1:
- run-specific AI planning truth gate
- deep-link blank routes
- price/free/partial-budget truth
- Me policy leakage
- Wallet consumer flow + parse feedback

Then:
- Copilot/Agent remaining engineering vocabulary
- evidence assertion cleanup

Do NOT start unrelated architecture work.

==================================================
3. BUDGET ADVISORY
==================================================

Implement a simple truthful advisory.

Do not invent exact trip cost.

Use:
- total budget
- trip duration
- traveler count

to produce an approximate budget-per-day / per-person sanity signal.

For obviously tight cases:
- warn;
- explain that actual lodging/transport/food may exceed the plan;
- let user edit budget;
- allow intentional continue.

==================================================
4. FINAL COPILOT PROOF
==================================================

Ask through visible UI:

`鼓浪屿好玩吗？`

Expected:
- useful Chinese traveler answer from grounded evidence;
OR
- honest cannot-verify response plus a useful real search/discovery action.

No raw enums.
No provider/model plumbing.
No engineering vocabulary.

Capture AFTER the final code.

==================================================
5. FINAL SAME-XIAMEN TRACE
==================================================

Create ONE fresh Xiamen journey and complete:

create
-> AI request
-> >=2 real Xiamen candidates
-> select plan
-> Trips multi-day
-> Activity Detail
-> hotel compare/select
-> booking import/confirm
-> Copilot place question
-> Xiamen map
-> Live disruption
-> material replan
-> UI accept
-> final state

Use one journey_id.

Record:
- journey_id
- candidate plan ids
- selected plan id
- post-replan active plan id
- booking id
- hotel/stay identity

No `/demo/reset`.
No API substitute for critical user actions.

==================================================
6. SPECIFIC REGRESSIONS
==================================================

Run focused tests:

A. known-free POI -> 免费
B. known-paid POI -> amount
C. unknown price -> 暂无价格
D. partial price coverage -> total unknown / known partial, no false budget verdict
E. 39d / 2p / CNY3000 -> budget advisory
F. /v8/today active/no-active
G. /v8/copilot active/no-active
H. old existing plan + failed new AI run -> NOT success
I. raw JSON invalid -> visible error, no crash
J. Me default -> no ADVISORY/权限边界
K. Copilot default -> no What-if Studio/JourneyTwin/deterministic

==================================================
7. FINAL EVIDENCE
==================================================

Produce:

- FINAL_HOTFIX_RESULTS.md
- FINAL_FINDINGS_REVALIDATION.md
- VISIBLE_UI_TRACE_FINAL.json
- FINAL_TRACE_MAPPING.md
- FINAL_XIAOMI_SCREENSHOTS/
- TEST_RESULTS.md
- CHANGED_FILES.txt

The trace must be generated after the final code changes.

Do not reuse stale canonical trace.

==================================================
8. VERDICT
==================================================

Final verdict exactly:

BLOCKED_FOR_REAL_USER_TRIAL

or

READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL

Target package:

CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917.zip
