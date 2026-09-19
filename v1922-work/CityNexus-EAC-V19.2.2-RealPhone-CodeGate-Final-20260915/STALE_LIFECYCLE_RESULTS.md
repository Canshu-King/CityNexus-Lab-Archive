# STALE_LIFECYCLE_RESULTS.md — Stale evidence blocks start

## Requirement

Expired or inconsistent frozen evidence must block `/start`
(`STALE_RECOMPOSE_REQUIRED` or equivalent), must not transition the Journey to
`ACTIVE`, and must be exposed to the phone UI.

## The defect

`POST /journeys/{id}/start` transitioned the Journey to `ACTIVE` without
revalidating the selected plan. A plan whose frozen mobility evidence had
expired could therefore be started silently, and select/booking/start disagreed
about the same plan.

## The fix — `app/main.py`

`start_journey` now runs `validate_selected_plan_feasibility` before any state
transition, the same truth policy select and booking already used:

* a `ValueError` (stale / inconsistent frozen evidence) -> HTTP 409 with
  `STALE_RECOMPOSE_REQUIRED: ...`;
* an infeasible gate result -> HTTP 409 with `START_BLOCKED_INFEASIBLE: ...`.

The Journey stays `PLANNED`; the selected plan is not activated.

`GET /journeys/{id}/experience` now revalidates for `PLANNED` **and** `ACTIVE`
journeys and exposes:

```json
"experience_flags": {
  "needs_review": true,
  "recovery_required": false,
  "staleness": true,
  "feasibility_failures": ["STALE_RECOMPOSE_REQUIRED: PlanVersion frozen mobility evidence expired"]
}
```

Staleness is computed independently of whether a recovery event exists, so a
merely-expired plan is visible too.

The phone renders the same panel with the title
"Trip evidence needs re-syncing".

## Verified behaviour

| Check | Result |
| --- | --- |
| `/start` on expired evidence | 409 |
| Message | `STALE_RECOMPOSE_REQUIRED: PlanVersion frozen mobility evidence expired` |
| Journey status after refusal | `PLANNED` |
| `experience_flags.staleness` | `true` |
| UI warning panel (390x844) | visible, "Trip evidence needs re-syncing" |
| UI warning panel (430x932) | visible, "Trip evidence needs re-syncing" |
| Page errors | 0 |

## Evidence

* `evidence/stale_candidates_d.json` — independent WorkBuddy probe:
  `stale_candidate_refused`, `all_shapes_refused`,
  `stale_selected_plan_revalidation_raises` all true;
  `journey_still_running_on_expired_evidence` **false**.
* `evidence/mobile_probe_d.json` — `STALE_EVIDENCE_WARNING` for both viewports.
* `tests/test_v192_shadow_trial_gate.py::test_v192_defect_start_refuses_expired_evidence`
  passes.

## Not claimed

The stale UI was exercised on emulated mobile viewports only. No physical
device was used.
