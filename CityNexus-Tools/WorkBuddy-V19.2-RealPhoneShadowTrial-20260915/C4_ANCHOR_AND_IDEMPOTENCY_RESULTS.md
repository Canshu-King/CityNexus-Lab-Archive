# C4 Anchor Lifecycle — start matrix, idempotency, reason propagation

Evidence: `evidence/c4_lifecycle_a.json`, `evidence/c4_lifecycle_b.json`,
`evidence/c4_start_a.json`, `evidence/feasibility_truth_a.json`.

Method note: the V19.1 probe generated plans *after* attaching the anchor, which only ever
surfaced the collapsed 422. This round generates the plans **first**, then attaches the anchor,
then re-validates those same plans with `include_active_c4=True`. That is what makes the real
failure code visible.

---

## 1. The V19.1 `/start` → 500 is gone — but so is the ability to start

| | V19.1 (C) | V19.2 (A and B) |
|---|---|---|
| ARRIVAL @12:30 | gen 201 / sel 200 / **start 500** / stranded | gen **422** / sel 422 / start never reached |
| DEPARTURE | start 200 / ACTIVE | gen **422** |
| MID_TRIP `place-old-town` | start 200 / ACTIVE | gen **422** |
| MID_TRIP `place-riverside-museum` | start 200 / ACTIVE | gen **422** |
| ARRIVAL @07:00 (out of window) | start 200 / ACTIVE | gen **422** |
| control (no reservation) | 200 / ACTIVE | 201 / 3 plans / 200 / **200 / ACTIVE** ✅ |

`evidence/c4_lifecycle_a.json` → `any_start_5xx: false` ✅, `start_statuses: {}` ❌.

So V19.2 changed the failure mode from *"crash at start"* to *"refuse at generate"*. That is
more honest, but it means **no journey with a confirmed C4 anchor can be planned or started**.
In the V19.1 round, DEPARTURE, MID_TRIP and the out-of-window ARRIVAL all worked; all four are
now blocked. For a shadow trial that involves a booked ticket — the flagship C4 case — the
product is unusable.

## 2. The real reason, made visible

Generating first and re-validating afterwards shows every plan failing with the same code:

```
validator_before_anchor:  3/3 passed: true,  failures: []
import: 201   confirm: 200   commitment: C4_Anchored / ACTIVE
validator_after_anchor:   3/3 passed: false
    failures: ["LOCKED_COMMITMENT_LOST:ea06631e-f5b4-598a-8a96-2483c271a825"]   (ARRIVAL)
    failures: ["LOCKED_COMMITMENT_LOST:21493e6c-9533-5d97-9f04-9dcf9384f2e0"]   (DEPARTURE)
    failures: ["LOCKED_COMMITMENT_LOST:place-old-town"]                          (MID_TRIP)
```

## 3. Root cause chain

1. `app/operations/v9.py` `confirm_reservation_draft()` hardcodes `level="C4_Anchored"` and
   derives `policy_json.semantic_key`. For ARRIVAL and DEPARTURE the key is a **synthetic uuid**
   (`ea06631e-…`, `21493e6c-…`), not a place id — there is no place in the city that can ever
   carry it.
2. `app/replanning/protected_commitments.py` `active_c4_hard_constraints()` emits a HARD
   `LOCKED_COMMITMENT` constraint whose `params.semantic_ref` is that key.
3. `app/replanning/feasibility.py` `_locked_commitments()` requires a plan activity whose key
   matches `semantic_ref`. No generator ever creates such an activity.
4. Therefore every plan is infeasible, `generate` returns 422, `select` returns 422, and
   `/start` is unreachable.

Even the **MID_TRIP** case, where the anchor is a real place (`place-old-town`), fails — because
the demo plan templates never include it. **Nothing in the planner attempts to satisfy the
anchor.** A locked commitment is treated purely as a veto, never as a requirement to build
around.

## 4. Reason propagation

| Path | Status | Message |
|---|---|---|
| `select` | 422 | `"PlanVersion 55523d40-… is infeasible: LOCKED_COMMITMENT_LOST:ea06631e-…"` ✅ names the rule and the anchor |
| `generate` | 422 | `"No feasible plan candidates satisfy the journey constraints"`, `details: null` ❌ |

`evidence/lifecycle_a.json` → `conflict.accessibility_conflict`: `names_capability: false`,
`names_commitment: false` — the same collapse applies to the capability path.

**Verdict: PARTIAL — fixed at `select`, still open at `generate`.** A traveller who taps
"Generate plans" learns nothing about why nothing appeared.

## 5. C4 confirmation idempotency — **PASS**

`evidence/c4_lifecycle_a.json` → `idempotency`:

| Action | Result |
|---|---|
| Import the same `confirmation_ref` twice | 201, 201 → two drafts |
| Confirm the same draft twice | 200, 200 → commitments stay **1** |
| Confirm the sibling draft carrying the same `confirmation_ref` | **409 CONFLICT** → commitments stay **1** |
| `one_confirmation_one_commitment` | **true** |

Identical on Snapshot B. This is a clean guard: one logical confirmation produces exactly one
active commitment, and a duplicate draft cannot mint a second one.

## 6. Constraints surface does not show the C4

`evidence/lifecycle_a.json` → `conflict`: `c4_projected_into_constraints: false`, and
`constraint_codes_after_c4` is `["BUDGET_MAX", "JOURNEY_END_BY", "MINIMISE_PLAN_CHANGES"]` — no
`LOCKED_COMMITMENT`. The feasibility validator does include it (proven by
`LOCKED_COMMITMENT_LOST`), so the `/constraints` HTTP view is a different, narrower view. A
client cannot see the anchor that is blocking it.

## Exact reproduction

```
cd D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915
python tools/sync_tests.py A
python tools/v192_probe_c4_lifecycle.py A
python tools/v192_probe_feasibility_truth.py A
python tools/v191_probe_c4_start.py A        # the original V19.1 matrix, for comparison
```

## What Codex should do

1. **Bind ARRIVAL / DEPARTURE anchors to a real, routable node** instead of a synthetic uuid.
   The V19.1 round already identified that `arrival-anchor` has no routable coordinates.
2. **Make generation try to satisfy the anchor.** A `LOCKED_COMMITMENT` should steer template
   selection / activity insertion so at least one candidate contains the anchored activity.
   Today it only vetoes.
3. **When no candidate can satisfy the anchor, say so specifically** — propagate
   `LOCKED_COMMITMENT_LOST:<key>` (plus which anchor and why) into the `generate` 422 body.
4. **Surface C4 constraints in the `/constraints` view** so the client can explain the block.
5. Keep the idempotency behaviour exactly as it is — it is correct.
