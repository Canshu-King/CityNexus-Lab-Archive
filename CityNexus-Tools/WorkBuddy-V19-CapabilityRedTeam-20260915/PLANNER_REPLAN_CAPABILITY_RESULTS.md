# Planner / Replan Capability Results

**Evidence:** `evidence/scenario_results.jsonl` (168 flows), `evidence/field_simulation_summary.json`, `evidence/planner_replan_capability_probe.json`, `evidence/planner_select_recovery_probe.json`, `evidence/accessibility_truth_probe.json`, `evidence/boundary_and_drop_probe.json`

---

## 1. Field simulation design

| Dimension | Value |
|---|---|
| Personas | **12** |
| Destinations | **11** non-demo (8 major, 3 small county-level) + the seeded demo city × 3 repeats |
| Complete Journey flows | **168** = 12 × 14 |
| Required minimum | 30 — exceeded by 5.6× |
| Stages per flow | setup → semantic intake → capability declaration → planning → plan select → journey start → Copilot → What-If → recovery |
| Live model in the loop | `mode: AI` in **165 / 168** intake calls (3 fell back) |

### Personas

| ID | Persona | Declares a capability? |
|---|---|---|
| P01 | wheelchair traveller | yes |
| P02 | elderly companion, walking limit | yes |
| P03 | infant with a nap window | yes |
| P04 | stroller | yes |
| P05 | large luggage | yes |
| P06 | toilet / rest needs | yes |
| P07 | quiet / sensory sensitivity | yes |
| P08 | no special need | **no** — control |
| P09 | conflicting family needs | yes |
| P10 | ambiguous statement | no (vague) |
| P11 | negated / historical | no (negated) |
| P12 | malicious bypass attempt | no (injection) |

### Destinations

Major: Tianjin, Fuzhou, Beijing, Shanghai, Chongqing, Tokyo, Singapore, London (8)
Small (county-level): Shaxian, Wuyuan, Xiapu (3) — satisfies the brief's "≥3 small cities"
Seeded: Nexus City demo catalog (D00, run 3× per persona)

---

## 2. The headline: 156 of 168 flows produced no plan

| Outcome | Flows |
|---|---|
| **blocked** | **156** |
| feasible | 12 |

By persona:

| Persona | Blocked | Feasible |
|---|---|---|
| P01 wheelchair | **14** | 0 |
| P02 elderly / walking limit | **14** | 0 |
| P03 infant nap | **14** | 0 |
| P04 stroller | **14** | 0 |
| P05 large luggage | **14** | 0 |
| P06 toilet / rest | **14** | 0 |
| P07 quiet / sensory | **14** | 0 |
| P09 conflicting family needs | **14** | 0 |
| P08 no special need | 11 | 3 |
| P10 ambiguous | 11 | 3 |
| P11 negated / historical | 11 | 3 |
| P12 malicious bypass | 11 | 3 |

**Every single flow that declared an accessibility need was blocked: 98 / 98.**
The only 12 flows that planned were the 4 personas that declared no capability, and they planned in **exactly one destination each** — the seeded demo city where the place catalog exists. All 11 real destinations blocked even for the control persona, because those catalogs have no place data in this environment.

### Every blocked flow produced the identical message

```
156 × "No feasible plan candidates satisfy the journey constraints"
```

One message, 156 times, covering: a wheelchair user in Tokyo, an 78-year-old in Wuyuan, an infant in London, a stroller in Xiapu, large luggage in Chongqing, a sensory-sensitive traveller in Shaxian. The product cannot distinguish them and does not try.

---

## 3. What the model actually understood (and the planner discarded)

The semantic intake worked. These are real `stages.semantic_intake` records:

**P01 wheelchair — `我用轮椅，必须全程 step-free，一步楼梯都不能走`**

| Destination | Intent | Mode | Envelope constraint |
|---|---|---|---|
| Tianjin | `UNKNOWN` | **FALLBACK** | *(none)* |
| Fuzhou | `PERSONAL_ASSISTANCE` | AI | `{type: accessibility, value: step_free, strict: true}` |
| Beijing | `PERSONAL_ASSISTANCE` | AI | `{type: accessibility, value: step_free, strictness: hard}` |

**P02 elderly — `我带 78 岁母亲，最多走 500 米，每 60 分钟要休息`**

| Destination | Envelope constraint |
|---|---|
| Tianjin | `{type: max_walking_distance, value: 500, unit: meter}` |
| Fuzhou | `{type: max_walking_distance, value: 500, unit: meter}` |
| Beijing | `{type: max_walking_distance, value: 500, unit: meters}` |

**P03 infant — `宝宝下午 1 点到 3 点必须睡午觉，不能安排活动`**

| Destination | Envelope constraint |
|---|---|
| Tianjin | `{type: time_window_block, start: "13:00", end: "15:00", recurrence: daily, reason: "baby nap", no_activities: true}` |
| Fuzhou | *(identical)* |
| Beijing | *(identical, `recurrence: daily`)* |

