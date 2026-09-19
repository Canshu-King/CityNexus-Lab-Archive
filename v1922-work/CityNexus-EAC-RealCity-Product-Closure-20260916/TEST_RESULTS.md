# TEST_RESULTS.md — CityNexus Real-City Product Closure

All numbers are from real runs in this round.

## Environment

| Item | Value |
| --- | --- |
| Backend | uvicorn 127.0.0.1:8000, live credentials + live providers |
| Frontend | Vite 127.0.0.1:5173 |
| Browser | real Chrome via Playwright, 390x844 and 430x932 |
| AI | live DeepSeek key injected into the child process only |
| Providers | Overpass (mirror rotation), Nominatim, Photon, Open-Meteo |
| Acceptance journey | `89695905-f434-447b-9477-72abffc1903d`, `CN-XIAMEN` |

## 1. Same-journey proof — PASS

`evidence/SAME_JOURNEY_TRACE.json`:

```
journey_id              : 89695905-f434-447b-9477-72abffc1903d
distinct journey ids    : 1
single_journey_proven   : true
entries                 : 31
demo_reset_used         : false
```

Computed from the recorded entries, not asserted.

## 2. Real Xiamen chain — PASS

| Stage | Result |
| --- | --- |
| create | 201, `CN-XIAMEN` |
| live discovery | 6 real Xiamen POIs |
| candidates | 3 plans, stops 6 / 5 / 4 |
| select | 200 |
| start | ACTIVE |
| stay options | 4 provider-backed Xiamen hotels |
| stay select | 200 |
| itinerary | day-grouped stops rendered |
| map | renders from real coordinates |
| Copilot | answered, no enum |
| disruption → replan | `PRESENTED`, `locked_commitments_preserved = true` |
| accept | `ACCEPTED` |
| final state | new plan, 6 stops, recovery consistent |

## 3. Backend truth suites — PASS

```
tests/test_v192_shadow_trial_gate.py    61 passed
tests/test_v1923_final_code_gate.py     13 passed
tests/test_v1924_final_truth_gate.py    12 passed
tests/test_v1925_c4_interior_truth.py    7 passed
                                       -----------
                                        93 passed
```

## 4. Authoritative broad regression — PASS

Command: `python -m pytest tests/ -q -p no:cacheprovider`

| Run | Result |
| --- | --- |
| Before this round | 2 failed, 703 passed, 15 skipped |
| After this round | **2 failed, 703 passed, 15 skipped** |

```
new regressions : 0
remaining       : 2 (the same pre-existing contradictory pairs)
```

The two remaining failures are unchanged and pre-existing on the untouched
V19.2.1 baseline:
`test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]`
(contradicted by `test_v191_defect_d4_…`, which requires `max_m == 0`) and
`test_v19_char_d6b_hard_accessibility_need_does_not_block_planning` (contradicted
by the V19/V19.2 evidence-negative guards).

## 5. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 6. Browser sweep — PASS

| Viewport | Tabs rendered | Horizontal overflow | Real page errors |
| --- | --- | --- | --- |
| 390x844 | all | none | **0** |
| 430x932 | all | none | **0** |

Map-tile fetch failures (`tile.openstreetmap.org` is blocked on this network)
are excluded as environment noise; the map still renders route geometry and
markers from real coordinates.

## 7. Not run / not claimed

| Item | Why |
| --- | --- |
| Physical device | out of scope for this round |
| Xiaomi-like physical viewport | deferred; 390x844 and 430x932 were swept |
| Screenshot/barcode order import | scanner exists, not driven live this round |
| Real-world disruption feed | the disruption was injected through the product API |
| Multi-day >7-day itinerary | no journey in this environment exceeded three days |

## 8. Credential handling

The live `DEEPSEEK_API_KEY` was read from the user environment and injected into
the **child process only**. It is not printed, not written to any log, and not
present anywhere in this package. Only its presence is recorded.
