# RECOVERY_GOVERNANCE_RESULTS.md — HARD recovery governance (P0-2/3/4, R01–R04)

## R01 — acknowledgement cannot hide unsafe truth

**Before.** `RecoveryRequiredPanel` exposed `Continue without changes`, whose
handler was `setDismissed(true)`. A HARD safety warning could be hidden with no
backend record and no change in the journey truth state.

**After.** The action is **`Acknowledge warning`** and calls
`POST /api/v1/journeys/{id}/recovery/acknowledge`:

| Property | Result |
| --- | --- |
| Persisted | `acknowledged_at` recorded, Event -> `ACKNOWLEDGED` |
| Resolves recovery | **no** (`resolved = false`) |
| Marks plan safe | **no** |
| Hides the banner | **no** — the panel stays while `needs_review` is true |
| Clears stale evidence | **no** |

Verified on both viewports: `backend_status = 200`,
`backend_acknowledged = true`, `backend_resolved = false`,
`banner_still_visible = true`, `needs_review_after = true`,
`recovery_required_after = true`.

The panel is never hidden by local component state. It disappears only when the
backend reports the journey truth healthy again.

## R02 — a feasible replacement resolves the durable Event

**Before.** `resolve_recovery_events()` ran only from capability confirmation.
Selecting a feasible replacement left the Event `DETECTED`, and the projection
could report `RESOLVED` while the Event had not changed.

**After.** `select_plan` resolves open recovery Events in the same transaction
as the selection, and `/experience` resolves when the plan is feasible.

| Check | Result |
| --- | --- |
| Generate replacement | 201 |
| Select replacement | 200 |
| `recovery` after selection | `null` |
| `recovery_required` | false |
| `needs_review` | false |
| Panel after reload | not rendered |
| Re-selecting the infeasible plan | 422, recovery **not** resolved |

## R03 — real NO_ALTERNATIVE state

**Before.** `RECOVERY_REQUIRED_NO_ALTERNATIVE` was chosen from
`is_feasible is None`, which is an absence of information, not a fact.

**After.** `record_replan_outcome()` persists the result of an actual replan
attempt. The generation endpoint records a 422 as zero feasible candidates and
a 201 as the validated candidate ids.

Verified: with an unmet HARD need the replan returns 422 and the durable state
becomes `RECOVERY_REQUIRED_NO_ALTERNATIVE` with `replan_attempted = true` and
`no_alternative = true`, surviving a reload. The UI states that no feasible
replacement is available and the current plan stays unverified.

## R04 — C4 preserved through recovery

Verified: after a reservation creates an ACTIVE `C4_Anchored` commitment, a
mid-trip HARD capability confirmation leaves the commitment count and
`ACTIVE` status unchanged. Recovery never drops or weakens a C4 commitment.

## Evidence

* `evidence/mobile_v1923_d.json` — `MIDTRIP_HARD_RECOVERY`,
  `ACKNOWLEDGE_WARNING`, `NO_ALTERNATIVE`, `FEASIBLE_REPLACEMENT_RESOLVES` for
  both viewports.
* `tests/test_v1923_final_code_gate.py` — R01/R02/R03/R04 regression tests.
* `evidence/v1923_gate_run.txt` — 74 passed.

## Event vocabulary note

`Event.event_type` and `Event.provenance` are closed vocabularies in
`backend/db/schema.sql`. Recovery uses the sanctioned `event_type = "USER_CHANGE"`
with `provider_key = "citynexus-capability-recovery"` as the discriminator and
`provenance = "USER_REPORTED"`. The recovery kind is carried in the payload.
No schema vocabulary was invented.
