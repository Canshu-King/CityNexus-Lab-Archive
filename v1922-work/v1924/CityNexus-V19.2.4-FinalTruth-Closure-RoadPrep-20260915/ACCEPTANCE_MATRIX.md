# V19.2.4 acceptance matrix

All rows must pass.

| ID | Gate | Required result |
|---|---|---|
| F01 | Pre-arrival persisted plan | shared feasibility gate rejects flexible activity before ARRIVAL completion |
| F02 | Post-departure persisted plan | shared feasibility gate rejects flexible activity after DEPARTURE begins |
| F03 | ARRIVAL after DEPARTURE | shared feasibility gate rejects with precise C4 ordering conflict |
| F04 | Valid ARRIVAL control | clean plan still passes |
| F05 | Scheduler regression | V19.2.3 scheduler boundary tests remain green |
| R01 | Recovery projection | open Event can never project RESOLVED |
| R02 | Recovery flags | Event state / recovery / flags agree |
| R03 | Read-only experience | GET projection does not perform an uncommitted durable resolution |
| R04 | Candidate truth | only replan-validated candidate ids are exposed as recovery alternatives |
| D01 | Startup migration | legacy duplicate migration remains green |
| D02 | ORM quarantine helper | uses valid event type and does not crash |
| D03 | Quarantine idempotency | quarantined losers are excluded from future duplicate detection |
| G01 | V19.2 contract | 61/61 or better, no regression |
| G02 | V19.2.3 closure suite | 13/13 or updated equivalent |
| G03 | New V19.2.4 tests | all pass |
| G04 | Broad backend | zero new regressions |
| G05 | Frontend build | pass |
| G06 | OpenAPI | parity remains green |
| G07 | Mobile | no regression in recovery/stale/C4 targeted flows |
| P01 | Patch/release truth | final patch applies to declared baseline; clean package |
| A01 | Physical device | NOT part of this code gate; must remain pending |

Final code verdict may only be:

- `BLOCKED`
- `SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE`
