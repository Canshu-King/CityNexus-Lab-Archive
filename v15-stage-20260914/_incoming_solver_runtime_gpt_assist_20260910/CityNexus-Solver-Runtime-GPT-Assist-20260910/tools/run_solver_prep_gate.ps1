$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"

if (-not (Test-Path $Backend)) {
  throw "Expected backend directory next to tools/ in a review checkpoint. For the live repo, copy/run these commands from D:\moodle\CityNexus\backend."
}

Push-Location $Backend
try {
  python -m pytest -q tests/test_solver_reference_contract.py tests/test_ortools_optional_boundary.py
  python -m compileall -q app tests
  if (Get-Command ruff -ErrorAction SilentlyContinue) {
    ruff check app tests
    ruff format --check app tests
  }
  python (Join-Path $PSScriptRoot "check_solver_static_boundary.py") .
} finally {
  Pop-Location
}
