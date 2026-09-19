# Accessibility Truth Findings

**Scope:** what CityNexus actually knows about a traveller's body, what it claims to know, and where a real traveller gets hurt.
**Evidence:** `evidence/accessibility_truth_probe.json`, `evidence/boundary_and_drop_probe.json`, `evidence/scenario_results.jsonl`, `evidence/semantic_live_results.jsonl`

---

## 0. The question this document answers

The task book's highest-priority attack is *"UNKNOWN accessibility treated as verified"*. This document reports what was measured, including where the answer is **not** the expected one.

**Answer in one line:** the product never treats UNKNOWN as *verified* — it treats it as **nothing at all**. There is no place in the system where a traveller's accessibility need can be represented, so UNKNOWN cannot be distinguished from VERIFIED, and the traveller's only route to a plan is to delete their own requirement.

---

## 1. What the requirements baseline actually asks for

The baseline holds **138 requirements** — 8 BG, 61 FR, 24 BR, 16 NFR, 15 IR, 14 SR — and **all 138 are `status: proposed`** (none approved).

Searching the whole baseline for accessibility yields exactly **one** requirement:

```yaml
- id: NFR-014
  type: non_functional_requirement
  title: Accessible Critical State and Controls
  statement: Critical state shall not be communicated by color alone and primary
    controls shall support keyboard interaction and text labels.
  priority: S
  acceptanceCriteria:
    - id: NFR-014-AC-01
      condition: Given critical-state components and primary controls, when
        accessibility inspection and keyboard testing are performed
      expectedResult: Critical state has a non-color indicator, and each primary
        control has an accessible text label and keyboard operation.
      verificationMethod: accessibility_test
  verificationMethod: accessibility_test
  status: proposed
```

Every other `accessib*` hit in the repository is generic English — *"journey data remains accessible"*, *"existing Journey data remains accessible"*. There is **no requirement** for:

- step-free / wheelchair routing
- maximum walking distance or continuous-walking time
- midday rest windows, infant nap windows
- stroller access, large luggage handling
- quiet / low-sensory environments
- toilet availability or frequency
- conflicting needs within a family party

**Consequence:** the product's accessibility commitment is *"make the UI usable by a screen reader"*. It is not *"know what the traveller can physically do"*. Every capability finding below is a consequence of that scope choice, not of a bug in a capability module — **there is no capability module.**

Note the one thing that *is* specified: `NFR-014` names `verificationMethod: accessibility_test` and asks for non-colour indicators and labelled controls. That is exactly what the axe-core scan in `WEB_MOBILE_CAPABILITY_RESULTS.md` measures, and it is the only accessibility claim this red-team could find a yardstick for.

---

## 2. What the code actually implements

| Term | Hits in `backend/app/` + `frontend/src/` |
|---|---|
| `step_free` / `step-free` | **0** |
| `wheelchair` | **0** |
| `stroller` | **0** |
| `accessib*` | **1**, and it is a CSS comment: `/* Progressive disclosure, mobile comparison, and accessible focus states. */` |
| `MAX_WALKING_PER_LEG_M` | **0** |
| `MIDDAY_REST_WINDOW` / `INFANT_NAP_WINDOW` / `QUIET_ENVIRONMENT` / `LARGE_LUGGAGE` | **0** |

The word **"capability" does appear** in the backend — 25 occurrences — but every one is infrastructure:

```
app/integrations/registry.py        capability-first provider selection
app/integrations/provider_status.py capability: str
app/integrations/push.py            push_capability() -> "WEB_PUSH_CONFIGURED"
app/integrations/mobility/runtime.py provider_capabilities / capability_by_deployment
app/main.py:484                     "Expose non-secret native Hermes capability facts"
```

The only module that extracts anything about a traveller's *needs* is `app/planning/day_rhythm.py` — wake/bed times, brunch, late-night, skip-breakfast. **No accessibility concept.**

The only vocabulary that *looks* like it could carry a capability is the semantic compiler's free-form `constraints` array. It is `additionalProperties: true`, so the model can emit any capability key it likes — and §4 shows exactly what happens to it.

---

## 3. The measured truth table

Every row is a real HTTP call against the isolated app (`evidence/accessibility_truth_probe.json`, `boundary_and_drop_probe.json`).

| Capability declared | Kind | Generate | Plans returned | Identical to baseline |
|---|---|---|---|---|
| *(none)* | — | `201` | 3 | — (baseline) |
| `STEP_FREE_REQUIRED` | HARD | `422` | 0 | n/a |
| `STEP_FREE_REQUIRED` (evidence UNKNOWN) | HARD | `422` | 0 | n/a |
| `STEP_FREE_REQUIRED` | SOFT | `201` | 3 | **yes — byte-identical** |
| `MAX_WALKING_PER_LEG_M` | HARD | `422` | 0 | n/a |
| `QUIET_ENVIRONMENT` | HARD | `422` | 0 | n/a |
| `MIDDAY_REST_WINDOW` | HARD | `422` | 0 | n/a |
| `INFANT_NAP_WINDOW` | HARD | `422` | 0 | n/a |
| `LARGE_LUGGAGE` | HARD | `422` | 0 | n/a |
| `STROLLER_ACCESS_REQUIRED` | HARD | `422` | 0 | n/a |
| `BUDGET_MAX 100` *(control, a supported code)* | HARD | `422` | 0 | n/a |
| `category="capability"` with **empty** `rule_code` | HARD | `422` | 0 | n/a |

