# CODE_GATE_REPORT.md — CityNexus V19.2.2 RealPhone Code Gate

## Verdict

**SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE**

The code gate is closed: the authoritative V19.2 contract is 61/61, the broad
backend regression has **zero new failures** and 39 previously failing tests
fixed, and every P0/P1 workstream in this round has executable evidence.
The remaining gate is physical-device trial, which cannot be performed here.

## Scope discipline

This round was a **constrained gate-closure**, not a product expansion.

* No V19.3 work was started.
* No broad new feature surface was added. The only new frontend surface is the
  recovery/stale panel the P1 workstream explicitly requires.
* Unrelated architecture was not redesigned.
* Frozen history was not rewritten.
* Coursework / Visio material was not touched.
* No release artifacts were written into source directories.
* All work is on `eac/v19.2.2-realphone-codegate`.

## What was actually wrong (root causes)

### C4 anchors were a veto with no satisfier

A confirmed reservation produced a `C4_Anchored` commitment whose
`semantic_key` was an unresolvable synthetic `uuid5` for ARRIVAL/DEPARTURE.
`LOCKED_COMMITMENT` could therefore only ever *reject* candidates; nothing in
the generator could ever satisfy it. Result: a booked traveller could not
produce, select or start any plan.

Fix (option a + b + c from the handoff, all three, as required):

1. **Canonical structural identity.** ARRIVAL/DEPARTURE anchors resolve to the
   concrete structural Place id `v12:{journey_id}:{arrival-anchor|departure-anchor}`,
   the same identity the authoritative V12 planner already uses.
2. **The generator injects the anchor activity.** A new
   `app/planning/anchor_schedule.py` pins each resolved anchor into the
   candidate schedule before the gate runs, re-timing optional POIs around it
   and dropping POIs that cannot fit rather than corrupting the plan. The same
   injection was added to the explicit-POI (`place_ids`) compose path.
3. **Unresolved anchors stay explicit.** A genuinely unresolvable location
   keeps its temporal commitment and raises `C4_ANCHOR_UNRESOLVED:<key>`;
   an unsatisfiable anchor raises `C4_ANCHOR_UNSATISFIABLE`. Neither pretends
   to be satisfied, and C4 validation was not weakened.

A confirmed reservation is also treated as an authoritative real-world fact:
the effective feasibility window expands to contain it, computed in one shared
place (`evaluate_feasibility`) so generation, select, booking, start and
replanning cannot disagree.

### The booking/order C4 anchor was being corrupted

A second, different C4 shape exists: booking/order commitments promote a
concrete Activity and carry **no** `anchor_role`. The first version of the
anchor rewrite treated a missing role as ARRIVAL and rewrote those commitments
to the structural node, which broke every booking-protected plan
(40 tests). Fixed by making "no role" mean "not a reservation anchor":
booking/order anchors keep their own activity-anchored identity and are
protected through `activity_id`. This is why the broad regression moved from
41 baseline failures to 2.

### Mobility identity drift

`Activity.metadata.semantic_key` is now the single stable routing/feasibility
identity and `Activity.place_id` is the database Place identity. The gate keys
on `semantic_key` at generation, selection, booking, start and replanning. The
V19.2.1 "temporary rebind" in `app/operations/v9.py` that translated frozen
facts from semantic node keys to concrete Place ids was **deleted**, not
extended: with one canonical identity the stored evidence is already exactly
what the gate needs.

### Numeric language corruption

The clause splitter treated `.` as a sentence separator, so `1.5` was split
into `1` and `5`. Fixed with a decimal-safe split (`(?<!\d)\.(?!\d)`), explicit
unit kinds (distance vs duration), explicit scope tokens (daily vs per-leg),
half-up rounding for sub-metre values, and a zero-metre policy that preserves
the parsed value but marks it `needs_clarification` at `STRONG` severity so it
is never a clean HARD cap.

### Stale evidence could still start a journey

`/start` did not apply the select/booking truth policy. It now revalidates the
selected plan and refuses with `STALE_RECOMPOSE_REQUIRED` (409) without
transitioning the Journey to ACTIVE. The condition is exposed to the phone
through `/experience` (`experience_flags.staleness`), independent of whether a
recovery event exists.

### Mid-trip HARD recovery was response-only

A newly confirmed HARD capability on an ACTIVE journey now writes a **durable**
recovery Event (`app/planning/hard_recovery.py`), leaves the active plan
untouched, and surfaces a governed state (`RECOVERY_REQUIRED`) with explicit
user actions. The phone renders it as a visible panel with "Generate new
options" and "Continue without changes". It is never only inside one response
body, and the plan is never silently mutated.

### Concurrent C4 confirmation

`/inbox/{draft}/confirm` now handles `IntegrityError` explicitly (pre-flush and
on commit), converging racing confirmations onto a single
`TransportReservation` identity and returning the existing artifact or a
deterministic 409 — never a 500. Historical duplicates are detected, reported
and quarantined by `app/operations/reservation_identity.py` before the unique
identity is relied upon.

### Provider evidence scope

* `wheelchair=yes` + `step_count=5` / `steps=yes` -> `ACCESSIBILITY_CONFLICT`.
* Top-level and nested (`tags` / `osm_tags`) forms now reach the evaluator
  identically; the whitelist previously dropped `step_free_verified`.
* A route without route-level proof stays `NEEDS_LIVE_EVIDENCE`.
* Facility tags (`toilets:wheelchair=yes`, `ramp=yes`, `elevator=yes`) never
  prove a whole place or a route step-free.
* Walking distance is mode-aware: `WALK` may use `distance_m`, motorised modes
  require an explicit `walking_distance_m`, and a total route distance is never
  promoted to a walking budget (unavailable -> `NEEDS_LIVE_EVIDENCE`).

## Contract and frontend

`contracts/openapi.yaml` was extended only for the response shapes this round
actually changed: journey capability confirm (`recovery`), `/experience`
(`recovery`, `experience_flags`), `/start` (409 semantics) plus the new
`RecoveryState` schema. Path parity is unchanged and re-verified:
**formal 137 / runtime 137 / missing 0 / extra 0**. The generated frontend API
types were regenerated from the updated contract; the frontend builds cleanly.

## Regression accounting

| | Baseline V19.2.1 | V19.2.2 |
| --- | --- | --- |
| Broad backend failures | 41 | **2** |
| New regressions | — | **0** |
| Fixed | — | **39** |

Both remaining failures are pre-existing and mutually contradictory with other
tests in the repository; see `TEST_RESULTS.md` §2.1 for the proof.

## Explicit non-claims

* No real payment was executed.
* No physical-device testing was performed; all mobile evidence is emulated
  viewports in headless Chrome.
* No live DeepSeek call was made (no provider credentials); the conservative
  local fallback is what is verified.
