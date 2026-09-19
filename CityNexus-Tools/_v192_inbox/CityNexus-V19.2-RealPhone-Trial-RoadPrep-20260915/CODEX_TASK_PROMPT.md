# Codex Task Prompt — V19.2 Real-Phone Trial Gate

Use the attached **CityNexus V19.2 Real-Phone Trial Road-Prep**.

Authoritative worktree:

```text
D:\moodle\CityNexus
```

Use the current live main tree as authority. Use these artifacts only as evidence/reference:

```text
CityNexus-V19.1-Capability-Evidence-LiveUX-20260915.zip
CityNexus-WorkBuddy-V19.1-ConvergenceRedTeam-20260915.zip
```

Read, in order:

```text
README_FIRST.md
BASELINE_AUDIT.md
DEFECT_MATRIX.md
PATCH_PORT_MATRIX.md
TRIAL_READINESS_GATE.md
ACCEPTANCE_MATRIX.md
VERIFICATION.md
RUNBOOK.md
```

This task supersedes the previous V19.1 convergence prompt.

## Mission

Do **not** start another broad feature wave.

Converge the current product into **V19.2 Real-Phone Trial Gate** so the user can run the first real-phone, real-GPS, real-city **SHADOW** trial without relying on fake feasibility or crash-prone C4 behavior.

## 1. Inspect before editing

Start with:

```text
git status --short
```

Inspect the live implementations around:

```text
backend/app/services.py
  _journey_constraints_with_capabilities
  _generic_compose_plans
  validate_plan_feasibility
  generate_plans

backend/app/main.py
  select_plan
  _assert_selected_plan_feasible
  _twin_snapshot
  start_journey

backend/app/operations/v9.py
  confirm_reservation_draft

backend/app/capabilities.py
backend/app/replanning/feasibility.py
```

Do not assume line numbers from the review package still match.

## 2. Port the verified low-conflict capability/evidence fixes

Review:

```text
patches/V19_2_VERIFIED_STARTER.patch
```

It apply-checks against the supplied Codex V19.1 reference and has targeted verification, but **do not blindly apply it** if the live tree moved.

Semantically preserve at least:

- canonicalization keyed by `(scope, code)`;
- mapping list/tuple value normalization;
- stairs conflict from `step_count`, `steps`, `highway=steps`;
- supported top-level step-free/stairs evidence keys;
- conservative local false-HARD guards for third-party/facility/speculation text;
- permanent vs this-trip scope hints as a fallback only;
- strictest numeric upper-bound merge;
- negative/km/time-window safety.

DeepSeek remains primary. The local extractor remains conservative and candidate-only.

## 3. Fix the P0 feasibility split-brain

This is the highest-value product fix.

Today:

```text
generate -> can ignore active C4
select   -> can ignore active C4
booking  -> includes active C4 and rejects the selected plan
```

Make generation, generic composition, selection, validation and booking consume one authoritative constraint assembly / feasibility contract.

Requirements:

- active C4 constraints included consistently;
- template and generic paths both covered;
- selection uses the same feasibility truth as booking;
- preserve the selected PlanVersion's frozen mobility snapshot semantics;
- do not duplicate C4 logic across five call sites if a single helper can own it;
- keep explainable failure codes.

Add regression tests that explicitly prove:

```text
If booking would reject a plan for LOCKED_COMMITMENT_LOST on the same evidence,
selection must not accept it first.
```

## 4. Fix ARRIVAL C4 `/start` crash

Do not patch around the exception with a generic try/except.

Fix the model/runtime boundary.

An ARRIVAL anchor must resolve to a routable place/coordinate/alias when trip context/provider data has one. If evidence is not routable, Twin/start must degrade explicitly and safely instead of raising HTTP 500.

Add a start matrix:

```text
ARRIVAL
DEPARTURE
MID_TRIP
ARRIVAL with missing route evidence
ARRIVAL already in the past
```

Verify Journey and Twin state transitions remain atomic.

## 5. Make mid-trip HARD capability operational

For an ACTIVE journey:

