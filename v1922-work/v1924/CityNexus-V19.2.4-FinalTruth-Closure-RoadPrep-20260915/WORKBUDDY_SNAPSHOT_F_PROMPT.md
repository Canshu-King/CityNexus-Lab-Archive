Continue as CityNexus read-only red-team.

You now have the final submitted Snapshot F:

CityNexus-EAC-V19.2.3-FinalShadowTrial-CodeGate-20260915.zip

The previous WorkBuddy package's binding verdict was against Snapshot E
(V19.2.2). Its in-flight V19.2.3 addendum was observational only.

Do NOT reuse the Snapshot-E verdict as a Snapshot-F verdict.

Perform a narrow Snapshot-F truth delta.

==================================================
1. SHARED C4 FEASIBILITY
==================================================

Run the shared deterministic gate directly, not only plan generation.

Cases:

ARRIVAL 12:30
+ flexible 09:00-10:15
-> MUST FAIL

DEPARTURE 15:30
+ flexible 17:00-18:30
-> MUST FAIL

ARRIVAL 17:00
+ DEPARTURE 10:00
-> MUST FAIL with a precise C4 ordering conflict

valid ARRIVAL 12:30
+ anchor 12:30-12:50
+ flexible 13:20-14:20
-> MUST PASS

Independent replay currently shows the first three incorrectly PASS in
Snapshot F. Verify independently.

==================================================
2. RECOVERY DURABLE TRUTH
==================================================

With an open DETECTED recovery Event:

recovery_state(... is_feasible=True)

must NOT report RESOLVED unless the Event was transactionally resolved.

Check:

Event.status
experience.recovery
experience_flags

must agree.

Also inspect whether GET /experience performs a state mutation that is not
committed. A read endpoint must not create a fake durable resolution.

Candidate ids exposed as alternatives must come from an actual validated replan
outcome, not arbitrary CANDIDATE rows.

==================================================
3. RESERVATION QUARANTINE HELPER
==================================================

The startup migration is expected to PASS.

Separately exercise:

quarantine_duplicate_confirmation_identities()

against a DB with duplicate active confirmation refs.

It must:

- not violate Event.event_type CHECK;
- quarantine losers;
- preserve evidence;
- write a valid audit Event;
- be idempotent on a second run.

Independent replay currently finds Snapshot F's helper raises IntegrityError
because event_type='RESERVATION_IDENTITY_DUPLICATE' is not in the schema
vocabulary.

==================================================
4. CONFIRM ALREADY-GREEN AREAS
==================================================

Do only targeted checks that:

- governed Acknowledge warning remains wired;
- scheduler ARRIVAL/DEPARTURE boundaries remain good;
- startup partial unique-index migration remains good;
- patch portability claim is truthful;
- stale start remains blocked.

Do not rerun the historical giant corpus.

==================================================
5. IF EAC V19.2.4 LANDS DURING THIS RUN
==================================================

Freeze Snapshot G and do one targeted delta on the above three findings.
Do not restart from Snapshot E.

Final verdict for Snapshot F/G:

BLOCKED

or

SNAPSHOT_G_ACCEPTED_FOR_PHYSICAL_TRIAL_PRECHECK

Do not modify the authoritative main tree.
