# Independent audit of Snapshot F (V19.2.3)

## 1. Important reconciliation of the two uploaded packages

### WorkBuddy package

`CityNexus-WorkBuddy-V19.2.3-SnapshotE-DeltaGate-20260915.zip`

does **not** contain a final verdict on Snapshot F.

Its binding verdict is:

- frozen snapshot: V19.2.2 Snapshot E
- verdict: `BLOCKED`

Its addendum explicitly says the live tree changed while the audit was running
and that the V19.2.3 observations were in-flight only.

Therefore WorkBuddy's `BLOCKED` must not be mislabelled as a final V19.2.3
verdict.

### EAC package

`CityNexus-EAC-V19.2.3-FinalShadowTrial-CodeGate-20260915.zip`

contains Snapshot F and self-reports:

`SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE`

Many of its claimed fixes are real, but the final code still contains a shared
feasibility-gate gap that the EAC regression suite does not cover.

---

## 2. Confirmed positive fixes in final V19.2.3

Independent inspection/replay confirmed:

- scheduler now treats ARRIVAL as a lower boundary;
- scheduler now treats DEPARTURE as an upper boundary;
- impossible ARRIVAL-after-DEPARTURE generation is rejected;
- RecoveryRequiredPanel now uses governed `Acknowledge warning`;
- acknowledgement calls the backend and does not hide the banner;
- legacy duplicate startup migration works;
- partial reservation uniqueness index is enforceable;
- V19.2.3 patch passes `git apply --check` against the explicitly LF-normalised
  V19.2.1 baseline;
- package hygiene is materially improved;
- DeepSeek canary evidence is present and does not contain the API key.

---

## 3. P0 still open: shared deterministic feasibility gate accepts impossible C4 timelines

The scheduler is fixed, but the authoritative shared feasibility gate is not.

Direct evaluation against the final submitted V19.2.3
`app/replanning/feasibility.py` produced:

### Confirmed ARRIVAL at 12:30 + flexible POI 09:00-10:15

Result:

`passed = true`
`failures = []`

Expected: FAIL.

### Confirmed DEPARTURE at 15:30 + flexible POI 17:00-18:30

Result:

`passed = true`
`failures = []`

Expected: FAIL.

### ARRIVAL 17:00 + DEPARTURE 10:00

Result:

`passed = true`
`failures = []`

Expected: precise C4 ordering conflict.

This is important because select/start/revalidation must protect against:

- plans persisted before the scheduler fix;
- imported plans;
- edited plans;
- stale plans;
- any future generator bug.

A scheduler that refuses to create an impossible plan is not enough. The shared
truth gate must independently reject one.

### Root cause

`evaluate_feasibility()` still does not interpret `anchor_role` as structural
temporal semantics. The previous code also widened the journey window with
locked commitment timestamps rather than enforcing ARRIVAL/DEPARTURE boundaries.

The V19.2.3 tests assert timestamps on newly generated schedules but do not call
the shared feasibility gate with deliberately invalid persisted plans.

---

## 4. Recovery projection remains structurally inconsistent

Against final V19.2.3, WorkBuddy's recovery probe was rerun with the submitted
source.

With an open `DETECTED` recovery Event and `is_feasible=True`:

- `recovery_state.state = RESOLVED`
- `event_status = DETECTED`
- `recovery_flags.recovery_required = true`

So the primitive can still say "resolved" while durable truth says "open".

The normal plan-selection path now resolves the Event transactionally, which is
good. But `GET /experience` also calls `resolve_recovery_events()` from a read
path and does not itself commit the session. A GET should not be relied on as a
durable state transition.

Recommended invariant:

- an open recovery Event never projects `RESOLVED`;
- only a transactional, revalidated state-changing workflow resolves it;
- arbitrary `CANDIDATE` rows are not advertised as feasible alternatives unless
  an actual replan outcome recorded them.

---

## 5. Reservation ORM quarantine helper is still inconsistent with the schema

The startup migration itself is fixed and independently replayed successfully.

However:

`app/operations/reservation_identity.py::quarantine_duplicate_confirmation_identities()`

still writes:

`event_type = RESERVATION_IDENTITY_DUPLICATE`

while `events.event_type` is a closed schema vocabulary.

Direct execution against a duplicate DB raises an SQLite CHECK-constraint
`IntegrityError`.

The helper is called from the reservation-confirm flow. Normal startup migration
should usually remove the duplicates before this path, so this is smaller than
the temporal P0, but the helper must still agree with the schema.

Recommended:

- use sanctioned `event_type = USER_CHANGE`;
- carry `kind = RESERVATION_IDENTITY_DUPLICATE` in payload;
- exclude already-quarantined rows from duplicate detection so the repair is
  idempotent.

---

## 6. Independent status

Snapshot F independent verdict:

`BLOCKED_PENDING_V19_2_4_TRUTH_CLOSURE`

Do not perform the formal physical-device shadow trial yet.
