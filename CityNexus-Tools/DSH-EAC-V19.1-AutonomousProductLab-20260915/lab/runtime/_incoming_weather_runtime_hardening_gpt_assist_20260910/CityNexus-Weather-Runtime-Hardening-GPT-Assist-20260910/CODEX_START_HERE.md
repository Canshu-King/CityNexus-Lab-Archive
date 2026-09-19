# Codex Start Here - Weather Runtime Hardening

Do not blindly apply the reference patch.

## 1. Inspect the real tree

```powershell
git status --short
git diff --stat
```

Do not reset, clean, checkout-away, or overwrite unrelated work.

## 2. Copy only the new adversarial test first

Copy:

`tests/test_gpt_weather_adversarial_next.py`

into:

`backend/tests/test_gpt_weather_adversarial_next.py`

Then run from `backend`:

```powershell
python -m pytest -q tests/test_gpt_weather_adversarial_next.py
```

The uploaded checkpoint fails all six tests. The real tree may already contain later fixes, so use test results to decide what must be merged.

## 3. Fix only failing semantics

Reference implementation is in:

- `patches/02_WEATHER_RUNTIME_HARDENING_CODE.patch`
- `reference_overlay/`

Prefer semantic merge if the real files have moved.

## 4. Mandatory gate

Run:

```powershell
python -m pytest -q `
  tests/test_gpt_weather_adversarial_next.py `
  tests/test_weather_runtime_gate_gpt.py `
  tests/test_weather_runtime_hardening.py `
  tests/test_weather_refresh_endpoint.py `
  tests/test_provider_runtime_gate.py `
  tests/test_gpt_adversarial_provider_hardening.py `
  tests/test_backend_connected_golden_contract.py `
  tests/test_wp07_foundation_assist.py

python -m pytest -q
python -m compileall -q app tests
ruff check app tests
ruff format --check app tests
python ..\tools\verify_openapi_parity.py
```

If frontend/API contracts were touched, also run frontend build and backend-connected Playwright.

## 5. Hard stop

Once WRH-01..06 and all regressions pass, make a fresh clean review checkpoint and stop.

Do not start OR-Tools in the same mutation batch.
