# V19.2.3 acceptance matrix

All P0/P1 rows below must pass before the code verdict can become `SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE`.

| ID | Gate | Required result |
|---|---|---|
| T01 | ARRIVAL temporal boundary | no flexible activity starts before ARRIVAL boundary |
| T02 | DEPARTURE temporal boundary | no flexible activity ends after DEPARTURE boundary |
| T03 | MID_TRIP pinned anchor | anchor remains at committed time and surrounding POIs are feasible |
| T04 | multiple C4 anchors | chronological, routable, no impossible overlap |
| T05 | impossible anchor combination | precise conflict, never a fabricated plan |
| R01 | HARD recovery acknowledgement | cannot hide/clear unsafe truth client-only |
| R02 | feasible replacement selected | durable recovery Event resolves; flags/UI agree |
| R03 | no alternative | durable explicit NO_ALTERNATIVE after attempted replan |
| R04 | C4 preservation during recovery | all active C4 commitments remain protected |
| S01 | stale candidate list | stale candidate is flagged/filtered, not ordinary current candidate |
| S02 | stale start | `/start` stays blocked with 409 |
| D01 | legacy duplicate DB migration | duplicates detected and migrated without silent index failure |
| D02 | post-migration uniqueness | DB uniqueness actually exists/enforces rule |
| D03 | concurrent confirm | one logical reservation/C4; loser deterministic; no 500 |
| P01 | clean patch apply | `git apply --check V19_2_3_CODE.patch` succeeds on exact clean baseline |
| P02 | release hygiene | no cache/db/log/error junk; changed-files list truthful |
| G01 | V19.2 contract suite | all non-obsolete gate tests pass |
| G02 | broad backend | zero new regressions |
| G03 | frontend build | pass |
| G04 | OpenAPI | runtime/contract parity; changed response schemas aligned |
| G05 | mobile delta | 390x844 + 430x932 recovery/stale/C4 flows pass |
| A01 | DeepSeek canary | one live canary if configured; otherwise explicit pre-trial blocker |
