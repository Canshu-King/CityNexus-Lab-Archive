# Real-Phone Shadow Trial Readiness Gate

This gate is the release boundary between "phone UI alpha" and "take CityNexus outside and use it during a real trip in shadow mode".

## Required P0 gates

### Planning truth

- [ ] template generation includes active C4 constraints
- [ ] generic composition includes active C4 constraints
- [ ] select uses the same authoritative feasibility contract as booking
- [ ] booking cannot disagree with a plan that selection just accepted on the same evidence/snapshot
- [ ] stale/infeasible candidates cannot remain selectable as current

### C4 / Journey start

- [ ] ARRIVAL C4 does not cause HTTP 500
- [ ] DEPARTURE and MID_TRIP C4 remain green
- [ ] missing route evidence produces an explicit recoverable state, not a crash
- [ ] start transition is atomic / no split Journey-Twin state
- [ ] duplicate confirmation refs do not create duplicate active C4 commitments

### Capability semantics

- [ ] both old mandated negation cases stay green
- [ ] third-party wheelchair statements do not create user HARD needs
- [ ] facility accessibility descriptions do not create user HARD needs
- [ ] hypothetical/speculative statements do not create user HARD needs
- [ ] `(TRAVELER, code)` and `(JOURNEY, code)` can coexist
- [ ] DeepSeek remains primary semantic interpreter
- [ ] local fallback is conservative and candidate-only

### Provider evidence

- [ ] `toilets:wheelchair=yes` does not satisfy `STEP_FREE_REQUIRED`
- [ ] `ramp=yes` alone does not prove full step-free place/route
- [ ] `elevator=yes` alone does not prove full step-free place/route
- [ ] `wheelchair=yes + step_count=5` -> CONFLICT
- [ ] mapping and list/tuple tag forms normalize consistently
- [ ] top-level and nested supported evidence shape behave consistently
- [ ] route step-free without route evidence remains UNKNOWN / NEEDS_LIVE_EVIDENCE

### Numeric/time constraints

- [ ] distinct distance values produce distinct actual limits
- [ ] km conversion/rejection is correct
- [ ] negative/absurd values are clarification/rejection, never clean limits
- [ ] invalid rest/nap windows are clarification/rejection, never silently usable
- [ ] interval constraints genuinely affect feasibility

### Mid-trip behavior

- [ ] confirm new HARD need while ACTIVE -> immediate reevaluation
- [ ] infeasible active plan -> governed ReplanProposal or explicit NO_ALTERNATIVE/conflict state
- [ ] live UX exposes that state

### Contract/release

- [ ] runtime OpenAPI == checked-in OpenAPI
- [ ] do not reintroduce `/api/v1` drift while "fixing" it
- [ ] frontend build passes
- [ ] broad backend genuine regressions = 0 for trial-critical paths
- [ ] remaining skips/environment-only failures are individually classified with evidence
- [ ] top-level release files describe V19.2, not V18.3

## Phone gates

Test at minimum:

```text
390x844
430x932
```

Required:

- [ ] no horizontal overflow on core pages
- [ ] PWA install/standalone launch works over a secure context
- [ ] geolocation permission + location update works on the real phone
- [ ] SSE/live updates recover after a short disconnect
- [ ] DeepSeek canary works when configured; graceful fallback when unavailable
- [ ] map/route/live journey/capability review render correctly
- [ ] offline behavior is read-only and clearly labelled; no fake success

## First real-world trial mode

The first outside trial is **SHADOW MODE**:

- real phone;
- real GPS;
- real city/location context where providers support it;
- simulated booking/payment only;
- no reliance on CityNexus for safety-critical mobility/accessibility decisions;
- user can compare CityNexus plan vs reality and record mismatches.

Passing this gate authorizes the first real-city shadow trial. It does **not** authorize production payment or unattended safety-critical use.
