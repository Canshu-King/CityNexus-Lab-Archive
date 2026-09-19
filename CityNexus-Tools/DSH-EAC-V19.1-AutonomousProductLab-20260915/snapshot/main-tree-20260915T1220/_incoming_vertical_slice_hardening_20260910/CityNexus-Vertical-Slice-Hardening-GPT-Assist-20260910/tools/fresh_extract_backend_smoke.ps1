param(
  [Parameter(Mandatory = $true)]
  [string]$ZipPath
)

$ErrorActionPreference = "Stop"
$Repo = (Get-Location).Path
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run from the real CityNexus repo with .venv available" }
if (-not (Test-Path $ZipPath)) { throw "ZIP not found: $ZipPath" }

$Temp = Join-Path ([System.IO.Path]::GetTempPath()) ("citynexus-review-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Temp | Out-Null
try {
  Expand-Archive -Path $ZipPath -DestinationPath $Temp -Force
  $Backend = Join-Path $Temp "backend"
  if (-not (Test-Path (Join-Path $Backend "app"))) {
    # Some ZIP tools wrap the payload in one top-level directory.
    $Candidate = Get-ChildItem $Temp -Directory | Select-Object -First 1
    if ($Candidate) { $Backend = Join-Path $Candidate.FullName "backend" }
  }
  if (-not (Test-Path (Join-Path $Backend "app"))) { throw "Extracted ZIP has no backend/app" }
  Push-Location $Backend
  & $Python -m pytest -q
  if ($LASTEXITCODE -ne 0) { throw "Fresh-extract backend pytest failed" }
  & $Python -m compileall -q app tests
  if ($LASTEXITCODE -ne 0) { throw "Fresh-extract compileall failed" }
  Pop-Location
  Write-Host "FRESH-EXTRACT BACKEND SMOKE PASS"
}
finally {
  if ((Get-Location).Path -like "$Temp*") { Pop-Location }
  Remove-Item -Recurse -Force $Temp -ErrorAction SilentlyContinue
}
