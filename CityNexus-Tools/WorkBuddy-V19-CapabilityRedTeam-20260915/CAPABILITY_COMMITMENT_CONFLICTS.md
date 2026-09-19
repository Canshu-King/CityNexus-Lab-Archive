# Capability ↔ Commitment Conflicts

**Question:** when a traveller's accessibility requirement contradicts something they have already paid for, does the product tell them — or does it silently pick a side?
**Evidence:** `evidence/capability_commitment_conflicts.json`, `evidence/planner_select_recovery_probe.json`, `evidence/accessibility_truth_probe.json`

---

## 1. Why this is the hardest case in the product

CityNexus has a genuine, well-built commitment ladder. A `C4_Anchored` commitment is money already spent — in the demo seed, a paid river cruise (`place-river-cruise`, ¥120.00, `confirmation_ref: V19-CRUISE-PAID`, `level: C4_Anchored`, `status: ACTIVE`). `active_c4_hard_constraints()` translates it into a `LOCKED_COMMITMENT` HARD rule with a stable `semantic_key` and `scheduled_start_at`, and the planner is required to preserve it.

An accessibility requirement is the mirror image: also hard, also non-negotiable, but **belonging to a person rather than to a ledger**. When the two collide, the product owes the traveller an explicit statement — *"your paid cruise departs from a pier with no step-free access; here are your options"*. Anything else is the product deciding, silently, which of the traveller's commitments matters.

**Measured answer:** the product preserves the paid commitment correctly, refuses to plan, and **never tells the traveller that a conflict exists.** No surface — not the error, not `experience`, not `twin` — contains the words `conflict`, `step_free`, or `accessib`.

---

## 2. The conflict matrix

`evidence/capability_commitment_conflicts.json`

| # | Conflict | Result | C4 state | Conflict surfaced? |
|---|---|---|---|---|
| 1 | paid cruise + `STEP_FREE_REQUIRED` (wheelchair, evidence UNKNOWN) | `422` generic | **`ACTIVE`** ✔ | ✘ |
| 2 | paid rail + `MIDDAY_REST_WINDOW` | `422` generic | preserved | ✘ |
| 3 | paid dinner + `INFANT_NAP_WINDOW` | `422` generic | preserved | ✘ |
| 4 | paid cruise + `STEP_FREE_REQUIRED` **SOFT** | **`201`, 3 plans, cruise still present** | preserved | ✘ *(worst case)* |
| 5 | paid cruise, no capability (control) | `201`, 3 plans, cruise in all 3 | preserved | n/a |
| 6 | C4-protected activity closed by an event | `422 "closed activity is protected and cannot be replaced automatically"` | preserved | ✘ *(never mentions capability)* |

### Case 1 — the wheelchair traveller with a paid cruise

```
POST /journeys/{id}/constraints
  {kind: HARD, category: capability, rule_code: STEP_FREE_REQUIRED,
   params: {requirement: "VERIFIED_STEP_FREE"}}          → 201
POST /journeys/{id}/plans/generate                       → 422
  "No feasible plan candidates satisfy the journey constraints"

commitment after  → {status: "ACTIVE", level: "C4_Anchored",
                     external_ref: "V19-CRUISE-PAID", monetary_value: ¥120.00}
experience        → mentions_conflict: false
                    mentions_step_free: false
                    mentions_accessib: false
twin              → mentions_conflict: false
                    risk_reason_codes: []
```

**What is right:** `C4_STATE_AFTER_CONFLICT → exists: true, status: ACTIVE`. The product did **not** silently delete the paid commitment to make the plan work. That is a real guard and it holds.

**What is wrong:** the traveller is told *"No feasible plan candidates satisfy the journey constraints"*. They paid ¥120 for a cruise. They use a wheelchair. The product knows both facts and says neither. There is no way for them to learn:

- whether the cruise is the problem,
- whether the pier is step-free,
- whether they can keep the cruise and change the rest,
- whether cancelling is possible (`cancel_refundable_booking` exists on the agent surface but nothing tells them to use it).

### Case 4 — the SOFT case is worse than the HARD case

```
POST /journeys/{id}/constraints
  {kind: SOFT, category: capability, rule_code: STEP_FREE_REQUIRED}   → 201
POST /journeys/{id}/plans/generate                                    → 201
  plan_count: 3
  cruise_present: [true, true, true]
```

A traveller declares a step-free requirement and receives **three plans, all containing the paid cruise**, with no warning, no deviation note, and no conflict record. The HARD case at least refuses. The SOFT case **actively produces an itinerary that ignores the need and presents it as the answer.**

The recorded verdict in the probe file:

> `"a KNOWN_STAIRS conflict against a SOFT capability is silently ignored: no conflict, no warning, the traveler is never told"`

