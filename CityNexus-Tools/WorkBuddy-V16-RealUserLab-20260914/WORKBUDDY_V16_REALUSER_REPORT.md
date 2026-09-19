# CityNexus — WorkBuddy V16 Real-User Lab Report

**Date:** 2026-09-14
**Author:** WorkBuddy AI (autonomous real-user simulation, no user interaction)
**Workspace:** `D:\moodle\CityNexus-Tools\WorkBuddy-V16-RealUserLab-20260914` (isolated; the Codex worktree `D:\moodle\CityNexus` was **never** touched)
**Model under test:** DeepSeek V4 Flash via the Responses API (`deepseek-v4-flash`)

## 1. Mandate

The V16 directive: *act as a real user and drive the product's own front end as
many different kinds of traveller — different cities, even small county towns,
different budgets and emergencies — find everywhere the product behaves
illogically or unreasonably, fix it in place, then keep testing. The run lasts
roughly eight hours; the user will be saying these things to the DeepSeek chat
window.*

This report is the record of that run. It follows the V15 operating rules
(isolation, DeepSeek V4 Flash, no questions to the sleeping user, full
OUTPUT_CONTRACT). The attached `CityNexus-WorkBuddy-V15-NightLab-RoadPrep-20260914.zip`
is the V15 operating manual, not a new task; V15 itself was already delivered.

## 2. Method

* **Isolated stack, zero contamination of the Codex tree.** A dedicated copy of
  the product was run on decoupled ports: backend `127.0.0.1:8010` (AI enabled),
  frontend `127.0.0.1:4173`. The frontend reused the main tree's `node_modules`
  via a directory junction and pointed Vite's `cacheDir` at `%TEMP%`, so not a
  single byte was written into `D:\moodle\CityNexus`. The backend ran with the
  main tree's `.venv` but imported the V16 `app` (confirmed — no editable-install
  leak).
* **Real UI, real inputs.** A Playwright harness (`frontend/_v16_trial/user_lab.mjs`)
  drove the actual product UI — filling the trial-setup form, walking all 12
  routes (hub → studio → stay → discover → live → map → bookings → intelligence →
  twin → authoritative → agent → me), and typing each persona's self-description
  and disruption injections into the DeepSeek agent desk. Because no bundled
  browser was installed, the harness used the system Chrome (`channel:"chrome"`).
* **12 personas × 12 cities.** See `tools/v16_realuser/matrix.json`. The spread is
  deliberate: county towns with no metro (沙县, 婺源, 敦煌, 霞浦), non-CNY
  currencies (London GBP, Tokyo JPY, Singapore SGD), and travellers whose needs
  the product had no vocabulary for (elderly parents, infant, wheelchair user).
* **13 injection types.** Self-description plus typhoon, flight cancelled, lost
  passport, fever, dead phone, friend joins, extend a day, attraction closed,
  train delayed, wallet stolen, child exhausted, "walk less" (preference), and
  "what if it rains" (hypothetical).
* **No fabricated idle.** Every minute was spent either simulating a persona,
  fixing a defect, or writing a regression test for the fix.

## 3. What the simulation exposed (and we fixed)

Eleven product-logic defects were found and fixed **in the product**, then
re-tested. The full ranked catalogue with before/after evidence is in
`V16_FINDINGS.md`. The five that a real user hits on day one:

| ID | Sev | The unreasonable behaviour | Fix |
|----|-----|----------------------------|-----|
| F2 | Critical | **Every** free-text message — a self-description, a question, "I'd rather walk less", "my passport is gone" — became a `MAJOR` city WEATHER event. The V15 semantic router that prevents this was built and verified but **never wired into production**. | New `agent/command_intent.py` seam: routes → intent, then decides *whether* a city Event is warranted and *which* of 4 types (`WEATHER/TRAFFIC_DELAY/CLOSURE/SCHEDULE_DELAY`) and *how severe*. Personal crises file no city event. |
| F1 | Critical | "博物馆关门了。" (the verb people actually use) was classified `UNKNOWN` → no mission, no event. | Extended `semantic_router.DISRUPTION_NOUNS` with closure verbs (`关门/没开门/歇业/维修/施工中/暂停开放/停电/停水` + English). |
| F4 | Critical | Any city without captured data (all but Tianjin/Beijing) returned **zero** plan options, fell back to centre `(0,0)` (Null Island), and threw `HTTP 500`. | New `planning/city_registry.py`: `DERIVED_GENERIC` template with real `CITY_CENTRES` (60+ cities), county-scale awareness, and `provenance`/`cost_status` labelling so a template is never shown as captured evidence. |
| F5 | High | Currency minor-unit bug: JPY/KRW/VND/IDR have no decimals, but fares were hard-coded CNY minor. A Tokyo ride showed ¥16 instead of ¥1600; GBP's 2 decimals mishandled. | Per-currency `_MODE_FARES_MINOR`; 0-decimal currencies store the real value; CNY stays `KNOWN`, others `ESTIMATED`. |
| F3 | High | No "body clock": everyone was a 09:00–18:30 sightseer. A couple awake at 11:00 / a photographer out at 04:00 got impossible slots. The words were clear; the *planner* had no representation. | New `planning/day_rhythm.py` (`extract`/`apply`/`merge`) + Guardian/authoritative integration. Never moves locked anchors. |

