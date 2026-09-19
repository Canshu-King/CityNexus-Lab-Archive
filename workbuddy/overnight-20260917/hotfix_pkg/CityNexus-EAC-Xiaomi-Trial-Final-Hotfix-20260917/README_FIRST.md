# CityNexus — Xiaomi Trial Final Hotfix

Package: `CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-20260917.zip`
Produced: 2026-09-17T18:53:28.030274+08:00
Authoritative repository: `D:\moodle\CityNexus`

This is the narrow final hotfix and evidence-closure round. It is NOT another
product sprint, and it is NOT the previous package.

## Verdict

**READY_FOR_XIAOMI_13_ULTRA_USER_TRIAL**

## Read in this order

1. `evidence/FINAL_HOTFIX_RESULTS.md` — what was fixed and the final verdict
2. `evidence/FINAL_FINDINGS_REVALIDATION.md` — B1..B6 verdicts with evidence
3. `evidence/FINAL_TRACE_MAPPING.md` — what each comparison actually compares
4. `evidence/VISIBLE_UI_TRACE_FINAL.json` — the post-fix trace
5. `evidence/TEST_RESULTS.md` — the regression run
6. `evidence/CHANGED_FILES.txt` — every file touched
7. `evidence/OVERNIGHT_RUN_LEDGER.jsonl` — the full run ledger, including the
   recorded host-shutdown interruption

## Contents

| folder | contents |
|---|---|
| `source/backend` | FastAPI app, tests, data |
| `source/frontend` | React/Vite source, config, assets |
| `source/docs` | repository documentation |
| `evidence/` | final reports, traces, ledger, scenario evidence |
| `reports/` | the five autonomous lab cycles and the WorkBuddy revalidation |
| `screenshots/` | the 14 final Xiaomi 13 Ultra screenshots |

## Headline results

* **Final same-Xiamen trace: 18 steps, 0 failures, 0 console errors, one journey.**
* **Backend suite: 748 passed, 0 failed, 15 skipped.** Frontend build succeeds.
* **B1..B6 all closed.** B2/B3/B4/B5/B6 were reproduced in current code and fixed;
  B1 was an evidence gap, closed by generating the trace after the last edit.
* Two further real defects were found while revalidating: the stay calendar and
  the feasibility gate reserved *different* leg durations (so every hotel was
  falsely rejected), and the materialiser trusted stale adjacency facts.

## Honest limitations

* Public OSM/Overpass/Nominatim providers are intermittently unreachable from
  this network. The product reports that rather than fabricating data.
* OSM does not publish a "free" fact, so discovered attractions legitimately
  read 暂无价格; the 免费 state is proven by unit test.
* Provider pricing is frequently absent, so plan cards read 花费未知 rather than
  claiming a budget verdict.

## How to run

```
cd source/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

cd source/frontend
npm install
npm run dev -- --host 127.0.0.1
```

No secrets are included; provider keys are read from the environment.
