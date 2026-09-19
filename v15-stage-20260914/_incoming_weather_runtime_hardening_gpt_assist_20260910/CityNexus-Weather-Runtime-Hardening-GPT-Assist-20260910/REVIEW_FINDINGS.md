# CityNexus Weather Runtime External Adversarial Review

Date: 2026-09-10
Source checkpoint: `CityNexus-Weather-Runtime-Checkpoint-20260910.zip`

## Verdict

The submitted Weather Runtime is a strong implementation and its reported baseline is reproducible:

- WRT-01..WRT-12: PASS
- weather trigger/scope hardening: PASS
- Provider Runtime regressions: PASS
- full submitted backend: 188 passed, 1 skipped
- original ZIP hygiene: clean

However, it should **not yet be externally frozen**. Six additional adversarial checks expose six semantic gaps that matter to Journey Continuity and provider evidence integrity.

## WRH-01 - Parallel Open-Meteo arrays can be silently truncated

The adapter currently accepts unequal `time`, `precipitation_probability`, and `weather_code` array lengths. Missing values are silently converted to `None`.

For trusted provider evidence, malformed parallel arrays should be rejected as a controlled `OpenMeteoProviderError`, causing provider degradation rather than partially trusting a malformed payload.

Reference fix: require all requested hourly arrays to have identical length.

## WRH-02 - Persisted Weather Event loses snapshot capture time

`WeatherSnapshot` has `captured_at`, but Event ingestion receives only `WeatherRiskFact`, so the persisted provider Event does not preserve when the forecast was actually captured.

That makes later audit unable to distinguish:

- when CityNexus learned the fact, versus
- when the forecast is valid.

Reference fix: carry `snapshot_captured_at` into the frozen fact and Event payload.

## WRH-03 - Forecast validity is incorrectly used as Event occurrence time

A forecast can be captured at 11:00 local for a risk valid at 15:00 local. The submitted Event uses `occurred_at = forecast_valid_from`.

But Replan uses `Event.occurred_at` as `effective_event_time`. This can make CityNexus act as if the Journey clock has already jumped into the future.

Reference fix:

- Event becomes actionable at server capture/detection time;
- forecast validity stays in `forecast_valid_from` / `forecast_valid_until`;
- provider WEATHER Replan reads latest `snapshot_captured_at` as its decision-time anchor.

## WRH-04 - A cleared forecast never resolves the prior weather risk Event

If poll #1 says heavy rain and poll #2 successfully observes the same forecast bucket below the threshold, the prior `WEATHER` Event remains `DETECTED` forever.

A successful provider response is allowed to clear a prior weather risk only when it explicitly covers the same forecast bucket and exact query scope. Network failure or missing coverage must never clear it.

Reference fix adds coverage-aware `FORECAST_CLEARED` resolution.

## WRH-05 - Same weather phenomenon can keep stale provider evidence forever

The current stable identity intentionally deduplicates repeated polling, which is good. But when the same bucket changes from, for example, 80% to 95% precipitation probability, the existing Event is returned without refreshing trusted evidence.

Reference fix keeps one stable Event identity while refreshing its provider evidence and latest snapshot capture timestamp, with audit history.

## WRH-06 - The wrong weather time propagates into frozen MobilitySnapshot

This proves WRH-03 is not merely naming semantics.

Adversarial scenario:

- forecast captured: `00:30Z` = `08:30+08:00`
- weather bucket valid: `01:00Z` = `09:00+08:00`
- risk affects current Old Town Activity
- user generates Replan

Submitted checkpoint captures replan mobility at `09:00+08:00`.

Correct result is `08:30+08:00`, because that is the reality/decision time when CityNexus learned the forecast.

## Reference validation

Original checkpoint + new WRH tests:

`6 failed`

Reference hardening implementation:

- WRH-01..WRH-06: PASS
- combined weather/provider/golden targeted gate: 44 PASS
- full backend printed: 194 passed, 1 skipped
- compileall: PASS

The Linux review environment still exhibits the previously observed post-pytest process linger after the complete PASS line. Windows Codex must still require a clean pytest exit code and Ruff PASS before freeze.

## Non-blocking future risks

These are worth tracking but should not expand the current patch unless tests prove them important:

1. Concurrent identical refresh requests can still race because Event identity has no DB-level unique key.
2. Weather Runtime currently has only heavy-rain risk semantics; wind/heat/snow should become separate policy later, not be smuggled into the rain rule.
3. The canonical Journey has no mutable outdoor afternoon Activity, so weather-driven successful replacement is less visually demonstrable than closure recovery. Product demo enrichment can address this later without weakening C4.

## Freeze recommendation

Do not start OR-Tools yet.

First merge WRH-01..WRH-06 semantically into the real Windows tree, rerun WRT + WRH + Provider + Golden + full backend + Ruff/OpenAPI/frontend regressions, then package a fresh checkpoint for external freeze.
