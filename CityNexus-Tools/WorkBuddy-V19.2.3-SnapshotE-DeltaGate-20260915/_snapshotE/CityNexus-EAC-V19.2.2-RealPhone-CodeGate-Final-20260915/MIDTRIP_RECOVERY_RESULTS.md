# MIDTRIP_RECOVERY_RESULTS.md — Durable mid-trip HARD recovery

## Requirement

A HARD capability discovered mid-trip must produce durable, governed recovery:
an Event / ReplanProposal-based state, C4 preserved, a governed ReplanProposal
or an explicit no-alternative state, a visible frontend recovery action, never
a `REPLAN_REQUIRED` value that exists only inside one response JSON, and never
a silent mutation of the active plan.

## Implementation — `app/planning/hard_recovery.py` (new)

* `open_recovery_event(...)` writes a durable `Event` for the Journey and
  refreshes it rather than duplicating on repeat confirmation.
* `active_recovery_event(...)`, `resolve_recovery_events(...)`,
  `recovery_state(...)`, `recovery_flags(...)`.

The event carries the capability code, the active plan version, the feasibility
failures, `requires_user_decision: true` and `silent_plan_mutation: false`.

### Vocabulary note

`Event.event_type` and `Event.provenance` are closed vocabularies enforced by
`backend/db/schema.sql`. Recovery therefore uses the sanctioned
`event_type = "USER_CHANGE"` with `provider_key = "citynexus-capability-recovery"`
as the discriminator, and `provenance = "USER_REPORTED"`. The specific recovery
kind (`CAPABILITY_HARD_RECOVERY`) is carried in the payload. Inventing a new
`event_type` would have required a schema change and was deliberately avoided.

### Wiring — `app/main.py`

* `POST /journeys/{id}/capabilities/confirm`: re-evaluates the active plan. If
  it is no longer feasible, a durable recovery event is opened, an audit record
  is written, and `recovery` is returned. If it is feasible again, open recovery
  events are resolved.
* `GET /journeys/{id}/experience`: exposes `recovery` and `experience_flags`
  for `PLANNED` and `ACTIVE` journeys, so a stale or invalidated plan can never
  look healthy to the phone.

### Frontend — `frontend/src/features/recovery/RecoveryRequiredPanel.tsx` (new)

Rendered before the plan on the authoritative route, with
`data-testid="recovery-required-panel"`, a title, the failure list, a
"Generate new options" action (`recovery-replan`) and a
"Continue without changes" action (`recovery-acknowledge`).

## Verified behaviour

| Check | Result |
| --- | --- |
| HARD capability confirm on ACTIVE journey | 200 |
| Active plan silently rewritten | **no** (plan version unchanged) |
| Durable recovery state | `RECOVERY_REQUIRED` |
| Recovery visible in `/experience` | `recovery.state = RECOVERY_REQUIRED`, `needs_review = true` |
| C4 commitments preserved | yes |
| Phone panel rendered (390x844) | visible, both actions present |
| Phone panel rendered (430x932) | visible, both actions present |
| Page errors | 0 |

The Journey remains `ACTIVE` with its original plan; the traveller is given an
explicit governed choice instead of a silent rewrite.

## Evidence

* `evidence/mobile_probe_d.json` — `MIDTRIP_HARD_RECOVERY` for both viewports:
  `confirm_recovery = RECOVERY_REQUIRED`, `ui_panel_visible = true`,
  `ui_replan_action = true`, `ui_acknowledge_action = true`.
* `tests/test_v192_shadow_trial_gate.py::test_v192_defect_midtrip_hard_need_produces_a_review`
  passes (61/61 total).

## Not claimed

The recovery UI was exercised on emulated mobile viewports only. No physical
device was used.
