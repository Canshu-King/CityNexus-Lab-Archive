# CityNexus MVP pre-WP04 minimal-repair checkpoint

Date: 2026-09-09  
Contract: `CityNexus_MVP_Implementation_Blueprint_v0.1.zip`  
Instruction applied: `contract-source/PRE_WP04_MINIMAL_REPAIR_INSTRUCTION.md`

This review package contains the executable WP00-WP03 implementation with the
requested pre-WP04 correctness repairs. Repository-relative implementation
paths are preserved at the package root: `backend/`, `contracts/`,
`data/mock/`, `scripts/` and `docs/implementation/`. The frozen contract
materials and the two repair instructions are under `contract-source/`.

## Scope and stop point

Included work is limited to P0-1 selected-plan feasibility preservation,
P0-2 locked-commitment normalization, and the small P1-1/P1-2 fixes. WP04
booking/payment, WP05 execution, WP06 replanning, frontend, AI, Visio and real
providers are deferred.

## Gate result

- Backend tests: **52 passed**.
- Ruff check: **PASS**.
- Ruff format check: **PASS**.
- Contract/bootstrap validator: **PASS**.
- Canonical generation: three feasible candidates.
- Canonical selection: Journey `PLANNED` and PlanVersion `SELECTED`.
- Canonical locked River Cruise at 15:30 passes both generation and persisted
  selection revalidation.
- No runtime provider is required.

## Run

From this package root with Python 3.12+ and dependencies from
`backend/pyproject.toml`:

```powershell
$env:PYTHONPATH='backend'
python -m pytest -q backend/tests
ruff check backend scripts
ruff format --check backend scripts
```

The authoritative deterministic gate is
`backend/app/replanning/feasibility.py`. It is invoked before candidate
persistence and immediately before selection; the selected-plan mutation
guard is `backend/app/services.py`.
