# Road-Prep Verification

## Inputs independently inspected

```text
CityNexus-V19.1-Capability-Evidence-LiveUX-20260915.zip
CityNexus-WorkBuddy-V19.1-ConvergenceRedTeam-20260915.zip
```

## Verified against supplied Codex V19.1 reference

```text
V19_1_LOW_CONFLICT_FIXES.patch  -> git apply --check PASS
V19_1_TESTS_ONLY.patch          -> git apply --check PASS
V19_2_VERIFIED_STARTER.patch    -> git apply --check PASS
```

## Starter-patch targeted tests

Production files touched:

```text
backend/app/capabilities.py
backend/app/replanning/feasibility.py
```

Targeted verification in an isolated scratch tree:

```text
false-HARD/evidence/merge selection: 32 passed
scope-language selection:             8 passed
numeric/window safety selection:      8 passed
```

Full two-module WorkBuddy contract run after the starter patch:

```text
144 passed
1 failed
13 skipped
```

The one failure is a contradictory test expectation for `0 m`:

- one test requires `max_m=0` to be extracted;
- another safety test requires a non-positive walking limit not to persist.

The V19.2 road-prep chooses the conservative trial policy: local fallback treats `0 m` as clarification/special-mobility input rather than a clean authoritative numeric limit.

## Important: not verified as fixed by this package

The road-prep does not claim these are already solved:

```text
C4 feasibility split-brain
ARRIVAL C4 /start 500
mid-trip HARD replan orchestration
stale candidate lifecycle
C4 confirmation_ref idempotency
broad backend regression
real-phone PWA secure-context run
```

Those are Codex V19.2 implementation tasks and WorkBuddy validation targets.