Two readings matter:

- **The control row is the tell.** `BUDGET_MAX 100` is a *supported* rule and refuses for a real reason (the journey cannot be done under ¥1.00). `STEP_FREE_REQUIRED` refuses because **the gate does not know the word**. Both return the same `422` and the same message. The traveller cannot tell "your budget is too small" from "we do not understand your wheelchair".
- **`category="capability"` with an empty rule code also refuses.** The gate keys off the rule *code*, never the category — so there is no category-level handling to extend either.

---

## 4. The evidence question: UNKNOWN vs VERIFIED

### 4.1 UNKNOWN is not treated as verified — the fail-closed gate holds

Declaring the need with `params={"requirement": "VERIFIED_STEP_FREE"}` and with `params={"evidence": "UNKNOWN"}` produce **the same `422`**. The gate never inspects evidence, so it can never mistake UNKNOWN for VERIFIED. **This is the safe direction and must not be weakened.**

This is the accidental safety property of `app/replanning/feasibility.py`:

```python
elif code not in {"LOCKED_COMMITMENT"}:
    # A hard rule that the gate cannot interpret must never be bypassed
    # by scoring or persistence.
    failures.append(f"UNSUPPORTED_HARD_CONSTRAINT:{code or category}")
```

Because *no* capability code is interpretable, *every* capability fails closed. A future fix that adds capability codes to the interpreted set **removes this protection** and must replace it with an explicit evidence model.

### 4.2 …but UNKNOWN is also not represented as UNKNOWN

`capability_path_exists` is **false for all 494** live semantic cases, and `server_canonical_capability` is **null for all 494**. There is no field anywhere that says "this traveller's step-free requirement is UNVERIFIED". The `422` says:

> `No feasible plan candidates satisfy the journey constraints`

Not *"accessibility unknown"*. Not *"venue has no lift data"*. The word `accessib` never appears in the error, in `experience`, or in `twin`.

**So the traveller-facing truth is neither "verified" nor "unknown" — it is absent.** And absence is the worst of the three, because:

1. The Copilot **actively reframes the need as a preference.** Measured end-to-end (`evidence/copilot_injection_probe.json`):

   | Raw text | Copilot intent | Copilot reply |
   |---|---|---|
   | `必须全程无障碍，一步楼梯都不能走` | `PREFERENCE_CHANGE` | *"已识别为偏好请求。当前只展示请求，不会静默修改 TravelerTwin；请通过明确的偏好更新动作继续。"* |
   | `最好少走点楼梯` | `PREFERENCE_CHANGE` | **identical** |

   A traveller who said *"not one step of stairs"* is told their requirement is a *preference*, in the same words used for *"I'd rather not"*.

2. **A SOFT declaration is answered with a plan that ignores it.** `201 Created`, 3 plans, byte-identical to the no-capability baseline. The traveller reads a success response and boards the trip.

3. **The only escape is deletion.** `DELETE` the constraint → `204` → planning resumes. `active=false` → planning resumes. Neither is audited, neither is warned about in any UI surface.

### 4.3 The practical trap

A wheelchair traveller's realistic sequence:

```
1. POST /journeys/{id}/constraints   {kind: HARD, category: capability,
                                      rule_code: STEP_FREE_REQUIRED}   → 201
2. POST /journeys/{id}/plans/generate                                  → 422
   "No feasible plan candidates satisfy the journey constraints"
3. (no plan, no explanation, no capability language)
4. DELETE /journeys/{id}/constraints/{cid}                             → 204
5. POST /journeys/{id}/plans/generate                                  → 201, 3 plans
```

Step 4 is the product teaching the traveller to delete their own accessibility requirement in order to use the app. Nothing in the product discourages it.

---

## 5. Numeric needs are not read at all

`MAX_WALKING_PER_LEG_M` with **15** distinct values produced **one** distinct outcome (`evidence/boundary_and_drop_probe.json`):

| Variant | Value | Outcome |
|---|---|---|
| `zero` | `0` | `422` |
| `one` | `1` | `422` |
| `hundred` | `100` | `422` |
| `just_below_500` | `499` | `422` |
| `at_500` | `500` | `422` |
| `just_above_500` | `501` | `422` |
| `thousand` | `1000` | `422` |
| `huge` | `10 000 000` | `422` |
| `negative` | `-5` | `422` |
| `string_numeric` | `"500"` | `422` |
| `string_units` | `"500m"` | `422` |
| `null` | `null` | `422` |
| `absent` | *(key missing)* | `422` |
| `wrong_key` | `{"limit": 500}` | `422` |
| `km_key` | `{"max_walking_per_leg_m_km": 0.5}` | `422` |

