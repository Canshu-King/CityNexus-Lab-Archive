param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference = "Stop"
$bad = Get-ChildItem -Path $Root -Recurse -Force | Where-Object {
  $_.FullName -match "(__pycache__|\\.pytest_cache|\\.ruff_cache|node_modules|\\dist|test-results)" -or
  $_.Name -match "\\.pyc$|\\.(db|sqlite|sqlite3)$"
}
if ($bad) {
  $bad | ForEach-Object { Write-Host $_.FullName }
  throw "Review package contains generated/runtime junk."
}
Write-Host "Review package hygiene PASS"
