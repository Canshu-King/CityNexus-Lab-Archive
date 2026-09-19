# C4_ANCHOR_RESULTS.md — C4 anchored commitments become satisfiable

## Requirement

A confirmed `C4_Anchored` reservation must be a constraint the planner can
**satisfy**, not only a veto. ARRIVAL, DEPARTURE and MID_TRIP must all produce a
real plan that can be selected and started; C4 must survive replanning; an
unresolvable location must keep its temporal commitment plus explicit
unresolved evidence; an impossible anchor must produce a specific conflict
reason; C4 validation must not be weakened.

## Root cause (from the WorkBuddy handoff, confirmed in source)

`confirm_reservation_draft` derived ARRIVAL/DEPARTURE `semantic_key` values from
an unresolvable synthetic `uuid5`. `LOCKED_COMMITMENT` in
`protected_commitments.py` could only reject candidates, and nothing in
`services.generate_plans` ever emitted a matching activity. Every plan was
therefore vetoed for a booked traveller.

## Implementation

### 1. Canonical structural identity — `app/planning/anchors.py` (new)

* `ARRIVAL_ROLE` / `DEPARTURE_ROLE` / `MID_TRIP_ROLE`, `ANCHOR_ROLES`.
* `structural_place_id(journey_id, role) -> "v12:{journey_id}:{key}"` — the
  same identity `app/planning/authoritative_v12.py::_ensure_place` already uses,
  so generation, C4, frozen evidence, persistence, selection, booking, start
  and replanning all agree.
* `normalise_role()` returns `""` for a missing role. This is deliberate and
  load-bearing: a booking/order C4 anchor has no reservation role and must
  never be treated as an ARRIVAL anchor.
* `is_reservation_anchor()`, `time_boundary_for()`, `resolve_anchor_key()`,
  `anchor_identity_from_policy()`.

`app/operations/v9.py::confirm_reservation_draft` now calls
`resolve_anchor_key(role=..., intent_key=..., journey_id=...)` and persists
`location_evidence` into the commitment policy. No synthetic uuid5 remains.

### 2. The generator satisfies the anchor — `app/planning/anchor_schedule.py` (new)

* `resolve_plan_anchors(session, journey)` -> `(resolved, unresolved)`.
  Booking/order anchors (no role) are skipped here; they are protected through
  `activity_id` instead.
* `schedule_template_with_anchors(...)` pins each anchor to its exact committed
  time, re-times optional POIs around it using real frozen travel times, drops
  POIs that cannot fit, and returns `None` when the anchor genuinely cannot be
  met.
* `effective_journey_window(...)` widens the draft window to contain confirmed
  anchors — a booked 08:00 departure is a real fact and must not be made
  unplannable by a 09:00 draft start.
* `anchor_assignment_for_activities(...)` maps commitment keys to activities.

The same injection was added to the explicit-POI compose path
(`_inject_anchors_into_generic` in `app/services.py`).

### 3. One shared window rule

`app/replanning/feasibility.py::evaluate_feasibility` widens the effective
window from the active `LOCKED_COMMITMENT` constraints themselves. Because
generation, select, booking and start all run through the same gate, they
cannot disagree about the same commitment.

### 4. `protected_commitments.py`

`LOCKED_COMMITMENT` now carries a concrete `semantic_ref`, plus
`anchor_role`, `generator_owns_anchor`, `location_evidence` and
`time_boundary` (END for DEPARTURE, START otherwise). A missing identity on a
reservation anchor emits `UNRESOLVED_COMMITMENT_ANCHOR`; a booking anchor with
no identity is left to the existing `activity_id` protection path.

### 5. Specific conflict reasons

* Unresolvable location -> `C4_ANCHOR_UNRESOLVED:<role>:<key>`.
* Anchor cannot be met -> `C4_ANCHOR_UNSATISFIABLE` / `C4_ANCHOR_BLOCKED:<keys>`.
* An anchor that is genuinely outside the achievable window is reported by the
  gate as `LOCKED_COMMITMENT_LOST:<semantic_ref>` with the real reference, not
  an anonymous sentence.

## Evidence

### Acceptance matrix — `evidence/acceptance_matrix_d.json`

| Case | import | confirm | generate | plans | select | start | journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ARRIVAL | 201 | 200 | 201 | 3 | 200 | 200 | ACTIVE |
| DEPARTURE | 201 | 200 | 201 | 3 | 200 | 200 | ACTIVE |
| MID_TRIP | 201 | 200 | 201 | 3 | 200 | 200 | ACTIVE |
| control | — | — | 201 | 3 | 200 | 200 | ACTIVE |

### Contract tests

`tests/test_v192_shadow_trial_gate.py` — **61 passed**, including
`test_v192_defect_c4_anchor_does_not_block_all_plans[ARRIVAL|DEPARTURE|MID_TRIP]`.

### Replanning preserves C4

Verified: after start, regenerating plans keeps the commitment `C4_Anchored`
/ `ACTIVE` with `activity_id` bound, and the new plan selects 200. The
regenerated plan contains the canonical structural activity
(`v12:{journey_id}:arrival-anchor`, `activity_type = arrival`).

### Independent probes

* `v192_probe_c4_lifecycle.py`: `any_start_5xx = false`,
  `one_confirmation_one_commitment = true`.
* `v191_probe_c4_start.py`: `any_stranded = false`, `stranded_roles = []`.

### Validation not weakened

`LOCKED_COMMITMENT` still hard-fails a candidate whose activities do not contain
the committed semantic reference. The change makes the constraint *satisfiable*;
it does not relax it. Plans generated before the anchor was attached continue
to be rejected (422) — that is the correct signal, and the probe's
`anchor_blocks_existing_plans` reflects exactly that.
