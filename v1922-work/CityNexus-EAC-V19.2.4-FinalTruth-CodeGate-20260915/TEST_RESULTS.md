# TEST_RESULTS.md — CityNexus V19.2.4 Final Truth Code Gate

Every number is copied from real output produced by this round.

## Environment

| Item | Value |
| --- | --- |
| Repository | `D:\moodle\CityNexus` |
| Snapshot F | `CityNexus-EAC-V19.2.3-FinalShadowTrial-CodeGate-20260915.zip`, frozen with a SHA-256 manifest (`evidence/SNAPSHOT_F_SOURCE_MANIFEST.json`) |
| Declared baseline | V19.2.1, explicitly normalised to LF |
| Python / pytest | 3.12.14 / 8.4.2, `-p no:cacheprovider` |
| AI | `CITYNEXUS_AI_ENABLED=false`; no canary this round (no semantic code changed) |

## 1. Gate suites — PASS

```
tests/test_v192_shadow_trial_gate.py   61 passed   (V19.2 contract)
tests/test_v1923_final_code_gate.py    13 passed   (V19.2.3 closure)
tests/test_v1924_final_truth_gate.py   12 passed   (V19.2.4 closure)
                                      -----------
                                       86 passed
```

Evidence: `evidence/gate_suites_run.txt`.

## 2. Shared-gate truth probe — PASS 4/4

`probes/v1924_truth_probe.py` (independent, shipped in the Road-Prep), executed
against the final tree with `CITYNEXUS_TREE=D:\moodle\CityNexus\backend`:

```
F01_prearrival              passed=false  C4_ACTIVITY_BEFORE_ARRIVAL:p        PASS
F02_postdeparture           passed=false  C4_ACTIVITY_AFTER_DEPARTURE:p       PASS
F03_arrival_after_departure passed=false  C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE   PASS
F04_control                 passed=true   []                                  PASS
```

Exit code 0. Evidence: `evidence/v1924_truth_probe.json`.

## 3. Authoritative broad backend regression — PASS

Command: `python -m pytest tests/ -q -p no:cacheprovider`.

| Run | Result |
| --- | --- |
| Snapshot F (V19.2.3) | 2 failed, 684 passed, 15 skipped |
| V19.2.4 | **2 failed, 696 passed, 15 skipped** |

```
new regressions : 0
net change      : +12 passing (the new V19.2.4 tests)
remaining       : 2 (the same pre-existing contradictory pairs)
```

Evidence: `evidence/broad_regression_head.txt`,
`evidence/broad_regression_failures.txt`.

### 3.1 The two remaining failures

Unchanged from the independent review and present on the untouched V19.2.1
baseline:

* `test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]`
  requires `max_m is None or >= 1`, while
  `test_v191_defect_d4_walking_limit_is_parsed_with_its_value[走路不能超过 0 米-0]`
  requires `max_m == 0` — mutually exclusive on one input.
* `test_v19_char_d6b_hard_accessibility_need_does_not_block_planning` requires
  the gate to pass with **no** accessibility evidence, contradicting the V19/V19.2
  evidence-negative guards.

Per the Road-Prep these obsolete expectations are a test-maintenance item.
Production truth was not weakened to satisfy them.

## 4. OpenAPI — PASS

```
OpenAPI 3.1.0; formal 138; runtime 138; missing 0; extra 0
```

Evidence: `evidence/openapi_parity.txt`.

## 5. Frontend build — PASS

```
npm run build  ->  ✓ built (vite 7.3.6), no errors
```

## 6. Targeted mobile flows — PASS 18/18

Both mandated viewports (390x844, 430x932), nine flows each:
ARRIVAL boundary, DEPARTURE boundary, mid-trip HARD recovery, acknowledge
warning, no-alternative, feasible replacement resolves, stale candidate
warning, GPS allowed, GPS denied.

```
page errors         : 0
horizontal overflow : 0
abnormal flows      : 0 / 18
```

Evidence: `evidence/mobile_v1924_d.json`.

## 7. Live DeepSeek canary — deliberately NOT run

The EAC task allows one bounded canary **only if semantic code changed**. This
round changed `feasibility.py`, `hard_recovery.py`, `main.py` and
`reservation_identity.py` only; no semantic/AI code was touched. A live call was
therefore not spent, and no canary pass is claimed for V19.2.4. The most recent
live evidence remains the V19.2.3 canary
(`LIVE_DEEPSEEK_CANARY_PASSED`, live == local on all three inputs).

## 8. Not performed / not claimed

* **No real payment.**
* **No physical-device testing.** All mobile evidence is emulated viewports in
  headless Chrome.
* Per the Road-Prep execution order an independent Snapshot-F/G red-team and a
  physical-device precheck still follow this code gate.
