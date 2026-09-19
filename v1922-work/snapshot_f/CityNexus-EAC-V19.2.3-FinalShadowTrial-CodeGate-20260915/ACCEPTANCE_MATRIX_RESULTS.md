# ACCEPTANCE_MATRIX_RESULTS.md — V19.2.3 gate-by-gate

Every row is backed by executable evidence produced this round.

| ID | Gate | Required result | Result | Evidence |
| --- | --- | --- | --- | --- |
| T01 | ARRIVAL temporal boundary | no flexible activity starts before ARRIVAL | **PASS** | `tests/test_v1923_final_code_gate.py::test_v1923_arrival_is_a_lower_temporal_boundary`; mobile `ARRIVAL_BOUNDARY` |
| T02 | DEPARTURE temporal boundary | no flexible activity ends after DEPARTURE | **PASS** | `...departure_is_an_upper_temporal_boundary`; mobile `DEPARTURE_BOUNDARY` |
| T03 | MID_TRIP pinned anchor | anchor at committed time, surrounding POIs feasible | **PASS** | `...multi_anchor_ordering_is_monotonic` |
| T04 | multiple C4 anchors | chronological, routable, no impossible overlap | **PASS** | same test; `validate_anchor_timeline` overlap branch |
| T05 | impossible anchor combination | precise conflict, no fabricated plan | **PASS** | `...arrival_after_departure_is_a_precise_conflict` (422 + `C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE`, 0 plans) |
| R01 | HARD recovery acknowledgement | cannot hide/clear unsafe truth client-only | **PASS** | `...acknowledge_never_resolves_or_hides_recovery`; mobile `ACKNOWLEDGE_WARNING` |
| R02 | feasible replacement selected | Event resolves; flags/UI agree | **PASS** | `...feasible_replacement_resolves_recovery`; mobile `FEASIBLE_REPLACEMENT_RESOLVES` |
| R03 | no alternative | durable explicit NO_ALTERNATIVE after attempted replan | **PASS** | `...zero_alternatives_persists_explicit_no_alternative`; mobile `NO_ALTERNATIVE` |
| R04 | C4 preservation during recovery | all active C4 remain protected | **PASS** | `...c4_is_preserved_through_recovery` |
| S01 | stale candidate list | flagged/filtered, not an ordinary candidate | **PASS** | `...stale_candidate_is_flagged_and_not_selectable`; mobile `STALE_CANDIDATE_WARNING` |
| S02 | stale start | `/start` stays blocked with 409 | **PASS** | `...stale_start_stays_blocked`; mobile `start_status = 409` |
| D01 | legacy duplicate DB migration | detected and migrated, no silent index failure | **PASS** | `...duplicate_confirmation_refs_are_migrated` (subprocess, real legacy DB) |
| D02 | post-migration uniqueness | uniqueness actually exists/enforces | **PASS** | same test: index present, duplicate insert rejected |
| D03 | concurrent confirm | one reservation/C4, loser deterministic, no 500 | **PASS** | threaded probe: 1 reservation, 1 C4, no 5xx |
| P01 | clean patch apply | `git apply --check` on the exact clean baseline | **PASS** | `patches/V19_2_3_CODE.patch`, no excluded paths |
| P02 | release hygiene | no junk; changed-files list truthful | **PASS** | `PATCH_RESULTS.md`; `CHANGED_FILES.txt` generated from the real diff |
| G01 | V19.2 contract suite | all non-obsolete gate tests pass | **PASS** | 61/61 |
| G02 | broad backend | zero new regressions | **PASS** | 684 passed / 2 pre-existing contradictory / 15 skipped; 0 new |
| G03 | frontend build | pass | **PASS** | `npm run build` -> ✓ built |
| G04 | OpenAPI | runtime/contract parity; changed schemas aligned | **PASS** | formal 138 / runtime 138 / missing 0 / extra 0 |
| G05 | mobile delta | 390x844 + 430x932 flows pass | **PASS** | 18/18 flows, 0 page errors, 0 overflow |
| A01 | DeepSeek canary | one live canary if configured | **PASS** | `LIVE_DEEPSEEK_CANARY_PASSED`, live == local on 3 inputs |

## Summary

`22 / 22 PASS` -> verdict `SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE`.

The only outstanding gate is physical-device trial, which cannot be performed
in this environment and is not claimed.
