# V19.2 Defect Matrix

## P0 — must be fixed before real-phone shadow trial

### P0-1 — split-brain feasibility across generate/select/booking

Measured behavior with an active C4 commitment:

```text
generate -> 201 / plans produced
validator -> the plans are infeasible: LOCKED_COMMITMENT_LOST
select -> 200
booking -> 422, selected plan is no longer feasible
```

This is a product-consistency failure, not a presentation issue.

Required direction:

- one authoritative constraint assembly for plan generation, generic composition, selection, validation and booking;
- active C4 commitments must be included consistently;
- selection must use the same feasibility truth as booking;
- preserve frozen mobility-snapshot semantics at selection time.

Relevant current code areas:

```text
backend/app/services.py
  _journey_constraints_with_capabilities
  _generic_compose_plans
  validate_plan_feasibility
  generate_plans

backend/app/main.py
  select_plan
  _assert_selected_plan_feasible
```

### P0-2 — ARRIVAL C4 can make `/start` return 500

A real ARRIVAL-anchored active C4 can lead to:

```text
POST /journeys/{id}/start -> 500
journey remains PLANNED
```

Root direction confirmed by red-team evidence: the arrival anchor can carry a semantic key with no routable coordinates, then the Twin/mobility snapshot tries to route to it.

Relevant code area:

```text
backend/app/operations/v9.py
  confirm_reservation_draft

backend/app/main.py
  _twin_snapshot
  start_journey
```

Required behavior:

- use a routable destination/coordinate/alias when one is actually available from trip context/provider data;
- if routing evidence is absent, degrade explicitly instead of throwing 500;
- start must remain transactionally safe: no half-started Journey/Twin state;
- return a recoverable reason if the product truly cannot start.

### P0-3 — residual local false-HARD cases

The V19.1 local fallback still mishandles third-party, facility-description and speculative language. Examples that must not create a user HARD wheelchair/step-free need include:

```text
I am not a wheelchair user
my friend needs a wheelchair, not me
my mother uses a wheelchair
我朋友需要轮椅
我妈妈坐轮椅
the station has an accessible toilet
车站有无障碍厕所
说不定到时候我需要轮椅
if I end up in a wheelchair I'll tell you
```

The two older mandated cases must remain green:

```text
I don't need a wheelchair, I can walk
朋友说我可能需要轮椅，但我不这么认为
```

### P0-4 — scope-aware canonicalization

Same code at TRAVELER and JOURNEY scope must survive as two distinct requirements.

Correct dedup key:

```text
(scope, code)
```

not:

```text
code
```

### P0-5 — evidence-shape and stair-conflict correctness

Required:

- list/tuple mapping values do not disappear;
- top-level evidence such as `step_free_verified` is handled consistently with nested tags;
- `wheelchair=yes + step_count=5` is a conflict, not verified step-free;
- `steps`, `step_count`, and `highway=steps` are recognized;
- route step-free remains unknown without route-level evidence;
- toilet evidence never proves whole-place/entrance/route step-free.

### P0-6 — mid-trip HARD capability must trigger a real consequence

When an ACTIVE journey confirms a new HARD capability:

- re-evaluate the active plan;
- if infeasible, create a replan proposal through the normal governed path, **or** persist an explicit no-alternative/conflict state;
- surface the result to `/experience` and `/twin`/live UX;
- do not silently mutate the active plan.

### P0-7 — numeric/time requirements must become real semantics

Must cover at least:

- walking distance limits genuinely compare against actual evidence;
- negative/absurd units are rejected or require clarification;
- kilometre input is converted correctly or explicitly rejected;
- invalid time windows are not silently converted into a usable constraint;
- REST/TOILET intervals are enforced by elapsed/continuous span rather than merely by presence;
- confirm/canonicalize performs parameter-range validation.

Road-prep policy for `0 m`: **do not persist it as a clean authoritative numeric limit in the local fallback.** Treat as clarification/special mobility requirement unless a stronger structured semantic path explicitly represents a no-walking requirement.

### P0-8 — stale candidates must not masquerade as viable

If regeneration or revalidation establishes that a candidate is infeasible, the old candidate must be marked stale/superseded/invalid or otherwise prevented from being selected as if current.

## P1 — fix in the same round if low-risk

### P1-1 — duplicate C4 confirmation reference

The same confirmation/reference must not be imported/confirmed into duplicate active commitments.

### P1-2 — reason propagation

Internal feasibility already has useful reason codes such as `LOCKED_COMMITMENT_LOST`. Preserve actionable reason codes through API and UX instead of collapsing everything to a generic "No feasible plan candidates" message.

### P1-3 — evidence policy asymmetry must be intentional

Current fail-closed/fail-open behavior differs across capability types. Document and test the intended policy rather than leaving it accidental.

### P1-4 — release truth

Regenerate V19.2 top-level status, test, changed-file, recommendation and package inventory files. No stale V18.3 headline files in the V19.2 artifact.