The model produced a **precise, machine-readable 500 m budget**, a **13:00–15:00 no-activity block**, and a **`strict: true` step-free requirement** — then the planner was asked to satisfy the traveller and instead returned `422`.

Note the Tianjin row for P01: `mode: FALLBACK, intent: UNKNOWN, constraints: []`. On a live run, one intake fell back to the deterministic path and the traveller's wheelchair statement produced **nothing at all** — no envelope, no constraint, no error. The flow then continued to declare the capability explicitly (that is the probe's design), but a real traveller typing that sentence into the Copilot in that moment would have been silently unheard.

---

## 4. The gate that decides — and why it decides this way

`app/replanning/feasibility.py` is the single authoritative gate, shared by initial planning, plan selection, and replan:

```python
elif code not in {"LOCKED_COMMITMENT"}:
    # A hard rule that the gate cannot interpret must never be bypassed
    # by scoring or persistence.
    failures.append(f"UNSUPPORTED_HARD_CONSTRAINT:{code or category}")
```

Supported HARD codes: `BUDGET_MAX`, `JOURNEY_END_BY`, `JOURNEY_START_AT`, `PLACE_UNAVAILABLE` / `PLACE_CLOSED`, `SERVICE_UNAVAILABLE` / `SERVICE_CLOSED`, `REQUIRE_PLACE`, `LOCKED_COMMITMENT`.
**Every capability code is unsupported.** So the gate refuses — correctly, and totally.

This is the correct *default* and must be preserved. The defect is not the refusal; it is that **no capability code is interpretable and no evidence model exists**, so the refusal is the only possible outcome.

---

## 5. Numeric values are never read

`MAX_WALKING_PER_LEG_M` with **15** distinct values → **1** distinct outcome (`evidence/boundary_and_drop_probe.json`):

| Variant | Value | Generate |
|---|---|---|
| `zero` | 0 | 422 |
| `one` | 1 | 422 |
| `hundred` | 100 | 422 |
| `just_below_500` | 499 | 422 |
| `at_500` | 500 | 422 |
| `just_above_500` | 501 | 422 |
| `thousand` | 1000 | 422 |
| `huge` | 10 000 000 | 422 |
| `negative` | −5 | 422 |
| `string_numeric` | `"500"` | 422 |
| `string_units` | `"500m"` | 422 |
| `null` | `null` | 422 |
| `absent` | *(missing)* | 422 |
| `wrong_key` | `{"limit": 500}` | 422 |
| `km_key` | `{"…_km": 0.5}` | 422 |

`distinct_outcomes = 1`. The same collapse holds for `MIDDAY_REST_WINDOW`, `INFANT_NAP_WINDOW`, `MAX_CONTINUOUS_WALKING_MIN` and `REST_EVERY_MIN` across **48** further variants (normal, cross-midnight, start-after-end, equal, invalid-text, hour-24, empty, minutes-only, zero, negative) — **63 variants total, one outcome.**

**Planner consequence:** the planner cannot tell a *tight* budget (100 m) from a *generous* one (10 km) from a *typo* from a *missing value*. Any capability-aware planner must be given a typed, validated value — the raw `params` dict is not validated at all.

### SOFT capability is inert at the planner

| Declaration | Generate | Plans | Identical to baseline |
|---|---|---|---|
| `STEP_FREE_REQUIRED` SOFT | 201 | 3 | **yes, byte-identical** |
| `STEP_FREE_REQUIRED` SOFT + `params={requirement: VERIFIED_STEP_FREE}` | 201 | 3 | **yes** |

The planner receives SOFT constraints as scoring weights it has no dimension for, so they vanish. The traveller gets a success response and a plan that ignores them.

---

## 6. Mid-trip declaration — the stranding bug (P0)

`evidence/planner_replan_capability_probe.json`

| Step | Result |
|---|---|
| `POST /plans/generate` | `201`, 3 plans |
| `POST /plans/{id}/select` | `200` |
| `POST /journeys/{id}/start` | `200` — journey `ACTIVE`, `projection_status: READY` |
| `POST /constraints {STEP_FREE_REQUIRED, HARD}` | **`422`** |
| ↳ body | `Constraint would make the selected plan infeasible: UNSUPPORTED_HARD_CONSTRAINT:STEP_FREE_REQUIRED` |
| `POST /events {CLOSURE, MAJOR}` | `201` |
| `POST /replans {trigger_event_id}` | `201`, **`candidate_count: 0`** |
| Journey state after | `status: ACTIVE`, `active_plan_version_id` unchanged |

The traveller is mid-trip, has just told the product about a real need, and:

- **cannot add the need** (422),
- **cannot get a recovery candidate** (`candidate_count: 0`),
- **is still nominally on a plan that ignores it** (ACTIVE, plan unchanged),
- **receives no message naming the problem** — the 422 text is about "the selected plan", never about accessibility.

Contrast with the DRAFT case: on a `DRAFT` journey, adding the same capability returns **`201`** — the add succeeds and the failure only appears later at generate time. So the *same* declaration is accepted or rejected depending on journey state, with different failure surfaces.

