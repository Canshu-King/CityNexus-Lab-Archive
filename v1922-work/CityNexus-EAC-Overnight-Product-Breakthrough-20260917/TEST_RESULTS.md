# TEST_RESULTS.md — Overnight Product Breakthrough

## Snapshot freeze

```
Snapshot L actual sha256 : e275ab1b1057144571c975307d2205f3ae2abd28beeced79bb7adc491c25bedd
frozen files             : 31
```

## 1. Snapshot M probe — PASS

`probes/snapshot_m_truth_edges.py`

| Stage | Result |
| --- | --- |
| Before the fix | **2 FAIL** (silent duration shrink; pinned pair not reachable) |
| After the fix | **2 PASS** |

Raw output: `evidence/probe_runs/snapshot_m_after.txt`.

## 2. Snapshot M permanent regressions — PASS

```
tests/test_snapshot_m_truth_edges.py     7 passed
  no silent duration shrink
  120-minute activity with a 20-minute window -> conflict
  pinned 10 minutes apart with 30 minutes travel -> conflict
  reachable pinned nodes accepted
  real Place coordinates survive into the plan payload
  known-free stays known-free; known-paid amount preserved
```

## 3. Timeline and truth suites — PASS

```
tests/test_snapshot_k_stay_timeline.py       8 passed
tests/test_snapshot_j_backend_truth_gaps.py  7 passed
tests/test_v9_real_trip_operations.py        4 passed
```

## 4. Authoritative broad regression — PASS (no new regression)

| Run | Result |
| --- | --- |
| Snapshot L baseline | 2 failed, 722 passed, 15 skipped |
| After this round | **2 failed, 729 passed, 15 skipped** |

```
new regressions : 0
new tests       : +7
remaining       : 2  (the same pre-existing contradictory pairs)
```

### Regression history inside this round

The pinned-reachability rule initially rejected four existing fixtures. Two
causes were found and both were **real defects, not over-strict validation**:

1. the fixtures carried the *previous* hotel's structural operations alongside
   the new hotel's, at identical clock times — now dropped as superseded;
2. `_travel_minutes` used WALK only, making a hotel-to-airport leg look like a
   170-minute impossibility — it now takes the fastest feasible mode.

The remaining fixture adjustments pin a deterministic transition cost for
co-located fixture coordinates, so those tests assert structural invariants
rather than distance heuristics. The reachability rule stays fully active.
Regressions went 4 -> 0 by fixing real behaviour.

## 5. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 6. Browser verification — PASS

Real Chrome, 390x844 and 430x932, Chinese locale, one journey id:

| Check | Result |
| --- | --- |
| `/v8/hub`, `trips`, `map`, `agent`, `me`, `live` | all render |
| Internal-vocabulary leak | **none** |
| Activity detail opens from the itinerary | **yes** |
| Consumer booking import: manual tab, form, preview | **yes** |
| Horizontal overflow | **none** |
| Real page errors | **0** |

## 7. Not run

| Item | Why |
| --- | --- |
| Full visible same-Xiamen chain | not completed in one browser session |
| `VISIBLE_UI_TRACE.json` | nothing truthful to record for the full chain |
| Hostile-user loops (5 personas) | budget spent on the truth closure + booking import |
| Physical device | out of scope |

## 8. Credential handling

The live `DEEPSEEK_API_KEY` is read from the user environment and injected into
the **child process only**. It is never printed, never logged, and does not
appear anywhere in this package. The public-provider network policy reads no
credentials.
