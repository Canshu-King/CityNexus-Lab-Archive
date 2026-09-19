# CityNexus Weather Runtime - Current Gap Analysis

Date: 2026-09-10
Basis: Provider Runtime Hardening checkpoint after external FROZEN_PASS review.

## What is already real

The repository already has useful Open-Meteo foundations:

- `OpenMeteoContextProvider`
- UTC / Unix timestamp-safe parsing
- `WeatherObservation` / `WeatherRisk`
- `WeatherSnapshot` / `WeatherRiskFact`
- `freeze_weather_risks()`
- server-owned `PROVIDER_VERIFIED` weather ingestion
- provider degradation / recovery events
- public Event API rejection of forged trusted provenance
- JourneyTwin projection of unresolved provider degradation
- existing Replan support for `WEATHER` events

Those pieces are not the missing product capability.

## What is missing in the checkpoint

### 1. There is no weather runtime orchestration

Nothing currently performs this complete operation:

```text
active/current + upcoming activities
-> determine weather-sensitive places
-> query Open-Meteo
-> freeze facts
-> attribute facts to activities
-> persist provider-verified events
```

The provider adapter is therefore still foundation rather than product runtime.

### 2. `affected_activity_id` is still manually supplied to trusted ingestion

`ingest_provider_verified_weather_event(..., affected_activity_id=...)` accepts an Activity id from its internal caller. There is no deterministic server-owned matcher proving why a specific Open-Meteo fact applies to that Activity.

### 3. Weather facts lack explicit query-scope evidence

The existing frozen fact records provider evidence such as precipitation probability but not the exact Place / latitude / longitude used to obtain that fact.

Without query scope, an auditor cannot prove why a forecast was applied to a particular Activity.

### 4. Hourly weather validity is implicit

An Open-Meteo hourly timestamp represents a weather bucket. The current fact only stores one instant. Activity matching needs an explicit interval, e.g. `[valid_from, valid_until)`.

### 5. Weather sensitivity has no explicit deterministic policy

Some Places already carry `indoor` / `outdoor` tags, but runtime logic does not use them. Do not let AI infer whether rain affects an Activity.

Recommended minimum policy:

```text
weather_sensitive tag -> eligible explicit override
indoor tag             -> not rain-sensitive
outdoor tag            -> rain-sensitive
otherwise              -> not attributed automatically
```

### 6. Repeated weather polling can create duplicate events

Trusted weather ingestion currently creates a new Event on every call. The same provider risk for the same Journey / Activity / validity bucket should be idempotent.

### 7. Repeated provider outages can create an Event storm

`record_provider_degradation()` currently creates a new unresolved provider outage event each time it is called. One unresolved Open-Meteo degradation marker is enough until recovery.

### 8. C4 safety exists, but should be tested as a contract

Current Replan behavior rejects automatic replacement of a locked Activity for `WEATHER`. That is conservative and acceptable for the Weather Runtime gate as long as the durable C4 Commitment is proven unchanged.

### 9. The read path is already correctly separated

`GET JourneyTwin` reads persisted events/degradation state. It does not call Open-Meteo. Keep this invariant.

## Reference solution prepared by GPT

The assist package contains a tested reference semantic core that adds:

- exact `WeatherQueryScope`
- immutable provider evidence
- explicit one-hour validity buckets
- deterministic tag-based weather sensitivity
- timezone-safe Activity overlap matching
- current/future execution filtering
- exact Place-scope attribution
- idempotent weather Event ingestion
- idempotent degradation recording
- recovery semantics
- WRT-01..WRT-12 tests

This is a reference implementation, not an instruction to overwrite the real repo. Codex should first run the tests against the current Windows worktree, then semantic-merge only what is missing.

## Product trigger still requires an explicit decision

The reference core intentionally does not force a scheduler/API design. Codex should inspect the current product and choose the smallest server-owned trigger, for example:

- a background/scheduled refresh service; or
- an explicit server-owned `POST .../weather/refresh` operation used by demo/UI/admin tooling.

Hard rule: never trigger live weather HTTP from a GET/read projection or from inside deterministic feasibility.