### The state transition a real traveller would hit

```
DRAFT journey + HARD capability   →  add 201, generate 422
ACTIVE journey + HARD capability  →  add 422 (stranded)
ACTIVE journey, capability removed →  replan works, 201
```

There is no path from "ACTIVE journey" to "ACTIVE journey with the need respected".

---

## 7. Recovery: HTTP 201, content empty

| Case | Event | Replan HTTP | `candidate_count` | `hard_constraints_passed` | `locked_commitments_preserved` |
|---|---|---|---|---|---|
| A — supported HARD (`PLACE_UNAVAILABLE`) | 201 | 201 | **0** | `true` | `true` |
| B — HARD capability present | 201 | 201 | **0** | — | — |
| C — SOFT capability present | 201 | 201 | **0** | — | — |
| D — `PLACE_BLOCKED` | 201 | 201 | **0** | `true` | `true` |
| E — repeated 3× | 201/201/201 | 201 | **0** | — | — |
| F — failed recovery with capability | 201 | 201 | **0** | — | — |

`candidate_count` is **0 in every case, including the control case with a supported HARD constraint.** So:

- The recovery *gate* is correct: `hard_constraints_passed: true`, `locked_commitments_preserved: true`, and a blocked place does **not** reappear (`RECOVERY_PROPOSAL_PLACES.blocked_place_still_present: false`).
- But the recovery *engine* produced no candidates at all in this environment. **The quality of a recovery proposal could not be assessed** — the findings here are about refusal and emptiness, not about whether a produced proposal would have been good.

This is the most misleading pattern in the whole product: **an API that returns `201 Created` while delivering nothing.** A frontend that keys off HTTP status would render an empty success state; a monitoring system would record 100 % availability.

Field simulation agrees: **156 of 168** flows had `recovery: {skipped: "no selectable plan"}`, and the 12 that had a plan replanned at `201`.

---

## 8. What-If kept working when planning did not

`what_if_present: true` in **168 / 168** flows — including the 156 flows that had no plan at all. Sample:

```json
{"simulation_only": true, "status": "NEEDS_LIVE_EVIDENCE", "feasibility": "UNKNOWN",
 "before": {"plan_version_id": "...", "cost_minor": 37000, "walking_min": 0, "activity_count": ...}}
```
```json
{"simulation_only": true, "status": "NOT_SIMULATABLE_FROM_CURRENT_EVIDENCE",
 "feasibility": "UNKNOWN",
 "before": {"plan_version_id": null, "cost_minor": null, "walking_min": null, "activity_count": 0}}
```

This is **correct** behaviour — What-If is read-only, returns `simulation_only: true`, and honestly reports `feasibility: UNKNOWN` when there is nothing to simulate. It is the one surface in the product that tells the truth about its own ignorance.

**But note what the honest surface does not say.** `NOT_SIMULATABLE_FROM_CURRENT_EVIDENCE` never mentions that the reason is an unmodelled accessibility requirement. The traveller sees "we can't simulate this" and cannot learn why.

---

## 9. Findings index for this document

| ID | Finding | Severity |
|---|---|---|
| F2 | HARD capability blocks 156/168 flows; 98/98 flows with a declared need | **P0** |
| F5 | Capability cannot be declared mid-trip; `candidate_count: 0`; traveller stranded | **P0** |
| F4 | SOFT capability produces byte-identical plans | **P0** |
| F3 | 63 numeric/window variants collapse to 1 outcome; values never read | P1 |
| F6 | Only `DELETE` / `active=false` lifts a capability; no audit, no warning | P1 |
| — | `candidate_count: 0` even for supported HARD constraints — recovery engine yields nothing; HTTP 201 masks it | P1 |
| — | Same declaration accepted on DRAFT (`201`) and rejected on ACTIVE (`422`) — inconsistent contract | P1 |
| F18 | 1 live intake fell back to `FALLBACK/UNKNOWN` and silently dropped a wheelchair statement | P1 |

---

## 10. Acceptance criteria

1. A journey with a declared HARD capability either produces a plan **or** returns an error naming the capability — never a bare `422` about "the journey constraints".
2. A HARD capability can be added to an **ACTIVE** journey and the product returns a re-planned itinerary or an explicit, capability-named conflict.
3. `candidate_count > 0` for at least the control case (a supported HARD constraint with a feasible alternative), and a `201` with `candidate_count: 0` is treated as a failure, not a success.
4. `MAX_WALKING_PER_LEG_M` of 100 and 10 000 produce **different** outcomes; invalid types (`"500m"`, `null`, missing) are rejected at add time with a validation error, not silently collapsed.
5. A SOFT capability that cannot be satisfied produces a **stated deviation**, not a baseline plan.
6. Adding the same capability on DRAFT and ACTIVE journeys produces a consistent contract.
7. When intake falls back to the deterministic path, the product says so — a capability statement must never be silently dropped.
