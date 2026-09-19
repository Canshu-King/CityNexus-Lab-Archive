param(
  [Parameter(Mandatory=$false)]
  [string]$RepoRoot = "D:\moodle\CityNexus"
)

$ErrorActionPreference = "Stop"

Write-Host "[CityNexus] Repo: $RepoRoot"
Set-Location $RepoRoot

Write-Host "`n== Non-destructive Git inspection =="
git status --short
git diff --stat

$Python = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
$Ruff   = Join-Path $RepoRoot "backend\.venv\Scripts\ruff.exe"

if (-not (Test-Path $Python)) {
  throw "Python venv executable not found: $Python"
}

Set-Location (Join-Path $RepoRoot "backend")

Write-Host "`n== Focused post-Goal semantic gate =="
& $Python -m pytest -q tests\test_post_goal_five_defects.py tests\test_backend_connected_golden_contract.py

Write-Host "`n== Full backend regression =="
& $Python -m pytest -q

Write-Host "`n== Compileall =="
& $Python -m compileall -q app tests

if (Test-Path $Ruff) {
  Write-Host "`n== Ruff check =="
  & $Ruff check app tests
  Write-Host "`n== Ruff format check =="
  & $Ruff format --check app tests
} else {
  Write-Warning "Ruff executable not found at $Ruff. Run the repository's configured Ruff command manually."
}

Write-Host "`nFocused and backend gates completed. Run the repository's OpenAPI exact-match validator next."
Write-Host "No destructive Git command was executed."
