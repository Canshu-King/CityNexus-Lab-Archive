# RECOVERY_TRUTH_RESULTS.md — Recovery projection follows durable facts

## R01 — an open Event never projects RESOLVED

**Defect in Snapshot F.** With an open `DETECTED` Event,
`recovery_state(..., is_feasible=True)` returned `state = RESOLVED` while
`recovery_flags(...).recovery_required` was still `true`. The primitive could
claim "resolved" while durable truth said "open".

**Fix.** `recovery_state()` no longer lets a caller boolean resolve durable
recovery. An open Event projects:

* `RECOVERY_REQUIRED_NO_ALTERNATIVE` when a recorded replan attempt produced
  zero feasible candidates;
* `RECOVERY_REQUIRED` otherwise.

Only a transactional workflow that revalidates and explicitly resolves the
Event may close it.

Verified (`test_v1924_open_event_never_projects_resolved`):

```
Event.status      = DETECTED
recovery_state    = RECOVERY_REQUIRED     (is_feasible=True passed in)
recovery_required = true
projection agrees = true
```

## R02 — Event state, recovery projection and flags agree

`/experience` now derives `experience_flags` from the same projected recovery
object:

* `open_recovery = recovery is not None and recovery["state"] != "RESOLVED"`
* `needs_review = open_recovery or staleness`
* `recovery_required = open_recovery`
* `recovery_state = recovery["state"]`

So the Event, `/experience.recovery` and `experience_flags` can no longer
disagree.

## R03 — GET is a projection, not a durable transition

**Defect in Snapshot F.** `GET /experience` called `resolve_recovery_events()`
on a read path without committing the session — an uncommitted, best-effort
state transition driven by a GET.

**Fix.** The call was removed. `resolve_recovery_events()` is now invoked only
from genuinely transactional workflows that already change authoritative truth:
plan selection and capability confirmation. Both commit.

Verified (`test_v1924_experience_get_does_not_resolve_recovery`): three
consecutive `GET /experience` calls return `recovery.state != RESOLVED`,
`recovery_required = true`, and the Event is still `DETECTED` afterwards.

## R04 — only replan-validated candidates are advertised

**Defect in Snapshot F.** Any arbitrary `PlanVersion(status="CANDIDATE")` row
was advertised as a recovery alternative, which is not proof of feasibility.

**Fix.** Only ids recorded by an actual feasibility-checked replan attempt
(`record_replan_outcome`) are exposed.

Verified:

| Situation | `replan_attempted` | candidate rows in DB | `candidate_plan_count` |
| --- | --- | --- | --- |
| no replan attempted | false | 2 | **0** |
| replan attempted, none feasible | true | 0 | **0** |

and when a replan does produce validated candidates, `record_replan_outcome`
persists their ids and they are advertised.

## Preserved behaviour

* Acknowledging a warning is still strictly non-resolving
  (`resolved = false`, banner stays, `needs_review` stays true).
* Selecting a genuinely feasible replacement still resolves recovery
  transactionally, and a reload does not resurrect it
  (`test_v1924_feasible_replacement_still_resolves_recovery`).
* `NO_ALTERNATIVE` still requires a recorded replan attempt.

## Evidence

* `evidence/mobile_v1924_d.json` — both viewports: `MIDTRIP_HARD_RECOVERY`,
  `ACKNOWLEDGE_WARNING` (`resolved=false`, `banner_still_visible=true`),
  `NO_ALTERNATIVE` (`state=RECOVERY_REQUIRED_NO_ALTERNATIVE`,
  `replan_attempted=true`), `FEASIBLE_REPLACEMENT_RESOLVES`
  (`recovery_after=null`).
* `evidence/gate_suites_run.txt` — 86 passed.
