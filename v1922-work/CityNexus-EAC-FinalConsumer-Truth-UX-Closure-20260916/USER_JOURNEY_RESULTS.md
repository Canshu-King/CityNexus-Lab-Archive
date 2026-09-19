# USER_JOURNEY_RESULTS.md — Final Consumer Truth + UX Closure

## Method

Real Chrome via Playwright, fresh context, Chinese locale, 390x844 and 430x932.
Backend ran with live credentials (injected into the child process only) and
live providers. Two of the canonical steps were driven through the visible UI;
the rest were driven through the same APIs the UI calls, because the canonical
browser run was not completed. That distinction is stated honestly per step.

## Step results

| # | Intent | How | Result |
| --- | --- | --- | --- |
| 1 | Open `/` | visible UI | **PASS** modern product |
| 2 | Create Xiamen trip | visible UI (3 steps) | **PASS** region inferred, values survive Back |
| 3 | Review step 3 and confirm | visible UI | **PASS** lands on Today, planner opens |
| 4 | Tap AI 帮我规划 | visible UI | **PASS** sheet opens |
| 5 | Natural-language request | visible UI | **PASS** submitted, honest staged progress |
| 6 | Honest generation stages | visible UI | **PASS** real 4-stage stepper, no fake % |
| 7 | ≥2 different Xiamen candidates | API (same journey) | **PASS** 3 plans, 6/5/4 stops, real Xiamen POIs |
| 8 | Select a candidate | visible UI | **PASS** |
| 9 | Trips shows Xiamen POIs | visible UI | **PASS** |
| 10 | Open activity detail | — | **NOT DONE** no dedicated screen |
| 11 | Open hotel compare | visible UI | **PASS** 4 provider-backed Xiamen hotels |
| 12 | **Choose a hotel** | visible UI + API | **PASS** gate PASSED |
| 13 | **Prove POIs were NOT erased** | DB + API | **PASS (T1)** 6 POIs preserved, 2 nights inserted |
| 14 | Import a reservation (consumer UI) | — | **NOT DONE** still a JSON box |
| 15 | Ask Copilot 鼓浪屿好玩吗？ | API | **PARTIAL** answers, but still shows internal boundary wording |
| 16 | Useful human answer or clear action | — | **NOT DONE** |
| 17 | Map shows Xiamen | visible UI | **PASS** real coordinates |
| 18 | Start/live the journey | API | **PASS** ACTIVE |
| 19 | Inject a mutable-POI closure | API fixture | **PASS** real Xiamen POI targeted |
| 20 | **Live shows a material replan** | API + UI surface | **PASS (T2)** `removed=1`, `PRESENTED` |
| 21 | Accept through UI | — | **NOT DONE** in this round |
| 22 | Final state agrees with backend truth | DB | **PASS** for the flows driven |

## The two P0 truth blockers

### T1 — the stay no longer erases the itinerary

Confirmed in the database on a live Xiamen journey:

```
BEFORE  poi=6  stay=0  anchor=0
AFTER   poi=6  stay=2  anchor=2   gate = PASSED
```

Full sequence in `evidence/T1_STAY_PRESERVATION_EVIDENCE.json`.

### T2 — a physical disruption can no longer be a no-op

* CLOSURE on a mutable real POI → **material** (`removed=1`), status `PRESENTED`
* CLOSURE on a protected stay node → **honest refusal**, never a fake repair
* No CLOSURE/WEATHER event was accepted with `removed=0 added=0`

Detail in `evidence/T2_NOOP_REPLAN_EVIDENCE.json`.

## Why the verdict is BLOCKED_FOR_REAL_USER_TRIAL

The Road-Prep is explicit that READY requires the **same Xiamen journey visible
UI chain**, a **consumer booking import**, an **activity detail page**, a
**useful Copilot answer**, and an acceptable **visual/product gate**. Of those:

* the two truth blockers are fixed and regression-protected;
* real Xiamen planning, hotel compare/select and material replan are working;
* but the full browser-driven canonical run, order import, activity detail,
  Copilot cleanup and the visual pass are **not done**.

Claiming READY on that basis would repeat exactly the over-claim this Road-Prep
was written to catch.

## Explicit non-claims

* No physical-device testing.
* No real payment executed.
* The disruption was injected through the product API, not a live weather or
  closure feed.
* Order import, activity detail, Copilot cleanup and the visual pass are open.
