# CityNexus Product and GitHub Context

## Product identity

CityNexus is an **Adaptive Urban Journey Orchestration Platform** for the Software Engineering coursework project **#11 A Smart City Traveler System**.

The product value is Journey Continuity, not a generic travel recommendation app.

Core lifecycle:

`Discover -> Compose -> Commit -> Execute -> Recover -> Reflect`

Core concepts:

- Journey / PlanVersion / Activity
- JourneyTwin as read projection, never source of truth
- durable Commitment, especially C4 anchored/paid facts
- deterministic feasibility as authority
- Opportunity Window
- Commitment-Aware Dynamic Replanning
- ReplanDiff and explainable evidence
- provider facts frozen before decision logic

## GitHub adoption map

### Active / direct

- `valhalla/valhalla`: primary real mobility provider; now behind frozen MobilitySnapshot
- `open-meteo/open-meteo`: real context/weather provider; current stage
- `google/or-tools`: next real candidate-generator stage after Weather freeze
- `maplibre/maplibre-gl-js`: real journey map later
- `Turfjs/turf`: frontend spatial helper only
- `statelyai/xstate`: UI workflow orchestration only
- `shadcn-ui/ui`: UI components
- `microsoft/playwright`: backend-connected Golden Scenario E2E

### Optional / future

- `graphhopper/graphhopper`: optional second routing provider
- `opentripplanner/OpenTripPlanner`: transit/GTFS later
- `Project-OSRM/osrm-backend`: fallback/reference
- `routingpy/routingpy`: optional compatibility wrapper
- `MasterKale/SimpleWebAuthn`: later trust/step-up authentication
- `stripe-samples/accept-a-payment`: demo/test payment adapter reference
- `BerriAI/litellm`: later AI provider abstraction / DeepSeek access

### Reference only

- `wang-bool/Travel-Story`: map/discovery interaction ideas
- `guberm/PlacesRecommendation`: candidate -> enrichment -> scoring -> explanation ideas
- `TimefoldAI/timefold-solver`: architecture reference; do not introduce JVM while Python + OR-Tools is current runtime

### Development tooling only

- `miuuyy/codex-chatgpt-web`
- `saerda8/codex-astra-team`

These must never appear as CityNexus runtime dependencies or product capabilities.

## Authority chain

```text
External provider / solver / AI
-> verified/frozen facts or candidates
-> deterministic CityNexus Gate
-> verified scoring / diff
-> Traveler confirmation
-> new Domain truth
```

Provider != judge. OR-Tools != judge. AI != judge. JourneyTwin != source of truth.
