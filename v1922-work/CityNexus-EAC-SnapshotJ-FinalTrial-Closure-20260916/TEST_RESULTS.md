# TEST_RESULTS.md — Snapshot J Final Trial Closure

## Environment

| Item | Value |
| --- | --- |
| Backend | uvicorn 127.0.0.1:8000, live credentials injected into the child process only |
| Live providers | Overpass, Nominatim, Photon, Open-Meteo, DeepSeek key present |
| Frontend | Vite 127.0.0.1:5173 |
| Snapshot J | `ae9d04c1…f405e17` — matches the Road-Prep SHA-256 exactly |

## 1. New Snapshot J backend suites — PASS

```
tests/test_snapshot_j_backend_truth_gaps.py     7 passed
  B1 structural survival        x3
  B2 locked-time preservation   x2
  B3 precise replan reason      x1
  B4 ambiguous target           x1
```

Plus the Snapshot J T1/T2 suites still green:

```
tests/test_final_consumer_truth_blockers.py     4 passed
```

## 2. Existing truth suites — PASS

```
test_v192_shadow_trial_gate.py      61
test_v1923_final_code_gate.py       13
test_v1924_final_truth_gate.py      12
test_v1925_c4_interior_truth.py      7
test_v8_stay_mobility.py            29
                                   ---
                                   122 passed
```

## 3. Authoritative broad regression — PASS (no new regression)

```
python -m pytest tests/ -q
```

| Run | Result |
| --- | --- |
| Snapshot J baseline | 2 failed, 707 passed, 15 skipped |
| After this round | **2 failed, 714 passed, 15 skipped** |

```
new regressions : 0
new tests       : +7  (all passing)
remaining       : 2   (the same pre-existing contradictory pairs)
```

The two failures are unchanged from the untouched V19.2.1 baseline:
`test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]`
and `test_v19_char_d6b_hard_accessibility_need_does_not_block_planning`.

### Regression history inside this round

The first B4 implementation removed the execution-position fallback entirely.
That broke five pre-existing replan tests (they drive a *started* journey and
send a target-less CLOSURE). The policy was refined: the execution position is
grounded truth and is kept; only "pick the first non-terminal activity" — the
actual guess — is forbidden. Regressions went 5 -> 0.

## 4. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 5. Offline verification harnesses built this round

Live Overpass retrieval was intermittent (ConnectTimeout on the public mirrors),
so the stay/identity work was verified with deterministic offline harnesses
instead of long network retries:

| Harness | Purpose |
| --- | --- |
| `b5_fixture.py` | builds a Xiamen journey with real POIs in one second, no network |
| `b5_offline.py` | materialises a stay and prints every activity's `semantic_key` |
| `b5_probe2.py` | closes a mutable POI on the stay plan and reports the outcome |

## 6. Not run this round

| Item | Why |
| --- | --- |
| Full canonical visible-UI run | see REMAINING_PRODUCT_GAPS.md |
| `VISIBLE_UI_TRACE.json` | the canonical browser run was not completed |
| Live B5 end-to-end acceptance | live provider retrieval was intermittent |
| Consumer order import / activity detail / Copilot cleanup / visual pass | not built |

## 7. Credential handling

The live `DEEPSEEK_API_KEY` was read from the user environment and injected into
the **child process only**. It is never printed, never written to a log, and
does not appear anywhere in this package.
