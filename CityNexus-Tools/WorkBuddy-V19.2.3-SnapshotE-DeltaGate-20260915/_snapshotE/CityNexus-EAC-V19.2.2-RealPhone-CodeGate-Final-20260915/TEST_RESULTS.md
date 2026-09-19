# TEST_RESULTS.md — CityNexus V19.2.2 RealPhone Code Gate

All numbers below are copied from real test output produced by this round.
Nothing in this file is carried over from V18/V19/V19.1/V19.2.1 status prose.

## Environment

| Item | Value |
| --- | --- |
| Repository | `D:\moodle\CityNexus` |
| Branch | `eac/v19.2.2-realphone-codegate` |
| Baseline source | V19.2.1 RealPhone ShadowTrial Gate package (byte-identical to the pre-edit worktree) |
| Python | 3.12.14 (`D:\moodle\CityNexus\.venv`) |
| pytest | 8.4.2, `-p no:cacheprovider` |
| Database | throwaway SQLite in system temp / lab `evidence/_db` |
| AI | `CITYNEXUS_AI_ENABLED=false` for every deterministic run |

## 1. WorkBuddy V19.2 contract gate — PASS

```
tests/test_v192_shadow_trial_gate.py ............ 61 passed
```

Target was **61/61**. Baseline was **37 passed / 24 failed**.
Evidence: `evidence/v192_contract_run.txt`.

## 2. Authoritative broad backend regression — PASS

Command: `python -m pytest tests/ -q -p no:cacheprovider` (authoritative
`backend/tests` root only; no `_fresh_*`, `review/`, renderer snapshots or
extracted release packages are collected).

| Run | Result |
| --- | --- |
| Pristine V19.2.1 baseline | **41 failed, 632 passed, 15 skipped** |
| V19.2.2 working tree | **2 failed, 671 passed, 15 skipped** |

```
new regressions (in head, not in baseline): 0
previously failing tests fixed:            39
remaining failures:                         2  (both pre-existing, see below)
```

Evidence: `evidence/broad_regression_head.txt`,
`evidence/broad_regression_baseline_failures.txt`,
`evidence/broad_regression_head_failures.txt`.

### 2.1 The two remaining failures are mutually contradictory test pairs

Both fail on the untouched V19.2.1 baseline as well, and each is contradicted
by another test in the same repository. They cannot both be satisfied.

**(a) `test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]`**

* This test requires `MAX_WALKING_PER_LEG_M.params.max_m is None or >= 1`.
* `test_v191_defect_d4_walking_limit_is_parsed_with_its_value[走路不能超过 0 米-0]`
  requires `max_m == 0` for the same sentence.
* The two demands are mutually exclusive on one input.

Resolution chosen: preserve `max_m = 0` **and** set
`needs_clarification = true` with severity `STRONG`. This is the only option
that satisfies the upstream V19.2 contract
(`test_v192_defect_zero_metre_limit_is_not_authoritative` asserts
`not (max_m == 0 and not needs_clarification)`) while keeping
`test_v191_defect_d4` green. A zero-metre cap is therefore never treated as a
clean authoritative HARD cap.

**(b) `test_v19_char_d6b_hard_accessibility_need_does_not_block_planning`**

* This test requires the gate to **pass** for a `STEP_FREE_REQUIRED` HARD need
  against a Place whose accessibility evidence is `{}` (no evidence at all).
* `test_v19_traveler_capability.py::test_feasibility_blocks_unknown_and_conflicting_step_free_evidence`
  requires the gate to **fail** with `NEEDS_LIVE_EVIDENCE:p1` on exactly that
  fixture, and `test_v192_guard_route_without_evidence` requires the same
  evidence-negative behaviour for routes.
* Passing d6b would silently treat "unknown accessibility" as "accessible",
  which is the specific false-negative the V19/V19.2 safety model exists to
  prevent.

Resolution chosen: keep the evidence-negative behaviour (unknown is never
verified). d6b remains a documented pre-existing contradiction.

No other test in the repository regressed.

## 3. Focused capability / evidence guard suites

```
tests/test_v191_capability_contract.py
tests/test_v191_eac_evidence_scope.py
tests/test_v19_postfix_capability_contract.py
tests/test_v19_traveler_capability.py
-> 181 passed, 2 failed, 13 skipped
```

The only two failures are the contradictory pairs documented in §2.1.
Evidence: `evidence/guard_suites_run.txt`.

## 4. WorkBuddy red-team probes (independent tooling, run against snapshot D)

| Probe | Result |
| --- | --- |
| `v192_probe_p0_numeric.py` | `n1_violations 0/7`, `n2_n3_defects 0/6`, `n4` empty only for the genuine third-party denial |
| `v192_probe_capability_semantics.py` | **64/64 ok, 0 failing** |
| `v192_probe_stale_candidates.py` | `stale_candidate_refused`, `all_shapes_refused`, `stale_selected_plan_revalidation_raises` all true; `journey_still_running_on_expired_evidence` false |
| `v192_probe_c4_lifecycle.py` | `any_start_5xx false`, `one_confirmation_one_commitment true` |
| `v191_probe_c4_start.py` | `any_stranded false`, `stranded_roles []` |

Evidence: `evidence/p0_numeric_d.json`,
`evidence/capability_semantics_d.json`, `evidence/stale_candidates_d.json`,
`evidence/c4_lifecycle_d.json`, `evidence/c4_start_d.json`.

## 5. Acceptance matrix (generate -> select -> start)

| Case | generate | plans | select | start | journey |
| --- | --- | --- | --- | --- | --- |
| ARRIVAL C4 | 201 | 3 | 200 | 200 | ACTIVE |
| DEPARTURE C4 | 201 | 3 | 200 | 200 | ACTIVE |
| MID_TRIP C4 | 201 | 3 | 200 | 200 | ACTIVE |
| control (no reservation) | 201 | 3 | 200 | 200 | ACTIVE |

Evidence: `evidence/acceptance_matrix_d.json`.

## 6. Frontend build and contract guard

```
npm run build      -> ✓ built (vite 7.3.6), no errors
openapi parity     -> formal 137; runtime 137; missing 0; extra 0
```

## 7. Focused mobile trial (390x844 and 430x932)

| Flow | 390x844 | 430x932 |
| --- | --- | --- |
| C4 anchored journey (plans/select/start) | 3 / 200 / 200 | 3 / 200 / 200 |
| Mid-trip HARD recovery (panel + actions) | visible, replan+ack | visible, replan+ack |
| Stale evidence warning | start 409, panel visible | start 409, panel visible |
| GPS allowed | rendered, no overflow | rendered, no overflow |
| GPS denied | rendered, no overflow | rendered, no overflow |

Page errors: **0**. Horizontal overflow: **0**.
Evidence: `evidence/mobile_probe_d.json`.

## 8. Not performed / not claimed

* **No real payment** was executed at any point.
* **No physical-device testing** was performed. All mobile evidence is from
  emulated viewports in headless Chrome; it does not establish behaviour on
  real phone hardware, real GPS, or a real network.
* The DeepSeek semantic canary was not run: no live AI provider credentials are
  available in this environment, so `CITYNEXUS_AI_ENABLED=false` was used for
  every deterministic run. The conservative local fallback is what is verified
  here.