`distinct_outcomes = 1`.

The same collapse holds for `MIDDAY_REST_WINDOW`, `INFANT_NAP_WINDOW`, `MAX_CONTINUOUS_WALKING_MIN` and `REST_EVERY_MIN` across normal / cross-midnight / start-after-end / equal / invalid-text / hour-24 / empty / minutes-only / zero / negative — **48 further variants, all `422`**.

**Impact on a real traveller:** an elderly walker whose limit is 100 m and a hiker whose limit is 10 km get the same answer. A traveller whose nap window is 13:00–15:00 and one who typed `start=15:00, end=13:00` (nonsense) get the same answer. The product cannot tell a *tight* budget from an *impossible* one, from a *typo*.

---

## 6. Mid-trip declaration: the stranding bug

`evidence/planner_replan_capability_probe.json`

| Step | Result |
|---|---|
| Generate + select + start journey | `201 / 200 / 200` — journey `ACTIVE` |
| Add `STEP_FREE_REQUIRED` while ACTIVE | `422 Constraint would make the selected plan infeasible: UNSUPPORTED_HARD_CONSTRAINT:STEP_FREE_REQUIRED` |
| Post a `CLOSURE` event | `201` |
| `POST /replans` | `201`, `candidate_count: 0` |
| Journey state afterwards | `status: ACTIVE`, `active_plan_version_id` unchanged |

The traveller is mid-trip, has just told the product about a real need, and:

- cannot add the need,
- cannot get a recovery candidate,
- is still nominally on a plan that ignores it,
- and receives no message naming the problem.

Repeated three times, `candidate_count` stayed `0` every round (`E_REPEATED_RECOVERY_STABILITY: [201, 201, 201]` — HTTP succeeds, content is empty). This is the single most dangerous pattern in the findings: **the API returns success while delivering nothing.**

---

## 7. What is genuinely right, and must be preserved

| Property | Evidence | Why it matters |
|---|---|---|
| Fail-closed on uninterpretable HARD rules | every capability → `422` | no capability can be silently scored away |
| The paid commitment survives a conflict | `C4_STATE_AFTER_CONFLICT: status ACTIVE` | the product does not delete a paid anchor to satisfy a need |
| A blocked place stays blocked in recovery | `RECOVERY_PROPOSAL_PLACES.blocked_place_still_present: false` | recovery honours supported HARD constraints |
| Learned evidence never escalates to HARD | `learned_created_any_constraint: false` | the twin cannot invent a disability |
| Agent commands never mutate constraints | 7/7 injections, `constraints_unchanged: true` | the agent cannot weaken a need |
| `active=false` leaves the row visible | `DROP_active_audit` shows the row with `active: false` | the capability is not *deleted*, just silenced — a hook for auditing |

---

## 8. Findings index for this document

| ID | Finding | Severity |
|---|---|---|
| F1 | No traveller-capability domain; 1 of 138 requirements, and it is about UI colour | **P0** |
| F2 | HARD capability blocks 98/98 affected flows (fail-closed — correct, but total) | **P0** |
| F3 | Numeric values never read; 63 variants collapse to one outcome | P1 |
| F4 | SOFT capability is entirely inert; plans byte-identical to baseline | **P0** |
| F5 | Capability cannot be declared mid-trip → traveller stranded with `candidate_count: 0` | **P0** |
| F6 | `DELETE` / `active=false` silences a HARD capability with no audit and no warning | P1 |
| F7 | Capability-vs-commitment conflict never surfaced; generic 422 only | **P0** |
| F9 | Negation/history do not resolve; 10/56 flagged, 0 resolved, route is a dead end | P1 |
| F16 | No capability audit vocabulary (`constraint.created` is the only action) | P1 |

---

## 9. Acceptance criteria for "fixed"

A capability surface is trustworthy when **all** of the following hold. These are written as testable statements; the corresponding regression tests live in `tests/test_v19_capability_redteam.py` and currently lock the *opposite* behaviour as characterisation tests.

1. `STEP_FREE_REQUIRED` with evidence `UNKNOWN` is **distinguishable** from evidence `VERIFIED_STEP_FREE` — different plan outcome, different message.
2. A HARD capability can be **declared on an ACTIVE journey** and the product returns a plan or an explicit, capability-named conflict — never a bare `422` and never a silent empty proposal.
3. A SOFT capability that cannot be satisfied produces a **stated** deviation ("no step-free option found for Riverside Museum"), not a silent baseline plan.
4. `MAX_WALKING_PER_LEG_M = 10 000` and `= 100` produce **different** outcomes.
5. Any capability mutation (create / weaken / delete / deactivate) writes an **audit entry** naming the capability.
6. A capability that conflicts with a `C4_Anchored` commitment produces a message naming both the capability and the commitment.
7. `NEGATED` capability statements produce an explicit **removal** action, not route `UNKNOWN`.
8. The Copilot reply for `必须全程无障碍` never says *"偏好请求"*.
