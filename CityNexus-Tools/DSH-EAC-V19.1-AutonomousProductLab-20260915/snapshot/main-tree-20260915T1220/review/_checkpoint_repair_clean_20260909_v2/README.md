# CityNexus WP03 correctness-repair checkpoint

Date: 2026-09-09  
Contract: `CityNexus_MVP_Implementation_Blueprint_v0.1.zip`  
Repair instruction applied: `contract-source/WP03_REPAIR_INSTRUCTION.md`

This package contains the executable WP00-WP03 implementation with the WP03
correctness repair applied. Repository-relative paths are preserved at the
package root: `backend/`, `contracts/`, `data/mock/`, `scripts/` and
`docs/implementation/`.

Scope stops after WP03. WP04 booking/payment, WP05 execution, WP06 replanning,
AI, frontend, Visio and real network providers remain deferred.

## Gate result

- Backend tests: 41 passed.
- Ruff check: PASS.
- Ruff format check: PASS.
- `git diff --check`: PASS.
- Canonical reset/seed and plan generation remain deterministic and fixture-only.
- Canonical generation returns three feasible candidates; canonical selection
  leaves Journey `PLANNED` and the selected PlanVersion `SELECTED`.

## Run from this package root

Use Python 3.12+ with dependencies from `backend/pyproject.toml`:

```powershell
$env:PYTHONPATH='backend'
python -m pytest -q backend/tests
ruff check --config backend/pyproject.toml backend scripts
ruff format --check --config backend/pyproject.toml backend scripts
python scripts/reset_demo.py
```

The API can be started with:

```powershell
$env:PYTHONPATH='backend'
uvicorn app.main:app --app-dir backend
```

No runtime network provider is required. The authoritative gate is
`backend/app/replanning/feasibility.py`; it is called before initial candidate
scoring/persistence and again immediately before plan selection.
