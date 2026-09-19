# Run from the real CityNexus repo after Solver Runtime integration.
$ErrorActionPreference = "Stop"
Set-Location "D:\moodle\CityNexus\backend"

# Promote/adapt these names to the actual tests created by Codex.
python -m pytest -q tests/test_solver_reference_contract.py tests/test_ortools_optional_boundary.py
if (Test-Path "tests/test_solver_runtime_gate.py") {
  python -m pytest -q tests/test_solver_runtime_gate.py
}

# Inherited authority regressions.
python -m pytest -q `
  tests/test_gpt_weather_adversarial_next.py `
  tests/test_weather_runtime_gate_gpt.py `
  tests/test_weather_runtime_hardening.py `
  tests/test_weather_refresh_endpoint.py `
  tests/test_provider_runtime_gate.py `
  tests/test_gpt_adversarial_provider_hardening.py `
  tests/test_backend_connected_golden_contract.py

python -m pytest -q
python -m compileall -q app tests
ruff check app tests
ruff format --check app tests

python "..\tools\verify_openapi_parity.py"
python "<ASSIST_DIR>\tools\check_solver_static_boundary.py" .

# If frontend/API contract changed, also run from frontend:
# npm run build
# npm run test:e2e
