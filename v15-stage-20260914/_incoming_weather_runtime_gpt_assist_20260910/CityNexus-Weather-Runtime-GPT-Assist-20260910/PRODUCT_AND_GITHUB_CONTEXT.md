# CityNexus Product + GitHub Context for Weather Runtime Work

## Product identity

CityNexus is an **Adaptive Urban Journey Orchestration Platform**.

Its product value is Journey Continuity:

```text
Discover -> Compose -> Commit -> Execute -> Recover -> Reflect
```

Core concepts:

- Journey Twin
- durable Commitment / C4
- deterministic feasibility
- Opportunity Window
- Commitment-Aware Dynamic Replanning
- explainable ReplanDiff
- verified provider evidence

## Current frozen engineering state

- Integrated Journey Vertical Slice: `FROZEN_PASS`
- Provider Runtime / frozen MobilitySnapshot: `FROZEN_PASS`
- Current next gate: Open-Meteo Weather Runtime -> Activity attribution

Do not reopen frozen work unless a regression test proves it is broken.

## GitHub / open-source adoption map

### Current gate

`open-meteo/open-meteo`

Role:

- weather/context provider
- produces external observations only
- server normalizes and freezes provider facts
- must not decide which Activity is authoritative without CityNexus deterministic matching

### Already active / adopted

`valhalla/valhalla`

- primary real Mobility Provider candidate
- route/matrix/ETA
- facts enter frozen MobilitySnapshot
- never the feasibility authority

`microsoft/playwright`

- real backend-connected Golden Scenario E2E
- retain as regression anchor

`statelyai/xstate`

- frontend workflow orchestration
- backend Domain state remains truth

`maplibre/maplibre-gl-js`

- future real Journey map and before/after Replan visualization
- not current priority

`Turfjs/turf`

- frontend spatial helpers only
- not authoritative mobility

`shadcn-ui/ui`

- frontend UI components
- not current priority

### Next after Weather Runtime

`google/or-tools`

- advanced candidate generator
- solver output must pass deterministic feasibility + C4 protection
- current repo has only foundation/selector code

### Later AI layer

`BerriAI/litellm`

- optional AI provider abstraction, including DeepSeek
- only explanation/semantic assistance after verified facts and deterministic results

### Optional/future providers

- `graphhopper/graphhopper`: optional second routing provider
- `opentripplanner/OpenTripPlanner`: future transit/GTFS
- `Project-OSRM/osrm-backend`: fallback/reference
- `routingpy/routingpy`: optional compatibility layer

### Selective reference only

- `wang-bool/Travel-Story`: map/discovery interaction ideas
- `guberm/PlacesRecommendation`: Candidate -> Enrichment -> Scoring -> Explanation pipeline ideas

### Trust/commerce later

- `MasterKale/SimpleWebAuthn`: Passkey/WebAuthn step-up auth
- `stripe-samples/accept-a-payment`: demo/test payment adapter reference

### Deferred

`TimefoldAI/timefold-solver`

- architecture reference only because current backend is Python and OR-Tools foundation already exists

### Development tooling only

- `miuuyy/codex-chatgpt-web`
- `saerda8/codex-astra-team`

These are not CityNexus runtime dependencies and must not appear as product architecture components.

## Absolute rule

```text
External Provider / Solver / AI
-> facts/candidates/explanation
-> CityNexus deterministic authority
```

GitHub projects are parts. Journey Continuity is the product.
