# Independent review of EAC V19.2.2

## What is genuinely improved

The V19.2.2 package is materially better than V19.2.1:

- WorkBuddy V19.2 contract evidence reports 61/61.
- Broad backend regression reports 671 passed, 2 pre-existing contradictory failures, 15 skipped, and zero new failures.
- C4 ARRIVAL/DEPARTURE/MID_TRIP generation/select/start has executable acceptance evidence.
- Canonical mobility identity now prefers `Activity.metadata.semantic_key`.
- Decimal walking limits and duration-vs-distance scope are materially improved.
- Stale evidence now blocks `/start`.
- Mid-trip HARD capability now creates a durable recovery Event and a visible mobile panel.
- OpenAPI path parity remains 137/137.
- Package hygiene is much cleaner: no DB/log/cache payload pollution was found in the review ZIP.

## Blocker 1 — C4 temporal semantics are still wrong

The contract test only proves that a plan exists. It does not prove that the plan is temporally possible relative to the reservation.

Direct independent execution of `schedule_template_with_anchors()` against the submitted V19.2.2 source produced:

### ARRIVAL at 12:30

```
POI1     09:00-10:15
ARRIVAL  12:30-12:50
POI2     13:20-14:20
POI3     17:00-18:30
```

A traveller cannot visit a city POI before arriving in the city.

### DEPARTURE at 15:30

```
POI1       09:00-10:15
POI2       13:20-14:20
DEPARTURE  15:10-15:30
POI3       17:00-18:30
```

A traveller cannot continue a city itinerary after departing the city.

Root cause:

- `schedule_template_with_anchors()` interleaves the anchor but does not enforce ARRIVAL as the lower temporal boundary or DEPARTURE as the upper temporal boundary.
- `effective_journey_window()` and `evaluate_feasibility()` widen the draft window with `min(start, anchor_start)` / `max(end, anchor_end)`, which can preserve impossible pre-arrival/post-departure flexible activities.

Required invariant:

- no flexible activity before confirmed ARRIVAL;
- no flexible activity after confirmed DEPARTURE;
- MID_TRIP remains an interior pinned anchor;
- multiple anchors must be chronologically consistent;
- impossible combinations must fail with a precise conflict.

## Blocker 2 — HARD recovery can be dismissed client-side without governance

`RecoveryRequiredPanel.tsx` exposes a button labelled:

`Continue without changes`

Its implementation only calls `setDismissed(true)`.

It does not:

- call a backend acknowledgement endpoint;
- persist an acknowledgement;
- change the recovery Event state;
- preserve a visible warning after acknowledgement;
- distinguish a HARD safety need from a merely informational warning.

For a confirmed HARD requirement, a client-only hide button violates the CityNexus truth policy. A user must never be allowed to make an infeasible plan look healthy merely by dismissing a panel.

For stale evidence, the same component also exposes this button, which is misleading.

Required behaviour:

- replace unsafe wording with governed acknowledgement semantics;
- acknowledging must never mark an infeasible plan safe;
- recovery/staleness must remain visible in the journey truth state until resolved;
- if the journey is already ACTIVE, the product may acknowledge the warning but must continue to label the current plan unverified/infeasible.

## Blocker 3 — recovery Event lifecycle does not actually resolve after selecting a feasible replacement

`resolve_recovery_events()` is only called from capability confirmation when the current plan immediately becomes feasible.

It is not called after selecting a newly generated feasible replacement plan.

`recovery_state()` can project `state = RESOLVED` while the underlying Event remains `DETECTED`, and `/experience` can then expose inconsistent flags (`recovery` projected resolved while `recovery_required` remains truthy).

Required:

- after a feasible replacement is selected/activated, resolve the durable recovery Event transactionally;
- `/experience.recovery`, `experience_flags`, Event.status and UI must agree;
- reopening the page must not resurrect an already-resolved recovery.

## Blocker 4 — explicit NO_ALTERNATIVE is claimed but not implemented reliably

`hard_recovery.py` defines `RECOVERY_REQUIRED_NO_ALTERNATIVE`, but `recovery_state()` chooses it from `is_feasible is None`, not from a verified "replan attempted and zero feasible alternatives" fact.

The UI's `Generate new options` calls the ordinary plan-generation endpoint. A failed generation does not persist a no-alternative recovery state.

Required:

- persist a real replan-attempt outcome;
- zero feasible alternatives => durable explicit NO_ALTERNATIVE state;
- candidates must be feasibility-checked against the current HARD capability and C4 set;
- do not infer no-alternative merely from a missing feasibility boolean.

## Blocker 5 — stale candidates are still ordinary `CANDIDATE` rows

Existing evidence proves selection refuses stale candidates, but the red-team evidence itself records:

`candidate_still_listed = true`

with status `CANDIDATE`.

Required:

- stale/recompose-required candidates must be flagged or filtered in API/UI;
- they must not look like current selectable recommendations;
- selection revalidation remains the final guard.

## Blocker 6 — historical duplicate migration is still not closed

The submitted V19.2.2 changed-file list does not include `backend/app/db/session.py` or the table uniqueness declaration.

The existing startup code still contains:

```
try:
    CREATE UNIQUE INDEX ... (journey_id, confirmation_ref)
except Exception:
    pass
```

This is exactly the silent failure that the previous gate required to remove.

The new `quarantine_duplicate_confirmation_identities()` changes duplicate row status but does not change `(journey_id, confirmation_ref)`. A non-partial unique index over those two columns still cannot be created while duplicate rows remain.

Required:

- no silent `except Exception: pass` for the uniqueness migration;
- migration from a database that already contains duplicate confirmation refs must be tested;
- preserve original evidence/audit while making the authoritative uniqueness rule actually enforceable;
- after migration, concurrent confirmations must be serialized by a real DB constraint/index, not only by application pre-checks.

## Blocker 7 — release patch is not fully portable against the packaged V19.2.1 baseline

Independent `git apply --check` of `patches/V19_2_2_CODE.patch` against the submitted V19.2.1 package fails at:

`contracts/openapi.yaml`

All other hunks pass when that path is excluded.

The V19.2.1 `openapi.yaml` contains mixed CRLF/LF line endings; the EAC patch was emitted against normalized LF content.

Required:

- normalize line endings deliberately;
- regenerate the release patch from the exact declared baseline;
- `git apply --check` must pass from a clean V19.2.1 baseline without path exclusions;
- source copies may remain as review evidence, but the claimed portable patch must actually be portable.

## Non-blocking debt

Two broad-suite failures are genuinely contradictory tests on the same fixtures. Do not "fix" production truth to satisfy the unsafe expectations. Instead, mark/deprecate the obsolete expectations with an explicit rationale in a future test-maintenance pass.

No live DeepSeek canary and no physical-device test were performed in V19.2.2. These remain pre-physical-trial gates.
