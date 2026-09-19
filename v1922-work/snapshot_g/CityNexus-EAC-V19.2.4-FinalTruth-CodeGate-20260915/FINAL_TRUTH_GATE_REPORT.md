# FINAL_TRUTH_GATE_REPORT.md — CityNexus V19.2.4 Final Truth Code Gate

## Verdict

**SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE**

The one P0 and the two smaller inconsistencies raised by the independent audit
of Snapshot F are closed with executable evidence. The V19.2 contract remains
61/61, the V19.2.3 closure suite remains 13/13, a new 12-test V19.2.4 suite
passes, and the broad regression has **zero new failures**.

## Scope discipline

* Snapshot F (the V19.2.3 package) was frozen first.
* V19.3 was **not** started.
* No broad product features were added.
* No already-green responsive or OpenAPI path work was redone.
* HARD constraints and C4 protection were not weakened.

## The starter patch: checked, then semantically ported

`patches/V19_2_4_GPT_VERIFIED_CLOSURE.patch` was verified with
`git apply --check` (exit 0) and applied.

Applying it **literally** produced one forbidden regression:
`test_v192_defect_c4_anchor_does_not_block_all_plans[DEPARTURE-synthetic]`
failed, because the patch removed the journey-window widening entirely. In the
V19.2 contract a booked 08:00 departure on a 09:00 draft Journey must still be
plannable — the reservation is an authoritative real-world fact.

The patch was therefore **ported, not forced**, as the Road-Prep instructed:

* the anchor-window widening is **retained**, but it now only governs whether an
  *anchor* sits inside the window; it never relaxes the ARRIVAL/DEPARTURE
  boundaries that constrain flexible city activity;
* `C4_ANCHOR_OUTSIDE_JOURNEY` is evaluated relative to that anchor-widened
  window, so an edge-defining anchor is not falsely rejected;
* every other semantic from the starter patch was adopted unchanged.

Result: the V19.2.4 truth probe passes 4/4 **and** the V19.2 contract stays
61/61. The port is covered by
`test_v1924_shared_gate_allows_edge_defining_departure`.

## P0 — shared feasibility gate now enforces C4 temporal truth

**Reproduced before fixing.** Direct evaluation of the shared gate on the
submitted Snapshot F source:

```
F01 pre-arrival          -> passed = true, failures = []   (WRONG)
F02 post-departure       -> passed = true, failures = []   (WRONG)
F03 arrival-after-departure -> passed = true, failures=[]  (WRONG)
```

**After the fix** (`evidence/v1924_truth_probe.json`, 4/4 PASS):

```
F01 -> passed=false  C4_ACTIVITY_BEFORE_ARRIVAL:p
F02 -> passed=false  C4_ACTIVITY_AFTER_DEPARTURE:p
F03 -> passed=false  C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE
F04 -> passed=true   failures=[]
```

The gate now:

1. does not widen the Journey window to make an impossible anchor set valid;
2. parses `anchor_role` and `time_boundary` from `LOCKED_COMMITMENT`;
3. treats ARRIVAL completion as a lower boundary for non-anchor activity;
4. treats DEPARTURE start as an upper boundary for non-anchor activity;
5. reports ARRIVAL-after-DEPARTURE as a precise deterministic conflict;
6. reports structural anchors outside the (anchor-widened) window explicitly;
7. keeps MID_TRIP as an interior pinned commitment;
8. keeps every existing lock-preservation check active;
9. still accepts a valid plan.

Why this matters: select, start and revalidation must reject plans persisted
before the scheduler fix, imported plans, edited plans and stale plans — not
merely rely on the generator refusing to create them.

## P1 — recovery projection follows durable facts

Snapshot F permitted an open `DETECTED` Event to project `RESOLVED` from a
caller boolean while `recovery_flags` still said `recovery_required = true`.

Now:

* an open Event projects `RECOVERY_REQUIRED` or
  `RECOVERY_REQUIRED_NO_ALTERNATIVE`, never `RESOLVED`;
* only a transactional workflow that revalidates and explicitly resolves the
  Event (plan selection, capability confirmation) may close it;
* acknowledgement remains strictly non-resolving;
* `NO_ALTERNATIVE` still requires a recorded replan attempt;
* only candidate ids recorded by a real feasibility-checked replan attempt are
  advertised as recovery alternatives — arbitrary `CANDIDATE` rows are not
  proof of feasibility;
* `GET /experience` is a pure projection; it no longer calls
  `resolve_recovery_events()`.

Verified: with an open Event and `is_feasible=True`, the projection stays
`RECOVERY_REQUIRED` and agrees with the flags; three consecutive
`GET /experience` calls leave the Event `DETECTED`.

## P1 — reservation quarantine helper now agrees with the schema

`app/operations/reservation_identity.py` wrote
`event_type = RESERVATION_IDENTITY_DUPLICATE`, which violates the closed
`events.event_type` CHECK and raised `IntegrityError`.

Now the ORM helper:

* writes the sanctioned `event_type = "USER_CHANGE"` and carries
  `payload.kind = "RESERVATION_IDENTITY_DUPLICATE"`;
* excludes already-quarantined rows from duplicate detection, so a second run is
  idempotent;
* was not allowed to weaken the partial unique index or the startup migration.

Verified: 3 seeded duplicates -> one authoritative winner, two quarantined,
exactly one audit Event, second run returns `[]` with no repeated repair.

## Retest summary

| Item | Result |
| --- | --- |
| Direct F01–F04 shared-feasibility tests | **PASS 4/4** |
| V19.2 contract suite | **61/61** |
| V19.2.3 closure suite | **13/13** |
| New V19.2.4 suite | **12/12** |
| Gate suites combined | **86/86** |
| Broad backend regression | **696 passed / 2 pre-existing / 15 skipped, 0 new** |
| Frontend build | **PASS** |
| OpenAPI parity | **138/138, missing 0, extra 0** |
| Targeted mobile flows (both viewports) | **18/18, 0 page errors, 0 overflow** |
| DeepSeek canary | **not run** — no semantic/AI code changed this round |

## Explicit non-claims

* No real payment was executed.
* **No physical-device testing.** All mobile evidence is emulated viewports in
  headless Chrome and does not establish real-phone behaviour.
* The live DeepSeek canary was deliberately **not** run this round: the EAC task
  allows it only when semantic code changed, and this round touched only
  `feasibility.py`, `hard_recovery.py`, `main.py` and `reservation_identity.py`.
  The V19.2.3 canary result remains the most recent live evidence, and an
  independent Snapshot-F/G red-team plus physical-device precheck still follow
  per the Road-Prep execution order.
