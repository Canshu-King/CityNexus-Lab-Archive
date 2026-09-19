$ErrorActionPreference = "Stop"

$Repo = (Get-Location).Path
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Ruff = Join-Path $Repo ".venv\Scripts\ruff.exe"

if (-not (Test-Path $Python)) { throw "Missing $Python" }
if (-not (Test-Path $Ruff)) { throw "Missing $Ruff" }
if (-not (Test-Path (Join-Path $Repo "backend\app"))) { throw "Run from D:\moodle\CityNexus" }

Write-Host "== Git safety snapshot =="
git status --short
git diff --stat

Write-Host "== Targeted backend hardening gate =="
Push-Location (Join-Path $Repo "backend")
& $Python -m pytest -q `
  tests\test_vertical_slice_hardening_next.py `
  tests\test_backend_connected_golden_contract.py `
  tests\test_post_goal_five_defects.py
if ($LASTEXITCODE -ne 0) { throw "Targeted backend gate failed" }

Write-Host "== Full backend regression =="
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Full backend regression failed" }

Write-Host "== Compileall =="
& $Python -m compileall -q app tests
if ($LASTEXITCODE -ne 0) { throw "compileall failed" }

Write-Host "== Ruff =="
& $Ruff check app tests
if ($LASTEXITCODE -ne 0) { throw "ruff check failed" }
& $Ruff format --check app tests
if ($LASTEXITCODE -ne 0) { throw "ruff format check failed" }
Pop-Location

Write-Host "== OpenAPI formal/runtime parity =="
& $Python (Join-Path $PSScriptRoot "verify_openapi_parity.py")
if ($LASTEXITCODE -ne 0) { throw "OpenAPI parity failed" }

Write-Host "== Frontend production build =="
Push-Location (Join-Path $Repo "frontend")
npm run build
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }

Write-Host "== Backend-connected Playwright =="
npm run test:e2e
if ($LASTEXITCODE -ne 0) { throw "Playwright failed" }
Pop-Location

Write-Host "ALL VERTICAL-SLICE HARDENING GATES PASSED"
