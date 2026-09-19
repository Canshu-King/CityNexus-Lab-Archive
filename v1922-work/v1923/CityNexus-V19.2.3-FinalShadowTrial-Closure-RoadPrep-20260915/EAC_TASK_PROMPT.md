You are continuing CityNexus as the constrained gate-closure engineer.

Authoritative repository:

D:\moodle\CityNexus

Freeze the current EAC V19.2.2 result as Snapshot E.

Do NOT start V19.3.
Do NOT add broad product features.
Do NOT weaken HARD constraints or C4 protection.

Read `VERIFIED_FINDINGS.md` and `ACCEPTANCE_MATRIX.md` from this Road-Prep.

Mission: produce V19.2.3 as the final code-gate repair before physical-phone trial.

==================================================
P0-1 — CORRECT C4 TEMPORAL BOUNDARIES
==================================================

The existing V19.2.2 tests only prove that a plan exists.
They do not prove that the plan is possible relative to ARRIVAL/DEPARTURE.

Independent direct execution of your submitted `schedule_template_with_anchors()` proved:

ARRIVAL 12:30 still permits a 09:00 POI before arrival.
DEPARTURE 15:30 still permits a 17:00 POI after departure.

Fix the temporal model.

Required invariant:

- confirmed ARRIVAL is a lower boundary for city activities;
- confirmed DEPARTURE is an upper boundary for city activities;
- MID_TRIP is an interior exact/pinned commitment;
- multiple anchors must be chronologically consistent;
- travel time to/from anchors must still be respected;
- optional POIs outside the usable interval are removed/re-timed;
- impossible anchor sets return a precise conflict.

Do not solve this by merely widening the journey window.
Review both:

- `app/planning/anchor_schedule.py`
- `app/replanning/feasibility.py`

Add tests that assert actual ordered activity timestamps, not only non-empty plan count.

Minimum regression cases:

1. journey 09:00-19:00, ARRIVAL 12:30
   -> no flexible POI before arrival.

2. journey 09:00-19:00, DEPARTURE 15:30
   -> no flexible POI after departure.

3. ARRIVAL 10:00 + MID_TRIP 13:00 + DEPARTURE 17:00
   -> all activities lie in the usable interval and anchor ordering is preserved.

4. ARRIVAL after DEPARTURE
   -> deterministic conflict; no plan.

==================================================
P0-2 — GOVERN HARD RECOVERY, DO NOT CLIENT-DISMISS IT
==================================================

The current `RecoveryRequiredPanel` button:

`Continue without changes`

only executes `setDismissed(true)`.

That is not acceptable for a confirmed HARD need or stale safety evidence.

Replace it with governed semantics.

Acknowledge may record that the traveller saw the warning, but it must NOT:

- mark an infeasible plan safe;
- resolve the recovery;
- hide the journey truth permanently;
- allow stale evidence to look current.

If acknowledgement is supported, persist it on the backend and keep an explicit
unverified/infeasible banner/state until recovery is actually resolved.

Use wording such as `Acknowledge warning` rather than `Continue without changes`.

==================================================
P0-3 — CLOSE THE DURABLE RECOVERY LIFECYCLE
==================================================

Current defect:

- recovery Event is opened when HARD capability invalidates ACTIVE plan;
- selecting a feasible replacement does not resolve the Event;
- `recovery_state()` can project RESOLVED while the underlying Event remains DETECTED;
- experience flags can disagree with the projected recovery state.

Required:

- selecting/activating a feasible replacement transactionally resolves the open recovery Event;
- Event.status, `/experience.recovery`, `experience_flags` and frontend display must agree;
- page refresh must not resurrect a resolved recovery;
- removing/relaxing the capability may resolve only after feasibility is revalidated.

==================================================
P0-4 — REAL NO-ALTERNATIVE STATE
==================================================

Do not derive NO_ALTERNATIVE from `is_feasible is None`.

Persist the result of an actual recovery/replan attempt.

If zero feasible alternatives exist after current HARD constraints + active C4 + frozen/live evidence:

-> durable `RECOVERY_REQUIRED_NO_ALTERNATIVE` (or equivalent)
-> reason/failures recorded
-> UI clearly states no feasible replacement is available
-> current plan remains explicitly infeasible/unverified

If feasible alternatives exist:

-> expose only validated candidates
-> selecting one can resolve recovery.

==================================================
P1-1 — STALE CANDIDATE LIFECYCLE
==================================================

V19.2.2 correctly refuses stale select/start, but stale rows remain ordinary `CANDIDATE` entries.

Add an explicit stale/recompose-required projection or filter.

The UI must not present an expired candidate as a normal current recommendation.
Selection revalidation remains the final guard.

==================================================
P1-2 — REAL LEGACY DUPLICATE MIGRATION
==================================================

Do not leave this startup logic:

try:
    CREATE UNIQUE INDEX ...
except Exception:
    pass

The current quarantine helper changes status but leaves duplicate
`(journey_id, confirmation_ref)` values intact, so a non-partial unique index can
still fail to be created.

Implement and test a real migration strategy for a DB that already contains duplicates.

Requirements:

- preserve original evidence/audit;
- duplicate losers become non-authoritative without data loss;
- the authoritative uniqueness mechanism is actually created and verified;
- no silent exception swallowing;
- concurrent new confirmations rely on a real DB serialization point;
- loser returns existing artifact or deterministic 409/422; never 500.

Choose the cleanest schema/index strategy compatible with current SQLite and the
project's intended DB portability. Do not fake success in application memory.

==================================================
P1-3 — PATCH PORTABILITY / RELEASE TRUTH
==================================================

The V19.2.2 review package claims `V19_2_2_CODE.patch` applies cleanly, but
independent `git apply --check` against the packaged V19.2.1 baseline fails at
`contracts/openapi.yaml` because the baseline has mixed CRLF/LF and the patch was
emitted from normalized LF content.

For V19.2.3:

- normalize line endings deliberately;
- generate the patch from the exact declared baseline;
- `git apply --check` from clean baseline must pass with no excluded paths;
- verify the full patch, not only source-file copies.

==================================================
P1-4 — LIVE SEMANTIC CANARY
==================================================

If the existing DeepSeek credential is available in the user's environment,
run one bounded live semantic canary through the real primary semantic compiler.

Use harmless inputs such as:

- `I don't need a wheelchair, I can walk.`
- `I need step-free access for this trip.`
- `走路不能超过 1.5 公里。`

Do not print or package the API key.

If credentials are unavailable, report:

`LIVE_DEEPSEEK_CANARY_PENDING_PHYSICAL_TRIAL`

and do not falsely claim it passed.

==================================================
FINAL TESTS
==================================================

Run:

1. all V19.2 gate tests plus new temporal/recovery/migration tests;
2. relevant V19/V19.1 capability guards;
3. authoritative backend regression root only;
4. OpenAPI parity + response-schema checks;
5. frontend build;
6. focused 390x844 and 430x932 flows:
   - ARRIVAL boundary
   - DEPARTURE boundary
   - mid-trip HARD recovery
   - acknowledge warning semantics
   - feasible replacement resolves recovery
   - no-alternative state
   - stale candidate/warning
   - GPS allowed/denied
7. one DeepSeek canary if configured.

No real payment.
No physical-device pass claim.

Final verdict must be exactly:

BLOCKED

or

SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE

Output:

CityNexus-EAC-V19.2.3-FinalShadowTrial-CodeGate-20260915.zip

Stop after packaging.
