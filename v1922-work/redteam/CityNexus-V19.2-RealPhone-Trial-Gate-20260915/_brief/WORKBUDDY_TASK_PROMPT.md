# WorkBuddy Task — V19.2 Real-Phone Trial Gate Red-Team

Continue as CityNexus's **read-only red-team**. Do not modify the authoritative main tree.

Authoritative subject:

```text
D:\moodle\CityNexus
```

Use the attached V19.2 road-prep and your previous V19.1 convergence evidence.

Do not restart the old 494-case / broad sweep. This round is narrower: prove whether Codex V19.2 is genuinely ready for a real-phone **SHADOW** trial.

## Protocol

1. Take one read-only baseline snapshot before Codex's V19.2 convergence if useful.
2. If Codex V19.2 lands during your run, take **one** targeted delta snapshot.
3. Run the same discriminating tests on both snapshots where possible.
4. Classify every target as:

```text
FIXED
STILL_REPRODUCIBLE
REGRESSED
STALE_TEST
NEW
GUARD_HOLDS
```

5. Never mutate the main tree. Apply patches only inside your isolated snapshot/lab.

## Highest-priority attacks

### 1. Single feasibility truth

Construct a real active C4 commitment and prove whether:

```text
generate
generic compose
validate
select
booking
```

all agree on the same plan and same evidence/snapshot.

Fail the gate if:

- generation offers a plan the authoritative validator rejects;
- selection accepts a plan booking immediately rejects for the same current evidence;
- template and generic compose paths disagree.

### 2. ARRIVAL C4 start matrix

Test:

```text
ARRIVAL routable
ARRIVAL missing route evidence
ARRIVAL past
DEPARTURE
MID_TRIP
```

Assert:

- no 500;
- no split Journey/Twin state;
- failure is explicit and recoverable if routing evidence is unavailable.

### 3. C4 idempotency

Attack duplicate import/confirm using the same `confirmation_ref` concurrently and sequentially.

Two active commitments for one logical confirmation is a defect.

### 4. Residual false-HARD corpus

Keep the two old mandated guards and heavily target:

```text
third-party statements
facility descriptions
speculation/hypotheticals
negated self-statements
historical/current contrasts
```

Use no more than ~120–180 high-discriminating raw-language cases. Do not inflate the run with redundant paraphrases.

DeepSeek-first behavior and local-fallback behavior should be distinguished in evidence.

### 5. Scope and canonicalization

Verify:

```text
TRAVELER + JOURNEY same code -> two rows survive
permanent language -> TRAVELER candidate when justified
this-trip language -> JOURNEY candidate
concurrent confirm does not collapse scopes
```

### 6. Provider evidence scope

Attack at least:

```text
toilets:wheelchair=yes
ramp=yes
elevator=yes
wheelchair=yes + step_count=5
highway=steps
steps=yes
{"wheelchair":["yes"]}
["wheelchair=yes", "ramp=yes"]
top-level step_free_verified
nested tag step_free evidence
route without route evidence
```

Requirement/subject scope must remain visible in the verdict.

### 7. Numeric/time boundaries

Test real boundary behavior, not only extraction:

```text
1m / 100m / 500m / 501m / 1000m
1 km
negative / absurd / missing value
continuous walking minutes
rest every N minutes
toilet every N minutes
valid and invalid time windows
```

Important road-prep policy: the conservative local fallback should not persist `0 m` as a clean authoritative walking limit. If an old test expects that while another safety test rejects it, classify the old expectation as `STALE_TEST` rather than changing product safety to satisfy contradictory tests.

### 8. Mid-trip HARD recovery

On an ACTIVE journey:

```text
confirm a new HARD capability
```

Then verify:

- active plan is reevaluated;
- infeasibility creates a governed ReplanProposal or an explicit no-alternative/conflict state;
- live `/experience` and `/twin` surfaces it;
- current plan is not silently rewritten.

### 9. Stale plan lifecycle

Cause revalidation/regeneration failure and verify old candidates are not still selectable/displayed as current viable plans.

### 10. OpenAPI

Keep an automated runtime-vs-checked-in parity check.

Do **not** file `/api/v1` prefix as a defect unless the current runtime contract actually differs. Your V19.1 Snapshot C already showed parity.

### 11. Mobile trial gate

At minimum test:

```text
390x844
430x932
```

Check:

- core pages load;
- no horizontal overflow;
- capability review uses live backend authority;
- geolocation success + denied/error path;
- SSE reconnect;
- PWA standalone/secure-context behavior if available;
- no fixture/localStorage masquerading as authoritative live state;
- a provider/error state is visible rather than silently faked.

If practical, use one real-city shadow scenario with no real payment.

## Patch validation

Validate the supplied patches independently:

```text
patches/V19_1_LOW_CONFLICT_FIXES.patch
patches/V19_1_TESTS_ONLY.patch
patches/V19_2_VERIFIED_STARTER.patch
```

Do not trust the road-prep's verification simply because it says PASS. Re-run apply-check and the focused tests in your isolated snapshot.

## Report only what changed

Deliver a concise V19.2 gate report with:

- P0 gate table;
- before/after delta;
- exact reproduction commands for remaining blockers;
- regression list;
- phone-trial verdict:
  - `BLOCKED`
  - `SHADOW_TRIAL_READY`
- evidence paths.

Do not modify the main tree.

Start now.