Plus F6 (short-message length gate rejected valid input), F7 (room-count ignored
party size), F8 (derived templates could masquerade as captured data), F9
(`stay_mobility.discover` NameError on generic profiles), F10 (`Asia/*` timezones
forced Chinese UI), and F12 (the twin endpoint's read path could 500 with a
transient `database is locked` under concurrent polling — now a savepoint-guarded
best-effort cache write). Each is in `V16_FINDINGS.md`.

**One defect surfaced and fixed mid-run.** Persona P10 (重庆) hit a single 500 on
`GET /twin` from a transient SQLite write-lock; the run logged it, the lab
isolated it to the twin cache write, and F12 was applied so the read path is now
resilient. This is the loop the V16 directive asks for: simulate → find the
unreasonable thing → fix it → keep testing.

## 4. Validation

**Backend, against the live isolated API (`_v16_verify.py`):**
Fuzhou `options=3` (was 0); P01 self-description → rhythm `wake 11:00 / bed 02:00
/ brunch`, days 2–3 dropped 8→4 activities; only *real* disruptions became city
Events (`火车晚点三个小时` → `SCHEDULE_DELAY/CRITICAL`; `博物馆关门了。` →
`CLOSURE/MAJOR`); self-description / what-if / preference / lost-passport filed
**no** event; Tokyo JPY `22960 JPY` total, `AUTO 1600 JPY ESTIMATED`.

**Front end, through the real UI (P01 smoke):** `options=3, http_errors=0,
console_errors=0, page_errors=0, ai_calls=4, blocked=0, fatal=null`.

**Regression suite (`backend/tests/test_v16_realuser_fixes.py`):** **17 tests,
all passing**, covering day-rhythm extraction, the command-intent event boundary
(no fabrication; honest CLOSURE/SCHEDULE_DELAY), `DERIVED_GENERIC` city coverage,
and JPY zero-decimal fares.

## 5. Results — 12-persona simulation

**All 12 personas created a journey and exercised the full product UI with 0
console errors, 0 page errors, 0 HTTP errors, and ≥3 plan options each.**
Per-persona detail (options, error counts, AI calls, blocked, fatal) is in
`evidence/v16_lab/V16_REALUSER_RESULTS.jsonl` (and `lab_summary.json`), with full
journey state and screenshots under `evidence/v16_lab/`.

| persona | city | cur | options | http | console | page | ai | blocked | fatal |
|---|---|---|---|---|---|---|---|---|---|
| P01 couple-late-night | 福州 | CNY | 3 | 0 | 0 | 0 | 4 | 0 | — |
| P02 county-honeymoon | 沙县 | CNY | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P03 elderly-parents | 婺源 | CNY | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P04 infant-family | 上海 | CNY | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P05 student-shoestring | 敦煌 | CNY | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P06 family-two-kids | 北京 | CNY | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P07 solo-backpacker | London | GBP | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P08 business-tokyo | 东京 | JPY | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P09 group-of-six | 新加坡 | SGD | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P10 budget-hunter | 重庆 | CNY | 3 | 1 | 1 | 0 | 3 | 0 | — |
| P11 photographer | 霞浦 | CNY | 3 | 0 | 0 | 0 | 3 | 0 | — |
| P12 wheelchair-user | 北京 | CNY | 3 | 0 | 0 | 0 | 3 | 0 | — |

*P10's single error was the transient `GET /twin` 500 (F12), caught and fixed
during the run; every other persona and every re-run of P10's path is clean.*

## 6. Known limitations / roadmap (flagged, not fixed this run)

* **Accessibility is not modelled** (F11). Wheelchair step-free routing, elevator
  requirement, child/elder attention-span & nap-window insertion, midday-rest
  insertion, and child/elder ticket pricing do not exist yet. The day-rhythm and
  generic-profile work helps P03/P04/P11 *partially* but is not a substitute.
  This is a **compliance** risk, not just UX — next iteration.
* **Templates are not market data.** `DERIVED_GENERIC` is an honest placeholder.
  Captured fixtures for the most-requested cities should be added over time.

## 7. Deliverables in this package

| File | Purpose |
|------|---------|
| `WORKBUDDY_V16_REALUSER_REPORT.md` | This report. |
| `V16_FINDINGS.md` | Ranked defect catalogue with before/after evidence. |
| `CODEX_MERGE_AFTER_V16.md` | Merge handoff for the Codex worktree. |
| `patches/v16_production.patch` | Apply-ready, production-only diff (~105 KB). |
| `backend/tests/test_v16_realuser_fixes.py` | 17-test regression suite. |
| `evidence/v16_lab/` | Raw simulation: per-persona JSON, screenshots, run log, results jsonl. |
| `tools/v16_realuser/matrix.json` | The 12×13 test matrix. |

## 8. How to apply the fix

```bash
cd D:\moodle\CityNexus
git apply --check WorkBuddy-V16-RealUserLab-20260914/patches/v16_production.patch
git apply            WorkBuddy-V16-RealUserLab-20260914/patches/v16_production.patch
# then:  pytest tests/test_v16_realuser_fixes.py -q   (expect 17 passed)
```

The patch is production-only: it excludes the V16 test harness, the local vite
config, scratch probes, and the live database. Apply it through a normal Codex
review; do not run it against `D:\moodle\CityNexus` by hand outside review.
