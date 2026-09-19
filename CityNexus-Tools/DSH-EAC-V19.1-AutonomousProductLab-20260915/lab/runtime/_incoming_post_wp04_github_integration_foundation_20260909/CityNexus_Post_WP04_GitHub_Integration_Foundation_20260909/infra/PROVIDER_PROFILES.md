# Provider profiles

Do not commit a speculative docker-compose containing unverified images/commands.

Use these rollout profiles instead:

## `mock` (default)
- MockCityDataProvider
- MockMobilityProvider
- MockContextEventProvider
- MockBookingProvider
- MockPaymentProvider
- DeterministicFallbackAIProvider

## `mobility-valhalla`
- install `routingpy` in backend;
- start a validated local/test Valhalla service;
- configure routingpy `valhalla` client using `base_url`;
- run adapter contract tests against fixture coordinates;
- retain mock fallback.

## `mobility-graphhopper`
- only after the routingpy adapter is stable;
- run GraphHopper as a separate service;
- map CityNexus mode names to GraphHopper profiles explicitly.

## `transit-otp`
- only after usable OSM + GTFS dataset exists;
- validate transit data first;
- treat OTP as TransitMobilityProvider, not the CityNexus planner.

## `context-open-meteo`
- HTTP adapter with attribution when shown in UI;
- weather can raise context/risk facts, not invent attraction closure facts.

## `ai-deepseek`
- LiteLLM backend adapter;
- key only in backend environment;
- verified-fact input boundary;
- deterministic fallback always available.
