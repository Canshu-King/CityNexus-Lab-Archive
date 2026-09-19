# OpenAPI Regression Guard

Evidence: `evidence/openapi_drift.json`.
Tool: `tools/v191_probe_openapi_drift.py` (the project's own parity definition, from
`tools/verify_openapi_parity.py`: compare `(path, method)` pairs, adding the `/api/v1` prefix
declared by the contract's `servers[0].url`).

Each target is loaded in a **fresh interpreter** with `PYTHONDONTWRITEBYTECODE=1`, so no module
state leaks between targets and nothing is written into any tree.

---

## Results

| Target | Runtime pairs | Contract pairs | missing | extra | `parity_ok` |
|---|---|---|---|---|---|
| **V19.2 snapshot A** | 137 | 137 | **0** | **0** | **True** |
| V19.1 snapshot C | 137 | 137 | 0 | 0 | True |
| **live main tree** | 137 | 137 | 0 | 0 | **True** |
| EAC reference lab | 143 | 131 | 12 | 0 | False |

**The guard holds.** The V19.2 tree, the V19.1 baseline and the live main tree are all in parity:
every route the runtime exposes is present in `contracts/openapi.yaml`, and the contract declares
no route the runtime lacks.

## `/api/v1` prefix

`BASELINE_AUDIT.md` explicitly says not to re-open the prefix question, and the measurement
confirms it: the contract declares `servers: [{url: "http://localhost:8000/api/v1"}]`, and parity
is computed with that prefix applied. **Not a defect.** No `/api/v1` finding is reported this
round.

## EAC reference lab — 12 missing routes

The EAC lab's own contract copy is behind its runtime. These routes exist only in the EAC branch
and are absent from its checked-in contract:

```
GET  /api/v1/capabilities/catalog
GET  /api/v1/journeys/{journey_id}/accessibility-evidence
GET  /api/v1/journeys/{journey_id}/capability-plan-impact
GET  /api/v1/places/{place_id}/accessibility-evidence
GET  /api/v1/travelers/{traveler_id}/capabilities/audit
POST /api/v1/travelers/{traveler_id}/capabilities/extract
```

This is the EAC reference package, **not** the authoritative tree, and it is out of scope for this
gate. Recorded so that nobody later mistakes it for main-tree drift. If any of these routes are
ever merged into the main tree, the contract must be regenerated in the same change.

## Capability / accessibility route coverage

For the V19.2 snapshot, the capability- and accessibility-related routes are **all present** in the
contract (`capability/accessibility missing from contract: []`). Specifically covered:
`GET|PUT /travelers/{id}/capabilities`, `POST /travelers/{id}/capabilities/confirm`,
`GET|PUT /journeys/{id}/capabilities`, `POST /journeys/{id}/capabilities/confirm`,
`GET /agent/hermes/capabilities`, `GET /journeys/{id}/route-evidence`.

## Verdict

**PASS.** No OpenAPI regression. Keep this check in CI: it is cheap (one subprocess per target) and
it caught a genuine 12-route gap in the EAC branch.

## Reproduction

```
cd D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915
python tools/v191_probe_openapi_drift.py
```
