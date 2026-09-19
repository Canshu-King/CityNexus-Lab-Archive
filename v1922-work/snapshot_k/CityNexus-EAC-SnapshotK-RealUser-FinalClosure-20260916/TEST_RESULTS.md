# TEST_RESULTS.md — Snapshot K Real-User Final Closure

## Snapshot freeze

```
Snapshot K candidate sha256 : ceff17993b765d53fe6cd1de7c571588ab43a04140c48c2a3b14173278cf6472
Road-Prep expected          : ceff17993b765d53fe6cd1de7c571588ab43a04140c48c2a3b14173278cf6472
MATCH                       : True
```

## 1. The Road-Prep probe — PASS

`probes/snapshot_k_stay_timeline_probe.py`

| Stage | Result |
| --- | --- |
| Before the fix | **2 FAIL** (CHECK_IN after first STAY; flexible overlaps locked) |
| After the fix | **2 PASS** |

## 2. New Snapshot K suite — PASS

```
tests/test_snapshot_k_stay_timeline.py     8 passed
  all ten STAY_TIMELINE_TRUTH invariants + POI survival
tests/test_snapshot_j_backend_truth_gaps.py  7 passed
  (B1-B4 still green after the calendar rewrite)
```

## 3. Existing truth suites — PASS

```
test_v192_shadow_trial_gate.py      61
test_v1923_final_code_gate.py       13
test_v1924_final_truth_gate.py      12
test_v1925_c4_interior_truth.py      7
test_final_consumer_truth_blockers.py 4
```

## 4. Authoritative broad regression — PASS (no new regression)

| Run | Result |
| --- | --- |
| Snapshot J baseline | 2 failed, 714 passed, 15 skipped |
| After this round | **2 failed, 722 passed, 15 skipped** |

```
new regressions : 0
new tests       : +8
remaining       : 2  (the same pre-existing contradictory pairs)
```

The two failures are unchanged from the untouched V19.2.1 baseline.

### Regression history inside this round

The tightened disruption-target policy initially broke five pre-existing tests
that posted a target-less CLOSURE on a started journey. Four were updated to
assert `payload.at_current_location` (the grounding a reporter actually
provides); `test_aav2_02` was updated to assert the stronger property that an
ungrounded retry is refused. Regressions went 5 -> 0 without weakening any
assertion: each of them still fails if the system guesses a target.

## 5. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 6. Browser sweep — PASS

Real Chrome, 390x844 and 430x932, Chinese locale, one journey id:

| Check | Result |
| --- | --- |
| `/v8/hub`, `trips`, `map`, `agent`, `me`, `live` | all render |
| Internal-vocabulary leak | **none** |
| Activity detail opens from the itinerary | **yes** |
| Back to itinerary | **yes** |
| Horizontal overflow | **none** |
| Real page errors | **0** |

Map-tile fetch failures are excluded as environment noise
(`tile.openstreetmap.org` is blocked on this network).

## 7. Not run

| Item | Why |
| --- | --- |
| Full visible create → plan → hotel → import → accept chain | not driven; see PRODUCT_RESULTS.md |
| `VISIBLE_UI_TRACE.json` | nothing truthful to record for the full chain |
| Physical device | out of scope |
| Live B5 end-to-end | live provider retrieval was intermittent |

## 8. Credential handling

The live `DEEPSEEK_API_KEY` was read from the user environment and injected into
the **child process only**. It is never printed, never logged, and does not
appear anywhere in this package.
