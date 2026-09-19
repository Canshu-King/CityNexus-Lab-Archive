# TEST_RESULTS.md — Final Consumer Truth + UX Closure

## Environment

| Item | Value |
| --- | --- |
| Backend | uvicorn 127.0.0.1:8000, live credentials injected into the child process only |
| Live providers | Overpass (mirror rotation), Nominatim, Photon, Open-Meteo, DeepSeek key present |
| Frontend | Vite 127.0.0.1:5173 |
| Browser | real Chrome via Playwright, 390x844 and 430x932 |
| Live acceptance journey | `abd8ed7b-585e-4bfd-bddc-83d45cdc4975` (`CN-XIAMEN`) — T1 |
| | `0db2081a-…` / `89695905-…` — T2 evidence runs |

## 1. New truth-blocker suites — PASS

```
tests/test_final_consumer_truth_blockers.py    4 passed
```

## 2. Existing truth suites — PASS

```
test_v192_shadow_trial_gate.py      61
test_v1923_final_code_gate.py       13
test_v1924_final_truth_gate.py      12
test_v1925_c4_interior_truth.py      7
                                   ---
                                    93 passed
```

## 3. Authoritative broad regression — PASS (no new regression)

```
python -m pytest tests/ -q
```

| Run | Result |
| --- | --- |
| Snapshot I baseline | 2 failed, 703 passed, 15 skipped |
| After this round | **2 failed, 707 passed, 15 skipped** |

```
new regressions : 0
new tests       : 4  (the truth-blocker suite)
remaining       : 2  (the same pre-existing contradictory pairs)
```

The two failures are unchanged from the untouched V19.2.1 baseline:
`test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]`
(contradicted by `test_v191_defect_d4_…`, which requires `max_m == 0`) and
`test_v19_char_d6b_hard_accessibility_need_does_not_block_planning`.

### Regression history this round

An early version of the new test module used `importlib.reload` to isolate its
database. That poisoned the shared pytest process and produced **99 failures**.
The module now uses one shared process-wide database with per-run unique ids,
which is what the rest of the suite does:
**99 -> 10 -> 0** new regressions.

## 4. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 5. Live Xiamen runs driven this round

| Flow | Result |
| --- | --- |
| create Xiamen journey | 201, `CN-XIAMEN` |
| live provider discovery | 6 real Xiamen POIs materialised |
| generate candidates | 3 plans (6 / 5 / 4 stops) |
| select plan | 200 |
| start | ACTIVE |
| stay offers + options | 4 provider-backed Xiamen hotels |
| **select stay (T1)** | **PASSED — 6 POIs preserved, 2 nights inserted, anchors pinned** |
| **CLOSURE on mutable POI (T2)** | **material `removed=1`, PRESENTED** |
| **CLOSURE on protected stay (T2)** | **honest refusal, no fake repair** |

## 6. Not run this round

| Item | Why |
| --- | --- |
| Visible-UI same-journey acceptance run | see REMAINING_PRODUCT_GAPS.md — not completed |
| `VISIBLE_UI_TRACE.json` | the driven chain was backend + targeted UI, not the full canonical 22-step run |
| Consumer order import | not built |
| Activity detail screen | not built |
| Copilot product cleanup | not built |
| Visual product pass | not built |
| Physical device | out of scope |

## 7. Credential handling

The live `DEEPSEEK_API_KEY` was read from the user environment and injected into
the **child process only**. It is not printed, not written to any log, and does
not appear anywhere in this package.
