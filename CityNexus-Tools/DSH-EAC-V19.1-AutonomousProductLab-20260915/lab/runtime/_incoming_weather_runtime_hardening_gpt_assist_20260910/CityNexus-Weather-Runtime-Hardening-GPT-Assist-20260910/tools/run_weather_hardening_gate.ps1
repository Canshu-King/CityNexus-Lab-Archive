$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..\..\backend")
try {
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
} finally {
  Pop-Location
}
