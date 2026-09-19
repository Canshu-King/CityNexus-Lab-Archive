# FEASIBILITY_EVIDENCE_RESULTS.md

**Scope:** does the feasibility gate actually understand capability, and is evidence
semantics consistent across codes and across surfaces?
**Evidence:** `evidence/lifecycle_a.json`, `evidence/lifecycle_b.json`,
`evidence/gate_codes_{a,b}.json`, `evidence/boundaries.jsonl`,
`evidence/accessibility_evidence_scope.json`, `evidence/eac_live.json`
**Probes:** `tools/v191_probe_lifecycle.py`, `tools/v191_probe_gate_codes.py`,
`tools/v191_probe_boundaries.py`, `tools/v191_probe_accessibility_evidence.py`

**Delta target `D6` (gate interprets capability): 2 `FIXED_IN_CURRENT` / 1
`STILL_REPRODUCIBLE`.**

---

## 1. FIXED: the gate now interprets capability

`_CAPABILITY_GATE_CODES` (11 codes) exists in `app/replanning/feasibility.py:236-248`:

```
STEP_FREE_REQUIRED  AVOID_STAIRS  MAX_WALKING_PER_LEG_M  MAX_CONTINUOUS_WALKING_MIN
MAX_DAILY_WALKING_M  MIDDAY_REST_WINDOW  REST_EVERY_MIN  INFANT_NAP_WINDOW
TOILET_BREAK_EVERY_MIN  STROLLER  LARGE_LUGGAGE
```

`_capability_failure_for_record()` (line 293) maps a capability plus a place record to
failures, and dedicated walking / rest / break checks exist. **The gate is no longer
capability-blind.** Tag: `FIXED_IN_CURRENT`.

## 2. FIXED: `UNKNOWN != ACCESSIBLE`

The brief's requirement holds. `evidence/lifecycle_a.json` → `evidence_matrix`:

| Place evidence | `generate` | Plans |
|---|---|---|
| no capability declared | 201 | 3 |
| `evidence_status: VERIFIED` | 201 | 3 |
| explicit `ACCESSIBILITY_VERIFIED` | 201 | 3 |
| evidence **missing** | **422** | 0 |
| evidence `UNKNOWN` | **422** | 0 |
| evidence `CONFLICT` | **422** | 0 |

Unknown is not treated as accessible. Tag: `FIXED_IN_CURRENT`.

## 3. STILL_REPRODUCIBLE: evidence semantics are asymmetric between codes

`evidence/boundaries.jsonl` → `evidence_symmetry`:

| Capability | Metadata absent | Explicit denial | Explicit allowance |
|---|---|---|---|
| `STEP_FREE_REQUIRED` | **422 / 0 plans** (fail **closed**) | 422 | 201 / 3 |
| `AVOID_STAIRS` | **422 / 0 plans** (fail **closed**) | 422 | 201 / 3 |
| `STROLLER` | **201 / 3 plans** (fail **open**) | 422 `STROLLER_ACCESS_UNAVAILABLE` | 201 / 3 |
| `LARGE_LUGGAGE` | **201 / 3 plans** (fail **open**) | 422 `LUGGAGE_ACCESS_UNAVAILABLE` | 201 / 3 |

`_capability_failure_for_record()` returns `[]` for `STROLLER`/`LARGE_LUGGAGE` when the
metadata key is simply absent (line 291-296), while `STEP_FREE_REQUIRED`/`AVOID_STAIRS` are
evidence-negative and fail closed. So **an absence of evidence blocks a wheelchair user but
not a stroller user.** Whether that asymmetry is intended is not documented anywhere in the
tree; it is at minimum an unstated policy.

## 4. STILL_REPRODUCIBLE: the gate computes rich reasons and the client sees one string

`tools/v191_probe_gate_codes.py` wraps `app.services.evaluate_feasibility` to record every
`FeasibilityResult` the gate produces, then compares with the single message the client
receives.

Gate codes observed (7 distinct families, `evidence/gate_codes_a.json`):

```
NEEDS_LIVE_EVIDENCE:MAX_WALKING_PER_LEG_M:{pair}      (x9 per call)
CAPABILITY_PARAMS_INVALID:{code}
REST_WINDOW_UNSATISFIED:{code}
BREAK_INTERVAL_UNSATISFIED:{code}
ACCESSIBILITY_UNVERIFIED:{place}
NEEDS_LIVE_EVIDENCE:{place}
LOCKED_COMMITMENT_LOST:{key}
```

Distinct messages the client receives: **exactly one** —

```
"No feasible plan candidates satisfy the journey constraints"
```

`backend/app/services.py:975-1013` builds the rich `failures` list and then discards it at
line 1003:

```python
if not created:
    raise ValueError("No feasible plan candidates satisfy the journey constraints")
```

`main.py` never references `UNSUPPORTED_HARD_CONSTRAINT` or `failures`. So a user who is
blocked cannot tell whether the cause is a missing provider fact, a malformed parameter, an
unsatisfiable rest window, an accessibility conflict, or a lost locked commitment.

**Notably, the one exception proves the mechanism works:** `POST /journeys/{id}/bookings`
returns the informative `"selected plan is no longer feasible:
LOCKED_COMMITMENT_LOST:ea06631e-…"`. The information exists; only the generate/select path
throws it away.

