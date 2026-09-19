# CityNexus Snapshot K Real-User Final Closure Road-Prep

Freeze the submitted package:

`CityNexus-EAC-SnapshotJ-FinalTrial-Closure-20260916.zip`

as **Snapshot K candidate** for independent review.

SHA-256:

`ceff17993b765d53fe6cd1de7c571588ab43a04140c48c2a3b14173278cf6472`

The submitted package is correctly self-labelled:

`BLOCKED_FOR_REAL_USER_TRIAL`

It fixes meaningful backend defects, but independent source replay found two
additional stay-scheduling P0s and one incomplete disruption-target policy.

This Road-Prep is deliberately narrow:

1. close the remaining stay timeline truth defects;
2. close disruption target truth;
3. prove recovery on the actual stay-enriched Xiamen plan;
4. then STOP backend work and complete the consumer UI that has now been skipped
   for several consecutive rounds.

Read:

- `docs/INDEPENDENT_AUDIT.md`
- `docs/STAY_TIMELINE_TRUTH.md`
- `docs/REAL_USER_PRODUCT_GATE.md`
- `docs/EAC_FINAL_TASK.md`
- `docs/WORKBUDDY_TARGETED_DELTA.md`

Run:

- `probes/snapshot_k_stay_timeline_probe.py`

against the authoritative backend before and after the fix.
