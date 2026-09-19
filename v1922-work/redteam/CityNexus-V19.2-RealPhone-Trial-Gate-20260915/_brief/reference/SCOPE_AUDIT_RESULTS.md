# SCOPE_AUDIT_RESULTS.md

**Scope:** JOURNEY vs TRAVELER capability scope, and the mutation audit trail.
**Evidence:** `evidence/lifecycle_{a,b}.json` (`scope_audit` step),
`evidence/eac_live.json` (`audit`, `confirm_semantics`)
**Probes:** `tools/v191_probe_lifecycle.py`, `tools/v191_probe_eac_live.py`

**Delta target `D7` (TRAVELER scope): 2 `FIXED_IN_CURRENT` / 7 `STILL_REPRODUCIBLE`.**

---

## 1. Scope is forced correctly at the API boundary

| Check | Result |
|---|---|
| `POST /travelers/{id}/capabilities/confirm` forces `scope="TRAVELER"` | **yes** — a body-supplied scope is overridden |
| `POST /journeys/{id}/capabilities/confirm` forces `scope="JOURNEY"` + `journey_id` | **yes** |
| `PUT /journeys/{id}/capabilities` forces `scope="JOURNEY"` | **yes** |
| Cross-scope rows stored separately (`UNIQUE(traveler_id, journey_id, scope, code)`) | **yes** — 2 rows for TRAVELER + JOURNEY `AVOID_STAIRS` |

`traveler_endpoint_scope_forced: true`, `journey_endpoint_scope_forced: true`. Tag: holds.

## 2. TRAVELER scope is unreachable from text (D7 STILL_REPRODUCIBLE)

**15 `scope_permanence` cases, 0 rows with `scope == "TRAVELER"`** — in both `FINAL_V19` and
`EAC_REFERENCE` (`eac_traveler_scope_rows: 0`, `b_traveler_scope_rows: 0`):

| Text | Scope produced |
|---|---|
| `我终身不能走楼梯，这是永久性的` | `JOURNEY` |
| `我长期需要无障碍通道` | `JOURNEY` |
| `I permanently need step-free access` | `JOURNEY` |
| `我一直坐轮椅，不是这次才需要` | `JOURNEY` (EAC) / `[]` (FINAL_V19) |
| `我每次出行都带大箱子` | `JOURNEY` |

Explicit permanence language (`终身` / `长期` / `永久性` / `一辈子` / `permanently` /
`every trip`) never produces a traveller-level fact. `EAC_REFERENCE` did not change this.

## 3. STILL_REPRODUCIBLE: a TRAVELER-scoped need blocks every future journey

Measured live (`evidence/lifecycle_a.json` → `scope_audit`):

| Step | Result |
|---|---|
| `POST /travelers/{id}/capabilities/confirm` `[AVOID_STAIRS, HARD, TRAVELER]` | 200 |
| Create a second journey | **201** |
| Second journey's `constraints` list | **`[]`** (empty) |
| Second journey's `capabilities` list | contains the TRAVELER row |
| `POST /journeys/{second}/plans/generate` | **422 / 0 plans** |

`future_journey_blocked: true`. The traveller-level need is visible in the capability list but
**absent from the constraint list**, so the gate blocks without ever naming the cause — and
because it is traveller-scoped, **every** future journey is blocked.

Combined with §2 (permanent needs cannot be expressed as TRAVELER from text) the two facts
together mean: the only way to reach TRAVELER scope is the explicit endpoint, and doing so
breaks all subsequent journeys.

## 4. Mutation audit

| Action | Observed |
|---|---|
| `traveler.capability.created` | yes |
| `traveler.capability.updated` | yes (on a severity downgrade attempt) |
| `traveler.capability.deactivated` | yes |
| Journey-scope events carry `journey_id` | yes |
| Traveler-scope events carry `journey_id: null` | yes |
| `before` / `after` payloads present | yes |

There is **no HTTP audit endpoint in `FINAL_V19`**; the rows must be read directly from
`audit_logs`. `EAC_REFERENCE` adds
`GET /api/v1/travelers/{id}/capabilities/audit`, and its output is complete: journey-scope
events visible, traveler-scope events visible, deactivation event present, `before`/`after`
present. Tag: `FIXED` in `EAC_REFERENCE` (new endpoint).

