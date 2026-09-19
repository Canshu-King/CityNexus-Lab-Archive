# CityNexus Project Truth Matrix - Solver Handoff

| Capability | Status | Evidence / boundary |
|---|---|---|
| Backend-connected Golden Scenario | FROZEN_PASS | Real FastAPI/SQLite Booking -> Payment -> C4 -> Execute -> Event -> Replan -> Accept -> Twin -> reload flow |
| Durable C4 Commitment protection | FROZEN_PASS | Generate-time + accept-time deterministic revalidation |
| Frozen Mobility Runtime | FROZEN_PASS | Valhalla/Mock facts captured into operation-scoped MobilitySnapshot; no network in gate/read path |
| Weather Runtime | EXTERNAL_FROZEN_PASS | Open-Meteo -> scoped/temporal WeatherSnapshot -> deterministic Activity attribution -> provider-verified Event; hardening regressions green |
| Weather event lifecycle | IMPLEMENTED with minor debt | dedup/update/clear/reopen supported; resolved trigger blocks accept, but stale PRESENTED proposal cleanup is later debt |
| OR-Tools adapter foundation | FOUNDATION_ONLY | Existing selector is not a Journey scheduler |
| Real OR-Tools Replan Runtime | NOT IMPLEMENTED | This Assist package prepares the first replacement-window CP-SAT integration |
| OR-Tools reference contract/oracle | GPT-PREPARED | 15 PASS / 2 SKIP in GPT environment; skips require real OR-Tools installation |
| AI Journey Copilot | PARTIAL / LATER | Deterministic fallback/abstraction exists; LiteLLM/DeepSeek must not become authority |
| Real MapLibre Journey map | PARTIAL / LATER | frontend shell/dependencies exist; do not claim full real map yet |
| WebAuthn / real payment gateway | LATER | Trust/Commerce enhancement after core intelligence |
| Visio/PPT/SRS final assembly | LATER | must be derived from real implemented/tested software |

## Current single next objective

```text
OR-Tools Solver Runtime V1
replacement-window CP-SAT
-> existing authoritative gate
-> verified scoring
-> review checkpoint
```
