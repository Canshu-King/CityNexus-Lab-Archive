# Provider Runtime Design for the stage after backend-connected Golden Scenario

This is a **future-stage design**, not permission to enable live providers before the current Golden gate passes.

## Independent code finding

In the uploaded Goal checkpoint:

- `settings.live_valhalla_url` is used by an opt-in smoke test, not by product route handlers;
- `generate_replan()` uses `MockMobilityProvider()` directly;
- persisted-plan feasibility also defaulted to `MockMobilityProvider()` before the repair seam;
- `_twin_snapshot()` computes OpportunityWindow travel/buffer using `MockMobilityProvider()` directly;
- Replan `verified_evidence.mobility.provider` is hardcoded as `mock-mobility`;
- Open-Meteo provider/ingestion code exists as modules but is not a live mandatory application path.

Therefore the correct claim today is **provider foundation exists**, not **real providers drive the product runtime**.

## Do not solve this by calling Valhalla from the gate or GET /twin

Forbidden architecture:

```text
GET JourneyTwin / evaluate_feasibility
→ live HTTP provider call
→ result changes with network state
```

The gate must remain pure/deterministic over frozen evidence.

## Recommended mobility evidence flow

```text
runtime orchestration
→ determine required origin/destination pairs
→ provider adapter call OUTSIDE deterministic gate
→ validate / normalize
→ fallback if allowed
→ freeze TravelEstimateFact[] into MobilitySnapshot
→ persist/refer to snapshot with captured_at + provider provenance
→ evaluate_feasibility(... mobility_provider=snapshot)
→ persist proposal evidence using the same snapshot provenance
→ JourneyTwin projects already-frozen evidence, never calls provider live
```

At accept-time, choose one explicit policy and test it:

```text
A. recapture a fresh server-side snapshot before revalidation
or
B. revalidate against the proposal's frozen snapshot plus staleness policy
```

For dynamic journey recovery, A is preferable if the provider is available, with explicit degraded fallback. In either case, the gate receives a frozen snapshot.

## Recommended persistence shape

Do not blindly add a giant new microservice. A small modular-monolith persistence record is enough, for example:

```text
MobilityEvidenceSnapshot
- id
- journey_id
- plan_version_id nullable
- trigger_event_id nullable
- purpose: INITIAL_PLAN | REPLAN_GENERATION | REPLAN_ACCEPT | TWIN_PROJECTION
- source_provider_key
- captured_at
- degraded
- facts_json
- created_at
```

`facts_json` can initially store normalized records:

```json
[
  {
    "origin_key": "place-food-hall",
    "destination_key": "place-city-park",
    "minutes": 15,
    "provider_key": "valhalla-http",
    "degraded": false
  }
]
```

This is adequate for course-level traceability and reproducibility. Normalize into a separate table only if later requirements actually need queryability at that granularity.

## JourneyTwin contract improvement

Twin should eventually expose provider evidence such as:

```text
mobility_snapshot_id
mobility_captured_at
mobility_provider
mobility_degraded
next_commitment_travel_min
```

Then `opportunity_window` and `next_commitment_buffer_min` can be explained from the same frozen evidence the backend trusts.

## Replan evidence improvement

Replace hardcoded:

```text
"provider": "mock-mobility"
```

with evidence derived from the actual frozen snapshot:

```text
provider
captured_at
degraded
pairs_used
```

Do not expose raw provider payload unless needed. Normalize first.

## Weather runtime flow

Use the same pattern:

```text
Open-Meteo HTTP
→ normalize timezone-safe observations
→ freeze WeatherSnapshot / WeatherRiskFact
→ server-owned PROVIDER_VERIFIED Event
→ deterministic disruption/replan logic
```

Provider outage:

```text
record SYSTEM_DERIVED degradation
→ Twin DEGRADED
→ retain deterministic fallback behavior
→ resolve degradation after provider recovery
```

## Order of implementation

Only after backend-connected Playwright passes:

```text
1. persist mobility evidence snapshot
2. make replan generation use a frozen snapshot
3. make accept-time revalidation use a freshly frozen/reused snapshot by explicit policy
4. make Twin project frozen mobility evidence instead of calling Mock directly
5. add Valhalla live opt-in orchestration with Mock fallback
6. add bounded Open-Meteo app orchestration
```

This avoids the classic human achievement of having six adapters and zero coherent evidence path.