### Case 6 — the closest thing to a capability-aware message, and it still misses

When a `C4`-protected activity is closed by an event:

```
POST /replans → 422
"closed activity is protected and cannot be replaced automatically"
```

This is the **best error message in the product** — it names the *reason* (protection), not just the outcome. It proves the architecture *can* explain a protected-commitment conflict. It simply has no capability dimension to add to it, so the capability side of the conflict is invisible even here.

---

## 3. Where conflicts are *not* reported

Every traveller-facing surface was checked for conflict and capability vocabulary.

| Surface | Key / field | Conflict present? | Capability present? |
|---|---|---|---|
| `POST /plans/generate` error | `error.message` | ✘ | ✘ |
| `GET /journeys/{id}/experience` | whole payload | ✘ | ✘ |
| `GET /journeys/{id}/twin` | whole payload | ✘ | ✘ |
| `GET /journeys/{id}/twin` | `risk_reason_codes` | **`[]`** | — |
| `feasibility_envelope` (journey context) | `risk_reason_codes` | **`[]`** | — |
| `feasibility_envelope` | `robust: true` | — | — |
| Replan proposal | `explanation` | ✘ | ✘ |
| Replan proposal | `diff` | ✘ | ✘ |

`experience` payload keys: `active_plan, journey, mobility_facts, offers, options, provider_mesh, selected_option_id, traveler_twin, trip`.

Two details are worth flagging:

- **`risk_reason_codes` is empty and `robust: true`** in the same response where planning was refused for an unsupported HARD constraint. The feasibility envelope reports *robustness* while the plan does not exist. A UI that renders `robust: true` as a green badge would show a confident green badge on a journey that has no plan.
- **`mobility_facts`** is the only mobility-adjacent key — and it describes the **provider** (`mock-mobility`, `deterministic-offline`), not the traveller. The naming invites a reader to assume it covers the traveller's mobility. It does not.

---

## 4. Conflict resolution, if it existed

The two constraint kinds differ in a way that matters for design:

| | `C4_Anchored` commitment | Traveller capability |
|---|---|---|
| Owner | the traveller's wallet | the traveller's body |
| Can be cancelled? | sometimes — `cancel_refundable_booking` exists | never |
| Can be downgraded? | no | no |
| Who may override? | the traveller, explicitly | **nobody** |
| Right default on conflict | ask | refuse to plan, name the capability |

The product currently applies the *commitment* rule to both: preserve and refuse. It is the right instinct for money and the wrong framing for a body, because a capability conflict is not a planning problem — it is a **disclosure** problem. The traveller needs to be told; the product needs to stop deciding for them.

`evidence/planner_select_recovery_probe.json` shows the C4 path is otherwise sound: `locked_commitments_preserved: true` on every proposal, and a blocked place never reappears in a recovery proposal.

---

## 5. Findings index for this document

| ID | Finding | Severity |
|---|---|---|
| F7a | Paid commitment **correctly survives** a capability conflict (guard holds) | — ✔ |
| F7b | Conflict never surfaced: generic 422; `experience`/`twin` contain no `conflict`/`step_free`/`accessib`; `risk_reason_codes: []` | **P0** |
| F7c | SOFT capability vs `KNOWN_STAIRS` anchor: **3 plans generated, cruise still present, nothing said** | **P0** |
| F7d | `feasibility_envelope` reports `robust: true` while the plan does not exist | P1 |
| F7e | `mobility_facts` describes the provider, not the traveller — misleading name | P2 |
| F7f | The `closed activity is protected` message proves the architecture can explain conflicts; the capability dimension is simply absent | — (opportunity) |

---

## 6. Acceptance criteria

1. A capability that conflicts with a `C4_Anchored` commitment produces a response naming **both**: the capability (`STEP_FREE_REQUIRED`) and the commitment (`place-river-cruise` / `V19-CRUISE-PAID`).
2. `experience` exposes the conflict — e.g. `risk_reason_codes` contains a capability-vs-commitment code, or a dedicated `capability_conflicts` array.
3. A SOFT capability that conflicts with a known-obstructed anchor produces a **stated deviation** ("no step-free route to Nexus River Cruise"), never a silent plan that includes the obstructed anchor.
4. `robust` is `false`, or absent, whenever no plan exists.
5. `mobility_facts` is renamed or extended so it cannot be read as traveller capability.
6. The traveller is offered the decision: keep the commitment and accept the obstacle, or change the commitment. The product must not choose.

---

## 7. A note on why this matters more than the other findings

A traveller who is blocked from planning will try again, or use another app. A traveller who is handed **three confident plans containing a paid activity they physically cannot reach** will board that activity and discover the problem at the pier. That is the difference between a frustrating product and a harmful one, and it is why case 4 is the single most serious result in this red-team.
