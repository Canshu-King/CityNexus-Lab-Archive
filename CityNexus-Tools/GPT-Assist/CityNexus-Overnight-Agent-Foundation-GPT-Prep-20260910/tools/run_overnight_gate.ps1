$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Repo = "D:\moodle\CityNexus"
$Backend = Join-Path $Repo "backend"

Write-Host "== CityNexus Overnight Gate =="
Set-Location $Backend

$tests = @(
  "tests/test_gpt_solver_hardening_next.py",
  "tests/test_solver_runtime_gate.py",
  "tests/test_agent_runtime_gate.py"
)

foreach ($t in $tests) {
  if (Test-Path $t) {
    python -m pytest -q $t
  } else {
    Write-Host "SKIP missing $t"
  }
}

python -m pytest -q
python -m compileall -q app tests
ruff check app tests
ruff format --check app tests

Set-Location $Repo
if (Test-Path "tools\verify_openapi_parity.py") {
  python tools\verify_openapi_parity.py
}

if (Test-Path "frontend\package.json") {
  Set-Location (Join-Path $Repo "frontend")
  npm run build
  npm run test:e2e
}
