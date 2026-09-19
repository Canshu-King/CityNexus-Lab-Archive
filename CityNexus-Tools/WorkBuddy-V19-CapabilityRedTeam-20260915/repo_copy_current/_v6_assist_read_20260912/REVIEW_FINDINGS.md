# External Review Findings — V5 Final

## V5 is real

The reviewed V5 checkpoint contains:
- server-owned Guardian autorun worker;
- provider observation and semantic incident fingerprint persistence;
- real cooldown/dedup logic;
- configured Agent runtime before deterministic fallback;
- real native DeepSeek model-backed tool loop;
- real OR-Tools CP-SAT Solver V2 in the Windows evidence;
- SSE operations stream;
- zero-manual-Guardian-scan browser flow;
- clean package hygiene in the uploaded V5 archive.

Independent focused replay in the external review environment produced 57 passing tests and two failures caused only by OR-Tools being unavailable in that environment, which forced the honest enumeration fallback where the Windows tests expected CP-SAT.

## Finding V6-A — Autopilot enablement is process-global, not Journey-scoped

`start_autorun()` starts one module-global thread.
`run_once()` scans every ACTIVE Journey that has an ACTIVE standing mission.
The route is shaped as:
`POST /journeys/{journey_id}/guardian/autopilot/start`
but starting J1 effectively enables processing for J2 as well if J2 also has a standing mission.

Likewise, stopping through one Journey stops the global worker.

V6 should separate:
- worker process lifecycle;
- per-Journey Autopilot enrollment.

Persist a Journey-level enrollment/subscription state. The worker may remain global, but it scans only enrolled Journeys.

## Finding V6-B — live signal mode is weather-only

`autorun.refresh_signals()` currently chooses either:
- `_live_weather_refresh()`, or
- `refresh_demo_signals()`.

The live branch does not compose live weather with mobility observation/delta capture.
The demo branch does both.

V6 needs a Provider Mesh:
weather + routing/mobility + POI/city discovery, normalized independently.

Do not model provider selection as one exclusive global string.

## Finding V6-C — current "Hermes adapter" is not yet literal Hermes orchestration

`HermesJourneyAgent` is an OpenAI-compatible endpoint adapter that inherits the native DeepSeek tool loop shape.
It is useful as an adapter seam, but V5 correctly did not claim Hermes model-backed execution.

V6 should run an actual Hermes Agent runtime when feasible, ideally against the current supported release, using CityNexus MCP V2 as its CityNexus tool boundary.

The native DeepSeek runtime remains a strong fallback.

## Finding V6-D — service discovery is still local-catalog only

`search_city_services` currently queries the CityNexus DB.
The demo Place catalog is seeded/static.

A real traveler product needs real city discovery:
- geocode natural-language places;
- find nearby real POIs;
- materialize selected provider-backed Places into CityNexus;
- preserve provider provenance.

Nominatim is suitable for name/address geocoding.
Overpass is suitable for area/category POI discovery.

## Finding V6-E — MapLibre still lacks a real basemap

The current `JourneyMap.tsx` initializes MapLibre with an empty source list and a plain background layer.
Routes and overlays are real CityNexus sources, but the city itself is visually blank.

V6 should use a real vector basemap. OpenFreeMap is a strong no-key option for development/demo.

## Finding V6-F — proactive recovery is reactive to detected facts, not predictive

V5 reacts after a provider signal becomes a disruption.

The next product leap is predictive:
- forecast near-future Journey risk;
- simulate plausible disruptions;
- calculate resilience before failure;
- preemptively replan when the expected benefit exceeds switching cost.

This should become a core CityNexus differentiator.
