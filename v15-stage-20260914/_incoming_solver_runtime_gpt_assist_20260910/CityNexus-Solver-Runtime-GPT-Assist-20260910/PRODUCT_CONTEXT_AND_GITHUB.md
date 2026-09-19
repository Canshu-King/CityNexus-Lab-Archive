# CityNexus Product / GitHub Context for Solver Runtime

CityNexus is an **Adaptive Urban Journey Orchestration Platform**. Its differentiator is Journey Continuity: preserve real-world Commitments while keeping the Journey executable as reality changes.

Lifecycle:

```text
Discover -> Compose -> Commit -> Execute -> Recover -> Reflect
```

Core authority chain:

```text
Provider facts
-> frozen evidence
-> Journey / PlanVersion / Activity / Commitment truth
-> candidate generation
-> deterministic feasibility
-> verified scoring / ReplanDiff
-> Traveler confirmation
```

## Current frozen milestones

- Integrated backend-connected Golden Scenario: FROZEN_PASS.
- Valhalla / Frozen Mobility Runtime: FROZEN_PASS.
- Open-Meteo Weather Runtime + hardening: EXTERNAL_FROZEN_PASS.

## GitHub / open-source adoption

### Current stage
- `google/or-tools`: first real advanced candidate generator. **Current main focus.**

### Already established
- `valhalla/valhalla`: primary real mobility provider, adapted into frozen `MobilitySnapshot` facts.
- Open-Meteo: real context/weather provider, adapted into frozen scoped weather facts and provider-verified Events.
- `microsoft/playwright`: backend-connected Golden Scenario E2E.

### Experience layer, later
- `maplibre/maplibre-gl-js`: real Journey map.
- `Turfjs/turf`: frontend spatial helpers only.
- `statelyai/xstate`: UI workflow orchestration, never Domain truth.
- `shadcn-ui/ui`: UI components.

### AI, later
- `BerriAI/litellm` + DeepSeek: explanation/semantic assistance only after verified facts and deterministic decisions.

### Optional / deferred
- GraphHopper: optional second mobility provider.
- OpenTripPlanner: future transit/GTFS.
- OSRM: fallback/reference.
- routingpy: optional compatibility wrapper.
- Timefold: architecture reference only; do not introduce a second JVM solver runtime now.
- SimpleWebAuthn and Stripe sample: later Trust/Commerce work.

### Development tooling only
- `miuuyy/codex-chatgpt-web`: developer workflow tool, **never** a CityNexus runtime/SRS dependency.

## Solver rule

OR-Tools is allowed to answer:

> "Here are candidate schedules worth checking."

It is never allowed to answer:

> "This Journey is officially feasible."

That judgment belongs to CityNexus deterministic feasibility after materialization using the same frozen facts.
