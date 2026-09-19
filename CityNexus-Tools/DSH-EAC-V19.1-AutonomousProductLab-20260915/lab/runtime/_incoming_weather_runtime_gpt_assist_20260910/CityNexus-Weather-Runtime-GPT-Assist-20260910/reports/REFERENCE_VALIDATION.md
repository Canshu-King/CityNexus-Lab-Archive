# GPT Reference Validation

Date: 2026-09-10

Reference implementation was applied to a clean copy of `CityNexus-Provider-Runtime-Hardening-Checkpoint-20260910`.

## New Weather Runtime gate

```text
12 passed in 2.67s
```

## Focused regression

Included:

- Weather Runtime WRT-01..WRT-12
- WP07 weather/provider foundation
- Provider Runtime PRT-01..PRT-08
- Provider Hardening PRH-01..PRH-05
- Backend Golden Scenario

Result:

```text
33 passed in 5.77s
```

## Full backend

Pytest printed:

```text
182 passed, 1 skipped in 26.91s
```

The review container then exhibited the same already-observed Linux process-cleanup hang after pytest had printed the complete successful summary. This is not being hidden or relabeled as a clean process exit. The Windows/Codex environment must verify a normal exit code before freeze.

## Compile

```text
python -m compileall -q app tests
PASS / exit 0
```

## Ruff

Ruff is not installed in the GPT review container:

```text
ruff: command not found
```

Run Ruff in the real CityNexus dev environment before freezing.

## Patch portability

Both staged patches were checked against a fresh extraction of the reviewed checkpoint:

```text
01_WEATHER_RUNTIME_TESTS.patch           git apply --check PASS
02_WEATHER_RUNTIME_REFERENCE_IMPL.patch  git apply --check PASS
```

## Tests-first baseline evidence

Applying only the tests patch to the reviewed checkpoint fails at collection because the product runtime module does not exist yet:

```text
ModuleNotFoundError: app.integrations.context.weather_runtime
```

This confirms the tested runtime capability was not already present in that checkpoint.
