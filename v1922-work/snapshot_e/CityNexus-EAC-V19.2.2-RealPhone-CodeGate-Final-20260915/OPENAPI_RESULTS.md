# OPENAPI_RESULTS.md — Contract path/schema guard

## Path parity (re-verified, not rebuilt)

```
python tools/verify_openapi_parity.py
OpenAPI 3.1.0; formal 137; runtime 137; missing 0; extra 0
```

Runtime pairs = 137, contract pairs = 137, missing = 0, extra = 0. The path
surface was **not** rebuilt; the V19.2 path parity simply still holds after this
round's changes.

## Response schemas updated (only those this round changed)

| Endpoint | Change |
| --- | --- |
| `POST /journeys/{id}/capabilities/confirm` | documents the new `recovery` object and the `active_plan_feasibility` shape |
| `GET /journeys/{id}/experience` | documents `recovery` and `experience_flags` (`needs_review`, `recovery_required`, `staleness`, `feasibility_failures`) |
| `POST /journeys/{id}/start` | documents 409 semantics: `STALE_RECOMPOSE_REQUIRED` and `START_BLOCKED_INFEASIBLE`, and that the Journey does not become ACTIVE |
| `components/schemas/RecoveryState` | new schema (state, kind, event id/status, capability code, active plan, failures, candidate plans, actions, `requires_user_decision`, `silent_plan_mutation`) |
| `components/schemas/Error` | alias to the existing `ErrorEnvelope` |

No unrelated endpoint or schema was touched.

## Frontend generated types

The project uses generated types (`frontend/src/generated/api.ts`,
`openapi-typescript`). They were regenerated from the updated contract:

```
openapi-typescript ../contracts/openapi.yaml -o src/generated/api.ts
-> 7.13.0, ok
```

The regenerated file now carries `RecoveryState` and the
`experience_flags` shape. Note: the previously checked-in generated file was
already stale relative to `contracts/openapi.yaml` (it was missing whole path
groups such as `/travelers/{traveler_id}/capabilities`). Regenerating therefore
also picks up that pre-existing drift; the diff is dominated by those
previously-missing declarations, not by this round's additions.

## Frontend build

```
npm run build
✓ built in 3.80s   (vite 7.3.6)
```

No TypeScript or bundling errors.

## Evidence

* `evidence/broad_regression_head.txt` — full suite green apart from the two
  documented contradictory pairs.
* `evidence/v192_contract_run.txt` — 61/61.
