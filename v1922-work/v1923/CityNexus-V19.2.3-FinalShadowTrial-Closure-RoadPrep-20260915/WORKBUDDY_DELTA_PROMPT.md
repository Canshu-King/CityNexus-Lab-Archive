Continue as CityNexus read-only red-team.

Freeze:

`CityNexus-EAC-V19.2.2-RealPhone-CodeGate-Final-20260915.zip`

as Snapshot E.

Do not modify the authoritative main tree.
Do not rerun the old giant corpus.

Build a narrow Snapshot-E delta gate around the independent findings below.

1. C4 temporal ordering

Prove or falsify:

- ARRIVAL 12:30 never permits a flexible activity before 12:30 / anchor completion.
- DEPARTURE 15:30 never permits a flexible activity after the departure boundary.
- ARRIVAL + MID_TRIP + DEPARTURE ordering is feasible and monotonic.
- ARRIVAL after DEPARTURE yields a precise conflict.

Do not accept `plans > 0` as sufficient evidence.
Inspect actual activity timestamps.

2. HARD recovery governance

Current Snapshot E UI contains `Continue without changes` whose handler is only
client-side dismissal.

Verify that this can hide the warning without changing backend recovery state.
Treat that as a failure for HARD/stale truth.

3. Recovery resolution lifecycle

Test:

ACTIVE journey
-> HARD invalidates plan
-> recovery Event DETECTED
-> generate feasible alternatives
-> select feasible replacement
-> refresh `/experience`

Required:

- recovery Event becomes RESOLVED;
- recovery_required = false;
- needs_review = false unless another issue exists;
- panel does not reappear on reload.

4. No-alternative

Force a HARD+C4 combination with zero feasible replacements.
Confirm the backend persists an explicit no-alternative state based on an actual
replan attempt, not on `is_feasible is None`.

5. stale candidate listing

Expired candidate must not remain visually/API-equivalent to a current selectable
candidate.

6. legacy duplicate DB migration

Create a pre-existing DB state with duplicate `(journey_id, confirmation_ref)`.
Run schema/startup migration.
Verify:

- no silent `except: pass` success;
- uniqueness becomes enforceable;
- historical evidence is preserved;
- new concurrent confirmations cannot create duplicates.

7. patch portability

Run `git apply --check` for the final V19.2.3 patch against the exact declared
clean baseline, including `contracts/openapi.yaml`.

If EAC V19.2.3 finishes while this task is running, perform one targeted delta
against it; do not restart the whole historical suite.

Final verdict:

BLOCKED

or

SNAPSHOT_E_ACCEPTED_FOR_FINAL_CODE_GATE

If validating V19.2.3 directly, use:

BLOCKED

or

SNAPSHOT_F_ACCEPTED_FOR_PHYSICAL_TRIAL_PRECHECK
