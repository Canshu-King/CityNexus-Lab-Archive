# TEST_RESULTS.md — CityNexus-EAC-Review-20260918

Round: CityNexus-EAC-Xiaomi-Trial-Final-Hotfix-v2
Date:  2026-09-18
Python: 3.12.14  (D:\moodle\CityNexus\.venv\Scripts\python.exe)
Runner: pytest, `-p no:randomly` (deterministic order)

## 1. Full backend suite

```
$ python -m pytest -q -p no:randomly
762 passed, 15 skipped, 2 warnings in 85.73s (0:01:25)
```

Baseline before this package's changes was 759 passed / 15 skipped.
This package adds 3 tests (the R1-d physical-identity tests) -> 762.

The 15 skips are pre-existing environment-conditional skips (live provider
credentials not configured in this offline run). No test was skipped,
deleted, weakened or marked xfail to make this package pass.

## 2. The tests added by this package (R1-d)

`backend/tests/test_hotfix_v2_closure_truth.py` — 14 tests, all passing:

```
test_null_protected_activity_id_cannot_protect_an_unrelated_poi   PASSED
test_null_commitment_id_does_not_match_a_null_closure_target      PASSED
test_real_protected_activity_still_blocks                         PASSED
test_named_venue_resolves_deterministically                       PASSED
test_exact_name_beats_a_partial_match                             PASSED
test_ambiguous_named_venue_is_not_guessed                         PASSED
test_unknown_named_venue_matches_nothing                          PASSED
test_named_venue_query_reads_the_expected_payload_keys            PASSED
test_opaque_place_ids_sharing_a_prefix_are_not_one_venue          PASSED
test_check_in_and_its_night_are_one_venue                         PASSED
test_reserved_leg_time_matches_the_gate_for_unrelated_places      PASSED
test_wrapper_and_provider_row_are_one_venue                       PASSED   <- NEW
test_closed_venue_is_not_its_own_replacement                      PASSED   <- NEW
test_occupied_venue_is_not_reused_under_another_id                PASSED   <- NEW
```

The three new tests fail against the previous code (id-equality exclusion) and
pass with `is_same_physical_venue`. `test_closed_venue_is_not_its_own_replacement`
reproduces the exact production data: the domain wrapper
`e1ced246-e238-5e48-a816-1b82e8b2953c`
(`CN-XIAMEN:real-place-07e7689756fa27109a8bff96`, 24.4581979/118.0689473) and the
provider row `real-place-07e7689756fa27109a8bff96` (`overpass:node/1588295483`,
identical coordinates).

## 3. Adjacent engine tests (no regression)

```
$ python -m pytest tests/test_hotfix_v2_closure_truth.py \
                   tests/test_mock_replan_engine_next.py -v -p no:randomly
15 passed, 2 warnings in 1.26s
```

## 4. Frontend

No frontend file was changed by this package, so no frontend regression surface
was touched. The frontend had been verified `npx vite build` clean earlier in
the round.

## 5. Known failing behaviour (NOT a test failure) — see MOCK_MOBILITY_LIMITATION.md

A real-user closure replan on a live-discovered city returns HTTP 422
`ACTIVITY_OVERLAP, INSUFFICIENT_TRAVEL_GAP:...`. This is the deterministic gate
correctly refusing an infeasible proposal. The cause is upstream: the replan
estimator prices every new leg at the mock fixture's constant
`default_minutes = 20`. This package documents the root cause and does NOT fix
it (out of scope for the evidence-correction package).

Raw log: `FULL_SUITE_762_PASSED.txt`