```text
confirm new HARD capability
-> reevaluate active plan
-> if infeasible:
     create governed ReplanProposal
     OR persist an explicit NO_ALTERNATIVE/conflict state
-> surface through live experience/twin UX
```

Do not silently mutate the active plan.

## 6. Finish numeric/time semantics

The product must not merely recognize numeric capability codes; it must enforce the values.

Cover:

- walking distances;
- continuous walking duration;
- rest interval;
- toilet interval;
- rest/nap time windows;
- unit conversion / input validation.

For the conservative local fallback, treat non-positive walking values such as `0 m` as clarification/special-mobility input rather than a clean authoritative numeric limit. The WorkBuddy tests contain a contradictory legacy expectation here; update the trial-gate test contract instead of satisfying both impossible assertions.

## 7. Candidate lifecycle

When regeneration/revalidation proves a candidate invalid, mark it stale/superseded/invalid or remove it from the selectable current set.

Do not leave a known-infeasible candidate looking live in the UI.

## 8. C4 idempotency and reasons

If low-risk in this round:

- enforce idempotency/uniqueness for C4 `confirmation_ref`;
- preserve useful feasibility reason codes through the API and frontend;
- avoid replacing actionable `LOCKED_COMMITMENT_LOST` with generic failure prose.

## 9. Do not regress already-correct V19.1 behavior

Must remain true:

```text
I don't need a wheelchair, I can walk
-> no HARD STEP_FREE_REQUIRED

朋友说我可能需要轮椅，但我不这么认为
-> no HARD STEP_FREE_REQUIRED

toilets:wheelchair=yes
-> does not verify whole STEP_FREE_REQUIRED

route step-free without real route evidence
-> UNKNOWN / NEEDS_LIVE_EVIDENCE

PUT capabilities
-> full desired-set replace

POST /capabilities/confirm
-> upsert submitted only, preserve other active items
```

## 10. OpenAPI

WorkBuddy Snapshot C found parity. Treat this as a regression guard, not a new architecture task.

Do not rework `/api/v1` unless a current test proves actual drift.

## 11. Mobile trial readiness

Keep the current React/Vite/PWA path. Do not detour into a native Android rewrite or APK packaging in this round.

Add/finalize a real-phone runbook that covers:

- backend start;
- frontend production/preview or secure dev tunnel;
- HTTPS requirement for PWA/geolocation where applicable;
- phone install/standalone launch;
- LAN/tunnel API connectivity;
- geolocation permission failure path;
- SSE reconnect;
- log collection;
- how to reset a trial Journey safely.

Run at minimum:

```text
390x844
430x932
```

## 12. Validation

Use the tests-only patch as a source of high-value red-team cases, not as an infallible oracle.

At convergence run:

1. focused capability/evidence tests;
2. C4 start matrix;
3. generate/generic/select/booking feasibility-consistency tests;
4. mid-trip HARD recovery tests;
5. numeric/time-boundary tests;
6. OpenAPI parity;
7. frontend build;
8. mobile browser flow at 390x844 and 430x932;
9. PWA secure-context/standalone smoke if the environment supports it;
10. one broad backend regression;
11. one DeepSeek canary if configured;
12. Hermes PLAN_ONLY only if native Hermes is actually available; do not fake Connected state.

## 13. Release truth

The supplied V19.1 artifact has stale top-level V18.3 release files.

V19.2 must regenerate current:

```text
CURRENT_STATUS.md
TEST_RESULTS.md
NEXT_RECOMMENDATION.md
CHANGED_FILES.txt
PACKAGE inventory/manifest if used
PHONE_TRIAL_RUNBOOK.md
```

Every headline claim must match the final tree and final test run.

## 14. Packaging and stop condition

Target:

```text
CityNexus-V19.2-RealPhone-Trial-Gate-20260915.zip
```

Fresh-extract once and rerun the focused gate once.

When `TRIAL_READINESS_GATE.md` is satisfied, **STOP**. Do not start V19.3, native Android, real payment, or another provider wave in the same task.

Start implementation now.
