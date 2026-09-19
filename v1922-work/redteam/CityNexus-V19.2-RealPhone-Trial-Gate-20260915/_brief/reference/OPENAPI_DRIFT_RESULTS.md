# OPENAPI_DRIFT_RESULTS.md

**Round:** CityNexus WorkBuddy V19.1 Convergence Red-Team — EAC-Aware Update
**Requirement (brief item 5):** *runtime OpenAPI vs checked-in OpenAPI; capability /
accessibility routes and the `/api/v1` prefix must agree.*
**Probe:** `tools/v191_probe_openapi_drift.py` (automated, re-runnable)
**Evidence:** `evidence/openapi_drift.json`

Each target is measured in a **fresh interpreter** (so no module state leaks), with
`PYTHONDONTWRITEBYTECODE=1` and `CITYNEXUS_DATABASE_URL` pointed at a throwaway file in
`%TEMP%`. No tree is modified.

---

## 1. Parity definition

The project already ships a checker — `D:\moodle\CityNexus\tools\verify_openapi_parity.py`.
Its semantics are authoritative and are reproduced exactly:

```python
runtime_paths()  = {(route.path, method) for route in app.routes
                    if route.path.startswith("/api/v1/") or route.path == "/api/v1"}
formal_paths()   = {("/api/v1" + path, method) for path, item in spec["paths"].items()
                    for method in item}                     # prefix ADDED to formal keys
parity_ok        = not (runtime - formal) and not (formal - runtime)
```

So the comparison is over **(path, method) pairs**, and the `/api/v1` prefix is added to the
checked-in document's path keys before comparing.

---

## 2. Results

| Target | Runtime (path, method) | Contract pairs | Missing | Extra | Parity |
|---|---|---|---|---|---|
| `main_tree` (live `D:\moodle\CityNexus`) | 137 | 137 | **0** | 0 | **OK** |
| `snapshot_b` (13:05:57) | 137 | 137 | **0** | 0 | **OK** |
| `snapshot_a` (12:38:11) | 137 | 131 | **6** | 0 | **FAIL** |
| `eac_lab` (EAC reference) | 143 | 131 | **12** | 0 | **FAIL** |

Checked-in document for every target: `<tree_root>/contracts/openapi.yaml`
(e.g. `D:\moodle\CityNexus\contracts\openapi.yaml`), `openapi: 3.1.0`,
`servers: [{"url": "http://localhost:8000/api/v1"}]`.

Unique-path counts from the generated schema, for comparison with the EAC report's numbers:

| Target | `app.openapi()` unique paths | `app.routes` (path, method) pairs |
|---|---|---|
| `main_tree` / `snapshot_b` | 128 | 137 |
| `snapshot_a` | 128 | 137 |
| `eac_lab` | **134** | 143 |

> **Metric note.** The EAC report's "runtime 134" is `len(spec["paths"])` (unique paths). The
> parity checker counts `(path, method)` pairs, which is larger because one path can serve
> several methods. Both are correct for their own question; they must not be compared to each
> other.

---

## 3. The `/api/v1` prefix claim is a **false positive**

The EAC report characterises the drift as a prefix problem:

> `runtime_prefix_sample: ["/api/v1/agent/hermes/capabilities", ...]`
> `checked_in_prefix_sample: ["/agent/hermes/capabilities", ...]`

The checked-in document's path keys genuinely have no `/api/v1` prefix — **because the prefix
is declared once, globally, in `servers`**:

```yaml
servers:
  - url: http://localhost:8000/api/v1
```

That is the standard OpenAPI way to express a base path. The project's own parity tool
therefore **adds** the prefix to the formal keys before comparing, and finds **no prefix
problem in any target**: after normalisation, `extra = 0` everywhere and the EAC lab's
non-`/api/v1` route count is 0 (`non_api_v1: 0`). A checker that string-compares raw path keys
without applying `servers` will report spurious prefix drift.

**Conclusion: the `/api/v1` prefix does agree.** The brief's prefix requirement is satisfied
in all four trees.

---

## 4. The route-coverage drift is real — and already fixed in the current tree

### 4.1 `snapshot_a` — 6 routes missing (all capability routes)