## 5. Cross-surface consistency

| Surface | Consults capability? | Consults C4? |
|---|---|---|
| `generate_plans()` (`services.py:847`) | yes | **no** |
| `select_plan()` (`main.py:3693`) | yes | **no** |
| `_assert_selected_plan_feasible()` (`main.py:4458`) → `validate_plan_feasibility(..., include_active_c4=True)` | yes | **yes** |
| `POST /bookings` | yes | **yes** |

So the **initial plan**, **What-If / select** and **booking** disagree. See
`CAPABILITY_COMMITMENT_CONFLICT_RESULTS.md` for the end-to-end consequence.

**Stale-plan behaviour is correct:** after declaring a HARD step-free need,
`regenerate → 422` (0 new plans) but 3 stale `CANDIDATE` plans remain listed; `select → 422`;
`start → 409`; the journey stays `DRAFT`. So the product does refuse — it just does not clean
up the stale candidates or explain why.

## 6. `EAC_REFERENCE`: the read endpoint and the gate disagree

`evidence/eac_live.json` → `consumer_divergence`: 9 place shapes, **6 divergent**, **3 in the
dangerous direction**:

| Shape | Read endpoint | Gate |
|---|---|---|
| `{"accessibility":{"evidence_status":"ACCESSIBILITY_VERIFIED"}}` | **NEEDS_LIVE_EVIDENCE** | **ACCESSIBILITY_VERIFIED** |
| `{"accessibility":{"evidence_status":"VERIFIED"}}` | **NEEDS_LIVE_EVIDENCE** | **ACCESSIBILITY_VERIFIED** |
| `{"accessibility":{"step_free":true}}` | **NEEDS_LIVE_EVIDENCE** | **ACCESSIBILITY_VERIFIED** |
| `place.tags_json=["wheelchair=yes"]` | **ACCESSIBILITY_VERIFIED** | **NEEDS_LIVE_EVIDENCE** |
| `place.tags_json={"wheelchair":"yes"}` | **ACCESSIBILITY_VERIFIED** | **NEEDS_LIVE_EVIDENCE** |
| `{"tags":{"wheelchair":"yes"}}` | ACCESSIBILITY_VERIFIED | ACCESSIBILITY_VERIFIED |

The first three are the **documented frozen-evidence shape** and are in the gate's own key set
(`evidence_status`, `status`, `step_free`, `wheelchair_access`, `stairs`, …): the product
reports "unknown" while the gate plans as if step-free were verified. The next two are the
mirror image: `place.tags_json` is a real column (`models.py:468`) that the read endpoint
parses and `_accessibility_metadata()` never reads, so the product says "verified" and the
gate blocks.

Also in `EAC_REFERENCE`: the journey endpoint's conservative `ROUTE_STEP_FREE`
`NEEDS_LIVE_EVIDENCE` fact is **never consulted by the gate** — `generate` returns **201**
while the read endpoint reports `NEEDS_LIVE_EVIDENCE`. Detail in
`ACCESSIBILITY_EVIDENCE_SCOPE_RESULTS.md`.

## 7. Verdict table

| # | Finding | Result | Tag |
|---|---|---|---|
| 1 | Gate interprets capability codes | **FIXED_IN_CURRENT** | — |
| 2 | `UNKNOWN != ACCESSIBLE` | **FIXED_IN_CURRENT** (missing / UNKNOWN / CONFLICT all 422) | — |
| 3 | Evidence semantics symmetric across codes | **VIOLATED** — STROLLER/LARGE_LUGGAGE fail open, STEP_FREE/AVOID_STAIRS fail closed | `FINAL_V19`, `NEW` |
| 4 | Gate reasons reach the client | **VIOLATED** — 7 code families collapse to 1 message | `FINAL_V19` |
| 5 | Initial plan / select / booking agree | **VIOLATED** — 3 paths, 2 definitions of feasibility | `FINAL_V19` |
| 6 | Stale candidates removed when a plan becomes infeasible | **VIOLATED** — 3 stale `CANDIDATE` plans remain listed | `FINAL_V19` |
| 7 | Read endpoint and gate agree about the same place | n/a in `FINAL_V19`; **VIOLATED in `EAC_REFERENCE`** (6/9 shapes) | `NEW` |
| 8 | Route-level step-free unknown is honoured by planning | **VIOLATED in `EAC_REFERENCE`** — reported unknown, planned as known | `NEW` |

## 8. Recommendation (not applied)

1. Propagate `failures` from `services.py:1003` into the HTTP error detail (the bookings path
   already proves this works), and map the leading code family to a user-facing sentence.
2. State the intended fail-open/fail-closed policy per code in the module docstring, or make
   `STROLLER`/`LARGE_LUGGAGE` evidence-negative like `STEP_FREE_REQUIRED`.
3. Make all four paths (`generate`, `select`, `_assert_selected_plan_feasible`, `bookings`)
   share one constraint-assembly function so C4 inclusion cannot diverge.
4. Mark stale `CANDIDATE` plans as `SUPERSEDED` when a regeneration fails feasibility.
5. In `EAC_REFERENCE`, have `_accessibility_metadata()` read `place.tags_json` and derive the
   read endpoint's state from the same subject-scoped projection the gate uses.
