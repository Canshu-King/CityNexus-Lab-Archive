param(
  [string]$OutputZip = "CityNexus-Vertical-Slice-Hardening-Checkpoint.zip"
)

$ErrorActionPreference = "Stop"
$Repo = (Get-Location).Path
if (-not (Test-Path (Join-Path $Repo "backend\app"))) { throw "Run from the CityNexus repository root" }

$Stage = Join-Path ([System.IO.Path]::GetTempPath()) ("citynexus-stage-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Stage | Out-Null

try {
  $Roots = @("backend", "data", "contracts", "contract", "docs", "frontend")
  foreach ($Name in $Roots) {
    $Source = Join-Path $Repo $Name
    if (Test-Path $Source) { Copy-Item -Recurse -Force $Source (Join-Path $Stage $Name) }
  }

  $TopFiles = @(
    ".env.example",
    "CHECKPOINT_README.md",
    "GATE_MATRIX.md",
    "TEST_RESULTS.txt",
    "BLOCKERS.md",
    "NEXT_RECOMMENDATION.md",
    "SEMANTIC_MERGE.md",
    "CHANGED_FILES.txt",
    "REPO_RELATIVE_MAPPING.md",
    "openapi.yaml"
  )
  foreach ($Name in $TopFiles) {
    $Source = Join-Path $Repo $Name
    if (Test-Path $Source) { Copy-Item -Force $Source (Join-Path $Stage $Name) }
  }

  # Remove generated/dependency state. Review evidence must come from source + tests,
  # not from somebody's 600 MB node_modules or stale SQLite file.
  Get-ChildItem $Stage -Recurse -Directory -Force |
    Where-Object { $_.Name -in @("node_modules", ".venv", ".pytest_cache", "__pycache__", "dist", ".git") } |
    Sort-Object FullName -Descending |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

  Get-ChildItem $Stage -Recurse -File -Force |
    Where-Object { $_.Extension -in @(".pyc", ".zip") -or $_.Name -eq "citynexus.db" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

  $Destination = if ([System.IO.Path]::IsPathRooted($OutputZip)) {
    $OutputZip
  } else {
    Join-Path $Repo $OutputZip
  }
  if (Test-Path $Destination) { Remove-Item -Force $Destination }
  Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $Destination -CompressionLevel Optimal
  Write-Host "Created $Destination"
  Write-Host "Now run tools/fresh_extract_backend_smoke.ps1 -ZipPath `"$Destination`" before reporting the checkpoint."
}
finally {
  Remove-Item -Recurse -Force $Stage -ErrorAction SilentlyContinue
}
