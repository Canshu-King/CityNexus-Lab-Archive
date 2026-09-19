# CODE_GATE_REPORT.md — CityNexus V19.2.3 Final Shadow-Trial Code Gate

## Verdict

**SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE**

All seven blockers raised by the independent review of Snapshot E are closed
with executable evidence, the V19.2 contract is unchanged at 61/61, the new
closure suite is 13/13, the broad regression has **zero new failures**, and one
live DeepSeek canary passed. The only remaining gate is physical-device trial,
which cannot be performed here.

## Scope discipline

* Snapshot E (the V19.2.2 package) was frozen first, with a SHA-256 manifest.
* V19.3 was **not** started.
* No broad product features were added. The only new endpoint is the governed
  recovery acknowledgement the review explicitly required.
* HARD constraints and C4 protection were not weakened.
* No release artifacts were written into source directories.

## Blocker closure

### Blocker 1 — C4 temporal semantics (P0-1)

**Defect (reproduced before fixing).** `schedule_template_with_anchors()`
interleaved the anchor without enforcing ARRIVAL as a lower boundary or
DEPARTURE as an upper boundary. Direct execution against Snapshot E produced:

```
ARRIVAL 12:30   ->  09:00 POI, 10:30 POI, then ARRIVAL 12:30
DEPARTURE 15:30 ->  DEPARTURE 15:10, then 15:50 POI, 17:10 POI
```

A traveller cannot visit a city before arriving, nor continue after departing.

**Fix.** The scheduler now models anchors as boundaries:

* `validate_anchor_timeline()` rejects overlapping anchors, anchors outside the
  window, and an empty usable interval, returning a precise reason
  (`C4_ANCHOR_OVERLAP`, `C4_ANCHOR_OUTSIDE_JOURNEY`,
  `C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE`).
* `usable_city_interval()` gives flexible activity an interval bounded below by
  the completed ARRIVAL and above by the start of DEPARTURE; MID_TRIP stays an
  interior pinned commitment.
* Flexible POIs are packed into the gaps with real frozen travel time and are
  **dropped** when they do not fit, instead of being allowed to escape the
  interval.
* `_anchor_block_reason()` surfaces the precise conflict instead of a generic
  "blocked" list.

**Verified (T01–T05).** With ARRIVAL 12:30 no flexible activity starts before
the anchor completes; with DEPARTURE 15:30 none ends after the anchor begins;
ARRIVAL 10:00 + MID_TRIP 13:00 + DEPARTURE 17:00 is monotonic and fully inside
the usable interval; ARRIVAL after DEPARTURE returns 422 with
`C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE` and persists no plan.

### Blocker 2 — HARD recovery could be dismissed client-side (P0-2)

**Defect.** The `Continue without changes` button only called
`setDismissed(true)`, which could hide a HARD safety warning with no backend
record and no change in truth state.

**Fix.** The button is replaced by **`Acknowledge warning`**, which calls a new
governed endpoint `POST /journeys/{id}/recovery/acknowledge`. Acknowledgement:

* persists `acknowledged_at` and moves the Event to `ACKNOWLEDGED`;
* **does not** resolve the recovery, mark the plan safe, or hide the banner;
* keeps `needs_review` and `recovery_required` true until a revalidated
  feasible plan is actually selected.

The panel is never hidden by local state; it disappears only when the backend
reports the journey truth is healthy again. The same governed component is used
for the stale-evidence warning.

### Blocker 3 — recovery lifecycle did not resolve (P0-3)

**Defect.** `resolve_recovery_events()` ran only from capability confirmation,
never after selecting a feasible replacement, and `recovery_state()` could
project `RESOLVED` while the Event stayed `DETECTED`.

**Fix.** `select_plan` now resolves open recovery Events in the same
transaction as the selection (the plan has just passed the same gate used by
generate/start), `/experience` resolves on `is_feasible is True`, and the
projected state is derived from persisted facts. Verified: after selecting a
feasible replacement the Event is resolved, `recovery` is `null`,
`needs_review` is false, and a reload does not resurrect it. Re-selecting the
infeasible plan is refused (422) and does **not** fake resolution.

### Blocker 4 — NO_ALTERNATIVE was inferred, not real (P0-4)

**Defect.** `recovery_state()` chose `RECOVERY_REQUIRED_NO_ALTERNATIVE` from
`is_feasible is None`, which is not a fact.

**Fix.** `record_replan_outcome()` persists the outcome of an actual replan
attempt (`replan_attempted`, `feasible_candidate_ids`, `no_alternative`). The
plan-generation endpoint records both outcomes: a 422 records zero feasible
candidates, a 201 records the validated candidate ids. Verified: an unmet HARD
need yields `RECOVERY_REQUIRED_NO_ALTERNATIVE` with
`replan_attempted = true` and `no_alternative = true`, surviving a reload.

### Blocker 5 — stale candidates looked ordinary (P1-1)

**Fix.** `PlanVersion` now projects `stale`, `selectable` and `stale_reason`,
computed from the frozen evidence (missing snapshot, expired, or unreadable).
An expired candidate is flagged `stale=true` / `selectable=false`. Selection
revalidation remains the final guard; `/start` still returns 409.

### Blocker 6 — duplicate migration was not closed (P1-2)

**Defect.** Startup contained `CREATE UNIQUE INDEX ... except Exception: pass`,
and a non-partial unique index over `(journey_id, confirmation_ref)` cannot be
created while duplicate rows exist. Quarantine changed `status` but left the
duplicated pair intact.

**Fix.** A real migration with no silent failure:

* before the schema script runs, `_quarantine_existing_duplicates()` moves
  duplicate losers to `QUARANTINED_DUPLICATE_IDENTITY` and releases their draft
  pointer, preserving evidence and audit;
* after the schema script, `_migrate_reservation_identity()` creates a
  **partial** unique index
  (`WHERE confirmation_ref IS NOT NULL AND status <> 'QUARANTINED_DUPLICATE_IDENTITY'`)
  and records a durable repair Event;
* any genuine failure now raises instead of being swallowed.

Verified end to end on a database that already contained three duplicate
confirmation refs: the earliest stays authoritative, the others are
quarantined, the repair Event is written, the index exists, and a duplicate
insert is rejected by the database. Concurrent confirmations still converge on
one reservation and one C4 with no 500.

### Blocker 7 — patch not portable (P1-3)

**Defect.** The V19.2.1 baseline `contracts/openapi.yaml` has **mixed** line
endings (792 CRLF + 1551 LF), so a patch emitted from normalised content could
not apply.

**Fix.** The declared baseline is now explicitly normalised to LF, the patch is
generated from that exact baseline, and `git apply --check` passes with **no
excluded paths**. Applying the patch reproduces all 21 changed files
byte-for-byte.

## Live semantic canary (P1-4)

`DEEPSEEK_API_KEY` was present in the user environment, so one bounded live
canary was run through the real primary semantic compiler. Live output matched
the local fallback exactly on all three inputs, including the negated sentence
(`NEGATED`, no capability) and `走路不能超过 1.5 公里` -> `max_m = 1500`.
The key was never printed and is absent from the package.

## Regression accounting

| | Snapshot E (V19.2.2) | V19.2.3 |
| --- | --- | --- |
| V19.2 contract | 61 passed | **61 passed** |
| New closure suite | — | **13 passed** |
| Broad backend failures | 2 | **2** (same contradictory pairs) |
| New regressions | — | **0** |

## Explicit non-claims

* No real payment was executed.
* No physical-device testing was performed; all mobile evidence is emulated
  viewports in headless Chrome.
* The live canary is one bounded semantic call, not a full live-provider trial.
