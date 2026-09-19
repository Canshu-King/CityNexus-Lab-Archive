# CityNexus — Overnight Continuation, Final

Package: `CityNexus-EAC-Overnight-Continuation-Final-20260917.zip`
Produced: 2026-09-17T15:05:02.584210+08:00
Authoritative repository: `D:\moodle\CityNexus`

This package continues the mission from Checkpoint O1 and absorbs the
independent WorkBuddy findings. It is NOT the O1 package.

## Verdict

**READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL**

## What is inside

| folder | contents |
|---|---|
| `source/backend` | FastAPI app, tests, data fixtures |
| `source/frontend` | React/Vite source, config, public assets |
| `source/docs` | repository documentation |
| `evidence/` | run traces, the overnight ledger, acceptance results, viewport evidence |
| `reports/` | the five autonomous lab cycles, WorkBuddy revalidation |
| `screenshots/` | 144 acceptance screenshots |

## Acceptance summary

* **SIX end-to-end browser runs**, all through the visible UI, all with zero
  console errors and zero failed steps:
  1. canonical same-Xiamen chain (create -> AI -> compare -> select ->
     itinerary -> detail/map -> hotels -> booking -> Copilot -> map -> Live ->
     disruption -> replan -> accept -> refresh -> back/forward)
  2. budget-constrained
  3. long six-day trip
  4. booking-first
  5. degraded / offline providers
  6. hostile loops (double-tap, refresh during AI, duplicate submit, network loss)
* **FIVE autonomous product-lab cycles** (`reports/AUTONOMOUS_CYCLE_1..5.md`).
  Cycle 1 and cycle 4 each found and fixed a real defect.
* **Three acceptance viewports**: 390x844, 430x932, and Xiaomi 13 Ultra
  (412x915 @ DPR 3.5).
* **Backend regression suite: 739 passed, 0 failed, 15 skipped.**
* Frontend production build succeeds.

## Defects found and fixed in this continuation

See `evidence/PRODUCT_ACCEPTANCE_RESULTS.md` section 5 for the full table.
Highlights: AI planning false success; the planner cramming every stop into
day 1; the stay calendar failing to place day-2 stops; one conflicting hotel
suppressing all options; structural places leaking into public discovery;
manual bookings that could never be applied; a typed booking price being
silently dropped; the Copilot answering a question with a routing stub;
Overpass ignoring the asked category; replan HTTP 500s from missing frozen
legs and mixed timezone offsets; an accepted replan failing to remap a C4
commitment; Today and Trips showing contradictory clock times; and the plan
comparison fabricating a "within budget" verdict from missing price data.

## Known limitations (honest)

* Public map and accommodation providers (Overpass, Nominatim, OSM tiles) are
  intermittently unreachable from the test network. The product reports this
  honestly rather than inventing data; a real trial on a normal network should
  show live tiles and live pricing.
* Accommodation prices are frequently unknown (`price_known = false`). Those
  are now shown as "暂无价格 / 花费未知" instead of CNY 0.
* Two repository tests that directly contradicted the safety rules were
  reconciled toward the truth rule (never treat missing accessibility evidence
  as accessible; never persist a nonsense 0 m walking cap as a hard limit).

## How to run

```
cd source/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

cd source/frontend
npm install
npm run dev -- --host 127.0.0.1
```

Secrets are never included. The backend reads provider keys from the
environment.