```
GET  /api/v1/journeys/{journey_id}/capabilities
GET  /api/v1/travelers/{traveler_id}/capabilities
POST /api/v1/journeys/{journey_id}/capabilities/confirm
POST /api/v1/travelers/{traveler_id}/capabilities/confirm
PUT  /api/v1/journeys/{journey_id}/capabilities
PUT  /api/v1/travelers/{traveler_id}/capabilities
```

### 4.2 `snapshot_b` / `main_tree` — **parity OK, 137/137, missing 0, extra 0**

Between Snapshot A (12:38:11) and Snapshot B (13:05:57) the checked-in contract gained the
6 capability routes and reached full parity with the runtime. **`FIXED_IN_CURRENT`** — the
moving-baseline protocol caught a real convergence that a single-snapshot audit would have
reported as a live defect.

### 4.3 `eac_lab` — 12 routes missing (all capability / accessibility routes)

The EAC lab's own `contracts/openapi.yaml` is a stale copy that never received the routes the
EAC patch added:

```
GET  /api/v1/capabilities/catalog
GET  /api/v1/journeys/{journey_id}/accessibility-evidence
GET  /api/v1/journeys/{journey_id}/capability-plan-impact
GET  /api/v1/places/{place_id}/accessibility-evidence
GET  /api/v1/travelers/{traveler_id}/capabilities/audit
POST /api/v1/travelers/{traveler_id}/capabilities/extract
GET  /api/v1/journeys/{journey_id}/capabilities
GET  /api/v1/travelers/{traveler_id}/capabilities
POST /api/v1/journeys/{journey_id}/capabilities/confirm
POST /api/v1/travelers/{traveler_id}/capabilities/confirm
PUT  /api/v1/journeys/{journey_id}/capabilities
PUT  /api/v1/travelers/{traveler_id}/capabilities
```

So **the EAC patch adds 6 new capability/accessibility routes and updates the contract with
none of them.** If the EAC patches were merged as-is, the contract would regress from
`parity_ok = true` (current tree) to 12 missing routes.

---

## 5. Capability / accessibility route surface

**EAC-only routes** (present in the EAC lab runtime, absent from the current tree) — 6:

```
GET  /api/v1/capabilities/catalog
GET  /api/v1/journeys/{journey_id}/accessibility-evidence
GET  /api/v1/journeys/{journey_id}/capability-plan-impact
GET  /api/v1/places/{place_id}/accessibility-evidence
GET  /api/v1/travelers/{traveler_id}/capabilities/audit
POST /api/v1/travelers/{traveler_id}/capabilities/extract
```

**`main_only_relevant` = []** and **`snapshot_b` vs `main_tree` delta = []** — the current tree
and Snapshot B expose an identical capability/accessibility surface, and EAC is a strict
superset. The 143 − 137 = 6 runtime pair difference is exactly these 6 routes.

---

## 6. Verdict table

| # | Requirement | Result | Tag |
|---|---|---|---|
| 1 | runtime vs checked-in OpenAPI compared automatically | done — `tools/v191_probe_openapi_drift.py`, re-runnable | — |
| 2 | `/api/v1` prefix must agree | **AGREES** in all 4 trees; EAC's prefix claim is a false positive (`servers[0].url`) | `EAC_REFERENCE` |
| 3 | capability/accessibility routes must agree | `main_tree`/`snapshot_b` **OK**; `snapshot_a` 6 missing; `eac_lab` 12 missing | `FIXED_IN_CURRENT` (A→B), `EAC_REFERENCE` |
| 4 | overall parity | `main_tree` & `snapshot_b` **parity_ok = true**; `snapshot_a` false; `eac_lab` false | `FIXED_IN_CURRENT` |
| 5 | EAC patch keeps the contract in sync | **NO** — adds 6 routes, contract unchanged | `NEW` |

## 7. Recommendation (not applied)

1. Wire `tools/verify_openapi_parity.py` into CI as a blocking gate; it already returns
   exit 1 on drift and needs no changes.
2. When merging the EAC patches, add the 6 new routes to `contracts/openapi.yaml`, otherwise
   the contract regresses.
3. If a parity report is produced from raw path keys, apply `servers[0].url` first — otherwise
   it will report the `/api/v1` prefix as drift on every run.
