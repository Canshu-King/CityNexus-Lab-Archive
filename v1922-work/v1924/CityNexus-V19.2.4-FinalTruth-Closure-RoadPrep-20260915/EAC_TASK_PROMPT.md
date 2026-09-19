You are performing one final narrow CityNexus code-truth closure.

Freeze:

CityNexus-EAC-V19.2.3-FinalShadowTrial-CodeGate-20260915.zip

as Snapshot F.

Authoritative worktree:

D:\moodle\CityNexus

Do NOT start V19.3.
Do NOT add broad product features.
Do NOT redo already-green responsive or OpenAPI path work.

Read:

README_FIRST.md
INDEPENDENT_AUDIT.md
ACCEPTANCE_MATRIX.md
VERIFICATION.md

A small starter patch is included:

patches/V19_2_4_GPT_VERIFIED_CLOSURE.patch

Run `git apply --check` first.
Do not blindly apply if the live tree differs. Port the same semantics.

==================================================
P0 — SHARED FEASIBILITY MUST ENFORCE C4 TEMPORAL TRUTH
==================================================

Snapshot F's scheduler is fixed, but the authoritative shared deterministic
feasibility gate still accepts impossible persisted plans.

Independent replay against the final V19.2.3 source proved:

ARRIVAL 12:30 + flexible POI 09:00-10:15
-> evaluate_feasibility() PASSES

DEPARTURE 15:30 + flexible POI 17:00-18:30
-> evaluate_feasibility() PASSES

ARRIVAL 17:00 + DEPARTURE 10:00
-> evaluate_feasibility() PASSES

This is a P0.

Fix app/replanning/feasibility.py.

Required:

1. Do not widen the Journey window to make C4 anchors fit.
2. Parse LOCKED_COMMITMENT anchor_role and time_boundary.
3. ARRIVAL completion is a lower boundary for all non-anchor city activities.
4. DEPARTURE start is an upper boundary for all non-anchor city activities.
5. ARRIVAL after DEPARTURE is a deterministic precise conflict.
6. Structural anchors outside the Journey window are explicit conflicts.
7. MID_TRIP remains an interior exact commitment.
8. Existing lock-preservation checks remain active.
9. A valid plan still passes.

Add tests that directly call the shared feasibility gate on deliberately invalid
persisted plans. Do not accept generator-only tests as proof.

Minimum tests:

F01 pre-arrival activity -> FAIL
F02 post-departure activity -> FAIL
F03 ARRIVAL-after-DEPARTURE -> FAIL
F04 valid ARRIVAL control -> PASS

==================================================
P1 — RECOVERY PROJECTION MUST FOLLOW DURABLE FACTS
==================================================

Snapshot F still permits:

open Event status = DETECTED
+
recovery_state(... is_feasible=True)
->
state = RESOLVED

while recovery_flags still says recovery_required=true.

Fix this structural inconsistency.

Required invariant:

- an open Event is RECOVERY_REQUIRED or NO_ALTERNATIVE;
- it is never projected RESOLVED merely from a caller boolean;
- only a transactional workflow that revalidates and explicitly resolves the
  Event may close it;
- acknowledgement remains non-resolving;
- NO_ALTERNATIVE still requires a recorded replan attempt;
- only candidate ids recorded by a real feasibility-checked replan attempt are
  exposed as recovery alternatives.

Review GET /experience.

A GET projection should not be the only thing performing a durable recovery
transition. Do not rely on an uncommitted read request to resolve Event truth.

Keep the existing correct transactional resolution after selecting a feasible
replacement.

==================================================
P1 — ALIGN RESERVATION QUARANTINE HELPER WITH DB SCHEMA
==================================================

The startup migration is now good. Keep it.

But app/operations/reservation_identity.py still writes:

event_type = RESERVATION_IDENTITY_DUPLICATE

which violates the closed Event event_type CHECK.

Fix the ORM helper:

- sanctioned event_type = USER_CHANGE
- provider key can remain reservation-specific
- payload.kind = RESERVATION_IDENTITY_DUPLICATE
- exclude status=QUARANTINED_DUPLICATE_IDENTITY from duplicate detection
- second run must be idempotent / no repeated repair

Do not weaken the partial unique index.

==================================================
RETEST
==================================================

Run:

1. direct F01-F04 shared-feasibility tests
2. V19.2 contract suite
3. V19.2.3 closure suite
4. recovery lifecycle tests
5. duplicate migration + helper tests
6. authoritative backend regression
7. frontend build
8. OpenAPI parity guard
9. targeted mobile recovery/stale/C4 flows only if affected
10. one bounded DeepSeek canary only if semantic code changed (otherwise do not
   waste a live call)

New regressions must be zero.

==================================================
OUTPUT
==================================================

Target:

CityNexus-EAC-V19.2.4-FinalTruth-CodeGate-20260915.zip

Include:

- actual changed source / clean patch
- FINAL_TRUTH_GATE_REPORT.md
- FEASIBILITY_C4_GATE_RESULTS.md
- RECOVERY_TRUTH_RESULTS.md
- RESERVATION_HELPER_RESULTS.md
- TEST_RESULTS.md
- PATCH_RESULTS.md
- CHANGED_FILES.txt
- clean package inventory

Final verdict exactly:

BLOCKED

or

SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE

Stop after packaging.
Do not start V19.3.
