# TEST_RESULTS.md — Snapshot L Consumer-Ship Closure

## Snapshot freeze

```
Snapshot K actual sha256 : d45accfac6b5f172f774055470ed942d3cedcccac473d1db5477fa2ca36d4360
Road-Prep expected       : d45accfac6b5f172f774055470ed942d3cedcccac473d1db5477fa2ca36d4360
MATCH                    : True
```

## 1. The Road-Prep probe — PASS

`probes/snapshot_l_scheduler_edges.py`

| Stage | Result |
| --- | --- |
| Before the fix | **3 FAIL** |
| After the fix | **3 PASS** |

Raw output in `evidence/probe_runs/snapshot_l_after.txt`.

## 2. Timeline suites — PASS

```
tests/test_snapshot_k_stay_timeline.py       8 passed
tests/test_snapshot_j_backend_truth_gaps.py  7 passed
tests/test_v9_real_trip_operations.py        4 passed
```

All ten `STAY_CALENDAR_V2` invariants remain green after the rewrite.

## 3. Authoritative broad regression — PASS (no new regression)

| Run | Result |
| --- | --- |
| Snapshot K baseline | 2 failed, 722 passed, 15 skipped |
| After this round | **2 failed, 722 passed, 15 skipped** |

```
new regressions : 0
remaining       : 2  (the same pre-existing contradictory pairs)
```

### Regression history inside this round

The first Calendar V2 draft rejected the Tianjin flagship fixture with
`STAY_PINNED_CONFLICT:PINNED_OVERLAP:luggage-drop`. Investigation showed this
was **not** an over-strict check: the fixture legitimately carried the *previous*
hotel's luggage-drop alongside the new hotel's, both at 09:00. The calendar now
drops structural operations belonging to a superseded property
(`_offer_of()`), which is the correct product behaviour, and the flagship test
passes again. Regressions went 1 -> 0 by fixing a real defect rather than by
weakening the new validation.

## 4. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 5. Browser sweep — PASS

Real Chrome, 390x844 and 430x932, Chinese locale, one journey id:

| Check | Result |
| --- | --- |
| `/v8/hub`, `trips`, `map`, `agent`, `me`, `live` | all render |
| Internal-vocabulary leak | **none** |
| Activity detail opens from the itinerary | **yes** |
| Back to itinerary | **yes** |
| Horizontal overflow | **none** |
| Real page errors | **0** |

## 6. Not run

| Item | Why |
| --- | --- |
| Full visible create → plan → hotel → import → accept chain | not driven this round |
| `VISIBLE_UI_TRACE.json` | nothing truthful to record for the full chain |
| Consumer booking import | not built |
| Physical device | out of scope |

## 7. Credential handling

The live `DEEPSEEK_API_KEY` is read from the user environment and injected into
the **child process only**. It is never printed, never logged, and does not
appear anywhere in this package. The new network policy reads no credentials and
records only the resolved mode (`auto` / `env_proxy` / `direct`).
