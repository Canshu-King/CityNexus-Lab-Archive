# FEASIBILITY_C4_GATE_RESULTS.md — Shared gate C4 temporal truth (F01–F05)

## The defect (P0)

Snapshot F fixed the **scheduler** so it no longer *constructs* an impossible
plan, but the authoritative shared deterministic feasibility gate still
**accepted** one. Independently reproduced against the submitted V19.2.3 source:

```
ARRIVAL 12:30 + flexible POI 09:00-10:15   -> passed = true, failures = []
DEPARTURE 15:30 + flexible POI 17:00-18:30 -> passed = true, failures = []
ARRIVAL 17:00 + DEPARTURE 10:00            -> passed = true, failures = []
```

A generator that refuses to create an impossible plan is not sufficient.
`select`, `start` and revalidation must independently reject:

* plans persisted before the scheduler fix,
* imported plans,
* planner-edited plans,
* stale plans,
* and any future generator bug.

## Root cause

`evaluate_feasibility()` did not interpret `anchor_role` as structural temporal
semantics, and the earlier code widened the journey window with locked
commitment timestamps instead of enforcing ARRIVAL/DEPARTURE as boundaries.

## Implementation (`backend/app/replanning/feasibility.py`)

1. **Window widening is not used to validate anchors loosely.** The widening is
   retained only so an *anchor* that legitimately defines a trip edge is not
   rejected; it never relaxes activity boundaries.
2. `_locked_commitment_specs()` supplies each anchor's `anchor_role`,
   `time_boundary` and start minute.
3. `C4_ANCHOR_OUTSIDE_JOURNEY` is evaluated relative to the anchor-widened
   window.
4. ARRIVAL completion becomes a lower boundary; every non-anchor activity whose
   start precedes it produces `C4_ACTIVITY_BEFORE_ARRIVAL:<key>`.
5. DEPARTURE start becomes an upper boundary; every non-anchor activity whose
   end exceeds it produces `C4_ACTIVITY_AFTER_DEPARTURE:<key>`.
6. An ARRIVAL boundary later than the DEPARTURE boundary produces
   `C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE`.
7. MID_TRIP stays an interior pinned commitment handled by the existing
   lock-preservation checks.
8. Existing lock-preservation checks are untouched.
9. A valid plan still passes.

## Verified behaviour

Probe `probes/v1924_truth_probe.py` — `evidence/v1924_truth_probe.json`:

| ID | Case | Result |
| --- | --- | --- |
| F01 | pre-arrival activity | `passed=false`, `C4_ACTIVITY_BEFORE_ARRIVAL:p` |
| F02 | post-departure activity | `passed=false`, `C4_ACTIVITY_AFTER_DEPARTURE:p` |
| F03 | ARRIVAL after DEPARTURE | `passed=false`, `C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE` |
| F04 | valid ARRIVAL control | `passed=true`, `failures=[]` |

`4/4 PASS`, probe exit code 0.

## Tests that call the shared gate directly

`tests/test_v1924_final_truth_gate.py` calls `evaluate_feasibility()` on
deliberately invalid persisted plans — not the generator:

* `test_v1924_shared_gate_rejects_pre_arrival_activity` (F01)
* `test_v1924_shared_gate_rejects_post_departure_activity` (F02)
* `test_v1924_shared_gate_rejects_arrival_after_departure` (F03)
* `test_v1924_shared_gate_accepts_valid_arrival_control` (F04)
* `test_v1924_shared_gate_allows_edge_defining_departure` (F05, the ported
  semantic)

## F05 — the port, and why it exists

Applying the starter patch literally removed the window widening entirely and
broke `test_v192_defect_c4_anchor_does_not_block_all_plans[DEPARTURE-synthetic]`:
a booked 08:00 departure on a 09:00 draft Journey produced zero plans.

A confirmed reservation is an authoritative real-world fact. The port keeps the
widening for **anchor placement only** while still enforcing the
ARRIVAL/DEPARTURE boundaries for flexible activity. F05 locks that behaviour in
so it cannot silently regress.

## Also verified

The V19.2.3 scheduler boundary tests remain green (F05 in the V19.2.4 matrix is
this scheduler-regression row): the full gate suite is 86/86.