One observation on deactivation: after `PUT /journeys/{id}/capabilities` with `[]`, the row is
still returned by the listing endpoint with `active: false` rather than being removed. The
audit trail records `traveler.capability.deactivated`, so the history is intact, but a client
that ignores `active` will still see the capability.

## 5. `EAC_REFERENCE`: confirm semantics destroy capabilities

The brief's item 3 — *`confirm A → confirm B`, A must not disappear* — plus the requested
concurrent / cross-scope cases. Measured live on the EAC lab backend:

### 5.1 `confirm A` → `confirm B` loses A

```
POST /journeys/{id}/capabilities/confirm  [STEP_FREE_REQUIRED, HARD] -> 200
POST /journeys/{id}/capabilities/confirm  [AVOID_STAIRS,       HARD] -> 200
GET  /journeys/{id}/capabilities -> ["AVOID_STAIRS"]     # STEP_FREE_REQUIRED gone
```

`a_survived: false`, `a_survived_after_reload: false`. `_replace_capability_rows()` replaces
the whole JOURNEY-scope set instead of upserting. **VIOLATED.**

### 5.2 Concurrent confirm silently loses a capability

Three concurrent confirms, **all returning 200**:

| Run | Surviving | Lost |
|---|---|---|
| 1 | `["AVOID_STAIRS","LARGE_LUGGAGE"]` | `STEP_FREE_REQUIRED` |
| 2 | `["LARGE_LUGGAGE","STEP_FREE_REQUIRED"]` | `AVOID_STAIRS` |

Every request reports success; one capability vanishes, and **which one is lost varies between
runs**. A lost-update race in the read-modify-write of the JOURNEY scope. `NEW`.

### 5.3 Cross-scope duplicate — storage correct, compiler wrong

| Check | Result |
|---|---|
| TRAVELER + JOURNEY `AVOID_STAIRS` stored | **2 rows**, correct scopes and params |
| Same two items through `canonicalize_capabilities` | **1 row**, `scope="TRAVELER"`, params from the JOURNEY item |

So the persistence layer honours scope; the semantic-compiler path collapses it. `NEW`. Detail
in `CAPABILITY_CANONICALIZATION_RESULTS.md` §4.3.

## 6. Verdict table

| # | Finding | Result | Tag |
|---|---|---|---|
| 1 | Endpoints force the correct scope | **holds** | — |
| 2 | Cross-scope rows are stored separately | **holds** (2 rows) | — |
| 3 | Permanent language produces TRAVELER scope | **VIOLATED** — 0/15 in both implementations | `FINAL_V19`, `EAC_REFERENCE` |
| 4 | A TRAVELER need is reflected in the journey's constraints | **VIOLATED** — `constraints: []` while `capabilities` lists it | `FINAL_V19` |
| 5 | A TRAVELER need does not block unrelated future journeys | **VIOLATED** — every future journey → 422 | `FINAL_V19` |
| 6 | Mutation audit records create / update / deactivate | **holds** | — |
| 7 | Audit is reachable over HTTP | **FIXED in `EAC_REFERENCE`** (new endpoint) | `EAC_REFERENCE` |
| 8 | Deactivated rows disappear from listings | **VIOLATED** — returned with `active: false` | `FINAL_V19` |
| 9 | `confirm A` → `confirm B` keeps A | **VIOLATED in `EAC_REFERENCE`** | `NEW` |
| 10 | Concurrent confirm is safe | **VIOLATED in `EAC_REFERENCE`** — nondeterministic silent loss | `NEW` |
| 11 | Dedupe respects scope | **VIOLATED in `EAC_REFERENCE`** (compiler path only) | `NEW` |

## 7. Recommendation (not applied)

1. Make `_replace_capability_rows()` an upsert keyed by `(scope, code)` so a second confirm
   merges instead of overwriting, and wrap it in a transaction that re-reads the scope before
   writing (fixes both §5.1 and §5.2).
2. Derive TRAVELER scope from explicit permanence markers (`终身`/`长期`/`永久`/`一辈子`/
   `permanently`/`every trip`) in `extract_capabilities_from_text`.
3. Include TRAVELER-scoped capabilities in `_journey_constraints_with_capabilities()` so the
   constraint list and the capability list agree, and so the block is attributable.
4. Filter `active == false` rows out of the default listing.
5. Expose an audit endpoint in `FINAL_V19` (EAC's implementation can be reused verbatim).
