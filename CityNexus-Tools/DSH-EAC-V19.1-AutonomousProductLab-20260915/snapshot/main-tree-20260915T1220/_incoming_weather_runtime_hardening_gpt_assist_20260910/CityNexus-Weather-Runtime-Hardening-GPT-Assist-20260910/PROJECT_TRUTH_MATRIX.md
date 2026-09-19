# CityNexus Project Truth Matrix - after Weather Runtime Review

| Area | Truth | Status |
|---|---|---|
| Backend-connected Golden Scenario | real FastAPI/SQLite path with Journey, commerce, C4, Event, Replan, Accept, Twin | FROZEN_PASS |
| Mobility Provider Runtime | Valhalla/fallback -> frozen MobilitySnapshot -> Gate with provenance and acceptance revalidation | FROZEN_PASS |
| Weather Runtime base | server-owned Open-Meteo refresh, scoped frozen facts, deterministic attribution, degradation/recovery | IMPLEMENTED |
| Weather Runtime external hardening | six new WRH semantic defects found; reference fix validated | REPAIR_REQUIRED |
| OR-Tools | small selector + ranking scaffold only; no real Activity/time-window candidate generation | FOUNDATION_ONLY |
| AI Copilot | provider abstraction/fallback foundation exists; not allowed to decide feasibility | PARTIAL / LATER |
| MapLibre | dependency/direction exists; rich real Journey map is not the current authority path | PARTIAL / LATER |
| Playwright | backend-connected Golden E2E exists | IMPLEMENTED |
| Visio/PPT/SRS | should be fed by real implementation evidence; not current engineering priority | DEFERRED |

## Immediate order

`Weather WRH-01..06 -> external freeze -> OR-Tools runtime candidate generator -> external freeze -> AI/Map experience`.
