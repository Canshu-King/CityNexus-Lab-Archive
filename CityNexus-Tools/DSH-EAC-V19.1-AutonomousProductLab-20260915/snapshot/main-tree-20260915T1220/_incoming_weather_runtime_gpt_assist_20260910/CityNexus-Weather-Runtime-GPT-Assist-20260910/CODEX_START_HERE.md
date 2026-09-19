# Codex - Start Here

This package prepares the next CityNexus gate after Provider Runtime `FROZEN_PASS`.

## Do not blindly apply patches

The real Windows worktree may already differ from the checkpoint reviewed by GPT.

First run:

```powershell
git status --short
git diff --stat
git log --oneline -n 10
```

Do not reset, clean, or overwrite unrelated work.

## First action: tests-first probe

Copy/apply only:

```text
patches/01_WEATHER_RUNTIME_TESTS.patch
```

Then run:

```powershell
cd D:\moodle\CityNexus\backend
$env:PYTHONPATH = "."
pytest -q tests/test_weather_runtime_gate_gpt.py
```

On the checkpoint GPT reviewed, the test-only patch fails at collection because there is no `weather_runtime` product module yet. That is expected and proves the runtime gap is real.

If your current worktree already has Weather Runtime work, use the 12 tests to discover which contracts are already satisfied.

## Reference implementation

GPT prepared and independently tested:

```text
patches/02_WEATHER_RUNTIME_REFERENCE_IMPL.patch
```

It is a semantic reference, not an order to overwrite current code.

Reference implementation adds:

- frozen weather query scope
- one-hour forecast validity interval
- deterministic timezone-safe Activity attribution
- explicit indoor/outdoor sensitivity policy
- current/future execution filtering
- idempotent trusted weather Event ingestion
- idempotent provider degradation marker
- provider recovery
- explicit outdoor tags in demo data for Old Town / River Cruise

Use semantic merge if the real repo has moved.

## Reference validation already performed by GPT

```text
WRT-01..WRT-12        12 PASS
focused old+new gate  33 PASS
full backend          182 PASS / 1 SKIP
compileall            PASS
```

The Linux review container still exhibits the previously observed post-pytest process-cleanup hang after the full suite prints its successful summary. Treat the Windows test process exit code as authoritative for freeze. Ruff is not installed in GPT's review container, so run Ruff locally.

## Important design freedom

The reference semantic core intentionally does not force the final runtime trigger mechanism.

After the core tests pass, inspect the real app and choose the smallest server-owned trigger:

- scheduled/background refresh; or
- explicit POST weather-refresh operation.

Do not use a GET/Twin read path to trigger live weather calls.

If you add an endpoint, update formal OpenAPI and test parity.

## Freeze sequence

1. WRT-01..WRT-12 PASS
2. Provider PRT/PRH regressions PASS
3. Backend Golden PASS
4. Full backend PASS
5. compileall PASS
6. Ruff PASS
7. OpenAPI parity PASS if API changes
8. frontend build/Playwright PASS if frontend/API touched
9. fresh-extract review package is reproducible and clean
10. STOP and package checkpoint

Do not begin OR-Tools in the same mutation batch.
