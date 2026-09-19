# Regression List — V19.1 (C) → V19.2 (A)

Same test bytes in both snapshots (verified by `sha256`): `test_v191_capability_contract.py`
`b34f468d19bd`, `test_v19_postfix_capability_contract.py` `8443b73c72b2`,
`test_v191_eac_evidence_scope.py` `bec956d494e2`, `v191_harness.py` `66a17dd7f55e`.

| | V19.1 (C) | V19.2 (A) | V19.2 (B) |
|---|---|---|---|
| passed | 119 | **161** | **161** |
| failed | 54 | **14** | **14** |
| skipped | 15 | 13 | 13 |
| collected | 188 | 188 | 188 |

By unique test function: **22 failing → 9 failing**; **13 fixed, 1 regressed, 8 still failing**.

Command (identical for every snapshot):

```
cd <snapshot>/backend
CITYNEXUS_DATABASE_URL="sqlite:///<lab>/evidence/_db/pytest_<label>.db" \
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_v191_capability_contract.py \
  tests/test_v19_postfix_capability_contract.py \
  tests/test_v191_eac_evidence_scope.py \
  -q --no-header -p no:cacheprovider
```

---

## FIXED in V19.2 (13 test functions)

| Test function | What it covers |
|---|---|
| `test_v191_defect_d2b_denial_hearsay_speculation_creates_no_hard_need` | denial / hearsay / speculation must not create HARD |
| `test_v191_defect_d4_distinct_values_do_not_collapse` | duplicate codes with distinct values survive |
| `test_v191_defect_d4_km_form_is_converted_or_rejected` | `1 km` handling |
| `test_v191_defect_d4_walking_limit_is_parsed_with_its_value` | walking limit keeps its number |
| `test_v191_defect_d7_permanent_language_selects_traveler_scope` | `终身` → TRAVELER |
| `test_v191_defect_d7_scope_is_distinguishable_from_language` | scope ≠ language |
| `test_v191_eac_defect_denial_does_not_create_need` | `I don't need a wheelchair` |
| `test_v191_eac_defect_facility_description_is_not_a_need` | `the station has an accessible toilet` |
| **`test_v191_eac_defect_merge_respects_scope`** | **the V19.1 cross-scope dedup regression — now closed** |
| `test_v191_eac_defect_sequence_tag_values_are_not_dropped_by_normalizer` | list/tuple tag values |
| `test_v191_eac_defect_speculation_does_not_create_hard` | `说不定…` / `if I end up…` |
| `test_v191_eac_defect_third_party_does_not_create_need` | `my friend needs a wheelchair, not me` |
| `test_v19_char_d4b_numeric_walking_limit_keeps_its_value` | numeric walking limit |
| `test_v19_char_d7a_language_can_select_traveler_scope` | TRAVELER scope from language |

The single most important one is `test_v191_eac_defect_merge_respects_scope`: that was the **only
regression** the V19.1 round found in Codex's tree, and it is now fixed.

## REGRESSED in V19.2 (1 test function)

| Test | Why it now fails |
|---|---|
| `test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]` | V19.2 added `不能超过` to the walking trigger list, so `走路不能超过 0 米` now yields `MAX_WALKING_PER_LEG_M HARD {'max_m': 0, 'needs_clarification': False}`. In V19.1 the trigger did not exist, nothing was produced, and the test passed vacuously |

This is the same root cause as the `1.5 公里 → 1` corruption: V19.2 made a code path reachable
that was previously dead, and the newly reachable path is defective. See
`NUMERIC_TIME_BOUNDARY_RESULTS.md`.

## STILL_REPRODUCIBLE (8 test functions)

| Test function | Underlying defect | Evidence |
|---|---|---|
| `test_v191_defect_d5_rest_and_nap_windows_are_extracted` (4 cases) | rest / nap window extraction incomplete | `capability_semantics_a.json` → `G4_nap` FAIL |
| `test_v191_defect_d5_window_params_are_well_formed` (2 cases) | window params not well formed for these phrasings | same |
| `test_v191_defect_d7_this_trip_language_selects_journey_scope[just for today I cannot walk far]` | this-trip language not always selecting JOURNEY | `capability_semantics_a.json` → G2 |
| `test_v191_eac_defect_step_evidence_contradiction_is_conflict[tags1]` | `steps: yes` beside `wheelchair=yes` is not CONFLICT | `G3_contradiction` 5/7 |
| `test_v191_eac_defect_top_level_step_free_verified_is_seen` | `_accessibility_metadata` whitelist gap | `PATCH_VALIDATION.md` |
| `test_v19_char_d4a_hard_care_and_limit_statements_are_extracted` (2 cases) | care/limit extraction for those phrasings | `G4_nap` |
| `test_v19_char_d6b_hard_accessibility_need_does_not_block_planning` | fails on both C and A — **policy question, not a V19.2 regression**. V19.2's fail-closed stance means a HARD need without VERIFIED evidence does block planning; this test encodes the opposite expectation | `lifecycle_a.json` → `evidence_matrix` |
| `test_v19_char_d6c_gate_consults_accessibility_evidence` | **STALE_TEST** — it greps `feasibility.py` for the literal `accessibility_state(`, which V19.1 replaced with `evaluate_accessibility_requirement(code, metadata)`. The behaviour it intends to check is covered by `evidence_matrix` | V19.1 round already classified this |

## New defects not covered by any existing test

These were found by this round's probes and have **no** test in the suite yet. They are the
content of `patches/V19_2_TESTS_ONLY.patch`:

| Defect | Probe |
|---|---|
| decimal walking limits corrupted by the clause splitter (`1.5 公里` → 1) | `v192_probe_p0_numeric.py` → `n2_n3_decimal` 6/6 |
| minutes value becomes a metres cap (`连续走不能超过 20 分钟` → `max_m: 20`) | `n1_unit_confusion` 3 violations |
| daily cap double-counted as a per-leg cap | `n1_unit_confusion` |
| first-person hedged needs silently dropped (`if possible I need step-free access`) | `n4_filtering` |
| companion journey needs dropped (`我妈妈要午休`) | `n4_filtering` |
| `evidence_status: VERIFIED` ignored → 422 | `lifecycle_a.json` |
| journey can start on expired evidence | `stale_candidates_a.json` |
| mid-trip HARD need produces no replan and no review prompt | `lifecycle_a.json` |
| C4 anchor blocks all planning | `c4_lifecycle_a.json` |

## Guard list — nothing broke

No test that was passing for a *guard* reason broke in V19.2. Specifically still holding:
HARD accessibility cannot be downgraded; facility tags never verify step-free; route without route
evidence stays unknown; list/tuple tag shapes survive; explicit step-free assertions verify;
reversed time windows are rejected; C4 confirmation idempotency; OpenAPI parity; stale candidates
are refused; the active plan is not silently rewritten mid-trip; Hermes exposes no capability
write tool.
