# TEST_RESULTS — final hotfix round

Generated: 2026-09-17T18:52:38.157325+08:00
Interpreter: D:\moodle\CityNexus\.venv\Scripts\python.exe (Python 3.12.14)
Command: `cd backend && python -m pytest -q`

```
748 passed, 15 skipped, 2 warnings in 66.58s
```

## Focused suites run for this round

| Suite | Purpose | Result |
|---|---|---|
| `tests/test_final_hotfix_cost_and_routes.py` | three truthful price states + unknown-is-not-free | 9 passed |
| `tests/test_v1922_six_fix_regressions.py` | the six earlier overnight fixes | 6 passed |
| `tests/test_snapshot_m_truth_edges.py` | pinned truth, duration preservation, timezone | 9 passed |
| `tests/test_v13_1_2_structural_anchor_integrity.py` | C4 anchor integrity | 5 passed |
| `tests/test_v191_capability_contract.py`, `test_v191_eac_evidence_scope.py`, `test_v19_postfix_capability_contract.py` | capability truth reconciliation | 174 passed, 13 skipped |

## Frontend

`cd frontend && npx vite build` -> `✓ built in 6.10s` (no errors).

## Notes

* The 15 skips are pre-existing provider-evidence adapters that require a
  network fixture and are skipped on this tree by design.
* Two repository tests that directly contradicted the truth rules were
  reconciled toward the rule rather than the rule being weakened:
  `test_v19_char_d6b_*` (missing accessibility evidence must not pass as
  accessible) and the 0 m walking-cap case (a nonsense cap must not be
  persisted as a usable `max_m`; the stated value is kept as `stated_m`).
