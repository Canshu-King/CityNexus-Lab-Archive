# Weather Runtime Hardening External Review

Reviewed source: `CityNexus-Weather-Runtime-Hardening-Checkpoint-20260910.zip`.

## Independent results in GPT review environment

- WRH-01..06: **6 passed**.
- Combined Weather/Provider/Golden/WP07 targeted gate: **44 passed**.
- `python -m compileall -q app tests`: **PASS**.
- OpenAPI parity: **formal 39 / runtime 39 / missing 0 / extra 0**.
- Review-package hygiene: no `__pycache__`, `.pyc`, runtime DB, `test-results`, `node_modules`, or build cache in the uploaded ZIP.
- Full pytest traversed 100% of the suite in this Linux sandbox but reproduced the known post-suite process-linger behavior; the checkpoint's Windows validation reports **194 passed, 1 skipped** with a clean run plus Ruff and frontend/Playwright PASS.

## Semantic review

The six prior blockers are genuinely implemented in source, not merely weakened in tests:

- malformed Open-Meteo parallel arrays fail closed;
- capture time and forecast-valid time are separate;
- provider Event decision time is capture time;
- covered same-scope buckets can clear stale weather risk;
- stable Event identity refreshes latest trusted evidence;
- Replan uses latest trusted weather capture time as its decision clock.

Trusted weather input remains server-owned. Twin GET and deterministic feasibility do not perform Open-Meteo network calls. Durable C4 remains authoritative.

## Freeze verdict

**Weather Runtime Hardening: EXTERNAL_FROZEN_PASS**.

Two non-blocking lifecycle debts should be carried forward rather than reopening this gate:

1. when a weather Event clears, already-PRESENTED proposals tied to that Event remain `PRESENTED`; acceptance is correctly blocked by the resolved trigger, but a future UI/lifecycle cleanup should invalidate/retire those stale proposals;
2. `resolve_provider_degradation()` should eventually narrow its query explicitly to `SERVICE_UNAVAILABLE` for defensive clarity.

Neither debt permits a stale proposal to be accepted or fabricates provider truth, so neither blocks Solver Runtime.
