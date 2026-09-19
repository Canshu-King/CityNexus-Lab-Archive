# 02 - Directory Structure

Recommended target under `D:\moodle\CityNexus\`:

```text
CityNexus/
├─ README.md
├─ .env.example
├─ .gitignore
├─ docs/
│  ├─ implementation/
│  │  ├─ architecture.md
│  │  ├─ domain-reconciliation.md
│  │  ├─ api.md
│  │  ├─ testing.md
│  │  └─ checkpoints/
│  └─ coursework/                 # existing coursework documentation, do not overwrite
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ tsconfig.json
│  └─ src/
│     ├─ app/
│     │  ├─ router.tsx
│     │  └─ queryClient.ts
│     ├─ api/
│     │  ├─ client.ts
│     │  └─ generated-or-types.ts
│     ├─ components/
│     ├─ features/
│     │  ├─ journeys/
│     │  ├─ planning/
│     │  ├─ discovery/
│     │  ├─ commerce/
│     │  ├─ execution/
│     │  ├─ replanning/
│     │  └─ copilot/
│     ├─ pages/
│     ├─ styles/
│     └─ main.tsx
├─ backend/
│  ├─ pyproject.toml
│  ├─ alembic.ini
│  ├─ alembic/
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     │  └─ v1/
│     │     ├─ router.py
│     │     ├─ journeys.py
│     │     ├─ plans.py
│     │     ├─ discovery.py
│     │     ├─ commerce.py
│     │     ├─ execution.py
│     │     ├─ events.py
│     │     ├─ replanning.py
│     │     └─ copilot.py
│     ├─ core/
│     │  ├─ config.py
│     │  ├─ errors.py
│     │  ├─ logging.py
│     │  └─ idempotency.py
│     ├─ db/
│     │  ├─ session.py
│     │  ├─ models.py
│     │  └─ repositories/
│     ├─ domain/
│     │  ├─ enums.py
│     │  ├─ value_objects.py
│     │  └─ transitions.py
│     ├─ services/
│     │  ├─ journey_service.py
│     │  ├─ planning_service.py
│     │  ├─ discovery_service.py
│     │  ├─ commerce_service.py
│     │  ├─ execution_service.py
│     │  ├─ replanning_service.py
│     │  └─ copilot_service.py
│     ├─ replanning/
│     │  ├─ feasibility.py
│     │  ├─ candidate_generation.py
│     │  ├─ scoring.py
│     │  ├─ diff.py
│     │  └─ engine.py
│     ├─ integrations/
│     │  ├─ ports.py
│     │  ├─ mock/
│     │  └─ real/                 # empty until intentionally implemented
│     └─ schemas/
│        ├─ common.py
│        ├─ journey.py
│        ├─ plan.py
│        ├─ commerce.py
│        ├─ event.py
│        └─ replan.py
├─ contracts/
│  └─ openapi.yaml
├─ data/
│  └─ mock/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ contract/
│  └─ e2e/
├─ scripts/
│  ├─ seed_demo.py
│  ├─ reset_demo.py
│  └─ run_demo_scenario.py
└─ existing frozen coursework folders...
```

## Placement rules

- Do not move or rename the frozen domain/requirements/Visio folders just to fit this tree.
- New executable application code lives in `frontend/`, `backend/`, `contracts/`, `data/`, `tests/`, `scripts/`.
- Keep implementation checkpoints separate from frozen design baselines.
- Generated files such as SQLite DBs, coverage output, build artifacts and caches are ignored by Git.
